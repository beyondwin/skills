#!/usr/bin/env python3
"""Audit frozen resources and distinct CLI dispatches; never calls a provider."""
import argparse
import collections
import json
from pathlib import Path
import run

PHASES = [
    ('0.4.0', 'candidate', 'protocol.json', 'ko_writing_plain_language_20261009'),
    ('0.4.1', 'revision', 'revision-protocol.json', 'ko_writing_plain_language_revision_20261009'),
    ('0.4.2', 'final-candidate', 'final-protocol.json', 'ko_writing_plain_language_final_20261009'),
    ('0.4.3', 'adoption-candidate', 'adoption-protocol.json', 'ko_writing_plain_language_adoption_20261009'),
    ('0.5.0', 'personal-candidate', 'personal-protocol.json', 'ko_writing_plain_language_personal_20261009'),
    ('0.5.1', 'validated-candidate', 'native-protocol.json', 'ko_writing_plain_language_native_20261009')]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('archive_parent', type=Path)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    phases, native, kinds = [], [], collections.Counter()
    for version, payload, protocol_name, archive_name in PHASES:
        protocol = json.loads((run.ROOT/protocol_name).read_text())
        candidate = run.ROOT/payload/'ko-technical-writing'
        assert run.h.manifest(candidate) == protocol['candidate']
        assert run.h.manifest(run.INCUMBENT) == protocol['incumbent']
        for name, sha in protocol['files'].items():
            assert run.h.digest(run.ROOT/name) == sha, name
        root = args.archive_parent/archive_name
        ledger = json.loads((root/'dispatches.json').read_text())
        assert len(ledger) == len(set(ledger)) <= protocol['call_cap']
        completed = 0
        for job in ledger:
            d = root/job
            row = json.loads((d/'normalized.json').read_text())
            assert row['id'] == job
            assert not list(d.glob('home/**/auth.json'))
            if row['response_sha256']:
                assert run.h.digest(d/'response.txt') == row['response_sha256']
            completed += row['status'] == 'ok'
            kinds[row['kind']] += 1
            if row['host'] != 'codex':
                continue
            assert row['workspace_unchanged']
            assert row['identity'] and all(i == {'model': 'gpt-6-astra', 'effort': 'high'} for i in row['identity'])
            skill = d/'home/.codex/skills/ko-technical-writing'
            reads = {}
            commands = json.loads((d/'commands.json').read_text())
            if row['arm'] == 'baseline':
                assert not skill.exists()
            else:
                expected = run.INCUMBENT if row['arm'] == 'previous' else candidate
                assert run.h.manifest(skill) == run.h.manifest(expected)
                reference = 'references/change-messages.md' if row['case'] in ('regression-commit', 'regression-submodule') else 'references/documents.md'
                for name in ('SKILL.md', reference):
                    path = skill/name
                    reads[name] = any(str(path) in c['command'] and c.get('exit_code') == 0
                                      and path.read_text().strip() in c.get('aggregated_output', '')
                                      for c in commands)
            assert not any('superpowers' in c['command'].lower() for c in commands)
            native.append(dict(version=version, id=job, skill_reads=reads, workspace_unchanged=True))
        phases.append(dict(version=version, dispatches=len(ledger), completed=completed,
                           protocol_sha256=run.h.digest(run.ROOT/protocol_name)))
    assert all(all(r['skill_reads'].values()) for r in native)
    result = dict(phases=phases, total_dispatches=sum(p['dispatches'] for p in phases),
                  total_completed=sum(p['completed'] for p in phases), kinds=dict(kinds),
                  unique_source_tasks=8, native_runs=len(native), native=native,
                  all_frozen_files_match=True, all_copied_auth_removed=True,
                  all_native_workspaces_unchanged=True, all_required_skill_reads_observed=True,
                  scope='Distinct CLI dispatches, not independent tasks or HTTP/model-request count. Reused incumbent directories are not counted again.')
    run.dump(args.out, result)
    print(json.dumps({k: v for k, v in result.items() if k != 'native'}))


if __name__ == '__main__':
    main()
