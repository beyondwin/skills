#!/usr/bin/env python3
"""Mask environment-specific paths before the frozen judge/reader dispatch."""
import argparse
import hashlib
import json
import re
import harness as h
import study


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('phase',choices=['judge','reader'])
    ap.add_argument('output',type=h.Path)
    ap.add_argument('--auth',type=h.Path)
    ap.add_argument('--execute',action='store_true')
    args=ap.parse_args()
    jobs=study.jobs_for(args.phase,args.output)
    receipt=[]
    for case,arm in jobs:
        for name,text in list(case['files'].items()):
            if name not in ('A.txt','B.txt','C.txt','draft.md'):
                continue
            # Every response may cite its synthetic source with an absolute host path.
            # Remove environment/arm identity, preserve file name and cited content.
            masked,n=re.subn(re.escape(str(args.output))+r'/[^/\s)]+/work/', '/source/', text)
            assert not re.search(r'--(?:candidate|previous|baseline)(?:/|\b)',masked), 'Unmasked arm path'
            case['files'][name]=masked
            receipt.append({'job':case['id'],'file':name,'replacements':n,
                            'raw_sha256':hashlib.sha256(text.encode()).hexdigest(),
                            'masked_sha256':hashlib.sha256(masked.encode()).hexdigest()})
    if not args.execute:
        print(json.dumps({'jobs':len(jobs),'live_calls':0,'masked_paths':sum(x['replacements'] for x in receipt)}))
        return
    amendment=json.loads((h.ROOT/'masking-amendment.json').read_text())
    assert h.digest(h.ROOT/'masked_evaluation.py')==amendment['wrapper_sha256']
    (args.output/(args.phase+'-mask-receipt.json')).write_text(json.dumps(receipt,indent=2))
    assert args.auth and args.auth.is_file()
    h.dispatch(jobs,args.output,args.auth)

if __name__=='__main__':
    main()
