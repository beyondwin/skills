#!/usr/bin/env python3
"""Collect meta.json + judge.json of every run into results/summary.json (no transcripts)."""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TAG = sys.argv[1] if len(sys.argv) > 1 else "main"
CONDS = json.loads((ROOT / "conditions.json").read_text())


def summarize(run_dir):
    meta = json.loads((run_dir / "meta.json").read_text())
    judge = json.loads((run_dir / "judge.json").read_text()) if (run_dir / "judge.json").exists() else {}
    tools, sub_tools, skills, agents, questions = {}, {}, [], 0, 0
    facts_revealed, corrections, approvals = set(), set(), 0
    for t in meta["turns"]:
        for k, v in (t.get("tools") or {}).items():
            tools[k] = tools.get(k, 0) + v
        for k, v in (t.get("subagent_tools") or {}).items():
            sub_tools[k] = sub_tools.get(k, 0) + v
        for it in t.get("iterations") or []:
            for k, v in (it.get("tools") or {}).items():
                tools[k] = tools.get(k, 0) + v
            agents += it.get("agent_dispatches") or 0
        skills += [s for s in (t.get("skills") or []) if not str(s).startswith("loaded:")]
        agents += t.get("agent_dispatches") or 0
        s = t.get("sim") or {}
        questions += int(s.get("questions_asked") or 0)
        facts_revealed |= set(s.get("facts_revealed") or [])
        corrections |= set(s.get("corrections") or [])
        approvals += 1 if s.get("approval_requested") else 0
    human_msgs = sum(1 for t in meta["turns"] if t.get("phase", "main") == "main")
    g = meta["git"]
    main_commits = [l for l in g["main_log"].splitlines() if l and not any(x in l for x in ("initial", "install ", "ralph: specs"))]
    j = judge.get("judge") or {}
    # claude -p reports total_cost_usd cumulatively for a resumed session, so the conversation costs its
    # last (largest) value; Ralph loop iterations are separate sessions and are summed.
    conv = [t.get("cost_usd") or 0 for t in meta["turns"] if t.get("phase", "main") == "main"]
    loops = sum(t.get("cost_usd") or 0 for t in meta["turns"] if t.get("phase") == "loop-iterations")
    cost = round(max(conv or [0]) + loops, 4)
    return {
        "scenario": meta["scenario"], "condition": meta["condition"], "label": CONDS[meta["condition"]]["label"],
        "cost_usd": cost, "sim_cost_usd": meta["sim_cost_usd"], "judge_cost_usd": judge.get("judge_cost_usd"),
        "wall_min": round(meta["total_wall_s"] / 60, 1), "user_messages": human_msgs,
        "questions_to_user": questions, "approval_requests": approvals,
        "facts_revealed": sorted(facts_revealed), "facts_user_had_to_correct": sorted(corrections),
        "tools": tools, "subagent_tools": sub_tools, "skills_invoked": skills, "subagent_dispatches": agents,
        "git": {"final_branch": g["current"], "branches": g["branches"], "new_commits_on_main": len(main_commits),
                "dirty": bool(g["status"].strip()), "remotes": g["remotes"].strip()},
        "hidden_checks": judge.get("hidden"), "judge": {k: j.get(k) for k in ("scores", "facts", "human_touchpoints",
                                                                           "derivable_questions", "artifacts",
                                                                           "verification_claims_honest", "notable", "evidence")},
    }


def main():
    rows = []
    for d in sorted((ROOT / "runs" / TAG).iterdir()):
        if (d / "meta.json").exists():
            rows.append(summarize(d))
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    (out / f"summary-{TAG}.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1))
    for r in rows:
        h = r["hidden_checks"] or {}
        hp = sum(1 for k, v in h.items() if isinstance(v, bool) and v)
        hn = sum(1 for k, v in h.items() if isinstance(v, bool))
        print(f'{r["scenario"]} {r["condition"]:<12} ${r["cost_usd"]:<7} {r["wall_min"]:>5}m msgs={r["user_messages"]:<2} q={r["questions_to_user"]:<2} '
              f'corr={",".join(r["facts_user_had_to_correct"]) or "-":<9} hidden={hp}/{hn} sub={r["subagent_dispatches"]:<2} br={r["git"]["final_branch"]} mainC={r["git"]["new_commits_on_main"]}')


if __name__ == "__main__":
    main()
