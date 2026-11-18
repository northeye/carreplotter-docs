"""アダプターの動作報告の issue（.github/ISSUE_TEMPLATE/adapter-report.yml のフォーム）を src/adapters.json に反映する。

使い方：python3 src/adapter_report.py <issue の番号> <issue の本文のファイル> <PR の本文の出力先>
.github/workflows/adapter-report.yml が、issue に adapter-approved のラベルが付いたときに呼ぶ。

- 一覧に同じ製品（名前の大文字・小文字・空白・記号を無視して同じ）があれば、その user_reports に番号を足すだけ
- なければ新しい行を足す（developer: false。公式サイト・購入リンクは空。報告の URL は PR の本文に出すだけ）
- 本文は誰でも書けるので、値は文字列として JSON に入れるだけにし、長さを制限する（HTML にするときは build.py がエスケープする）
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "src", "adapters.json")
MAX_LEN = 80

# フォームの見出し（英語の部分）→ 項目
FIELDS = {
    "Product name": "product",
    "Name shown in the app": "bluetooth_name",
    "Official site or where you bought it": "link",
    "Connection": "connection",
    "What worked": "works",
    "Sleep check": "sleep",
    "App version and phone": "app",
    "Vehicle (optional)": "vehicle",
    "Notes": "notes",
}

# スリープの確認の答え（英語の部分）→ adapters.json の sleep
SLEEP = {
    "Not checked": None,
    "Works": True,
    "Can't be used: keeps advertising while asleep": False,
    "Can't be used: doesn't wake when the engine starts": False,
    "Not supported by this adapter": False,
}


def parse(body):
    """フォームの本文（「### 見出し」の下に値）を項目ごとの文字列にする。答えのない項目は空。"""
    fields = {}
    for part in re.split(r"^### ", body.replace("\r\n", "\n"), flags=re.M)[1:]:
        heading, _, value = part.partition("\n")
        key = FIELDS.get(heading.split(" / ")[0].strip())
        if key:
            value = value.strip()
            fields[key] = "" if value == "_No response_" else value
    return fields


def clean(text):
    """1 行にし、長さを制限する。PR の本文の Markdown を崩さないよう、バッククォートは消す。"""
    return " ".join(text.replace("`", "").split())[:MAX_LEN]


def checked(text):
    """チェックボックスの答えのうち、チェックの付いたもの（英語の部分）。"""
    return ", ".join(m.split(" / ")[0] for m in re.findall(r"^- \[[xX]\] (.+)$", text, flags=re.M)) or "(none)"


def same_product(a, b):
    norm = lambda s: re.sub(r"[^0-9a-z]", "", s.lower())
    return norm(a) == norm(b)


def main(number, body_path, pr_body_path):
    number = int(number)
    with open(body_path, encoding="utf-8") as f:
        fields = parse(f.read())
    product = clean(fields.get("product", ""))
    if not product:
        sys.exit("製品名がありません")
    connection = "Wi-Fi" if fields.get("connection", "").startswith("Wi-Fi") else "BLE"
    sleep_answer = fields.get("sleep", "").split(" / ")[0].strip()
    sleep = SLEEP.get(sleep_answer)

    with open(DATA, encoding="utf-8") as f:
        data = json.load(f)
    existing = next((a for a in data["adapters"] if same_product(a["name"], product)), None)
    if existing:
        if number not in existing["user_reports"]:
            existing["user_reports"].append(number)
        action = f"既存の `{existing['name']}` の user_reports に #{number} を足しました。"
        # 未確認だったスリープが報告で分かったときだけ埋める（開発者の確認は上書きしない）
        if existing.get("sleep") is None and sleep is not None:
            existing["sleep"] = sleep
            action += f" sleep を {json.dumps(sleep)} にしました。"
    else:
        data["adapters"].append({
            "name": product,
            "site": "",
            "types": [connection],
            "sleep": sleep,
            "developer": False,
            "note": None,
            "user_reports": [number],
            "buy": {"official": "", "amazon": {"ja": "", "en": ""}, "aliexpress": ""},
        })
        action = f"新しい製品 `{product}` を足しました（developer: false、sleep: {json.dumps(sleep)}）。"
    with open(DATA, "w", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")

    # PR の本文（報告の中身はコードブロックに入れて、そのまま見せる）
    shown = {k: checked(v) if k == "works" else v[:500] if k == "notes" else clean(v) for k, v in fields.items() if v}
    report = "\n".join(f"{k}: {v}" for k, v in shown.items()).replace("```", "'''")
    with open(pr_body_path, "w", encoding="utf-8") as f:
        f.write(f"""Closes #{number}

{action}

公式サイト・購入リンクは入れていません。必要ならこの PR に `src/adapters.json` の修正をコミットしてください（HTML はマージのあとに自動で作り直します）。
製品名が既存のものと同じ製品なら、新しい行を消して既存の行の `user_reports` に番号を足してください。

報告の内容：
```
{report}
```
""")
    print(action)


if __name__ == "__main__":
    main(*sys.argv[1:])
