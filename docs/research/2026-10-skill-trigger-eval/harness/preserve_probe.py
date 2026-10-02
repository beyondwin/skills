#!/usr/bin/env python3
"""korean-writing-editor meaning-preservation probe on Codex: old text vs new text.

usage: preserve_probe.py <label> <skill-dir> [--reps N] [--parallel P]
Each call: an isolated Codex home holding only this skill, a `$korean-writing-editor` request on
one synthetic sentence that carries a meaning invariant, and a check that the edited sentence keeps it.
"""
import argparse, concurrent.futures as cf, hashlib, json, os, re, shutil, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HOME = Path.home()
CASES = [  # (id, text, every compact substring the edited sentence must keep)
    ("neg-oblig", "이 기능은 사용할수 있지만 반드시 켤 필요는 없습니다.", ["반드시", "필요는없"]),
    ("modality", "회의는 내일 오전 10시에 시작 할수 있을것 같습니다.", ["수있을것같"]),
    ("quantity-attr", "대표는 이번 분기 매출이 약 30% 늘었다고 밝혔다.", ["약30%", "밝혔다"]),
    ("partial-neg", "모든 사용자가 이 설정을 바꿀수 있는건 아닙니다.", ["모든", "아닙니다"]),
    ("limit", "이 약은 하루에 두번 이상 복용하면 안됩니다.", ["두번이상", "안됩니다"]),
    ("neg-attr", "그는 그 계획에 반대하지 않았다고 말했다.", ["반대하지않았", "말했다"]),
]


def home_for(label, skill):
    h = ROOT / "homes" / f"preserve-{label}"
    if not h.exists():
        (h / ".codex").mkdir(parents=True)
        shutil.copy(HOME / ".codex/auth.json", h / ".codex/auth.json")
        if (HOME / ".codex/models_cache.json").exists():
            shutil.copy(HOME / ".codex/models_cache.json", h / ".codex/models_cache.json")
        (h / ".codex/config.toml").write_text('model = "gpt-6-astra"\nmodel_reasoning_effort = "high"\n\n[memories]\ngenerate_memories = false\nuse_memories = false\n')
        shutil.copytree(skill, h / ".agents/skills/korean-writing-editor", ignore=shutil.ignore_patterns("README*", "CHANGELOG.md", "release.toml", "LICENSE.txt"))
    return h


def call(label, home, cid, text, keep, rep):
    run = ROOT / "runs" / "preserve" / label / f"{cid}-r{rep}"
    if (run / "result.json").exists():
        return json.loads((run / "result.json").read_text())
    shutil.rmtree(run, ignore_errors=True)
    repo = run / "repo"
    repo.mkdir(parents=True)
    subprocess.run("git init -q -b main", cwd=repo, shell=True, check=True)
    env = {**{k: v for k, v in os.environ.items() if k != "CLAUDECODE" and not k.startswith("CLAUDE_CODE_")},
           "HOME": str(home), "CODEX_HOME": str(home / ".codex")}
    msg = f"$korean-writing-editor 맞춤법이랑 띄어쓰기 고쳐줘: {text}"
    p = subprocess.run(["codex", "exec", "--json", "--ephemeral", "--skip-git-repo-check", "-s", "read-only", "-o", str(run / "reply.md"), msg],
                       cwd=repo, capture_output=True, text=True, env=env, timeout=600, stdin=subprocess.DEVNULL)
    (run / "out.jsonl").write_text(p.stdout)
    reply = (run / "reply.md").read_text() if (run / "reply.md").exists() else ""
    loaded = "korean-writing-editor/SKILL.md" in p.stdout or "<skill>" in p.stdout
    compact = re.sub(r"\s+", "", reply)
    res = {"label": label, "id": cid, "rep": rep, "loaded": loaded, "kept": all(k in compact for k in keep),
           "missing": [k for k in keep if k not in compact], "reply_chars": len(reply),
           "sha": hashlib.sha256((home / ".agents/skills/korean-writing-editor/SKILL.md").read_bytes()).hexdigest()[:12]}
    shutil.rmtree(repo, ignore_errors=True)
    (run / "result.json").write_text(json.dumps(res, ensure_ascii=False))
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("label"); ap.add_argument("skill")
    ap.add_argument("--reps", type=int, default=2); ap.add_argument("--parallel", type=int, default=6)
    a = ap.parse_args()
    home = home_for(a.label, Path(a.skill))
    jobs = [(cid, t, k, r) for r in range(1, a.reps + 1) for cid, t, k in CASES]
    with cf.ThreadPoolExecutor(a.parallel) as ex:
        for res in ex.map(lambda j: call(a.label, home, *j), jobs):
            print(json.dumps(res, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
