# Live Docs Structure and Voice Design

**Status:** Approved in chat on 2026-09-05; implementation has not started

**Scope:** Rewrite live documentation so the next reader finds the right
page quickly, reads it in easy language, and can keep the tree consistent
without a new docs framework. Prune `docs/history/` to reasons that still
matter and are not already in live docs. Inspect `.gitignore` and add only
recurring local artifacts.

**Out of scope:** Changing review semantics, host support, or
`products.toml`; rewriting `SKILL.md` or `reviewer-protocol.md`; tagging,
pushing, GitHub Release, or catalog mutation; reading, migrating, or
deleting schema 1 receipts or the owner-machine launcher; adding MkDocs,
a docs generator, or a new documentation directory tree.

## Context

The physical tree is already the right shape: `docs/users/`,
`docs/maintainers/`, `docs/history/`, and `skills/<name>/README.md`. Tests
pin public headings, shared sections, and SHA-256 digests, so a rewrite
must move the pins in the same change.

What is not working:

1. Facts repeat across the root README, product READMEs, and user guides.
2. Maintainer pages mix Korean and English in the same sentence, so the
   page is harder than the rule it explains.
3. Live user guides still mention the removed `pre-sdd-review-evidence`
   launcher as something to find and delete.
4. `docs/history/` holds ~14 500 lines of finished specs and plans. Live
   contracts already own the current rules. Old names are allowed there,
   which makes history a magnet for leftover identity.
5. `pre-sdd-review` has no `## 함께 고칠 파일` map. The other products do.
6. Quality was treated as a line budget in the last recorder work. Here
   the budget is the opposite: one place per fact, short sentences, no
   extra pages.

The owner's order is quality first, then lightness.

## Goals

1. Two front doors, one file tree: a product README for “this skill”, and
   the job indexes for “install / verify / change / release”.
2. Each live fact has one owner page. Other pages link; they do not
   restate the procedure.
3. Live prose is everyday language. Commands, paths, and contract tokens
   stay English.
4. Live pages do not teach removed installers, launchers, or schema 1.
5. History keeps only in-progress specs and plans, plus any still-binding
   reason that is not yet in a live page. Finished plans, unused field
   notes, and superseded specs go away after that reason is absorbed.
6. Digest pins and “함께 고칠 파일” maps stay the maintenance mechanism.
   No new docs tooling.

## Non-goals

- Changing what a skill does, which hosts it supports, or catalog lock.
- Rewriting agent instruction files (`SKILL.md`, reviewer protocol).
- A numeric line cap on any document.
- Supporting old evidence installation paths in live guides.
- Touching files under the owner's home directory.

## Decisions

### 1. Keep the audience tree; keep two front doors

Physical layout does not change:

| Tree | Audience | Job |
| --- | --- | --- |
| `skills/<name>/README.md`, `README.en.md` | Person choosing or invoking one skill | What it is, when to use it, first call, limits, link out |
| `docs/users/{ko,en}/` | Person installing or verifying the repo | Install, compatibility, safety, verification |
| `docs/maintainers/` | Person changing a product or the repo | Contract, test, compatibility, release, registry |
| `docs/history/` | Person running or reading an in-progress SDD pair | Non-authoritative; see Decision 5 |
| Repository `README.md` / `README.en.md`, `docs/README.md` | Arrival | Route only |

Do not add a product-shaped docs tree. Do not add `docs/maintainers/docs.md`.
Put the maintenance rules in `docs/maintainers/README.md` and the history
rule in `docs/history/README.md`.

Product README heading sets stay as they are today. Tests already pin
them. Rewrite the bodies; do not invent parallel section names.

### 2. One place per fact

A fact has one owner. Duplicating a procedure is a defect.

| Fact | Owner |
| --- | --- |
| Codex `$skill-installer` commands, How It Works links, update/remove | `docs/users/{ko,en}/installation.md` |
| Host support matrix and `not_measured` | `docs/users/{ko,en}/compatibility.md`; product README states the one-line support claim tests already pin |
| Safety, telemetry, high-stakes, evidence privacy | `docs/users/{ko,en}/safety-and-privacy.md` |
| `python3 scripts/verify.py` profiles, offline vs live evidence | `docs/users/{ko,en}/verification.md` |
| Product trigger, modes, verdicts, editable paths | that product's maintainer `contract.md` and `SKILL.md` |
| How to invoke this skill | that product's README |
| Recorder commands, stdin, limits | `skills/pre-sdd-review/evidence/README.md` |
| SemVer table | `docs/maintainers/repository/versioning.md` |
| Independent release commands | `docs/maintainers/repository/release.md` |
| Payload vs test split | `docs/maintainers/repository/architecture.md` |
| Catalog lock and plugin ZIP | `docs/maintainers/repository/catalog.md` and `catalog/README.md` |
| Docs maintenance (front doors, language, pins, history rule) | `docs/maintainers/README.md` |

Product READMEs keep a short install snippet so a GitHub skill page still
works, then link to the shared installation guide for the rest. Strings
that tests already pin stay: the `$skill-installer` URL, the How It Works
`ln -s` / `unlink` commands, the one-line support claim, maintainer doc
links, and a short “confirm the folder before update or remove” sentence
(`확인` / `inspect`). Full update/remove, profile lists, and catalog lock
stay on their owner pages.

### 3. Language

- Maintainer docs: Korean is the original. Commands, paths, identifiers,
  enum values, and JSON keys stay English.
- User guides and product READMEs: Korean original plus English sibling.
  The same facts, same commands, same limits.
- Voice: short sentences, everyday words, one idea per sentence.
- Do not pack an English clause into a Korean sentence unless the English
  is a command, path, or token.
- Machine-readable lists that tests pin (authority order, verdicts,
  finding classes, risk triggers, README `### Contract` tokens) stay in
  their current English form so semantics cannot drift.
- `SKILL.md` and `references/reviewer-protocol.md` are not rewritten.

Example of the voice change (maintainer contract, not a semantic change):

- Before: `before dispatching any reviewer 현재 checkout을 git merge-base …로 확인합니다.`
- After: `검토자를 부르기 전에, 현재 checkout이 필수 베이스의 조상인지 git merge-base …로 확인합니다.`

### 4. Dead names leave live docs

Live pages, including product READMEs and `evidence/README.md`, must not
tell anyone how to install, invoke, or uninstall the removed recorder.

Forbidden in live docs (active markdown outside `docs/history/` and
outside dated CHANGELOG entries):

- `install.py`, `--bin-dir`, `record-outcome`, `finish-review`
- “remove the old launcher” / `~/.local/bin/pre-sdd-review-evidence`
- schema 1 receipt layout as a user or maintainer procedure

Allowed:

- The verify stage name `pre-sdd-review-evidence` (it is a unittest stage,
  not the launcher).
- `schema 2` as the current record schema.
- Dated CHANGELOG entries that describe the 2.0.0 break.
- `kws-` near-miss notes that are still the live no-op contract.

`evidence/README.md` describes current commands and schema 2. It does not
explain the old package.

### 5. History is in-progress only

`docs/history/` does not define the current contract. After this work:

- `docs/history/plans/`: delete every finished plan listed below.
- `docs/history/field-notes/`: delete the directory, including its README.
  The v1.2.0 convergence note was adopted in v1.3.0. Still-binding
  rejections move into the pre-sdd-review contract, then the note goes.
- `docs/history/specs/`: delete every superseded spec listed below, after
  any still-binding reason is copied into a live page.
- Keep `docs/history/README.md`, rewritten to say: this tree holds only
  in-progress specs and plans; it is not the contract; old names may
  appear here.
- Keep this design and its implementation plan until the work is merged.
  They may be deleted later once `docs/maintainers/README.md` owns the
  maintenance rules.

Delete after absorb (all finished):

| Path | Absorb if needed | Then |
| --- | --- | --- |
| `docs/history/plans/*.md` (all eight current plans) | none; live docs own the results | delete |
| `docs/history/field-notes/**` | pre-sdd-review `하지 않는 것`: no closure-only input schema, no shared-design invalidation map, no program ledger, no evidence probe cache | delete the directory |
| `docs/history/specs/2026-08-26-public-skills-repository-design.md` | architecture / registry already own this | delete |
| `docs/history/specs/2026-08-27-graspic-design.md` | `how-it-works` CHANGELOG already owns the unpublished identity | delete |
| `docs/history/specs/2026-08-27-independent-skill-product-architecture-design.md` | architecture.md | delete |
| `docs/history/specs/2026-08-28-how-it-works-repository-architecture-design.md` | how-it-works live docs | delete |
| `docs/history/specs/2026-08-29-pre-sdd-review-design.md` | pre-sdd-review live docs | delete |
| `docs/history/specs/2026-08-30-pre-sdd-review-evidence-loop-design.md` | superseded by 2.0.0 | delete |
| `docs/history/specs/2026-09-05-pre-sdd-review-evidence-simplification-design.md` | evidence README + product docs | delete |

Stale-identifier allowlist stays `docs/history/` plus
`skills/how-it-works/CHANGELOG.md`. After graspic specs/plans are gone,
the CHANGELOG remains the only live mention.

First-call examples in the pre-sdd-review README keep the paths
`docs/history/specs/<design>.md` and `docs/history/plans/<plan>.md`.
That is where in-progress SDD files in this repo still live.

### 6. Pins and “함께 고칠 파일” are the process

Do not add a docs framework. Keep:

- SHA-256 pins in `tests/repository/test_public_docs.py` and
  `tests/products/pre-sdd-review/test_contract.py`.
- Heading and fact assertions in those tests.
- `## 함께 고칠 파일` on every product `contract.md`, including
  pre-sdd-review (it is missing today).
- A short maintenance section on `docs/maintainers/README.md`: two front
  doors, one owner per fact, language rule, pin rule, history rule.

A live-doc change and its digest/fact pins land in the same commit. A
task that rewrites a pinned page without updating the pin is incomplete.

### 7. `.gitignore` is additive

Current ignore already covers worktrees, Superpowers ledgers, bytecode,
`dist/`, coverage caches, secrets, and editor junk.

Inspect `git status --ignored`. Add a pattern only when a **recurring**
local artifact is not covered. Do not ignore leftover source trees.

The untracked tree `skills/pre-sdd-review/evidence/pre_sdd_review_evidence/`
is bytecode from the deleted package. Delete it from the working tree.
Do not add that package name to `.gitignore`.

Do not rewrite the ignore file for style.

### 8. Frozen product contracts

These do not change meaning:

- `products.toml` host support and verify stages.
- Review semantics in `SKILL.md` and `reviewer-protocol.md`.
- Evidence recorder behaviour and schema 2.
- Catalog lock, Archive manifest digest, SemVer table.

Installed README language changes are documentation. They do not bump a
product version unless `python3 scripts/release.py check --product <name>`
requires it. Today korean-writing-editor and image-workbench already
target `2.0.1` above catalog baseline `2.0.0`; how-it-works `1.0.0` and
pre-sdd-review `2.0.0` have no product-tag baseline. Add a CHANGELOG
`Unreleased` note when an installed README body changes. Do not tag,
push, or edit `catalog/`.

### 9. Leftover owner-machine files stay untouched

`~/.local/bin/pre-sdd-review-evidence` and schema 1 files under
`~/.pre-sdd-review/` are outside the repository. This work does not
inspect, migrate, or delete them, and live docs do not mention them.

## Package and repository impact

| Area | Change |
| --- | --- |
| `docs/users/{ko,en}/*.md` | Easy language; drop launcher-removal text; keep owned facts and the verify stage name |
| `docs/maintainers/README.md` | Job index plus the maintenance rules in Decision 6 |
| `docs/maintainers/products/*/contract.md` | Easy Korean around pinned lists; add `## 함께 고칠 파일` to pre-sdd-review; absorb the four rejections |
| `docs/maintainers/products/*/{testing,compatibility,release}.md` | Easy Korean; same commands and evidence limits |
| `docs/maintainers/repository/*.md` | Easy Korean; history row matches Decision 5 |
| `docs/README.md`, root `README.md` / `README.en.md`, `catalog/README.md` | Route; do not own procedures |
| `docs/history/README.md` | In-progress only; keep the non-authoritative facts tests pin |
| `docs/history/specs/`, `plans/`, `field-notes/` | Delete finished files per Decision 5 |
| `skills/*/README.md`, `README.en.md` | Easy language; short install snippet; no dead names; headings unchanged |
| `skills/pre-sdd-review/evidence/README.md` | Current recorder only |
| `skills/*/CHANGELOG.md` | `Unreleased` note if that product's installed README changes; do not rewrite dated entries |
| `SKILL.md`, `reviewer-protocol.md` | No change |
| `tests/repository/test_public_docs.py` | Dead-name assertions; shared-section digests; history README facts if the wording changes |
| `tests/products/pre-sdd-review/test_contract.py` | README and maintainer digests; forbid dead names without a launcher exception |
| `.gitignore` | Add only if inspection finds a recurring artifact |
| `products.toml`, `scripts/release.py` payload lists | No change |

`scripts/lib/documentation.py` already tracks the live markdown set.
Deleting history files does not require a scanner change. Adding a new
live page would; this design adds none.

## Verification design

All verification stays provider-free through existing unittest stages.

1. Update fact and dead-name assertions first so they fail on the old
   text.
2. Rewrite the owning page.
3. Recompute SHA-256 pins with the helpers in the implementation plan.
4. `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover` for
   `tests/repository` and the affected product `test_contract.py`.
5. After the last docs task: `python3 scripts/verify.py --profile full`
   and `--profile windows-portable`.
6. `python3 scripts/release.py check --product <name>` for each product
   whose installed README changed. No tag, no publish.

Broken-link checks on `active_markdown_paths` must stay green after
history files that live pages used to link are gone. Live pages must not
link to deleted history files.

## Success criteria

- A new reader can pick a skill from a product README, or a job from
  `docs/users/` / `docs/maintainers/`, without being sent through history.
- Each procedure in Decision 2 has one owner. Other pages link to it.
- Live docs contain none of the forbidden strings in Decision 4, except
  the verify stage name and dated CHANGELOG entries.
- `docs/history/` contains `README.md`, this spec, its plan, and no
  finished plans, field notes, or superseded specs.
- Every product `contract.md` has `## 함께 고칠 파일`.
- `python3 scripts/verify.py --profile full` and `windows-portable` pass.
- No host-support claim, review rule, or `products.toml` row changed.
