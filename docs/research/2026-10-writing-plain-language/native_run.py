#!/usr/bin/env python3
"""0.5.1 native Codex acceptance with Opus/Grok audits; dry run by default."""
import json
from pathlib import Path
import run

run.CANDIDATE = run.ROOT/'validated-candidate/ko-technical-writing'
original_prepare = run.prepare


def check_freeze():
    p = json.loads((run.ROOT/'native-protocol.json').read_text())
    assert run.h.manifest(run.CANDIDATE) == p['candidate']
    assert run.h.manifest(run.INCUMBENT) == p['incumbent']
    for name, sha in p['files'].items():
        assert run.h.digest(run.ROOT/name) == sha, name
    return p


def prepare(phase, root):
    cases = json.loads((run.ROOT/'native-cases.json').read_text())
    if phase == 'generate':
        return [dict(id=c['id']+'--candidate', host='codex', kind='generation',
                     arm='candidate', case=c) for c in cases]
    if phase == 'judge':
        jobs = []
        (root/'prompts').mkdir(exist_ok=True)
        rubric = (run.ROOT/'personal-rubric.txt').read_text()
        for c in cases:
            d = root/(c['id']+'--candidate')
            assert json.loads((d/'normalized.json').read_text())['status'] == 'ok'
            draft = (d/'response.txt').read_text().replace(str(d/'work')+'/', '/source/')
            files = {'notes.md': c['files']['notes.md'], 'request.txt': c['prompt'], 'draft.md': draft}
            job_id = 'review-'+c['id']+'--baseline'
            path = root/'prompts'/(job_id+'.txt')
            path.write_text(run.e.inline(files, rubric))
            jobs.append(dict(id=job_id, host=c['reviewer'], kind='review', arm='baseline',
                             case=c, prompt_path=str(path), prompt_sha256=run.h.digest(path)))
        return jobs
    return original_prepare(phase, root)


run.check_freeze = check_freeze
run.prepare = prepare
if __name__ == '__main__':
    run.main()
