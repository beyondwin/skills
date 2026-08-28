# How It Works Rename and Repository Architecture Design

**Status:** Approved on 2026-08-28

**Scope:** Rename the unpublished `graspic` product to `how-it-works`, support
local or repository-based use in Codex, Claude Code, Grok, and Cursor, and
reorganize this repository so products, tests, documentation, and tooling are
easier to find and update.

**Out of scope:** Legacy invocation aliases, redirect skill packages,
Claude.ai/Cowork or Skills API upload, cloud skill synchronization,
marketplace publication, GitHub tags, and GitHub Releases.

## Context

The current product is unpublished. A fresh remote tag query and GitHub Release
listing on 2026-08-28 show only the integrated `v2.0.0` release, which contains
`korean-writing-editor` and `image-workbench`, not `graspic`. The current
product therefore has no public artifact, tag, or catalog lock that must retain
its working name.

The working name is spread across 46 tracked files. It is not limited to the
skill directory: release archive names, verification stages, change-target
routing, issue templates, public documentation, maintainer protocols, tests,
and local installation links all depend on it.

The repository also has structural friction:

- product identities and paths are repeated in several Python modules and
  tests;
- product fixtures and product contract tests live in separate trees;
- eight transitional documents under `docs/ko/` and `docs/en/` only redirect
  to `docs/users/`;
- active user documentation, maintainer documentation, and historical plans
  share one navigation surface;
- “catalog” sometimes means the three current standalone products and
  sometimes means the immutable two-product `v2.0.0` plugin bundle.

Current provider-free product, catalog, release-check, and whitespace gates
pass before this work begins. That baseline proves repository contracts only;
it does not prove live behavior in any model host.

## Goals

1. Make `how-it-works` the only active identity of the explanation skill.
2. Keep one installable payload that works in Codex, Claude Code, Grok, and
   Cursor without host-specific copies.
3. Define a useful common output that does not require an Artifact, Canvas,
   browser, or Mermaid renderer.
4. Preserve direct GitHub installation from `skills/<name>/`.
5. Make the product registry, tests, documentation, and release tooling easy
   to navigate and update.
6. Separate current contracts from historical plans without rewriting history.
7. Fail closed when a product, path, document, or verification stage is
   missing or unregistered.

## Non-goals

- Do not add support for the old skill name or invocation.
- Do not broaden `korean-writing-editor` or `image-workbench` host support.
- Do not turn the repository into four host-specific packages.
- Do not generate public prose from configuration files.
- Do not change the immutable `v2.0.0` catalog payload or legacy fixtures.
- Do not publish a tag or release as a side effect of implementation.

## Decisions

### 1. Product identity

| Surface | Value |
| --- | --- |
| Product ID | `how-it-works` |
| Directory | `skills/how-it-works/` |
| Frontmatter `name` | `how-it-works` |
| Display name | `How It Works` |
| First public target | `1.0.0` |
| Tag prefix | `how-it-works-v` |
| First archive | `how-it-works-v1.0.0.zip` |
| Python identifier form | `how_it_works` |

The old name has no alias, redirect directory, compatibility command, or
deprecation period. Except for the explicit changelog migration note described
below, active source, tests, public documentation, maintainer documentation,
CI, release tooling, and community templates must not contain it.

Historical plans and specifications retain factual references to the old
working name under `docs/history/`. A narrow stale-identifier allowlist covers
that directory and an explicit changelog migration note only. Historical text
is not an active compatibility promise.

Because there is no public release under the old identity, `how-it-works`
starts at `1.0.0` instead of inheriting the unpublished `3.0.0` target.

### 2. One portable payload

`skills/how-it-works/` is the only payload source. Host-specific wrappers and
copies are forbidden because they create four independently drifting behavior
contracts.

```text
skills/how-it-works/              canonical repository source
├─ ~/.agents/skills/how-it-works ─→ Codex, Grok, Cursor
└─ ~/.claude/skills/how-it-works ─→ Claude Code
```

The shared `SKILL.md` uses only the portable Agent Skills frontmatter
intersection:

- `name`
- `description`
- `license`
- `compatibility`
- `metadata`

`argument-hint` is removed. Host-only routing fields are not required for core
behavior. `agents/openai.yaml` remains as optional Codex presentation metadata,
but no runtime instruction depends on it.

Explicit invocation differs only at the host surface:

| Host | Explicit invocation | Discovery path |
| --- | --- | --- |
| Codex | `$how-it-works` | `~/.agents/skills/how-it-works` |
| Claude Code | `/how-it-works` | `~/.claude/skills/how-it-works` |
| Grok | `/how-it-works` | `~/.agents/skills/how-it-works` |
| Cursor | `/how-it-works`, optional `@how-it-works` | `~/.agents/skills/how-it-works` |

The description front-loads the intended visual or flow-explanation use case
and chosen depth. The generic product name alone must not broaden implicit
activation to debugging, implementation, review, translation, one-line factual
lookups, child-register explanation, or `/eli5`.

### 3. Runtime flow

All four hosts follow the same state machine:

```text
request
  -> fill slice, type, rung, language
  -> emit one intent line
  -> read the required focused references
  -> emit Markdown explanation, Mermaid, and numbered hop list
  -> offer one next move
```

The gate remains strict:

- a civilization-scale noun is cut into a slice before explanation;
- only one missing-slot question is asked at a time;
- a filled slot is not asked again;
- the same hop identifiers survive from 그림 through 허점;
- later rungs add detail without retracting the earlier true picture.

### 4. Portable output and capability enhancement

The required deliverable is complete in chat and contains:

1. a one-sentence claim;
2. a Mermaid code block;
3. a numbered textual hop list that remains useful when Mermaid is not
   rendered;
4. the rung-specific body;
5. adjacent slices that were not covered;
6. one next move.

The current mandatory `artifact-design` and Artifact publishing contract is
removed. No required instruction names a host tool.

When a host exposes a page, Canvas, or visualization capability, the agent may
add a preview. A preview never replaces the complete common output, and preview
failure never turns a valid explanation into a failed task. Page URLs, temporary
files, browser opening, and URL continuity are not support criteria.

### 5. Failure and safety behavior

- Broad topic: offer three bounded slices and ask one question.
- Missing rung: ask one closed question; do not silently pick a depth.
- Missing Mermaid renderer: show Mermaid source and the textual hop list.
- Preview failure: continue with the portable deliverable and mention the
  fallback once only when useful.
- No fetched source: omit citations instead of inventing them.
- Medical, legal, or financial topic: keep the exact mechanism-only safety
  banner and avoid personalized direction.
- User data: do not persist user topics, private prompts, full model responses,
  or generated media in fixtures or support records.

## Repository architecture

The repository keeps installation-first product directories and mirrors them
in tests and maintainer documentation.

```text
/
├── products.toml
├── skills/
│   ├── korean-writing-editor/
│   ├── image-workbench/
│   └── how-it-works/
├── tests/
│   ├── products/
│   │   ├── korean-writing-editor/
│   │   ├── image-workbench/
│   │   └── how-it-works/
│   └── repository/
├── docs/
│   ├── README.md
│   ├── users/
│   │   ├── ko/
│   │   └── en/
│   ├── maintainers/
│   │   ├── products/
│   │   │   ├── korean-writing-editor/
│   │   │   ├── image-workbench/
│   │   │   └── how-it-works/
│   │   └── repository/
│   └── history/
│       ├── specs/
│       └── plans/
├── scripts/
│   ├── lib/
│   ├── verify.py
│   └── release.py
└── catalog/
```

### Installation boundary

`skills/<name>/` remains directly installable from GitHub. Tests, maintainer
documents, live evidence, repository tooling, and historical records stay
outside the payload. This preserves the existing public installation shape and
avoids a generated installation directory.

### Product registry

`products.toml` is the single repository index for ordered product discovery,
display names, support claims, owned paths, and verification stage selection.
It does not own versions.

Illustrative schema:

```toml
schema_version = 1

[[products]]
name = "how-it-works"
display_name = "How It Works"
skill_path = "skills/how-it-works"
test_path = "tests/products/how-it-works"
maintainer_docs = "docs/maintainers/products/how-it-works"
supported_hosts = ["codex", "claude-code", "grok", "cursor"]
verify_stages = ["product-contract", "how-it-works-contract", "python-compile"]
```

The other two products are registered with their current, narrower support
claims. Registry validation rejects:

- duplicate names or paths;
- a missing skill, test, or maintainer-doc directory;
- an unregistered directory under `skills/` or `tests/products/`;
- an unknown host or verification stage;
- a mismatch between the registry name, skill directory, `SKILL.md` name, and
  product `release.toml` name.

Each product `release.toml` remains the only version and tag source. General
documentation must not copy current version literals.

### Tooling boundaries

Reusable code moves under `scripts/lib/`:

- product registry loading and validation;
- product payload and release contracts;
- change-target routing;
- archive validation;
- documentation facts and link checks.

`scripts/verify.py` and `scripts/release.py` remain small CLI entry points.
Verification stage implementations stay code, while `products.toml` selects
registered stage identifiers. The registry never contains shell commands.

An unmatched changed path remains fail closed and selects the full repository
matrix. Windows separators are normalized before routing.

### Catalog boundary

`catalog/` continues to reproduce the immutable published `v2.0.0` catalog and
its two locked standalone products. It does not automatically adopt current
products from `products.toml`. A current product release and catalog adoption
remain separate operations.

Root and contributor documentation use “current standalone products” for the
three development products. “Catalog” refers only to the separately versioned
plugin bundle under `catalog/`.

## Test architecture

### Product tests

`tests/products/<name>/` owns each product's fixtures, deterministic runners,
and product-specific contract tests. `tests/products/how-it-works/` covers:

- directory and frontmatter identity;
- the portable frontmatter field set;
- explicit invocation examples for all four hosts;
- implicit trigger and near-miss boundaries;
- slice, type, rung, and language gates;
- Markdown, Mermaid, and numbered-hop requirements;
- no mandatory Artifact, Canvas, browser, or host-tool name;
- high-stakes banners and citation behavior;
- payload file inclusion and exclusion.

Only synthetic topics such as DNS and rebase appear in committed fixtures.

### Repository tests

`tests/repository/` owns:

- `products.toml` schema and directory coverage;
- payload and independent release contracts;
- documentation links and bilingual fact parity;
- change-target and GitHub Actions matrix behavior;
- ZIP construction, checksum, extraction, and download verification;
- catalog lock and immutable legacy fixture behavior;
- archive-source manifest behavior;
- community templates and CI policy;
- stale active identifier scanning.

### Host smoke

Support is claimed only after fresh-session checks prove:

1. skill discovery;
2. explicit invocation;
3. intended implicit invocation and near-miss non-invocation;
4. complete Markdown, Mermaid, and numbered-hop output.

Codex, Claude Code, and Grok use their locally available CLIs. Cursor uses the
installed desktop application because no Cursor CLI is currently available on
this host. The smoke record stores only host name, client version, date, case
ID, and verdict. Full responses and private prompts are not committed.

Live smoke is explicit, optional, potentially billable, and excluded from CI.
Provider-free CI proves package and shape contracts, not live model quality.

## Documentation architecture

### Reader paths

`docs/README.md` routes three audiences:

- someone choosing or installing a product;
- someone reading one product's usage guide;
- a maintainer changing, testing, or releasing a product.

The root README answers within one screen:

- which standalone products exist;
- what each product does;
- which hosts each product supports;
- where to install it;
- how to verify the repository.

### Product README template

Every Korean and English product README uses the same order:

1. one-sentence purpose;
2. use and non-use boundary;
3. supported hosts;
4. shortest installation;
5. first invocation;
6. expected result;
7. safety and privacy;
8. verification level;
9. update and removal;
10. changelog and maintainer links.

Product README files own product-specific use. Shared safe copy, link, update,
and removal procedures live in user installation guides and are linked instead
of duplicated.

### User documentation

Only four paired guides remain under each of `docs/users/ko/` and
`docs/users/en/`:

- `installation.md`;
- `compatibility.md`;
- `safety-and-privacy.md`;
- `verification.md`.

The eight redirect-only documents under `docs/ko/` and `docs/en/` are removed.
They were never part of a subsequent published catalog minor, so Git history is
the recovery path.

### Maintainer documentation

Each product owns `contract.md`, `testing.md`, `compatibility.md`, and
`release.md` under `docs/maintainers/products/<name>/`.

Repository documents cover architecture, the product registry, versioning,
release operations, the catalog boundary, and migrations. The maintainer index
is task-oriented: change behavior, add host support, register a product, verify,
release, or inspect history.

Maintainer documentation remains Korean-first. Public user and product guides
remain paired in Korean and English with matching information order.

### History

Existing `docs/superpowers/specs/` and `docs/superpowers/plans/` move to
`docs/history/specs/` and `docs/history/plans/`. A history README states that
these files describe decisions at a point in time and do not define the current
contract. Archive-capture exclusions and tests are updated for the new history
prefix.

## Migration sequence

The implementation is one design with two independently reviewable workstreams.

### Workstream A: repository foundations

1. Add failing registry and structure tests.
2. Add `products.toml` and registry loading.
3. Move repository tests and product tests with Git-aware renames.
4. Move maintainer product documents and historical plans/specifications.
5. Remove redirect-only user-document stubs.
6. Refactor verification, change routing, and release tools to consume the
   registry.
7. Restore the full provider-free baseline before behavior changes.

Pure moves should be separated from content edits where practical so review
can distinguish relocation from changed meaning.

### Workstream B: product identity and behavior

1. Add failing `how-it-works` identity and portable-output tests.
2. Rename the product, tests, maintainer documents, release identity, and
   community surfaces.
3. Replace the mandatory Artifact contract with the portable output contract.
4. Rewrite active Korean and English documentation.
5. Add stale-identifier enforcement for active paths.
6. Build and re-verify the standalone `1.0.0` archive in a new empty directory.
7. Replace exact local links and run four-host smoke checks.

No implementation step publishes a remote tag or Release.

## Local installation migration

The current machine has old-name links in `.codex`, `.claude`, `.grok`, and
`.agents`. Before changing them, implementation resolves and verifies that each
is a symbolic link to the current repository product.

It then creates only:

- `/Users/kws/.agents/skills/how-it-works` pointing to the repository product;
- `/Users/kws/.claude/skills/how-it-works` pointing to the repository product.

The old four links are removed only after exact-target verification. Real
directories, unexpected targets, or non-links stop the migration for that path.
No parent skill directory is deleted. `.codex` and `.grok` duplicates are not
recreated because Codex, Grok, and Cursor can share `.agents/skills`.

## Verification and acceptance

Implementation is complete only when all of the following hold:

1. `products.toml` is valid and covers every current product, test tree, and
   maintainer product directory.
2. The full provider-free repository verification passes on the supported CI
   profiles.
3. `python3 scripts/verify.py --skill how-it-works` passes.
4. Product check, build, and fresh extraction/download verification pass for
   `how-it-works-v1.0.0.zip`.
5. Active paths contain no old identifier outside the documented history and
   changelog allowlist.
6. All public and maintainer Markdown links resolve.
7. Korean and English install commands, product names, and host support claims
   agree with `products.toml`.
8. Codex, Claude Code, Grok, and Cursor fresh-session smoke checks pass the four
   support criteria.
9. The two new local links resolve to `skills/how-it-works/`; old-name links do
   not remain.
10. The worktree contains no unintended files, generated archives, provider
    responses, credentials, or unrelated changes.
11. `git diff --check` passes.

Passing package tests is not release evidence. Passing local host smoke is not
remote publication evidence. A tag and GitHub Release require a later explicit
release decision.

## Recovery

- Registry or structure failure: keep the old entry points working until the
  new registry-driven test suite is green; do not leave two authoritative
  registries.
- Rename failure: fix the new identity in place; do not restore a compatibility
  alias.
- Host smoke failure: mark that host unsupported in active documentation until
  the same build passes; do not weaken the common output to hide the failure.
- Link migration mismatch: leave the unexpected local path untouched and
  report it.
- Archive verification failure: discard the new local output directory and
  rebuild from a clean empty directory.
- Remote publication failure: not applicable to this implementation because
  publishing is out of scope.

## Approved outcome

The repository exposes three clearly separated standalone products, with
`how-it-works` as the only current identity of the explanation product. One
portable payload serves four local hosts, active documentation is concise and
task-oriented, historical material is visibly non-authoritative, and one
registry drives product discovery without taking version ownership away from
individual products.
