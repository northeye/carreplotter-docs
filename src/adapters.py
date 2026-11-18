"""動作確認済みアダプターの一覧（adapters.html の表）。上から順に出す。

  name   製品名（訳さない）
  site   公式サイトの URL（空ならリンクにしない）
  types  CarReplotter で使える接続（"BLE" / "Wi-Fi"）
  sleep  「切断時にスリープ」（AT LP）で眠り、エンジン始動で起きるか（True / False）
  note   補足の文言のキー（translations/site/<言語>.json。なければ None）
  buy    購入リンクの URL。言語ごと（{"ja": "...", "en": "..."}）。その言語がなければ "en"、空なら「—」
"""

ADAPTERS = [
    {
        "name": "Vgate iCar Pro Bluetooth 4.0 (BLE)",
        "site": "",
        "types": ["BLE"],
        "sleep": True,
        "note": "adapters.note.vgate",
        "buy": {"ja": "", "en": ""},
    },
    {
        "name": "Infocar PH-02",
        "site": "",
        "types": ["BLE"],
        "sleep": False,
        "note": "adapters.note.infocar",
        "buy": {"ja": "", "en": ""},
    },
]
