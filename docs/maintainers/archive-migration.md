# Archive skill migration provenance

This document freezes the `beyondwin/Archive` source used to create the public
`beyondwin/skills` repository. It is the import pin, not a description of the
current Archive tree. Do not rewrite Archive history or treat a local checkout
path as part of this record.

## Pinned source

| Field | Value |
| --- | --- |
| Source repository | `https://github.com/beyondwin/Archive.git` |
| Pinned commit | `76e6bf4ebbc9430aee9a04a5b780ae38330f3021` |
| Manifest | [`archive-source-manifest.json`](archive-source-manifest.json) |
| Manifest digest (`manifest_sha256`) | `6917f68e6e0d81226e50195d58a884373d23ffbbbe48363ef2428c8cbcb83f78` |
| Source prefixes | `skills/korean-writing-editor/`, `skills/image-workbench/` |
| Tracked source files | 22 |
| Capture tool | `scripts/capture_archive_manifest.py` |

At capture time Archive `HEAD` equalled `origin/main` at the pinned commit and
the tracked worktree was clean. Recapture is required if either source prefix
changes before import.

Verify the pin by passing a local Archive checkout as `--repository` only. Do
not commit that checkout path.

```bash
python3 scripts/capture_archive_manifest.py verify \
  --repository <archive-checkout> \
  --manifest docs/maintainers/archive-source-manifest.json
```

## 22-file source boundary

The import authority is the 22 tracked files under the two prefixes, each
recorded with Git mode, blob OID, byte size, and SHA-256. Later tasks copy those
bytes; they do not import Archive Git history.

`korean-writing-editor` (13 files):

- `SKILL.md`, `README.md`, `CHANGE_PROTOCOL.md`
- `references/editorial-guide.md`, `references/sources.md`
- `evals/run.py`, `evals/cases.json`, `evals/README.md`
- `evals/live_matrix.py`, `evals/test_live_matrix.py`, `evals/live_cases.json`
- `evals/fixtures/task-7-install-state.json`
- `evals/fixtures/task-7-preflight-commit.json`

`image-workbench` (9 files):

- `SKILL.md`, `README.md`, `CHANGE_PROTOCOL.md`
- `references/image-spec.md`, `references/quality-rubric.md`, `references/sources.md`
- `scripts/inspect_asset.py`
- `evals/run.py`, `evals/cases.json`

## Identifier inventory

The scan is exact-name scoped to these four identifiers:

- `korean-writing-editor`
- `image-workbench`
- `kws-korean-writing-editor`
- `kws-image-workbench`

Every hit in the checked-in manifest has exactly one class:

| Class | Count | Meaning |
| --- | ---: | --- |
| `source` | 22 | Tracked files under the two skill prefixes |
| `active-routing` | 2 | `skills/AGENTS.md`, `skills/README.md` |
| `verification-registration` | 4 | `scripts/agent/contract.ts`, `verification-map.ts`, and their tests |
| `skill-history-document` | 11 | Skill-specific operations, plans, and specs, including catalog-identity history |
| `mixed-document` | 4 | Root `AGENTS.md` and `README.md`, plus the two frozen plan-runner catalog assertions |
| `generated-residue` | 8 | Ignored cache files, two named worktrees, and two ignored session logs |

Unrelated `kws-*` trees are out of scope. The catalog-identity plan and spec are
included because they name the four identifiers; they remain skill-history
documents for later exact-path removal.

## Worktrees observed at freeze

These extra Archive worktrees were clean and already merged into `main` at
freeze time. They were later removed without `--force` after the public
deletion gate.

| Worktree (repo-relative) | Branch | Tip |
| --- | --- | --- |
| `.superpowers/worktrees/kws-korean-writing-editor-cross-model-evaluation` | `codex/kws-korean-writing-editor-cross-model-evaluation` | `90b0776b7cce407cdc1cf3509d5f1dc9e09df107` |
| `.superpowers/worktrees/kws-korean-writing-editor-live-hardening` | `kws-korean-writing-editor-live-hardening` | `64bb7a20898a93b1866698639dd5cde41aeaf334` |
| `.superpowers/worktrees/skills-catalog-identity` | `skills-catalog-identity` | `6788ed37aa43d7014e15c29048e52141b0116cce` |

The first two worktree paths match a scanned identifier and appear in the
manifest as `generated-residue`. `skills-catalog-identity` does not contain an
exact identifier in its path, so it is recorded here rather than as an
identifier hit.

## Ignored cache-only legacy directory

`skills/kws-korean-writing-editor/` exists only as ignored bytecode:

- `evals/__pycache__/live_matrix.cpython-314.pyc`
- `evals/__pycache__/test_live_matrix.cpython-314.pyc`

No `skills/kws-image-workbench/` directory was present. Two additional ignored
`.pyc` files exist under `skills/korean-writing-editor/evals/__pycache__/`.
Ignored session logs whose *content* names the identifiers, not their paths,
are also recorded:

- `.remember/logs/memory-2026-08-23.log`
- `.remember/logs/memory-2026-08-24.log`

`.git` internals are not identifier hits. Worktree interiors collapse to
`.superpowers/worktrees/<name>`. After the public deletion gate those
residues were removed from Archive's current and ignored trees.

## Removal gate

Archive stayed untouched through public repository creation, `v2.0.0`
publication, and independent download verification. After that gate, Archive
current-tree copies and active references for the two skills were removed in a
normal revertible commit. Rollback on Archive is `git revert` of that removal
commit.

## Post-transition

| Field | Value |
| --- | --- |
| Public repository | `https://github.com/beyondwin/skills` |
| Public `v2.0.0` commit | `d072a37870b5099cb131c91b5270fd7ad032db9f` |
| Public release | `https://github.com/beyondwin/skills/releases/tag/v2.0.0` |
| Archive removal commit | `e25fd6d023f8baac4f1c48a0df312ba5e9b53bcd` |

This table records the completed transition. It does not claim a marketplace
listing. The freeze fields above remain the import pin.
