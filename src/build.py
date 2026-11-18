"""サイトの HTML（トップページと使い方マニュアル）を作る。

使い方：python3 src/build.py

- 文言はサブモジュール translations/（github.com/northeye/carreplotter-i18n）の site/<言語>.json にある。英語（en.json）が元
- translations/site/ にある言語ごとに作る。英語はサイトのルート、ほかの言語は <言語>/ の下
- 訳のない文言は英語で出す
- マニュアルの構成（ページの並び・見出し・段落・画像と番号の座標）は src/manual.py
- 動作確認済みアダプターの一覧（adapters.html の表。製品名・リンクなど訳さないもの）は src/adapters.json。
  name 製品名、site 公式サイト（空ならリンクにしない）、types 接続（BLE / Wi-Fi）、sleep「切断時にスリープ」で眠って起きるか、
  developer 開発者が試したか（false ならユーザーの報告だけで、製品名の下にその旨を出す）。
  user_reports ユーザーの報告の issue の番号（ユーザー確認の列にリンクで出す）。sleep が null なら「未確認」。おすすめ（●）は sleep が true のもの。
  note 補足の文言のキー、buy.amazon は言語ごと（なければ en）、buy.aliexpress は 1 つ。購入リンクが 1 つもなければ「—」
- スクリーンショットは manual/img/<言語>/<名前>.png。その言語のものがなければ英語のものを使う
  （撮影は InfoDrive の tools/png_half.py で半分に縮めたもの）
- 画像に重ねる番号と枠は、元の画面（1080×2424）の座標を割合にして HTML で重ねる（画像には描き込まない）
- プライバシーポリシー（privacy.html・ja/privacy.html）と利用規約（terms.html・ja/terms.html）、特定商取引法に基づく表記（ja/tokushoho.html。日本語だけ）は法的な文書なので翻訳に出さず、手で書く。
  その言語のものがなければ英語のものにリンクする
- 文言の {privacy}・{email}・{github} は、リンク先などに置き換える

文言を直すとき：translations/site/en.json と ja.json を直して carreplotter-i18n に push し、
ここで git submodule update --remote translations、python3 src/build.py を実行して、できた HTML と一緒にコミットする。
"""
import html
import importlib.util
import json
import os
import posixpath
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "translations", "site")
W, H = 1080, 2424
EMAIL = "carreplotter@northeye.org"
GITHUB = "https://github.com/northeye/carreplotter-i18n"
PLAY = "https://play.google.com/store/apps/details?id=org.northeye.replotter"
# アダプターの動作報告の受け付け（このリポジトリの issue。テンプレートは .github/ISSUE_TEMPLATE/adapter-report.yml）
ISSUES = "https://github.com/northeye/carreplotter-docs/issues"

# 言語の切り替えに出す名前（その言語での呼び名）
LANGUAGE_NAMES = {
    "en": "English", "ja": "日本語", "de": "Deutsch", "es": "Español", "fr": "Français",
    "it": "Italiano", "ko": "한국어", "pt-BR": "Português (Brasil)",
}

def load_module(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, "src", f"{name}.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


manual = load_module("manual")
with open(os.path.join(ROOT, "src", "adapters.json"), encoding="utf-8") as f:
    ADAPTERS = json.load(f)["adapters"]


def load(lang):
    with open(os.path.join(SITE, f"{lang}.json"), encoding="utf-8") as f:
        return json.load(f)


EN = load("en")
LANGS = ["en"] + sorted(
    name[:-5] for name in os.listdir(SITE) if name.endswith(".json") and name not in ("en.json", "context.json")
)


def lang_dir(lang):
    """サイトのルートから、その言語のトップページのフォルダー（末尾に /。英語は空）。"""
    return "" if lang == "en" else f"{lang}/"


class Page:
    """1 つの言語の 1 つのページ。[path] はサイトのルートから、その言語のフォルダーの中の場所（"index.html"、"manual/start.html" など）。"""

    def __init__(self, lang, path):
        self.lang = lang
        self.path = path
        self.text = load(lang)

    def t(self, key):
        """文言（訳がなければ英語）。{privacy} などを置き換える。"""
        value = self.text.get(key) or EN[key]
        return value.replace("{privacy}", self.privacy_href()).replace("{email}", EMAIL).replace("{github}", GITHUB)

    def root(self, target):
        """サイトのルートからの場所 [target] への、このページからの相対パス（フォルダーは末尾に /）。"""
        here = posixpath.dirname(lang_dir(self.lang) + self.path) or "."
        rel = posixpath.relpath(target.rstrip("/") or ".", here)
        if target == "" or target.endswith("/"):
            rel = "./" if rel == "." else rel + "/"
        return rel

    def own(self, target):
        """この言語のフォルダーの中の場所 [target] への相対パス。"""
        return "../" * self.path.count("/") + target

    def privacy_href(self):
        return self.legal_href("privacy.html")

    def legal_href(self, name):
        """手で書いた法的な文書（privacy.html・terms.html）への相対パス。この言語の版がなければ英語の版。"""
        if os.path.exists(os.path.join(ROOT, lang_dir(self.lang) + name)):
            return self.own(name)
        return self.root(name)

    def footer(self):
        """ページの下：利用規約・プライバシーポリシー・特定商取引法に基づく表記（日本語だけ）へのリンクと著作権表示。"""
        docs = [("terms.html", "footer.terms"), ("privacy.html", "footer.privacy")]
        if os.path.exists(os.path.join(ROOT, lang_dir(self.lang) + "tokushoho.html")):
            docs.append(("tokushoho.html", "footer.tokushoho"))
        links = " · ".join(f'<a href="{self.legal_href(name)}">{self.t(key)}</a>' for name, key in docs)
        return f"<footer><p>{links}</p><p>Copyright © 2026 Northeye Labs</p></footer>"

    def other_langs(self):
        """ほかの言語の同じページへのリンク（hreflang と、ヘッダーの言語の切り替え）。"""
        links = []
        for other in LANGS:
            if other == self.lang:
                continue
            # トップページはフォルダーで指す（ja/ など）
            target = lang_dir(other) + ("" if self.path == "index.html" else self.path)
            links.append((other, self.root(target)))
        return links

    def head(self, title, description=None, css="style.css"):
        alternates = "".join(f'\n<link rel="alternate" hreflang="{lang}" href="{href}">' for lang, href in self.other_langs())
        desc = f'\n<meta name="description" content="{html.escape(description)}">' if description else ""
        return f"""<!doctype html>
<html lang="{self.lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>{desc}
<link rel="stylesheet" href="{self.root(css)}">{alternates}
</head>"""

    def nav(self, manual_label, manual_href):
        """上のメニュー：使い方・動作確認済みアダプター・よくある質問・プライバシー・ほかの言語。"""
        langs = "".join(f'<a href="{href}">{LANGUAGE_NAMES.get(lang, lang)}</a>' for lang, href in self.other_langs())
        links = [(manual_href, manual_label), (self.own("adapters.html"), self.t("nav.adapters")),
                 (self.own("manual/faq.html"), self.t("nav.faq")), (self.privacy_href(), self.t("nav.privacy"))]
        return "<nav>" + "".join(f'<a href="{href}">{label}</a>' for href, label in links) + langs + "</nav>"

    def write(self, content):
        out = os.path.join(ROOT, lang_dir(self.lang) + self.path)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            f.write(content)


# ---- トップページ ----

def top(lang):
    p = Page(lang, "index.html")
    t = p.t
    badge = f"google-play-badge-{lang}.svg"
    if not os.path.exists(os.path.join(ROOT, badge)):
        badge = "google-play-badge.svg"
    play = PLAY if lang == "en" else f"{PLAY}&amp;hl={lang}"
    store = f'<p class="store"><a class="play" href="{play}"><img src="{p.root(badge)}" alt="{html.escape(t("top.play_badge_alt"))}"></a></p>'
    # 機能ごとに画面と説明（img/top/<言語>/。その言語の画面がなければ英語）
    shots = "en" if not os.path.isdir(os.path.join(ROOT, "img", "top", lang)) else lang

    def feature(key, images):
        alt = html.escape(re.sub(r"<[^>]+>", "", t(f"top.f.{key}.title")), quote=True)
        imgs = "".join(f'<img src="{p.root(f"img/top/{shots}/{name}.jpg")}" alt="{alt}" loading="lazy">' for name in images)
        return (f'<section class="feature"><div class="shots">{imgs}</div>'
                f'<div class="text"><h3>{t(f"top.f.{key}.title")}</h3><p>{t(f"top.f.{key}.body")}</p></div></section>')

    feature_list = "\n".join(feature(k, imgs) for k, imgs in (
        ("replay", ["replay"]), ("3d", ["3d"]), ("trips", ["trips"]), ("score", ["score"]),
        ("meter", ["meter", "mini"]), ("fuel", ["fuel"]),
    ))
    # 画面のない機能は短い箇条書きで（自動で記録・複数の車両・書き出しとバックアップ）
    features = "\n".join(f"  <li>{t(f'top.features.{i}')}</li>" for i in (1, 5, 6))
    p.write(f"""{p.head("CarReplotter", t("top.description"))}
<body>
<main>
<header>
  <a class="brand" href="./">CarReplotter</a>
  {p.nav(t("nav.manual"), "manual/")}
</header>

<div class="hero">
  <img class="photo" src="{p.root("hero-photo.webp")}" alt="">
  <div class="scrim"></div>
  <img src="{p.root("hero.svg")}" alt="">
  <div class="hero-text"><img class="icon" src="{p.root("app-icon.png")}" alt=""><h1><span>{t("top.hero_1")}</span>{"" if lang in ("ja", "zh") else " "}<span>{t("top.hero_2")}</span></h1></div>
</div>
<p class="lead">{t("top.lead")}</p>
{store}

<h2 class="features-heading">{t("top.features.heading")}</h2>
{feature_list}

<div class="card">
<h2>{t("top.more.heading")}</h2>
<ul>
{features}
</ul>
<p>{t("top.features.adapters")} <a href="adapters.html">{t("adapters.title")}</a></p>
</div>

<div class="card">
<h2>{t("top.pricing.heading")}</h2>
<div class="plans">
<div class="plan"><h3>{t("top.pricing.free.title")}</h3><p>{t("top.pricing.free.body")}</p></div>
<div class="plan premium"><h3>{t("top.pricing.premium.title")}</h3><p>{t("top.pricing.premium.body")}</p></div>
</div>
<p class="price">{t("top.pricing.price")}</p>
</div>

<div class="card">
<h2>{t("top.data.heading")}</h2>
<p>{t("top.data.body")}</p>
</div>

<div class="card">
<h2>{t("top.support.heading")}</h2>
<p>{t("top.support.contact")}</p>
<p>{t("top.support.translate")}</p>
</div>

{store}

{p.footer()}
</main>
</body>
</html>
""")


# ---- 動作確認済みアダプター ----

def adapters_page(lang):
    p = Page(lang, "adapters.html")
    t = p.t
    rows = []
    for a in ADAPTERS:
        name = html.escape(a["name"])
        if a["site"]:
            name = f'<a href="{html.escape(a["site"])}" rel="noopener">{name}</a>'
        if a.get("note"):
            name += f'<span class="sub">{t(a["note"])}</span>'
        if not a.get("developer", True):
            name += f'<span class="sub">{t("adapters.user_only")}</span>'
        # スリープ：true 対応・false 非対応・null 未確認。おすすめはスリープに対応しているもの
        sleep_state = {True: "yes", False: "no"}.get(a.get("sleep"), "unknown")
        sleep = t(f"adapters.sleep.{sleep_state}")
        recommended = "●" if a.get("sleep") is True else ""
        # ユーザー確認：報告の issue の番号ごとにリンク
        reports = " ".join(f'<a href="{ISSUES}/{n}" rel="noopener">#{n}</a>' for n in a.get("user_reports", [])) or "—"
        # Amazon は国ごとに違うので言語ごと（その言語がなければ英語の版）。AliExpress は 1 つ
        amazon = a["buy"].get("amazon", {})
        stores = [("Amazon", amazon.get(lang) or amazon.get("en") or ""), ("AliExpress", a["buy"].get("aliexpress") or "")]
        buy = " / ".join(f'<a href="{html.escape(url)}" rel="noopener sponsored">{store}</a>' for store, url in stores if url) or "—"
        rows.append(f'<tr><td>{name}</td><td>{" / ".join(a["types"])}</td>'
                    f'<td class="{sleep_state}">{sleep}</td><td class="mark">{recommended}</td><td>{reports}</td><td>{buy}</td></tr>')
    table = "\n".join(rows)
    p.write(f"""{p.head(f"{t('adapters.title')} — CarReplotter", t("adapters.lead"))}
<body>
<main>
<header>
  <a class="brand" href="./">CarReplotter</a>
  {p.nav(t("nav.manual"), "manual/")}
</header>
<h1>{t("adapters.title")}</h1>
<p class="lead">{t("adapters.lead")}</p>
<p class="ads"><span class="tag">{t("adapters.ads.tag")}</span>{t("adapters.ads")}{(" " + t("adapters.ads.amazon")) if t("adapters.ads.amazon") else ""}</p>
<div class="table-scroll">
<table class="adapters">
<thead><tr><th>{t("adapters.col.name")}</th><th>{t("adapters.col.type")}</th><th>{t("adapters.col.sleep")}</th><th>{t("adapters.col.recommended")}</th><th>{t("adapters.col.user")}</th><th>{t("adapters.col.buy")}</th></tr></thead>
<tbody>
{table}
</tbody>
</table>
</div>
<ul class="notes">
<li>{t("adapters.sleep_note")}</li>
<li>{t("adapters.recommended_note")}</li>
<li>{t("adapters.user_note")}</li>
<li>{t("adapters.disclaimer")}</li>
</ul>
<div class="card">
<h2>{t("adapters.report.heading")}</h2>
<p>{t("adapters.report.body")}</p>
<p><a class="button" href="{ISSUES}/new?template=adapter-report.yml" rel="noopener">{t("adapters.report.button")}</a></p>
</div>
{p.footer()}
</main>
</body>
</html>
""")


# ---- 使い方マニュアル ----

def screenshot_lang(lang, name):
    return lang if os.path.exists(os.path.join(ROOT, "manual", "img", lang, name + ".png")) else "en"


def figure(p, name, marks, caption):
    shot = screenshot_lang(p.lang, name)
    path = os.path.join(ROOT, "manual", "img", shot, name + ".png")
    if not os.path.exists(path):
        print("missing image:", path)
    if isinstance(marks, dict):
        marks = marks[shot]
    marks = [(n, c[shot] if isinstance(c, dict) else c, key) for n, c, key in marks]
    alt = html.escape(re.sub(r"<[^>]+>", "", p.t(caption)), quote=True) if caption else ""
    parts = [f'<figure class="shot"><div class="frame"><img src="{p.root(f"manual/img/{shot}/{name}.png")}" alt="{alt}" loading="lazy">']
    for n, (x1, y1, x2, y2), _ in marks:
        style = f"left:{x1 / W * 100:.2f}%;top:{y1 / H * 100:.2f}%;width:{(x2 - x1) / W * 100:.2f}%;height:{(y2 - y1) / H * 100:.2f}%"
        parts.append(f'<span class="box" style="{style}"><span class="mark">{n}</span></span>')
    parts.append("</div>")
    if marks or caption:
        parts.append("<figcaption>")
        if caption:
            parts.append(f"<p>{p.t(caption)}</p>")
        if marks:
            parts.append('<ol class="legend">')
            for n, _, key in marks:
                parts.append(f'<li><span class="mark">{n}</span><span>{p.t(key)}</span></li>')
            parts.append("</ol>")
        parts.append("</figcaption>")
    parts.append("</figure>")
    return "".join(parts)


def body_html(p, items):
    t = p.t
    out = []
    for item in items:
        kind = item[0]
        if kind == "h2":
            out.append(f'<h2 id="{item[2]}">{t(item[1])}</h2>' if len(item) > 2 else f"<h2>{t(item[1])}</h2>")
        elif kind == "h3":
            out.append(f"<h3>{t(item[1])}</h3>")
        elif kind == "p":
            out.append(f"<p>{t(item[1])}</p>")
        elif kind == "ul":
            out.append("<ul>" + "".join(f"<li>{t(x)}</li>" for x in item[1]) + "</ul>")
        elif kind == "note":
            out.append(f'<div class="note">{t(item[1])}</div>')
        elif kind == "fig":
            out.append(figure(p, item[1], item[2], item[3]))
        elif kind == "faq":
            for q, a in item[1]:
                out.append(f'<details class="faq"><summary>{t(q)}</summary><div>{t(a)}</div></details>')
    return "\n".join(out)


def manual_page(p, title, inner):
    t = p.t
    p.write(f"""{p.head(f"{title} — {t('manual.title')} — CarReplotter")}
<body>
<main class="manual">
<header>
  <a class="brand" href="{p.own("")}">CarReplotter</a>
  {p.nav(t("manual.title"), "index.html")}
</header>
{inner}
{p.footer()}
</main>
</body>
</html>
""")


def manual_pages(lang):
    pages = manual.PAGES
    title = lambda page: Page(lang, "manual/index.html").t(f"manual.{page['slug']}.title")

    def pager(t, i):
        prev = pages[i - 1] if i > 0 else None
        nxt = pages[i + 1] if i + 1 < len(pages) else None
        links = [f'<a href="index.html">{t("manual.contents")}</a>']
        if prev:
            links.insert(0, f'<a href="{prev["slug"]}.html">← {title(prev)}</a>')
        if nxt:
            links.append(f'<a href="{nxt["slug"]}.html">{title(nxt)} →</a>')
        return '<nav class="pager">' + "".join(links) + "</nav>"

    # 目次
    p = Page(lang, "manual/index.html")
    toc = [f"<h1>{p.t('manual.title')}</h1>", f'<p class="lead">{p.t("manual.lead")}</p>', '<ol class="toc">']
    for page in pages:
        summary = p.t(f"manual.{page['slug']}.summary") if page.get("summary") else ""
        toc.append(f'<li><a href="{page["slug"]}.html">{title(page)}</a><span>{summary}</span></li>')
    toc.append("</ol>")
    manual_page(p, p.t("manual.title"), "\n".join(toc))

    for i, page in enumerate(pages):
        p = Page(lang, f"manual/{page['slug']}.html")
        lead = '<p class="lead">' + p.t(f"manual.{page['slug']}.lead") + "</p>\n" if page.get("lead") else ""
        inner = f'{pager(p.t, i)}\n<h1>{title(page)}</h1>\n{lead}{body_html(p, page["body"])}\n{pager(p.t, i)}'
        manual_page(p, title(page), inner)
    return len(pages) + 1


for lang in LANGS:
    top(lang)
    adapters_page(lang)
    n = manual_pages(lang)
    print(f"{lang}: top + {n} manual pages -> /{lang_dir(lang)}")
