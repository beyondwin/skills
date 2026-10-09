"""Bounded Cursor Grok writing pilot; raw artifacts must be outside the repo.

Usage: python3 grok_runner.py /absolute/path/to/live/jobs.json
Fresh HOME/config/data/workspace per job. Only authentication is copied from the
OS keychain into a private auth.json; it is deleted after the process exits.
no personal Cursor configuration, skills, MCP configuration or rules are copied.
Host/server system instructions cannot be removed. A deny-all preToolUse hook
blocks model tools; tool attempts are retained and invalidate clean completion.
"""
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import random
import shlex
import shutil
import signal
import subprocess
import sys
import time

MODEL = "grok-4.7-high"
SEED = 20261009
LIMIT = 24
TIMEOUT = 240


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def run_job(job, root, executable, credentials):
    folder = root / job["id"]
    folder.mkdir()
    home = folder / "home"
    config = home / ".cursor"
    workspace = folder / "workspace"
    config.mkdir(parents=True)
    config.chmod(0o700)
    workspace.mkdir()
    write_json(config / "auth.json", credentials)
    (config / "auth.json").chmod(0o600)
    write_json(config / "cli-config.json", {
        "version": 1, "permissions": {"allow": [], "deny": [
            "Shell(*)", "Read(*)", "Write(*)", "WebSearch(*)", "WebFetch(*)", "MCP(*)"
        ]}, "approvalMode": "allowlist", "autoAcceptWebSearch": False
    })
    hook = folder / "deny_tools.py"
    hook.write_text('import json,sys\njson.load(sys.stdin)\nprint(json.dumps({"permission":"deny","user_message":"Tools are disabled for this writing experiment."}))\n')
    write_json(config / "hooks.json", {"version": 1, "hooks": {
        "preToolUse": [{"command": "{} {}".format(shlex.quote(sys.executable), shlex.quote(str(hook))),
                       "matcher": "*", "failClosed": True}]
    }})
    write_json(config / "mcp.json", {"mcpServers": {}})
    prompt = Path(job["prompt_path"]).read_text()
    if hashlib.sha256(prompt.encode()).hexdigest() != job["prompt_sha256"]:
        raise ValueError("Prompt digest mismatch")
    env = {key: value for key, value in os.environ.items()
           if key in ("PATH", "TMPDIR", "LANG", "LC_ALL", "TERM", "USER", "LOGNAME")}
    env.update({"HOME": str(home), "CURSOR_CONFIG_DIR": str(config),
                "CURSOR_DATA_DIR": str(config), "XDG_CONFIG_HOME": str(home / ".config"),
                "DIRENV_DISABLE": "1", "NO_OPEN_BROWSER": "1", "AGENT_CLI_CREDENTIAL_STORE": "file"})
    command = [executable, "--print", "--model", MODEL, "--mode", "ask",
               "--trust", "--workspace", str(workspace), "--output-format", "stream-json"]
    write_json(folder / "request.json", {
        "job_id": job["id"], "requested_model": MODEL, "prompt_sha256": job["prompt_sha256"],
        "timeout_seconds": TIMEOUT, "prompt_delivery": "stdin verbatim",
        "isolation_limits": "Shared OS keychain and provider system instructions; tool schemas remain visible, deny-all preToolUse hook installed."
    })
    started = time.monotonic()
    timed_out = False
    with (folder / "stream.jsonl").open("w") as stdout, (folder / "stderr.txt").open("w") as stderr:
        proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr,
                                cwd=str(workspace), env=env, text=True, start_new_session=True)
        try:
            proc.communicate(prompt, timeout=TIMEOUT)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(proc.pid, signal.SIGTERM)
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
    (config / "auth.json").unlink(missing_ok=True)
    events = []
    for line in (folder / "stream.jsonl").read_text().splitlines():
        try:
            events.append(json.loads(line))
        except ValueError:
            pass
    results = [item for item in events if item.get("type") == "result"]
    result = results[-1] if results else {}
    texts = []
    for item in events:
        if item.get("type") == "assistant":
            for content in item.get("message", {}).get("content", []):
                if content.get("type") == "text":
                    texts.append(content.get("text", ""))
    response = result.get("result") or "\n".join(texts)
    (folder / "response.txt").write_text(response)
    tool_events = [item for item in events if item.get("type") == "tool_call"]
    identities = [{"event_type": item.get("type"), "subtype": item.get("subtype"),
                   "model": item.get("model") or item.get("message", {}).get("model")}
                  for item in events if item.get("model") or item.get("message", {}).get("model")]
    receipt_prompt = "\n".join(content.get("text", "") for item in events
                               if item.get("type") == "user"
                               for content in item.get("message", {}).get("content", [])
                               if content.get("type") == "text")
    row = {"job_id": job["id"], "status": "timeout" if timed_out else (
        "ok" if proc.returncode == 0 and response and not tool_events and not result.get("is_error") else "failed"),
        "requested_model": MODEL, "actual_model_identity_evidence": identities,
        "response_path": str(folder / "response.txt"), "wall_seconds": round(time.monotonic() - started, 3),
        "provider_duration_ms": result.get("duration_ms"), "provider_duration_api_ms": result.get("duration_api_ms"),
        "usage": result.get("usage"), "exit_code": proc.returncode, "tool_event_count": len(tool_events),
        "receipt_prompt_sha256": hashlib.sha256(receipt_prompt.encode()).hexdigest(),
        "receipt_prompt_matches_except_terminal_newline": receipt_prompt.rstrip("\n") == prompt.rstrip("\n"),
        "authentication_material_deleted": not (config / "auth.json").exists(),
        "isolation_limits": "OS keychain and provider system instructions shared; no personal config/skills copied. Tools denied with preToolUse hook, but tool schemas cannot be removed.",
        "raw_receipt_path": str(folder / "stream.jsonl")}
    write_json(folder / "summary.json", row)
    return row


def main():
    jobs_path = Path(sys.argv[1]).resolve()
    root = jobs_path.parent / "grok"
    root.mkdir(exist_ok=True)
    jobs = json.loads(jobs_path.read_text())
    if len(jobs) > LIMIT:
        raise ValueError("Approved call limit exceeded")
    resume_remaining = "--resume-remaining" in sys.argv
    if (root / "dispatch-order.json").exists() and not resume_remaining:
        raise ValueError("Refusing automatic rerun; failed calls consume budget")
    random.Random(SEED).shuffle(jobs)
    if not resume_remaining:
        write_json(root / "dispatch-order.json", {"seed": SEED, "jobs": [job["id"] for job in jobs]})
    executable = shutil.which("cursor-agent") or shutil.which("agent")
    credentials = {}
    for key, service in (("accessToken", "cursor-access-token"), ("refreshToken", "cursor-refresh-token")):
        value = subprocess.run(["security", "find-generic-password", "-a", "cursor-user", "-s", service, "-w"],
                               capture_output=True, text=True, check=True).stdout.strip()
        credentials[key] = value
    rows = json.loads((root / "summary.json").read_text()) if resume_remaining else []
    jobs = [job for job in jobs if not (root / job["id"]).exists()]
    if not jobs:
        return
    # The first real job doubles as host validation. No separate generation probe.
    first = run_job(jobs[0], root, executable, credentials)
    rows.append(first)
    write_json(root / "summary.json", rows)
    print(json.dumps({"job_id": first["job_id"], "status": first["status"]}), flush=True)
    if first["status"] != "ok":
        return
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(run_job, job, root, executable, credentials) for job in jobs[1:]]
        for future in concurrent.futures.as_completed(futures):
            row = future.result()
            rows.append(row)
            write_json(root / "summary.json", rows)
            print(json.dumps({"job_id": row["job_id"], "status": row["status"]}), flush=True)


if __name__ == "__main__":
    main()
