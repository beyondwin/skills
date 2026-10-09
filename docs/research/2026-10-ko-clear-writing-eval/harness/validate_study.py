#!/usr/bin/env python3
"""Validate study accounting and frozen input integrity without providers."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    protocol = json.loads((ROOT / 'protocol.json').read_text())
    for name, key in [('cases.json', 'cases_sha256'), ('core-candidate.txt', 'core_sha256')]:
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == protocol[key], name
    cases = json.loads((ROOT / 'cases.json').read_text())
    assert len(cases) == len({r['id'] for r in cases}) == 8
    live = json.loads((ROOT / 'live-results.json').read_text())
    runs = live['runs']
    assert len(runs) == live['dispatches'] == 72
    assert len({(r['host'], r['case'], r['condition']) for r in runs}) == 72
    completed = [r for r in runs if r['status'] == 'completed']
    assert len(completed) == live['completed'] == 71
    assert len({r['grade_id'] for r in completed}) == 71
    for r in completed:
        assert r['actual_models'] and r['tool_events'] == 0
        assert len(r['response_sha256']) == len(r['prompt_sha256']) == 64
        assert type(r['semantic_pass']) is bool and type(r['format_pass']) is bool
        assert r['clarity'] in (0, 1, 2) and r['overhead'] in (0, 1, 2)
        if r['case'] == 'json':
            assert r['json_shape_check'] == 'passed'
    for group in live['groups']:
        rows = [r for r in completed if r['host'] == group['host'] and r['condition'] == group['condition']]
        assert len(rows) == group['completed']
        assert sum(r['semantic_pass'] for r in rows) == group['semantic_pass']
        assert sum(r['primary_pass'] for r in rows) == group['primary_pass']
        assert sum(r['format_pass'] for r in rows) == group['format_pass']
        matched = [r for r in rows if r['case'] in group['matched_cases']]
        assert len(matched) == group['matched_n']
        assert sum(r['output_characters'] for r in matched) == group['matched_output_characters']
    offline = json.loads((ROOT / 'offline-results.json').read_text())
    assert len(offline['probes']) == len({r['id'] for r in offline['probes']}) == 15
    assert offline['policy']['source_tool_hashes_unchanged']
    assert sum(r['classification'] == 'positive_control' for r in offline['probes']) == 4
    assert sum(r['classification'] == 'defect' for r in offline['probes']) == 8
    assert all(r['expectation_met'] for r in offline['probes'] if r['classification'] == 'positive_control')
    print('PASS: frozen inputs, 72 dispatches / 71 grades, matched denominators, JSON checks and 15 offline probes')


if __name__ == '__main__':
    main()
