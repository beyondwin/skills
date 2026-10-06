#!/usr/bin/env python3
"""Aggregate the 2026-10-02 routing cells from meta.json and progress.md.

usage: analyze_routing.py [--json OUT]   (reads runs/route-pilot and runs/route)
Roles come from the agent definition type when there is one, else the dispatch description.
Cost per role is the list-price estimate from each transcript (bench.py transcript_usage),
recomputed here: meta.json of runs before a7276a6 stored the undercounting first-usage sums.
"""
import json, re, statistics as st, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import bench  # noqa: E402
CELLS = ["wg_base", "wg_final_xhigh", "wg_review_high", "wg_impl_sonnet"]
EXCLUDE = {"route-pilot/wg_base-opus-1-app2"}  # an implementer hit a 429 mid-final; see the pre-registration


def role(a):
    d = (a.get("desc") or "").lower()
    t = a.get("type") or ""
    if t == "waygent-final-reviewer" or ("final" in d and "review" in d and "fix" not in d):
        return "final_review"
    if "final" in d or "walk" in d:
        return "final_fix"
    if t == "waygent-task-reviewer" or ("review" in d and "fix" not in d):
        return "task_review"
    return "implement"


def runs():
    for tag in ["route-pilot", "route"]:
        for d in sorted((ROOT / "runs" / tag).glob("wg_*-app2")):
            if f"{tag}/{d.name}" in EXCLUDE or not (d / "meta.json").exists():
                continue
            yield tag, d


def one(tag, d):
    m = json.loads((d / "meta.json").read_text())
    prog = next((d / "repo/.waygent").glob("*/progress.md"), None)
    ptxt = prog.read_text() if prog else ""
    fixed_tasks = sum(int(x) for x in re.findall(r"review=fixed (\d+)", ptxt))
    overruled = sum(int(x) for x in re.findall(r"review=overruled (\d+)", ptxt))
    final_fixed = sum(int(x) for x in re.findall(r"^final: done .*?fixed=(\d+)", ptxt, re.M))
    t = bench.session_agents(m["sessions"])
    roles = {}
    impl_turns = []
    observed = set()
    for a in t.get("agents", []):
        r = role(a)
        roles.setdefault(r, 0.0)
        roles[r] += a["list_cost"]
        for mo in a["models"]:
            for ef in a["efforts"]:
                observed.add(f"{r}:{mo.replace('claude-', '')}/{ef}")
        if r == "implement" and "fix" not in (a.get("desc") or "").lower():
            impl_turns.append(a["turns"])
    roles["controller"] = sum(x["list_cost"] for x in t.get("main", []))
    s = m["score"]
    return {"run": f"{tag}/{d.name}", "cell": m["cond"], "cost_reported": m["cost_usd"], "cost_list": round(sum(roles.values()), 3),
            "wall_min": round(m["wall_s"] / 60, 1), "hidden": s["hidden_pass"], "trap": s["trap_pass"],
            "task_fixed": fixed_tasks, "task_overruled": overruled, "final_fixed": final_fixed,
            "roles": {k: round(v, 3) for k, v in roles.items()}, "impl_turns_mean": round(st.mean(impl_turns), 1) if impl_turns else None,
            "agents": len(t.get("agents", [])), "observed": sorted(observed),
            "lows": len(re.findall(r": low: ", ptxt))}


def summary(rows):
    out = {}
    for c in CELLS:
        xs = [r for r in rows if r["cell"] == c]
        if not xs:
            continue
        def ms(f):
            v = [f(x) for x in xs if f(x) is not None]
            return (round(st.mean(v), 3), round(st.stdev(v) / len(v) ** 0.5, 3) if len(v) > 1 else None)
        out[c] = {"n": len(xs), "hidden_min": min(x["hidden"] for x in xs), "trap_min": min(x["trap"] for x in xs),
                  "cost_reported": ms(lambda x: x["cost_reported"]), "wall_min": ms(lambda x: x["wall_min"]),
                  "final_review": ms(lambda x: x["roles"].get("final_review", 0)),
                  "task_review": ms(lambda x: x["roles"].get("task_review", 0)),
                  "implement": ms(lambda x: x["roles"].get("implement", 0)),
                  "final_fix": ms(lambda x: x["roles"].get("final_fix", 0)),
                  "controller": ms(lambda x: x["roles"].get("controller", 0)),
                  "task_fixed": ms(lambda x: x["task_fixed"]), "final_fixed": ms(lambda x: x["final_fixed"]),
                  "impl_turns": ms(lambda x: x["impl_turns_mean"]),
                  "observed": sorted({o for x in xs for o in x["observed"]})}
    return out


if __name__ == "__main__":
    rows = [one(t, d) for t, d in runs()]
    for r in rows:
        print(r["run"], r["cost_reported"], r["hidden"], r["trap"], r["task_fixed"], r["final_fixed"], r["roles"], r["impl_turns_mean"])
    s = summary(rows)
    print(json.dumps(s, indent=1))
    if "--json" in sys.argv:
        Path(sys.argv[sys.argv.index("--json") + 1]).write_text(json.dumps({"runs": rows, "summary": s}, indent=1))
