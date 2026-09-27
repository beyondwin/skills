#!/usr/bin/env python3
"""Per-condition summary across tags (e.g. main rev2) from results/<tag>.json, as markdown."""
import json, statistics as st, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
groups = defaultdict(list)
for tag in sys.argv[1:]:
    for r in json.loads((ROOT / "results" / f"{tag}.json").read_text()):
        key = (r["cond"] + ("-rev2" if tag == "rev2" else ""), r["model"], r["resume"])
        groups[key].append(r)


def m(xs, nd=1):
    xs = [x for x in xs if x is not None]
    return round(st.mean(xs), nd) if xs else "-"


print("| 조건 | 모델 | n | 숨긴 64 | 재생성 결함 피함 | 비용 $ | 시간 분 | 서브에이전트 | 메인 컨텍스트 최대 | main 커밋 |")
print("|---|---|---:|---|---|---:|---:|---:|---:|---:|")
for (c, mo, res), rs in sorted(groups.items()):
    print(f"| {c}{' (끊고 이어 하기)' if res else ''} | {mo} | {len(rs)} | {'/'.join(str(r['hidden']) for r in rs)} | "
          f"{sum(r['x_recreate_ok'] for r in rs)}/{len(rs)} | {m([r['cost'] for r in rs], 2)} | {m([r['wall_min'] for r in rs])} | "
          f"{m([r['agents'] for r in rs])} | {m([r['main_peak_ctx'] for r in rs], 0)} | {sum(r['main_commits'] for r in rs)} |")
