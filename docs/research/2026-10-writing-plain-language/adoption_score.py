#!/usr/bin/env python3
"""Score all frozen judgments; accept structured finding text without changing votes."""
import json
import adoption_summary as summary


def parse(path):
    text = path.read_text().strip()
    if text.startswith('```'):
        text = '\n'.join(text.splitlines()[1:-1])
    obj = json.loads(text)
    assert set(obj) == {'drafts', 'preferred', 'reason'}
    assert set(obj['drafts']) == {'A', 'B'}
    assert obj['preferred'] in ('A', 'B', 'tie')
    assert isinstance(obj['reason'], str)
    for draft in obj['drafts'].values():
        assert set(draft) == {'material_errors', 'reading_obstacles'}
        for findings in draft.values():
            assert isinstance(findings, list)
            for finding in findings:
                assert isinstance(finding, str) or (
                    isinstance(finding, dict) and bool(finding)
                    and all(isinstance(k, str) and isinstance(v, str)
                            for k, v in finding.items()))
    return obj


summary.parse = parse
if __name__ == '__main__':
    summary.main()
