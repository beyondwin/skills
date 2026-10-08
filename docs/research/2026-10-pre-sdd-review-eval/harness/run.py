#!/usr/bin/env python3
"""Explicit live study runner. Never called by repository verification.

python3 run.py --engine sol --stage discovery --output /tmp/psdr-study-20261008
Each invocation runs its own engine cells, two at a time, never overwrites a cell.
"""
import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import signal
import subprocess
import time

HERE = Path(__file__).resolve().parent
PRODUCT = HERE.parents[3] / 'skills' / 'pre-sdd-review'
MODELS = {'sol': 'gpt-6.1-sol', 'astra': 'gpt-6-astra'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(repo):
    return {str(p.relative_to(repo)): sha(p) for p in sorted(repo.rglob('*'))
            if p.is_file() and '.git' not in p.relative_to(repo).parts
            and '__pycache__' not in p.parts}


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo)] + list(args), text=True).strip()


def frames(path):
    if not path.exists():
        return []
    values = []
    for line in path.read_text(errors='replace').splitlines():
        try:
            v = json.loads(line)
        except ValueError:
            continue
        if isinstance(v, dict):
            values.append(v)
    return values


def codex_prepare(run, repo, prompt, arm, engine):
    h = run / 'home'
    c = h / '.codex'
    c.mkdir(parents=True)
    shutil.copy2(Path.home() / '.codex/auth.json', c / 'auth.json')
    (c / 'auth.json').chmod(0o600)
    (c / 'config.toml').write_text(
        '[features]\nmulti_agent = true\n[memories]\n'
        'generate_memories = false\nuse_memories = false\n')
    env = dict(os.environ, HOME=str(h), CODEX_HOME=str(c),
               PRE_SDD_REVIEW_HOME=str(run / 'evidence'), PYTHONDONTWRITEBYTECODE='1')
    cmd = ['codex', 'exec', '--json', '--dangerously-bypass-approvals-and-sandbox',
           '-m', MODELS[engine], '-c', 'model_reasoning_effort="high"',
           '-o', str(run / 'reply.md'), prompt]
    return cmd, env


def codex_parse(run):
    sessions = []
    for path in sorted((run / 'home/.codex/sessions').rglob('*.jsonl')):
        entries = frames(path)
        identities = sorted(set((str(x['payload'].get('model')), str(x['payload'].get('effort')))
                                for x in entries if x.get('type') == 'turn_context'))
        usage = None
        calls = []
        meta = next((x.get('payload', {}) for x in entries if x.get('type') == 'session_meta'), {})
        for e in entries:
            p = e.get('payload', {})
            if e.get('type') == 'event_msg' and p.get('type') == 'token_count':
                usage = (p.get('info') or {}).get('total_token_usage') or usage
            if e.get('type') == 'response_item' and p.get('type') == 'function_call':
                if 'spawn_agent' in str(p.get('name')):
                    try:
                        a = json.loads(p.get('arguments', '{}'))
                    except ValueError:
                        a = {}
                    calls.append({'name': p.get('name'), 'fork_turns': a.get('fork_turns'),
                                  'model': a.get('model'), 'reasoning_effort': a.get('reasoning_effort')})
        sessions.append({'id': meta.get('id'), 'source': meta.get('source'),
                         'model_effort': [list(x) for x in identities], 'usage': usage,
                         'spawn_calls': calls})
    stream = frames(run / 'stdout.jsonl')
    terminal = [x for x in stream if x.get('type') in ('turn.completed', 'turn.failed', 'error')]
    return {'sessions': sessions, 'terminal': terminal,
            'usage_scope': 'per-session cumulative totals; parent stream may exclude child usage'}


def prompt_for(run, arm, stage):
    base = ('Review docs/plan.md against its linked design and the actual repository, '
            'immediately before implementation. Report material, actionable readiness defects '
            'with specific evidence, and whether the plan is ready, needs revision, or is blocked. '
            'Preserve approved product decisions. Implementation has not started. '
            'Do not implement code, commit, access the network, or inspect anything outside '
            'this repository and the explicitly supplied review resources. ')
    if stage == 'repair':
        base += ('Correct repairable document defects and check the result before reporting. '
                 'You may edit only docs/design.md and docs/plan.md. '
                 'If a new product decision is required, leave it unresolved and report it. ')
    else:
        base += 'Do not edit any reviewed document, application code, tests, or configuration. '
    if arm == 'plain':
        return base + 'Perform the review yourself, without skills or subagents.'
    if arm == 'protocol':
        return base + ('Perform the review yourself, without subagents. Apply the reviewer '
                       'protocol at ' + str(run / 'protocol.md') + '. No controller or recorder is requested.')
    return base + ('Use the pinned pre-sdd-review skill at ' + str(run / 'skill/SKILL.md') +
                   (' in default mode' if stage == 'repair' else ' in explicit review-only mode') +
                   ' for docs/plan.md. Read that SKILL.md and follow its procedure. '
                   'Its bundled evidence recorder may write to PRE_SDD_REVIEW_HOME, which is isolated '
                   'for this run. Use fresh read-only reviewers through the native agent facility.')


def extract_reply(run, engine):
    if engine in MODELS:
        return
    data = frames(run / 'stdout.jsonl')
    results = [x for x in data if x.get('type') == 'result' and isinstance(x.get('result'), str)]
    if results:
        text = results[-1]['result']
    else:
        texts = []
        for x in data:
            if x.get('type') == 'assistant':
                msg = x.get('message', {})
                for part in msg.get('content', []):
                    if part.get('type') == 'text':
                        texts.append(part.get('text', ''))
        text = '\n\n'.join(texts)
    (run / 'reply.md').write_text(text)


def execute(output, engine, case, arm, rep, stage, skill_root=PRODUCT):
    name = '{}-{}-{}-r{}-{}'.format(engine, case, arm, rep, stage)
    run = output / name
    run.mkdir(parents=True, exist_ok=False)
    repo = run / 'repo'
    shutil.copytree(HERE / 'fixtures' / case, repo)
    git(repo, 'init', '-q', '-b', 'main')
    git(repo, 'config', 'user.name', 'Synthetic Study')
    git(repo, 'config', 'user.email', 'study@example.invalid')
    git(repo, 'config', 'commit.gpgsign', 'false')
    git(repo, 'add', '.')
    git(repo, 'commit', '-qm', 'Synthetic approved input')
    if arm == 'skill':
        shutil.copytree(skill_root, run / 'skill', ignore=shutil.ignore_patterns('__pycache__'))
    elif arm == 'protocol':
        shutil.copy2(skill_root / 'references/reviewer-protocol.md', run / 'protocol.md')
    before = inventory(repo)
    prompt = prompt_for(run, arm, stage)
    (run / 'prompt.txt').write_text(prompt)
    if engine in MODELS:
        cmd, env = codex_prepare(run, repo, prompt, arm, engine)
    else:
        module = __import__(engine + '_adapter')
        cmd, env = module.prepare(run, repo, prompt, arm)
    env.update(PRE_SDD_REVIEW_HOME=str(run / 'evidence'), PYTHONDONTWRITEBYTECODE='1')
    meta = {'cell': name, 'engine': engine, 'case': case, 'arm': arm, 'rep': rep,
            'stage': stage, 'input_hashes': before, 'head_start': git(repo, 'rev-parse', 'HEAD'),
            'skill_sha256': sha(run / 'skill/SKILL.md') if arm == 'skill' else None,
            'protocol_sha256': (sha(run / 'protocol.md') if arm == 'protocol' else
                                sha(run / 'skill/references/reviewer-protocol.md')
                                if arm == 'skill' else None),
            'started_unix': time.time()}
    (run / 'meta.json').write_text(json.dumps(meta, indent=2))
    timeout = False
    with (run / 'stdout.jsonl').open('w') as out, (run / 'stderr.txt').open('w') as err:
        process = subprocess.Popen(cmd, cwd=repo, env=env, stdout=out, stderr=err,
                                   stdin=subprocess.DEVNULL, start_new_session=True)
        (run / 'pid').write_text(str(process.pid))
        try:
            rc = process.wait(timeout=900)
        except subprocess.TimeoutExpired:
            timeout = True
            os.killpg(process.pid, signal.SIGTERM)
            try:
                rc = process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                rc = process.wait()
    extract_reply(run, engine)
    after = inventory(repo)
    result = dict(meta, seconds=round(time.time()-meta['started_unix'], 3),
                  returncode=rc, timeout=timeout,
                  head_end=git(repo, 'rev-parse', 'HEAD'),
                  changed_paths=sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k)),
                  final_hashes=after,
                  adapter=codex_parse(run) if engine in MODELS else module.parse(run))
    (run / 'result.json').write_text(json.dumps(result, indent=2))
    return {'cell': name, 'seconds': result['seconds'], 'returncode': rc,
            'timeout': timeout, 'changed_paths': result['changed_paths']}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--engine', choices=['sol', 'astra', 'grok', 'claude'], required=True)
    ap.add_argument('--stage', choices=['discovery', 'repeat', 'protocol', 'repair'], default='discovery')
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--parallel', type=int, default=2)
    ap.add_argument('--skill-root', type=Path, default=PRODUCT)
    a = ap.parse_args()
    output = a.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if a.stage == 'discovery':
        jobs = [(c, arm, 1, 'discovery') for c in 'abcd' for arm in ['plain', 'skill']]
    elif a.stage == 'repeat':
        jobs = [(c, arm, 2, 'discovery') for c in 'ad' for arm in ['plain', 'skill']]
    elif a.stage == 'protocol':
        jobs = [(c, 'protocol', 1, 'discovery') for c in 'ad']
    else:
        jobs = [('b', arm, 1, 'repair') for arm in ['plain', 'skill']]
    random.Random(1008).shuffle(jobs)
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.parallel) as pool:
        futures = [pool.submit(execute, output, a.engine, *job, a.skill_root.resolve()) for job in jobs]
        for future in concurrent.futures.as_completed(futures):
            print(json.dumps(future.result()), flush=True)


if __name__ == '__main__':
    main()
