#!/usr/bin/env python3
"""Read-only native instruction and workspace audit; no provider calls."""
import argparse
import json
from pathlib import Path
import run
import sys
if sys.argv[1] == "0.4.2":
 import final_run
else:
 import adoption_run
del sys.argv[1]


def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('archive',type=Path);ap.add_argument('--out',type=Path,required=True)
 a=ap.parse_args();rows=[]
 for p in sorted(a.archive.glob('*/normalized.json')):
  row=json.loads(p.read_text())
  if row['host']!='codex':continue
  d=p.parent.resolve();config=d/'home/.codex';commands=json.loads((d/'commands.json').read_text())
  full_calls=[]
  for transcript in config.glob('sessions/**/*.jsonl'):
   for line in transcript.read_text().splitlines():
    try:e=json.loads(line)
    except ValueError:continue
    payload=e.get('payload',{})
    if e.get('type')=='response_item' and payload.get('type') in ('custom_tool_call','function_call'):
     full_calls.append(payload.get('input',payload.get('arguments','')))
  skill=config/'skills/ko-technical-writing'
  expected=run.CANDIDATE if row['arm'] in ('candidate','installed') else run.INCUMBENT
  reads={}
  if row['arm']!='baseline':
   assert run.h.manifest(skill)==run.h.manifest(expected)
   for rel in ['SKILL.md','references/change-messages.md' if row['case'] in ['regression-commit','regression-submodule'] else 'references/documents.md']:
    path=skill/rel;content=path.read_text()
    # Successful stdout must contain the actual resource, not merely a path mention.
    reads[rel]=any(str(path) in c['command'] and c.get('exit_code')==0 and content.strip() in c.get('aggregated_output','') for c in commands)
  else: assert not skill.exists()
  rows.append({'id':row['id'],'workspace_unchanged':row['workspace_unchanged'],'native_reads':reads,'recorded_tool_calls':len(full_calls),'stdout_command_count':len(commands),'auth_removed':not(config/'auth.json').exists(),'superpowers_present':any('superpowers' in str(p).lower() for p in (config/'skills').rglob('*'))})
 run.dump(a.out,{'runs':rows,'all_workspaces_unchanged':all(r['workspace_unchanged'] for r in rows),'all_required_reads_observed':all(all(r['native_reads'].values()) for r in rows),'all_auth_removed':all(r['auth_removed'] for r in rows)})
 print(json.dumps({'audited':len(rows),'missing_reads':[r['id'] for r in rows if not all(r['native_reads'].values())]}))

if __name__=='__main__':main()
