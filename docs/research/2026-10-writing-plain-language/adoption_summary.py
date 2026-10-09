#!/usr/bin/env python3
"""Verify study receipts and compute task-level, order-concordant comparisons."""
import argparse
import collections
import json
from pathlib import Path
import statistics
import run
import adoption_run


def parse(path):
 value=path.read_text().strip()
 if value.startswith('```'):
  value='\n'.join(value.splitlines()[1:-1])
 obj=json.loads(value)
 assert set(obj)=={'drafts','preferred','reason'}
 assert set(obj['drafts'])==set('AB')
 for d in obj['drafts'].values():
  assert set(d)=={'material_errors','reading_obstacles'}
  assert all(isinstance(d[k],list) and all(isinstance(s,str) for s in d[k]) for k in d)
 assert obj['preferred'] in ['A','B','tie'] and isinstance(obj['reason'],str)
 return obj


def preference(obj,mapping):
 if obj['preferred']=='tie':return 0
 return 1 if mapping[obj['preferred']]=='candidate' else -1


def outcome(votes):
 return 'win' if votes==[1,1] else 'loss' if votes==[-1,-1] else 'undecided'


def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('archive',type=Path);ap.add_argument('--out',type=Path,required=True)
 a=ap.parse_args();root=a.archive;run.check_freeze()
 ledger=json.loads((root/'dispatches.json').read_text())
 assert len(ledger)==len(set(ledger))<=28
 cases=json.loads((run.ROOT/'cases.json').read_text())
 new_dispatch_count=len(ledger)
 reused=[c['id']+'--previous' for c in cases]
 assert not set(reused)&set(ledger)
 ledger=ledger+reused
 rows=[];reviews={};anomalies=[]
 for job in ledger:
  d=root/job
  if not (d/'normalized.json').exists():
   anomalies.append({'id':job,'issue':'no final result'});continue
  row=json.loads((d/'normalized.json').read_text())
  assert row['id']==job
  response=d/'response.txt'
  if row['response_sha256']: assert run.h.digest(response)==row['response_sha256']
  assert not list(d.glob('home/**/auth.json'))
  if row['host']=='codex':
   receipt=json.loads((d/'result.json').read_text())
   assert run.h.digest(d/'prompt.txt')==receipt['prompt_sha256']
   assert row['status']!='ok' or row['workspace_unchanged']
   assert row['status']!='ok' or all(i=={'model':'gpt-6-astra','effort':'high'} for i in row['identity'])
  else:
   receipt=json.loads((d/'summary.json').read_text())
   request=receipt if row['host']=='opus' else json.loads((d/'request.json').read_text())
   assert run.h.digest(root/'prompts'/(job+'.txt'))==request['prompt_sha256']
   if row['host']=='opus':
    assert not receipt['tool_calls'] and not receipt['init_tools'] and not receipt['init_skills'] and not receipt['init_mcp_servers']
   else:
    assert not receipt['tool_event_count'] and receipt['receipt_prompt_matches_except_terminal_newline']
  rows.append(row)
  if row['kind']=='judge' and row['status']=='ok':
   try: obj=parse(response)
   except (ValueError,AssertionError):
    anomalies.append({'id':job,'issue':'invalid scorer JSON'});continue
   reviews[job]=(obj,row['mapping'])
 per_case=[];fidelity=[]
 for c in cases:
  votes=[]
  for order in range(2):
   item=reviews.get('judge-'+c['id']+'-'+str(order))
   votes.append(preference(*item) if item else None)
  per_case.append({'case':c['id'],'host':c['host'],'votes':votes,'outcome':outcome(votes)})
 for job,(obj,mapping) in reviews.items():
  fidelity.append({'id':job,'errors':{mapping[label]:len(d['material_errors']) for label,d in obj['drafts'].items()},'obstacles':{mapping[label]:len(d['reading_obstacles']) for label,d in obj['drafts'].items()}})
 counts=collections.Counter(r['outcome'] for r in per_case)
 secondary={}
 for host in ('codex','opus','grok'):
  for arm in run.ARMS:
   group=[r for r in rows if r['host']==host and r['arm']==arm and r['kind']=='generation' and r['status']=='ok']
   if group: secondary[host+'-'+arm]={'completed':len(group),'total_characters':sum(r['response_characters'] for r in group),'median_seconds':statistics.median(r['wall_seconds'] for r in group)}
 complete=sum(r['kind']=='generation' and r['status']=='ok' for r in rows)==12 and len(reviews)==12
 result={'dispatches':new_dispatch_count,'reused_generations':len(reused),'completed':sum(r['status']=='ok' and r['id'] not in reused for r in rows),'complete_primary_batch':complete,'comparisons':dict(counts),'preference_gate':complete and counts['win']>=4 and counts['loss']==0,'adoption':'requires author review, regression and installed smoke; not statistical superiority','per_case':per_case,'review_counts':fidelity,'secondary':secondary,'anomalies':anomalies,'runs':rows,'protocol_sha256':run.h.digest(run.ROOT/'adoption-protocol.json')}
 run.dump(a.out,result)
 print(json.dumps({k:result[k] for k in ['dispatches','completed','complete_primary_batch','comparisons','preference_gate','anomalies']},ensure_ascii=False))

if __name__=='__main__':main()
