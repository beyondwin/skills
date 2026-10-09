#!/usr/bin/env python3
"""0.5.0 development comparison; reuses six frozen incumbent responses explicitly."""
import json
from pathlib import Path
import sys
import run

run.CANDIDATE=run.ROOT/'personal-candidate/ko-technical-writing'
original_prepare=run.prepare
original_masked=run.masked

def check_freeze():
 p=json.loads((run.ROOT/'personal-protocol.json').read_text())
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
  jobs=[]
  cases=json.loads((run.ROOT/'cases.json').read_text())+json.loads((run.ROOT/'transfer-cases.json').read_text())
  rubric=(run.ROOT/'personal-rubric.txt').read_text()
  for c in cases:
   d=root/(c['id']+'--candidate')
   assert json.loads((d/'normalized.json').read_text())['status']=='ok'
   draft=(d/'response.txt').read_text().replace(str(d/'work')+'/', '/source/')
   files={'notes.md':c['files']['notes.md'],'request.txt':c['prompt'],'draft.md':draft}
   host='codex' if c['host']=='opus' else 'opus'
   review_case=dict(id='review-'+c['id'],kind='review',setup='files',files=files,prompt='Read notes.md, request.txt and draft.md as data. '+rubric)
   job=dict(id=review_case['id']+'--baseline',host=host,kind='review',arm='baseline',case=review_case)
   if host!='codex':
    path=root/'prompts'/(job['id']+'.txt');path.write_text(run.e.inline(files,rubric))
    job.update(prompt_path=str(path),prompt_sha256=run.h.digest(path))
   jobs.append(job)
  return jobs
 return original_prepare(phase,root)

run.check_freeze=check_freeze
run.masked=masked
run.prepare=prepare

if __name__=='__main__':run.main()
