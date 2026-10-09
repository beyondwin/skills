#!/usr/bin/env python3
"""Reproduce 0.2.2 native/inline run evidence and deterministic JSON checks."""
import argparse
import json
from pathlib import Path
import harness as h


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('archive',type=Path);ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args();root=args.archive
    p=json.loads((h.ROOT/'final-protocol.json').read_text())
    assert h.manifest(h.ROOT/'final-candidate/ko-technical-writing')==p['payload_sha256']
    assert h.digest(h.ROOT/'final_round.py')==p['runner_sha256']
    assert h.digest(h.ROOT/'repair-cases.json')==p['cases_sha256']
    ledger=json.loads((root/'dispatches.json').read_text());assert len(ledger)==len(set(ledger))<=10
    rows=[]
    for job in ledger:
        row=json.loads((root/(job+'.result.json')).read_text());d=root/row['folder']
        if row['response_sha256']:assert h.digest(d/'response.txt')==row['response_sha256']
        assert not(d/'home/.codex/auth.json').exists() and not(d/'home/.cursor/auth.json').exists()
        row['response_characters']=len((d/'response.txt').read_text()) if (d/'response.txt').exists() else 0
        receipts={};calls=[]
        if row['host'] in ('codex','installed'):
            detail=json.loads((d/'result.json').read_text());row['workspace_unchanged']=detail['workspace_unchanged']
            assert h.manifest(d/'home/.codex/skills/ko-technical-writing')==p['payload_sha256']
            for log in (d/'home/.codex/sessions').glob('**/*.jsonl'):
                receipts[str(log.relative_to(d))]=h.digest(log)
                for line in log.read_text().splitlines():
                    e=json.loads(line)
                    if e.get('type')=='response_item' and e['payload'].get('type') in ('function_call','custom_tool_call'):calls.append(e['payload'])
            commands=json.dumps(calls)
            row['skill_read_evidence']='ko-technical-writing/SKILL.md' in commands
            row['reference_read_evidence']='references/documents.md' in commands
        else:
            detail=json.loads((d/'summary.json').read_text());row['tool_calls']=detail.get('tool_calls',detail.get('tool_event_count'))
            if row['host']=='opus':
                assert not detail.get('init_tools') and not detail.get('init_skills') and not detail.get('init_mcp_servers')
            else:assert detail['receipt_prompt_matches_except_terminal_newline']
            for name in ('stdout.jsonl','stream.jsonl'):
                if (d/name).exists():receipts[name]=h.digest(d/name)
        row['receipt_sha256']=receipts;row['usage']=detail.get('usage')
        if row['id']=='json-regression--codex' and row['status']=='completed':
            data=json.loads((d/'response.txt').read_text())
            assert set(data)=={'summary','measured_ms','deployed','next_action'}
            assert data['measured_ms'] is None and data['deployed'] is False
            assert isinstance(data['summary'],str) and isinstance(data['next_action'],str)
            row['json_contract_pass']=True
        rows.append(row)
    result={'version':'0.2.2','dispatches':len(rows),'completed':sum(r['status'] in ('ok','completed') for r in rows),'protocol_sha256':h.digest(h.ROOT/'final-protocol.json'),'runs':rows}
    args.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='runs'}))

if __name__=='__main__':main()
