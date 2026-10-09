#!/usr/bin/env python3
"""0.2.1 repair validation, separate 10-dispatch cap. No live run by default."""
import argparse
import concurrent.futures
import json
from pathlib import Path
import random
import shutil
import subprocess
import harness as h
import external as e

REV=h.ROOT/'revision/ko-technical-writing'


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('phase',choices=['generate','smoke'])
    ap.add_argument('output',type=Path);ap.add_argument('--execute',action='store_true')
    ap.add_argument('--auth',type=Path)
    args=ap.parse_args();root=args.output;root.mkdir(parents=True,exist_ok=True)
    cases=json.loads((h.ROOT/'repair-cases.json').read_text());jobs=[]
    if args.phase=='generate':
        jobs=[(dict(c),host) for c in cases for host in ('codex','opus','grok-medium')]
        old=json.loads((h.ROOT/'cases.json').read_text())
        jobs.append((dict(next(c for c in old if c['id']=='measurement'),id='measurement-replay'),'opus'))
        old=json.loads((h.ROOT.parent/'2026-10-personal-writing-pilot/cases.json').read_text())
        jobs.append((dict(next(c for c in old if c['id']=='json'),id='json-regression'),'codex'))
    else:
        c=dict(cases[0],id='installed-smoke');c['prompt']='Use $ko-technical-writing. '+c['prompt'];jobs=[(c,'installed')]
    if not args.execute:print(json.dumps({'jobs':len(jobs),'live_calls':0}));return
    protocol=json.loads((h.ROOT/'repair-protocol.json').read_text())
    assert h.manifest(REV)==protocol['payload_sha256']
    assert h.digest(h.ROOT/'repair.py')==protocol['runner_sha256']
    assert h.digest(h.ROOT/'repair-cases.json')==protocol['cases_sha256']
    ledger=root/'dispatches.json';done=json.loads(ledger.read_text()) if ledger.exists() else []
    ids=[c['id']+'--'+host for c,host in jobs]
    assert not set(done)&set(ids) and len(done)+len(ids)<=10
    ledger.write_text(json.dumps(done+ids,indent=2));random.Random(901).shuffle(jobs)
    h.PAYLOAD=REV
    opus=e.module('opus_runner');grok=e.module('grok_runner');grok.MODEL='grok-4.7-medium'
    credentials={}
    if any(host=='grok-medium' for c,host in jobs):
        for key,service in (('accessToken','cursor-access-token'),('refreshToken','cursor-refresh-token')):
            credentials[key]=subprocess.run(['security','find-generic-password','-a','cursor-user','-s',service,'-w'],capture_output=True,text=True,check=True).stdout.strip()
    def run(item):
        c,host=item;job_id=c['id']+'--'+host
        if host in ('codex','installed'):
            # h.run uses arm in the folder name; keep that native identity in a map.
            c=dict(c,id=c['id']+'-'+host)
            row=h.run(c,'installed' if host=='installed' else 'candidate',root,args.auth)
            folder=root/row['id'];status=row['status'];actual=row['actual_identity']
        else:
            files={'SKILL.md':(REV/'SKILL.md').read_text(),'references/documents.md':(REV/'references/documents.md').read_text(),**c['files']}
            prompt=e.inline(files,c['prompt']+'\nApply the supplied writing skill and its document reference.')
            p=root/(job_id+'.prompt.txt');p.write_text(prompt)
            job={'id':job_id,'prompt_path':str(p),'prompt_sha256':h.digest(p)}
            try:
                row=opus.run_job(job,root,'claude',300) if host=='opus' else grok.run_job(job,root,shutil.which('cursor-agent'),credentials)
            finally:
                auth=root/job_id/'home/.cursor/auth.json'
                if auth.exists():auth.unlink()
            folder=root/job_id;status=row['status'];actual=row.get('actual_model',row.get('actual_model_identity_evidence'))
        final={'id':job_id,'folder':folder.name,'host':host,'case':c['id'],'status':status,'actual_identity':actual,'response_sha256':h.digest(folder/'response.txt') if (folder/'response.txt').exists() else None,'wall_seconds':row['wall_seconds']}
        (root/(job_id+'.result.json')).write_text(json.dumps(final,indent=2))
        print(json.dumps(final),flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(run,jobs))

if __name__=='__main__':main()
