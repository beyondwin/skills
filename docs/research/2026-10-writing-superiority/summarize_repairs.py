#!/usr/bin/env python3
"""Export verified repair metadata and author grades, without raw provider text."""
import argparse
import json
from pathlib import Path
import run


def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('archive',type=Path);ap.add_argument('protocol',type=Path);ap.add_argument('grades',type=Path);ap.add_argument('--out',type=Path,required=True)
 a=ap.parse_args();root=a.archive;p=json.loads(a.protocol.read_text());grades=json.loads(a.grades.read_text())
 for name,sha in p['files'].items():assert run.h.digest(run.ROOT/name)==sha
 ledger=json.loads((root/'dispatches.json').read_text());assert len(ledger)==len(set(ledger))<=p['dispatch_cap']
 assert set(grades)==set(ledger)
 rows=[]
 for job in ledger:
  d=root/job;row=json.loads((d/'normalized.json').read_text());assert row['id']==job
  response=d/'response.txt';assert row['response_sha256']==run.h.digest(response)
  assert not list(d.glob('home/**/auth.json'))
  reads={}
  if row['host']=='codex':
   config=d/'home/.codex';skill=config/'skills/ko-technical-writing'
   assert run.h.manifest(skill)==p['payload']
   receipt=json.loads((d/'result.json').read_text());assert run.h.digest(d/'prompt.txt')==receipt['prompt_sha256']
   assert row['status']!='ok' or row['workspace_unchanged']
   assert row['identity'] and all(v=={'model':'gpt-6-astra','effort':'high'} for v in row['identity'])
   commands=json.loads((d/'commands.json').read_text())
   ref='references/change-messages.md' if job.startswith(('regression-commit','regression-submodule')) else 'references/documents.md'
   for rel in ['SKILL.md',ref]:
    resource=skill/rel
    reads[rel]=any(str(resource) in c['command'] and c.get('exit_code')==0 and resource.read_text().strip() in c.get('aggregated_output','') for c in commands)
   assert all(reads.values())
  else:
   receipt=json.loads((d/'summary.json').read_text())
   request=receipt if row['host']=='opus' else json.loads((d/'request.json').read_text())
   assert run.h.digest(root/(job+'.prompt.txt'))==request['prompt_sha256']
   if row['host']=='opus':assert not receipt['tool_calls'] and not receipt['init_tools'] and not receipt['init_skills'] and not receipt['init_mcp_servers']
   else:assert not receipt['tool_event_count'] and receipt['receipt_prompt_matches_except_terminal_newline']
  if job.startswith('regression-json') and row['status']=='ok':
   obj=json.loads(response.read_text());assert set(obj)=={'summary','measured_ms','deployed','next_action'}
   assert obj['measured_ms'] is None and obj['deployed'] is False
  rows.append(dict(row,native_reads=reads,author_grade=grades[job]))
 result={'dispatches':len(ledger),'completed':sum(r['status']=='ok' for r in rows),'author_passes':sum(r['status']=='ok' and r['author_grade']['pass'] for r in rows),'protocol_sha256':run.h.digest(a.protocol),'grades_sha256':run.h.digest(a.grades),'scope':'Targeted development regression, not blinded superiority or human assessment.','runs':rows}
 run.dump(a.out,result);print(json.dumps({k:result[k] for k in ['dispatches','completed','author_passes']}))

if __name__=='__main__':main()
