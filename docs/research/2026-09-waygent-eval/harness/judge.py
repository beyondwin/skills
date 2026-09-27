#!/usr/bin/env python3
"""Blind defect judge: a non-Claude model reads each final tree (condition hidden) against the design.

usage: judge.py <tag> [--parallel N]
Writes judge/<tag>/map.json (anon id -> run) and judge/<tag>/<id>.json (defect list).
"""
import json, random, shutil, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROMPT = """You are auditing a small Python package against its design. Work read-only.
Read docs/design.md and docs/plan.md first, then every file in promptops/ (tests/ only if useful).
List real behavior defects: places where the code violates the design or plan, including cases the
design implies but does not spell out. Ignore style, naming, docs and test quality. Do not report a
missing feature the plan does not ask for.

For each defect give: severity (High = user-visible wrong behavior, data loss or overwrite, stuck state;
Medium = wrong result in an edge case; Low = minor), file:line, the design section it violates, and a
reproduction of at most 5 lines of Python using the public API. Verify each reproduction by running it
if you can.

Reply with ONLY a JSON array (no prose) of objects:
{"severity": "High|Medium|Low", "where": "file:line", "design": "§N", "summary": "...", "repro": "..."}
Return [] if you find none."""


def judge_one(item):
    anon, src, out = item
    if out.exists():
        return
    p = subprocess.run(["codex", "exec", "-m", "gpt-5.6-sol", "-c", "model_reasoning_effort=high",
                        "--skip-git-repo-check", "-s", "read-only", "-o", str(out.with_suffix(".txt")), PROMPT],
                       cwd=src, capture_output=True, text=True, timeout=1800)
    txt = out.with_suffix(".txt").read_text() if out.with_suffix(".txt").exists() else ""
    s, e = txt.find("["), txt.rfind("]")
    try:
        data = json.loads(txt[s:e + 1])
    except Exception:
        data = {"parse_error": True, "raw": txt[-3000:], "stderr": p.stderr[-2000:]}
    out.write_text(json.dumps(data, ensure_ascii=False, indent=1))


def main():
    tag = sys.argv[1]
    par = int(sys.argv[sys.argv.index("--parallel") + 1]) if "--parallel" in sys.argv else 4
    jd = ROOT / "judge" / tag
    jd.mkdir(parents=True, exist_ok=True)
    mp = jd / "map.json"
    mapping = json.loads(mp.read_text()) if mp.exists() else {}
    known = set(mapping.values())
    runs = sorted(d for d in (ROOT / "runs" / tag).iterdir() if (d / "meta.json").exists() and d.name not in known)
    rng = random.Random(len(mapping) + 7)
    ids = [f"tree-{len(mapping) + i + 1:02d}" for i in range(len(runs))]
    rng.shuffle(runs)
    items = []
    for anon, run in zip(ids, runs):
        mapping[anon] = run.name
        dst = jd / "trees" / anon
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(run / "score", dst, ignore=shutil.ignore_patterns("_hidden", "__pycache__", ".claude", ".cursor"))
        items.append((anon, dst, jd / f"{anon}.json"))
    mp.write_text(json.dumps(mapping, indent=1))
    for anon, run in mapping.items():
        if not (jd / f"{anon}.json").exists() and all(a != anon for a, _, _ in items):
            items.append((anon, jd / "trees" / anon, jd / f"{anon}.json"))
    with ThreadPoolExecutor(par) as ex:
        list(ex.map(judge_one, items))
    for anon, run in sorted(mapping.items()):
        d = json.loads((jd / f"{anon}.json").read_text())
        if isinstance(d, list):
            sev = [x.get("severity") for x in d]
            print(anon, run, "H", sev.count("High"), "M", sev.count("Medium"), "L", sev.count("Low"))
        else:
            print(anon, run, "PARSE ERROR")


if __name__ == "__main__":
    main()
