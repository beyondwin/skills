#!/usr/bin/env python3
"""Skill-trigger eval: does a request load the right skill in an environment shaped like the user's?

One call = one fresh fixture repo + one host process, stopped as soon as the target skill loads,
the host finishes, or TIMEOUT passes. Only which skills loaded is kept; the task itself is not graded.

usage: run.py <variant> <host> [--targets DIR] [--skills a,b] [--ids x,y] [--reps N] [--parallel P]
  host: claude | codex. The variant's skill set is copied once into homes/<variant>/ (pinned) and
  every call copies from there, so edits made while a batch runs cannot leak in.
"""
import argparse, concurrent.futures as cf, hashlib, json, os, re, shutil, signal, subprocess, sys, threading, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
TARGETS = ["how-it-works", "korean-writing-editor", "image-workbench", "pre-sdd-review"]
HOSTS_FOR = {"how-it-works": ["claude", "codex"], "korean-writing-editor": ["codex"],
             "image-workbench": ["codex"], "pre-sdd-review": ["claude", "codex"]}
TIMEOUT = 180
CODEX_MODEL = ("gpt-6-astra", "high")
HOME = Path.home()
CLAUDE_PLUGINS = [HOME / ".claude/plugins/cache/claude-community/eli5/1.0.0",
                  HOME / ".claude/plugins/cache/claude-plugins-official/claude-md-management/1.0.0"]
CLAUDE_PLUGINS += sorted((HOME / ".claude/plugins/cache/claude-plugins-official/commit-commands").glob("*"))[:1]
SKILL_RE = re.compile(r"([A-Za-z0-9_.:-]+)/SKILL\.md")
sys.path.insert(0, str(ROOT))
import fixture  # noqa: E402


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def copy_skill(src, dst):
    shutil.copytree(src, dst, symlinks=False, ignore=shutil.ignore_patterns("__pycache__", ".git"))


def build_home(variant, host, targets):
    """Pinned copy of the skill set the user's host loads, with the target skills taken from `targets`."""
    home = ROOT / "homes" / variant / host
    if home.exists():
        return home
    pins = {}
    if host == "claude":
        off = {k for k, v in json.loads((HOME / ".claude/settings.json").read_text()).get("skillOverrides", {}).items() if v == "off"}
        dst = home / "skills"
        for s in sorted((HOME / ".claude/skills").iterdir()):
            if s.name in off or not (s / "SKILL.md").exists():
                continue
            copy_skill(targets / s.name if s.name in TARGETS else s, dst / s.name)
    else:
        codex = home / ".codex"
        codex.mkdir(parents=True)
        shutil.copy(HOME / ".codex/auth.json", codex / "auth.json")
        keep, cfg = [], (HOME / ".codex/config.toml").read_text().splitlines()
        section = ""
        for line in cfg:
            if line.startswith("["):
                section = line
            if section.startswith(("[mcp_servers", "[projects", "[desktop", "[memories", "[[skills.config")):
                continue
            if section == "[features]" and line.startswith("memories"):
                continue
            keep.append(line)
        # Calls must not share memories; everything else (model, effort, plugins, features) is the user's.
        keep += ["", "[memories]", "generate_memories = false", "use_memories = false"]
        # config.toml names gpt-6.1-sol/low, but 12 of the user's last 15 Codex sessions ran gpt-6-astra/high.
        keep = [("model = " + json.dumps(CODEX_MODEL[0])) if l.startswith("model =") else
                ("model_reasoning_effort = " + json.dumps(CODEX_MODEL[1])) if l.startswith("model_reasoning_effort") else l for l in keep]
        (codex / "config.toml").write_text("\n".join(keep) + "\n")
        if (HOME / ".codex/models_cache.json").exists():
            shutil.copy(HOME / ".codex/models_cache.json", codex / "models_cache.json")
        for sub in ["plugins", "skills"]:
            if (HOME / ".codex" / sub).exists():
                shutil.copytree(HOME / ".codex" / sub, codex / sub, symlinks=False, ignore_dangling_symlinks=True,
                                ignore=shutil.ignore_patterns("__pycache__"))
        dst = home / ".agents/skills"
        for s in sorted((HOME / ".agents/skills").iterdir()):
            if (s / "SKILL.md").exists():
                copy_skill(targets / s.name if s.name in TARGETS else s, dst / s.name)
    for t in TARGETS:
        if (dst / t / "SKILL.md").exists():
            pins[t] = sha(dst / t / "SKILL.md")
    (home / "pins.json").write_text(json.dumps({"variant": variant, "host": host, "targets": str(targets), "sha256": pins}, indent=1))
    return home


def clean_env():
    return {k: v for k, v in os.environ.items() if k != "CLAUDECODE" and not k.startswith("CLAUDE_CODE_")}


def call(variant, host, home, case, rep):
    run = ROOT / "runs" / variant / host / f"{case['id'].replace(':', '_')}-r{rep}"
    if (run / "result.json").exists():
        return json.loads((run / "result.json").read_text())
    if run.exists():
        shutil.rmtree(run)
    repo = run / "repo"
    repo.mkdir(parents=True)
    fixture.build(repo)
    env = clean_env()
    if host == "claude":
        shutil.copytree(home / "skills", repo / ".claude/skills")
        (repo / ".claude/settings.json").write_text(json.dumps({"hooks": {"SessionStart": [{"matcher": "startup|clear|compact",
            "hooks": [{"type": "command", "command": str(HOME / ".claude/hooks/superpowers-session-start.sh")}]}]}}))
        with open(repo / ".git/info/exclude", "a") as f:
            f.write(".claude/\n")
        cmd = ["claude", "-p", case["text"], "--model", "opus", "--effort", "high", "--output-format", "stream-json",
               "--verbose", "--setting-sources", "project", "--strict-mcp-config", "--permission-mode", "bypassPermissions",
               "--no-session-persistence"]
        for p in CLAUDE_PLUGINS:
            cmd += ["--plugin-dir", str(p)]
    else:
        env.update({"HOME": str(home), "CODEX_HOME": str(home / ".codex")})
        cmd = ["codex", "exec", "--json", "--ephemeral", "--skip-git-repo-check", "-s", "workspace-write", case["text"]]
    fired, events, ended = [], [], "exit"
    t0 = time.time()
    out = open(run / "out.jsonl", "w")
    p = subprocess.Popen(cmd, cwd=repo, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                         env=env, start_new_session=True, text=True, errors="replace")
    timer = threading.Timer(TIMEOUT, lambda: os.killpg(p.pid, signal.SIGKILL))
    timer.start()
    try:
        for line in p.stdout:
            out.write(line)
            names = []
            try:
                e = json.loads(line)
            except Exception:
                continue
            if host == "claude":
                if e.get("type") == "assistant":
                    for b in e.get("message", {}).get("content", []) or []:
                        if b.get("type") == "tool_use" and b.get("name") == "Skill":
                            names.append(str(b.get("input", {}).get("skill", "")))
                if e.get("type") == "result":
                    ended = "result"
            else:
                it = e.get("item") or {}
                if it.get("type") == "command_execution" and e.get("type") == "item.started":
                    names += [m.split(":")[-1] for m in SKILL_RE.findall(str(it.get("command", "")))]
                if e.get("type") == "turn.completed":
                    ended = "result"
            for n in names:
                short = n.split(":")[-1]
                if short not in fired:
                    fired.append(short)
                    events.append({"skill": n, "t": round(time.time() - t0, 1)})
            if case["skill"] in fired:
                ended = "target"
                os.killpg(p.pid, signal.SIGKILL)
                break
            if ended == "result":
                break
    finally:
        timer.cancel()
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
        p.wait()
        out.close()
    if ended == "exit" and time.time() - t0 >= TIMEOUT - 1:
        ended = "timeout"
    res = {"variant": variant, "host": host, "id": case["id"], "skill": case["skill"], "kind": case["kind"],
           "split": case["split"], "rep": rep, "fired": fired, "events": events, "target_fired": case["skill"] in fired,
           "ended": ended, "secs": round(time.time() - t0, 1), "returncode": p.returncode}
    shutil.rmtree(repo, ignore_errors=True)
    (run / "result.json").write_text(json.dumps(res, ensure_ascii=False))
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("variant"); ap.add_argument("host", choices=["claude", "codex"])
    ap.add_argument("--targets", default=str(REPO / "skills")); ap.add_argument("--skills", default="")
    ap.add_argument("--ids", default=""); ap.add_argument("--reps", type=int, default=2)
    ap.add_argument("--parallel", type=int, default=4)
    a = ap.parse_args()
    home = build_home(a.variant, a.host, Path(a.targets))
    cases = json.loads((ROOT / "prompts.json").read_text())["cases"]
    cases = [c for c in cases if a.host in HOSTS_FOR[c["skill"]]]
    if a.skills:
        cases = [c for c in cases if c["skill"] in a.skills.split(",")]
    if a.ids:
        cases = [c for c in cases if c["id"] in a.ids.split(",")]
    jobs = [(c, r) for r in range(1, a.reps + 1) for c in cases]
    with cf.ThreadPoolExecutor(a.parallel) as ex:
        for res in ex.map(lambda j: call(a.variant, a.host, home, *j), jobs):
            mark = "ok" if res["target_fired"] == (res["kind"] == "pos") else "MISS"
            print(f"{mark} {res['id']} r{res['rep']} fired={res['fired']} {res['ended']} {res['secs']}s", flush=True)


if __name__ == "__main__":
    main()
