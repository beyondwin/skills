#!/usr/bin/env python3
"""Verify study receipts and compute task-level, order-concordant comparisons."""
import argparse
import collections
import json
import math
from pathlib import Path
import statistics
import run


def parse(path):
 value=path.read_text().strip()
 if value.startswith('```'):
  value='\n'.join(value.splitlines()[1:-1])
 obj=json.loads(value)
 assert set(obj)=={'drafts','pairs'}
 assert set(obj['drafts'])==set('ABC') and set(obj['pairs'])=={'AB','AC','BC'}
 for d in obj['drafts'].values():
  assert set(d)=={'material_errors','reading_obstacles'}
  assert all(isinstance(d[k],list) and all(isinstance(s,str) for s in d[k]) for k in d)
 for pair,p in obj['pairs'].items():
  assert set(p)=={'preferred','reason'} and p['preferred'] in list(pair)+['tie']
  assert isinstance(p['reason'],str)
 return obj


def tail(wins,losses):
 n=wins+losses
 return sum(math.comb(n,k) for k in range(wins,n+1))/(2**n) if n else 1.0


def preference(obj,mapping,other):
 labels={arm:label for label,arm in mapping.items()}
 a,b=labels['candidate'],labels[other]
 pref=obj['pairs'][''.join(sorted([a,b]))]['preferred']
 return 1 if pref==a else -1 if pref==b else 0


def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('archive',type=Path);ap.add_argument('--out',type=Path,required=True)
 a=ap.parse_args();root=a.archive;run.check_freeze()
 ledger=json.loads((root/'dispatches.json').read_text())
 assert len(ledger)==len(set(ledger))<=70
 cases=json.loads((run.ROOT/'cases.json').read_text())
 rows=[];reviews={};controls={};anomalies=[]
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
  if row['kind'] in ('judge','control') and row['status']=='ok':
   try: obj=parse(response)
   except (ValueError,AssertionError) as ex:
    anomalies.append({'id':job,'issue':'invalid scorer JSON'});continue
   if row['kind']=='judge': reviews[job]=(obj,row['mapping'])
   else:
    controls[job]={'detects_mutated_threshold':bool(obj['drafts']['B']['material_errors']),
       'prefers_faithful_to_mutated':obj['pairs']['AB']['preferred']=='A',
       'prefers_nonduplicated':obj['pairs']['AC']['preferred']=='A',
       'clean_reference':not obj['drafts']['A']['material_errors']}
 results={};per_case=[];fidelity=[]
 for c in cases:
  record={'case':c['id'],'host':c['host']}
  for other in ('baseline','previous'):
   votes=[]
   for order in range(2):
    item=reviews.get('judge-'+c['id']+'-'+str(order))
    votes.append(preference(*item,other) if item else 0)
   record[other]={'votes':votes,'outcome':'win' if votes==[1,1] else 'loss' if votes==[-1,-1] else 'tie'}
  per_case.append(record)
 for job,(obj,mapping) in reviews.items():
  fidelity.append({'id':job,'errors':{mapping[label]:len(d['material_errors']) for label,d in obj['drafts'].items()},'obstacles':{mapping[label]:len(d['reading_obstacles']) for label,d in obj['drafts'].items()}})
 for other in ('baseline','previous'):
  counts=collections.Counter(r[other]['outcome'] for r in per_case)
  p=tail(counts['win'],counts['loss'])
  results[other]={'wins':counts['win'],'losses':counts['loss'],'ties_or_missing':counts['tie'],'exact_one_sided_tail':p,'preference_gate':counts['win']>=8 and counts['win']>counts['loss'] and p<=0.025}
 secondary={}
 for host in ('codex','opus','grok'):
  for arm in run.ARMS:
   group=[r for r in rows if r['host']==host and r['arm']==arm and r['kind']=='generation' and r['status']=='ok']
   if group: secondary[host+'-'+arm]={'completed':len(group),'total_characters':sum(r['response_characters'] for r in group),'median_seconds':statistics.median(r['wall_seconds'] for r in group)}
 complete=sum(r['kind']=='generation' and r['status']=='ok' for r in rows)==36 and len(reviews)==24
 control_pass=len(controls)==2 and all(all(c.values()) for c in controls.values())
 result={'dispatches':len(ledger),'completed':sum(r['status']=='ok' for r in rows),'complete_primary_batch':complete,'controls':controls,'controls_pass':control_pass,'comparisons':results,'preference_gate':complete and control_pass and all(r['preference_gate'] for r in results.values()),'adoption':'not decided: requires source adjudication, regression and installed smoke','per_case':per_case,'review_counts':fidelity,'secondary':secondary,'anomalies':anomalies,'runs':rows,'protocol_sha256':run.h.digest(run.ROOT/'protocol.json')}
 run.dump(a.out,result)
 print(json.dumps({k:result[k] for k in ['dispatches','completed','complete_primary_batch','controls_pass','comparisons','preference_gate','anomalies']},ensure_ascii=False))

if __name__=='__main__':main()
