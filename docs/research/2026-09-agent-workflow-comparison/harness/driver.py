#!/usr/bin/env python3
"""Multi-turn probe driver: runs one (scenario, condition) to completion with a simulated user."""
import json, os, re, shutil, subprocess, sys, time, uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRATCH = ROOT.parent
CONDITIONS = json.loads((ROOT / "conditions.json").read_text())


def expand(s):
    return s.replace("$SCRATCH", str(SCRATCH)).replace("$HOME", str(Path.home())) if isinstance(s, str) else s
SCEN = {
    "s1": {"fixture": "empty", "prompt": "가계부 CLI 하나 만들어줘"},
    "s2": {"fixture": "shop", "prompt": "쿠폰 두 장까지 같이 쓸 수 있게 해줘"},
    "s3": {"fixture": "shopbug", "prompt": "고객 문의가 왔어. 상품 금액 딱 50,000원으로 주문했는데 배송비 3,000원이 붙었대. 고쳐줘"},
}
MAX_TURNS = int(os.environ.get("PROBE_MAX_TURNS", "14"))
TURN_TIMEOUT = 90 * 60
MODEL = os.environ.get("PROBE_MODEL", "opus")
SIM_MODEL = os.environ.get("SIM_MODEL", "sonnet")


def first_message(cond, prompt, scen):
    c = CONDITIONS[cond]
    tmpl = c.get("first_by_scenario", {}).get(scen, c.get("first", "{prompt}"))
    return tmpl.replace("{prompt}", prompt)


def cond_env(cond, run_dir=None):
    """$RUN expands to this trial's own directory, so per-tool state never crosses trials."""
    env = dict(os.environ)
    c = CONDITIONS[cond]
    for k, v in c.get("env", {}).items():
        v = expand(v)
        if "$RUN" in v:
            assert run_dir is not None, f"{cond}: $RUN needs a run dir"
            v = v.replace("$RUN", str(run_dir))
        env[k] = v
    if c.get("path_prepend"):
        env["PATH"] = ":".join(expand(x) for x in c["path_prepend"]) + ":" + env["PATH"]
    return env


def sh(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True).stdout


def setup_repo(run_dir, fixture):
    repo = run_dir / "repo"
    if repo.exists():
        shutil.rmtree(repo)
    shutil.copytree(ROOT / "fixtures" / fixture, repo)
    cmds = [
        "git init -q -b main",
        "git config user.name probe-user",
        "git config user.email probe@example.invalid",
        "git config commit.gpgsign false",
    ]
    for c in cmds:
        sh(c, repo)
    if any(p for p in repo.iterdir() if p.name != ".git"):
        sh("git add -A && git commit -q -m 'initial'", repo)
    else:
        sh("git commit -q --allow-empty -m 'initial'", repo)
    return repo


def install_tool(repo, cond):
    setup = CONDITIONS[cond].get("setup")
    if not setup:
        return ""
    p = subprocess.run(["bash", expand(setup), str(repo)], cwd=repo, capture_output=True, text=True, env=cond_env(cond, repo.parent))
    subprocess.run(["git", "add", "-A"], cwd=repo)
    subprocess.run(["git", "commit", "-q", "-m", f"install {cond}"], cwd=repo)
    return p.stdout[-3000:] + p.stderr[-3000:]


def run_agent(repo, cond, msg, session, first, out_path):
    cmd = ["claude", "-p", msg, "--model", MODEL, "--output-format", "stream-json", "--verbose",
           "--setting-sources", "project", "--permission-mode", "bypassPermissions",
           "--disallowedTools", "AskUserQuestion", "--max-budget-usd", "40", "--strict-mcp-config"]
    for d in CONDITIONS[cond].get("plugin_dirs", []):
        cmd += ["--plugin-dir", expand(d)]
    cmd += (["--session-id", session] if first else ["--resume", session])
    t0 = time.time()
    with open(out_path, "w") as f:
        try:
            subprocess.run(cmd, cwd=repo, stdout=f, stderr=subprocess.STDOUT, timeout=TURN_TIMEOUT, env=cond_env(cond, repo.parent))
            timed_out = False
        except subprocess.TimeoutExpired:
            timed_out = True
    wall = time.time() - t0
    return parse_stream(out_path, wall, timed_out)


def parse_stream(path, wall, timed_out):
    tools, sub_tools, skills, agents = {}, {}, [], 0
    texts, result = [], None
    for line in open(path, errors="replace"):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            ev = json.loads(line)
        except Exception:
            continue
        if ev.get("type") == "assistant":
            parent = ev.get("parent_tool_use_id")
            for c in ev.get("message", {}).get("content", []):
                if c.get("type") == "tool_use":
                    bucket = sub_tools if parent else tools
                    bucket[c["name"]] = bucket.get(c["name"], 0) + 1
                    if c["name"] == "Skill":
                        skills.append(c.get("input", {}).get("skill"))
                    if c["name"] in ("Agent", "Task"):
                        agents += 1
                elif c.get("type") == "text" and not parent:
                    texts.append(c["text"])
        elif ev.get("type") == "user":
            for m in re.findall(r"Base directory for this skill: ([^\\\n\"]+)", line):
                skills.append("loaded:" + m.rstrip("/").split("/")[-1])
        elif ev.get("type") == "result":
            result = ev
    r = result or {}
    return {
        "wall_s": round(wall, 1), "timed_out": timed_out,
        "cost_usd": r.get("total_cost_usd"), "num_turns": r.get("num_turns"),
        "is_error": r.get("is_error"), "subtype": r.get("subtype"),
        "result": r.get("result") if r.get("result") is not None else (texts[-1] if texts else ""),
        "tools": tools, "subagent_tools": sub_tools, "skills": skills, "agent_dispatches": agents,
        "usage": r.get("usage"),
    }


SIM_PROMPT = """너는 소프트웨어 개발을 맡긴 '사용자'를 연기한다. 개발 에이전트와 대화 중이다.
아래 '사용자 사실 시트'가 네가 아는 전부다.

규칙:
- 에이전트가 물은 것에만 답한다. 묻지 않은 사실을 먼저 꺼내지 않는다.
- 단, 에이전트가 승인을 요청하며 보여준 설계/계획/결과가 사실 시트와 **명백히 모순**되면, 실제 사용자처럼 그 부분을 바로잡는다(이것을 correction으로 기록).
- 사실 시트에 없는 것을 물으면 "잘 모르겠어요, 추천하는 대로 해주세요"처럼 위임한다.
- 설계/스펙/계획 승인 요청 → 모순이 없으면 승인한다. 에이전트가 문서 파일을 가리키면 현재 폴더에서 그 파일을 읽어 확인해도 된다(Read/Grep/Glob만).
- 실행 방식 선택(예: 서브에이전트 vs 직접) 같은 기술 선택 질문 → "추천하는 방식으로 해주세요".
- git 통합(머지/PR/푸시/브랜치 유지) 질문 → 사실 시트의 git 규칙대로 답한다.
- 에이전트가 작업 완료를 보고했고 네 답이 필요한 질문이 없으면 action=done.
- 짧고 자연스러운 한국어로 답한다.

반드시 마지막에 아래 형식의 JSON 하나만 ```json 블록으로 출력한다:
{"action": "answer|approve|done", "reply": "에이전트에게 보낼 말(done이면 빈 문자열)",
 "questions_asked": <이번 에이전트 메시지에 들어있던 사용자에게 한 질문 수(정수)>,
 "facts_revealed": ["이번 답에서 알려준 사실 ID들, 예: F1"],
 "corrections": ["모순을 바로잡느라 알려준 사실 ID들"],
 "approval_requested": true/false}

## 이 도구의 사용법 (사용자가 단계 전환 때 입력할 명령)
{playbook}
- 사용법이 "다음 단계로 넘어갈 때 X를 입력"이라고 하면, 해당 단계가 끝나 승인할 때 reply를 정확히 그 명령(필요하면 뒤에 짧은 말)으로 보낸다. 슬래시 명령은 reply 맨 앞에 둔다.

## 사용자 사실 시트
{persona}

## 지금까지 대화 (사용자에게 보인 메시지만)
{history}

## 에이전트의 최신 메시지
{latest}
"""


def sim_user(repo, persona, playbook, history, latest, out_path):
    hist = "\n\n".join(f"[{who}] {txt}" for who, txt in history) or "(없음)"
    prompt = SIM_PROMPT.replace("{playbook}", playbook).replace("{persona}", persona).replace("{history}", hist[-30000:]).replace("{latest}", latest[-20000:])
    cmd = ["claude", "-p", prompt, "--model", SIM_MODEL, "--output-format", "json",
           "--setting-sources", "project", "--tools", "Read,Grep,Glob", "--permission-mode", "bypassPermissions", "--strict-mcp-config"]
    p = subprocess.run(cmd, cwd=repo, capture_output=True, text=True, timeout=900)
    Path(out_path).write_text(p.stdout)
    try:
        d = json.loads(p.stdout)
        txt, cost = d.get("result", ""), d.get("total_cost_usd", 0)
    except Exception:
        txt, cost = p.stdout, 0
    m = re.findall(r"```json\s*(\{.*?\})\s*```", txt, re.S)
    try:
        j = json.loads(m[-1])
    except Exception:
        j = {"action": "answer", "reply": "추천하는 대로 진행해주세요.", "parse_error": True}
    j["sim_cost"] = cost
    return j


RALPH_BUILD_ITERS = {"s1": 8, "s2": 6, "s3": 4}


def run_ralph(repo, cond, scen, run_dir):
    """Planning loop then building loop, as the Ralph Playbook documents (bounded)."""
    tools = SCRATCH / "tools" / "ralph"
    env = cond_env(cond, run_dir)
    subprocess.run(["bash", str(tools / "setup.sh"), str(repo), SCEN[scen]["prompt"]], cwd=repo, env=env, capture_output=True)
    subprocess.run(["git", "add", "-A"], cwd=repo)
    subprocess.run(["git", "commit", "-q", "-m", "ralph: specs + prompts baseline"], cwd=repo)
    out = []
    for mode, n in (("plan", 2), ("build", RALPH_BUILD_ITERS[scen])):
        t0 = time.time()
        p = subprocess.run(["bash", str(tools / "run_loop.sh"), str(repo), mode, str(n)], cwd=repo, env=env,
                           capture_output=True, text=True, timeout=4 * 3600)
        (run_dir / f"ralph_{mode}.log").write_text(p.stdout + p.stderr)
        out.append({"phase": f"loop-{mode}", "sent": f"(loop {mode} x<= {n})", "wall_s": round(time.time() - t0, 1)})
    iters = []
    for f in sorted(run_dir.glob("ralph_iter_*.jsonl")):
        r = parse_stream(f, 0, False)
        r["file"] = f.name
        iters.append(r)
    for o in out:
        o["cost_usd"] = 0
        o["result"] = ""
        o["sim"] = {}
    out.append({"phase": "loop-iterations", "sent": "", "result": iters[-1]["result"] if iters else "",
                "cost_usd": round(sum((i["cost_usd"] or 0) for i in iters), 4), "iterations": [
                    {k: i[k] for k in ("file", "cost_usd", "num_turns", "tools", "agent_dispatches", "subtype")} for i in iters],
                "wall_s": 0, "sim": {}})
    return out


def git_snapshot(repo):
    return {
        "branches": sh("git branch -a --format='%(refname:short)'", repo).split(),
        "current": sh("git rev-parse --abbrev-ref HEAD", repo).strip(),
        "log_all": sh("git log --all --oneline --decorate", repo),
        "main_log": sh("git log main --oneline", repo),
        "status": sh("git status --porcelain --untracked-files=all", repo),
        "files": sh("git ls-files", repo),
        "untracked_or_ignored": sh("find . -path ./.git -prune -o -type f -print | grep -v __pycache__ | sort", repo),
        "worktrees": sh("git worktree list", repo),
        "remotes": sh("git remote -v", repo),
    }


def main():
    scen, cond = sys.argv[1], sys.argv[2]
    extra = int(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[3] == "--continue" else 0
    run_dir = ROOT / "runs" / os.environ.get("PROBE_TAG", "main") / f"{scen}-{cond}"
    persona = (ROOT / "personas" / f"{scen}.md").read_text()
    playbook = CONDITIONS[cond].get("playbook", "(특별한 사용법 없음. 평소처럼 대화한다.)")
    phase = "main"
    if extra:
        # resume a run that hit the turn cap: same session, same simulated user, more turns
        old = json.loads((run_dir / "meta.json").read_text())
        repo, session, turns = run_dir / "repo", old["session"], old["turns"]
        history = []
        for t in turns:
            history += [("사용자", t["sent"]), ("에이전트", t["result"] or "")]
        msg = turns[-1]["sim"].get("reply") or "추천하는 대로 진행해주세요."
        t_start = time.time() - old["total_wall_s"]
        start, stop = len(turns), len(turns) + extra
    else:
        run_dir.mkdir(parents=True, exist_ok=True)
        repo = setup_repo(run_dir, SCEN[scen]["fixture"])
        (run_dir / "setup.log").write_text(install_tool(repo, cond))
        session = str(uuid.uuid4())
        msg = first_message(cond, SCEN[scen]["prompt"], scen)
        history, turns = [], []
        t_start = time.time()
        start, stop = 0, MAX_TURNS
    for i in range(start, stop):
        history.append(("사용자", msg))
        r = run_agent(repo, cond, msg, session, i == 0, run_dir / f"turn{i:02d}.jsonl")
        r["sent"] = msg
        r["phase"] = phase
        latest = r["result"] or ""
        history.append(("에이전트", latest))
        s = sim_user(repo, persona, playbook, history[:-1], latest, run_dir / f"sim{i:02d}.json")
        r["sim"] = s
        turns.append(r)
        json.dump({"scenario": scen, "condition": cond, "session": session, "turns": turns},
                  open(run_dir / "progress.json", "w"), ensure_ascii=False, indent=1)
        if r["timed_out"] or s.get("action") == "done":
            break
        if extra and turns[-1]["sim"].get("action") == "done":
            break
        msg = s.get("reply") or "추천하는 대로 진행해주세요."
    if CONDITIONS[cond].get("mode") == "ralph":
        turns += run_ralph(repo, cond, scen, run_dir)
    meta = {
        "scenario": scen, "condition": cond, "session": session, "model": MODEL,
        "total_wall_s": round(time.time() - t_start, 1),
        # total_cost_usd is cumulative within a resumed session: take the conversation's last value, add loop sessions
        "agent_cost_usd": round(max([(t["cost_usd"] or 0) for t in turns if t.get("phase", "main") == "main"] or [0])
                                + sum((t["cost_usd"] or 0) for t in turns if t.get("phase") == "loop-iterations"), 4),
        "sim_cost_usd": round(sum((t["sim"].get("sim_cost") or 0) for t in turns), 4),
        "user_turns": len(turns), "turns": turns, "git": git_snapshot(repo),
    }
    json.dump(meta, open(run_dir / "meta.json", "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: meta[k] for k in ("scenario", "condition", "total_wall_s", "agent_cost_usd", "user_turns")}))


if __name__ == "__main__":
    main()
