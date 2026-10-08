"""Claude Code adapter for the isolated pre-SDD study; no automatic auth fallback."""
import json
import os
from pathlib import Path
import shutil
import uuid

def usage(path):
    messages = {}
    for line in path.read_text(errors="replace").splitlines():
        try: event = json.loads(line)
        except ValueError: continue
        msg = event.get("message") or {}
        if event.get("type") != "assistant" or msg.get("model") in (None, "<synthetic>"): continue
        data = msg.get("usage") or {}
        old = messages.get(msg.get("id"))
        if old is None or data.get("output_tokens", 0) >= old[2].get("output_tokens", 0):
            messages[msg.get("id")] = (msg.get("model"), event.get("effort"), data)
    models, efforts, tokens = {}, {}, {}
    for model, effort, data in messages.values():
        models[model] = models.get(model, 0) + 1
        efforts[str(effort)] = efforts.get(str(effort), 0) + 1
        for key in ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"):
            tokens[key] = tokens.get(key, 0) + (data.get(key) or 0)
    return {"models": models, "efforts": efforts, "message_count": len(messages), "tokens": tokens}

def prepare(run: Path, repo: Path, prompt: str, arm: str):
    run = Path(run).resolve()
    repo = Path(repo).resolve()
    run.mkdir(parents=True, exist_ok=True)
    sid = str(uuid.uuid4())
    command = ["claude", "-p", "--model", "claude-opus-5-5", "--effort", "high",
        "--output-format", "stream-json", "--verbose", "--setting-sources", "project",
        "--strict-mcp-config", "--permission-mode", "bypassPermissions",
        "--disable-slash-commands", "--no-chrome", "--session-id", sid,
        "--settings", json.dumps({"disableAllHooks": True, "autoMemoryEnabled": False})]
    if arm in ("skill", "full", "full-skill", "pre-sdd-review"):
        agent = {"psdr-reviewer": {"description": "Fresh independent read-only plan reviewer",
            "model": "opus", "effort": "high", "tools": ["Read", "Glob", "Grep"],
            "prompt": "You are a fresh independent read-only reviewer. Use only the dispatch instruction and readable repository evidence. Do not modify any files."}}
        command += ["--agents", json.dumps(agent)]
        prompt += "\nHost mapping only: a fresh read-only Agent subagent_type psdr-reviewer is available. Dispatch with that subagent_type and omit the model field to preserve its Opus/high binding. This does not change the skill's review procedure.\n"
    else:
        command += ["--disallowedTools", "Agent", "Task"]
    command += ["--", prompt]
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE" and not k.startswith("CLAUDE_CODE_")}
    env["PRE_SDD_REVIEW_HOME"] = str(run / "evidence")
    (run / "claude-identity.json").write_text(json.dumps({"session_id": sid,
        "requested_model": "claude-opus-5-5", "requested_effort": "high", "arm": arm,
        "repo": str(repo)}, indent=2))
    return command, env


def parse(run: Path):
    run = Path(run).resolve()
    identity = json.loads((run / "claude-identity.json").read_text())
    result = None
    init = None
    agent_dispatches = []
    stream_models = set()
    errors = []
    for line in (run / "stdout.jsonl").read_text(errors="replace").splitlines():
        try: event = json.loads(line)
        except ValueError: continue
        if event.get("type") == "system" and event.get("subtype") == "init": init = event
        if event.get("type") == "result": result = event
        if event.get("error"): errors.append(event["error"])
        if event.get("type") == "assistant":
            msg = event.get("message") or {}
            if msg.get("model") not in (None, "<synthetic>"): stream_models.add(msg["model"])
            for block in msg.get("content") or []:
                if block.get("type") == "tool_use" and block.get("name") in ("Agent", "Task"):
                    data = block.get("input") or {}
                    agent_dispatches.append({"subagent_type": data.get("subagent_type"),
                        "model_override": data.get("model"), "tool_id": block.get("id")})
    records = []
    transcript_root = Path.home() / ".claude/projects"
    for controller in transcript_root.glob("*/" + identity["session_id"] + ".jsonl"):
        paths = [controller] + sorted((controller.parent / identity["session_id"] / "subagents").glob("*.jsonl"))
        for source in paths:
            target = run / ("controller.jsonl" if source == controller else source.name)
            shutil.copyfile(str(source), str(target))
            records.append({"file": target.name, "role": "controller" if source == controller else "subagent", "usage": usage(target)})
    answer = (result or {}).get("result") or ""
    (run / "answer.txt").write_text(answer)
    return {"requested_identity": identity, "answer": answer,
        "errors": errors, "is_error": (result or {}).get("is_error"),
        "cost_usd": (result or {}).get("total_cost_usd"),
        "model_usage": (result or {}).get("modelUsage"),
        "num_turns": (result or {}).get("num_turns"),
        "observed_stream_models": sorted(stream_models), "transcripts": records,
        "agent_dispatches": agent_dispatches,
        "init": {k: (init or {}).get(k) for k in ("model", "skills", "agents", "mcp_servers")}}
