"""使い方マニュアルの HTML を作る。

使い方：
  python3 manual-src/build.py ja   # ja/manual/*.html
  python3 manual-src/build.py en   # manual/*.html

- 本文は manual-src/<言語>.py の PAGES（ページの並び）に書く
- スクリーンショットは manual/img/<言語>/<名前>.png（撮影は InfoDrive の tools/png_half.py で半分に縮めたもの）
- 画像に重ねる番号と枠は、元の画面（1080×2424）の座標で書き、割合にして HTML で重ねる（画像には描き込まない）

本文の書き方（各ページの "body" の並び）：
  ("h2", "見出し")
  ("p", "段落（HTML 可）")
  ("ul", ["項目", ...])
  ("note", "注意の囲み（HTML 可）")
  ("fig", "画像の名前", [(番号, (x1, y1, x2, y2), "説明"), ...], "画像の下の説明（なくてもよい）")
  ("faq", [("問い", "答え（HTML 可）"), ...])
"""
import html
import importlib.util
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 1080, 2424

lang = sys.argv[1]
spec = importlib.util.spec_from_file_location("content", os.path.join(ROOT, "manual-src", f"{lang}.py"))
content = importlib.util.module_from_spec(spec)
spec.loader.exec_module(content)

out_dir = os.path.join(ROOT, "ja", "manual") if lang == "ja" else os.path.join(ROOT, "manual")
img_prefix = f"../../manual/img/{lang}/" if lang == "ja" else f"img/{lang}/"
css = "../../style.css" if lang == "ja" else "../style.css"
os.makedirs(out_dir, exist_ok=True)


def figure(name, marks, caption):
    path = os.path.join(ROOT, "manual", "img", lang, name + ".png")
    if not os.path.exists(path):
        print("missing image:", path)
    parts = [f'<figure class="shot"><div class="frame"><img src="{img_prefix}{name}.png" alt="" loading="lazy">']
    for n, (x1, y1, x2, y2), _ in marks:
        style = f"left:{x1 / W * 100:.2f}%;top:{y1 / H * 100:.2f}%;width:{(x2 - x1) / W * 100:.2f}%;height:{(y2 - y1) / H * 100:.2f}%"
        parts.append(f'<span class="box" style="{style}"><span class="mark">{n}</span></span>')
    parts.append("</div>")
    if marks or caption:
        parts.append("<figcaption>")
        if caption:
            parts.append(f"<p>{caption}</p>")
        if marks:
            parts.append('<ol class="legend">')
            for n, _, text in marks:
                parts.append(f'<li><span class="mark">{n}</span><span>{text}</span></li>')
            parts.append("</ol>")
        parts.append("</figcaption>")
    parts.append("</figure>")
    return "".join(parts)


def body_html(items):
    out = []
    for item in items:
        kind = item[0]
        if kind == "h2":
            out.append(f'<h2 id="{item[2]}">{item[1]}</h2>' if len(item) > 2 else f"<h2>{item[1]}</h2>")
        elif kind == "h3":
            out.append(f"<h3>{item[1]}</h3>")
        elif kind == "p":
            out.append(f"<p>{item[1]}</p>")
        elif kind == "ul":
            out.append("<ul>" + "".join(f"<li>{x}</li>" for x in item[1]) + "</ul>")
        elif kind == "note":
            out.append(f'<div class="note">{item[1]}</div>')
        elif kind == "fig":
            out.append(figure(item[1], item[2], item[3] if len(item) > 3 else None))
        elif kind == "faq":
            for q, a in item[1]:
                out.append(f'<details class="faq"><summary>{q}</summary><div>{a}</div></details>')
    return "\n".join(out)


T = content.TEXT
pages = content.PAGES


def nav(i):
    prev = pages[i - 1] if i > 0 else None
    nxt = pages[i + 1] if i + 1 < len(pages) else None
    links = [f'<a href="index.html">{T["toc"]}</a>']
    if prev:
        links.insert(0, f'<a href="{prev["slug"]}.html">← {prev["title"]}</a>')
    if nxt:
        links.append(f'<a href="{nxt["slug"]}.html">{nxt["title"]} →</a>')
    return '<nav class="pager">' + "".join(links) + "</nav>"


def page(title, inner, alt_href):
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} — {T["manual"]} — CarReplotter</title>
<link rel="stylesheet" href="{css}">
<link rel="alternate" hreflang="{T["alt_lang"]}" href="{alt_href}">
</head>
<body>
<main class="manual">
<header>
  <a class="brand" href="{T["home"]}">CarReplotter</a>
  <nav><a href="index.html">{T["manual"]}</a><a href="{T["privacy"]}">{T["privacy_label"]}</a><a href="{alt_href}">{T["alt_label"]}</a></nav>
</header>
{inner}
<footer>Copyright © 2026 Northeye</footer>
</main>
</body>
</html>
"""


alt_base = "../../manual/" if lang == "ja" else "../ja/manual/"

# 目次
toc = [f"<h1>{T['manual']}</h1>", f'<p class="lead">{T["lead"]}</p>', '<ol class="toc">']
for p in pages:
    toc.append(f'<li><a href="{p["slug"]}.html">{p["title"]}</a><span>{p.get("summary", "")}</span></li>')
toc.append("</ol>")
open(os.path.join(out_dir, "index.html"), "w").write(page(T["manual"], "\n".join(toc), alt_base + "index.html"))

for i, p in enumerate(pages):
    inner = f'{nav(i)}\n<h1>{p["title"]}</h1>\n' + (f'<p class="lead">{p["lead"]}</p>\n' if p.get("lead") else "") + body_html(p["body"]) + "\n" + nav(i)
    open(os.path.join(out_dir, p["slug"] + ".html"), "w").write(page(p["title"], inner, alt_base + p["slug"] + ".html"))
print(f"{len(pages) + 1} pages -> {out_dir}")
