#!/usr/bin/env python3
"""One predeclared reserve retry for a timed-out Grok final-regression job."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import harness as h
import external as e


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('output',type=Path);ap.add_argument('--execute',action='store_true');args=ap.parse_args()
    if not args.execute:print('{"jobs":1,"live_calls":0}');return
    root=args.output;job_id='replica-rejoin-retry--grok-medium';original='replica-rejoin--grok-medium'
    p=json.loads((h.ROOT/'final-protocol.json').read_text());assert h.manifest(h.ROOT/'final-candidate/ko-technical-writing')==p['payload_sha256']
    policy=json.loads((h.ROOT/'final-followup.json').read_text());assert h.digest(h.ROOT/'final_retry.py')==policy['runner_sha256']
    ledger=root/'dispatches.json';done=json.loads(ledger.read_text());assert job_id not in done and len(done)<10
    ledger.write_text(json.dumps(done+[job_id],indent=2))
    prompt=root/(original+'.prompt.txt');job={'id':job_id,'prompt_path':str(prompt),'prompt_sha256':h.digest(prompt)}
    assert job['prompt_sha256']==json.loads((root/original/'request.json').read_text())['prompt_sha256']
    grok=e.module('grok_runner');grok.MODEL='grok-4.7-medium';grok.TIMEOUT=480;credentials={}
    for key,service in (('accessToken','cursor-access-token'),('refreshToken','cursor-refresh-token')):
        credentials[key]=subprocess.run(['security','find-generic-password','-a','cursor-user','-s',service,'-w'],capture_output=True,text=True,check=True).stdout.strip()
    try:row=grok.run_job(job,root,shutil.which('cursor-agent'),credentials)
    finally:
        auth=root/job_id/'home/.cursor/auth.json'
        if auth.exists():auth.unlink()
    result={'id':job_id,'folder':job_id,'host':'grok-medium','case':'replica-rejoin','status':row['status'],'actual_identity':row['actual_model_identity_evidence'],'response_sha256':h.digest(root/job_id/'response.txt'),'wall_seconds':row['wall_seconds']}
    (root/(job_id+'.result.json')).write_text(json.dumps(result,indent=2));print(json.dumps(result))

if __name__=='__main__':main()
