#!/usr/bin/env python3
"""Summarize runs/<tag>/*/meta.json into results/<tag>.json and a markdown table."""
import json, statistics as st, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
tag = sys.argv[1] if len(sys.argv) > 1 else "main"
rows = []
for m in sorted((ROOT / "runs" / tag).glob("*/meta.json")):
    d = json.loads(m.read_text())
    turns = d["turns"]
    main_out = sum(t["usage"].get("main", {}).get("out") or 0 for t in turns)
    sub_out = sum(t["usage"].get("sub", {}).get("out") or 0 for t in turns)
    peak = max((t["usage"].get("main", {}).get("peak_ctx") or 0) for t in turns)
    agents = [a for t in turns for a in t["agents"]]
    s, g = d["score"], d["git"]
    rows.append({
        "run": m.parent.name, "cond": d["cond"], "model": d["model"], "resume": d["resume_test"],
        "hidden": s["hidden_pass"], "edge": s["edge_pass"], "basic": s["basic_pass"],
        "cost": d["cost_usd"], "wall_min": round(d["wall_s"] / 60, 1), "turns": len(turns),
        "agents": len(agents), "brief_chars_avg": round(st.mean([a["chars"] for a in agents])) if agents else 0,
        "main_out": main_out, "sub_out": sub_out, "main_peak_ctx": peak,
        "main_commits": g["main_commits_after_initial"], "work_commits": g["work_commits"], "dirty": g["dirty"],
        "own_tests": s["own_tests"], "own_ok": s["own_suite_ok"], "sem_dup": s["semaphores_outside_helper"],
        "gl_users": len(s["uses_gather_limited"]), "skills": sorted({x for t in turns for x in t.get("skills", []) if x}),
        "x_recreate_ok": s["hidden"].get("test_x_edge_recreated_prompt_not_overwritten_by_stale_session") == "ok",
        "cost_known": d["cost_usd"] if all(t.get("cost") is not None for t in turns) else None,
        "harness_continued": len(turns) > 1 and not d["resume_test"],
        "failed_hidden": sorted(k for k, v in s["hidden"].items() if v != "ok"),
    })
out = ROOT / "results"
out.mkdir(exist_ok=True)
(out / f"{tag}.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1))
cols = ["run", "hidden", "edge", "cost", "wall_min", "agents", "main_peak_ctx", "main_out", "sub_out", "main_commits", "work_commits", "own_tests", "sem_dup"]
print("| " + " | ".join(cols) + " |")
print("|" + "---|" * len(cols))
for r in rows:
    print("| " + " | ".join(str(r[c]) for c in cols) + " |")
