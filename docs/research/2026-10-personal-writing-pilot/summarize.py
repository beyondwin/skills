#!/usr/bin/env python3
"""Rebuild public aggregates from a private archive and explicit author grades."""
import argparse
import json
from pathlib import Path
import statistics

import harness


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('archive', type=Path)
    args = ap.parse_args()
    root = harness.ROOT
    protocol = json.loads((root / 'protocol.json').read_text())
    assert harness.manifest(harness.PAYLOAD) == protocol['payload_sha256']
    assert harness.digest(root / 'cases.json') == protocol['cases_sha256']
    assert harness.digest(root / 'harness.py') == protocol['harness_sha256']
    assert harness.manifest(harness.REPO / 'skills/korean-writing-editor') == protocol['competing_editor_sha256']
    grades = json.loads((root / 'grades.json').read_text())
    ledger = json.loads((args.archive / 'dispatches.json').read_text())
    assert len(ledger) == len(set(ledger)) <= protocol['calls']['max_total']
    cases = {c['id']: c for c in json.loads((root / 'cases.json').read_text())}
    rows = []
    for job in ledger:
        folder = args.archive / job
        row = json.loads((folder / 'result.json').read_text())
        assert row['id'] == job
        canonical_case = row['case'].removesuffix('-retry')
        case = cases[canonical_case]
        row['canonical_case'] = canonical_case
        row['retry'] = row['case'] != canonical_case
        assert row['prompt_sha256'] == harness.digest(folder / 'prompt.txt')
        assert (folder / 'prompt.txt').read_text() == case['prompt']
        commands = json.loads((folder / 'commands.json').read_text())
        row['stream_command_count'] = row.pop('command_count')
        row['rollout_tool_call_count'] = 0
        row['rollout_sha256'] = []
        for path in sorted((folder / 'home/.codex/sessions').rglob('*.jsonl')):
            row['rollout_sha256'].append(harness.digest(path))
            for line in path.read_text().splitlines():
                event = json.loads(line)
                if (event.get('type') == 'response_item' and
                        event.get('payload', {}).get('type') in ('custom_tool_call', 'function_call')):
                    row['rollout_tool_call_count'] += 1
        output = '\n'.join(c.get('aggregated_output', '') for c in commands
                           if c.get('exit_code') == 0)
        row['candidate_read'] = '# Korean Technical Writing\n' in output
        heading = ('# Commit messages and PR descriptions' if case.get('reference') == 'change-messages.md'
                   else '# Documents, runbooks and engineering handoffs')
        row['reference_read'] = heading in output if case['kind'] == 'positive' else None
        row['grade'] = grades[job]
        if row['status'] == 'completed':
            response = (folder / 'response.txt').read_text()
            assert row['response_sha256'] == harness.digest(folder / 'response.txt')
            row['output_characters'] = len(response)
            assert row['actual_identity']
            assert row['grade']['semantic_pass'] is not None
            if canonical_case == 'json':
                parsed = json.loads(response)
                row['json_shape_pass'] = (set(parsed) == {'summary', 'measured_ms', 'deployed', 'next_action'}
                                          and parsed['measured_ms'] is None and parsed['deployed'] is False
                                          and isinstance(parsed['summary'], str)
                                          and isinstance(parsed['next_action'], str))
            row['primary_pass'] = all((row['grade']['semantic_pass'], row['grade']['format_pass'],
                                       row['grade']['scope_pass'], row['workspace_unchanged'],
                                       row.get('json_shape_pass', True)))
        else:
            assert row['grade']['semantic_pass'] is None
            row['primary_pass'] = None
        rows.append(row)
    assert set(grades) == set(ledger)
    groups = []
    for arm in ['baseline', 'candidate']:
        group = [r for r in rows if r['arm'] == arm and r['kind'] == 'positive']
        complete = [r for r in group if r['status'] == 'completed']
        groups.append({'arm': arm, 'dispatches': len(group), 'completed': len(complete),
                       'primary_pass': sum(r['primary_pass'] for r in complete),
                       'median_seconds': statistics.median(r['wall_seconds'] for r in complete) if complete else None,
                       'output_characters': sum(r['output_characters'] for r in complete),
                       'input_tokens': sum(u.get('input_tokens', 0) for r in complete for u in r['usage']),
                       'cached_input_tokens': sum(u.get('cached_input_tokens', 0) for r in complete for u in r['usage']),
                       'output_tokens': sum(u.get('output_tokens', 0) for r in complete for u in r['usage'])})
    positives = [r for r in rows if r['arm'] == 'candidate' and r['kind'] == 'positive']
    negatives = [r for r in rows if r['kind'] == 'negative' and r['status'] == 'completed']
    gate = (len(positives) == 8 and all(r['primary_pass'] and r['candidate_read'] and r['reference_read']
                                     and r['grade']['source_read_verified'] for r in positives)
            and {r['canonical_case'] for r in negatives} == {c['id'] for c in cases.values() if c['kind'] == 'negative'}
            and all(not r['candidate_read'] and r['primary_pass'] for r in negatives))
    result = {'date': '2026-10-09', 'dispatches': len(rows),
              'completed': sum(r['status'] == 'completed' for r in rows),
              'personal_pilot_gate_pass': gate, 'semantic_reviewer': 'author; not independent',
              'groups': groups, 'runs': rows}
    (root / 'results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'runs'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
