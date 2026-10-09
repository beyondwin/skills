#!/usr/bin/env python3
"""Validate private external receipts and export only aggregate evidence."""
import argparse
import json
from pathlib import Path
import harness as h
from summarize import json_response


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('archive',type=Path);ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args();root=args.archive
    protocol=json.loads((h.ROOT/'external-protocol.json').read_text())
    assert h.manifest(h.PAYLOAD)==protocol['candidate_sha256']
    assert h.digest(h.ROOT/'external.py')==protocol['runner_sha256']
    assert h.digest(h.ROOT/'cases.json')==protocol['cases_sha256']
    amendment=json.loads((h.ROOT/'external-followup.json').read_text())
    assert h.digest(h.ROOT/'external_followup.py')==amendment['runner_sha256']
    ledger=json.loads((root/'dispatches.json').read_text());assert len(ledger)==len(set(ledger))<=40
    mapping=json.loads((root/'judge-mapping.json').read_text()) if (root/'judge-mapping.json').exists() else {}
    rows=[];judges=[];controls=[]
    for job in ledger:
        d=root/job;v=json.loads((d/'summary.json').read_text())
        assert v['job_id']==job
        assert h.digest(root/'prompts'/(job+'.txt'))==v['prompt_sha256']
        assert h.digest(d/'response.txt')==v['response_sha256']
        assert not(d/'home/.cursor/auth.json').exists()
        row={k:v.get(k) for k in ('job_id','host','case','arm','kind','status','actual_model','actual_effort','actual_model_identity_evidence','requested_model','requested_effort','wall_seconds','tool_calls','tool_event_count','prompt_sha256','response_sha256','response_characters','receipt_prompt_matches_except_terminal_newline')}
        for name in ('stdout.jsonl','stream.jsonl'):
            if (d/name).exists():row['receipt_sha256']=h.digest(d/name)
        row['usage']=v.get('usage');row['cost_usd_estimate']=v.get('cost_usd')
        if v['host']=='opus':
            assert not v.get('init_tools') and not v.get('init_skills') and not v.get('init_mcp_servers')
        rows.append(row)
        if v['kind'] in ('judge','control') and v['status']=='ok':
            data=json_response(d/'response.txt')
            labels='AB' if v['kind']=='judge' else 'ABC'
            assert set(data['drafts'])==set(labels)
            assert data['preferred'] and set(data['preferred'])<=set(labels)
            for draft in data['drafts'].values():
                assert set(draft['scores'])=={'orientation','connections','naturalness','economy'}
                assert all(type(s)==int and 1<=s<=4 for s in draft['scores'].values())
                assert len(draft['answers'])==3
            item={'job_id':job,'scores':{k:x['scores'] for k,x in data['drafts'].items()},'error_counts':{k:len(x['material_errors']) for k,x in data['drafts'].items()},'preferred':data['preferred'],'response_sha256':v['response_sha256']}
            if v['kind']=='judge':
                item['mapping']=mapping[job]
                item['preferred_arms']=[mapping[job][x] for x in data['preferred']]
                judges.append(item)
            else:
                item['detects_factual_mutation']=len(data['drafts']['B']['material_errors'])>0
                item['detects_repetition']=data['drafts']['C']['scores']['economy']<3
                controls.append(item)
    result={'dispatch_count':len(rows),'completed':sum(r['status']=='ok' for r in rows),'protocol_sha256':h.digest(h.ROOT/'external-protocol.json'),'followup_sha256':h.digest(h.ROOT/'external-followup.json'),'runs':rows,'judgments':judges,'controls':controls}
    args.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('runs','judgments','controls')}))

if __name__=='__main__':main()
