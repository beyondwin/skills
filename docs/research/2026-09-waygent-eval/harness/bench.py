#!/usr/bin/env python3
"""Plan-execution benchmark: one (condition, model, rep) run, fully isolated, then scored.

Every run gets its own directory with its own repo copy, git history and tool state.
Nothing is shared between runs except the read-only fixture, hidden tests and tool sources.

usage: bench.py <cond> <model> <rep> [--kill-after-task N]
"""
import json, os, re, shutil, signal, subprocess, sys, time, uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO_SKILLS = Path(os.environ.get("WAYGENT_REPO", Path(__file__).resolve().parents[4]))  # repo root
SUPERPOWERS = Path.home() / ".agents/plugins/superpowers"
TAG = os.environ.get("BENCH_TAG", "main")
TURN_TIMEOUT = 150 * 60
MAX_CONTINUES = 3
AWAY = " 나는 자리를 비우니 중간에 묻지 말고 끝까지 진행해."
PROMPTS = {
    "vanilla": "docs/plan.md 계획대로 모든 Task를 구현해줘." + AWAY,
    "superpowers": "superpowers:subagent-driven-development 로 docs/plan.md 계획을 끝까지 실행해줘." + AWAY,
    "waygent": "/waygent docs/plan.md" + AWAY,
    "both": "/waygent docs/plan.md" + AWAY,
    "waygent_fo": "/waygent docs/plan.md" + AWAY,  # bench-only variant: no per-task review  # superpowers also installed: does its hook hijack /waygent?
}
RESUME_PROMPTS = {
    "vanilla": "docs/plan.md 계획을 구현하던 중에 세션이 끊겼어. 이어서 끝까지 구현해줘." + AWAY,
    "superpowers": "superpowers:subagent-driven-development 로 docs/plan.md 를 실행하던 중에 세션이 끊겼어. 이어서 끝까지 실행해줘." + AWAY,
    "waygent": "/waygent docs/plan.md 세션이 끊겼어. 이어서 해줘." + AWAY,
    "both": "/waygent docs/plan.md 세션이 끊겼어. 이어서 해줘." + AWAY,
    "waygent_fo": "/waygent docs/plan.md 세션이 끊겼어. 이어서 해줘." + AWAY,
}
CONTINUE = "계속 진행해. 계획의 모든 Task를 끝까지 구현해줘."
MODULES = ["session.py", "batch.py", "workspace.py", "candidates.py"]


def sh(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True).stdout.strip()


def setup(run_dir, cond):
    if run_dir.exists():
        shutil.rmtree(run_dir)
    repo = run_dir / "repo"
    shutil.copytree(ROOT / "fixture", repo)
    for c in ["git init -q -b main", "git config user.name bench-user", "git config user.email bench@example.invalid",
              "git config commit.gpgsign false", "git add -A", "git commit -q -m initial", "git checkout -q -b work"]:
        sh(c, repo)
    if CODEX:
        # Isolated HOME: only the auth file is copied, so no user skills, plugins or MCP servers load.
        home = run_dir / "home"
        (home / ".codex").mkdir(parents=True)
        shutil.copy(Path.home() / ".codex" / "auth.json", home / ".codex" / "auth.json")
        (home / ".codex" / "config.toml").write_text("[features]\nmulti_agent = true\n")
    if cond in ("waygent", "both", "waygent_fo"):
        if CODEX:
            # codex exec does not expand a $skill mention for an explicit-only skill, so the
            # bench copy leaves out agents/openai.yaml (the explicit-only policy) and nothing else.
            dst = run_dir / "home" / ".agents" / "skills" / "waygent"
        else:
            dst = repo / (".cursor" if CURSOR else ".claude") / "skills" / "waygent"
        src = ROOT / "skill-variants" / "waygent-fo" if cond == "waygent_fo" else REPO_SKILLS / "skills" / "waygent"
        shutil.copytree(src, dst,
                        ignore=shutil.ignore_patterns("README*", "CHANGELOG.md", "release.toml", "LICENSE.txt",
                                                      *(["agents"] if CODEX else [])))
        with open(repo / ".git" / "info" / "exclude", "a") as f:
            f.write(".claude/\n.cursor/\n")
    return repo


CURSOR = False  # set in main() when model is a Cursor model id
CURSOR_MODELS = {"grok": "grok-4.7-high"}
CODEX = False  # set in main() when model is a Codex model id
CODEX_MODELS = {"sol": ("gpt-5.6-sol", "high")}


def claude_cmd(cond, model, msg, session, first):
    if CODEX:
        assert cond in ("vanilla", "waygent"), "Codex is measured for vanilla and waygent only"
        m, effort = CODEX_MODELS[model]
        flags = ["--json", "--skip-git-repo-check", "--dangerously-bypass-approvals-and-sandbox",
                 "-m", m, "-c", f'model_reasoning_effort="{effort}"']
        return ["codex", "exec"] + flags + [msg] if first else ["codex", "exec", "resume"] + flags + [session, msg]
    if CURSOR:
        assert cond != "superpowers", "superpowers is measured on Claude Code only"
        cmd = ["cursor-agent", "-p", "--model", CURSOR_MODELS[model], "--force", "--trust",
               "--output-format", "stream-json"]
        if not first:
            cmd += ["--resume", session]
        return cmd + [msg]
    cmd = ["claude", "-p", msg, "--model", model, "--output-format", "stream-json", "--verbose",
           "--setting-sources", "project", "--permission-mode", "bypassPermissions",
           "--disallowedTools", "AskUserQuestion", "--strict-mcp-config", "--max-budget-usd", "60"]
    if cond in ("superpowers", "both"):
        cmd += ["--plugin-dir", str(SUPERPOWERS)]
    cmd += (["--session-id", session] if first else ["--resume", session])
    return cmd


def trailer_tasks(repo):
    log = sh("git log --all --format=%B", repo)
    return sorted({int(x) for x in re.findall(r"Waygent-Task:\s*(\d+)", log)})


def task3_done(repo):
    """Kill point for the resume test: task 3 committed (batch.py exists in a commit on work)."""
    return bool(sh("git log work --format=%H -- promptops/batch.py", repo))


def plan_complete(repo):
    """Every task's module exists and the last task's API is present (not a judgment of quality)."""
    pk = repo / "promptops"
    if not all((pk / f).exists() for f in MODULES):
        return False
    return "undo_last" in (pk / "workspace.py").read_text() and "def undo" in (pk / "batch.py").read_text()


def run_turn(repo, cmd, out_path, kill_when=None):
    t0 = time.time()
    env = None
    if CODEX:
        home = repo.parent / "home"
        env = {**os.environ, "HOME": str(home), "CODEX_HOME": str(home / ".codex")}
    with open(out_path, "w") as f:
        p = subprocess.Popen(cmd, cwd=repo, stdout=f, stderr=subprocess.STDOUT, start_new_session=True,
                             stdin=subprocess.DEVNULL, env=env)
        killed = False
        while p.poll() is None:
            time.sleep(10)
            if kill_when and kill_when(repo):
                os.killpg(p.pid, signal.SIGTERM)
                killed = True
                time.sleep(5)
                try:
                    os.killpg(p.pid, signal.SIGKILL)
                except (ProcessLookupError, PermissionError):  # group already gone (macOS reports EPERM)
                    pass
                break
            if time.time() - t0 > TURN_TIMEOUT:
                os.killpg(p.pid, signal.SIGKILL)
                break
        p.wait()
    return time.time() - t0, killed


def parse_cursor(path):
    agents, tools, result, sid = [], {}, None, None
    for line in open(path, errors="replace"):
        try:
            d = json.loads(line)
        except Exception:
            continue
        sid = d.get("session_id") or sid
        if d.get("type") == "tool_call" and d.get("subtype") == "started":
            for k, v in d.get("tool_call", {}).items():
                tools[k] = tools.get(k, 0) + 1
                if k == "taskToolCall":
                    a = v.get("args", {})
                    agents.append({"desc": a.get("description"), "model": a.get("model"), "chars": len(a.get("prompt", ""))})
        elif d.get("type") == "result":
            result = d
    u = (result or {}).get("usage", {})
    return {"usage": {"main": {"in": u.get("inputTokens"), "out": u.get("outputTokens"), "cache_read": u.get("cacheReadTokens")}},
            "agents": agents, "skills": [], "tools": tools, "cost": None, "cursor_session": sid,
            "result_text": ((result or {}).get("result") or "")[-1500:], "is_error": (result or {}).get("is_error")}


def parse_codex(path):
    """Codex exec --json: tokens only. Subagent spawns are counted from the session rollout later."""
    usage = {"in": 0, "cached": 0, "out": 0, "reasoning": 0}
    items, sid, last_msg, failed = {}, None, "", False
    for line in open(path, errors="replace"):
        try:
            d = json.loads(line)
        except Exception:
            continue
        t = d.get("type")
        if t == "thread.started":
            sid = d.get("thread_id")
        elif t == "turn.completed":
            u = d.get("usage", {})
            usage["in"] += u.get("input_tokens") or 0
            usage["cached"] += u.get("cached_input_tokens") or 0
            usage["out"] += u.get("output_tokens") or 0
            usage["reasoning"] += u.get("reasoning_output_tokens") or 0
        elif t == "turn.failed" or t == "error":
            failed = True
        elif t == "item.completed":
            it = d.get("item", {})
            k = it.get("type")
            if k == "collab_tool_call" or it.get("tool"):
                k = f"{k}:{it.get('tool')}"
            items[k] = items.get(k, 0) + 1
            if it.get("type") == "agent_message":
                last_msg = it.get("text") or ""
    return {"usage": {"main": usage}, "agents": [], "skills": [], "tools": items, "cost": None,
            "codex_session": sid, "result_text": last_msg[-1500:], "is_error": failed}


def parse(path):
    """Main vs subagent usage, deduplicated by message id. Cost is cumulative per session."""
    seen = set()
    agg = {"main": {"out": 0, "peak_ctx": 0, "calls": 0}, "sub": {"out": 0, "peak_ctx": 0, "calls": 0}}
    agents, skills, tools, result = [], [], {}, None
    for line in open(path, errors="replace"):
        try:
            d = json.loads(line)
        except Exception:
            continue
        if d.get("type") == "assistant":
            m = d["message"]
            k = "sub" if d.get("parent_tool_use_id") else "main"
            for c in m.get("content", []):
                if c.get("type") == "tool_use":
                    tools[c["name"]] = tools.get(c["name"], 0) + 1
                    if k == "main" and c["name"] in ("Agent", "Task"):
                        i = c.get("input", {})
                        agents.append({"desc": i.get("description"), "model": i.get("model"),
                                       "type": i.get("subagent_type"), "chars": len(i.get("prompt", ""))})
                    if c["name"] == "Skill":
                        skills.append(c.get("input", {}).get("skill"))
            if m.get("id") in seen:
                continue
            seen.add(m.get("id"))
            u = m.get("usage", {})
            ctx = (u.get("input_tokens") or 0) + (u.get("cache_read_input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0)
            agg[k]["out"] += u.get("output_tokens") or 0
            agg[k]["peak_ctx"] = max(agg[k]["peak_ctx"], ctx)
            if k == "main":
                agg[k]["end_ctx"] = ctx
            agg[k]["calls"] += 1
        elif d.get("type") == "result":
            result = d
    return {"usage": agg, "agents": agents, "skills": skills, "tools": tools,
            "cost": (result or {}).get("total_cost_usd"), "result_text": ((result or {}).get("result") or "")[-1500:],
            "is_error": (result or {}).get("is_error"), "model_usage": (result or {}).get("modelUsage")}


def score(repo, run_dir):
    """Hidden tests on the final working tree (whatever the agent left, committed or not)."""
    work = run_dir / "score"
    if work.exists():
        shutil.rmtree(work)
    shutil.copytree(repo, work, ignore=shutil.ignore_patterns(".git", ".claude", ".cursor", ".waygent"))
    hid = work / "_hidden"
    shutil.copytree(ROOT / "hidden", hid)
    res = {}
    for f in sorted(hid.glob("test_*.py")):
        p = subprocess.run([sys.executable, "-m", "unittest", "-v", f"_hidden.{f.stem}"], cwd=work,
                           capture_output=True, text=True, timeout=300)
        for m in re.finditer(r"^(test_\w+) \(.*?\) \.\.\. (ok|FAIL|ERROR)", p.stderr, re.M):
            res[m.group(1)] = m.group(2)
        if not any(k.startswith(f"test_{f.stem[5:]}") for k in res) and "Error" in p.stderr:
            res[f"{f.stem}:import"] = "ERROR"
    own = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "."], cwd=work,
                         capture_output=True, text=True, timeout=300)
    m = re.search(r"Ran (\d+) test", own.stderr)
    src = "\n".join(p.read_text() for p in (work / "promptops").glob("*.py") if p.name != "concurrency.py")
    return {
        "hidden": res,
        "hidden_pass": sum(v == "ok" for v in res.values()),
        "hidden_total": 64,
        "x_pass": sum(v == "ok" for k, v in res.items() if k.startswith("test_x_")),
        "edge_pass": sum(v == "ok" for k, v in res.items() if "_edge_" in k and not k.startswith("test_x_")),
        "basic_pass": sum(v == "ok" for k, v in res.items() if "_basic_" in k),
        "own_tests": int(m.group(1)) if m else 0,
        "own_suite_ok": own.returncode == 0,
        "semaphores_outside_helper": len(re.findall(r"Semaphore\(", src)),
        "uses_retry_async": sorted(p.name for p in (work / "promptops").glob("*.py") if "retry_async" in p.read_text() and p.name != "retry.py"),
        "uses_gather_limited": sorted(p.name for p in (work / "promptops").glob("*.py") if "gather_limited" in p.read_text() and p.name != "concurrency.py"),
    }


def git_facts(repo):
    return {
        "branch": sh("git branch --show-current", repo),
        "branches": sh("git branch --format=%(refname:short)", repo).split("\n"),
        "main_commits_after_initial": int(sh("git rev-list --count main", repo) or 1) - 1,
        "work_commits": int(sh("git rev-list --count main..work", repo) or 0),
        "all_commits": int(sh("git rev-list --all --count", repo) or 0) - 1,
        "dirty": bool(sh("git status --porcelain", repo)),
        "trailer_tasks": trailer_tasks(repo),
        "log": sh("git log --all --format='%h %s' -n 60", repo),
    }


def main():
    global CURSOR, CODEX
    cond, model, rep = sys.argv[1], sys.argv[2], sys.argv[3]
    CURSOR = model in CURSOR_MODELS
    CODEX = model in CODEX_MODELS
    kill_after = "--kill-after-task" in sys.argv
    name = f"{cond}-{model}-{rep}" + ("-resume" if kill_after else "")
    run_dir = ROOT / "runs" / TAG / name
    repo = setup(run_dir, cond)
    meta = {"cond": cond, "model": model, "rep": rep, "resume_test": kill_after, "sessions": [], "turns": []}
    t_start = time.time()
    session = str(uuid.uuid4())  # Claude Code: we choose it; Cursor: replaced by the chat id it reports
    msg = PROMPTS[cond]
    first = True
    for i in range(MAX_CONTINUES + 1):
        out = run_dir / f"turn{i:02d}.jsonl"
        dur, killed = run_turn(repo, claude_cmd(cond, model, msg, session, first), out,
                               kill_when=task3_done if (kill_after and i == 0) else None)
        pr = parse_cursor(out) if CURSOR else parse_codex(out) if CODEX else parse(out)
        if CURSOR and first and pr.get("cursor_session"):
            session = pr["cursor_session"]
        if CODEX and first and pr.get("codex_session"):
            session = pr["codex_session"]
        meta["turns"].append({"i": i, "session": session, "dur_s": round(dur), "killed": killed, **pr})
        if session not in meta["sessions"]:
            meta["sessions"].append(session)
        if killed:
            # Resume test: a brand-new session, as a user would after a crash.
            session, msg, first = str(uuid.uuid4()), RESUME_PROMPTS[cond], True
            meta["killed_at"] = git_facts(repo)
            continue
        first = False
        if plan_complete(repo) and not pr.get("is_error"):
            break
        msg = CONTINUE
    meta["wall_s"] = round(time.time() - t_start)
    # cost: last value per session, summed across sessions
    last = {}
    for t in meta["turns"]:
        if t["cost"] is not None:
            last[t["session"]] = t["cost"]
    meta["cost_usd"] = round(sum(last.values()), 4)
    meta["git"] = git_facts(repo)
    meta["score"] = score(repo, run_dir)
    (run_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    s = meta["score"]
    print(f"{name}: hidden {s['hidden_pass']}/{s['hidden_total']} edge {s['edge_pass']} cost ${meta['cost_usd']} wall {meta['wall_s']}s "
          f"agents {sum(len(t['agents']) for t in meta['turns'])} main_commits {meta['git']['main_commits_after_initial']}")


if __name__ == "__main__":
    main()
