"""匿名統計の集計(GAS doGet の JSON)を読み、prices.json の popularity を更新する。

- 件数が多い順に 1,2,3... を振る。件数0やカタログに無い名前は無視
- 統計に無いサービスの popularity は触らない(内蔵順位にフォールバックする)
- 件数が極端に少ない(合計 < MIN_TOTAL)うちは更新しない(数人のクセで並びが暴れないように)
"""
import json
import os
import sys
import urllib.request

MIN_TOTAL = 30
PRICES = os.path.join(os.path.dirname(__file__), "..", "prices.json")

url = os.environ.get("POPULARITY_URL", "").strip()
if not url:
    print("POPULARITY_URL が無いので何もしない")
    sys.exit(0)

with urllib.request.urlopen(url, timeout=20) as res:
    data = json.load(res)
counts = {k: int(v) for k, v in (data.get("counts") or {}).items() if int(v) > 0}
total = sum(counts.values())
print(f"集計: {len(counts)} サービス / 合計 {total} 件")
if total < MIN_TOTAL:
    print(f"合計が {MIN_TOTAL} 件未満なのでまだ反映しない")
    sys.exit(0)

with open(PRICES, encoding="utf-8") as f:
    prices = json.load(f)

names = {s["name"] for s in prices["services"]}
ranked = [n for n, _ in sorted(counts.items(), key=lambda kv: -kv[1]) if n in names]
rank = {n: i + 1 for i, n in enumerate(ranked)}

changed = 0
for s in prices["services"]:
    new = rank.get(s["name"])
    if new is not None and s.get("popularity") != new:
        s["popularity"] = new
        changed += 1

if changed == 0:
    print("順位に変化なし")
    sys.exit(0)

with open(PRICES, "w", encoding="utf-8") as f:
    json.dump(prices, f, ensure_ascii=False, indent=2)
    f.write("\n")
print(f"{changed} 件の popularity を更新")
