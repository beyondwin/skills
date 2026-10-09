#!/usr/bin/env python3
"""Seven-dispatch development regression; not a superiority experiment."""
import argparse
import concurrent.futures
import json
from pathlib import Path
import shutil
import subprocess
import threading
import run

REV=run.ROOT/'final-candidate/ko-technical-writing'

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('archive',type=Path);ap.add_argument('--execute',action='store_true')
 args=ap.parse_args();root=args.archive.resolve()
 assert run.h.REPO!=root and run.h.REPO not in root.parents
 root.mkdir(parents=True,exist_ok=True)
 p=json.loads((run.ROOT/'final-repair-protocol.json').read_text())
 assert run.h.manifest(REV)==p['payload']
 for name,sha in p['files'].items():assert run.h.digest(run.ROOT/name)==sha
 cases=json.loads((run.ROOT/'revision-cases.json').read_text())
 jobs=[]
 for c in cases:
  for host in ['codex','opus','grok']:
   jobs.append((dict(c,id=c['id']+'-'+host),host))
 old=json.loads((run.ROOT.parent/'2026-10-personal-writing-pilot/cases.json').read_text())
 for c in old:
  if c['id'] in ['json']:jobs.append((dict(c,id='regression-'+c['id']), 'codex'))
 if not args.execute:print(json.dumps({'jobs':len(jobs),'live_calls':0}));return
 assert not (root/'dispatches.json').exists()
 lock=threading.Lock();ledger=[]
 opus=run.e.module('opus_runner');grok=run.e.module('grok_runner');grok.MODEL='grok-4.7-medium';grok.TIMEOUT=480
 run.h.PAYLOAD=REV
 credentials={}
 for key,service in [('accessToken','cursor-access-token'),('refreshToken','cursor-refresh-token')]:
  credentials[key]=subprocess.run(['security','find-generic-password','-a','cursor-user','-s',service,'-w'],capture_output=True,text=True,check=True).stdout.strip()
 def execute(item):
  c,host=item;job_id=c['id']+'--candidate';folder=root/job_id
  with lock:
   ledger.append(job_id);run.dump(root/'dispatches.json',ledger)
  if host=='codex':
   row=run.h.run(c,'candidate',root,Path.home()/'.codex/auth.json');status='ok' if row['status']=='completed' else row['status'];identity=row['actual_identity']
  else:
   files={'SKILL.md':(REV/'SKILL.md').read_text(),'references/documents.md':(REV/'references/documents.md').read_text(),**c['files']}
   prompt=run.e.inline(files,c['prompt']+'\nApply the supplied writing skill and its document reference.')
   path=root/(job_id+'.prompt.txt');path.write_text(prompt)
   job={'id':job_id,'prompt_path':str(path),'prompt_sha256':run.h.digest(path)}
   try:row=opus.run_job(job,root,'claude',300) if host=='opus' else grok.run_job(job,root,shutil.which('cursor-agent'),credentials)
   finally:
    auth=folder/'home/.cursor/auth.json'
    if auth.exists():auth.unlink()
   status=row['status'];identity=row.get('actual_model',row.get('actual_model_identity_evidence'))
  result={'id':job_id,'host':host,'status':status,'identity':identity,'response_sha256':run.h.digest(folder/'response.txt') if (folder/'response.txt').exists() else None,'wall_seconds':row['wall_seconds'],'workspace_unchanged':row.get('workspace_unchanged')}
  run.dump(folder/'normalized.json',result);print(json.dumps(result),flush=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(execute,jobs))

if __name__=='__main__':main()
