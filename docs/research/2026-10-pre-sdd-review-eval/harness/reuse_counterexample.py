"""Offline proof that HEAD-relative diff misses removed reviewed dirty code."""
from pathlib import Path
import tempfile, subprocess, hashlib, json

def git(repo,*args):
    return subprocess.check_output(['git','-C',str(repo),*args],text=True).strip()
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
with tempfile.TemporaryDirectory() as td:
    repo=Path(td)
    (repo/'source.py').write_text('SUPPORTED = {"base"}\n')
    (repo/'design.md').write_text('Approved: integrate the existing extra capability.\n')
    (repo/'plan.md').write_text('**Spec:** design.md\nUse existing source.SUPPORTED extra capability.\n')
    git(repo,'init','-q')
    git(repo,'add','.')
    git(repo,'-c','user.name=Test','-c','user.email=test@example.invalid','commit','-qm','base')
    head=git(repo,'rev-parse','HEAD')
    (repo/'source.py').write_text('SUPPORTED = {"base", "extra"}\n')
    source_reviewed=digest(repo/'source.py')
    docs_before={p:digest(repo/p) for p in ('design.md','plan.md')}
    dirty_reviewed=bool(git(repo,'status','--porcelain'))
    git(repo,'restore','source.py')
    change_list=git(repo,'diff','--name-only',head).splitlines()+git(repo,'ls-files','--others','--exclude-standard').splitlines()
    result={'reviewed_worktree_dirty':dirty_reviewed,'current_worktree_dirty':bool(git(repo,'status','--porcelain')),
            'head_unchanged':git(repo,'rev-parse','HEAD')==head,
            'documents_unchanged':docs_before=={p:digest(repo/p) for p in docs_before},
            'reviewed_source_changed':source_reviewed!=digest(repo/'source.py'),
            'specified_change_list':change_list,
            'specified_docs_only_predicate':all(p in ('design.md','plan.md') for p in change_list)}
    assert all(result[k] for k in ('reviewed_worktree_dirty','head_unchanged','documents_unchanged','reviewed_source_changed','specified_docs_only_predicate'))
    assert result['specified_change_list']==[]
    print(json.dumps(result,indent=2))
