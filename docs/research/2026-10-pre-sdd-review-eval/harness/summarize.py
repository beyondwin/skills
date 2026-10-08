#!/usr/bin/env python3
"""Derive non-sensitive study tables from external receipts and adjudicated grades.

No model calls. This intentionally exports no prompts, replies, session IDs,
absolute receipt paths, or credentials. Each cell's grade remains inspectable.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import statistics


def usage(row):
    a = row['adapter']
    model = row['engine']
    if model in ('sol', 'astra'):
        records = [s.get('usage') or {} for s in a['sessions']]
        identities = sorted(set(tuple(x) for s in a['sessions'] for x in s['model_effort']))
        return {'input_including_cache': sum(x.get('input_tokens', 0) for x in records),
                'cache_read': sum(x.get('cached_input_tokens', 0) for x in records),
                'output': sum(x.get('output_tokens', 0) for x in records),
                'reported_usd': None, 'observed': identities,
                'sessions': len(records), 'scope': 'sum of distinct session totals including children'}
    if model == 'claude':
        records = [s['usage']['tokens'] for s in a['transcripts']]
        identities = sorted(set((m, e) for s in a['transcripts']
                                for m in s['usage']['models'] for e in s['usage']['efforts']))
        return {'input_including_cache': sum(x.get('input_tokens', 0) +
                  x.get('cache_read_input_tokens', 0) + x.get('cache_creation_input_tokens', 0)
                  for x in records),
                'cache_read': sum(x.get('cache_read_input_tokens', 0) for x in records),
                'output': sum(x.get('output_tokens', 0) for x in records),
                'reported_usd': a.get('cost_usd'), 'observed': identities,
                'sessions': len(records), 'scope': 'message-ID-deduplicated controller and child transcripts'}
    u = a.get('usage') or {}
    return {'input_including_cache': a.get('input_total_including_cache'),
            'cache_read': u.get('cache_read_input_tokens'), 'output': u.get('output_tokens'),
            'reported_usd': a.get('total_cost_usd'), 'observed': a.get('observed_model_effort'),
            'sessions': len(a.get('sessions', [])),
            'scope': 'inclusive parent ledger; child calls audited as included, do not add child ledgers'}


def summarize(root):
    mapping = json.loads((root / 'blind/mapping-private.json').read_text())
    grades = json.loads((root / 'blind/grades.json').read_text())
    reverse = {name: key for key, name in mapping.items()}
    oracle = json.loads(Path(__file__).with_name('oracle.json').read_text())
    cells = []
    for path in sorted((root / 'cells').glob('*/result.json')):
        row = json.loads(path.read_text())
        grade = grades.get(reverse.get(row['cell']))
        cell = {k: row[k] for k in ('cell', 'engine', 'case', 'arm', 'rep', 'stage',
                'seconds', 'returncode', 'timeout', 'changed_paths', 'skill_sha256', 'protocol_sha256')}
        if row['arm'] == 'skill':
            protocol = path.parent / 'skill/references/reviewer-protocol.md'
            cell['protocol_sha256'] = hashlib.sha256(protocol.read_bytes()).hexdigest()
        cell.update(usage=usage(row), grade=grade,
                    completed=row['returncode'] == 0 and not row['timeout'],
                    head_preserved=row['head_start'] == row['head_end'])
        cells.append(cell)
    groups = defaultdict(list)
    for cell in cells:
        groups[(cell['engine'], cell['arm'], cell['stage'])].append(cell)
    summaries = []
    for (engine, arm, stage), rows in sorted(groups.items()):
        costs = [r['usage']['reported_usd'] for r in rows]
        completed = [r for r in rows if r['completed']]
        scored = [r for r in completed if r['grade'] is not None and r['grade'].get('scorable', True)]
        grading_complete = len(scored) == len(completed)
        summaries.append({'engine': engine, 'arm': arm, 'stage': stage, 'n': len(rows),
            'completed': len(completed),
            'scored_completed': len(scored),
            'grading_complete_for_completed': grading_complete,
            'quality_observed': grading_complete and bool(scored),
            'median_seconds_completed': round(statistics.median(r['seconds'] for r in completed), 3) if completed else None,
            'min_seconds': min(r['seconds'] for r in rows),
            'max_seconds': max(r['seconds'] for r in rows),
            'reported_usd_sum': round(sum(costs), 6) if all(c is not None for c in costs) else None,
            'known_defects_found_completed': sum(len(r['grade'].get('known_defects_found', [])) for r in scored) if grading_complete and scored else None,
            'known_defect_opportunities_scored': sum(len(oracle[r['case']]['defects']) for r in scored),
            'material_fp_completed': sum(len(r['grade'].get('fp_material', [])) for r in scored) if grading_complete and scored else None,
            'ungraded': sum(r['grade'] is None for r in rows)})
    return {'cells': cells, 'groups': summaries}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('external_root', type=Path)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    args.output.write_text(json.dumps(summarize(args.external_root), indent=2, ensure_ascii=False) + '\n')
