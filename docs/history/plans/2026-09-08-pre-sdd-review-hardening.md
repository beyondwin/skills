# Pre-SDD Review Recorder Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bind optional review records to one checkout, serialize state transitions, and report damaged or contradictory observations without changing the semantic review verdict.

**Architecture:** Keep the installed recorder in the existing single `evidence/evidence.py` file. Schema 3 adds a private, locally salted checkout key; readers retain schema 2 as historical evidence, while OS locks protect current mutations. Typed record validation and observation annotations are separate responsibilities inside that file.

**Tech Stack:** Python 3.11+, standard library, Git, `unittest`, POSIX `fcntl.flock` loaded only when a mutation needs it.

**Spec:** docs/history/specs/2026-09-08-skills-hardening-design.md

## Global Constraints

- Implement P1–P4, the Pre-SDD share of R5, and the `3.0.0` release metadata from the approved spec. This file is a plan, not an implementation-completion claim.
- Preserve two reviewer roles, the existing scalar trigger list, two editable documents, at most two repair passes, and the semantic READY/REVISE/BLOCKED rules. P5 is excluded.
- The recorder is optional. An unavailable, incompatible, corrupt, or permission-failing recorder produces `not_recorded`; it cannot change a semantic verdict.
- Keep `skills/pre-sdd-review/`, `tests/products/pre-sdd-review/`, and `docs/maintainers/products/pre-sdd-review/` as this worker's only write scope. The existing ten-file installed payload remains intact; add no runtime module or dependency.
- Shared scripts, registry, `tests/repository/`, and `docs/users/` belong to the integration controller. In particular, that controller owns the extracted CLI version expectation in `scripts/release.py` and shared documentation digests.
- All evidence tests use temporary homes, temporary repositories, and synthetic documents. No real installed skill, evidence home, provider, model, remote publication, tag, or push is involved.
- Never store the salt, raw checkout path, Git directory path, environment, command output, prompt, or transcript in a record. HMAC input paths remain in memory.
- Separate clones and worktrees have different identities. A checkout move starts a new identity. The source clarification is necessary because `git worktree move` can preserve its Git directory: hash canonical **Git directory and checkout root**, not Git directory alone.
- The product phase uses direct product tests. `python3 scripts/verify.py --skill pre-sdd-review` includes shared release tests whose version pins change during final integration, so it is a post-integration gate.
- One agent owns this product at a time. The controller stages and commits reviewed changes serially; workers do not write the shared Git index concurrently.

## Files and fixed interfaces

| File | Responsibility |
| --- | --- |
| `skills/pre-sdd-review/evidence/evidence.py` | Identity, storage, validation, six existing commands, aggregation |
| `tests/products/pre-sdd-review/evidence/test_hardening.py` (new) | Independent identity, migration boundary, damaged-record, race, and observation regressions |
| `tests/products/pre-sdd-review/evidence/test_evidence.py` | Existing behavior coverage; approved schema and summary-shape expectations |
| `tests/products/pre-sdd-review/evidence/support.py` | Existing synthetic helpers; default synthetic version changes to `3.0.0` at release integration |
| `skills/pre-sdd-review/evidence/README.md` | Schema 3, identity lifecycle, read-only legacy records, error and summary contracts |
| `skills/pre-sdd-review/SKILL.md`, `release.toml`, `CHANGELOG.md`, `README.md`, `README.en.md` | Matching version, optional recorder handshake, public links, usage and compatibility |
| `tests/products/pre-sdd-review/test_contract.py` | Product instruction and documentation contract checks; retain mutation/digest protection |
| `docs/maintainers/products/pre-sdd-review/{contract,testing,compatibility,release}.md` | Maintainer ownership and measured/unmeasured boundaries |

New runtime interfaces are fixed here so later tasks can rely on them:

```text
# Context manager functions yield once and return no value.
_file_lock(path: Path) -> Iterator[None]
_identity_salt(home: Path, *, create: bool) -> bytes
checkout_key(root: Path, home: Path, *, create: bool) -> str
require_current_schema(record: dict[str, object]) -> None
validate_record(record: object, expected_run_id: str) -> dict[str, object]
validate_finish_shape(payload: object) -> dict[str, object]
scan_records(home: Path) -> tuple[list[dict[str, object]], int]
observation_anomalies(record: dict[str, object]) -> list[str]
```

Use `@contextmanager` for `_file_lock`. Retain existing signatures for `write_record`, `_read_record`, `load_record`, `iter_records`, `cmd_start`, `_require_pending`, `cmd_finish`, `cmd_abandon`, `cmd_outcome`, `cmd_show`, `summarize`, and `cmd_summary`. `iter_records` remains a compatibility wrapper over `scan_records(home)[0]`. `show` continues to print validated source bytes verbatim; historical binding appears in summary metadata and documentation, never by rewriting the old record.

---

### Task 1: Establish schema 3 checkout identity and the read-only legacy boundary

**Files:** Modify `skills/pre-sdd-review/evidence/evidence.py`, `tests/products/pre-sdd-review/evidence/test_evidence.py`; create `tests/products/pre-sdd-review/evidence/test_hardening.py`.

**Interfaces:** Consume existing `git`, `git_root`, `canonical`, `fail`, `start`, `finish`, `load`, `run`, `error_code`, and `make_git_repo`. Produce `_file_lock`, `_identity_salt`, `checkout_key`, and `require_current_schema` with the signatures above. New records have integer `schema=3` and `repo_key` containing 64 lowercase hex characters; `repo` remains the display basename.

- [ ] **Step 1: Add the independent identity regressions.** Start the new test module with these imports and fixture base; subsequent tasks add classes in the same module.

```python
from __future__ import annotations

import copy
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import evidence
from support import (
    EVIDENCE_DIR, error_code, finding, finish, finish_payload, load,
    make_git_repo, make_skill_root, run, run_git, start,
)


class RecorderFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.workspace = Path(self.directory.name)
        self.home = self.workspace / "evidence home"
        self.repo = make_git_repo(self.workspace / "first", "same")
        self.skill = make_skill_root(self.workspace)

    def put(self, run_id: str, record: dict[str, object]) -> Path:
        path = self.home / "runs" / f"{run_id}.json"
        path.write_bytes(evidence.canonical(record))
        return path


class IdentityTests(RecorderFixture):
    def test_same_basename_cannot_finish_another_checkout(self) -> None:
        run_id = start(self.home, self.repo, self.skill)
        other = make_git_repo(self.workspace / "second", "same")
        before = (self.home / "runs" / f"{run_id}.json").read_bytes()
        code, out, err = finish(self.home, other, run_id, finish_payload())
        self.assertEqual((code, out, error_code(err)), (2, "", "outside-repository"))
        self.assertEqual((self.home / "runs" / f"{run_id}.json").read_bytes(), before)

    def test_start_binds_without_storing_identity_paths(self) -> None:
        first = start(self.home, self.repo, self.skill)
        second = start(self.home, self.repo, self.skill)
        record = load(self.home, first)
        self.assertEqual(record["schema"], 3)
        self.assertRegex(record["repo_key"], r"^[0-9a-f]{64}$")
        self.assertEqual(record["repo_key"], load(self.home, second)["repo_key"])
        encoded = evidence.canonical(record)
        self.assertNotIn(str(self.repo).encode(), encoded)
        self.assertNotIn(str(self.home).encode(), encoded)
        salt = self.home / ".identity-salt"
        self.assertEqual(len(salt.read_bytes()), 32)
        self.assertEqual(stat.S_IMODE(salt.stat().st_mode), 0o600)
        self.assertNotIn(salt.read_bytes().hex().encode(), encoded)

    def test_worktree_move_changes_identity_even_with_same_git_directory(self) -> None:
        worktree = self.workspace / "linked checkout"
        result = run_git(self.repo, "worktree", "add", "--detach", str(worktree))
        self.assertEqual(result.returncode, 0, result.stderr)
        before_git_dir = run_git(worktree, "rev-parse", "--absolute-git-dir").stdout.strip()
        run_id = start(self.home, worktree, self.skill)
        moved = self.workspace / "moved checkout"
        result = run_git(self.repo, "worktree", "move", str(worktree), str(moved))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(run_git(moved, "rev-parse", "--absolute-git-dir").stdout.strip(), before_git_dir)
        code, _, err = finish(self.home, moved, run_id, finish_payload())
        self.assertEqual((code, error_code(err)), (2, "outside-repository"))
        new_run = start(self.home, moved, self.skill)
        self.assertNotEqual(load(self.home, run_id)["repo_key"], load(self.home, new_run)["repo_key"])
```

Add separate positive assertions for two worktrees of one repository, an actual `git clone --local` into a different path, and ordinary directory `Path.rename`: all new locations receive different keys, while a symlink alias resolving to the same checkout keeps its key. Existing matching-checkout finish remains the positive control.

- [ ] **Step 2: Run RED.**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/pre-sdd-review/evidence -p 'test_hardening.py' -v
```

Expected before the fix: same-basename finish succeeds incorrectly; `repo_key` is absent; the worktree-move case is not rejected by checkout identity. These are behavior failures, not import/setup failures.

- [ ] **Step 3: Add a private lock and salt; keep version inspection independent.** Add imports `hmac`, `tempfile`, `contextmanager` from `contextlib`, and `Iterator` from `collections.abc`. The existing `--version` early return must stay above `evidence_home` and all filesystem activity.

```python
@contextmanager
def _file_lock(path: Path) -> Iterator[None]:
    try:
        import fcntl
    except ImportError:
        fail("locking-unavailable", "OS file locking is unavailable for evidence mutations")
    descriptor: int | None = None
    try:
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(path.parent, 0o700)
        descriptor = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
        os.fchmod(descriptor, 0o600)
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield
    except OSError as exc:
        raise EvidenceError("evidence-home-unwritable", "evidence storage is unavailable") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _identity_salt(home: Path, *, create: bool) -> bytes:
    salt_path = home / ".identity-salt"
    with _file_lock(home / ".identity.lock"):
        if not salt_path.exists():
            if not create:
                fail("identity-unavailable", "checkout identity is unavailable; start a new run")
            descriptor, temporary = tempfile.mkstemp(prefix=".identity-salt-", dir=home)
            temp_path = Path(temporary)
            try:
                with os.fdopen(descriptor, "wb") as stream:
                    stream.write(os.urandom(32))
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temp_path, salt_path)
            finally:
                temp_path.unlink(missing_ok=True)
        os.chmod(salt_path, 0o600)
        salt = read_bounded_bytes(salt_path, 32)
        if len(salt) != 32:
            fail("schema-invalid", "checkout identity salt must contain exactly 32 bytes")
        return salt


def checkout_key(root: Path, home: Path, *, create: bool) -> str:
    result = git(root, "rev-parse", "--absolute-git-dir")
    raw = result.stdout.strip()
    if result.returncode != 0 or not raw or "\n" in raw:
        fail("not-git-repository", "checkout Git directory is unavailable")
    material = canonical({
        "git_dir": str(Path(raw).resolve()),
        "checkout": str(root.resolve()),
    })
    return hmac.new(_identity_salt(home, create=create), material, hashlib.sha256).hexdigest()


def require_current_schema(record: dict[str, object]) -> None:
    if record["schema"] != 3:
        fail("legacy-record-read-only", "schema 2 is historical-unbound; preserve it and start a new run")
```

Set `CLI_VERSION = "3.0.0"`, `SCHEMA = 3`; include `"repo_key": checkout_key(root, home, create=True)` in the `cmd_start` record. In `cmd_finish`, replace the basename comparison with `hmac.compare_digest(checkout_key(root, home, create=False), str(record["repo_key"]))`, returning the existing `outside-repository` code on mismatch. At this stage `_read_record` accepts exact integer schemas 2 and 3; Task 3 supplies full shape validation. Call `require_current_schema` in `_require_pending` and in `cmd_outcome` before any state changes. Keep `show` bytes unchanged.

- [ ] **Step 4: Prove legacy reads and mutator refusals; verify salt initialization.** Add the following test. Repeat the mutation refusal for a completed schema 2 record and `outcome`; retain the same bytes and no invented `repo_key`.

```python
class LegacyTests(RecorderFixture):
    def test_legacy_pending_is_readable_but_not_mutated(self) -> None:
        run_id = start(self.home, self.repo, self.skill)
        old = load(self.home, run_id)
        old["schema"] = 2
        old.pop("repo_key")
        path = self.put(run_id, old)
        before = path.read_bytes()
        code, out, err = run(["show", "--run-id", run_id], home=self.home, cwd=self.repo)
        self.assertEqual((code, out.encode(), err), (0, before, ""))
        code, _, err = finish(self.home, self.repo, run_id, finish_payload())
        self.assertEqual((code, error_code(err)), (2, "legacy-record-read-only"))
        code, _, err = run(["abandon", "--run-id", run_id, "--reason", "other"], home=self.home, cwd=self.repo)
        self.assertEqual((code, error_code(err)), (2, "legacy-record-read-only"))
        self.assertEqual(path.read_bytes(), before)
```

For concurrent salt initialization, launch four `subprocess.Popen` calls to the existing `evidence.py start` command against the same empty temporary home and same repository. Supply each the explicit `--skill-root`, `--repo`, `--plan`, `--design`, `--client codex`, `--model gpt-test`, and `--mode default` values used by `support.start`. Collect each with a 15-second timeout, require four exit-zero records, one distinct `repo_key`, exactly one 32-byte `.identity-salt`, and no `.identity-salt-*` residue. Use the process structure from Task 2 rather than threads; this tests separate-process initialization.

Update `VERSION_LINE` and the existing `record["schema"]` expectation in `test_evidence.py` to 3 because this is the approved major format change. Synthetic skill snapshots can still report the helper's old default until Task 6; do not globally replace historical `2` values. Run the full direct evidence suite. Expected: GREEN for identity, legacy boundaries, and existing record behavior; Task 3 has not yet added stricter corruption cases.

- [ ] **Step 5: Review and hand off the bounded commit.** Have the controller inspect record privacy, the genuine worktree-move test, and salt initialization, then commit only this task's three files with `fix(pre-sdd-review): bind schema 3 records to checkout identity`. Record actual test output in the execution ledger.

### Task 2: Serialize terminal transitions and make every write use a unique temporary file

**Files:** Modify `skills/pre-sdd-review/evidence/evidence.py`, `tests/products/pre-sdd-review/evidence/test_hardening.py`.

**Interfaces:** Consume Task 1 `_file_lock` and `require_current_schema`. A run lock is `home / "locks" / f"{validate_run_id(run_id)}.lock"`. Hold it across the complete read-check-write sequence in `finish`, `abandon`, and `outcome`. `.identity.lock` protects only salt initialization; no path acquires a run lock while already holding the identity lock.

- [ ] **Step 1: Add a race test that proves command-level locking.** Parameterize two finish commands and finish-versus-abandon. The parent holds the exact run lock until both child calls demonstrably wait, then checks one terminal winner. The subprocess uses the real recorder module without a provider or installed copy.

```python
class TransitionTests(RecorderFixture):
    def test_terminal_commands_wait_for_lock_and_have_one_winner(self) -> None:
        for second_command in ("finish", "abandon"):
            with self.subTest(second_command=second_command):
                run_id = start(self.home, self.repo, self.skill)
                processes = []
                worker = (
                    "import sys; sys.path.insert(0, sys.argv.pop(1)); "
                    "import evidence; print('ready', flush=True); "
                    "raise SystemExit(evidence.main())"
                )
                with evidence._file_lock(self.home / "locks" / f"{run_id}.lock"):
                    for command in ("finish", second_command):
                        arguments = [command, "--run-id", run_id]
                        arguments += (["--repo", str(self.repo)] if command == "finish"
                                      else ["--reason", "other"])
                        process = subprocess.Popen(
                            [sys.executable, "-c", worker, str(EVIDENCE_DIR), *arguments],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, cwd=self.repo,
                            env={**os.environ, "PRE_SDD_REVIEW_HOME": str(self.home),
                                 "PYTHONDONTWRITEBYTECODE": "1"},
                        )
                        processes.append(process)
                        self.addCleanup(lambda child=process: child.kill() if child.poll() is None else None)
                        self.assertEqual(process.stdout.readline(), "ready\n")
                        process.stdin.write(json.dumps(finish_payload()))
                        process.stdin.close()
                        process.stdin = None
                    for process in processes:
                        with self.assertRaises(subprocess.TimeoutExpired):
                            process.communicate(timeout=0.2)
                results = []
                for process in processes:
                    out, err = process.communicate(timeout=15)
                    results.append((process.returncode, out, err))
                self.assertEqual(sorted(code for code, _, _ in results), [0, 2])
                loser = next(err for code, _, err in results if code == 2)
                self.assertEqual(error_code(loser), "already-finished")
                final = load(self.home, run_id)
                self.assertIn(final["status"], ("completed", "abandoned"))
                self.assertEqual(len(list((self.home / "runs").glob("*.json"))),
                                 1 if second_command == "finish" else 2)
```

- [ ] **Step 2: Run RED.** Run discovery for `test_hardening.py`. Expected: baseline command implementations can exit while the parent holds the run lock; checking only `os.replace` atomicity does not satisfy this test.

- [ ] **Step 3: Put rereads and writes inside locks, and use unique temporary names.** Keep each public `cmd_*` signature unchanged. Indent its existing body under its run lock, so `_require_pending` or `load_record` executes **after** acquisition. Parse stdin inside that same command flow; each losing terminal call checks status before parsing or changing anything. `outcome` rereads the latest completed record and preserves its existing `false-ready` admissibility rule.

```python
def cmd_abandon(args: argparse.Namespace, home: Path) -> dict[str, object]:
    lock = home / "locks" / f"{validate_run_id(args.run_id)}.lock"
    with _file_lock(lock):
        record = _require_pending(home, args.run_id)
        completed_at = utc_now()
        record["status"] = "abandoned"
        record["abandon_reason"] = args.reason
        record["completed_at"] = completed_at
        record["elapsed_s"] = elapsed_seconds(str(record["started_at"]), completed_at)
        write_record(run_path(home, args.run_id), record)
        return {"run_id": args.run_id, "status": "abandoned"}
```

Replace the fixed `path.name + ".tmp"` write in `write_record` with `tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)`. Keep canonical serialization, 64 KiB limit, private home/run permissions, stream `flush`, `os.fsync`, and `os.replace`. Always unlink that writer's temporary path in a `finally` block. Use the same code structure as Task 1's salt write; never unlink the destination on an exception.

```python
descriptor, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
temp = Path(temporary)
try:
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)
finally:
    temp.unlink(missing_ok=True)
```

- [ ] **Step 4: Verify failures, serialized outcomes, and platform limits.** Add a write failure regression with a real existing record, `mock.patch.object(evidence.os, "replace", side_effect=OSError("synthetic failure"))`, and `assertRaises(evidence.EvidenceError)`: original bytes must remain identical, and `list(path.parent.glob(path.name + ".*.tmp"))` must be empty. Add two concurrent outcomes under the parent-held run lock using the process pattern above: both eventually succeed, final outcome is one complete input label/note pair, and every other record field stays identical. Do not require a particular scheduling order.

Patch `builtins.__import__` only for `name == "fcntl"` to raise `ImportError`; require `start` to return exit 2, code `locking-unavailable`, and exactly one JSON error line without a traceback. Under the same patch, `--version` and empty `summary` succeed without creating a home. This is an unsupported-platform regression, not a claim of native Windows mutation support.

Run the full direct evidence suite once. Expected: GREEN, exactly one terminal winner and serial outcome updates. Review lock scope and error cleanup, then controller commit `fix(pre-sdd-review): serialize record transitions`.

### Task 3: Validate records at read boundaries and isolate damaged files

**Files:** Modify `skills/pre-sdd-review/evidence/evidence.py`, `tests/products/pre-sdd-review/evidence/test_hardening.py`, `tests/products/pre-sdd-review/evidence/test_evidence.py`.

**Interfaces:** Produce `validate_record(record, expected_run_id)`, `validate_finish_shape(payload)`, and `scan_records(home)`. `_read_record` remains `(source_bytes, validated_record)`; malformed records use `schema-invalid`. `scan_records` returns valid sorted records plus the number of invalid top-level `runs/*.json` entries, with no source paths or raw exceptions in summary.

- [ ] **Step 1: Write counterexamples that remain valid JSON.** Add a `ReaderTests` class derived from `RecorderFixture` and use the following body. Each case isolates a real missing/type/status/date/binding failure rather than only malformed JSON.

```python
class ReaderTests(RecorderFixture):
    def test_schema_shaped_damage_is_rejected_and_counted(self) -> None:
        good_id = start(self.home, self.repo, self.skill)
        bad_id = start(self.home, self.repo, self.skill)
        original = load(self.home, bad_id)
        cases = []
        missing = copy.deepcopy(original)
        del missing["plan"]
        cases.append(missing)
        cases.append({**original, "status": "completed"})
        cases.append({**original, "started_at": "not-a-date"})
        cases.append({**original, "run_id": good_id})
        cases.append({**original, "schema": True})
        cases.append({**original, "repo_key": "not-a-key"})
        cases.append({**original, "git": {**original["git"], "dirty_start": 1}})
        for damaged in cases:
            with self.subTest(damaged=damaged):
                self.put(bad_id, damaged)
                code, out, err = run(["show", "--run-id", bad_id], home=self.home, cwd=self.repo)
                self.assertEqual((code, out, error_code(err)), (2, "", "schema-invalid"))
                code, out, err = run(["summary"], home=self.home, cwd=self.repo)
                self.assertEqual((code, err), (0, ""))
                summary = json.loads(out)
                self.assertEqual(summary["invalid_records"], 1)
                self.assertEqual([item["run_id"] for item in summary["runs"]], [good_id])
```

Repeat missing nested fields against schema 2 pending and completed samples derived from a complete synthetic record by changing only `schema` and removing `repo_key`. Preserve valid legacy bytes as the positive control. Add invalid JSON, oversized JSON, `NaN`/boolean integer values, invalid nested `outcome`, unknown top-level keys, unsafe document paths, and UUID/filename mismatch cases. No real evidence files are fixtures.

Add this parser-boundary test to `ReaderTests`. The deep payload is below the 64 KiB limit and must not escape as `RecursionError`; ordinary malformed syntax and non-finite numeric constants must use the same JSON error contract.

```python
def test_deep_or_nonfinite_json_cannot_kill_a_healthy_summary(self) -> None:
    good_id = start(self.home, self.repo, self.skill)
    bad_id = start(self.home, self.repo, self.skill)
    bad_path = self.home / "runs" / f"{bad_id}.json"
    payloads = (b"[" * 1200 + b"0" + b"]" * 1200, b"NaN", b"Infinity", b"-Infinity")
    for raw in payloads:
        with self.subTest(prefix=raw[:20]):
            with self.assertRaises(evidence.EvidenceError) as raised:
                evidence.parse_json(raw, "synthetic record")
            self.assertEqual(raised.exception.code, "schema-invalid")
            bad_path.write_bytes(raw)
            code, out, err = run(["summary"], home=self.home, cwd=self.repo)
            self.assertEqual((code, err), (0, ""))
            summary = json.loads(out)
            self.assertEqual(summary["invalid_records"], 1)
            self.assertEqual([item["run_id"] for item in summary["runs"]], [good_id])
```

- [ ] **Step 2: Run RED.** Discovery for `test_hardening.py` must fail because current `_read_record` accepts missing fields and current `summary` can raise `KeyError`. Record the actual failure and then implement the reader.

- [ ] **Step 3: Implement exact schema and status validation before consumers index fields.** First bound parser failures consistently; the existing `read_bounded_bytes` size limit remains in place. `fail` raises `EvidenceError`, so rejected constants flow directly into the same one-line envelope.

```python
def parse_json(data: bytes, name: str) -> object:
    try:
        return json.loads(
            data.decode("utf-8"),
            parse_constant=lambda token: fail("schema-invalid", "non-finite JSON numbers are not allowed"),
        )
    except (UnicodeDecodeError, ValueError, RecursionError):
        fail("schema-invalid", f"{name} is not valid bounded UTF-8 JSON")
```

Add these helpers; they define the reader's primitive contracts, separate from semantic anomalies.

```python
def _object(value: object, name: str, keys: set[str]) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != keys:
        fail("schema-invalid", f"{name} must contain exactly its declared fields")
    return value


def _timestamp(value: object, name: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z", value
    ):
        fail("schema-invalid", f"{name} must be a canonical UTC timestamp")
    try:
        dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        fail("schema-invalid", f"{name} is not a valid date")
    return value


def _digest(value: object, name: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        fail("schema-invalid", f"{name} must be a lowercase SHA-256 value")
    return value


def _boolean(value: object, name: str) -> bool:
    if type(value) is not bool:
        fail("schema-invalid", f"{name} must be a boolean")
    return value
```

Implement `validate_record` using this exhaustive table and the existing `_string`, `_enum`, `_integer`, `_relative`, and finding validators. These checks must occur before any nested field access. Extract the existing field/type portion of `validate_finish` into `validate_finish_shape(payload: object) -> dict[str, object]`. Preserve its existing normalized result keys and use `validate_finding(item, 2)` there: individual finding pass 1 or 2 is valid shape, while comparison with the observed total is relational. At this task's boundary, the public `validate_finish(payload, mode)` still applies all its existing relational checks after calling the shape helper, including an explicit finding-pass-versus-total check. Readers call only `validate_finish_shape`, so an old, well-typed contradictory observation remains readable before Task 4 enables recording such observations through `finish`.

```python
# In validate_finish_shape, after validating repair_passes and the findings list:
findings = [validate_finding(item, 2) for item in payload["findings"]]

# In validate_finish, after obtaining normalized = validate_finish_shape(payload):
if any(item["repair_pass"] is not None and item["repair_pass"] > normalized["repair_passes"]
       for item in normalized["findings"]):
    fail("schema-invalid", "finding.repair_pass exceeds repair_passes")
```

Keep the current relational checks in the wrapper until Task 4 and move the current normalized-return dictionary into the shape helper. This is an in-file function boundary; no module extraction or new framework is involved.

| Surface | Exact reader rule |
| --- | --- |
| Top-level keys | The existing `cmd_start` literal's key set, plus `repo_key` only for schema 3. No missing/extra keys. `type(schema) is int` and schema in `(2, 3)`. |
| `run_id` | Canonical lowercase UUID and equals `expected_run_id`; convert `validate_run_id` failure to `schema-invalid` when reading stored data. |
| `repo`, `repo_key` | Nonempty single-line display basename, maximum 255; schema 3 requires `_digest(repo_key)`. Schema 2 must lack this field. |
| `started_at`, terminal time | `_timestamp`; pending has `completed_at=None, elapsed_s=None`; completed/abandoned have timestamp and nonnegative non-boolean integer elapsed seconds. Reject terminal dates before start. |
| `skill` | Exactly `version, sha256`; nonempty version at most 100 characters, SHA-256 hex digest. |
| `client` | Exactly `id, model`; existing CLIENTS enum and model at most 100 characters. |
| `mode`, `status` | Existing MODES; status exactly pending/completed/abandoned. |
| `plan`, `design` | Plan exactly `path, sha_start, sha_end`; design null or same shape. Safe relative path and 64-hex initial digest. End digest is required only for completed status, null otherwise. |
| `git` | Exactly `head_start, head_end, dirty_start, dirty_end`; head is `unborn` or 40/64 lowercase hex. Exact boolean start; completed requires valid end values, other statuses require null ends. |
| Pending/abandoned semantic fields | `execution, reviewers, trigger, review_passes, repair_passes, verdict, block_reason` all null; `degraded_reasons=[]`, `findings=[]`, `outcome=None`. Pending `abandon_reason=None`; abandoned requires ABANDON_REASONS. |
| Completed semantic fields | `abandon_reason=None`; the exact FINISH_KEYS subset passes `validate_finish_shape`. Use existing enums, numeric ranges, bounded strings, finding IDs, evidence paths, and unique finding IDs. |
| `outcome` | Null or, for completed only, exactly `label, note, recorded_at`; existing OUTCOME_LABELS, nullable note maximum 300, valid timestamp. |

Use this explicit constant and validation flow. Do not infer valid fields from the candidate record or a freshly generated record. Use `validate_record` on reads, not inside `write_record`: test fixtures and observed anomalies must be representable without accidentally deriving trust from the writer.

```python
RECORD_KEYS_V2 = {
    "schema", "run_id", "status", "started_at", "completed_at", "elapsed_s",
    "skill", "client", "repo", "mode", "plan", "design", "git", "execution",
    "reviewers", "trigger", "degraded_reasons", "review_passes", "repair_passes",
    "verdict", "block_reason", "abandon_reason", "findings", "outcome",
}


def validate_record(record: object, expected_run_id: str) -> dict[str, object]:
    if not isinstance(record, dict) or type(record.get("schema")) is not int:
        fail("schema-invalid", "record schema must be an integer")
    schema = record["schema"]
    if schema not in (2, 3):
        fail("schema-invalid", "record must use schema 2 or 3")
    value = _object(record, "record", RECORD_KEYS_V2 | ({"repo_key"} if schema == 3 else set()))
    if not isinstance(value["run_id"], str):
        fail("schema-invalid", "record run_id must be a string")
    try:
        validate_run_id(expected_run_id)
        validate_run_id(value["run_id"])
    except EvidenceError:
        fail("schema-invalid", "record filename and run_id must be canonical UUIDs")
    if value["run_id"] != expected_run_id:
        fail("schema-invalid", "record run_id does not match its filename")
    repo = _string(value["repo"], "repo", 255)
    if repo in (".", "..") or "/" in repo or "\\" in repo:
        fail("schema-invalid", "repo must be a display basename")
    if schema == 3:
        _digest(value["repo_key"], "repo_key")
    _enum(value["mode"], "mode", MODES)
    status = _enum(value["status"], "status", ("pending", "completed", "abandoned"))
    started = _timestamp(value["started_at"], "started_at")
    if status == "pending":
        if value["completed_at"] is not None or value["elapsed_s"] is not None:
            fail("schema-invalid", "pending records cannot have terminal timestamps")
    else:
        ended = _timestamp(value["completed_at"], "completed_at")
        _integer(value["elapsed_s"], "elapsed_s", 0, 2**63 - 1)
        if ended < started:
            fail("schema-invalid", "completed_at precedes started_at")
    skill = _object(value["skill"], "skill", {"version", "sha256"})
    _string(skill["version"], "skill.version", 100)
    _digest(skill["sha256"], "skill.sha256")
    client = _object(value["client"], "client", {"id", "model"})
    _enum(client["id"], "client.id", CLIENTS)
    _string(client["model"], "client.model", 100)
    for name in ("plan", "design"):
        if name == "design" and value[name] is None:
            continue
        document = _object(value[name], name, {"path", "sha_start", "sha_end"})
        _relative(document["path"], name + ".path")
        _digest(document["sha_start"], name + ".sha_start")
        if status == "completed":
            _digest(document["sha_end"], name + ".sha_end")
        elif document["sha_end"] is not None:
            fail("schema-invalid", "unfinished documents cannot have end hashes")
    git_facts = _object(value["git"], "git", {"head_start", "head_end", "dirty_start", "dirty_end"})
    for suffix in ("start", "end"):
        head, dirty = git_facts["head_" + suffix], git_facts["dirty_" + suffix]
        if suffix == "end" and status != "completed":
            if head is not None or dirty is not None:
                fail("schema-invalid", "unfinished review cannot have end Git facts")
        else:
            if not isinstance(head, str) or not re.fullmatch(r"unborn|[0-9a-f]{40}|[0-9a-f]{64}", head):
                fail("schema-invalid", "Git head must be unborn or a commit hash")
            _boolean(dirty, "git.dirty_" + suffix)
    if status == "completed":
        validate_finish_shape({key: value[key] for key in FINISH_KEYS})
        if value["abandon_reason"] is not None:
            fail("schema-invalid", "completed records cannot have abandon_reason")
    else:
        null_fields = FINISH_KEYS - {"degraded_reasons", "findings"}
        if any(value[key] is not None for key in null_fields):
            fail("schema-invalid", "unfinished review cannot contain semantic completion fields")
        if value["degraded_reasons"] != [] or value["findings"] != []:
            fail("schema-invalid", "unfinished review must have empty observation lists")
        if status == "abandoned":
            _enum(value["abandon_reason"], "abandon_reason", ABANDON_REASONS)
        elif value["abandon_reason"] is not None:
            fail("schema-invalid", "pending records cannot have abandon_reason")
    if value["outcome"] is not None:
        if status != "completed":
            fail("schema-invalid", "outcome requires a completed record")
        outcome = _object(value["outcome"], "outcome", {"label", "note", "recorded_at"})
        _enum(outcome["label"], "outcome.label", OUTCOME_LABELS)
        _string(outcome["note"], "outcome.note", 300, nullable=True)
        _timestamp(outcome["recorded_at"], "outcome.recorded_at")
    return value
```

Replace the permissive `_read_record` tail and scanner with this flow:

```python
# In _read_record, after the existing bounded read and JSON parse:
record = validate_record(record, path.stem)
return data, record


def scan_records(home: Path) -> tuple[list[dict[str, object]], int]:
    runs = home / "runs"
    if not runs.is_dir():
        return [], 0
    records: list[dict[str, object]] = []
    invalid = 0
    for path in sorted(runs.glob("*.json")):
        if not path.is_file():
            continue
        try:
            records.append(_read_record(path)[1])
        except EvidenceError:
            invalid += 1
        except OSError:
            invalid += 1
    records.sort(key=lambda item: (str(item["started_at"]), str(item["run_id"])))
    return records, invalid


def iter_records(home: Path) -> list[dict[str, object]]:
    return scan_records(home)[0]
```

Use `records, invalid = scan_records(home)` in `cmd_summary`; apply existing `--repo` basename and `--last` filters to **valid** records, then add `result["invalid_records"] = invalid` to the result of `summarize(records)`. The invalid count covers the scanned directory before filters because a corrupt record cannot be reliably assigned to a repo or date. Update exact summary key assertions accordingly. Single-record read I/O failure must use the existing one-line `evidence-home-unwritable` envelope, not an uncaught exception; missing files retain `run-not-found`.

- [ ] **Step 4: Run GREEN and retain byte-preserving legacy reads.** Run the full direct evidence suite. Pending, completed, and abandoned current/legacy positive examples must pass. A damaged record never reaches `summarize`; one bad file cannot hide the healthy run. Review the schema table against every field read by `summarize`, then controller commit `fix(pre-sdd-review): validate stored records before aggregation`.

### Task 4: Separate typed observations from semantic anomalies and checkout chains

**Files:** Modify `skills/pre-sdd-review/evidence/evidence.py`, `tests/products/pre-sdd-review/evidence/test_hardening.py`, `tests/products/pre-sdd-review/evidence/test_evidence.py`.

**Interfaces:** Produce `observation_anomalies(record) -> list[str]`, returning stable sorted codes. `summarize` keeps observed verdicts untouched, exposes separate normal/anomalous completed counts, and uses `(repo_key, plan.path)` for schema 3 chains. Schema 2 has `binding="historical-unbound"`, no fabricated key, and no checkout chain.

- [ ] **Step 1: Add contradictory-observation and chain-isolation tests.**

```python
class ObservationTests(RecorderFixture):
    def test_blocked_ready_is_preserved_and_separated(self) -> None:
        normal = start(self.home, self.repo, self.skill)
        self.assertEqual(finish(self.home, self.repo, normal, finish_payload())[0], 0)
        suspect = start(self.home, self.repo, self.skill)
        payload = finish_payload(execution="blocked", reviewers=0, verdict="READY")
        code, _, err = finish(self.home, self.repo, suspect, payload)
        self.assertEqual(code, 0, err)
        self.assertEqual(load(self.home, suspect)["verdict"], "READY")
        code, out, err = run(["summary"], home=self.home, cwd=self.repo)
        self.assertEqual((code, err), (0, ""))
        summary = json.loads(out)
        self.assertIn(suspect, summary["anomalies"]["blocked_execution_with_nonblocked_verdict"])
        self.assertEqual(summary["counts"]["observation"], {"normal": 1, "anomalous": 1})
        self.assertEqual(summary["counts"]["normal_verdict"]["READY"], 1)
        self.assertEqual(summary["counts"]["anomalous_verdict"]["READY"], 1)

    def test_same_basename_and_legacy_are_not_checkout_chains(self) -> None:
        first = start(self.home, self.repo, self.skill)
        second = start(self.home, self.repo, self.skill)
        other = make_git_repo(self.workspace / "second", "same")
        third = start(self.home, other, self.skill)
        legacy = start(self.home, self.repo, self.skill)
        record = load(self.home, legacy)
        record["schema"] = 2
        record.pop("repo_key")
        self.put(legacy, record)
        code, out, err = run(["summary", "--repo", "same"], home=self.home, cwd=self.repo)
        self.assertEqual((code, err), (0, ""))
        summary = json.loads(out)
        self.assertEqual(len(summary["chains"]), 1)
        self.assertEqual([row["run_id"] for row in summary["chains"][0]["runs"]], [first, second])
        rows = {row["run_id"]: row for row in summary["runs"]}
        self.assertEqual(rows[legacy]["binding"], "historical-unbound")
        self.assertIsNone(rows[legacy]["repo_key"])
        self.assertNotEqual(rows[first]["repo_key"], rows[third]["repo_key"])
```

- [ ] **Step 2: Run RED.** Discovery for `test_hardening.py` must fail on missing anomaly segregation and mixed basename chains. Existing failure expectations that enforced semantic consistency in the recorder are explicitly changing under spec P4; preserve their inputs as anomaly regressions.

- [ ] **Step 3: Make finish validation typed-only and annotate contradictions without rewriting verdicts.** Task 3 already separated `validate_finish_shape`; replace the public wrapper's relational checks with `return validate_finish_shape(payload)` while preserving its `mode` parameter for callers. Keep enums, bounds, field sets, relative paths, duplicate IDs, and list types in the shape/finding validators. Move only cross-field consistency checks into `observation_anomalies`. For each moved check, keep the same old input in `test_evidence.py` but require accepted recording plus its anomaly instead of `schema-invalid`. The reader already uses the same shape helper, so new contradictory records remain readable without changing its schema rules.

```python
def observation_anomalies(record: dict[str, object]) -> list[str]:
    if record["status"] != "completed":
        return []
    findings = record["findings"]
    statuses = [item["status"] for item in findings]
    expected_reviewers = 2 if record["trigger"] is not None else 1
    checks = {
        "blocked_execution_with_nonblocked_verdict": record["execution"] == "blocked" and record["verdict"] != "BLOCKED",
        "ready_with_unresolved_findings": record["verdict"] == "READY" and any(status != "repaired" for status in statuses),
        "revise_without_unresolved_finding": record["verdict"] == "REVISE" and "unresolved" not in statuses,
        "blocked_without_reason": record["verdict"] == "BLOCKED" and record["block_reason"] is None,
        "repair_without_repaired_finding": bool(record["repair_passes"]) and "repaired" not in statuses,
        "review_only_with_repair": record["mode"] == "review-only" and record["repair_passes"] != 0,
        "full_reviewer_count_mismatch": record["execution"] == "full" and record["reviewers"] != expected_reviewers,
        "full_with_degraded_reasons": record["execution"] == "full" and bool(record["degraded_reasons"]),
        "degraded_without_reason": record["execution"] == "degraded" and not record["degraded_reasons"],
        "finding_repair_pass_exceeds_total": any(item["repair_pass"] is not None and item["repair_pass"] > record["repair_passes"] for item in findings),
        "head_changed_during_review": record["git"]["head_start"] != record["git"]["head_end"],
        "design_unresolved_but_full_execution": record["design"] is None and record["execution"] == "full",
    }
    return sorted(name for name, observed in checks.items() if observed)
```

Preserve the existing `repo_reality_citing_documents_only` anomaly's `{run_id, finding_id}` entries. Include that existing annotation when deciding whether the completed record is anomalous. These annotations report observations; a head change is not automatically misconduct or a false READY. Do not add new roles or trigger values, and keep the semantic instruction rules intact. The `outcome false-ready requires READY` command admission rule remains unchanged.

Construct chain keys only when `record["schema"] == 3`; keep human `repo` in the emitted chain record, include `repo_key`, and retain original run ordering. Add `binding` and nullable `repo_key` to each summary run row. Binding is `checkout-bound` for schema 3 and `historical-unbound` for schema 2; it does not claim that the current filesystem still contains that checkout.

Keep existing `counts.verdict` as all observed completed verdicts, and add:

```python
# In summarize, after computing anomaly run IDs and completed records:
normal = [record for record in completed if str(record["run_id"]) not in anomalous_run_ids]
anomalous = [record for record in completed if str(record["run_id"]) in anomalous_run_ids]
counts["observation"] = {"normal": len(normal), "anomalous": len(anomalous)}
counts["normal_verdict"] = _count([str(record["verdict"]) for record in normal], VERDICTS)
counts["anomalous_verdict"] = _count([str(record["verdict"]) for record in anomalous], VERDICTS)
counts["binding"] = _count([
    "checkout-bound" if record["schema"] == 3 else "historical-unbound"
    for record in records
], ("checkout-bound", "historical-unbound"))
```

Define `anomalous_run_ids: set[str]` by collecting each completed record with a nonempty `observation_anomalies(record)` and the run IDs in `repo_reality_citing_documents_only`. Define `counts` as the existing summary `counts` dictionary before constructing the return object. Do not store computed anomalies back into a record, mutate stored verdicts, or upgrade historical schema.

- [ ] **Step 4: Run GREEN and preserve structural rejection tests.** Existing tests for unknown/missing keys, out-of-range counts, duplicate finding IDs, absolute evidence paths, and oversized strings must still fail input with `schema-invalid`. Tests for contradictory observations must now preserve the observed values and return stable anomaly codes. Run the full direct evidence suite, review historical chain isolation and count definitions, then controller commit `fix(pre-sdd-review): separate observations from semantic verdicts`.

### Task 5: Document the schema 3 lifecycle, privacy, and optional failure behavior

**Files:** Modify `skills/pre-sdd-review/SKILL.md`, `skills/pre-sdd-review/evidence/README.md`, `skills/pre-sdd-review/README.md`, `skills/pre-sdd-review/README.en.md`, `docs/maintainers/products/pre-sdd-review/contract.md`, `docs/maintainers/products/pre-sdd-review/testing.md`, `docs/maintainers/products/pre-sdd-review/compatibility.md`, `tests/products/pre-sdd-review/test_contract.py`.

**Interfaces:** Consume the runtime behavior verified in Tasks 1–4. The recorder handshake is exactly `skill_name=pre-sdd-review`, `schema=3`; the canonical `--version` line is `{"cli_version":"3.0.0","schema":3,"skill_name":"pre-sdd-review"}` followed by one LF. No change to reviewer protocol, role count, trigger list, activation inventory, or seven fixture directories is required.

- [ ] **Step 1: Add contract assertions for the new lifecycle while keeping negative mutation checks.** In `test_contract.py`, add a test that checks explicit schema 3 handshake, read-only legacy handling, `repo_key`, `historical-unbound`, `locking-unavailable`, `invalid_records`, and separate normal/anomalous verdict counts in the recorder/maintainer docs. This is documentation consistency evidence; Tasks 1–4 provide behavior evidence.

```python
def test_recorder_v3_documents_legacy_and_observation_boundaries(self) -> None:
    skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    recorder = (SKILL / "evidence/README.md").read_text(encoding="utf-8")
    contract = (MAINTAINERS / "contract.md").read_text(encoding="utf-8")
    self.assertIn("schema=3", skill_text)
    for token in (
        "repo_key", "historical-unbound", "legacy-record-read-only",
        "locking-unavailable", "invalid_records", "normal_verdict", "anomalous_verdict",
    ):
        self.assertIn(token, recorder)
    self.assertIn("cannot change `READY`, `REVISE`, or `BLOCKED`", contract)
    self.assertIn("false-ready` requires a `READY` verdict", contract)
```

Run the direct `test_contract.py` discovery and capture the expected RED on schema 3 docs. Existing instruction/README digest checks can also fail until the reviewed text is updated; they are not to be removed.

- [ ] **Step 2: Update the exact user and maintainer contracts.** Replace the schema 2 handshake in SKILL and maintainer contract with schema 3 and retain this operational rule:

```text
Record only when skill_name=pre-sdd-review and schema=3. If the recorder is
unavailable or fails, report Evidence: not_recorded with its error code;
this cannot change READY, REVISE, or BLOCKED. A schema 2 pending run remains
historical-unbound and read-only; preserve it and start a new run if recording
is still wanted. Never infer a checkout identity for a historical record.
```

The recorder README must explain `.identity-salt` as local 32-byte private state and `.identity.lock`/`locks/<run-id>.lock` as mutation locks, without printing the salt or path material. Explain that a moved checkout, clone, other worktree, lost salt, or a different evidence home cannot be treated as the original binding. The two normalized paths feed HMAC only; records store `repo` and `repo_key`. Locks require supported OS locking; read-only commands and `--version` do not require it. Do not advertise native Windows mutation support.

Add the full error list including `identity-unavailable`, `legacy-record-read-only`, and `locking-unavailable`, retaining existing codes. State `show` returns validated original bytes. Define `invalid_records` as scan-wide before filters, `--repo` as display-name filtering only, and `--last` as selecting valid ordered records. Define all-observed `counts.verdict`, separate `normal_verdict`/`anomalous_verdict`, and historical binding counts; none is a model-quality or signed-audit claim.

Replace recorder README claims that invalid semantic combinations cannot be stored with: semantic review still requires the existing verdict/reviewer/repair rules; structurally valid deviations remain observed values and appear in `anomalies`. Retain shape, count ranges, record-size, and path restrictions as rejected input. The reviewer protocol remains authoritative for semantic behavior.

- [ ] **Step 3: Make both installed READMEs self-contained.** Replace only repository-external relative links with public repository URLs. Keep `SKILL.md`, `release.toml`, `CHANGELOG.md`, `evidence/README.md`, and `references/reviewer-protocol.md` links local.

```text
../../docs/users/ko/safety-and-privacy.md
→ https://github.com/beyondwin/skills/blob/main/docs/users/ko/safety-and-privacy.md

../../docs/users/en/safety-and-privacy.md
→ https://github.com/beyondwin/skills/blob/main/docs/users/en/safety-and-privacy.md

../../docs/maintainers/products/pre-sdd-review/contract.md
→ https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/pre-sdd-review/contract.md
```

Apply that same deterministic prefix transformation to any other `../../docs/` links in these two files. Do not claim remote availability from local link checks. The shared installed-payload link gate is owned by the integration plan.

- [ ] **Step 4: Refresh only the digests whose approved text changed.** In `test_contract.py`, retain `INSTRUCTION_DOCUMENT_SHA256`, `README_CANONICAL_SECTION_DIGESTS`, `README_CANONICAL_DOCUMENT_DIGESTS`, and maintainer subsection protections. Use the existing hash normalization functions, inspect the exact changed section, update its expected digest, and rerun its existing mutation cases. Do not change `references/reviewer-protocol.md`, risk triggers, case inventory, or fixture fingerprints just to make unrelated checks pass. Send the integration controller the exact changed shared safety/verification statements so its four shared digests can be updated independently.

Run direct product contract and evidence discovery. Version-source checks may still require Task 6's metadata alignment; report those exact expected failures instead of calling the whole product GREEN. Review the schema/privacy/optional boundary text together, then controller commit `docs(pre-sdd-review): explain schema 3 evidence lifecycle`.

### Task 6: Align the 3.0.0 product release and hand off integration evidence

**Files:** Modify `skills/pre-sdd-review/release.toml`, `skills/pre-sdd-review/SKILL.md`, `skills/pre-sdd-review/CHANGELOG.md`, `docs/maintainers/products/pre-sdd-review/release.md`, `tests/products/pre-sdd-review/test_contract.py`, `tests/products/pre-sdd-review/evidence/support.py`, `tests/products/pre-sdd-review/evidence/test_evidence.py`.

**Interfaces:** Product release version, SKILL metadata, CLI version, product test target, and default synthetic skill snapshot become `3.0.0`. Schema 2 remains a deliberate legacy fixture value and read-only compatibility contract. The integration controller consumes canonical schema 3 `--version`, unchanged exact payload membership, and the reviewed product docs.

- [ ] **Step 1: Assert the new release identity before changing metadata.** Set `TARGET_VERSION = "3.0.0"` in the product contract test. Use its existing release/SKILL assertions; update the real-skill snapshot test to `3.0.0`. Run direct product discovery and record RED for existing `2.0.0` release metadata. Do not weaken the release comparisons or use the candidate's version as its own expected value.

- [ ] **Step 2: Change current release metadata and add a dated changelog entry.** Use the actual local implementation date in the new heading, retaining all older entries unchanged. The following code gets the date without assuming planning day is release day:

```bash
python3 -c 'import datetime; print(datetime.date.today().isoformat())'
```

Set `version = "3.0.0"` in `release.toml` and `metadata.version: "3.0.0"` in SKILL. Set SKILL `metadata.updated_at` to that same actual implementation date. Add a `3.0.0` changelog entry with the returned date and these release facts:

```text
- New optional recorder schema 3 binds records to a locally salted checkout identity.
- Schema 2 remains readable as historical-unbound evidence and cannot be mutated.
- Run locks serialize finish, abandon, and outcome; reads isolate corrupt records.
- Structurally valid contradictory observations remain recorded and appear as anomalies.
- Installed README links resolve inside the payload or point to public repository docs.
- Reviewer roles, scalar risk triggers, two-document repairs, repair limits, and semantic verdicts are unchanged.
- This change does not publish a release or claim new native platform/model evidence.
```

Update the current release identity in the maintainer release guide. Change `support.SKILL_MD` and `make_skill_root`'s default version to `3.0.0`, retaining the helper's explicit `version` argument so legacy/snapshot tests can request older versions. Update only positive current-version expectations; keep schema 2 reader samples intact. Refresh the SKILL digest after this metadata change using the same reviewed-byte workflow as Task 5.

- [ ] **Step 3: Run direct product GREEN.**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/pre-sdd-review -p 'test_contract.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/pre-sdd-review/evidence -p 'test_*.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 skills/pre-sdd-review/evidence/evidence.py --version
git diff --check
```

Expected: direct suites pass, `--version` emits exactly the schema 3 canonical line, and diff has no whitespace errors. The existing version test proves no home creation. Native Windows/Linux execution and actual model review quality remain `not_measured` unless separately executed in that environment.

- [ ] **Step 4: Complete focused review and hand off to the controller.** Review the full product diff against P1–P4 and all exclusions, fixing only concrete defects. Include direct test commands/results, changed digests, new summary keys and error codes, unchanged ten-file payload list, and the canonical CLI output in the execution handoff. The controller commits the bounded release alignment as `feat(pre-sdd-review): prepare schema 3 product release` and then owns `scripts/release.py`, shared contracts, full/portable profiles, source-bound extracted ZIP checks, and final repository review. Product-only GREEN is not full-program completion.

## Plan self-review and completion boundary

- P1 maps to Task 1 identity/legacy and Task 4 chain separation, including the actual `git worktree move` regression.
- P2 maps to Task 2 locks, rereads, unique temporary files, exactly one terminal winner, serialized outcomes, and explicit unsupported-lock errors.
- P3 maps to Task 3 exact record shape, timestamps, UUID filename binding, valid schema 2 reads, and isolated invalid-file counts.
- P4 maps to Task 4 typed-only recording, preserved verdicts, anomalies, and separate normal/anomalous counts.
- R5 and schema 3 user contracts map to Task 5; version and dated metadata map to Task 6. Shared release smoke and shared docs belong to the integration controller.
- R6 and P5 remain excluded. Existing record-size, privacy, no-provider, no-publication, role, trigger, repair, and semantic-verdict boundaries remain explicit.
- Source code has not changed merely because this plan exists. Execution starts only in the authorized implementation phase, in the controller-selected isolated worktree.
