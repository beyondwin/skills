#!/usr/bin/env python3
"""how-it-works reply-format probe: same checks as the 2026-10-01 record, old text vs new text.

usage: format_probe.py <label> <skill-dir> <model> [--reps N] [--parallel P]
One call = a fresh repo holding only this skill under .claude/skills/, `claude -p` with
--setting-sources project. Scores the reply text and the reference reads in the stream.
"""
import argparse, concurrent.futures as cf, hashlib, json, os, re, shutil, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROMPTS = [("ko", "/how-it-works DNS가 브라우저 요청에서 IP 주소가 되는 과정이 어떻게 돌아가는지 보여줘"),
           ("en", "/how-it-works Walk me along the path a git rebase takes through the commit graph")]
HEAD = {"ko": ["## 한 줄", "## 지도", "## 본문", "## 지금 다루지 않은 것"], "en": ["## One sentence", "## Map", "## Body", "## Adjacent slices"]}
RUNG = {"ko": "그림|길|뼈대|허점", "en": "picture|path|skeleton|fracture"}
NEXT = {"ko": "다음:", "en": "Next:"}


def score(text, lang, reads):
    mer = re.findall(r"```mermaid\n(.*?)```", text, re.S)
    listed = set(re.findall(r"\*\*H(\d+)", text))
    in_map = set(re.findall(r"\bH(\d+)[a-z]?\b", mer[0])) if mer else set()
    return {"mermaid": bool(mer),
            "hop_ids": bool(mer) and bool(listed) and bool(in_map) and in_map <= listed,
            "title": bool(re.search(rf"^# .+ · ({RUNG[lang]})\s*$", text, re.M)),
            "headings": all(re.search(rf"^{re.escape(h)}\s*$", text, re.M) for h in HEAD[lang]),
            "next": bool(re.search(rf"^\**{re.escape(NEXT[lang])}", text, re.M)),
            "read_output_md": any("references/output.md" in r for r in reads)}


def call(label, skill, model, lang, prompt, rep):
    run = ROOT / "runs" / "format" / label / model / f"{lang}-r{rep}"
    if (run / "result.json").exists():
        return json.loads((run / "result.json").read_text())
    shutil.rmtree(run, ignore_errors=True)
    repo = run / "repo"
    shutil.copytree(skill, repo / ".claude/skills/how-it-works", ignore=shutil.ignore_patterns("README*", "CHANGELOG.md", "release.toml", "LICENSE.txt", "agents"))
    subprocess.run("git init -q -b main && git -c user.name=t -c user.email=t@e.invalid commit -q --allow-empty -m init", cwd=repo, shell=True, check=True)
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE" and not k.startswith("CLAUDE_CODE_")}
    cmd = ["claude", "-p", prompt, "--model", model, "--output-format", "stream-json", "--verbose", "--setting-sources", "project",
           "--strict-mcp-config", "--permission-mode", "bypassPermissions", "--no-session-persistence"]
    if model == "opus":
        cmd += ["--effort", "high"]
    p = subprocess.run(cmd, cwd=repo, capture_output=True, text=True, env=env, timeout=600, stdin=subprocess.DEVNULL)
    (run / "out.jsonl").write_text(p.stdout)
    text, reads, cost, err = "", [], None, None
    for line in p.stdout.splitlines():
        try:
            e = json.loads(line)
        except Exception:
            continue
        if e.get("type") == "assistant":
            for b in e["message"].get("content", []):
                if b.get("type") == "tool_use" and b.get("name") == "Read":
                    reads.append(str(b["input"].get("file_path", "")))
        if e.get("type") == "result":
            text, cost, err = e.get("result") or "", e.get("total_cost_usd"), e.get("is_error")
    res = {"label": label, "model": model, "lang": lang, "rep": rep, "cost": cost, "is_error": err,
           "sha": hashlib.sha256((Path(skill) / "SKILL.md").read_bytes()).hexdigest()[:12], **score(text, lang, reads)}
    shutil.rmtree(repo, ignore_errors=True)
    (run / "result.json").write_text(json.dumps(res))
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("label"); ap.add_argument("skill"); ap.add_argument("model")
    ap.add_argument("--reps", type=int, default=3); ap.add_argument("--parallel", type=int, default=4)
    a = ap.parse_args()
    jobs = [(lang, pr, r) for lang, pr in PROMPTS for r in range(1, (a.reps if lang == "ko" else 1) + 1)]
    with cf.ThreadPoolExecutor(a.parallel) as ex:
        for res in ex.map(lambda j: call(a.label, a.skill, a.model, *j), jobs):
            print(json.dumps(res), flush=True)


if __name__ == "__main__":
    main()
