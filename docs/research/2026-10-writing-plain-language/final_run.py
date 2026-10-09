#!/usr/bin/env python3
"""0.4.2 development comparison; reuses six frozen incumbent responses explicitly."""
import json
from pathlib import Path
import sys
import run

run.CANDIDATE=run.ROOT/'final-candidate/ko-technical-writing'
original_prepare=run.prepare
original_masked=run.masked

def check_freeze():
 p=json.loads((run.ROOT/'final-protocol.json').read_text())
 assert run.h.manifest(run.CANDIDATE)==p['candidate']
 assert run.h.manifest(run.INCUMBENT)==p['incumbent']
 for name,sha in p['files'].items():assert run.h.digest(run.ROOT/name)==sha,name
 return p


def masked(root,c,arm):
 d=root/(c['id']+'--'+arm)
 raw=(d/'response.txt').read_text()
 if c['host']=='codex':raw=raw.replace(str(d.resolve()/'work')+'/', '/source/')
 return raw


def prepare(phase,root):
 if phase=='generate':
  run.ARMS=['candidate']
  jobs=original_prepare(phase,root)
  run.ARMS=['previous','candidate']
  transfer=json.loads((run.ROOT/'transfer-cases.json').read_text())
  for c in transfer:
   job=dict(id=c['id']+'--candidate',host=c['host'],kind='transfer',arm='candidate',case=c)
   if c['host']!='codex':
    files={'SKILL.md':(run.CANDIDATE/'SKILL.md').read_text(),'references/documents.md':(run.CANDIDATE/'references/documents.md').read_text(),**c['files']}
    prompt=run.e.inline(files,c['prompt']+'\nApply the supplied writing skill and its document reference.')
    path=root/'prompts'/(job['id']+'.txt');path.write_text(prompt)
    job.update(prompt_path=str(path),prompt_sha256=run.h.digest(path))
   jobs.append(job)
  return jobs
 if phase=='judge':
  for c in json.loads((run.ROOT/'cases.json').read_text()):
   d=root/(c['id']+'--previous'); expected=json.loads((run.ROOT/'final-protocol.json').read_text())['reused_responses'][c['id']]
   assert run.h.digest(d/'response.txt')==expected
 return original_prepare(phase,root)

run.check_freeze=check_freeze
run.masked=masked
run.prepare=prepare

if __name__=='__main__':run.main()
