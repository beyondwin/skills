# Archive skill migration provenance

This document freezes the `beyondwin/Archive` source used to create the public
`beyondwin/skills` repository. Archive is read-only until Task 12 of the public
skills plan. Do not mutate Archive, rewrite its history, or treat a local
checkout path as part of this record.

## Pinned source

| Field | Value |
| --- | --- |
| Source repository | `https://github.com/beyondwin/Archive.git` |
| Pinned commit | `76e6bf4ebbc9430aee9a04a5b780ae38330f3021` |
| Manifest | [`archive-source-manifest.json`](archive-source-manifest.json) |
| Manifest digest (`manifest_sha256`) | `de758712a2df5da808fd5b600be211e80e29ee9ae19f74ec1fd4ad6c93b1d8ef` |
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
| `generated-residue` | 6 | Ignored cache files and two named worktrees |

Unrelated `kws-*` trees are out of scope. The catalog-identity plan and spec are
included because they name the four identifiers; they remain skill-history
documents for later exact-path removal.

## Worktrees observed at freeze

These extra Archive worktrees were clean and already merged into `main`. They
were not deleted.

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
These residues stay in place until the Archive removal work after Task 12.

## Removal gate

Archive stays untouched through public repository creation, `v2.0.0`
publication, and independent download verification. Task 12 re-proves this pin
before any Archive worktree is opened for deletion.
