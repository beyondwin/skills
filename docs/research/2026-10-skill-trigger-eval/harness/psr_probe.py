#!/usr/bin/env python3
"""pre-sdd-review end-to-end probe on Codex: old text vs new text, full run to the report.

usage: psr_probe.py <label> <skill-dir> [--single N] [--multi N] [--parallel P]
single: one approved spec + plan whose Task 1 names `npm test` in a Python repo (a repo-reality defect).
multi: the same plan plus a second plan that edits the same file, run as one campaign.
Checks the final report (Verdict:, Handoff: for REVISE/BLOCKED), whether the plan's wrong
command was repaired, whether a recorder record exists, and which references were opened.
"""
import argparse, concurrent.futures as cf, hashlib, json, os, re, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HOME = Path.home()
sys.path.insert(0, str(ROOT))
import fixture  # noqa: E402

PLAN = "docs/plans/2026-10-01-retry-backoff.md"
PLAN2 = "docs/plans/2026-10-01-parked-errors.md"
PLAN2_TEXT = """# Parked errors implementation plan

Spec: docs/specs/2026-10-01-retry-backoff-design.md

## Task 1: keep the last error
- Files: src/queue.py, tests/test_queue.py
- `parked` holds `(job, error_message)`; `run_once` stores `str(exc)`.
- Verify: `python3 -m unittest`
"""


def home_for(label, skill):
    h = ROOT / "homes" / f"psr-{label}"
    if not h.exists():
        (h / ".codex").mkdir(parents=True)
        shutil.copy(HOME / ".codex/auth.json", h / ".codex/auth.json")
        if (HOME / ".codex/models_cache.json").exists():
            shutil.copy(HOME / ".codex/models_cache.json", h / ".codex/models_cache.json")
        (h / ".codex/config.toml").write_text('model = "gpt-6-astra"\nmodel_reasoning_effort = "high"\n\n[features]\nmulti_agent = true\n\n[memories]\ngenerate_memories = false\nuse_memories = false\n')
        shutil.copytree(skill, h / ".agents/skills/pre-sdd-review", ignore=shutil.ignore_patterns("README*", "CHANGELOG.md", "release.toml", "LICENSE.txt", "__pycache__"))
    return h


def call(label, home, kind, rep):
    run = ROOT / "runs" / "psr" / label / f"{kind}-r{rep}"
    if (run / "result.json").exists():
        return json.loads((run / "result.json").read_text())
    shutil.rmtree(run, ignore_errors=True)
    repo = run / "repo"
    repo.mkdir(parents=True)
    fixture.build(repo)
    if kind == "multi":
        (repo / PLAN2).write_text(PLAN2_TEXT)
        subprocess.run("git add -A && git commit -q -m 'add second plan'", cwd=repo, shell=True, check=True)
    evid = run / "evidence-home"
    env = {**{k: v for k, v in os.environ.items() if k != "CLAUDECODE" and not k.startswith("CLAUDE_CODE_")},
           "HOME": str(home), "CODEX_HOME": str(home / ".codex"), "PRE_SDD_REVIEW_HOME": str(evid)}
    msg = (f"$pre-sdd-review {PLAN}" if kind == "single" else
           f"$pre-sdd-review {PLAN} {PLAN2} 실행 순서: retry-backoff 먼저, 그다음 parked-errors.")
    p = subprocess.run(["codex", "exec", "--json", "--ephemeral", "--skip-git-repo-check", "--dangerously-bypass-approvals-and-sandbox",
                        "-o", str(run / "reply.md"), msg], cwd=repo, capture_output=True, text=True, env=env,
                       timeout=3600, stdin=subprocess.DEVNULL)
    (run / "out.jsonl").write_text(p.stdout)
    reply = (run / "reply.md").read_text() if (run / "reply.md").exists() else ""
    verdicts = re.findall(r"Verdict:\s*\**\s*(READY|REVISE|BLOCKED)", reply)
    plan_now = (repo / PLAN).read_text()
    cmds = " ".join(re.findall(r'"command":"((?:[^"\\]|\\.)*)"', p.stdout))
    usage = {"in": 0, "cached": 0, "out": 0}
    for line in p.stdout.splitlines():
        if '"turn.completed"' in line:
            u = json.loads(line).get("usage", {})
            usage = {"in": usage["in"] + (u.get("input_tokens") or 0), "cached": usage["cached"] + (u.get("cached_input_tokens") or 0),
                     "out": usage["out"] + (u.get("output_tokens") or 0)}
    res = {"label": label, "kind": kind, "rep": rep, "verdicts": verdicts,
           "handoff_line": bool(re.search(r"^\**Handoff:", reply, re.M)),
           "npm_repaired": "npm test" not in plan_now,
           "records": len(list(evid.rglob("*.json"))) if evid.exists() else 0,
           "read_campaign_md": "campaign.md" in cmds, "read_evidence_readme": "evidence/README.md" in cmds,
           "spawn_agent": p.stdout.count('"spawn_agent"'), "usage": usage, "returncode": p.returncode,
           "sha": hashlib.sha256((home / ".agents/skills/pre-sdd-review/SKILL.md").read_bytes()).hexdigest()[:12]}
    (run / "plan-after.md").write_text(plan_now)
    shutil.rmtree(repo / ".git", ignore_errors=True)
    (run / "result.json").write_text(json.dumps(res))
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("label"); ap.add_argument("skill")
    ap.add_argument("--single", type=int, default=2); ap.add_argument("--multi", type=int, default=1)
    ap.add_argument("--parallel", type=int, default=3)
    a = ap.parse_args()
    home = home_for(a.label, Path(a.skill))
    jobs = [("single", r) for r in range(1, a.single + 1)] + [("multi", r) for r in range(1, a.multi + 1)]
    with cf.ThreadPoolExecutor(a.parallel) as ex:
        for res in ex.map(lambda j: call(a.label, home, *j), jobs):
            print(json.dumps(res), flush=True)


if __name__ == "__main__":
    main()
