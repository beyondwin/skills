#!/usr/bin/env python3
"""Reproduce sanitized facts and masked scores from the private archive. No live calls."""
import argparse
import json
from pathlib import Path
import harness as h


def json_response(p):
    s=p.read_text().strip()
    if s.startswith('```'):
        s=s[s.index('\n')+1:s.rfind('```')]
    return json.loads(s)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('archive',type=Path)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    protocol=json.loads((h.ROOT/'protocol.json').read_text())
    assert h.manifest(h.PAYLOAD)==protocol['candidate_sha256']
    assert h.manifest(h.PREVIOUS)==protocol['previous_sha256']
    for file in ('cases.json','harness.py','study.py'):
        key={'cases.json':'cases_sha256','harness.py':'harness_sha256','study.py':'study_sha256'}[file]
        assert h.digest(h.ROOT/file)==protocol[key]
    ledger=json.loads((args.archive/'dispatches.json').read_text())
    assert len(ledger)==len(set(ledger))<=40
    mapping=json.loads((args.archive/'judge-mapping.json').read_text()) if (args.archive/'judge-mapping.json').exists() else {}
    rows=[]
    judgments=[]
    for job in ledger:
        d=args.archive/job
        row=json.loads((d/'result.json').read_text())
        assert row['id']==job
        assert h.digest(d/'prompt.txt')==row['prompt_sha256']
        if row['response_sha256']:
            assert h.digest(d/'response.txt')==row['response_sha256']
        assert not (d/'home/.codex/auth.json').exists()
        calls=[]
        rollouts={}
        for p in (d/'home/.codex/sessions').glob('**/*.jsonl'):
            rollouts[str(p.relative_to(d))]=h.digest(p)
            for line in p.read_text().splitlines():
                e=json.loads(line)
                if e.get('type')=='response_item' and e['payload'].get('type') in ('function_call','custom_tool_call'):
                    calls.append(e['payload'])
        row['rollout_sha256']=rollouts
        row['rollout_tool_call_count']=len(calls)
        row['response_characters']=len((d/'response.txt').read_text()) if (d/'response.txt').exists() else 0
        serialized=json.dumps(calls,ensure_ascii=False)
        row['skill_read_evidence']='ko-technical-writing/SKILL.md' in serialized
        row['documents_read_evidence']='references/documents.md' in serialized
        row['payload_in_home_sha256']=h.manifest(d/'home/.codex/skills/ko-technical-writing') if (d/'home/.codex/skills/ko-technical-writing').exists() else None
        if row['arm'] in ('candidate','installed'):
            assert row['payload_in_home_sha256']==protocol['candidate_sha256']
        elif row['arm']=='previous':
            assert row['payload_in_home_sha256']==protocol['previous_sha256']
        rows.append(row)
        if row['kind']=='judge' and row['status']=='completed':
            data=json_response(d/'response.txt')
            assert set(data)=={'drafts','preferred','rationale'}
            assert set(data['drafts'])==set('ABC')
            assert data['preferred'] and set(data['preferred'])<=set('ABC')
            for v in data['drafts'].values():
                assert set(v['scores'])=={'orientation','connections','naturalness','economy'}
                assert all(type(x)==int and 1<=x<=4 for x in v['scores'].values())
                assert len(v['answers'])==3
                assert isinstance(v['material_errors'],list)
            judgments.append({'job':job,'mapping':mapping[row['case']],
                              'scores':{mapping[row['case']][k]:v['scores'] for k,v in data['drafts'].items()},
                              'error_counts':{mapping[row['case']][k]:len(v['material_errors']) for k,v in data['drafts'].items()},
                              'preferred':[mapping[row['case']][k] for k in data['preferred']],
                              'raw_response_sha256':row['response_sha256']})
    result={'dispatch_count':len(ledger),'completed':sum(r['status']=='completed' for r in rows),'unchanged_workspaces':sum(r['workspace_unchanged'] for r in rows),'protocol_sha256':h.digest(h.ROOT/'protocol.json'),'runs':rows,'masked_judgments':judgments}
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('runs','masked_judgments')}))

if __name__=='__main__':
    main()
