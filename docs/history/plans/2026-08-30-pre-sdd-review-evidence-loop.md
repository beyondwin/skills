# Pre-SDD Review Evidence Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a provider-neutral `pre-sdd-review-evidence` CLI that records bounded local review receipts, links downstream outcomes, and produces deterministic improvement signals without changing review verdicts or storing source content.

**Architecture:** Bundle a Python-standard-library evidence package inside `skills/pre-sdd-review/evidence/`, install one self-contained launcher explicitly, and store create-only run records under `~/.pre-sdd-review/` or `PRE_SDD_REVIEW_HOME`. The skill remains the semantic controller; the CLI owns Git facts, hashes, identity, validation, atomic persistence, matching, and aggregation. Product payload, archive, documentation, and verification contracts stay exact and fail closed as the runtime surface expands.

**Tech Stack:** Python 3.11+ standard library (`argparse`, `dataclasses`, `hashlib`, `hmac`, `json`, `pathlib`, `secrets`, `subprocess`, `tempfile`, `uuid`, `zipapp`), `unittest`, Git CLI, Markdown/TOML product contracts

**Spec:** `docs/history/specs/2026-08-30-pre-sdd-review-evidence-loop-design.md`

## Global Constraints

- The data root is exactly `~/.pre-sdd-review/`; `PRE_SDD_REVIEW_HOME` is the only supported override.
- The installed command is exactly `pre-sdd-review-evidence`.
- Candidate versions are `pre-sdd-review` `1.2.0`, CLI `1.0.0`, and receipt schema `1`.
- The CLI uses only the Python standard library and makes no model, provider, telemetry, upload, or network call.
- The plan path is primary; the design is resolved only from the plan's `**Spec:**` field.
- The skill and agent own semantic findings, document repairs, protocol-compliance observations, and verdicts. The CLI never creates or changes `READY`, `REVISE`, or `BLOCKED`.
- Evidence failure is always visible as `Evidence: not_recorded; reason=<code>` and never changes the review verdict.
- `review.json` is create-only with a 16 KiB soft target and 32 KiB hard limit. `outcome.json` is create-only with a 4 KiB soft target and 8 KiB hard limit. Completed runs have a 40 KiB hard limit.
- Persist no absolute repository or skill paths, source bodies, prompts, full model responses, provider transcripts, arbitrary command output, credentials, or environment-variable values.
- Repository paths in receipts are POSIX relative paths without `..` and must resolve inside the repository after symlink resolution.
- `review.json` is immutable. Later disputes are stored only in `outcome.downstream.disputed_findings`.
- Schema `1` records one terminal outcome and has no silent overwrite or outcome-amendment mechanism.
- Completed receipts are retained indefinitely by default. Deletion is explicit, previewed, and confirmed.
- There is no global JSONL writer, global write lock, daemon, database, or automatic background analysis.
- Real-project outcomes cannot rank clients. Cross-client comparisons require the same synthetic fixture, skill fingerprint, schema, and protocol level.
- `products.toml` continues to claim semantic review support only for Codex. CLI portability and review-host support remain separate.
- No live provider or billable cross-client call is required by CI or this implementation plan. Such checks remain explicit and `not_measured` until separately authorized and run.
- No tag, push, GitHub Release, catalog mutation, or publication is part of this plan.

## File and Interface Map

### Runtime package

- `skills/pre-sdd-review/evidence/pre_sdd_review_evidence/__init__.py` — CLI and schema version constants.
- `skills/pre-sdd-review/evidence/pre_sdd_review_evidence/__main__.py` — `python -m pre_sdd_review_evidence` entry point.
- `skills/pre-sdd-review/evidence/pre_sdd_review_evidence/schema.py` — enumerations, canonical JSON encoding, review/outcome validation, size limits, and deterministic assessment.
- `skills/pre-sdd-review/evidence/pre_sdd_review_evidence/repository.py` — Git discovery, dirty/HEAD capture, deterministic `**Spec:**` resolution, hashing, path safety, identity-key lifecycle, and HMAC repository IDs.
- `skills/pre-sdd-review/evidence/pre_sdd_review_evidence/storage.py` — evidence-home layout, per-run pending/final lifecycle, per-run locking, atomic create-only writes, reads, and run scanning.
- `skills/pre-sdd-review/evidence/pre_sdd_review_evidence/reporting.py` — resolution matching, summary metrics, candidate selection/export, pending classification, and prune selection.
- `skills/pre-sdd-review/evidence/pre_sdd_review_evidence/cli.py` — argument parsing, command orchestration, JSON stdout/stderr, and stable exit codes.
- `skills/pre-sdd-review/evidence/install.py` — explicit zipapp/launcher installation into a caller-selected PATH directory without overwriting existing files.
- `skills/pre-sdd-review/evidence/README.md` — runtime requirements, install, commands, data root, safety, backup, and removal.

### Tests and product routing

- `tests/products/pre-sdd-review/evidence/__init__.py` — makes recursive unittest discovery portable.
- `tests/products/pre-sdd-review/evidence/support.py` — imports the packaged CLI and creates isolated Git/skill/evidence fixtures.
- `tests/products/pre-sdd-review/evidence/test_schema.py` — schema and assessment contract.
- `tests/products/pre-sdd-review/evidence/test_repository.py` — repository resolution, hashes, identity, and path safety.
- `tests/products/pre-sdd-review/evidence/test_storage.py` — atomic lifecycle, permissions, concurrency, corruption, and interruption.
- `tests/products/pre-sdd-review/evidence/test_cli.py` — end-to-end command contract and privacy-safe errors.
- `tests/products/pre-sdd-review/evidence/test_reporting.py` — matching, summary, candidates, export, and prune.
- `tests/products/pre-sdd-review/evidence/test_install.py` — POSIX and Windows launcher generation and no-overwrite behavior.
- `products.toml` — add `pre-sdd-review-evidence` to the pre-SDD product stages without adding semantic host claims.
- `scripts/lib/verification.py` — register the evidence unittest stage on full and Windows-portable profiles.
- `scripts/lib/product_contract.py` — allow the product-specific `evidence/` payload while rejecting it on other skills.
- `scripts/release.py` — keep the pre-SDD payload and archive inventory exact as evidence files are added.
- `tests/products/pre-sdd-review/test_contract.py` — close instruction, documentation, payload, and new evidence workflow contracts.
- `tests/repository/test_release_contract.py` — update the expected `1.2.0` identity and verify executable modes remain bounded.

### Skill and documentation

- `skills/pre-sdd-review/SKILL.md` — start/finalize evidence when compatible, report non-recording explicitly, and hand `run_id` to combined SDD.
- `skills/pre-sdd-review/README.md` and `README.en.md` — user-facing evidence install/use and non-blocking behavior.
- `skills/pre-sdd-review/CHANGELOG.md` and `release.toml` — `1.2.0` contract.
- `docs/maintainers/products/pre-sdd-review/contract.md` — evidence responsibility and verdict independence.
- `docs/maintainers/products/pre-sdd-review/testing.md` — evidence stage, synthetic lifecycle matrix, and optional live boundary.
- `docs/maintainers/products/pre-sdd-review/compatibility.md` — separate CLI OS evidence from semantic host support.
- `docs/maintainers/products/pre-sdd-review/release.md` — new payload/version and check/build/verify-download procedure.
- `docs/users/ko/installation.md` and `docs/users/en/installation.md` — explicit CLI installation and PATH inspection.
- `docs/users/ko/safety-and-privacy.md` and `docs/users/en/safety-and-privacy.md` — local evidence contents and prohibited data.
- `docs/users/ko/verification.md` and `docs/users/en/verification.md` — provider-free evidence stage and no-live-quality limit.

---

### Task 1: Close the Schema and Product Boundary

**Files:**
- Create: `skills/pre-sdd-review/evidence/pre_sdd_review_evidence/__init__.py`
- Create: `skills/pre-sdd-review/evidence/pre_sdd_review_evidence/schema.py`
- Create: `tests/products/pre-sdd-review/evidence/__init__.py`
- Create: `tests/products/pre-sdd-review/evidence/support.py`
- Create: `tests/products/pre-sdd-review/evidence/test_schema.py`
- Modify: `scripts/lib/product_contract.py`
- Modify: `scripts/lib/verification.py`
- Modify: `scripts/release.py`
- Modify: `products.toml`
- Modify: `tests/products/pre-sdd-review/test_contract.py`
- Modify: `tests/repository/test_release_contract.py`
- Modify: `skills/pre-sdd-review/SKILL.md`
- Modify: `skills/pre-sdd-review/CHANGELOG.md`
- Modify: `skills/pre-sdd-review/release.toml`
- Modify: `docs/maintainers/products/pre-sdd-review/release.md`

**Interfaces:**
- Consumes: current `ProductRelease`, `validate_product()`, exact pre-SDD payload checks, and `pre-sdd-review-contract` stage.
- Produces: `SCHEMA_VERSION: int`, `CLI_VERSION: str`, `EvidenceError`, `canonical_json_bytes(value) -> bytes`, `validate_review(value) -> dict[str, object]`, `validate_outcome(value, review) -> dict[str, object]`, and `derive_assessment(review, downstream) -> str`.

- [ ] **Step 1: Write failing schema tests**

Create a test loader in `support.py` that prepends `skills/pre-sdd-review/evidence` to `sys.path`, then add exact tests such as:

```python
def test_review_limits_and_enums_are_exact(self) -> None:
    self.assertEqual(schema.SCHEMA_VERSION, 1)
    self.assertEqual(schema.REVIEW_HARD_LIMIT, 32 * 1024)
    self.assertEqual(schema.OUTCOME_HARD_LIMIT, 8 * 1024)
    self.assertEqual(schema.VERDICTS, frozenset({"READY", "REVISE", "BLOCKED"}))
    self.assertEqual(
        schema.FINDING_CLASSES,
        frozenset({"authority-drift", "repo-reality", "coverage", "ordering", "verification-gap"}),
    )

def test_false_ready_requires_ready_and_material_escape(self) -> None:
    review = valid_review(verdict="REVISE")
    downstream = valid_downstream(escaped_findings=[{"class": "coverage", "severity": "BLOCKER"}])
    with self.assertRaisesRegex(schema.EvidenceError, "false-ready requires READY"):
        schema.validate_outcome(valid_outcome(label="false-ready", downstream=downstream), review)
```

Also cover unknown top-level fields, nullable resolution failures, 300-character bounded finding prose, forbidden absolute paths, `..`, prohibited content-bearing keys (`prompt`, `response`, `document_body`, `code`, `environment`), canonical sorted UTF-8 JSON, and hard-size rejection.

- [ ] **Step 2: Run the schema tests to verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests/products/pre-sdd-review/evidence -p 'test_schema.py' -v
```

Expected: FAIL because `pre_sdd_review_evidence.schema` does not exist.

- [ ] **Step 3: Implement the schema package**

Define constants in `__init__.py`:

```python
CLI_VERSION = "1.0.0"
SCHEMA_VERSION = 1
```

Implement `EvidenceError` with stable `code` and `message`, canonical encoding with `ensure_ascii=False`, `sort_keys=True`, compact separators, and a trailing newline. Validate exact top-level/nested key sets and all enum relationships; return a normalized copy rather than mutating the caller's dictionary.

```python
class EvidenceError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message

def canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")
```

The assessment derivation order must be `false-ready`, `noisy`, `prevented-rework`, `good`, then `inconclusive`; `abandoned` is selected only from a downstream abandoned status.

- [ ] **Step 4: Run schema tests to verify GREEN**

Run the Step 2 command.

Expected: PASS.

- [ ] **Step 5: Write failing product-boundary tests**

Add tests proving:

```python
def test_pre_sdd_review_evidence_payload_is_allowed_only_for_pre_sdd(self) -> None:
    self.assertEqual(validate_product(ROOT / "skills/pre-sdd-review", REGISTRY), [])
    copied = self._copy("how-it-works")
    (copied / "evidence").mkdir()
    (copied / "evidence/probe.py").write_text("pass\n", encoding="utf-8")
    self.assertIn("unexpected top-level file: evidence", validate_product(copied, REGISTRY))
```

Update expected payload inventories to include only the two new runtime files. Add a verification-routing test expecting `pre-sdd-review-evidence` in the product's stage list.

- [ ] **Step 6: Run product tests to verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.repository.test_release_contract -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests/products/pre-sdd-review -p 'test_contract.py' -v
```

Expected: FAIL because `evidence/` is rejected, the stage is absent, the payload allowlist is stale, and the version is still `1.1.0`.

- [ ] **Step 7: Open the exact product and release boundary**

In `product_contract.py`, compute the allowed top level per product instead of adding `evidence` globally:

```python
allowed_top_level = ALLOWED_TOP_LEVEL
if skill_root.name == "pre-sdd-review":
    allowed_top_level = allowed_top_level | {"evidence"}
```

Register `pre-sdd-review-evidence` as its own unittest-discovery stage and append it to the pre-SDD `verify_stages`. Extend both copies of `PRE_SDD_REVIEW_PAYLOAD_FILES` with the exact present evidence files. Keep arbitrary extra files rejected.

- [ ] **Step 8: Advance the product identity to 1.2.0**

Update `release.toml`, `SKILL.md` frontmatter, release docs, changelog, and repository expected versions to `1.2.0`. Add a dated changelog entry that states the local evidence CLI is optional, non-blocking, provider-neutral, and content-bounded. Recompute only the affected canonical instruction/document digests with the existing `whole_document_digest()` and `canonical_digest()` helpers; never weaken or remove those checks.

- [ ] **Step 9: Run the task gate**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --skill pre-sdd-review
git diff --check
```

Expected: all pre-SDD stages PASS; no whitespace errors.

- [ ] **Step 10: Commit**

```bash
git add products.toml scripts/lib/product_contract.py scripts/lib/verification.py \
  scripts/release.py skills/pre-sdd-review tests/products/pre-sdd-review \
  tests/repository/test_release_contract.py \
  docs/maintainers/products/pre-sdd-review/release.md
git commit -m "feat: define pre-sdd evidence schema"
```

### Task 2: Capture Repository, Plan, and Identity Facts

**Files:**
- Create: `skills/pre-sdd-review/evidence/pre_sdd_review_evidence/repository.py`
- Create: `tests/products/pre-sdd-review/evidence/test_repository.py`
- Modify: `tests/products/pre-sdd-review/evidence/support.py`
- Modify: `scripts/release.py`
- Modify: `tests/products/pre-sdd-review/test_contract.py`

**Interfaces:**
- Consumes: `EvidenceError`, schema path rules, Git CLI, skill root, plan argument, evidence home.
- Produces: `GitSnapshot(head: str, dirty: bool)`, `SkillSnapshot`, `TargetSnapshot`, `git_snapshot(repo_root)`, `resolve_target(start, plan_argument, identity_key)`, `load_or_create_identity(evidence_home)`, and `repository_id(repo_root, identity_key)`.

- [ ] **Step 1: Write failing repository-resolution tests**

Use isolated temporary Git repositories and assert:

```python
def test_root_relative_spec_resolves_and_stores_only_relative_paths(self) -> None:
    repo = make_git_repo(self.workspace)
    write(repo / "docs/plan.md", "# Plan\n\n**Spec:** docs/design.md\n")
    write(repo / "docs/design.md", "# Design\n")
    target = repository.resolve_target(repo, Path("docs/plan.md"), b"k" * 32)
    self.assertEqual(target.resolution_status, "resolved")
    self.assertEqual(target.plan_path, "docs/plan.md")
    self.assertEqual(target.design_path, "docs/design.md")
    self.assertNotIn(str(repo), repr(target))
```

Cover `./design.md` as plan-directory-relative, plain paths as repository-root-relative, duplicate `**Spec:**`, missing plan, missing field, missing design, absolute/outside paths, `..`, symlink escape, unborn HEAD, tracked/untracked dirty state, SHA-256, and stable/different HMAC IDs.

- [ ] **Step 2: Run repository tests to verify RED**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests/products/pre-sdd-review/evidence -p 'test_repository.py' -v
```

Expected: FAIL because `repository.py` does not exist.

- [ ] **Step 3: Implement deterministic path and Git resolution**

Use argument-list subprocess calls only:

```python
def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
        text=True,
    )
```

Resolution rules are exact:

1. Locate the Git root with `git rev-parse --show-toplevel`.
2. Accept an absolute plan input only when its resolved path is inside that root; persist only its relative path.
3. Resolve `**Spec:** ./name` from the plan directory.
4. Resolve every other relative `**Spec:**` value from the repository root.
5. Reject zero or multiple `**Spec:**` fields, absolute/tilde values, `..`, missing files, and post-resolution escapes.

Use `git rev-parse --verify HEAD` with `unborn` fallback and `git status --porcelain=v1 --untracked-files=normal` for dirty state.

- [ ] **Step 4: Implement local identity initialization**

`config.json` contains schema version, UTC creation time, and SHA-256 fingerprint of a 32-byte `identity.key`. First setup creates both with user-only permissions where supported. Existing config plus missing or mismatched key raises `identity-key-missing` and never regenerates automatically.

```python
def repository_id(repo_root: Path, identity_key: bytes) -> str:
    canonical = str(repo_root.resolve()).encode("utf-8")
    return hmac.new(identity_key, canonical, hashlib.sha256).hexdigest()
```

- [ ] **Step 5: Update exact payload inventories**

Add only `evidence/pre_sdd_review_evidence/repository.py` to both pre-SDD payload allowlists. Add a mutation test proving an unlisted sibling such as `evidence/pre_sdd_review_evidence/network.py` is rejected.

- [ ] **Step 6: Run the task gate**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests/products/pre-sdd-review/evidence -p 'test_repository.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --skill pre-sdd-review
git diff --check
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add skills/pre-sdd-review/evidence/pre_sdd_review_evidence/repository.py \
  tests/products/pre-sdd-review/evidence tests/products/pre-sdd-review/test_contract.py \
  scripts/release.py
git commit -m "feat: capture pre-sdd repository evidence"
```

### Task 3: Implement Atomic Run Storage and Core Commands

**Files:**
- Create: `skills/pre-sdd-review/evidence/pre_sdd_review_evidence/storage.py`
- Create: `skills/pre-sdd-review/evidence/pre_sdd_review_evidence/cli.py`
- Create: `skills/pre-sdd-review/evidence/pre_sdd_review_evidence/__main__.py`
- Create: `tests/products/pre-sdd-review/evidence/test_storage.py`
- Create: `tests/products/pre-sdd-review/evidence/test_cli.py`
- Modify: `tests/products/pre-sdd-review/evidence/support.py`
- Modify: `scripts/release.py`
- Modify: `tests/products/pre-sdd-review/test_contract.py`

**Interfaces:**
- Consumes: schema validation, `TargetSnapshot`, identity initialization, filesystem.
- Produces: `EvidencePaths`, `RunHandle`, `WriteResult`, `evidence_home()`, `create_pending()`, `finish_review()`, `abandon_run()`, `load_review()`, `scan_runs()`, and CLI commands `start`, `finish-review`, `show`, `pending`, `abandon`, `doctor`.

- [ ] **Step 1: Write failing storage lifecycle tests**

Cover a complete create/finalize lifecycle and create-only conflict:

```python
def test_finish_review_is_atomic_create_only_and_idempotent(self) -> None:
    handle = storage.create_pending(self.paths, pending_record())
    first = storage.finish_review(self.paths, handle.run_id, valid_review())
    second = storage.finish_review(self.paths, handle.run_id, valid_review())
    self.assertEqual(first.sha256, second.sha256)
    with self.assertRaisesRegex(EvidenceError, "conflicting retry"):
        storage.finish_review(self.paths, handle.run_id, valid_review(verdict="REVISE"))
```

Also test `YYYY/MM/<uuid>/`, private file modes where supported, no global lock, per-run lock conflicts, pending cleanup after finalization, interrupted/stale age classes, abandon to null-verdict durable review, corrupt JSON exclusion, and no automatic deletion.

- [ ] **Step 2: Run storage tests to verify RED**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests/products/pre-sdd-review/evidence -p 'test_storage.py' -v
```

Expected: FAIL because storage is absent.

- [ ] **Step 3: Implement evidence paths and per-run atomic writes**

```python
@dataclasses.dataclass(frozen=True)
class EvidencePaths:
    home: Path
    config: Path
    identity_key: Path
    runs: Path
    exports: Path

def evidence_home(environ: Mapping[str, str], user_home: Path) -> Path:
    override = environ.get("PRE_SDD_REVIEW_HOME")
    return Path(override).expanduser() if override else user_home / ".pre-sdd-review"
```

Use a per-run `.write.lock` created with `os.O_CREAT | os.O_EXCL`. Write canonical bytes to a private temp file in the run directory, flush and `os.fsync()`, then replace only while the per-run lock is held and only after proving the final path is absent. Remove the lock in `finally`; `doctor` reports abandoned lock files instead of silently deleting them.

- [ ] **Step 4: Write failing core CLI tests**

Invoke `cli.main()` with injected streams/environment/cwd and test exact JSON status/error records:

```python
def test_start_then_finish_reports_run_and_writes_review(self) -> None:
    started = run_cli(["start", "--skill-root", str(SKILL), "--plan", "docs/plan.md", "--client", "cursor"])
    self.assertEqual(started.code, 0)
    run_id = started.json["run_id"]
    finished = run_cli(["finish-review", "--run-id", run_id, "--from-stdin"], stdin=semantic_result_json())
    self.assertEqual(finished.json, {"status": "recorded", "run_id": run_id, "sha256": finished.json["sha256"]})
```

Cover unavailable home, resolution-status `BLOCKED` capture, invalid stdin, oversized records, missing run, exact retry, conflicting retry, `show`, `pending`, `abandon`, and `doctor`. Error JSON may include stable codes and bounded messages but never absolute paths.

- [ ] **Step 5: Run CLI tests to verify RED**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests/products/pre-sdd-review/evidence -p 'test_cli.py' -v
```

Expected: FAIL because the CLI is absent.

- [ ] **Step 6: Implement core CLI orchestration**

Define an injectable entry point:

```python
def main(
    argv: list[str] | None = None,
    *,
    input_stream: TextIO | None = None,
    output_stream: TextIO | None = None,
    error_stream: TextIO | None = None,
    environ: Mapping[str, str] | None = None,
    cwd: Path | None = None,
) -> int:
    ...
```

Successful commands write one canonical JSON object to stdout. Failures write one object shaped as `{"error":{"code":"...","message":"..."}}` to stderr and return nonzero. `__main__.py` calls this `main()` only.

`finish-review --from-stdin` accepts only bounded semantic fields (`mode`, protocol facts, result, findings); the CLI merges them with pending and freshly recomputed repository facts.

- [ ] **Step 7: Add the three runtime files to exact payload checks**

Update both allowlists and keep the source/archive mutation tests exact. No runtime file receives executable mode inside the ZIP; users run the package through Python or the separately generated launcher.

- [ ] **Step 8: Run the task gate**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests/products/pre-sdd-review/evidence -p 'test_*.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --skill pre-sdd-review
git diff --check
```

Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add skills/pre-sdd-review/evidence/pre_sdd_review_evidence \
  tests/products/pre-sdd-review/evidence tests/products/pre-sdd-review/test_contract.py \
  scripts/release.py
git commit -m "feat: record pre-sdd review runs atomically"
```

### Task 4: Link Exact Downstream Outcomes

**Files:**
- Modify: `skills/pre-sdd-review/evidence/pre_sdd_review_evidence/schema.py`
- Modify: `skills/pre-sdd-review/evidence/pre_sdd_review_evidence/storage.py`
- Modify: `skills/pre-sdd-review/evidence/pre_sdd_review_evidence/cli.py`
- Create: `skills/pre-sdd-review/evidence/pre_sdd_review_evidence/reporting.py`
- Create: `tests/products/pre-sdd-review/evidence/test_outcome.py`
- Modify: `tests/products/pre-sdd-review/evidence/test_cli.py`
- Modify: `scripts/release.py`
- Modify: `tests/products/pre-sdd-review/test_contract.py`

**Interfaces:**
- Consumes: finalized reviews, current repository/plan snapshot, downstream fact JSON.
- Produces: `resolve_review(paths, repo_root, plan_path) -> MatchResult`, `record_outcome(paths, run_id, facts) -> WriteResult`, CLI `resolve`, CLI `record-outcome`, and deterministic outcome labels.

- [ ] **Step 1: Write failing matching and outcome tests**

Cover one exact match, changed plan, multiple exact reviews, no match, cross-repository HMAC mismatch, duplicate outcome, and invalid assessment combinations:

```python
def test_resolve_returns_ambiguous_instead_of_latest(self) -> None:
    first = finalize_ready_run(self.paths, self.repo)
    second = finalize_ready_run(self.paths, self.repo)
    result = reporting.resolve_review(self.paths, self.repo, Path("docs/plan.md"))
    self.assertEqual(result.status, "ambiguous")
    self.assertEqual(set(result.candidate_run_ids), {first.run_id, second.run_id})

def test_material_escape_derives_false_ready(self) -> None:
    facts = downstream_facts(
        escaped_findings=[{"class": "coverage", "severity": "BLOCKER", "basis": "verified-repository-evidence"}]
    )
    self.assertEqual(schema.derive_assessment(valid_review(verdict="READY"), facts), "false-ready")
```

- [ ] **Step 2: Run outcome tests to verify RED**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests/products/pre-sdd-review/evidence -p 'test_outcome.py' -v
```

Expected: FAIL because matching/outcome persistence does not exist.

- [ ] **Step 3: Implement exact-match resolution in reporting.py**

Scan validated reviews only. Match `repo_id`, normalized plan path, and current plan SHA-256 to `freshness.plan_final_sha256`. Return stable statuses `matched`, `stale`, `ambiguous`, or `not-found`; never infer that the newest run was used.

- [ ] **Step 4: Implement create-only outcome recording**

Validate recorder, terminal downstream status, plan-hash match, replan count, escaped/disputed finding records, basis, and confidence. Derive the assessment when facts are sufficient. `agent-inferred` remains distinct. Write `outcome.json` through the same per-run lock and atomic create-only path as review finalization.

- [ ] **Step 5: Add reporting.py to exact payload checks**

Add `evidence/pre_sdd_review_evidence/reporting.py` to both source and archive allowlists in this task, because `resolve` already imports it. Add a contract mutation proving an undeclared sibling report module remains rejected.

- [ ] **Step 6: Add CLI commands**

```text
resolve --repo <path> --plan <path>
record-outcome --run-id <id> --from-stdin
```

`record-outcome` rejects an existing outcome and documents that schema `1` has no amendment command.

- [ ] **Step 7: Run the task gate**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests/products/pre-sdd-review/evidence -p 'test_*.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --skill pre-sdd-review
git diff --check
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add skills/pre-sdd-review/evidence/pre_sdd_review_evidence \
  tests/products/pre-sdd-review/evidence tests/products/pre-sdd-review/test_contract.py \
  scripts/release.py
git commit -m "feat: link pre-sdd downstream outcomes"
```

### Task 5: Add Deterministic Reporting, Candidates, and Retention

**Files:**
- Modify: `skills/pre-sdd-review/evidence/pre_sdd_review_evidence/reporting.py`
- Create: `tests/products/pre-sdd-review/evidence/test_reporting.py`
- Modify: `skills/pre-sdd-review/evidence/pre_sdd_review_evidence/cli.py`
- Modify: `skills/pre-sdd-review/evidence/pre_sdd_review_evidence/storage.py`
- Modify: `scripts/release.py`
- Modify: `tests/products/pre-sdd-review/test_contract.py`

**Interfaces:**
- Consumes: validated review/outcome pairs and pending records.
- Produces: `summarize(records) -> dict[str, object]`, `select_candidates(records) -> tuple[Candidate, ...]`, `export_candidate(candidate, exports_root) -> Path`, `select_prune_runs(records, cutoff, include_without_outcome)`, and CLI `summary`, `candidates`, `prune`.

- [ ] **Step 1: Write failing reporting tests with fixed receipts**

Create content-free synthetic receipts and verify exact denominators:

```python
def test_summary_keeps_unknown_and_degraded_out_of_verified_rates(self) -> None:
    records = [
        run(verdict="READY", protocol="full", outcome="good", basis="verified-repository-evidence"),
        run(verdict="READY", protocol="full", outcome="false-ready", basis="verified-repository-evidence"),
        run(verdict="READY", protocol="degraded", outcome="good", basis="agent-inferred"),
        run(verdict="REVISE", protocol="full", outcome=None),
    ]
    summary = reporting.summarize(records)
    self.assertEqual(summary["outcome_coverage"], {"numerator": 3, "denominator": 4})
    self.assertEqual(summary["verified_false_ready"], {"numerator": 1, "denominator": 2})
```

Test immediate candidates, repeated thresholds across distinct run IDs, no automatic skill edit, blank sanitized export, small-sample warning, full/degraded client slices, pending age classes, dry-run prune, explicit confirmation, and default exclusion of review-only-without-outcome records.

- [ ] **Step 2: Run reporting tests to verify RED**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests/products/pre-sdd-review/evidence -p 'test_reporting.py' -v
```

Expected: FAIL because the summary, candidate, export, and prune interfaces do not exist yet.

- [ ] **Step 3: Implement pure aggregation and candidate functions**

Keep calculations pure and deterministic. Every rate is an object containing `numerator`, `denominator`, and `interpretation`; denominators below ten use `insufficient-sample`. Group by client, protocol execution, risk trigger, finding class, and anonymous repository ID without producing a client ranking.

Candidate export contains only:

```json
{
  "schema_version": 1,
  "candidate_id": "...",
  "finding_class": "verification-gap",
  "consequence_category": "escaped-material-defect",
  "required_synthetic_files": ["design.md", "plan.md", "repository.json", "expected.json"]
}
```

- [ ] **Step 4: Implement reporting and deletion CLI commands**

`summary` and `candidates` default to canonical JSON and accept `--format text` for human output. `candidates export <id>` writes only beneath `exports/`. `prune --older-than 730d --dry-run` lists exact run IDs; mutation requires `--confirm`. Refuse `--confirm` when the requested path or run selection escapes the evidence root.

- [ ] **Step 5: Preserve the exact payload boundary**

No runtime file is added in this task, so the Task 4 allowlists and archive expectations must remain unchanged. Keep undeclared report scripts and generated exports out of the product payload, and retain the exact-inventory mutation test.

- [ ] **Step 6: Run the task gate**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests/products/pre-sdd-review/evidence -p 'test_*.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --skill pre-sdd-review
git diff --check
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add skills/pre-sdd-review/evidence/pre_sdd_review_evidence \
  tests/products/pre-sdd-review/evidence tests/products/pre-sdd-review/test_contract.py \
  scripts/release.py
git commit -m "feat: summarize pre-sdd evidence locally"
```

### Task 6: Package and Install One Shared CLI

**Files:**
- Create: `skills/pre-sdd-review/evidence/install.py`
- Create: `skills/pre-sdd-review/evidence/README.md`
- Create: `tests/products/pre-sdd-review/evidence/test_install.py`
- Modify: `scripts/release.py`
- Modify: `tests/products/pre-sdd-review/test_contract.py`
- Modify: `tests/repository/test_release_contract.py`

**Interfaces:**
- Consumes: bundled evidence Python package and a user-selected directory already intended for PATH.
- Produces: `build_posix_launcher()`, `build_windows_launcher()`, `install(skill_root, bin_dir, platform) -> tuple[Path, ...]`, and an installed `pre-sdd-review-evidence` command.

- [ ] **Step 1: Write failing installer tests**

Cover POSIX and Windows render paths without changing the real home or PATH:

```python
def test_posix_install_creates_executable_zipapp_command(self) -> None:
    installed = installer.install(SKILL, self.bin_dir, platform="posix", python_executable=Path(sys.executable))
    command = self.bin_dir / "pre-sdd-review-evidence"
    self.assertIn(command, installed)
    self.assertTrue(command.stat().st_mode & stat.S_IXUSR)
    completed = subprocess.run([str(command), "--version"], capture_output=True, text=True, check=False)
    self.assertEqual(completed.returncode, 0)
    self.assertIn('"cli_version":"1.0.0"', completed.stdout)

def test_installer_refuses_nonidentical_existing_launcher(self) -> None:
    target = self.bin_dir / "pre-sdd-review-evidence"
    target.write_text("foreign\n", encoding="utf-8")
    with self.assertRaisesRegex(EvidenceError, "install target exists"):
        installer.install(SKILL, self.bin_dir, platform="posix", python_executable=Path(sys.executable))
```

Test identical reinstall idempotence, bin directory requirement, spaces in paths, Windows `.pyz` plus `.cmd` quoting, no shell-profile mutation, and no automatic PATH changes.

- [ ] **Step 2: Run installer tests to verify RED**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests/products/pre-sdd-review/evidence -p 'test_install.py' -v
```

Expected: FAIL because `install.py` does not exist.

- [ ] **Step 3: Implement explicit standard-library installation**

Use `zipapp.create_archive()` over a temporary staging directory containing only `pre_sdd_review_evidence/`.

- POSIX: create an executable zipapp named `pre-sdd-review-evidence` with the current Python interpreter in the shebang.
- Windows: create `pre-sdd-review-evidence.pyz` and a `pre-sdd-review-evidence.cmd` wrapper that invokes the exact installer interpreter and forwards `%*`.
- Refuse an existing nonidentical file. Treat byte-identical installation as success. Do not provide a force flag.
- Require `--bin-dir`; document that it must already be on PATH.

```python
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bin-dir", type=Path, required=True)
    parser.add_argument("--skill-root", type=Path, default=Path(__file__).resolve().parents[1])
    ...
```

- [ ] **Step 4: Document install, update, backup, and removal**

The evidence README must show explicit commands, `~/.pre-sdd-review/`, `PRE_SDD_REVIEW_HOME`, CLI/data separation, exact target inspection before removal, no remote pipe-to-shell, and the fact that removing a launcher does not delete receipts.

- [ ] **Step 5: Extend exact payload and archive smoke**

Add `evidence/install.py` and `evidence/README.md` to both source/archive inventories. Keep packaged source files non-executable; the installer-generated POSIX command is executable outside the ZIP. Add verify-download tests that import and run `--version` from the extracted evidence package without touching the user's real evidence home.

- [ ] **Step 6: Run the task gate**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests/products/pre-sdd-review/evidence -p 'test_*.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --skill pre-sdd-review
git diff --check
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add skills/pre-sdd-review/evidence tests/products/pre-sdd-review \
  tests/repository/test_release_contract.py scripts/release.py
git commit -m "feat: install shared pre-sdd evidence cli"
```

### Task 7: Integrate Evidence into the Skill and Current Documentation

**Files:**
- Modify: `skills/pre-sdd-review/SKILL.md`
- Modify: `skills/pre-sdd-review/README.md`
- Modify: `skills/pre-sdd-review/README.en.md`
- Modify: `skills/pre-sdd-review/CHANGELOG.md`
- Modify: `tests/products/pre-sdd-review/cases.json`
- Modify: `tests/products/pre-sdd-review/test_contract.py`
- Modify: `docs/maintainers/products/pre-sdd-review/contract.md`
- Modify: `docs/maintainers/products/pre-sdd-review/testing.md`
- Modify: `docs/maintainers/products/pre-sdd-review/compatibility.md`
- Modify: `docs/maintainers/products/pre-sdd-review/release.md`
- Modify: `docs/users/ko/installation.md`
- Modify: `docs/users/en/installation.md`
- Modify: `docs/users/ko/safety-and-privacy.md`
- Modify: `docs/users/en/safety-and-privacy.md`
- Modify: `docs/users/ko/verification.md`
- Modify: `docs/users/en/verification.md`
- Modify: `tests/repository/test_public_docs.py`

**Interfaces:**
- Consumes: installed CLI commands and all existing review/verdict contracts.
- Produces: exact optional evidence state machine in the skill, stable final-report receipt line, combined-SDD `run_id` handoff, and current user/maintainer guidance.

- [ ] **Step 1: Add failing skill workflow cases**

Add bounded case IDs for:

```text
evidence-cli-recorded
evidence-cli-unavailable
evidence-review-only
evidence-resolution-blocked
evidence-combined-sdd-outcome
```

Extend contract tests to require this order:

```text
compatible CLI available
  -> start before semantic review
  -> normal review/repair/re-review
  -> finish-review after final verdict
  -> print Evidence status
  -> hand run_id to explicitly requested combined SDD
  -> record terminal outcome without changing verdict
```

Require the unavailable/incompatible/permission-failure branch to print `not_recorded` and continue the review.

- [ ] **Step 2: Run instruction tests to verify RED**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests/products/pre-sdd-review -p 'test_contract.py' -v
```

Expected: FAIL because skill and docs do not describe evidence behavior and canonical digests are old.

- [ ] **Step 3: Add the minimal evidence controller instructions**

Add one bounded section to `SKILL.md` without changing the reviewer protocol or mutation allowlist. It must state:

- check `pre-sdd-review-evidence --version` without installing anything;
- call `start` only when a compatible CLI is present;
- pass the actual loaded skill root and primary plan;
- keep `run_id` controller-local and never place it in user documents;
- call `finish-review` after the semantic verdict and repairs are final;
- print exactly one `Evidence:` line;
- never change verdict because the recorder failed;
- pass the recorded `run_id` only to an explicitly requested combined SDD worker;
- record an outcome only at terminal downstream status; and
- store no full reviewer response or source body.

- [ ] **Step 4: Update Korean and English product docs**

Document the explicit installer, one shared command for Codex/Claude Code/Cursor/Grok, the stable data root, commands, limits, backup/removal, and `not_measured` host boundary. Preserve the one approved `$pre-sdd-review` first-call line and existing product contract entries; add a separate evidence contract entry instead of altering mutation authority.

- [ ] **Step 5: Update maintainer and shared user docs**

Keep semantic host support as Codex only. Add a separate CLI compatibility table and evidence test command. Safety docs must say receipts remain local and content-bounded, not that every third-party host is trustworthy. Installation docs must require inspecting `--bin-dir` and must not pipe remote scripts to a shell.

- [ ] **Step 6: Recompute closed-document fingerprints after semantic review**

Update `INSTRUCTION_DOCUMENT_SHA256`, README section/document digests, maintainer contract digest, testing/compatibility/release digests, and exact case counts only after the final prose is stable. Keep mutation tests that prove append-only drift is rejected.

- [ ] **Step 7: Run document and product gates**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests/products/pre-sdd-review -p 'test_contract.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.repository.test_public_docs -v
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --skill pre-sdd-review
git diff --check
```

Expected: PASS; supported host remains Codex and other semantic hosts remain `not_measured`.

- [ ] **Step 8: Commit**

```bash
git add skills/pre-sdd-review docs/maintainers/products/pre-sdd-review \
  docs/users tests/products/pre-sdd-review tests/repository/test_public_docs.py
git commit -m "docs: integrate pre-sdd evidence workflow"
```

### Task 8: Harden Concurrency, Privacy, and Release Proof

**Files:**
- Modify: `tests/products/pre-sdd-review/evidence/test_storage.py`
- Modify: `tests/products/pre-sdd-review/evidence/test_cli.py`
- Modify: `tests/products/pre-sdd-review/evidence/test_reporting.py`
- Modify: `tests/products/pre-sdd-review/evidence/test_install.py`
- Modify: runtime files only when a failing adversarial test proves a defect
- Modify: `skills/pre-sdd-review/CHANGELOG.md` only if final verified behavior differs from the Task 1 entry

**Interfaces:**
- Consumes: complete CLI, exact payload, skill integration, and release pipeline.
- Produces: adversarial regression coverage, platform-portable provider-free proof, standalone ZIP parity, and an honest unmeasured live-client report.

- [ ] **Step 1: Add failing adversarial privacy and concurrency tests**

Add tests that launch independent processes against one temporary evidence root and prove:

```python
def test_concurrent_distinct_runs_never_share_or_truncate_files(self) -> None:
    results = run_concurrent_cli_starts(count=20, evidence_home=self.home, repo=self.repo)
    self.assertEqual(len({item["run_id"] for item in results}), 20)
    for item in results:
        json.loads(find_pending(item["run_id"]).read_text(encoding="utf-8"))
```

Inject absolute home paths, API-key-shaped values, environment mappings, source bodies, prompt/response fields, symlink escapes, oversized Unicode, stale locks, truncated JSON, case-folded run-ID collisions, and Windows separators. Assert that neither stdout, stderr, receipts, exports, nor summary output leaks the injected values.

- [ ] **Step 2: Run adversarial tests to verify at least one RED mutation**

Before changing runtime code, introduce each test against the current implementation and confirm the targeted unsafe mutation fails. Do not count a test that passes immediately as a demonstrated regression unless it verifies a previously uncovered branch.

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests/products/pre-sdd-review/evidence -p 'test_*.py' -v
```

Expected: new adversarial tests expose any remaining defects; record exact failures in the task ledger.

- [ ] **Step 3: Apply the smallest fixes and rerun GREEN**

Change only the module responsible for each proved defect. Preserve public signatures from Tasks 1-6. Re-run the Step 2 command until all tests pass with no leaked fixture values.

- [ ] **Step 4: Run full and Windows-portable provider-free verification**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --profile full
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --profile windows-portable
git diff --check
```

Expected: all stages PASS. A Windows-portable profile run on a non-Windows host proves only portable command selection, not actual Windows execution.

- [ ] **Step 5: Build and verify a fresh standalone product archive**

Create a unique new empty output directory, then run:

```bash
release_output_dir="$(mktemp -d "${TMPDIR:-/tmp}/pre-sdd-review-release.XXXXXX")"
release_verify_dir="$(mktemp -d "${TMPDIR:-/tmp}/pre-sdd-review-verify.XXXXXX")"
python3 scripts/release.py check --product pre-sdd-review
python3 scripts/release.py build --product pre-sdd-review --output "$release_output_dir"
cp "$release_output_dir/pre-sdd-review-v1.2.0.zip" "$release_verify_dir/"
cp "$release_output_dir/SHA256SUMS" "$release_verify_dir/"
python3 scripts/release.py verify-download --product pre-sdd-review --input "$release_verify_dir"
```

Expected: `pre-sdd-review-v1.2.0.zip` and `SHA256SUMS` only; exact source/archive payload parity; extracted evidence CLI `--version` smoke PASS. Do not publish the artifacts.

- [ ] **Step 6: Perform whole-branch review against the spec**

Review the complete branch for:

- one product-specific evidence root and command;
- no semantic verdict path inside the CLI;
- exact payload and archive inventory;
- no hidden network/provider code;
- no absolute-path or source-content persistence;
- create-only review/outcome behavior;
- honest full/degraded/not-measured separation;
- non-blocking recorder failures; and
- no release or catalog side effects.

Turn every material finding into a failing focused test before fixing it. Re-run the affected focused suite and the full profile after any change.

- [ ] **Step 7: Record live-client status honestly**

Do not invoke billable or external clients as part of this plan. In the closeout report, record Codex/Claude Code/Cursor/Grok fixture execution as `not_measured` unless the user separately authorized and the run produced a validated receipt. Do not infer support from the provider-free CLI suite.

- [ ] **Step 8: Commit final hardening**

If Task 8 changed files:

```bash
git add skills/pre-sdd-review tests/products/pre-sdd-review
git commit -m "test: harden pre-sdd evidence receipts"
```

If no file changed, record the fresh verification outputs in the task handoff and do not create an empty commit.

## Final Handoff Checklist

- [ ] Every task commit is present and scoped.
- [ ] `git diff --check` passes.
- [ ] `PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --profile full` passes.
- [ ] `PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --profile windows-portable` passes.
- [ ] Pre-SDD check/build/verify-download passes from fresh directories.
- [ ] The final worktree contains no generated evidence, receipt, zipapp, ZIP, checksum, cache, credential, or live-provider artifact.
- [ ] `products.toml` still lists only Codex as a supported semantic host for `pre-sdd-review` unless separate live evidence and authority changed that claim.
- [ ] No tag, push, release, catalog mutation, or publication occurred.
