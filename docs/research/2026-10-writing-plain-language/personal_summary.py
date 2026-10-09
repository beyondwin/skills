#!/usr/bin/env python3
"""Receipt audit for personal-use acceptance, not pairwise preference scoring."""
import argparse
import json
from pathlib import Path
import run
import personal_run


def parse(path):
    value = path.read_text().strip()
    if value.startswith('```'):
        value = '\n'.join(value.splitlines()[1:-1])
    obj = json.loads(value)
    assert set(obj) == {'material_errors', 'reading_obstacles', 'verdict', 'reason'}
    assert obj['verdict'] in ('pass', 'needs_revision')
    assert isinstance(obj['reason'], str)
    for item in obj['material_errors']:
        assert set(item) == {'phrase', 'source_basis', 'effect'}
        assert all(isinstance(v, str) for v in item.values())
    for item in obj['reading_obstacles']:
        assert set(item) == {'phrase', 'effect', 'severity'}
        assert all(isinstance(v, str) for v in item.values())
        assert item['severity'] in ('blocking', 'minor')
    assert isinstance(obj['material_errors'], list)
    assert isinstance(obj['reading_obstacles'], list)
    return obj


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('archive', type=Path)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    root = args.archive
    run.check_freeze()
    ledger = json.loads((root/'dispatches.json').read_text())
    assert len(ledger) == len(set(ledger)) <= 20
    rows, reviews, anomalies = [], [], []
    for job in ledger:
        d = root/job
        if not (d/'normalized.json').exists():
            anomalies.append({'id': job, 'issue': 'no final result'})
            continue
        row = json.loads((d/'normalized.json').read_text())
        assert row['id'] == job
        if row['response_sha256']:
            assert run.h.digest(d/'response.txt') == row['response_sha256']
        assert not list(d.glob('home/**/auth.json'))
        if row['host'] == 'codex':
            receipt = json.loads((d/'result.json').read_text())
            assert run.h.digest(d/'prompt.txt') == receipt['prompt_sha256']
            assert row['status'] != 'ok' or row['workspace_unchanged']
            assert row['identity']
            assert all(i == {'model': 'gpt-6-astra', 'effort': 'high'} for i in row['identity'])
        else:
            receipt = json.loads((d/'summary.json').read_text())
            request = receipt if row['host'] == 'opus' else json.loads((d/'request.json').read_text())
            assert run.h.digest(root/'prompts'/(job+'.txt')) == request['prompt_sha256']
            if row['host'] == 'opus':
                assert not receipt['tool_calls'] and not receipt['init_tools']
                assert not receipt['init_skills'] and not receipt['init_mcp_servers']
            else:
                assert not receipt['tool_event_count']
                assert receipt['receipt_prompt_matches_except_terminal_newline']
        rows.append(row)
        if row['kind'] == 'review' and row['status'] == 'ok':
            try:
                review = parse(d/'response.txt')
            except (ValueError, AssertionError):
                anomalies.append({'id': job, 'issue': 'invalid audit schema'})
            else:
                reviews.append(dict(id=job, **review))
    result = {
        'dispatches': len(ledger), 'completed': sum(r['status'] == 'ok' for r in rows),
        'reviews_received': len(reviews),
        'model_audit_passes': sum(r['verdict'] == 'pass' for r in reviews),
        'model_material_error_reports': sum(len(r['material_errors']) for r in reviews),
        'model_blocking_obstacles': sum(sum(i['severity'] == 'blocking' for i in r['reading_obstacles']) for r in reviews),
        'acceptance': 'Requires source adjudication, native regressions and installed smoke; not comparative superiority.',
        'reviews': reviews, 'anomalies': anomalies, 'runs': rows,
        'protocol_sha256': run.h.digest(run.ROOT/'personal-protocol.json')}
    run.dump(args.out, result)
    print(json.dumps({k: result[k] for k in ('dispatches', 'completed', 'reviews_received', 'model_audit_passes', 'model_material_error_reports', 'model_blocking_obstacles', 'anomalies')}))


if __name__ == '__main__':
    main()
