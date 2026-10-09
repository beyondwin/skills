#!/usr/bin/env python3
"""Frozen follow-up: uniform Grok Medium condition after the High timeout."""
import argparse
import concurrent.futures
import json
from pathlib import Path
import random
import shutil
import subprocess
import external as e
import harness as h
import study


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('phase',choices=['generate-medium','judge','control'])
    ap.add_argument('output',type=Path)
    ap.add_argument('--execute',action='store_true')
    args=ap.parse_args();root=args.output
    cases=json.loads((h.ROOT/'cases.json').read_text());jobs=[];mapping={}
    if args.phase=='generate-medium':
        for c in cases:
            for arm in ('baseline','candidate'):
                files={'notes.md':c['files']['notes.md']};task=c['prompt']
                if arm=='candidate':
                    task+='\nApply the supplied writing skill and its document reference.'
                    files={'SKILL.md':(h.PAYLOAD/'SKILL.md').read_text(),'references/documents.md':(h.PAYLOAD/'references/documents.md').read_text(),**files}
                jobs.append({'id':'grok-medium-'+c['id']+'-'+arm,'host':'grok-medium','kind':'generation','case':c['id'],'arm':arm,'prompt':e.inline(files,task)})
    elif args.phase=='judge':
        for host,other in [('opus','grok-medium'),('grok-medium','opus')]:
            for n,c in enumerate(cases):
                arms=['baseline','candidate']
                if (n+(host=='grok-medium'))%2:arms.reverse()
                job_id=host+'-judge-'+c['id'];mapping[job_id]={'generator':other,**dict(zip('AB',arms))}
                files={'source.md':c['files']['notes.md'],'request.txt':c['prompt'],'questions.json':json.dumps([q['q'] for q in c['questions']],ensure_ascii=False)}
                for label,arm in zip('AB',arms):
                    files[label+'.txt']=(root/(other+'-'+c['id']+'-'+arm)/'response.txt').read_text()
                    assert files[label+'.txt']
                rubric=study.RUBRIC.replace('three anonymous','two anonymous').replace('A.txt/B.txt/C.txt','A.txt/B.txt').replace(',"C":{...}','')
                jobs.append({'id':job_id,'host':host,'kind':'judge','case':c['id'],'arm':'masked','prompt':e.inline(files,rubric)})
        (root/'judge-mapping.json').write_text(json.dumps(mapping,indent=2))
    else:
        jobs=e.prepare('control',root)
        for job in jobs:
            job['prompt']=Path(job['prompt_path']).read_text()
            if job['host']=='grok':job['host']='grok-medium';job['id']=job['id'].replace('grok-','grok-medium-',1)
    for job in jobs:
        p=root/'prompts'/(job['id']+'.txt');p.write_text(job.pop('prompt'))
        job.update(prompt_path=str(p),prompt_sha256=h.digest(p))
    (root/(args.phase+'-followup-jobs.json')).write_text(json.dumps(jobs,indent=2))
    if not args.execute:print(json.dumps({'jobs':len(jobs),'live_calls':0}));return
    amendment=json.loads((h.ROOT/'external-followup.json').read_text())
    assert h.digest(h.ROOT/'external_followup.py')==amendment['runner_sha256']
    p=json.loads((h.ROOT/'external-protocol.json').read_text())
    assert h.manifest(h.PAYLOAD)==p['candidate_sha256']
    assert h.digest(h.ROOT/'cases.json')==p['cases_sha256']
    ledger=root/'dispatches.json';done=json.loads(ledger.read_text())
    assert len(done)+len(jobs)<=40 and not(set(done)&{j['id'] for j in jobs})
    random.Random(8091).shuffle(jobs);ledger.write_text(json.dumps(done+[j['id'] for j in jobs],indent=2))
    opus=e.module('opus_runner');grok=e.module('grok_runner');grok.MODEL='grok-4.7-medium'
    credentials={}
    for key,service in (('accessToken','cursor-access-token'),('refreshToken','cursor-refresh-token')):
        credentials[key]=subprocess.run(['security','find-generic-password','-a','cursor-user','-s',service,'-w'],capture_output=True,text=True,check=True).stdout.strip()
    def run(job):
        try:
            row=opus.run_job(job,root,'claude',300) if job['host']=='opus' else grok.run_job(job,root,shutil.which('cursor-agent'),credentials)
        finally:
            auth=root/job['id']/'home/.cursor/auth.json'
            if auth.exists():auth.unlink()
        row.update(case=job['case'],arm=job['arm'],kind=job['kind'],host=job['host'],prompt_sha256=job['prompt_sha256'])
        row.update(response_sha256=h.digest(Path(row['response_path'])),response_characters=len(Path(row['response_path']).read_text()))
        (root/job['id']/'summary.json').write_text(json.dumps(row,indent=2))
        print(json.dumps({'id':job['id'],'status':row['status'],'seconds':row['wall_seconds']}),flush=True)
        return row
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(run,jobs))

if __name__=='__main__':main()
