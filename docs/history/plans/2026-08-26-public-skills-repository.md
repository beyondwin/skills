# Public Skills Repository Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish `korean-writing-editor` and `image-workbench` as the two curated skills in `beyondwin/skills` v2.0.0, prove the public artifacts, and then remove every current-tree and safely removable local residue for those skills from `beyondwin/Archive` without rewriting history.

**Architecture:** The new repository is one Codex plugin whose installed payload is only `skills/`; deterministic evaluators, the Korean live harness, documentation, migration evidence, and release tooling remain outside that payload. The transition is deliberately one-way and gated: capture an immutable Archive snapshot, import and adapt it, pass provider-free verification, publish and redownload the public release, then perform a separate revertible Archive removal commit.

**Tech Stack:** Markdown, JSON, YAML, Python 3.11+ standard library, `unittest`, Git, GitHub Actions, GitHub CLI (`gh`), Codex Agent Skills, Codex plugin manifest.

**Spec:** `docs/superpowers/specs/2026-08-26-public-skills-repository-design.md`

## Global Constraints

- Read the approved spec before execution and do not reopen its approved decisions.
- Use `superpowers:using-git-worktrees` before implementation; create `codex/public-skills-v2` for this repository and a separate `codex/remove-migrated-public-skills` worktree for Archive only after the public-release gate passes.
- Read `superpowers:writing-skills` before changing either `SKILL.md`; use `plugin-creator` when creating `.codex-plugin/plugin.json` and `skill-creator` when validating the skill packages.
- Use TDD for new or changed behavior: run the focused test RED, make the smallest change, run it GREEN, then run the neighboring suite.
- Preserve unrelated dirty state and never use `git reset --hard`, `git checkout --`, forced worktree removal, forced branch deletion, or Archive history rewriting.
- The public catalog contains exactly `korean-writing-editor` and `image-workbench`; no third skill, MCP server, hook, app, custom installer, telemetry, or required provider call is added.
- Codex is first-class for both skills; only `korean-writing-editor` has an Agent Skills portability goal. `image-workbench` remains explicitly Codex-only.
- Repository, plugin, and both skill versions start at `2.0.0`; the license is Apache-2.0 at root and in each standalone skill.
- Required CI and `python3 scripts/verify.py` are credential-free and provider-free. Live Korean evaluation remains an explicit local operation with a positive execution flag and a 160-call total ceiling.
- Public fixtures are synthetic and redistributable. Do not commit user Korean text, private images, provider responses, receipts, credentials, or generated media.
- Do not claim marketplace listing, universal host support, general editing quality, live image quality, rights clearance, or provider superiority without direct evidence.
- Do not mutate Archive until the remote `v2.0.0` release and all four downloaded artifacts pass the deletion gate.
- Archive removal is exact-name scoped to `korean-writing-editor`, `image-workbench`, `kws-korean-writing-editor`, and `kws-image-workbench`; unrelated `kws-*` content stays intact.
- Every task ends with a focused verification and a narrow commit. Use `superpowers:requesting-code-review` before publication and `superpowers:verification-before-completion` before every success claim, tag, release, merge, or push.

At execution start, resolve the migration-only source checkout without recording a personal absolute path in public files:

```bash
SKILLS_ARCHIVE_CHECKOUT="$(git -C ../Archive rev-parse --show-toplevel)"
test "$(git -C "$SKILLS_ARCHIVE_CHECKOUT" remote get-url origin)" = "https://github.com/beyondwin/Archive.git"
export SKILLS_ARCHIVE_CHECKOUT
```

---

## File and Ownership Map

### New public repository

| Path | Responsibility |
| --- | --- |
| `.codex-plugin/plugin.json` | One `beyondwin-skills` plugin manifest pointing only to `./skills/`. |
| `skills/korean-writing-editor/` | Installable Korean editor payload: `SKILL.md`, license, OpenAI display metadata, and two references. |
| `skills/image-workbench/` | Installable Codex-only raster payload, including the production-only image inspector. |
| `tests/contract/` | Manifest, frontmatter, payload closure, links, public facts, privacy scans, migration manifest, and release archive tests. |
| `tests/korean-writing-editor/offline/` | The 31 deterministic behavior cases, evaluator, and its self-tests. |
| `tests/korean-writing-editor/live/` | Synthetic live cases, provider runner, provider-free unit tests, dry-run planning, and operator documentation. |
| `tests/image-workbench/` | The 31 decision cases, evaluator tests, and inspector tests moved out of the installed payload. |
| `scripts/capture_archive_manifest.py` | Read-only capture and verification of the pinned Archive source snapshot. |
| `scripts/verify.py` | Cross-platform provider-free verification orchestrator. |
| `scripts/build_release.py` | Deterministic construction and extraction-smoke verification of three zip files plus `SHA256SUMS`. |
| `docs/ko/`, `docs/en/` | Paired public installation, compatibility, privacy/rights, and evaluation documentation. |
| `docs/maintainers/` | Architecture, release, migration provenance, and per-skill change protocols. |
| `.github/` | Provider-free CI, issue forms, PR policy, CODEOWNERS, and Dependabot. |
| Root community files | Korean and English landing pages, changelog, contribution/security/conduct policy, Apache license, and provenance notice. |

### Archive source-to-target mapping

| Archive source at the pinned commit | New canonical location |
| --- | --- |
| `skills/korean-writing-editor/SKILL.md` | `skills/korean-writing-editor/SKILL.md` |
| `skills/korean-writing-editor/references/*` | `skills/korean-writing-editor/references/*` |
| `skills/korean-writing-editor/evals/run.py` and `cases.json` | `tests/korean-writing-editor/offline/` |
| `skills/korean-writing-editor/evals/live_matrix.py`, `test_live_matrix.py`, `live_cases.json`, fixtures | `tests/korean-writing-editor/live/` |
| `skills/korean-writing-editor/README.md`, `CHANGE_PROTOCOL.md`, eval README | Paired public docs plus `docs/maintainers/korean-writing-editor.md` and live operator docs; not installed. |
| `skills/image-workbench/SKILL.md`, references, production inspector | `skills/image-workbench/` |
| `skills/image-workbench/evals/run.py`, `cases.json`, inspector self-tests | `tests/image-workbench/` |
| `skills/image-workbench/README.md`, `CHANGE_PROTOCOL.md` | Paired public docs plus `docs/maintainers/image-workbench.md`; not installed. |

### Archive removal surfaces

- Delete both complete active skill directories.
- Delete the one skill-specific operations record, five skill/catalog plans, and five matching specs identified by the migration inventory.
- Remove only skill-specific clauses from `AGENTS.md`, `README.md`, `skills/AGENTS.md`, `skills/README.md`, `scripts/agent/contract.ts`, `scripts/agent/check-contract.test.ts`, `scripts/agent/verification-map.ts`, `scripts/agent/verification-map.test.ts`, and the two frozen plan-runner contract tests.
- Remove the three clean, merged worktrees currently under `.superpowers/worktrees/` and their merged local branch refs without `--force`.
- Remove the ignored cache-only `skills/kws-korean-writing-editor/` residue after exact inspection.

---

### Task 1: Freeze Archive source and record a reproducible migration manifest

**Files:**
- Create: `scripts/capture_archive_manifest.py`
- Create: `tests/contract/test_archive_manifest.py`
- Create: `docs/maintainers/archive-source-manifest.json`
- Create: `docs/maintainers/archive-migration.md`
- Create: `.gitignore`

**Interfaces:**
- Consumes: a clean Archive checkout, its `origin/main`, the two source prefixes, and the four exact identifiers.
- Produces: `git(repository: Path, *arguments: str) -> str`, `remote_url(repository: Path) -> str`, `source_entries(repository: Path, prefixes: tuple[str, ...]) -> list[dict[str, object]]`, `identifier_hits(repository: Path, identifiers: tuple[str, ...]) -> list[dict[str, str]]`, `build_manifest(repository: Path, prefixes: tuple[str, ...], identifiers: tuple[str, ...]) -> dict[str, object]`, and `verify_manifest(repository: Path, manifest: dict[str, object]) -> list[str]`; a canonical JSON manifest containing source commit, remote URL, file mode, Git blob OID, byte size, SHA-256, identifier-hit classification, and a manifest digest.

- [ ] **Step 1: Perform both-repository preflight before writing**

```bash
pwd
git status --short --branch --untracked-files=all
git rev-parse HEAD
git worktree list --porcelain
git -C "$SKILLS_ARCHIVE_CHECKOUT" status --short --branch --untracked-files=all
git -C "$SKILLS_ARCHIVE_CHECKOUT" rev-parse HEAD
git -C "$SKILLS_ARCHIVE_CHECKOUT" rev-parse origin/main
git -C "$SKILLS_ARCHIVE_CHECKOUT" worktree list --porcelain
```

Expected: both checked-out branches are clean; Archive `HEAD` equals `origin/main`. If Archive changed from the design-time observation `76e6bf4e`, use the current verified commit and regenerate all baseline evidence from it.

- [ ] **Step 2: Write the failing manifest unit tests**

```python
def test_build_manifest_records_git_and_byte_identity(self):
    manifest = build_manifest(self.repository, ("skills/a/",), ("skill-a",))
    entry = manifest["entries"][0]
    self.assertEqual(entry["mode"], "100644")
    self.assertRegex(entry["blob_oid"], r"^[0-9a-f]{40}$")
    self.assertRegex(entry["sha256"], r"^[0-9a-f]{64}$")
    self.assertEqual(entry["size"], len(b"name: skill-a\n"))

def test_verify_manifest_rejects_source_drift(self):
    manifest = build_manifest(self.repository, ("skills/a/",), ("skill-a",))
    (self.repository / "skills/a/SKILL.md").write_text("changed\n")
    self.assertIn("source tree differs from manifest", verify_manifest(self.repository, manifest))
```

- [ ] **Step 3: Run the tests and observe RED**

Run: `python3 -m unittest discover -s tests/contract -p 'test_archive_manifest.py' -v`

Expected: FAIL because `scripts.capture_archive_manifest` does not exist.

- [ ] **Step 4: Implement canonical capture and verification**

```python
def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()

def build_manifest(repository: Path, prefixes: tuple[str, ...], identifiers: tuple[str, ...]) -> dict[str, object]:
    # Read tracked names with `git ls-files -s`, bytes from the verified checkout,
    # and identifier hits with an argv-based subprocess call. Never use a shell.
    payload = {
        "schema_version": 1,
        "source_repository": remote_url(repository),
        "source_commit": git(repository, "rev-parse", "HEAD"),
        "prefixes": list(prefixes),
        "identifiers": list(identifiers),
        "entries": source_entries(repository, prefixes),
        "identifier_hits": identifier_hits(repository, identifiers),
    }
    payload["manifest_sha256"] = hashlib.sha256(canonical_bytes(payload)).hexdigest()
    return payload
```

The CLI accepts `capture --repository --output` and `verify --repository --manifest`. It rejects a dirty source, a detached source, a source whose `HEAD` differs from `origin/main`, symlinks/special files in the selected prefixes, duplicate paths, or a manifest digest mismatch. Every hit receives one of `source`, `active-routing`, `verification-registration`, `skill-history-document`, `mixed-document`, or `generated-residue`; the checked-in manifest contains no unclassified hit. Do not use `path` as a zsh variable name; it aliases zsh's executable search path.

- [ ] **Step 5: Run the focused tests GREEN and capture the actual snapshot**

```bash
python3 -m unittest discover -s tests/contract -p 'test_archive_manifest.py' -v
python3 scripts/capture_archive_manifest.py capture \
  --repository "$SKILLS_ARCHIVE_CHECKOUT" \
  --output docs/maintainers/archive-source-manifest.json
python3 scripts/capture_archive_manifest.py verify \
  --repository "$SKILLS_ARCHIVE_CHECKOUT" \
  --manifest docs/maintainers/archive-source-manifest.json
```

Expected: tests pass; the manifest records 22 tracked files under the two source prefixes and the actual source commit.

- [ ] **Step 6: Document provenance and ignored/worktree residue without deleting it**

`docs/maintainers/archive-migration.md` must name the source repository, manifest digest, pinned commit, 22-file source boundary, the four identifiers, the current three clean merged worktrees, and the ignored cache-only legacy directory. State that Archive is untouched until Task 12.

- [ ] **Step 7: Commit the freeze evidence**

```bash
git add .gitignore scripts/capture_archive_manifest.py tests/contract/test_archive_manifest.py \
  docs/maintainers/archive-source-manifest.json docs/maintainers/archive-migration.md
git commit -m "chore: freeze Archive skill migration source"
```

---

### Task 2: Import the Korean editor payload and deterministic contract

**Files:**
- Create: `skills/korean-writing-editor/SKILL.md`
- Create: `skills/korean-writing-editor/references/editorial-guide.md`
- Create: `skills/korean-writing-editor/references/sources.md`
- Create: `tests/korean-writing-editor/offline/run.py`
- Create: `tests/korean-writing-editor/offline/cases.json`
- Create: `tests/contract/test_korean_package.py`

**Interfaces:**
- Consumes: the exact Korean source files whose hashes appear in `archive-source-manifest.json`.
- Produces: an installable payload with `name: korean-writing-editor`, `license: Apache-2.0`, `metadata.version: "2.0.0"`; an offline runner supporting `--self-test`, `--scope fixtures|core|full`, and `--skill-root PATH`.

- [ ] **Step 1: Add a failing staged-layout test before importing**

```python
def test_korean_offline_runner_accepts_explicit_skill_root(self):
    result = subprocess.run(
        [sys.executable, str(RUNNER), "--scope", "full", "--skill-root", str(SKILL_ROOT)],
        cwd=REPOSITORY_ROOT,
        text=True,
        capture_output=True,
    )
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertIn("31 cases:", result.stdout)
```

- [ ] **Step 2: Run RED**

Run: `python3 -m unittest discover -s tests/contract -p 'test_korean_package.py' -v`

Expected: FAIL because the public payload and runner are absent.

- [ ] **Step 3: Copy only the pinned source snapshot into its new boundaries**

```bash
mkdir -p skills/korean-writing-editor/references tests/korean-writing-editor/offline
cp "$SKILLS_ARCHIVE_CHECKOUT/skills/korean-writing-editor/SKILL.md" skills/korean-writing-editor/SKILL.md
cp "$SKILLS_ARCHIVE_CHECKOUT/skills/korean-writing-editor/references/editorial-guide.md" skills/korean-writing-editor/references/editorial-guide.md
cp "$SKILLS_ARCHIVE_CHECKOUT/skills/korean-writing-editor/references/sources.md" skills/korean-writing-editor/references/sources.md
cp "$SKILLS_ARCHIVE_CHECKOUT/skills/korean-writing-editor/evals/run.py" tests/korean-writing-editor/offline/run.py
cp "$SKILLS_ARCHIVE_CHECKOUT/skills/korean-writing-editor/evals/cases.json" tests/korean-writing-editor/offline/cases.json
```

Immediately run manifest verification again; stop if any copied source hash no longer matches the pinned manifest.

- [ ] **Step 4: Adapt the evaluator and skill metadata without weakening behavior**

Add `--skill-root` to the runner and resolve its cases from `Path(__file__).with_name("cases.json")`. Replace per-skill README/change-protocol requirements with payload-only requirements: `SKILL.md`, its two relative references, canonical name, Apache license declaration, compatibility, and version. Add `license: Apache-2.0` to the skill frontmatter; keep the 31 cases and all mutation assertions unchanged.

```python
parser.add_argument("--skill-root", type=pathlib.Path)
skill_root = args.skill_root or (
    pathlib.Path(__file__).resolve().parents[3] / "skills" / "korean-writing-editor"
)
cases_path = pathlib.Path(__file__).with_name("cases.json")
```

- [ ] **Step 5: Prove preservation and a temporary standalone install**

```bash
python3 tests/korean-writing-editor/offline/run.py --self-test
python3 tests/korean-writing-editor/offline/run.py --scope full
python3 -c 'import pathlib, shutil, tempfile, subprocess, sys; d=pathlib.Path(tempfile.mkdtemp()); s=d/"korean-writing-editor"; shutil.copytree("skills/korean-writing-editor", s); raise SystemExit(subprocess.run([sys.executable,"tests/korean-writing-editor/offline/run.py","--scope","full","--skill-root",str(s)]).returncode)'
```

Expected: 8 evaluator self-tests pass; 31 cases report `normative=8 preservation=8 noop=6 voice=4 trigger=5`; mutation checks pass in source and staged copies.

- [ ] **Step 6: Commit the Korean deterministic payload**

```bash
git add skills/korean-writing-editor tests/korean-writing-editor/offline tests/contract/test_korean_package.py
git commit -m "feat: migrate Korean writing editor contract"
```

---

### Task 3: Move and public-harden the Korean live harness

**Files:**
- Create: `tests/korean-writing-editor/live/live_cases.json`
- Create: `tests/korean-writing-editor/live/live_matrix.py`
- Create: `tests/korean-writing-editor/live/test_live_matrix.py`
- Create: `tests/korean-writing-editor/live/fixtures/task-7-install-state.json`
- Create: `tests/korean-writing-editor/live/fixtures/task-7-preflight-commit.json`
- Create: `tests/korean-writing-editor/live/README.md`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: `skills/korean-writing-editor`, the offline runner from Task 2, and synthetic live cases.
- Produces: `repository_root(start: Path) -> Path`, `default_source_skill_root(repo: Path) -> Path`, provider-free `--dry-run` output of 119 producer + 3 reviewer + 122 baseline + 38 remediation + 160 total, and opt-in `--preflight`/`--execute` behavior whose evidence and reports remain under an explicitly supplied ignored evidence root.

- [ ] **Step 1: Copy the pinned harness and run its unadapted tests to establish RED**

```bash
mkdir -p tests/korean-writing-editor/live/fixtures
cp "$SKILLS_ARCHIVE_CHECKOUT/skills/korean-writing-editor/evals/live_cases.json" tests/korean-writing-editor/live/live_cases.json
cp "$SKILLS_ARCHIVE_CHECKOUT/skills/korean-writing-editor/evals/live_matrix.py" tests/korean-writing-editor/live/live_matrix.py
cp "$SKILLS_ARCHIVE_CHECKOUT/skills/korean-writing-editor/evals/test_live_matrix.py" tests/korean-writing-editor/live/test_live_matrix.py
cp "$SKILLS_ARCHIVE_CHECKOUT"/skills/korean-writing-editor/evals/fixtures/*.json tests/korean-writing-editor/live/fixtures/
python3 -m unittest discover -s tests/korean-writing-editor/live -p 'test_*.py'
```

Expected: FAIL on old Archive-relative source/eval/report assumptions.

- [ ] **Step 2: Add focused path and privacy assertions first**

```python
def test_default_source_is_public_payload(self):
    self.assertEqual(
        live_matrix.default_source_skill_root(REPOSITORY_ROOT),
        REPOSITORY_ROOT / "skills" / "korean-writing-editor",
    )

def test_default_report_must_stay_under_evidence_root(self):
    with self.assertRaisesRegex(live_matrix.LiveMatrixError, "evidence root"):
        live_matrix.validate_report_path(REPOSITORY_ROOT / "README.md", EVIDENCE_ROOT)
```

- [ ] **Step 3: Adapt repository, evaluator, installed-skill, evidence, and report roots**

Use `Path(__file__).resolve().parents[3]` only as a validated default repository root. The source skill is `<repo>/skills/korean-writing-editor`; the offline runner is `<repo>/tests/korean-writing-editor/offline/run.py`. Reports live under `<evidence-root>/reports/`, not tracked `docs/operations`. Keep `--execute` as the only dispatching mode and retain argv, run identity, reservation, receipt, budget, resume, and no-follow safety checks.

```python
def default_source_skill_root(repository_root: pathlib.Path) -> pathlib.Path:
    return repository_root / "skills" / "korean-writing-editor"

def validate_report_path(report: pathlib.Path, evidence_root: pathlib.Path) -> pathlib.Path:
    resolved = report.resolve(strict=False)
    reports_root = (evidence_root / "reports").resolve(strict=False)
    if not resolved.is_relative_to(reports_root):
        raise LiveMatrixError("report must remain under the evidence root reports directory")
    return resolved
```

Remove dated Archive operation-path rules and old consumed run IDs from defaults. Retain legacy receipt compatibility only where unit tests prove it is needed; do not retain legacy invocation aliases in the public payload.

- [ ] **Step 4: Replace the private historical operator README with a public procedure**

Document only synthetic inputs, `--dry-run`, explicit preflight, explicit billable execution, 122/38/160 budgets, resume semantics, evidence-root ownership, and redacted output. Do not copy the old dated report, raw evidence, provider responses, personal paths, or a claim that any provider is currently available.

- [ ] **Step 5: Run the complete provider-free live gate**

```bash
python3 -m unittest discover -s tests/korean-writing-editor/live -p 'test_*.py'
python3 tests/korean-writing-editor/live/live_matrix.py --dry-run
```

Expected: 209 unit tests pass; dry-run emits exactly `producer_calls=119`, `reviewer_calls=3`, `baseline_calls=122`, `remediation_calls=38`, and `approved_total_ceiling=160`. No provider subprocess is invoked.

- [ ] **Step 6: Add ignored evidence patterns and commit**

Add `.evidence/`, `receipts/`, `generated-media/`, Python caches, virtual environments, coverage, and `dist/` to `.gitignore` without ignoring tracked public fixtures.

```bash
git add .gitignore tests/korean-writing-editor/live
git commit -m "test: migrate Korean live evaluation harness"
```

---

### Task 4: Import image-workbench and split runtime code from tests

**Files:**
- Create: `skills/image-workbench/SKILL.md`
- Create: `skills/image-workbench/references/image-spec.md`
- Create: `skills/image-workbench/references/quality-rubric.md`
- Create: `skills/image-workbench/references/sources.md`
- Create: `skills/image-workbench/scripts/inspect_asset.py`
- Create: `tests/image-workbench/cases.json`
- Create: `tests/image-workbench/run.py`
- Create: `tests/image-workbench/test_inspect_asset.py`

**Interfaces:**
- Consumes: the pinned nine-file image-workbench snapshot.
- Produces: a Codex-only payload with `license: Apache-2.0`, version `2.0.0`, a production inspector exposing `AssetFacts`, `parse_png`, `parse_jpeg`, `parse_webp`, `inspect_bytes`, `inspect_file`, and `main`; external evaluator and inspector tests.

- [ ] **Step 1: Add failing external inspector tests**

```python
def test_png_reports_dimensions_alpha_size_and_hash(self):
    data = make_png(width=3, height=2, color_type=6)
    facts = INSPECTOR.inspect_bytes(data)
    self.assertEqual((facts.width, facts.height, facts.alpha), (3, 2, True))
    self.assertEqual(facts.byte_size, len(data))
    self.assertEqual(facts.sha256, hashlib.sha256(data).hexdigest())

def test_runtime_script_contains_no_unittest_suite(self):
    text = INSPECTOR_PATH.read_text(encoding="utf-8")
    self.assertNotIn("import unittest", text)
    self.assertNotIn("class AssetInspectorTests", text)
```

- [ ] **Step 2: Run RED**

Run: `python3 -m unittest discover -s tests/image-workbench -p 'test_*.py' -v`

Expected: FAIL because the public inspector is absent.

- [ ] **Step 3: Copy the pinned payload/evaluator and extract tests**

```bash
mkdir -p skills/image-workbench/references skills/image-workbench/scripts tests/image-workbench
cp "$SKILLS_ARCHIVE_CHECKOUT/skills/image-workbench/SKILL.md" skills/image-workbench/SKILL.md
cp "$SKILLS_ARCHIVE_CHECKOUT"/skills/image-workbench/references/*.md skills/image-workbench/references/
cp "$SKILLS_ARCHIVE_CHECKOUT/skills/image-workbench/scripts/inspect_asset.py" skills/image-workbench/scripts/inspect_asset.py
cp "$SKILLS_ARCHIVE_CHECKOUT/skills/image-workbench/evals/run.py" tests/image-workbench/run.py
cp "$SKILLS_ARCHIVE_CHECKOUT/skills/image-workbench/evals/cases.json" tests/image-workbench/cases.json
```

Move fixture builders and `AssetInspectorTests` from the runtime script into `test_inspect_asset.py`; load the hyphenated skill path with `importlib.util.spec_from_file_location`. Do not change parser limits, errors, output keys, format detection, or hashing behavior.

- [ ] **Step 4: Adapt paths and payload assertions**

Add `--skill-root` to `tests/image-workbench/run.py`, resolve cases beside the runner, and replace README/change-protocol requirements with payload-only checks. Update the skill's inspector command to resolve from the actual skill root, not `skills/image-workbench` relative to a repository checkout.

```python
parser.add_argument("--skill-root", type=pathlib.Path)
skill_root = args.skill_root or pathlib.Path(__file__).resolve().parents[2] / "skills" / "image-workbench"
cases_path = args.cases or pathlib.Path(__file__).with_name("cases.json")
```

- [ ] **Step 5: Run the preserved decision and parser gates**

```bash
python3 tests/image-workbench/run.py --self-test
python3 tests/image-workbench/run.py --scope full
python3 -m unittest discover -s tests/image-workbench -p 'test_*.py' -v
```

Expected: 29 evaluator tests pass; 31 cases report `routing=9 authorization=5 spec=5 hybrid=4 handoff=5 trust=3`; 8 mutation checks and the 24 inspector tests pass.

- [ ] **Step 6: Verify staged install and commit**

Stage the payload with `shutil.copytree`, run the evaluator using `--skill-root`, run the inspector tests against that staged script, and require no repository-relative runtime path.

```bash
git add skills/image-workbench tests/image-workbench
git commit -m "feat: migrate image workbench contract"
```

---

### Task 5: Add plugin metadata, standalone licenses, and package closure contracts

**Files:**
- Create: `.codex-plugin/plugin.json`
- Create: `skills/korean-writing-editor/LICENSE.txt`
- Create: `skills/korean-writing-editor/agents/openai.yaml`
- Create: `skills/image-workbench/LICENSE.txt`
- Create: `skills/image-workbench/agents/openai.yaml`
- Create: `LICENSE`
- Create: `NOTICE`
- Create: `tests/contract/test_repository.py`

**Interfaces:**
- Consumes: the two payloads and pinned Archive manifest.
- Produces: `load_plugin_manifest() -> dict[str, object]`, `validate_skill(skill_root: Path) -> list[str]`, `stage_skill(skill_root: Path, destination: Path) -> Path`, and a plugin that discovers exactly two skill directories.

- [ ] **Step 1: Write failing manifest, license, and payload-closure tests**

```python
def test_plugin_discovers_exactly_two_skills(self):
    manifest = json.loads((ROOT / ".codex-plugin/plugin.json").read_text())
    self.assertEqual(manifest["name"], "beyondwin-skills")
    self.assertEqual(manifest["version"], "2.0.0")
    self.assertEqual(manifest["skills"], "./skills/")
    self.assertEqual({p.name for p in (ROOT / "skills").iterdir() if p.is_dir()}, {
        "korean-writing-editor", "image-workbench"
    })

def test_installed_payload_excludes_maintainer_material(self):
    forbidden = {"README.md", "CHANGE_PROTOCOL.md", "evals", "tests"}
    for skill in SKILLS:
        self.assertFalse(forbidden.intersection({p.name for p in skill.iterdir()}))
```

- [ ] **Step 2: Run RED**

Run: `python3 -m unittest discover -s tests/contract -p 'test_repository.py' -v`

Expected: FAIL because plugin, license, notice, and agent metadata files are absent.

- [ ] **Step 3: Create the minimal plugin manifest**

```json
{
  "name": "beyondwin-skills",
  "version": "2.0.0",
  "description": "Two conservative, project-aware skills for Korean editing and raster asset work.",
  "author": {"name": "beyondwin", "url": "https://github.com/beyondwin"},
  "homepage": "https://github.com/beyondwin/skills",
  "repository": "https://github.com/beyondwin/skills",
  "license": "Apache-2.0",
  "keywords": ["agent-skills", "codex", "korean-writing", "image-workbench"],
  "skills": "./skills/",
  "interface": {
    "displayName": "Beyondwin Skills",
    "shortDescription": "Korean editing and raster asset workflows",
    "longDescription": "A curated pair of Codex-first skills for conservative Korean text editing and project-bound raster asset work.",
    "developerName": "beyondwin",
    "category": "Developer Tools",
    "capabilities": ["Interactive", "Read", "Write"],
    "websiteURL": "https://github.com/beyondwin/skills",
    "defaultPrompt": ["Polish supplied Korean text", "Plan or audit a project raster asset"]
  }
}
```

Do not add icons, MCP servers, apps, hooks, remote dependencies, privacy URLs that do not exist, or marketplace claims.

- [ ] **Step 4: Add Apache-2.0 and per-skill OpenAI metadata**

Each `LICENSE.txt` is a complete copy of the root Apache-2.0 text. `NOTICE` names the project, copyright holder, Archive repository, pinned source commit, and manifest digest. Each `agents/openai.yaml` contains `interface.display_name`, `short_description`, and `default_prompt`; invocation policy must match the skill activation gate and must not bypass excluded near misses.

- [ ] **Step 5: Add package closure, frontmatter, link, and prohibited-content checks**

`validate_skill` must reject: directory/frontmatter name mismatch, version mismatch, missing Apache declaration/license, broken relative link, a personal macOS home-prefix path, Archive checkout assumption, payload test/eval/maintainer file, symlink/special file, credential-like token, or a third skill. Allow the old prefixed identifiers only inside pinned migration evidence and explicit near-miss fixture files, never in installed payload.

- [ ] **Step 6: Run contract and staged-copy tests GREEN**

```bash
python3 -m unittest discover -s tests/contract -p 'test_*.py' -v
python3 tests/korean-writing-editor/offline/run.py --scope full
python3 tests/image-workbench/run.py --scope full
```

- [ ] **Step 7: Commit package metadata**

```bash
git add .codex-plugin skills LICENSE NOTICE tests/contract/test_repository.py
git commit -m "feat: package two skills as a Codex plugin"
```

---

### Task 6: Build paired public documentation and maintainer protocols

**Files:**
- Create: `README.md`
- Create: `README.en.md`
- Create: `docs/ko/getting-started.md`
- Create: `docs/ko/compatibility.md`
- Create: `docs/ko/privacy-and-rights.md`
- Create: `docs/ko/evaluation.md`
- Create: `docs/en/getting-started.md`
- Create: `docs/en/compatibility.md`
- Create: `docs/en/privacy-and-rights.md`
- Create: `docs/en/evaluation.md`
- Create: `docs/maintainers/architecture.md`
- Create: `docs/maintainers/release-process.md`
- Create: `docs/maintainers/korean-writing-editor.md`
- Create: `docs/maintainers/image-workbench.md`
- Create: `tests/contract/test_public_docs.py`

**Interfaces:**
- Consumes: plugin/skill metadata, exact verification commands, migrated change protocols, and measured baseline results.
- Produces: paired Korean/English facts for version `2.0.0`, exactly two skills, Codex support, Korean portability status, image Codex-only status, offline/live evidence boundary, safe install/update/uninstall paths, and no-telemetry/privacy/rights statements.

- [ ] **Step 1: Write failing bilingual fact and relative-link tests**

```python
SHARED_FACTS = (
    "2.0.0",
    "korean-writing-editor",
    "image-workbench",
    "python3 scripts/verify.py",
    "Apache-2.0",
)

def test_readmes_share_release_and_command_facts(self):
    for document in (ROOT / "README.md", ROOT / "README.en.md"):
        text = document.read_text(encoding="utf-8")
        for fact in SHARED_FACTS:
            self.assertIn(fact, text)
```

- [ ] **Step 2: Run RED**

Run: `python3 -m unittest discover -s tests/contract -p 'test_public_docs.py' -v`

Expected: FAIL because public docs do not exist.

- [ ] **Step 3: Write both landing pages in the approved order**

Use: purpose; CI/release/license badges; two-skill catalog and support matrix; one-minute installation/invocation; exclusions/safety; offline versus live evidence; documentation/community links. `README.md` is Korean and `README.en.md` is a full English counterpart, not a summary.

The primary install examples use `$skill-installer` with the exact public GitHub skill path. The optional command is `npx skills add beyondwin/skills --skill korean-writing-editor`, labeled third-party. The non-`npx` alternative is a normal verified Git clone plus host-native folder installation; never document `curl | sh`, unchecked overwrite, broad recursive deletion, or automatic replacement of an existing install.

- [ ] **Step 4: Write paired user guides**

Both languages must state:

```text
korean-writing-editor: Codex supported; Agent Skills contract portable; other hosts only supported after a recorded smoke.
image-workbench: Codex-only; generate/edit requires Codex image generation and local image viewing.
Offline fixtures: deterministic contract evidence only.
Live execution: local, explicit, optional, potentially billable, and never required by CI.
```

Include exact-target inspection before update/uninstall and distinguish hash/provenance/consent/rights evidence.

- [ ] **Step 5: Consolidate maintainer protocols outside payload**

`architecture.md` owns payload/test separation and interfaces. `korean-writing-editor.md` preserves trigger/mode/output/tier fixture synchronization and 119/3/122/38/160 live invariants. `image-workbench.md` preserves route/authorization/ImageSpec/rubric/inspector synchronization. `release-process.md` owns clean-tree, archive, extraction, checksum, remote-download, and deletion gates.

- [ ] **Step 6: Run doc parity and link checks GREEN**

```bash
python3 -m unittest discover -s tests/contract -p 'test_public_docs.py' -v
python3 -m unittest discover -s tests/contract -p 'test_*.py' -v
```

- [ ] **Step 7: Commit documentation**

```bash
git add README.md README.en.md docs/ko docs/en docs/maintainers tests/contract/test_public_docs.py
git commit -m "docs: publish bilingual skill guidance"
```

---

### Task 7: Add public governance and provider-free CI

**Files:**
- Create: `CONTRIBUTING.md`
- Create: `SECURITY.md`
- Create: `CODE_OF_CONDUCT.md`
- Create: `.github/CODEOWNERS`
- Create: `.github/pull_request_template.md`
- Create: `.github/ISSUE_TEMPLATE/bug.yml`
- Create: `.github/ISSUE_TEMPLATE/documentation.yml`
- Create: `.github/ISSUE_TEMPLATE/config.yml`
- Create: `.github/dependabot.yml`
- Create: `.github/workflows/verify.yml`
- Create: `tests/contract/test_community_and_ci.py`

**Interfaces:**
- Consumes: `scripts/verify.py` profiles defined in Task 8.
- Produces: curated contribution policy, private vulnerability route, and read-only CI on Ubuntu/macOS full profiles plus Windows portable profile.

- [ ] **Step 1: Add failing CI/security-policy tests**

```python
def test_ci_is_read_only_provider_free_and_sha_pinned(self):
    workflow = (ROOT / ".github/workflows/verify.yml").read_text()
    self.assertIn("permissions:\n  contents: read", workflow)
    self.assertNotIn("pull_request_target", workflow)
    self.assertNotRegex(workflow, r"uses: [^\n]+@(v|main|master)")
    for secret_name in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "CURSOR_API_KEY"):
        self.assertNotIn(secret_name, workflow)

def test_contributions_reject_third_skill_by_default(self):
    text = (ROOT / "CONTRIBUTING.md").read_text()
    self.assertIn("new skills are not accepted by default", text.lower())
```

- [ ] **Step 2: Run RED**

Run: `python3 -m unittest discover -s tests/contract -p 'test_community_and_ci.py' -v`

- [ ] **Step 3: Write governance files**

Accept behavior fixes, docs, security fixes, measured compatibility evidence, and synthetic non-personal fixtures for only the two skills. Require Apache-2.0 contribution terms, exact reproduction, no private prompt/image, and deterministic evidence. `SECURITY.md` supports the current `2.x` line and directs vulnerabilities to GitHub private vulnerability reporting without publishing a personal email.

- [ ] **Step 4: Write the SHA-pinned workflow**

Use `actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683` and `actions/setup-python@42375524e23c412d93fb67b49958b491fce71c38`. Set `contents: read`, job timeout 20 minutes, Python `3.11`, and this matrix:

```yaml
strategy:
  fail-fast: false
  matrix:
    include:
      - os: ubuntu-latest
        profile: full
      - os: macos-latest
        profile: full
      - os: windows-latest
        profile: windows-portable
```

The only execution command is `python scripts/verify.py --profile "${{ matrix.profile }}"`. No live runner execute/preflight, provider CLI, remote image call, or secret appears.

- [ ] **Step 5: Add Dependabot and ownership**

Dependabot checks `github-actions` weekly. CODEOWNERS uses `* @beyondwin`. Issue forms prohibit personal text/images and route security reports away from public issues.

- [ ] **Step 6: Run GREEN and commit**

```bash
python3 -m unittest discover -s tests/contract -p 'test_community_and_ci.py' -v
git add CONTRIBUTING.md SECURITY.md CODE_OF_CONDUCT.md .github tests/contract/test_community_and_ci.py
git commit -m "chore: add public governance and CI"
```

---

### Task 8: Implement the single provider-free verification command

**Files:**
- Create: `scripts/verify.py`
- Create: `tests/contract/test_verify.py`
- Modify: `README.md`
- Modify: `README.en.md`
- Modify: `docs/ko/evaluation.md`
- Modify: `docs/en/evaluation.md`

**Interfaces:**
- Consumes: every provider-free test/runner created in Tasks 1–7.
- Produces: `Stage(name: str, argv: tuple[str, ...], cwd: Path)`, `stages(profile: str) -> tuple[Stage, ...]`, `run_stage(stage: Stage) -> int`, and CLI `--profile full|windows-portable` with fail-fast stage reporting.

- [ ] **Step 1: Write failing stage-order and failure-propagation tests**

```python
def test_full_profile_contains_all_provider_free_gates(self):
    names = [stage.name for stage in verify.stages("full")]
    self.assertEqual(names, [
        "contract", "korean-offline", "image-contract", "image-inspector",
        "korean-live-unit", "korean-live-dry-run", "python-compile"
    ])

def test_windows_profile_excludes_codex_only_image_gate(self):
    names = [stage.name for stage in verify.stages("windows-portable")]
    self.assertNotIn("image-contract", names)
    self.assertNotIn("image-inspector", names)
```

- [ ] **Step 2: Run RED**

Run: `python3 -m unittest discover -s tests/contract -p 'test_verify.py' -v`

Expected: FAIL because `scripts.verify` does not exist.

- [ ] **Step 3: Implement argv-only fail-fast orchestration**

```python
@dataclasses.dataclass(frozen=True)
class Stage:
    name: str
    argv: tuple[str, ...]
    cwd: pathlib.Path = ROOT

def run_stage(stage: Stage) -> int:
    print(f"==> {stage.name}: {' '.join(stage.argv)}", flush=True)
    return subprocess.run(stage.argv, cwd=stage.cwd, check=False).returncode
```

Use `sys.executable`, not a shell. Contract discovery runs first. Full then runs both deterministic evaluators, external inspector tests, all 209 live unit tests, live dry-run, and `compileall` over `scripts`, `skills/*/scripts`, and `tests`. Windows portable runs contract, Korean offline, live unit/dry-run, and compilation only. The first nonzero stage stops the command and names the failed stage.

- [ ] **Step 4: Run unit tests and both profiles**

```bash
python3 -m unittest discover -s tests/contract -p 'test_verify.py' -v
python3 scripts/verify.py --profile windows-portable
python3 scripts/verify.py --profile full
```

Expected: both profiles exit 0; full reports the preserved Korean/image counts and no provider process.

- [ ] **Step 5: Synchronize documented commands and commit**

```bash
git add scripts/verify.py tests/contract/test_verify.py README.md README.en.md docs/ko/evaluation.md docs/en/evaluation.md
git commit -m "test: add provider-free repository verifier"
```

---

### Task 9: Build deterministic release archives and extraction smokes

**Files:**
- Create: `scripts/build_release.py`
- Create: `tests/contract/test_release.py`
- Modify: `.gitignore`
- Modify: `docs/maintainers/release-process.md`

**Interfaces:**
- Consumes: a clean tracked checkout at plugin version `2.0.0`.
- Produces: `build_archives(root: Path, output: Path, version: str) -> tuple[Path, ...]`, `write_checksums(archives: Iterable[Path], output: Path) -> Path`, `zip_names(path: Path) -> tuple[str, ...]`, `hashes(paths: Iterable[Path]) -> dict[str, str]`, `verify_archive(path: Path) -> list[str]`, `verify_download(directory: Path, version: str) -> list[str]`, and four artifacts: three deterministic zips and `SHA256SUMS`.

- [ ] **Step 1: Write failing archive membership and reproducibility tests**

```python
def test_release_names_and_membership(self):
    artifacts = build_release.build_archives(ROOT, self.output, "2.0.0")
    self.assertEqual({p.name for p in artifacts}, {
        "beyondwin-skills-v2.0.0.zip",
        "korean-writing-editor-v2.0.0.zip",
        "image-workbench-v2.0.0.zip",
    })
    plugin_names = zip_names(self.output / "beyondwin-skills-v2.0.0.zip")
    self.assertIn(".codex-plugin/plugin.json", plugin_names)
    self.assertFalse(any(name.startswith("tests/") for name in plugin_names))

def test_two_builds_are_byte_identical(self):
    first = hashes(build_release.build_archives(ROOT, self.one, "2.0.0"))
    second = hashes(build_release.build_archives(ROOT, self.two, "2.0.0"))
    self.assertEqual(first, second)
```

- [ ] **Step 2: Run RED**

Run: `python3 -m unittest discover -s tests/contract -p 'test_release.py' -v`

- [ ] **Step 3: Implement deterministic archives**

Sort members, reject symlinks/special files, normalize zip timestamps to `1980-01-01T00:00:00`, normalize regular-file mode to `0644` and executable script mode to `0755`, and read only tracked source files. Plugin zip contains `.codex-plugin/plugin.json`, both complete `skills/` payloads, `LICENSE`, and `NOTICE`. Each standalone zip contains one top-level skill directory with its `LICENSE.txt`. No tests, live harness, docs, caches, or evidence are included.

```python
ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)

def zip_info(name: str, executable: bool) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, ZIP_EPOCH)
    mode = 0o755 if executable else 0o644
    info.external_attr = (stat.S_IFREG | mode) << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    return info
```

- [ ] **Step 4: Implement fresh extraction and install smokes**

Reject absolute paths, `..`, duplicates, case-fold collisions, and unexpected members before extraction. Extract to `tempfile.TemporaryDirectory`, validate both plugin skills, run Korean/image deterministic evaluators against extracted skill roots, and run inspector tests against the extracted inspector.

- [ ] **Step 5: Run release tests and a local build**

```bash
python3 -m unittest discover -s tests/contract -p 'test_release.py' -v
python3 scripts/build_release.py --version 2.0.0 --output dist
shasum -a 256 -c dist/SHA256SUMS
```

Expected: three zips plus `SHA256SUMS`; all archive/extraction/install tests pass. `SHA256SUMS` lists exactly the three zips.

- [ ] **Step 6: Commit release tooling, not generated artifacts**

```bash
git add scripts/build_release.py tests/contract/test_release.py .gitignore docs/maintainers/release-process.md
git commit -m "build: add deterministic v2 release archives"
```

---

### Task 10: Complete public-surface audit, changelog, and independent review

**Files:**
- Create: `CHANGELOG.md`
- Modify: any public-repository file identified by review, limited to spec compliance.

**Interfaces:**
- Consumes: complete new repository candidate.
- Produces: a clean, review-approved commit whose full verifier and release tests pass and whose public surface contains no private or unsupported claim.

- [ ] **Step 1: Add the v2.0.0 changelog entry**

Record initial public plugin, the two migrated skills, installed-payload separation, provider-free verification, opt-in live boundary, Apache-2.0, and Archive provenance. Do not claim the release exists before Task 11.

- [ ] **Step 2: Run the complete local gate from a clean candidate**

```bash
python3 scripts/capture_archive_manifest.py verify --repository "$SKILLS_ARCHIVE_CHECKOUT" --manifest docs/maintainers/archive-source-manifest.json
python3 scripts/verify.py --profile full
python3 scripts/build_release.py --version 2.0.0 --output dist
shasum -a 256 -c dist/SHA256SUMS
git diff --check
git status --short --branch --untracked-files=all
```

- [ ] **Step 3: Run explicit public-surface scans**

```bash
PERSONAL_HOME_PATTERN='/''Users/'
PRIVATE_SOURCE_PATTERN='source/''private'
rg -n --hidden --glob '!.git/**' --glob '!docs/maintainers/archive-*' --glob '!docs/superpowers/**' --glob '!tests/**/cases.json' \
  "$PERSONAL_HOME_PATTERN|$PRIVATE_SOURCE_PATTERN|OPENAI_API_KEY|ANTHROPIC_API_KEY|CURSOR_API_KEY|kws-korean-writing-editor|kws-image-workbench" .
find skills -type l -o -type s -o -type p
```

Expected: no unallowlisted match and no symlink/socket/FIFO in payload. Manually inspect every allowlisted migration/near-miss occurrence.

Review authoritative external links from the README and `docs/` once as a nonblocking release procedure. Record broken or redirected authoritative locators as release blockers, but keep network freshness outside required PR-time CI.

- [ ] **Step 4: Request independent code review**

Invoke `superpowers:requesting-code-review` against the approved spec and this plan. Require reviewers to check payload closure, test preservation, live non-execution, plugin schema, license/provenance, doc parity, release extraction safety, and the Archive deletion gate. Fix only evidenced findings and rerun the affected RED/GREEN/full gates.

- [ ] **Step 5: Commit review closeout and verify clean HEAD**

```bash
git add CHANGELOG.md . ':(exclude)dist'
git commit -m "docs: finalize public v2 release notes"
python3 scripts/verify.py --profile full
git status --short --branch --untracked-files=all
```

Expected: only ignored `dist/` may exist; tracked worktree is clean.

---

### Task 11: Merge, create the public GitHub repository, publish v2.0.0, and prove remote bytes

**Files:**
- No source changes expected.
- External state: `https://github.com/beyondwin/skills`, `main`, CI, tag `v2.0.0`, GitHub release, repository security settings.

**Interfaces:**
- Consumes: the reviewed clean feature-branch commit and locally verified artifacts.
- Produces: public remote main/tag equality, green required CI, four downloadable release artifacts, matching downloaded checksums, and extracted installation smokes from remote bytes.

- [ ] **Step 1: Use the finishing workflow and merge locally**

Invoke `superpowers:finishing-a-development-branch`. Merge `codex/public-skills-v2` into local `main` only after Task 10 passes. Rerun `python3 scripts/verify.py --profile full` on merged `main` and require a clean tree.

- [ ] **Step 2: Verify GitHub identity and remote-name collision before creation**

```bash
gh auth status
gh repo view beyondwin/skills --json nameWithOwner,visibility,url,defaultBranchRef 2>/dev/null || true
git remote -v
```

If a repository already exists, do not overwrite or force-push it. Verify ownership, visibility, history, and whether it is the intended empty target; any conflicting content blocks publication.

- [ ] **Step 3: Create the public repository and push main**

```bash
gh repo create beyondwin/skills --public --source=. --remote=origin
git push -u origin main
git ls-remote --heads origin main
```

Expected: remote `main` OID equals local reviewed `HEAD`.

- [ ] **Step 4: Wait for and inspect actual CI**

```bash
gh run list --repo beyondwin/skills --branch main --workflow verify.yml --limit 5
CI_RUN_ID="$(gh run list --repo beyondwin/skills --branch main --workflow verify.yml \
  --limit 1 --json databaseId --jq '.[0].databaseId')"
gh run watch "$CI_RUN_ID" --repo beyondwin/skills --exit-status
```

Require green Ubuntu, macOS, and Windows jobs. A queued, skipped, missing, or unavailable job is not green.

Create a fresh temporary clone from the public URL and run `python3 scripts/verify.py --profile full` there before tagging. This is the fresh-clone acceptance proof; a passing development worktree alone is insufficient.

- [ ] **Step 5: Configure supported public-repository security settings**

Enable private vulnerability reporting, secret scanning, push protection, CodeQL default setup, and branch protection with the actual CI check name using `gh api` when the account supports each setting. Dependabot file configuration is already tracked. If GitHub rejects a setting because of account/plan support, record it as a manual external limitation; do not claim it enabled.

- [ ] **Step 6: Tag the exact green commit and publish built artifacts**

```bash
git tag -a v2.0.0 -m "beyondwin-skills v2.0.0"
git push origin v2.0.0
python3 scripts/build_release.py --version 2.0.0 --output dist
gh release create v2.0.0 dist/beyondwin-skills-v2.0.0.zip \
  dist/korean-writing-editor-v2.0.0.zip dist/image-workbench-v2.0.0.zip \
  dist/SHA256SUMS --repo beyondwin/skills --verify-tag \
  --title "beyondwin-skills v2.0.0" --notes-file CHANGELOG.md
```

- [ ] **Step 7: Redownload and verify remote bytes in a fresh directory**

```bash
RELEASE_DOWNLOAD_DIR="$(mktemp -d)"
gh release download v2.0.0 --repo beyondwin/skills --dir "$RELEASE_DOWNLOAD_DIR"
(cd "$RELEASE_DOWNLOAD_DIR" && shasum -a 256 -c SHA256SUMS)
python3 scripts/build_release.py --verify-download "$RELEASE_DOWNLOAD_DIR" --version 2.0.0
git ls-remote origin refs/heads/main refs/tags/v2.0.0 'refs/tags/v2.0.0^{}'
```

Expected: four files download; checksums and fresh extraction/install smokes pass; dereferenced tag commit equals remote main and local reviewed `HEAD`.

- [ ] **Step 8: Confirm public links and release inventory**

Use `gh api` or direct HTTP status checks for both skill source URLs, README links, release page, and all artifact URLs. Only after every Task 11 gate succeeds may Archive mutation begin.

---

### Task 12: Open the Archive removal worktree and prove the deletion gate again

**Files:**
- No mutation in this task.
- External checkout: a new Archive worktree on `codex/remove-migrated-public-skills`.

**Interfaces:**
- Consumes: public proof from Task 11 and the pinned Archive manifest.
- Produces: an isolated clean Archive removal branch based on current `origin/main`, with the two source prefixes unchanged from the published manifest.

- [ ] **Step 1: Refresh Archive without changing it**

```bash
git -C "$SKILLS_ARCHIVE_CHECKOUT" fetch origin --prune
git -C "$SKILLS_ARCHIVE_CHECKOUT" status --short --branch --untracked-files=all
git -C "$SKILLS_ARCHIVE_CHECKOUT" rev-parse origin/main
git -C "$SKILLS_ARCHIVE_CHECKOUT" worktree list --porcelain
```

- [ ] **Step 2: Re-run the complete public deletion gate**

Recheck remote main/tag OIDs, actual CI, four downloads, checksum verification, install smokes, manifest digest, public links, and unsupported-claim scan. Do not reuse local `dist/` as proof.

- [ ] **Step 3: Verify Archive source has not drifted since publication**

Run the manifest verifier against current Archive. If unrelated Archive main advanced, allow it only when every selected source entry still matches. Any change under either source prefix blocks deletion and requires a new import/release cycle.

- [ ] **Step 4: Create the isolated Archive worktree**

Invoke `superpowers:using-git-worktrees` and create `codex/remove-migrated-public-skills` from current `origin/main`. Run Archive mandatory preflight in that worktree: `pwd`, full status, branch, `git rev-parse HEAD`, nearest `AGENTS.md`, and `git worktree list --porcelain`.

---

### Task 13: Remove Archive contracts, routing, docs, skill trees, and safe local residues

**Files:**
- Modify: `AGENTS.md`
- Modify: `README.md`
- Modify: `skills/AGENTS.md`
- Modify: `skills/README.md`
- Modify: `scripts/agent/contract.ts`
- Modify: `scripts/agent/check-contract.test.ts`
- Modify: `scripts/agent/verification-map.ts`
- Modify: `scripts/agent/verification-map.test.ts`
- Modify: `skills/_legacy/kws-claude-plan-runner/evals/test_skill_contract.py`
- Modify: `skills/_legacy/kws-codex-plan-runner/evals/test_skill_contract.py`
- Delete: `skills/korean-writing-editor/`
- Delete: `skills/image-workbench/`
- Delete: `docs/operations/2026-08-23-kws-korean-writing-editor-cross-model-evaluation.md`
- Delete: `docs/superpowers/plans/2026-08-22-kws-korean-writing-editor.md`
- Delete: `docs/superpowers/plans/2026-08-23-kws-image-workbench.md`
- Delete: `docs/superpowers/plans/2026-08-23-kws-korean-writing-editor-cross-model-evaluation.md`
- Delete: `docs/superpowers/plans/2026-08-23-kws-korean-writing-editor-live-hardening.md`
- Delete: `docs/superpowers/plans/2026-08-25-skills-catalog-identity.md`
- Delete: `docs/superpowers/specs/2026-08-22-kws-korean-writing-editor-design.md`
- Delete: `docs/superpowers/specs/2026-08-23-kws-image-workbench-design.md`
- Delete: `docs/superpowers/specs/2026-08-23-kws-korean-writing-editor-cross-model-evaluation-design.md`
- Delete: `docs/superpowers/specs/2026-08-23-kws-korean-writing-editor-live-hardening-design.md`
- Delete: `docs/superpowers/specs/2026-08-25-skills-catalog-identity-design.md`
- Remove after safety proof: `.superpowers/worktrees/kws-korean-writing-editor-cross-model-evaluation`, `.superpowers/worktrees/kws-korean-writing-editor-live-hardening`, `.superpowers/worktrees/skills-catalog-identity`, and ignored `skills/kws-korean-writing-editor/` cache residue.

**Interfaces:**
- Consumes: current Archive contract and verification map.
- Produces: Archive contract/routing with no general-skill roots or commands, no current-tree/reference residue for the four identifiers, and no unrelated Waygent/legacy executor loss.

- [ ] **Step 1: Change Archive tests first to define the post-migration contract**

```typescript
test("does not require migrated public skill roots", () => {
  expect(REQUIRED_PATHS).not.toContain("skills/korean-writing-editor");
  expect(REQUIRED_PATHS).not.toContain("skills/image-workbench");
});

test("verification map has no migrated skill scopes", () => {
  expect(VERIFICATION_SCOPES.map(({ id }) => id)).not.toContain("korean-writing-editor");
  expect(VERIFICATION_SCOPES.map(({ id }) => id)).not.toContain("image-workbench");
});
```

Remove the two catalog-link assertions from each frozen plan-runner contract test; retain their runner version/frontmatter/changelog assertions.

- [ ] **Step 2: Run RED against unchanged Archive implementation**

```bash
bun test scripts/agent/check-contract.test.ts scripts/agent/verification-map.test.ts
python3 -m unittest skills/_legacy/kws-codex-plan-runner/evals/test_skill_contract.py
python3 -m unittest skills/_legacy/kws-claude-plan-runner/evals/test_skill_contract.py
```

Expected: TypeScript tests fail because both required roots and verification scopes still exist.

- [ ] **Step 3: Remove contract and verification registrations minimally**

Delete only the two `REQUIRED_PATHS` entries; two `ScopeId` members; three command constants; two verification scopes; and the three commands from `OFFLINE_COMMANDS`. Preserve all Waygent, native, package, console, frozen runner, and executor scopes. Update exact expected arrays in tests.

- [ ] **Step 4: Remove mixed documentation clauses**

Remove Archive's statement that `skills/` is canonical for the two public skills, their task-routing bullets, their root catalog summary, the two catalog rows, install/invocation guidance, and the two active-skill routing rules. Preserve `_legacy` rules and Waygent ownership. `skills/README.md` may remain as a legacy-tree pointer, but must not redirect to or name the migrated public skills.

- [ ] **Step 5: Delete single-purpose tracked files and both complete skill directories**

Use an exact explicit path list. Do not glob `skills/kws-*`, `docs/superpowers/*`, or any broad directory. Review `git diff --stat` immediately and confirm that only the paths enumerated in this task changed.

- [ ] **Step 6: Make focused tests GREEN**

```bash
bun test scripts/agent/check-contract.test.ts scripts/agent/verification-map.test.ts
python3 -m unittest skills/_legacy/kws-codex-plan-runner/evals/test_skill_contract.py
python3 -m unittest skills/_legacy/kws-claude-plan-runner/evals/test_skill_contract.py
bun run agent:contract
```

- [ ] **Step 7: Remove the three clean merged auxiliary worktrees without force**

For each of these exact branches, recheck `git status --short`, then require `git merge-base --is-ancestor <branch> main`:

```text
codex/kws-korean-writing-editor-cross-model-evaluation
kws-korean-writing-editor-live-hardening
skills-catalog-identity
```

Only if clean and merged, run `git worktree remove <exact-worktree-path>` and `git branch -d <exact-branch>`. If either precondition changed, stop; do not use `--force` or `-D`.

- [ ] **Step 8: Remove the inspected ignored cache-only residue**

Reinspect `skills/kws-korean-writing-editor/` and require that it contains only `evals/__pycache__/*.pyc`/`*.pyo` regular files and directories. Remove that exact ignored directory. Any source, symlink, special file, or unrelated content blocks cleanup.

---

### Task 14: Prove zero Archive residue, verify the whole repository, commit, merge, and push

**Files:**
- Modify/delete only the exact Task 13 surfaces.
- External state: Archive removal commit on `main` and `origin/main`.

**Interfaces:**
- Consumes: Task 13 removal candidate and public release proof.
- Produces: one normal revertible Archive removal commit, complete relevant verification, zero current/ignored residue outside `.git`, and remote main proof.

- [ ] **Step 1: Run content and filename zero-residue scans**

```bash
rg -n --hidden --no-ignore --glob '!.git/**' \
  'korean-writing-editor|image-workbench|kws-korean-writing-editor|kws-image-workbench' .
find . -path './.git' -prune -o \( \
  -iname '*korean-writing-editor*' -o -iname '*image-workbench*' \
  -o -iname '*kws-korean-writing-editor*' -o -iname '*kws-image-workbench*' \
\) -print
```

Expected: no output. Inspect any match; do not suppress or blanket-allow it.

- [ ] **Step 2: Review deletion scope and unrelated preservation**

```bash
git status --short --branch --untracked-files=all
git diff --stat
git diff -- AGENTS.md README.md skills/AGENTS.md skills/README.md \
  scripts/agent/contract.ts scripts/agent/check-contract.test.ts \
  scripts/agent/verification-map.ts scripts/agent/verification-map.test.ts
git diff --check
```

Confirm that Waygent application/package/native paths and every unrelated `_legacy` skill remain present.

- [ ] **Step 3: Run Archive's complete relevant gate**

```bash
bun test scripts/agent
bun run agent:contract
bun run agent:verify
git diff --check
```

Any opt-in provider smoke remains skipped and is reported as not run; no billable action is authorized by this plan.

- [ ] **Step 4: Request final Archive review**

Use `superpowers:requesting-code-review` to compare the deletion diff with the Task 13 explicit list, confirm zero identifiers, check verification-map closure, and look for unrelated loss. Fix evidenced findings only and rerun Steps 1–3.

- [ ] **Step 5: Commit the deletion separately**

```bash
git add -A -- . ':(exclude)**/.DS_Store'
git commit -m "chore: remove migrated public skills from Archive"
git status --short --branch --untracked-files=all
```

- [ ] **Step 6: Merge non-destructively and verify merged main**

Invoke `superpowers:finishing-a-development-branch`. Merge into current Archive `main` only when it still fast-forwards from the reviewed base; if remote main advanced, integrate normally and rerun the full zero-residue and verification gates.

- [ ] **Step 7: Push and prove remote state**

```bash
git push origin main
git ls-remote origin refs/heads/main
git log -1 --oneline --decorate
```

Expected: remote Archive main equals the verified local removal commit. Report the new public repository commit/tag/release evidence, Archive removal commit, commands and results, skipped opt-in evidence, external settings that were unavailable, and rollback via `git revert <removal-commit>`.

---

## Final Acceptance Matrix

| Claim | Required fresh evidence |
| --- | --- |
| New repository deterministic contract | `python3 scripts/verify.py --profile full` exits 0 from clean merged main. |
| Korean preservation | 8 self-tests, 31 cases with exact category counts, mutation checks, and 209 provider-free live tests pass. |
| Image preservation | 29 evaluator tests, 31 cases with exact category counts, 8 mutations, and 24 external inspector tests pass. |
| Installed payload closure | Staged-copy and release-extraction tests show no evals, maintainer docs, private paths, or Archive-relative assumptions. |
| Public distribution | Remote main and dereferenced `v2.0.0` match; CI is green; four artifacts redownload; checksums and extraction smokes pass. |
| Archive deletion authority | All public distribution evidence is fresh before any Archive mutation. |
| Archive completeness | Exact content and filename scans produce zero matches outside `.git`, including ignored paths and removable worktrees. |
| Archive safety | `bun test scripts/agent`, `bun run agent:contract`, `bun run agent:verify`, diff review, and independent review pass. |
| Recoverability | Public source and release artifacts remain available; Archive history is unchanged; removal is one normal commit reversible with `git revert`. |
