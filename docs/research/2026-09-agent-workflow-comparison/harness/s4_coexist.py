#!/usr/bin/env python3
"""S4: with superpowers AND dryforge loaded, does /dryforge:ready get hijacked by the superpowers hook? One turn per trial."""
import json, sys, uuid
from pathlib import Path
import driver

ROOT = Path(__file__).resolve().parent
out = []
for trial, (cond, first) in enumerate([("coexist", "/dryforge:ready {prompt}"), ("coexist", "/dryforge:ready {prompt}"),
                                       ("coexist", "{prompt}"), ("coexist", "{prompt}")]):
    run_dir = ROOT / "runs" / "s4" / f"trial{trial}"
    run_dir.mkdir(parents=True, exist_ok=True)
    repo = driver.setup_repo(run_dir, "shop")
    msg = first.replace("{prompt}", driver.SCEN["s2"]["prompt"])
    r = driver.run_agent(repo, cond, msg, str(uuid.uuid4()), True, run_dir / "turn00.jsonl")
    hook = "You have superpowers" in (run_dir / "turn00.jsonl").read_text()
    row = {"trial": trial, "sent": msg, "skills": r["skills"], "tools": r["tools"], "cost_usd": r["cost_usd"],
           "hook_injected": hook, "result_head": (r["result"] or "")[:600]}
    out.append(row)
    print(json.dumps({k: row[k] for k in ("trial", "sent", "skills", "hook_injected", "cost_usd")}, ensure_ascii=False), flush=True)
(ROOT / "results" / "s4-coexist.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
