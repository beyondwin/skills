#!/usr/bin/env python3
"""Approved, synthetic writing pilot; raw artifacts stay outside this repository."""
import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import time


def run(job, output, auth):
    run_dir = output / job['id']
    run_dir.mkdir(parents=True, exist_ok=False)
    home = run_dir / 'home'
    config = home / '.codex'
    config.mkdir(parents=True)
    copied_auth = config / 'auth.json'
    shutil.copyfile(auth, copied_auth)
    copied_auth.chmod(0o600)
    (config / 'config.toml').write_text(
        'model = "gpt-6-astra"\nmodel_reasoning_effort = "high"\n'
        'web_search = "disabled"\napproval_policy = "never"\n'
        '[memories]\ngenerate_memories = false\nuse_memories = false\n'
        '[features]\napps = false\nmulti_agent = false\n'
        'browser_use = false\ncomputer_use = false\nimage_generation = false\n'
    )
    work = home / 'work'
    work.mkdir()
    env = {k: os.environ[k] for k in ('PATH', 'TMPDIR', 'LANG', 'LC_ALL') if k in os.environ}
    env.update({'HOME': str(home), 'CODEX_HOME': str(config)})
    prompt = Path(job['prompt_path']).read_text()
    if hashlib.sha256(prompt.encode()).hexdigest() != job['prompt_sha256']:
        raise ValueError('Prompt hash changed')
    reply = run_dir / 'response.txt'
    argv = ['codex', 'exec', '--json', '--skip-git-repo-check', '-s', 'read-only',
            '-o', str(reply), '-']
    start = time.monotonic()
    try:
        result = subprocess.run(argv, input=prompt, cwd=work, env=env,
                                capture_output=True, text=True, timeout=240)
        (run_dir / 'stdout.jsonl').write_text(result.stdout)
        (run_dir / 'stderr.txt').write_text(result.stderr)
        status = 'completed' if result.returncode == 0 and reply.is_file() else 'failed'
        events = []
        for line in result.stdout.splitlines():
            try:
                events.append(json.loads(line))
            except ValueError:
                pass
        usage = [e.get('usage') for e in events if e.get('type') == 'turn.completed']
        tool_events = [e for e in events if e.get('item', {}).get('type') in
                       ('command_execution', 'mcp_tool_call', 'web_search', 'file_change')]
    except subprocess.TimeoutExpired:
        status, usage, tool_events = 'timeout', [], []
    finally:
        copied_auth.unlink(missing_ok=True)
    identities = []
    for path in config.glob('sessions/**/*.jsonl'):
        for line in path.read_text().splitlines():
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if event.get('type') == 'turn_context':
                payload = event.get('payload', {})
                identities.append({k: payload.get(k) for k in ('model', 'effort')})
    row = {'job_id': job['id'], 'status': status, 'actual_identity': identities,
           'identity_source': 'rollout turn_context', 'response_path': str(reply),
           'wall_seconds': round(time.monotonic() - start, 3), 'usage': usage,
           'tool_event_count': len(tool_events), 'prompt_sha256': job['prompt_sha256']}
    if reply.exists():
        row['response_sha256'] = hashlib.sha256(reply.read_bytes()).hexdigest()
    (run_dir / 'result.json').write_text(json.dumps(row, indent=2))
    print(json.dumps({'job': job['id'], 'status': status, 'seconds': row['wall_seconds']}), flush=True)
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('jobs', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--auth', type=Path, required=True)
    parser.add_argument('--execute', action='store_true', help='Requires explicit live-call approval')
    args = parser.parse_args()
    jobs = json.loads(args.jobs.read_text())
    if len(jobs) > 24:
        parser.error('Pilot is capped at 24 dispatches')
    if not args.execute:
        print(json.dumps({'jobs': len(jobs), 'live_calls': 0}))
        return
    args.output.mkdir(parents=True, exist_ok=True)
    random.Random(20261009).shuffle(jobs)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(run, job, args.output, args.auth) for job in jobs]
        rows = []
        for future in concurrent.futures.as_completed(futures):
            rows.append(future.result())
            (args.output / 'summary.json').write_text(json.dumps(rows, indent=2))


if __name__ == '__main__':
    main()
