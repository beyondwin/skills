# Public Skills Repository Design

**Date:** 2026-08-26

**Status:** Approved in chat; implementation has not started

**Target repository:** `https://github.com/beyondwin/skills`
**Source repository:** `https://github.com/beyondwin/Archive`

## 1. Decision Summary

Create a public, curated repository for exactly two Agent Skills:

- `korean-writing-editor`: conservatively proofreads, corrects, or polishes
  Korean text supplied by the user while preserving meaning and voice.
- `image-workbench`: plans, generates, edits, compares, or audits a raster
  asset for a local project. This skill is Codex-only.

The new repository becomes the only canonical source. After the new public
release is independently downloadable and verified, remove all current-tree
copies and active references for these two skills from `beyondwin/Archive`.
Do not rewrite Archive Git history.

The repository is:

- Codex-first;
- compatible with the open Agent Skills directory format;
- a single Codex plugin bundle named `beyondwin-skills`;
- licensed uniformly under Apache-2.0;
- curated rather than an open-ended skill collection; and
- free of telemetry, provider calls, and credentials in required CI.

The first public release is `v2.0.0`, preserving the current version identity
of both skills.

## 2. Context

The target worktree was an empty Git repository when this design was written.
The source Archive `main` was observed at `76e6bf4e`, with both skills already
carrying behavior contracts, references, deterministic evaluations, change
protocols, and runtime-specific evidence. That observed commit is research
context, not the migration pin: implementation must record and verify the
actual Archive commit used at transition time.

The current installed footprint mixes runtime payload and maintainer-only
material. In particular, `korean-writing-editor` includes a large live-eval
runner and unit suite, while `image-workbench` includes offline evaluation
machinery alongside its runtime image inspector. A public installation should
contain what the agent needs to perform the skill, not provider runners,
historical operation receipts, or maintainer procedures.

The design follows these current public conventions:

- The [Agent Skills specification](https://agentskills.io/specification)
  defines a skill as a directory with `SKILL.md` and optional `scripts/`,
  `references/`, and `assets/`, with progressive disclosure.
- [OpenAI's skills documentation](https://learn.chatgpt.com/docs/build-skills)
  distinguishes skill authoring from plugin distribution and recommends
  plugins for reusable public distribution.
- [OpenAI's plugin packaging documentation](https://developers.openai.com/plugins/build/plugins)
  requires `.codex-plugin/plugin.json` and permits one plugin to bundle
  multiple skills.
- The [`skills` CLI](https://github.com/vercel-labs/skills) can discover a
  `skills/` catalog and install one named skill for cross-agent use. It is an
  optional third-party path, not the primary Codex installer.
- GitHub's [community profile guidance](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/about-community-profiles-for-public-repositories)
  motivates explicit license, contribution, conduct, security, and issue
  reporting files.

## 3. Goals

1. Make the new repository the sole human-edited source of both skills.
2. Keep the installed skill payload small, focused, and legally self-contained.
3. Provide a Codex plugin-ready bundle without claiming marketplace
   availability before publication actually occurs.
4. Preserve deterministic tests and honest live-evaluation evidence outside
   the installed payload.
5. Make installation, compatibility, privacy, rights, and measured limitations
   obvious from the repository landing page.
6. Make the Archive removal recoverable and conditional on verified public
   distribution.
7. Accept focused fixes without turning the repository into a general skill
   registry.

## 4. Non-goals

- Adding a third skill in the first release.
- Adding an MCP server, hooks, a web UI, a package registry, or a custom
  installer.
- Submitting to the universal plugin directory as part of repository creation.
- Claiming non-Codex compatibility for `image-workbench`.
- Claiming cross-runtime behavior for `korean-writing-editor` without a
  runtime-specific smoke result.
- Running models or provider CLIs in required CI.
- Importing Archive's full Git history or rewriting Archive history.
- Adding telemetry, analytics, automatic uploads, or remote image services.
- Accepting unsolicited new skills through pull requests.

## 5. Repository Architecture

```text
.
├── .codex-plugin/
│   └── plugin.json
├── skills/
│   ├── korean-writing-editor/
│   │   ├── SKILL.md
│   │   ├── LICENSE.txt
│   │   ├── agents/
│   │   │   └── openai.yaml
│   │   └── references/
│   │       ├── editorial-guide.md
│   │       └── sources.md
│   └── image-workbench/
│       ├── SKILL.md
│       ├── LICENSE.txt
│       ├── agents/
│       │   └── openai.yaml
│       ├── references/
│       │   ├── image-spec.md
│       │   ├── quality-rubric.md
│       │   └── sources.md
│       └── scripts/
│           └── inspect_asset.py
├── tests/
│   ├── contract/
│   ├── korean-writing-editor/
│   │   ├── offline/
│   │   └── live/
│   └── image-workbench/
├── scripts/
│   └── verify.py
├── docs/
│   ├── ko/
│   │   ├── getting-started.md
│   │   ├── compatibility.md
│   │   ├── privacy-and-rights.md
│   │   └── evaluation.md
│   ├── en/
│   │   ├── getting-started.md
│   │   ├── compatibility.md
│   │   ├── privacy-and-rights.md
│   │   └── evaluation.md
│   ├── maintainers/
│   │   ├── architecture.md
│   │   ├── release-process.md
│   │   ├── korean-writing-editor.md
│   │   ├── image-workbench.md
│   │   └── archive-migration.md
│   └── superpowers/specs/
│       └── this design
├── .github/
│   ├── ISSUE_TEMPLATE/
│   ├── workflows/
│   ├── CODEOWNERS
│   ├── dependabot.yml
│   └── pull_request_template.md
├── README.md
├── README.en.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── SECURITY.md
├── CODE_OF_CONDUCT.md
├── LICENSE
└── NOTICE
```

### 5.1 Installed payload

Only `skills/` is installed as skill content. Human quick starts, change
protocols, offline evaluations, live runners, release procedures, and migration
records remain outside the installed payload.

Each skill includes `LICENSE.txt` so direct folder installation retains its
license. `SKILL.md` also declares `license: Apache-2.0` and uses the top-level
`compatibility` field when a runtime requirement is material. The directory
name and `name` frontmatter value must match.

`agents/openai.yaml` contains only display metadata, a short description, a
default prompt, and invocation policy. The first release does not invent a
logo, depend on remote icons, or add an MCP dependency.

`image-workbench/scripts/inspect_asset.py` remains in the payload because it is
a runtime tool. Its invocation must resolve from the actual skill directory,
not assume an Archive checkout or repository-relative `skills/` path.

### 5.2 Plugin boundary

The repository root is one plugin named `beyondwin-skills`.
`.codex-plugin/plugin.json` points `skills` to `./skills/` and declares bundle
version `2.0.0`, Apache-2.0, author, repository, keywords, and minimal interface
metadata. It does not declare MCP servers, apps, hooks, or capabilities that
the repository does not ship.

The manifest makes the repository plugin-ready. Documentation must not say the
plugin is listed in a marketplace until remote publication has been separately
authorized and verified.

### 5.3 Test boundary

Existing evaluations move under `tests/` without weakening their behavioral
assertions. Path and packaging assertions are deliberately updated to verify
the new source layout and a staged temporary install.

- `tests/korean-writing-editor/offline/` owns deterministic trigger, mode,
  preservation, and output-contract fixtures.
- `tests/korean-writing-editor/live/` owns the provider runner, live cases,
  provider-free unit tests, receipt integrity, and dry-run planning.
- `tests/image-workbench/` owns routing, authorization, evidence, and
  inspector-contract fixtures.
- `tests/contract/` owns repository-wide manifest, frontmatter, link,
  packaging, version, license, and prohibited-string checks.

Test files are not copied into release skill zips. The plugin bundle source
archive may contain tests because it is the repository archive, but the
purpose-built plugin release zip contains only plugin payload and legally
required files.

## 6. Distribution and Compatibility

### 6.1 First-class support

Codex is the first-class runtime for both skills.

- `korean-writing-editor` remains portable at the Agent Skills contract level.
  A host is marked `supported` only after a current smoke test; otherwise its
  status is `partially verified` or `not measured`.
- `image-workbench` is explicitly Codex-only because it requires Codex built-in
  image generation and local image viewing for generate or edit modes. Similar
  tools in another host do not establish compatibility.

### 6.2 Installation paths

The primary Codex path uses `$skill-installer` with a public GitHub skill path
until a plugin-directory install is actually available. The optional
cross-agent path uses `npx skills add beyondwin/skills --skill
korean-writing-editor` and is labeled as a third-party installer with its own
release and telemetry policy. Documentation provides a non-`npx` alternative.

No documentation includes `curl | sh`, an unchecked recursive copy, an
unchecked overwrite, or `rm -rf` as a routine update path.

## 7. Documentation and Public Information Architecture

`README.md` is the Korean landing page. `README.en.md` is a complete English
counterpart. Both present the same commands, versions, support statuses, and
limitations. Verification checks those shared facts rather than trying to
enforce byte-for-byte translation parity.

The README order is:

1. one-sentence project purpose;
2. CI, release, and Apache-2.0 badges;
3. a two-skill catalog and support matrix;
4. one-minute installation and invocation;
5. exclusions and safety boundaries;
6. separate offline and live evidence status; and
7. documentation, contribution, security, and license links.

User documentation is paired under `docs/ko/` and `docs/en/`:

- `getting-started.md`: install, invoke, update, and uninstall without unsafe
  broad deletion;
- `compatibility.md`: contract portability versus measured host support;
- `privacy-and-rights.md`: Korean source-text privacy, image reference rights,
  consent, provenance, and the no-telemetry policy; and
- `evaluation.md`: deterministic fixtures, live evaluation, result labels,
  commands, and limitations.

Maintainer documentation is written once under `docs/maintainers/` and covers
architecture, release gates, each skill's change protocol, and migration
provenance. It replaces per-skill `README.md` and `CHANGE_PROTOCOL.md` inside
the installed payload.

The project does not claim “best quality,” “human-like,” “production verified,”
provider superiority, rights clearance, or runtime parity without direct
evidence.

## 8. Contribution and Community Policy

The repository accepts focused fixes to the two existing skills:

- behavior defects;
- documentation corrections;
- security fixes;
- compatibility evidence; and
- synthetic, non-personal regression fixtures.

It does not accept new skills by default. A pull request adding a third skill
is out of scope unless repository governance is explicitly changed first.
Live provider results are not accepted as sufficient evidence without the
reproducible case definition, runtime identity, consent-safe artifacts, and
the deterministic contract gate.

`CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, issue forms, a PR
template, and CODEOWNERS make those rules discoverable. Apache-2.0 applies to
all submitted contributions unless explicitly rejected before merge.

## 9. Verification Design

The required local command is:

```bash
python3 scripts/verify.py
```

It performs, in order:

1. plugin-manifest and skill-frontmatter validation;
2. directory/name/version/license consistency checks;
3. installed-payload closure and relative-link validation;
4. scans for absolute user paths, Archive checkout assumptions, credentials,
   private fixtures, and non-allowlisted legacy skill identifiers;
5. Python compilation;
6. complete offline Korean-editor fixtures;
7. complete image-workbench fixtures;
8. image-inspector self-tests; and
9. provider-free live-runner unit tests and dry-run accounting.

The orchestrator stops on deterministic failure and reports the exact failing
stage. It does not turn a failed test into `partially_verified`, nor does it
turn an unavailable provider into a passing result.

Tests stage each skill into a temporary install root and validate the staged
copy. This detects references that accidentally work only in the source
checkout. Generated evidence stays outside tracked paths and is deleted after
the offline run.

### 9.1 GitHub Actions

Required CI runs on pull requests and pushes to `main`:

- Ubuntu and macOS execute the complete provider-free verification suite.
- Windows executes the portable `korean-writing-editor` offline suite and
  repository contract checks that are meaningful on Windows.
- Workflow permissions are `contents: read`.
- Every Action reference is pinned to a full commit SHA.
- Every job has a timeout.
- `pull_request_target` is prohibited.
- Required CI has no API keys, model calls, remote image calls, or provider
  CLI execution.

The public repository enables GitHub secret scanning, Dependabot for Action
updates, and CodeQL default setup when the host account supports them. If a
repository setting cannot be configured automatically, implementation reports
it as a manual external setting rather than pretending a file enabled it.

External-link freshness is not a blocking PR-time network test. Relative links
are blocking; authoritative external links are reviewed through a separate
manual freshness procedure so transient network failures do not make the core
gate flaky.

## 10. Live Evaluation and Evidence

Live evaluation is an explicit local operation only. It requires a positive
execution flag, a named runtime, a bounded call budget, and an evidence root
outside tracked source. Provider subprocesses are never silently substituted.

The existing status vocabulary remains:

- `verified`
- `partially_verified`
- `failed`
- `blocked`
- `not_measured`

Raw user Korean text, provider responses, private reference images, generated
images, credentials, and receipts are not committed. CI logs emit bounded case
IDs and statuses rather than prompts or raw content. `.gitignore` covers live
evidence, receipts, generated media, caches, virtual environments, and local
tool output.

Offline fixture success proves the deterministic contract only. It does not
prove general Korean editing quality, semantic equivalence, live image quality,
rights clearance, provider superiority, or cross-runtime parity.

## 11. Privacy, Rights, and Security

- Fixtures are synthetic or authored for redistribution under the repository
  license. Personal conversations and private project images are excluded.
- The Korean editor does not persist user text, call spelling services, or
  advertise detector evasion.
- Image references have one declared role. A reference does not confer rights
  to reproduce a person, mark, or protected work.
- Repository code, an output hash, a source URL, and C2PA metadata are distinct
  evidence types; none alone proves ownership, consent, truth, or commercial
  permission.
- Runtime scripts use bounded input, bounded output, explicit paths, and stable
  errors. They do not upload content.
- The project itself has no telemetry. Optional third-party installers are
  identified as third party and linked to their own policy.
- Vulnerabilities are reported privately according to `SECURITY.md`, including
  supported versions and response expectations.

## 12. Versioning and Release

The plugin bundle and repository release start at `2.0.0`. Each `SKILL.md`
keeps its own metadata version. A skill version changes only when that skill's
contract or runtime payload changes; the plugin version changes whenever the
packaged bundle changes. Root documentation-only changes do not require a new
release.

The first release produces:

```text
beyondwin-skills-v2.0.0.zip
korean-writing-editor-v2.0.0.zip
image-workbench-v2.0.0.zip
SHA256SUMS
```

Release archives are built in a temporary directory from tracked files. The
release gate runs the full provider-free verifier, checks a clean source tree,
validates archive contents, extracts every archive into a fresh directory, and
runs installation smokes against the extracted content. `SHA256SUMS` is
computed only after those checks pass.

The release notes state measured support and limitations. They do not claim
universal plugin-directory availability until that external state is verified.

## 13. Archive Migration and Removal

### Phase 1: Freeze and inventory

1. Re-read Archive `main`, remote state, dirty state, and worktrees.
2. Resolve the exact source commit and list every tracked file under the two
   active skill directories.
3. Compute a source manifest with paths, Git object IDs, file modes, sizes, and
   SHA-256 values.
4. Search the entire current Archive tree for exact active and legacy names:
   `korean-writing-editor`, `image-workbench`,
   `kws-korean-writing-editor`, and `kws-image-workbench`.
5. Classify each hit as source, active routing, verification registration,
   skill-specific history document, mixed document, or generated/ignored
   residue.
6. Do not mutate Archive during this phase.

The scan is exact-name scoped. It must not remove unrelated `kws-*` projects.

### Phase 2: Import and adapt

1. Copy the tracked source snapshot, not Archive's full Git history.
2. Separate installed payload, tests, and maintainer documentation according
   to this design.
3. Replace Archive-relative assumptions with skill-root or repository-root
   resolution as appropriate.
4. Preserve behavioral fixtures and compare old versus new deterministic
   results.
5. Add the plugin manifest, license files, public documentation, community
   files, CI, and release tooling.
6. Record the actual source commit and manifest digest in `NOTICE` and
   `docs/maintainers/archive-migration.md`.
7. Run public-surface scans for user paths, private content, secrets, ignored
   evidence, and stale links.

### Phase 3: Publish and prove

1. Commit and push the new repository to `beyondwin/skills`.
2. Confirm remote `main` by direct remote-ref lookup.
3. Wait for required CI and inspect the actual results.
4. Tag the verified commit `v2.0.0` and publish the four release artifacts.
5. Download the remote artifacts rather than reusing local build output.
6. Verify checksums and run fresh extraction and installation smokes.
7. Confirm that public README links and source skill URLs resolve.

No Archive deletion can begin until every Phase 3 item succeeds.

### Phase 4: Remove from Archive

Remove from Archive's current tree:

- both active skill directories;
- exact legacy residues for these two skills;
- catalog and routing entries;
- verification-map registrations and tests that exist only for these skills;
- skill-specific design, plan, and operation documents; and
- generated or ignored residues proven to belong to these skills.

For a mixed file, remove only the two-skill material and preserve unrelated
content. For a file whose sole subject is one or both migrated skills, delete
the file. Do not leave a redirect or duplicate copy in Archive, per the
approved transition policy.

After removal:

1. search the current tree again for all four exact identifiers;
2. inspect every remaining hit and require zero active or stale references;
3. run Archive's complete relevant verification suite;
4. review the deletion diff for unrelated loss;
5. commit the removal separately; and
6. push only after the local commit and tests are verified.

Git history is not rewritten. Historical commits remain recoverable.

### 13.1 Rollback

- Before Archive removal: abandon or repair the new release; Archive remains
  canonical until Phase 3 finishes.
- After a local Archive removal commit but before push: do not publish the
  commit; repair or revert it non-destructively.
- After push: use `git revert` on the exact removal commit and restore files
  from the verified release artifacts and migration manifest.

## 14. Archive Deletion Gate

Archive removal requires all of the following:

- public `beyondwin/skills` `main` resolves to the reviewed commit;
- tag `v2.0.0` resolves to that commit;
- all required CI jobs are green;
- all four release artifacts are publicly downloadable;
- release checksums match freshly downloaded bytes;
- plugin and individual-skill installation smokes pass;
- the source-to-import manifest is accounted for;
- Archive source commit and migration provenance are recorded;
- personal paths, secrets, private fixtures, and unintended artifacts are
  absent; and
- no unsupported compatibility or quality claim is present.

Any missing condition blocks deletion.

## 15. Acceptance Criteria

The repository transition is complete only when:

1. `python3 scripts/verify.py` passes from a fresh clone without credentials or
   model access.
2. The plugin manifest discovers exactly two skills.
3. Direct installation contains no maintainer eval runner, Archive path, or
   unsafe update command.
4. `korean-writing-editor` preserves its trigger, mode, preservation, and
   output contract under the migrated offline suite.
5. `image-workbench` preserves its authorization, routing, non-destructive
   save, rights, and inspection contract under the migrated suite.
6. Korean and English public docs agree on commands, versions, support states,
   and limitations.
7. GitHub community, security, license, and contribution entry points exist.
8. The public release and its checksums are verified from downloaded bytes.
9. Archive's current tree contains no copy or active/stale reference for the
   two migrated skills, while unrelated Archive content remains intact.
10. Archive history remains unchanged and the removal is represented by a
    normal, revertible commit.

## 16. Approved Decisions

- New repository is the sole canonical source: approved.
- Archive current-tree material is fully removed after transition: approved.
- Codex is first-class; only the Korean editor has a portable Agent Skills
  support goal: approved.
- Apache-2.0 applies to the entire repository and each standalone skill:
  approved.
- Contributions are curated fixes to the two skills; new skills are not
  accepted by default: approved.
- Catalog-centered single plugin architecture: approved.
- Bilingual public documentation: approved.
- Offline CI and explicit local-only live evaluation boundary: approved.
- `v2.0.0` release and gated Archive deletion process: approved.
