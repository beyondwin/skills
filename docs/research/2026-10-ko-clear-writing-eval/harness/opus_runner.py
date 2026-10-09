#!/usr/bin/env python3
"""Run the consented synthetic writing pilot; receipts stay outside the repository.

Requires a jobs.json manifest with id, prompt_path, and prompt_sha256 fields.
No live preflight, automatic retry, or model fallback is performed. The CLI can
internally retry transport requests, so the cap counts job dispatches, not HTTP.
"""
import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import random
import signal
import subprocess
import time
import uuid


LIMITS = [
    "Fresh session UUID and empty cwd; safe mode disables user customization.",
    "All tools disabled; strict MCP; no native skill expansion; memory disabled.",
    "Host authentication, built-in system prompt, admin policy and provider cache remain.",
    "Requested high effort is not confirmed unless the receipt reports effort.",
]


def parse_receipt(path):
    result, init, models, efforts, tool_calls = {}, {}, set(), set(), 0
    for line in path.read_text(errors="replace").splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if event.get("type") == "result":
            result = event
        if event.get("type") == "system" and event.get("subtype") == "init":
            init = event
        if event.get("effort"):
            efforts.add(event["effort"])
        message = event.get("message") or {}
        if event.get("type") == "assistant":
            if message.get("model") not in (None, "<synthetic>"):
                models.add(message["model"])
            tool_calls += sum(block.get("type") == "tool_use"
                              for block in message.get("content", []))
    return result, init, sorted(models), sorted(efforts), tool_calls


def run_job(job, output, executable, timeout):
    run_dir = output / job["id"]
    run_dir.mkdir()
    cwd = run_dir / "cwd"
    cwd.mkdir()
    prompt = Path(job["prompt_path"]).read_bytes()
    if hashlib.sha256(prompt).hexdigest() != job["prompt_sha256"]:
        raise ValueError("Prompt hash mismatch: " + job["id"])
    command = [executable, "-p", "--model", "opus", "--effort", "high",
               "--safe-mode", "--setting-sources", "", "--tools", "",
               "--disable-slash-commands", "--strict-mcp-config", "--no-chrome",
               "--permission-mode", "dontAsk", "--no-session-persistence",
               "--session-id", str(uuid.uuid4()), "--output-format", "stream-json",
               "--verbose", "--settings", json.dumps({"disableAllHooks": True,
                                                        "autoMemoryEnabled": False})]
    env = {k: v for k, v in os.environ.items()
           if k != "CLAUDECODE" and not k.startswith("CLAUDE_CODE_")}
    receipt = run_dir / "stdout.jsonl"
    start = time.monotonic()
    timed_out = False
    with receipt.open("wb") as stdout, (run_dir / "stderr.txt").open("wb") as stderr:
        process = subprocess.Popen(command, cwd=str(cwd), env=env,
                                   stdin=subprocess.PIPE, stdout=stdout,
                                   stderr=stderr, start_new_session=True)
        try:
            process.communicate(prompt, timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
    elapsed = round(time.monotonic() - start, 3)
    result, init, models, efforts, calls = parse_receipt(receipt)
    answer = result.get("result") or ""
    answer_path = run_dir / "response.txt"
    answer_path.write_text(answer)
    success = (process.returncode == 0 and not result.get("is_error")
               and bool(answer) and calls == 0 and bool(models)
               and all("opus" in model for model in models))
    row = {"job_id": job["id"], "status": "timeout" if timed_out else
           ("ok" if success else "error"), "actual_model": models,
           "requested_model": "opus", "requested_effort": "high",
           "actual_effort": efforts, "response_path": str(answer_path),
           "receipt_path": str(receipt), "wall_seconds": elapsed,
           "returncode": process.returncode, "usage": result.get("usage"),
           "model_usage": result.get("modelUsage"),
           "cost_usd": result.get("total_cost_usd"), "tool_calls": calls,
           "init_tools": init.get("tools"), "init_skills": init.get("skills"),
           "init_mcp_servers": init.get("mcp_servers"),
           "prompt_sha256": job["prompt_sha256"], "isolation_limits": LIMITS}
    (run_dir / "summary.json").write_text(json.dumps(row, indent=2))
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jobs", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()
    jobs = json.loads(args.jobs.read_text())
    if len(jobs) > 24 or len({job["id"] for job in jobs}) != len(jobs):
        raise ValueError("Maximum 24 unique job dispatches")
    for job in jobs:
        if Path(job["id"]).name != job["id"] or job["id"] in (".", ".."):
            raise ValueError("Unsafe job id")
        if hashlib.sha256(Path(job["prompt_path"]).read_bytes()).hexdigest() != job["prompt_sha256"]:
            raise ValueError("Prompt hash mismatch")
    random.Random(20261009).shuffle(jobs)
    if not args.execute:
        print(json.dumps({"dispatches": len(jobs), "order": [j["id"] for j in jobs],
                          "execute": False}))
        return
    output = args.output.resolve()
    repo = Path(__file__).resolve().parents[4]
    if output == repo or repo in output.parents:
        raise ValueError("Raw output must remain outside repository")
    output.mkdir(parents=True, exist_ok=False)
    (output / "dispatch_order.json").write_text(json.dumps([j["id"] for j in jobs], indent=2))
    version = subprocess.run(["claude", "--version"], capture_output=True, text=True, check=True).stdout.strip()
    (output / "cli_version.txt").write_text(version)
    rows = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(run_job, job, output, "claude", args.timeout) for job in jobs]
        for future in concurrent.futures.as_completed(futures):
            row = future.result()
            rows.append(row)
            (output / "summary.json").write_text(json.dumps(rows, indent=2))
            print(json.dumps({k: row[k] for k in ("job_id", "status", "actual_model", "wall_seconds")}), flush=True)


if __name__ == "__main__":
    main()
