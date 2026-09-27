#!/usr/bin/env python3
"""Render results/summary-<tag>.json as the markdown tables used in results.md."""
import json, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
# results/ sits next to the scripts in the work dir, and one level up in the repo copy
if not (ROOT / "results").is_dir():
    ROOT = ROOT.parent
ORDER = ["vanilla", "superpowers", "dryforge", "wo", "mattpocock", "gstack", "bmad", "speckit", "openspec", "ralph"]
NAME = {"vanilla": "기본(대조군)", "superpowers": "superpowers", "dryforge": "dryforge", "wo": "workflow-orchestrator",
        "mattpocock": "mattpocock", "gstack": "gstack", "bmad": "BMAD", "speckit": "Spec Kit", "openspec": "OpenSpec",
        "ralph": "Ralph"}
# read from the transcripts: main commit first, moved to a branch after the user pointed it out
GIT_FIXED = {("s2", "wo"): "지적 후 고침"}
rows = json.loads((ROOT / "results" / f"summary-{sys.argv[1] if len(sys.argv) > 1 else 'main'}.json").read_text())
by = {(r["scenario"], r["condition"]): r for r in rows}


def facts(r):
    c = Counter(((r["judge"] or {}).get("facts") or {}).values())
    return c


def hidden(r):
    h = r["hidden_checks"] or {}
    b = {k: v for k, v in h.items() if isinstance(v, bool) and k != "unittest_discover"}
    return f'{sum(b.values())}/{len(b)}' if b else "-"


def tests(r):
    h = r["hidden_checks"] or {}
    return "통과" if h.get("unittest_discover") else "실패"


def docs(r):
    return len((r["judge"] or {}).get("artifacts") or [])


for scen in ("s1", "s2", "s3"):
    print(f"\n### {scen.upper()}\n")
    if scen == "s1":
        print("| 도구 | 비용 | 시간 | 사람 답변 | 질문 수 | 물어서 확인 | 묻지 않고 맞춤 | 틀린 가정 | 빠짐 | 테스트 | 새 문서·설정 | 서브에이전트 |")
        print("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: |")
    elif scen == "s2":
        print("| 도구 | 비용 | 시간 | 사람 답변 | 질문 수 | 30/50 충돌 질문 | 틀린 가정 | 숨긴 검사 | 테스트 | git 규칙 | 새 문서·설정 | 서브에이전트 |")
        print("| --- | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- | ---: | ---: |")
    else:
        print("| 도구 | 비용 | 시간 | 사람 답변 | 질문 수 | 숨긴 검사 | 테스트 | 새 문서·설정 | 서브에이전트 | 최종 위치 |")
        print("| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- |")
    for c in ORDER:
        r = by.get((scen, c))
        if not r:
            continue
        base = f'| {NAME[c]} | ${r["cost_usd"]:.2f} | {r["wall_min"]}분 | {r["user_messages"]} | {r["questions_to_user"]} |'
        f = facts(r)
        s = (r["judge"] or {}).get("scores") or {}
        if scen == "s1":
            print(base + f' {f.get("asked", 0)} | {f.get("guessed_right", 0)} | {f.get("guessed_wrong", 0)} | {f.get("missing", 0)} | {tests(r)} | {docs(r)} | {r["subagent_dispatches"]} |')
        elif scen == "s2":
            wrong = ",".join(k for k, v in ((r["judge"] or {}).get("facts") or {}).items() if v == "guessed_wrong") or "없음"
            print(base + f' {"예" if s.get("conflict_detected") else "아니오"} | {wrong} | {hidden(r)} | {tests(r)} | {GIT_FIXED.get((scen, c)) or ("지킴" if s.get("git_rule") else "어김")} | {docs(r)} | {r["subagent_dispatches"]} |')
        else:
            g = r["git"]
            where = "main" if g["final_branch"] == "main" else "브랜치"
            print(base + f' {hidden(r)} | {tests(r)} | {docs(r)} | {r["subagent_dispatches"]} | {where} |')
tot = sum(r["cost_usd"] for r in rows)
sim = sum(r["sim_cost_usd"] or 0 for r in rows)
jud = sum(r["judge_cost_usd"] or 0 for r in rows)
print(f"\n합계: 에이전트 ${tot:.2f}, 모의 사용자 ${sim:.2f}, 채점 ${jud:.2f}, 실행 {len(rows)}건")
