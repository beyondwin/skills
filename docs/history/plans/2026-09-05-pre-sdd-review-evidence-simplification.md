# Pre-SDD Review Evidence Simplification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the `pre-sdd-review-evidence` package, installer, and schema 1 receipts with one standard-library script (`evidence/evidence.py`, schema 2) that records what is needed to judge whether `pre-sdd-review` works, exposes it as agent-readable JSON, and ships as `pre-sdd-review` 2.0.0.

**Architecture:** One Python file owns paths, hashes, Git facts, validation, atomic file replacement, and aggregation; the controller (SKILL.md) owns semantic findings, repairs, verdicts, and design-path resolution. Records are one JSON file per run under `~/.pre-sdd-review/runs/`. The repository's closed-contract tests (payload manifest, document digests, case matrix) are updated in the same task as the surface they pin, so every task ends green.

**Tech Stack:** Python 3.11+ standard library (`argparse`, `datetime`, `hashlib`, `json`, `os`, `re`, `statistics`, `subprocess`, `uuid`), `unittest`, Git CLI, Markdown/TOML product contracts.

**Spec:** `docs/history/specs/2026-09-05-pre-sdd-review-evidence-simplification-design.md`

## Global Constraints

- The recorder is exactly `skills/pre-sdd-review/evidence/evidence.py`; no shebang line (the payload contract treats `#!` as executable and rejects it); file mode `0644`.
- Invocation is `python3 "<skill-root>/evidence/evidence.py" <command>`; there is no installer, launcher, PATH entry, zipapp, or Windows wrapper.
- `--version` prints exactly `{"cli_version":"2.0.0","schema":2,"skill_name":"pre-sdd-review"}` followed by `\n`, and touches no evidence home.
- Data root is `~/.pre-sdd-review/`; the only override is a non-empty absolute `PRE_SDD_REVIEW_HOME`. Runs live at `runs/<run-id>.json`. Readers consider only `runs/*.json` with `schema == 2`.
- Every record is at most 64 KiB. Directories are `0o700`, files `0o600`, writes are temp file + `os.replace`.
- Only the standard library. The only subprocess is `git`. All file reads go through one `read_bounded_bytes(path, limit)` that calls `stream.read(limit + 1)`; stdin is read only in `read_stdin(stream, limit)` with the same shape. No `Path.read_text`, `Path.read_bytes`, `os.system`, or `shell=True`. No string constant that begins with `http`, `socket`, `urllib`, `openai`, `anthropic`, or `telemetry`.
- Records hold only repository-relative POSIX paths, a directory name, hashes, enum values, integers, RFC 3339 UTC timestamps, and single-line paraphrases (≤ 300 chars). Never absolute paths.
- Enumerations (exact): clients `codex`, `claude-code`, `cursor`, `grok`, `other`, `unknown`; modes `default`, `review-only`; executions `full`, `degraded`, `blocked`; triggers `runtime-removal`, `schema-migration`, `auth-boundary`, `data-boundary`, `external-side-effect`; verdicts `READY`, `REVISE`, `BLOCKED`; abandon reasons `user-cancelled`, `input-changed`, `scope-changed`, `input-format-fixed`, `other`; outcome labels `good`, `false-ready`, `noisy`, `abandoned`; severities `BLOCKER`, `IMPORTANT`; classes `authority-drift`, `repo-reality`, `coverage`, `ordering`, `verification-gap`; finding statuses `repaired`, `unresolved`, `blocked-by-authority`, `accepted-as-is`.
- Error envelope: one stderr line `{"error":{"code":"<code>","message":"<≤300 chars>"}}` and exit code 2. Codes: `invalid-arguments`, `schema-invalid`, `run-not-found`, `not-git-repository`, `outside-repository`, `already-finished`, `evidence-home-unwritable`.
- Review semantics in SKILL.md do not change except the `## Optional local evidence` section. The reviewer protocol changes by exactly one sentence.
- Product version becomes `2.0.0` in `release.toml`, `SKILL.md` `metadata.version`, and a dated `## 2.0.0 - 2026-09-05` CHANGELOG heading.
- Host support in `products.toml` does not change. No tag, push, GitHub Release, or catalog mutation.
- Schema 1 receipts, `config.json`, `identity.key`, and the installed launcher on the owner's machine are outside the repository and are not migrated or deleted by this plan.
- Run tests with `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s <dir> -p '<pattern>'` from the repository root, as the maintainer docs specify.

---

## File Structure

| Path | Responsibility |
| --- | --- |
| `skills/pre-sdd-review/evidence/evidence.py` (create) | Whole recorder: constants, errors, JSON/IO helpers, Git helpers, skill snapshot, validation, commands, summary, `main` |
| `skills/pre-sdd-review/evidence/README.md` (rewrite) | Invocation, data layout, commands, stdin shape, boundary, errors |
| `skills/pre-sdd-review/evidence/install.py`, `evidence/pre_sdd_review_evidence/` (delete) | Old installer and package |
| `tests/products/pre-sdd-review/evidence/support.py` (rewrite) | Temp Git repo, synthetic skill root, in-process CLI runner, payload builders |
| `tests/products/pre-sdd-review/evidence/test_evidence.py` (create) | All recorder tests |
| `tests/products/pre-sdd-review/evidence/test_{cli,install,outcome,reporting,repository,schema,storage}.py` (delete) | Old tests |
| `tests/products/pre-sdd-review/test_contract.py` (modify) | Payload set, AST allowlist, SKILL/protocol digests, evidence-section facts, cases, README/maintainer digests, version pins |
| `tests/products/pre-sdd-review/cases.json` (modify) | Five evidence cases |
| `scripts/release.py` (modify) | Payload set and `--version` smoke |
| `tests/repository/test_release.py`, `test_release_contract.py`, `test_public_docs.py` (modify) | Payload, version, and user-doc pins |
| `skills/pre-sdd-review/SKILL.md`, `references/reviewer-protocol.md`, `README.md`, `README.en.md`, `CHANGELOG.md`, `release.toml` (modify) | Contract, docs, version |
| `docs/maintainers/products/pre-sdd-review/{contract,testing,compatibility,release}.md` (modify) | Maintainer evidence text |
| `docs/users/{ko,en}/{installation,verification,safety-and-privacy}.md` (modify) | User evidence text |

Digest helper used by Tasks 6–9 (run from the repository root; paste the printed values into the named constants):

```bash
python3 - <<'EOF'
import hashlib, sys
sys.path.insert(0, "tests/products/pre-sdd-review")
import test_contract as t
skill = t.SKILL
print("INSTRUCTION SKILL.md", hashlib.sha256((skill / "SKILL.md").read_bytes()).hexdigest())
print("INSTRUCTION protocol", hashlib.sha256((skill / "references/reviewer-protocol.md").read_bytes()).hexdigest())
for lang, name in (("ko", "README.md"), ("en", "README.en.md")):
    text = (skill / name).read_text(encoding="utf-8")
    print("README_CANONICAL_DOCUMENT_DIGESTS", lang, t.whole_document_digest(text))
    for heading, _ in t.README_CANONICAL_SECTION_DIGESTS[lang]:
        print("README_CANONICAL_SECTION_DIGESTS", lang, heading, t.canonical_digest(t.markdown_section(text, heading)))
contract = (t.MAINTAINERS / "contract.md").read_text(encoding="utf-8")
print("MAINTAINER_CANONICAL_DIGEST", t.canonical_digest(contract))
for heading, _ in t.MAINTAINER_CANONICAL_SUBSECTION_DIGESTS:
    print("MAINTAINER_CANONICAL_SUBSECTION_DIGESTS", heading, t.canonical_digest(t.subsection(contract, heading)))
for name in ("testing", "compatibility", "release"):
    print(f"{name.upper()}_CANONICAL_DIGEST", t.whole_document_digest((t.MAINTAINERS / f"{name}.md").read_text(encoding="utf-8")))
EOF
```

---

### Task 1: Swap the payload — skeleton script, delete the old package, update every manifest

**Files:**
- Create: `skills/pre-sdd-review/evidence/evidence.py`
- Delete: `skills/pre-sdd-review/evidence/install.py`, `skills/pre-sdd-review/evidence/pre_sdd_review_evidence/` (all files and `__pycache__`), `tests/products/pre-sdd-review/evidence/test_cli.py`, `test_install.py`, `test_outcome.py`, `test_reporting.py`, `test_repository.py`, `test_schema.py`, `test_storage.py`
- Rewrite: `tests/products/pre-sdd-review/evidence/support.py`
- Create: `tests/products/pre-sdd-review/evidence/test_evidence.py`
- Modify: `tests/products/pre-sdd-review/test_contract.py:27-47` (payload set), `:711-855` (AST allowlist), `:863-1017` (runtime and payload tests)
- Modify: `scripts/release.py:76-86` (payload set), `:574-643` (`_smoke_pre_sdd_review`)
- Modify: `tests/repository/test_release_contract.py:92-113`
- Modify: `tests/repository/test_release.py:556-577`

**Interfaces:**
- Produces: `evidence.main(argv, *, stdin, stdout, stderr, environ, cwd) -> int`; `evidence.EvidenceError(code, message)`; `evidence.canonical(value) -> bytes`; constants `CLI_VERSION = "2.0.0"`, `SCHEMA = 2`, `SKILL_NAME = "pre-sdd-review"`.
- Produces for tests: `support.run(argv, *, home, cwd, stdin_text="") -> tuple[int, str, str]`.

- [ ] **Step 1: Write the failing test for `--version` and the error envelope**

Create `tests/products/pre-sdd-review/evidence/support.py`:

```python
from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
EVIDENCE_DIR = ROOT / "skills" / "pre-sdd-review" / "evidence"
if str(EVIDENCE_DIR) not in sys.path:
    sys.path.insert(0, str(EVIDENCE_DIR))

import evidence  # noqa: E402

SKILL_MD = (
    "---\n"
    "name: pre-sdd-review\n"
    "description: synthetic\n"
    "metadata:\n"
    '  version: "2.0.0"\n'
    "---\n\n# Pre-SDD Review\n"
)
PROTOCOL_MD = "# Reviewer protocol\n\nRead-only.\n"


def run_git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args], check=False, capture_output=True, text=True
    )


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def make_git_repo(workspace: Path, name: str = "repo") -> Path:
    repo = workspace / name
    repo.mkdir(parents=True)
    for args in (
        ("init", "--quiet"),
        ("config", "user.name", "Evidence Tests"),
        ("config", "user.email", "evidence@example.invalid"),
    ):
        result = run_git(repo, *args)
        if result.returncode != 0:
            raise AssertionError(result.stderr)
    write(repo / "docs/design.md", "# Design\n")
    write(repo / "docs/plan.md", "# Plan\n\n**Spec:** docs/design.md\n")
    write(repo / "src/app.ts", "export const app = 1;\n")
    for args in (("add", "."), ("commit", "--quiet", "-m", "initial")):
        result = run_git(repo, *args)
        if result.returncode != 0:
            raise AssertionError(result.stderr)
    return repo


def commit_all(repo: Path, message: str = "change") -> None:
    for args in (("add", "."), ("commit", "--quiet", "-m", message)):
        result = run_git(repo, *args)
        if result.returncode != 0:
            raise AssertionError(result.stderr)


def make_skill_root(workspace: Path, version: str = "2.0.0") -> Path:
    root = workspace / "skill"
    write(root / "SKILL.md", SKILL_MD.replace('"2.0.0"', f'"{version}"'))
    write(root / "references/reviewer-protocol.md", PROTOCOL_MD)
    return root


def run(argv: list[str], *, home: Path, cwd: Path, stdin_text: str = "") -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    code = evidence.main(
        list(argv),
        stdin=io.StringIO(stdin_text),
        stdout=out,
        stderr=err,
        environ={"PRE_SDD_REVIEW_HOME": str(home)},
        cwd=cwd,
    )
    return code, out.getvalue(), err.getvalue()


def error_code(stderr_text: str) -> str:
    return json.loads(stderr_text)["error"]["code"]


def start(
    home: Path,
    repo: Path,
    skill_root: Path,
    *,
    design: bool = True,
    client: str = "codex",
    model: str = "gpt-test",
    mode: str = "default",
) -> str:
    argv = [
        "start",
        "--skill-root", str(skill_root),
        "--repo", str(repo),
        "--plan", str(repo / "docs/plan.md"),
        "--client", client,
        "--model", model,
        "--mode", mode,
    ]
    if design:
        argv += ["--design", str(repo / "docs/design.md")]
    code, out, err = run(argv, home=home, cwd=repo)
    if code != 0:
        raise AssertionError(err)
    return json.loads(out)["run_id"]


def finding(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "id": "PSDR-001",
        "severity": "IMPORTANT",
        "class": "verification-gap",
        "pattern": "build-only-acceptance",
        "status": "repaired",
        "repair_pass": 1,
        "location": {"path": "docs/plan.md", "locator": "Task 2"},
        "evidence": ["src/app.ts"],
        "consequence": "A build-only check passes a wrong implementation.",
        "fix": "Add a behavioral unit test to Task 2.",
    }
    value.update(overrides)
    return value


def finish_payload(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "execution": "full",
        "reviewers": 1,
        "trigger": None,
        "degraded_reasons": [],
        "verdict": "READY",
        "block_reason": None,
        "review_passes": 1,
        "repair_passes": 0,
        "findings": [],
    }
    value.update(overrides)
    return value


def finish(home: Path, repo: Path, run_id: str, payload: dict[str, object]) -> tuple[int, str, str]:
    return run(
        ["finish", "--run-id", run_id, "--repo", str(repo)],
        home=home,
        cwd=repo,
        stdin_text=json.dumps(payload),
    )


def load(home: Path, run_id: str) -> dict[str, object]:
    return json.loads((home / "runs" / f"{run_id}.json").read_text(encoding="utf-8"))
```

Create `tests/products/pre-sdd-review/evidence/test_evidence.py`:

```python
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from support import EVIDENCE_DIR, error_code, run


VERSION_LINE = b'{"cli_version":"2.0.0","schema":2,"skill_name":"pre-sdd-review"}\n'


class VersionTests(unittest.TestCase):
    def test_version_is_canonical_and_touches_no_home(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "home"
            code, out, err = run(["--version"], home=home, cwd=Path(directory))
            self.assertEqual((code, out.encode("utf-8"), err), (0, VERSION_LINE, ""))
            self.assertFalse(home.exists())

    def test_version_rejects_extra_arguments(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            code, out, err = run(["--version", "summary"], home=Path(directory), cwd=Path(directory))
            self.assertEqual((code, out), (2, ""))
            self.assertEqual(error_code(err), "invalid-arguments")

    def test_unknown_command_uses_error_envelope(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            code, out, err = run(["prune"], home=Path(directory), cwd=Path(directory))
            self.assertEqual((code, out), (2, ""))
            envelope = json.loads(err)
            self.assertEqual(set(envelope), {"error"})
            self.assertEqual(set(envelope["error"]), {"code", "message"})
            self.assertEqual(envelope["error"]["code"], "invalid-arguments")

    def test_script_runs_as_a_file_without_installation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "home"
            completed = subprocess.run(
                [sys.executable, str(EVIDENCE_DIR / "evidence.py"), "--version"],
                check=False,
                capture_output=True,
                env={"PRE_SDD_REVIEW_HOME": str(home), "PYTHONDONTWRITEBYTECODE": "1", "PATH": ""},
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(completed.stdout, VERSION_LINE)
            self.assertFalse(home.exists())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the new test to verify it fails**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/pre-sdd-review/evidence -p 'test_evidence.py'`
Expected: FAIL/ERROR with `ModuleNotFoundError: No module named 'evidence'`.

- [ ] **Step 3: Delete the old package, installer, and tests**

```bash
git rm -q -r skills/pre-sdd-review/evidence/install.py skills/pre-sdd-review/evidence/pre_sdd_review_evidence
rm -rf skills/pre-sdd-review/evidence/__pycache__
git rm -q tests/products/pre-sdd-review/evidence/test_cli.py tests/products/pre-sdd-review/evidence/test_install.py tests/products/pre-sdd-review/evidence/test_outcome.py tests/products/pre-sdd-review/evidence/test_reporting.py tests/products/pre-sdd-review/evidence/test_repository.py tests/products/pre-sdd-review/evidence/test_schema.py tests/products/pre-sdd-review/evidence/test_storage.py
rm -rf tests/products/pre-sdd-review/evidence/__pycache__
```

- [ ] **Step 4: Write the skeleton `evidence.py`**

Create `skills/pre-sdd-review/evidence/evidence.py` (no shebang):

```python
"""Local evidence recorder for pre-sdd-review (schema 2). Standard library only."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import statistics
import subprocess
import sys
import uuid
from collections.abc import Mapping
from pathlib import Path
from typing import TextIO

CLI_VERSION = "2.0.0"
SCHEMA = 2
SKILL_NAME = "pre-sdd-review"
RECORD_LIMIT = 64 * 1024
DOCUMENT_LIMIT = 8 * 1024 * 1024
SKILL_DOCUMENT_LIMIT = 256 * 1024

CLIENTS = ("codex", "claude-code", "cursor", "grok", "other", "unknown")
MODES = ("default", "review-only")
EXECUTIONS = ("full", "degraded", "blocked")
TRIGGERS = ("runtime-removal", "schema-migration", "auth-boundary", "data-boundary", "external-side-effect")
VERDICTS = ("READY", "REVISE", "BLOCKED")
ABANDON_REASONS = ("user-cancelled", "input-changed", "scope-changed", "input-format-fixed", "other")
OUTCOME_LABELS = ("good", "false-ready", "noisy", "abandoned")
SEVERITIES = ("BLOCKER", "IMPORTANT")
CLASSES = ("authority-drift", "repo-reality", "coverage", "ordering", "verification-gap")
FINDING_STATUSES = ("repaired", "unresolved", "blocked-by-authority", "accepted-as-is")
FINISH_KEYS = frozenset({
    "execution", "reviewers", "trigger", "degraded_reasons", "verdict",
    "block_reason", "review_passes", "repair_passes", "findings",
})
FINDING_KEYS = frozenset({
    "id", "severity", "class", "pattern", "status", "repair_pass",
    "location", "evidence", "consequence", "fix",
})

_PATTERN = re.compile(r"[a-z0-9][a-z0-9._-]{0,79}\Z")
_FINDING_ID = re.compile(r"PSDR-[0-9]{3,}\Z")
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")
_VERSION_LINE = re.compile(r'^\s*version:\s*["\']?([^\s"\']+)["\']?\s*$', re.MULTILINE)
_DRIVE = re.compile(r"^[A-Za-z]:")


class EvidenceError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def fail(code: str, message: str) -> None:
    raise EvidenceError(code, message)


def canonical(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:  # noqa: D401 - argparse hook
        raise EvidenceError("invalid-arguments", message)


def build_parser() -> _Parser:
    parser = _Parser(prog="evidence.py", add_help=True)
    parser.add_subparsers(dest="command", required=True)
    return parser


def main(
    argv: list[str] | None = None,
    *,
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
    environ: Mapping[str, str] | None = None,
    cwd: Path | None = None,
) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    stdin = sys.stdin if stdin is None else stdin
    stdout = sys.stdout if stdout is None else stdout
    stderr = sys.stderr if stderr is None else stderr
    environ = os.environ if environ is None else environ
    cwd = Path.cwd() if cwd is None else Path(cwd)
    try:
        if arguments == ["--version"]:
            stdout.write(canonical({"cli_version": CLI_VERSION, "schema": SCHEMA, "skill_name": SKILL_NAME}).decode("utf-8"))
            return 0
        if "--version" in arguments:
            fail("invalid-arguments", "--version accepts no other arguments")
        build_parser().parse_args(arguments)
        fail("invalid-arguments", "unknown command")
    except EvidenceError as exc:
        message = exc.message[:300].replace("\n", " ").replace("\r", " ")
        stderr.write(canonical({"error": {"code": exc.code, "message": message}}).decode("utf-8"))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Run the new test to verify it passes**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/pre-sdd-review/evidence -p 'test_evidence.py'`
Expected: `Ran 4 tests ... OK`.

- [ ] **Step 6: Update the payload manifest and runtime contract in `test_contract.py`**

Replace lines 27–47 (the `PRE_SDD_REVIEW_PAYLOAD_FILES` literal) with:

```python
PRE_SDD_REVIEW_PAYLOAD_FILES = frozenset(
    {
        "CHANGELOG.md",
        "LICENSE.txt",
        "README.en.md",
        "README.md",
        "SKILL.md",
        "agents/openai.yaml",
        "evidence/README.md",
        "evidence/evidence.py",
        "references/reviewer-protocol.md",
        "release.toml",
    }
)
```

In `evidence_runtime_contract_errors`, replace the reader allowlist

```python
                        if (path.name, owner) not in {
                            ("cli.py", "_read_stdin"),
                            ("schema.py", "read_bounded_bytes"),
                        }:
```

with

```python
                        if (path.name, owner) not in {
                            ("evidence.py", "read_stdin"),
                            ("evidence.py", "read_bounded_bytes"),
                        }:
```

Replace the three tests `test_evidence_runtime_is_offline_provider_free_and_uses_bounded_reads`, `test_evidence_runtime_contract_detects_aliased_offline_and_reader_bypasses`, and `test_source_payload_contract_ignores_generated_python_cache` with:

```python
    def test_evidence_runtime_is_offline_provider_free_and_uses_bounded_reads(self) -> None:
        self.assertEqual(evidence_runtime_contract_errors(SKILL / "evidence"), ())

    def test_evidence_runtime_contract_detects_aliased_offline_and_reader_bypasses(self) -> None:
        mutations = (
            ("subprocess-module-alias", "\nimport subprocess as sp\nsp.run(['python3', '-c', 'pass'])\n", "launches a non-Git subprocess"),
            ("subprocess-symbol-alias", "\nfrom subprocess import run as invoke\ninvoke(['python3', '-c', 'pass'])\n", "launches a non-Git subprocess"),
            ("os-module-alias", "\nimport os as operating\noperating.system('git status')\n", "may not call os.system"),
            ("os-symbol-alias", "\nfrom os import system as invoke\ninvoke('git status')\n", "may not call os.system"),
            ("reader-method-alias", "\ndef bypass(stream):\n    reader = stream.read\n    return reader()\n", "bypasses the single bounded reader path"),
            ("path-read-text", "\ndef bypass(path):\n    return path.read_text()\n", "bypasses the shared bounded reader"),
            ("unbounded-read", "\ndef other(stream):\n    return stream.read()\n", "bypasses the single bounded reader path"),
        )
        for name, content, expected in mutations:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                copied = Path(directory) / "evidence"
                shutil.copytree(SKILL / "evidence", copied, ignore=shutil.ignore_patterns("__pycache__"))
                module = copied / "evidence.py"
                module.write_text(module.read_text(encoding="utf-8") + content, encoding="utf-8")
                self.assertTrue(any(expected in error for error in evidence_runtime_contract_errors(copied)), name)

        with tempfile.TemporaryDirectory() as directory:
            copied = Path(directory) / "evidence"
            shutil.copytree(SKILL / "evidence", copied, ignore=shutil.ignore_patterns("__pycache__"))
            module = copied / "evidence.py"
            module.write_text(
                module.read_text(encoding="utf-8") + "\nimport subprocess as sp\nsp.run(['git', 'status'])\n",
                encoding="utf-8",
            )
            self.assertEqual(evidence_runtime_contract_errors(copied), ())

    def test_source_payload_contract_ignores_generated_python_cache(self) -> None:
        validator = globals().get("product_payload_contract_errors")
        assert validator is not None
        with tempfile.TemporaryDirectory() as directory:
            copied = Path(directory) / "pre-sdd-review"
            shutil.copytree(SKILL, copied, ignore=shutil.ignore_patterns("__pycache__"))
            cache = copied / "evidence/__pycache__"
            cache.mkdir()
            (cache / "evidence.cpython-311.pyc").write_bytes(b"bytecode")
            self.assertEqual(validator(copied), ())
```

In `test_source_payload_contract_rejects_append_only_overrides_and_runtime`, replace the two mutations named `unlisted-evidence-sibling` and `unlisted-report-sibling` with:

```python
            (
                "unlisted-evidence-sibling",
                "evidence/network.py",
                "# Network access is not part of this product.\n",
                "unexpected payload member: evidence/network.py",
            ),
            (
                "unlisted-installer",
                "evidence/install.py",
                "# Installers are not part of this product.\n",
                "unexpected payload member: evidence/install.py",
            ),
```

- [ ] **Step 7: Update `scripts/release.py`**

Replace lines 76–86 (the `PRE_SDD_REVIEW_PAYLOAD_FILES` literal) with the same ten-entry set as Step 6. Replace the body of `_smoke_pre_sdd_review` from `runtime_prefix = "evidence/pre_sdd_review_evidence/"` through the end of the function with:

```python
    if errors:
        return errors

    expected_version = {"cli_version": "2.0.0", "schema": 2, "skill_name": "pre-sdd-review"}
    expected_bytes = b'{"cli_version":"2.0.0","schema":2,"skill_name":"pre-sdd-review"}\n'
    with tempfile.TemporaryDirectory(prefix="pre-sdd-review-smoke-") as directory:
        evidence_home = Path(directory) / "evidence-home-must-stay-absent"
        environ = os.environ.copy()
        environ["PRE_SDD_REVIEW_HOME"] = str(evidence_home)
        environ["PYTHONDONTWRITEBYTECODE"] = "1"
        try:
            completed = subprocess.run(
                [sys.executable, str(skill_root / "evidence" / "evidence.py"), "--version"],
                cwd=skill_root,
                env=environ,
                check=False,
                capture_output=True,
            )
        except OSError:
            return ["pre-sdd-review: extracted evidence recorder could not execute"]
        if completed.returncode != 0:
            errors.append("pre-sdd-review: extracted evidence recorder --version failed")
        if completed.stdout != expected_bytes or completed.stderr != b"":
            errors.append("pre-sdd-review: extracted evidence recorder version bytes differ")
        try:
            version = json.loads(completed.stdout)
        except (UnicodeError, json.JSONDecodeError):
            version = None
        if version != expected_version:
            errors.append("pre-sdd-review: extracted evidence recorder version object differs")
        if evidence_home.exists():
            errors.append("pre-sdd-review: extracted evidence recorder --version touched evidence home")
    return errors
```

(Keep the `present`/`errors` computation above it unchanged; the removed block is only the `runtime_prefix` manifest check and the old `-m pre_sdd_review_evidence` invocation.)

- [ ] **Step 8: Update repository tests**

In `tests/repository/test_release_contract.py`, replace `test_pre_sdd_installer_sources_remain_non_executable` (lines 92–113) with:

```python
    def test_pre_sdd_evidence_sources_remain_non_executable(self) -> None:
        from scripts.lib.product_contract import payload_entries

        entries = {
            entry["path"]: entry
            for entry in payload_entries(ROOT / "skills/pre-sdd-review")
        }
        self.assertEqual(entries["evidence/evidence.py"]["mode"], "0644")
        self.assertEqual(entries["evidence/README.md"]["mode"], "0644")
        self.assertNotIn("evidence/install.py", entries)
```

In `tests/repository/test_release.py`, inside `test_pre_sdd_review_extracted_smoke_checks_runtime_and_avoids_configured_home`, replace

```python
            runtime = skill_root / "evidence/pre_sdd_review_evidence"
            (runtime / "network.py").write_text("# extra\n", encoding="utf-8")
            self.assertIn(
                "pre-sdd-review: runtime package manifest mismatch",
                release._smoke_pre_sdd_review(skill_root),
            )
```

with

```python
            (skill_root / "evidence/extra.py").write_text("# extra\n", encoding="utf-8")
            self.assertIn(
                "pre-sdd-review: unexpected payload member: evidence/extra.py",
                release._smoke_pre_sdd_review(skill_root),
            )
```

- [ ] **Step 9: Run the three affected stages**

Run:
```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/pre-sdd-review -p 'test_contract.py'
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/pre-sdd-review/evidence -p 'test_*.py'
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/repository -p 'test_*.py'
```
Expected: all `OK`. (The `test_v1_2_docs_*` tests still pass because the docs are unchanged in this task.)

- [ ] **Step 10: Commit**

```bash
git add -A skills/pre-sdd-review/evidence tests/products/pre-sdd-review scripts/release.py tests/repository
git commit -m "refactor(pre-sdd-review): replace evidence package with single-file recorder skeleton"
```

---

### Task 2: Paths, Git facts, skill snapshot, and `start`

**Files:**
- Modify: `skills/pre-sdd-review/evidence/evidence.py`
- Test: `tests/products/pre-sdd-review/evidence/test_evidence.py`

**Interfaces:**
- Produces: `evidence_home(environ) -> Path`, `run_path(home, run_id) -> Path`, `write_record(path, record)`, `load_record(home, run_id) -> dict`, `read_bounded_bytes(path, limit) -> bytes`, `git_root(locator) -> Path`, `git_state(root) -> tuple[str, bool]`, `repository_relative(root, argument, cwd) -> str`, `document_hash(root, relative) -> str`, `skill_snapshot(skill_root) -> dict`, `utc_now() -> str`, `cmd_start(args, home, cwd) -> dict`.
- Record shape after `start` (used by Tasks 3–5): all top-level keys from the spec present; `status = "pending"`; `completed_at`, `elapsed_s`, `plan.sha_end`, `design.sha_end`, `git.head_end`, `git.dirty_end`, `execution`, `reviewers`, `trigger`, `review_passes`, `repair_passes`, `verdict`, `block_reason`, `abandon_reason`, `outcome` are `null`; `degraded_reasons = []`; `findings = []`.

- [ ] **Step 1: Write failing tests for `start`**

Append to `test_evidence.py` (add `import os` and `import stat` at the top, and extend the `support` import to `from support import EVIDENCE_DIR, commit_all, error_code, finding, finish, finish_payload, load, make_git_repo, make_skill_root, run, start, write`):

```python
class StartTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.workspace = Path(self.directory.name)
        self.home = self.workspace / "home"
        self.repo = make_git_repo(self.workspace)
        self.skill = make_skill_root(self.workspace)

    def tearDown(self) -> None:
        self.directory.cleanup()

    def test_start_writes_a_pending_record_with_git_and_document_facts(self) -> None:
        run_id = start(self.home, self.repo, self.skill)
        record = load(self.home, run_id)
        head = subprocess.run(["git", "-C", str(self.repo), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
        self.assertEqual(record["schema"], 2)
        self.assertEqual(record["status"], "pending")
        self.assertEqual(record["repo"], "repo")
        self.assertEqual(record["client"], {"id": "codex", "model": "gpt-test"})
        self.assertEqual(record["mode"], "default")
        self.assertEqual(record["skill"]["version"], "2.0.0")
        self.assertRegex(record["skill"]["sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(record["plan"]["path"], "docs/plan.md")
        self.assertRegex(record["plan"]["sha_start"], r"^[0-9a-f]{64}$")
        self.assertIsNone(record["plan"]["sha_end"])
        self.assertEqual(record["design"]["path"], "docs/design.md")
        self.assertEqual(record["git"], {"head_start": head, "head_end": None, "dirty_start": False, "dirty_end": None})
        for key in ("completed_at", "elapsed_s", "execution", "reviewers", "trigger", "review_passes", "repair_passes", "verdict", "block_reason", "abandon_reason", "outcome"):
            self.assertIsNone(record[key], key)
        self.assertEqual(record["degraded_reasons"], [])
        self.assertEqual(record["findings"], [])
        self.assertRegex(record["started_at"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z$")
        path = self.home / "runs" / f"{run_id}.json"
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE((self.home / "runs").stat().st_mode), 0o700)
        self.assertNotIn(str(self.repo), path.read_text(encoding="utf-8"))

    def test_start_without_design_records_null_and_dirty_worktree(self) -> None:
        write(self.repo / "docs/plan.md", "# Plan\n\nno spec\n")
        run_id = start(self.home, self.repo, self.skill, design=False)
        record = load(self.home, run_id)
        self.assertIsNone(record["design"])
        self.assertTrue(record["git"]["dirty_start"])

    def test_start_accepts_relative_paths_from_cwd(self) -> None:
        code, out, err = run(
            ["start", "--skill-root", str(self.skill), "--repo", ".", "--plan", "docs/plan.md",
             "--design", "./docs/design.md", "--client", "claude-code", "--model", "unknown", "--mode", "review-only"],
            home=self.home, cwd=self.repo,
        )
        self.assertEqual(code, 0, err)
        record = load(self.home, json.loads(out)["run_id"])
        self.assertEqual((record["plan"]["path"], record["design"]["path"], record["mode"]), ("docs/plan.md", "docs/design.md", "review-only"))

    def test_start_rejects_plan_outside_repository(self) -> None:
        outside = self.workspace / "elsewhere.md"
        write(outside, "# Plan\n")
        code, _, err = run(
            ["start", "--skill-root", str(self.skill), "--repo", str(self.repo), "--plan", str(outside),
             "--client", "codex", "--model", "m", "--mode", "default"],
            home=self.home, cwd=self.repo,
        )
        self.assertEqual((code, error_code(err)), (2, "outside-repository"))

    def test_start_rejects_non_git_repository(self) -> None:
        plain = self.workspace / "plain"
        write(plain / "plan.md", "# Plan\n")
        code, _, err = run(
            ["start", "--skill-root", str(self.skill), "--repo", str(plain), "--plan", str(plain / "plan.md"),
             "--client", "codex", "--model", "m", "--mode", "default"],
            home=self.home, cwd=plain,
        )
        self.assertEqual((code, error_code(err)), (2, "not-git-repository"))

    def test_start_rejects_skill_root_without_protocol_or_version(self) -> None:
        broken = self.workspace / "broken"
        write(broken / "SKILL.md", "---\nname: pre-sdd-review\n---\n")
        code, _, err = run(
            ["start", "--skill-root", str(broken), "--repo", str(self.repo), "--plan", "docs/plan.md",
             "--client", "codex", "--model", "m", "--mode", "default"],
            home=self.home, cwd=self.repo,
        )
        self.assertEqual((code, error_code(err)), (2, "invalid-arguments"))

    def test_start_rejects_unknown_client_and_invalid_home(self) -> None:
        code, _, err = run(
            ["start", "--skill-root", str(self.skill), "--repo", str(self.repo), "--plan", "docs/plan.md",
             "--client", "gemini", "--model", "m", "--mode", "default"],
            home=self.home, cwd=self.repo,
        )
        self.assertEqual((code, error_code(err)), (2, "invalid-arguments"))
        code, _, err = run(["summary"], home=Path("relative/home"), cwd=self.repo)
        self.assertEqual((code, error_code(err)), (2, "invalid-arguments"))

    def test_start_reads_the_real_skill_root_version(self) -> None:
        real_skill = EVIDENCE_DIR.parent
        code, out, err = run(
            ["start", "--skill-root", str(real_skill), "--repo", str(self.repo), "--plan", "docs/plan.md",
             "--client", "codex", "--model", "m", "--mode", "default"],
            home=self.home, cwd=self.repo,
        )
        self.assertEqual(code, 0, err)
        import tomllib
        release = tomllib.loads((real_skill / "release.toml").read_text(encoding="utf-8"))
        self.assertEqual(load(self.home, json.loads(out)["run_id"])["skill"]["version"], release["version"])
```

- [ ] **Step 2: Run to verify failure**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/pre-sdd-review/evidence -p 'test_evidence.py'`
Expected: `StartTests` fail with `invalid-arguments` (no `start` subcommand yet) and `test_start_rejects_unknown_client_and_invalid_home` fails on the `summary` call.

- [ ] **Step 3: Implement helpers and `start`**

Insert after `canonical` in `evidence.py`:

```python
def read_bounded_bytes(path: Path, limit: int) -> bytes:
    with Path(path).open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        fail("schema-invalid", f"{Path(path).name} exceeds {limit} bytes")
    return data


def read_stdin(stream: TextIO, limit: int) -> object:
    text = stream.read(limit + 1)
    if len(text.encode("utf-8")) > limit:
        fail("schema-invalid", f"stdin exceeds {limit} bytes")
    return parse_json(text.encode("utf-8"), "stdin")


def parse_json(data: bytes, name: str) -> object:
    try:
        return json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        fail("schema-invalid", f"{name} is not valid UTF-8 JSON")
    return None


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def utc_now() -> str:
    # Microsecond precision keeps `started_at` ordering stable for runs started in the same second.
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def elapsed_seconds(start: str, end: str) -> int:
    begin = dt.datetime.fromisoformat(start.replace("Z", "+00:00"))
    finish = dt.datetime.fromisoformat(end.replace("Z", "+00:00"))
    return max(0, int((finish - begin).total_seconds()))


# ---------------------------------------------------------------- storage

def evidence_home(environ: Mapping[str, str]) -> Path:
    override = environ.get("PRE_SDD_REVIEW_HOME")
    if override is None:
        return Path.home() / ".pre-sdd-review"
    candidate = Path(override.strip()).expanduser()
    if not override.strip() or not candidate.is_absolute():
        fail("invalid-arguments", "PRE_SDD_REVIEW_HOME must be a non-empty absolute path")
    return candidate


def validate_run_id(value: str) -> str:
    try:
        parsed = uuid.UUID(str(value))
    except ValueError:
        fail("invalid-arguments", "run_id must be a canonical lowercase UUID")
    if str(parsed) != value:
        fail("invalid-arguments", "run_id must be a canonical lowercase UUID")
    return value


def run_path(home: Path, run_id: str) -> Path:
    return home / "runs" / f"{validate_run_id(run_id)}.json"


def write_record(path: Path, record: dict[str, object]) -> None:
    payload = canonical(record)
    if len(payload) > RECORD_LIMIT:
        fail("schema-invalid", f"record exceeds {RECORD_LIMIT} bytes")
    temp = path.with_name(path.name + ".tmp")
    try:
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        descriptor = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    except OSError as exc:
        raise EvidenceError("evidence-home-unwritable", "evidence storage is unavailable") from exc


def load_record(home: Path, run_id: str) -> dict[str, object]:
    path = run_path(home, run_id)
    if not path.is_file():
        fail("run-not-found", "run was not found")
    record = parse_json(read_bounded_bytes(path, RECORD_LIMIT), "record")
    if not isinstance(record, dict) or record.get("schema") != SCHEMA:
        fail("schema-invalid", "record is not a schema 2 record")
    return record


def iter_records(home: Path) -> list[dict[str, object]]:
    runs = home / "runs"
    if not runs.is_dir():
        return []
    records: list[dict[str, object]] = []
    for path in runs.glob("*.json"):
        if not path.is_file():
            continue
        try:
            record = parse_json(read_bounded_bytes(path, RECORD_LIMIT), path.name)
        except EvidenceError:
            continue
        if isinstance(record, dict) and record.get("schema") == SCHEMA and isinstance(record.get("started_at"), str):
            records.append(record)
    return sorted(records, key=lambda item: (str(item["started_at"]), str(item["run_id"])))


# -------------------------------------------------------------------- git

def git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(root), *args], check=False, capture_output=True, text=True)


def locator(cwd: Path, value: str) -> Path:
    candidate = Path(value)
    return candidate if candidate.is_absolute() else cwd / candidate


def git_root(path: Path) -> Path:
    directory = path if path.is_dir() else path.parent
    if not directory.is_dir():
        fail("not-git-repository", "repository locator does not exist")
    result = git(directory, "rev-parse", "--show-toplevel")
    output = result.stdout.strip()
    if result.returncode != 0 or not output or "\n" in output:
        fail("not-git-repository", "repository locator is not inside a Git repository")
    return Path(output).resolve()


def git_state(root: Path) -> tuple[str, bool]:
    head = git(root, "rev-parse", "--verify", "HEAD")
    head_value = head.stdout.strip().lower() if head.returncode == 0 else "unborn"
    status = git(root, "status", "--porcelain")
    if status.returncode != 0:
        fail("not-git-repository", "git status is unavailable")
    return head_value, bool(status.stdout.strip())


def safe_relative(value: object) -> bool:
    if not isinstance(value, str) or not value or "\\" in value or value.startswith("/") or _DRIVE.match(value):
        return False
    return all(part not in ("", ".", "..") for part in value.split("/"))


def repository_relative(root: Path, argument: str, cwd: Path) -> str:
    resolved = locator(cwd, argument).resolve()
    try:
        relative = resolved.relative_to(root).as_posix()
    except ValueError:
        fail("outside-repository", f"{Path(argument).name} is outside the repository")
    if not resolved.is_file() or not safe_relative(relative):
        fail("outside-repository", f"{Path(argument).name} is not a file inside the repository")
    return relative


def document_hash(root: Path, relative: str) -> str:
    path = root / relative
    if not path.is_file():
        fail("outside-repository", f"{relative} is missing")
    return sha256(read_bounded_bytes(path, DOCUMENT_LIMIT))


def skill_snapshot(skill_root: Path) -> dict[str, str]:
    skill_md = skill_root / "SKILL.md"
    protocol = skill_root / "references" / "reviewer-protocol.md"
    if not skill_md.is_file() or not protocol.is_file():
        fail("invalid-arguments", "skill root must contain SKILL.md and references/reviewer-protocol.md")
    skill_bytes = read_bounded_bytes(skill_md, SKILL_DOCUMENT_LIMIT)
    protocol_bytes = read_bounded_bytes(protocol, SKILL_DOCUMENT_LIMIT)
    text = skill_bytes.decode("utf-8", errors="replace")
    if not text.startswith("---\n") or "\n---" not in text[4:]:
        fail("invalid-arguments", "SKILL.md frontmatter is unavailable")
    frontmatter = text[4 : text.index("\n---", 4)]
    match = _VERSION_LINE.search(frontmatter)
    if match is None:
        fail("invalid-arguments", "SKILL.md frontmatter does not declare metadata.version")
    return {"version": match.group(1), "sha256": sha256(skill_bytes + protocol_bytes)}


# ------------------------------------------------------------- validation

def _string(value: object, name: str, maximum: int, *, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str) or not value.strip() or len(value) > maximum or _CONTROL.search(value):
        fail("schema-invalid", f"{name} must be a non-empty single-line string of at most {maximum} characters")
    return value


def _enum(value: object, name: str, allowed: tuple[str, ...], *, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if value not in allowed:
        fail("schema-invalid", f"{name} must be one of {', '.join(allowed)}")
    return str(value)


def _integer(value: object, name: str, minimum: int, maximum: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum or value > maximum:
        fail("schema-invalid", f"{name} must be an integer between {minimum} and {maximum}")
    return int(value)


def _relative(value: object, name: str) -> str:
    if not safe_relative(value) or len(str(value)) > 500:
        fail("schema-invalid", f"{name} must be a safe repository-relative path")
    return str(value)


# --------------------------------------------------------------- commands

def cmd_start(args: argparse.Namespace, home: Path, cwd: Path) -> dict[str, object]:
    root = git_root(locator(cwd, args.repo))
    plan = repository_relative(root, args.plan, cwd)
    design = None if args.design is None else repository_relative(root, args.design, cwd)
    head, dirty = git_state(root)
    skill = skill_snapshot(locator(cwd, args.skill_root))
    model = _string(args.model, "model", 100)
    run_id = str(uuid.uuid4())
    record: dict[str, object] = {
        "schema": SCHEMA,
        "run_id": run_id,
        "status": "pending",
        "started_at": utc_now(),
        "completed_at": None,
        "elapsed_s": None,
        "skill": skill,
        "client": {"id": args.client, "model": model},
        "repo": root.name,
        "mode": args.mode,
        "plan": {"path": plan, "sha_start": document_hash(root, plan), "sha_end": None},
        "design": None if design is None else {"path": design, "sha_start": document_hash(root, design), "sha_end": None},
        "git": {"head_start": head, "head_end": None, "dirty_start": dirty, "dirty_end": None},
        "execution": None,
        "reviewers": None,
        "trigger": None,
        "degraded_reasons": [],
        "review_passes": None,
        "repair_passes": None,
        "verdict": None,
        "block_reason": None,
        "abandon_reason": None,
        "findings": [],
        "outcome": None,
    }
    write_record(run_path(home, run_id), record)
    return {"run_id": run_id, "status": "pending"}
```

Replace `build_parser` and the body of `main` after the `--version` handling with:

```python
def build_parser() -> _Parser:
    parser = _Parser(prog="evidence.py", add_help=True)
    commands = parser.add_subparsers(dest="command", required=True)
    start = commands.add_parser("start")
    start.add_argument("--skill-root", required=True)
    start.add_argument("--repo", required=True)
    start.add_argument("--plan", required=True)
    start.add_argument("--design")
    start.add_argument("--client", required=True, choices=CLIENTS)
    start.add_argument("--model", default="unknown")
    start.add_argument("--mode", required=True, choices=MODES)
    finish = commands.add_parser("finish")
    finish.add_argument("--run-id", required=True)
    finish.add_argument("--repo", required=True)
    abandon = commands.add_parser("abandon")
    abandon.add_argument("--run-id", required=True)
    abandon.add_argument("--reason", required=True, choices=ABANDON_REASONS)
    outcome = commands.add_parser("outcome")
    outcome.add_argument("--run-id", required=True)
    outcome.add_argument("--label", required=True, choices=OUTCOME_LABELS)
    outcome.add_argument("--note")
    show = commands.add_parser("show")
    show.add_argument("--run-id", required=True)
    summary = commands.add_parser("summary")
    summary.add_argument("--repo")
    summary.add_argument("--last", type=int)
    return parser
```

```python
        args = build_parser().parse_args(arguments)
        home = evidence_home(environ)
        if args.command == "start":
            result: object = cmd_start(args, home, cwd)
        else:
            fail("invalid-arguments", f"{args.command} is not implemented")
        stdout.write(canonical(result).decode("utf-8"))
        return 0
```

- [ ] **Step 4: Run to verify pass**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/pre-sdd-review/evidence -p 'test_evidence.py'`
Expected: `OK` (12 tests). Also run `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/pre-sdd-review -p 'test_contract.py'` — the AST contract test must still report `()` for `evidence/`.

- [ ] **Step 5: Commit**

```bash
git add skills/pre-sdd-review/evidence/evidence.py tests/products/pre-sdd-review/evidence
git commit -m "feat(pre-sdd-review): record pending runs with evidence.py start"
```

---

### Task 3: `finish` with invariants and end-state facts

**Files:**
- Modify: `skills/pre-sdd-review/evidence/evidence.py`
- Test: `tests/products/pre-sdd-review/evidence/test_evidence.py`

**Interfaces:**
- Produces: `validate_finding(item, repair_passes) -> dict`, `validate_finish(payload, mode) -> dict`, `cmd_finish(args, home, cwd, stdin) -> dict`.
- After `finish`, the record has `status = "completed"`, all end-state fields set, and the nine finish keys copied from the validated stdin object.

- [ ] **Step 1: Write failing tests**

Append to `test_evidence.py`:

```python
class FinishTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.workspace = Path(self.directory.name)
        self.home = self.workspace / "home"
        self.repo = make_git_repo(self.workspace)
        self.skill = make_skill_root(self.workspace)
        self.run_id = start(self.home, self.repo, self.skill)

    def tearDown(self) -> None:
        self.directory.cleanup()

    def test_finish_completes_the_record_with_end_state(self) -> None:
        write(self.repo / "docs/plan.md", "# Plan\n\n**Spec:** docs/design.md\n\nrepaired\n")
        commit_all(self.repo)
        payload = finish_payload(verdict="READY", review_passes=2, repair_passes=1, findings=[finding()])
        code, out, err = finish(self.home, self.repo, self.run_id, payload)
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out), {"run_id": self.run_id, "status": "completed", "verdict": "READY"})
        record = load(self.home, self.run_id)
        self.assertEqual(record["status"], "completed")
        self.assertEqual((record["execution"], record["reviewers"], record["verdict"]), ("full", 1, "READY"))
        self.assertEqual((record["review_passes"], record["repair_passes"]), (2, 1))
        self.assertEqual(record["findings"], [finding()])
        self.assertNotEqual(record["plan"]["sha_start"], record["plan"]["sha_end"])
        self.assertEqual(record["design"]["sha_start"], record["design"]["sha_end"])
        self.assertNotEqual(record["git"]["head_start"], record["git"]["head_end"])
        self.assertFalse(record["git"]["dirty_end"])
        self.assertIsInstance(record["elapsed_s"], int)
        self.assertRegex(record["completed_at"], r"Z$")

    def test_finish_rejects_each_invariant_violation(self) -> None:
        cases = {
            "ready-with-unresolved": finish_payload(findings=[finding(status="unresolved", repair_pass=None)]),
            "revise-without-unresolved": finish_payload(verdict="REVISE", repair_passes=1, findings=[finding()]),
            "blocked-without-reason": finish_payload(verdict="BLOCKED", execution="blocked", reviewers=0),
            "repair-without-repaired": finish_payload(repair_passes=1),
            "full-two-reviewers-no-trigger": finish_payload(reviewers=2),
            "full-one-reviewer-with-trigger": finish_payload(trigger="schema-migration"),
            "full-with-degraded-reason": finish_payload(degraded_reasons=["fresh-reviewer-unavailable"]),
            "degraded-without-reason": finish_payload(execution="degraded"),
            "duplicate-finding-id": finish_payload(repair_passes=1, findings=[finding(), finding(pattern="other")]),
            "repair-pass-exceeds": finish_payload(repair_passes=1, findings=[finding(repair_pass=2)]),
            "absolute-evidence-path": finish_payload(repair_passes=1, findings=[finding(evidence=["/etc/passwd"])]),
            "parent-location-path": finish_payload(repair_passes=1, findings=[finding(location={"path": "../x.md", "locator": "L1"})]),
            "long-consequence": finish_payload(repair_passes=1, findings=[finding(consequence="x" * 301)]),
            "bad-finding-id": finish_payload(repair_passes=1, findings=[finding(id="F-1")]),
            "unknown-key": {**finish_payload(), "token_usage": None},
            "missing-key": {key: value for key, value in finish_payload().items() if key != "findings"},
            "review-passes-zero": finish_payload(review_passes=0),
        }
        for name, payload in cases.items():
            with self.subTest(name=name):
                code, out, err = finish(self.home, self.repo, self.run_id, payload)
                self.assertEqual((code, out), (2, ""), name)
                self.assertEqual(error_code(err), "schema-invalid", name)
                self.assertEqual(load(self.home, self.run_id)["status"], "pending")

    def test_finish_accepts_blocked_degraded_and_triggered_full_runs(self) -> None:
        for payload in (
            finish_payload(verdict="BLOCKED", block_reason="spec-unresolved", execution="blocked", reviewers=0),
            finish_payload(verdict="REVISE", execution="degraded", degraded_reasons=["fresh-reviewer-unavailable"], findings=[finding(status="unresolved", repair_pass=None)]),
            finish_payload(reviewers=2, trigger="data-boundary"),
        ):
            with self.subTest(payload=payload["verdict"] + payload["execution"]):
                run_id = start(self.home, self.repo, self.skill)
                code, _, err = finish(self.home, self.repo, run_id, payload)
                self.assertEqual(code, 0, err)

    def test_review_only_rejects_repair_passes(self) -> None:
        run_id = start(self.home, self.repo, self.skill, mode="review-only")
        code, _, err = finish(self.home, self.repo, run_id, finish_payload(repair_passes=1, findings=[finding()]))
        self.assertEqual((code, error_code(err)), (2, "schema-invalid"))

    def test_finish_rejects_wrong_repository_and_second_finish(self) -> None:
        other = make_git_repo(self.workspace, name="other")
        code, _, err = finish(self.home, other, self.run_id, finish_payload())
        self.assertEqual((code, error_code(err)), (2, "outside-repository"))
        self.assertEqual(finish(self.home, self.repo, self.run_id, finish_payload())[0], 0)
        code, _, err = finish(self.home, self.repo, self.run_id, finish_payload())
        self.assertEqual((code, error_code(err)), (2, "already-finished"))

    def test_finish_rejects_unknown_run_and_invalid_json(self) -> None:
        code, _, err = finish(self.home, self.repo, "00000000-0000-4000-8000-000000000000", finish_payload())
        self.assertEqual((code, error_code(err)), (2, "run-not-found"))
        code, _, err = run(["finish", "--run-id", self.run_id, "--repo", str(self.repo)], home=self.home, cwd=self.repo, stdin_text="{not json")
        self.assertEqual((code, error_code(err)), (2, "schema-invalid"))

    def test_finish_rejects_records_over_the_size_limit(self) -> None:
        findings = [
            finding(id=f"PSDR-{index:03d}", pattern=f"pattern-{index}", consequence="c" * 300, fix="f" * 300)
            for index in range(1, 130)
        ]
        code, _, err = finish(self.home, self.repo, self.run_id, finish_payload(repair_passes=1, findings=findings))
        self.assertEqual((code, error_code(err)), (2, "schema-invalid"))
        self.assertEqual(load(self.home, self.run_id)["status"], "pending")
```

- [ ] **Step 2: Run to verify failure**

Run the evidence discovery command. Expected: `FinishTests` fail with `invalid-arguments` ("finish is not implemented").

- [ ] **Step 3: Implement validation and `finish`**

Insert before `cmd_start`:

```python
def validate_finding(item: object, repair_passes: int) -> dict[str, object]:
    if not isinstance(item, dict) or set(item) != FINDING_KEYS:
        fail("schema-invalid", "finding must contain exactly the finding keys")
    identifier = _string(item["id"], "finding.id", 20)
    if identifier is None or not _FINDING_ID.fullmatch(identifier):
        fail("schema-invalid", "finding.id must look like PSDR-001")
    _enum(item["severity"], "finding.severity", SEVERITIES)
    _enum(item["class"], "finding.class", CLASSES)
    pattern = _string(item["pattern"], "finding.pattern", 80)
    if pattern is None or not _PATTERN.fullmatch(pattern):
        fail("schema-invalid", "finding.pattern must be lowercase kebab, dot, or underscore tokens")
    _enum(item["status"], "finding.status", FINDING_STATUSES)
    repair_pass = item["repair_pass"]
    if repair_pass is not None:
        _integer(repair_pass, "finding.repair_pass", 1, 2)
        if repair_pass > repair_passes:
            fail("schema-invalid", "finding.repair_pass exceeds repair_passes")
    location = item["location"]
    if not isinstance(location, dict) or set(location) != {"path", "locator"}:
        fail("schema-invalid", "finding.location must contain path and locator")
    _relative(location["path"], "finding.location.path")
    _string(location["locator"], "finding.location.locator", 200)
    if not isinstance(item["evidence"], list):
        fail("schema-invalid", "finding.evidence must be a list")
    references: list[str] = []
    for reference in item["evidence"]:
        value = _relative(reference, "finding.evidence[]")
        if value not in references:
            references.append(value)
    _string(item["consequence"], "finding.consequence", 300)
    _string(item["fix"], "finding.fix", 300)
    normalized = dict(item)
    normalized["evidence"] = references
    return normalized


def validate_finish(payload: object, mode: str) -> dict[str, object]:
    if not isinstance(payload, dict) or set(payload) != FINISH_KEYS:
        fail("schema-invalid", "finish input must contain exactly the finish keys")
    execution = _enum(payload["execution"], "execution", EXECUTIONS)
    reviewers = _integer(payload["reviewers"], "reviewers", 0, 2)
    trigger = _enum(payload["trigger"], "trigger", TRIGGERS, nullable=True)
    if not isinstance(payload["degraded_reasons"], list):
        fail("schema-invalid", "degraded_reasons must be a list")
    reasons = [str(_string(item, "degraded_reasons[]", 100)) for item in payload["degraded_reasons"]]
    verdict = _enum(payload["verdict"], "verdict", VERDICTS)
    block_reason = _string(payload["block_reason"], "block_reason", 100, nullable=True)
    review_passes = _integer(payload["review_passes"], "review_passes", 1, 3)
    repair_passes = _integer(payload["repair_passes"], "repair_passes", 0, 2)
    if not isinstance(payload["findings"], list):
        fail("schema-invalid", "findings must be a list")
    findings = [validate_finding(item, repair_passes) for item in payload["findings"]]
    identifiers = [str(item["id"]) for item in findings]
    if len(set(identifiers)) != len(identifiers):
        fail("schema-invalid", "finding ids must be unique")
    statuses = [str(item["status"]) for item in findings]
    if verdict == "READY" and any(status != "repaired" for status in statuses):
        fail("schema-invalid", "READY permits only repaired findings")
    if verdict == "REVISE" and "unresolved" not in statuses:
        fail("schema-invalid", "REVISE requires an unresolved finding")
    if verdict == "BLOCKED" and block_reason is None:
        fail("schema-invalid", "BLOCKED requires block_reason")
    if repair_passes > 0 and "repaired" not in statuses:
        fail("schema-invalid", "repair_passes requires at least one repaired finding")
    if mode == "review-only" and repair_passes != 0:
        fail("schema-invalid", "review-only permits no repair pass")
    if execution == "full" and (reasons or reviewers != (2 if trigger is not None else 1)):
        fail("schema-invalid", "full execution requires one reviewer, or two with a trigger, and no degraded reasons")
    if execution == "degraded" and not reasons:
        fail("schema-invalid", "degraded execution requires degraded_reasons")
    return {
        "execution": execution,
        "reviewers": reviewers,
        "trigger": trigger,
        "degraded_reasons": reasons,
        "verdict": verdict,
        "block_reason": block_reason,
        "review_passes": review_passes,
        "repair_passes": repair_passes,
        "findings": findings,
    }
```

Insert after `cmd_start`:

```python
def _require_pending(home: Path, run_id: str) -> dict[str, object]:
    record = load_record(home, run_id)
    if record["status"] != "pending":
        fail("already-finished", "run is already finished")
    return record


def cmd_finish(args: argparse.Namespace, home: Path, cwd: Path, stdin: TextIO) -> dict[str, object]:
    record = _require_pending(home, args.run_id)
    root = git_root(locator(cwd, args.repo))
    if root.name != record["repo"]:
        fail("outside-repository", "repository does not match the recorded run")
    semantic = validate_finish(read_stdin(stdin, RECORD_LIMIT), str(record["mode"]))
    head, dirty = git_state(root)
    plan = record["plan"]
    design = record["design"]
    assert isinstance(plan, dict)
    plan["sha_end"] = document_hash(root, str(plan["path"]))
    if isinstance(design, dict):
        design["sha_end"] = document_hash(root, str(design["path"]))
    git_facts = record["git"]
    assert isinstance(git_facts, dict)
    git_facts["head_end"] = head
    git_facts["dirty_end"] = dirty
    completed_at = utc_now()
    record.update(semantic)
    record["status"] = "completed"
    record["completed_at"] = completed_at
    record["elapsed_s"] = elapsed_seconds(str(record["started_at"]), completed_at)
    write_record(run_path(home, args.run_id), record)
    return {"run_id": args.run_id, "status": "completed", "verdict": record["verdict"]}
```

In `main`, add the dispatch branch before the `else`:

```python
        elif args.command == "finish":
            result = cmd_finish(args, home, cwd, stdin)
```

- [ ] **Step 4: Run to verify pass**

Run the evidence discovery command. Expected: `OK`. Run the contract discovery command. Expected: `OK`.

- [ ] **Step 5: Commit**

```bash
git add skills/pre-sdd-review/evidence/evidence.py tests/products/pre-sdd-review/evidence/test_evidence.py
git commit -m "feat(pre-sdd-review): finish evidence runs with validated invariants"
```

---

### Task 4: `abandon`, `outcome`, and `show`

**Files:**
- Modify: `skills/pre-sdd-review/evidence/evidence.py`
- Test: `tests/products/pre-sdd-review/evidence/test_evidence.py`

**Interfaces:**
- Produces: `cmd_abandon(args, home) -> dict`, `cmd_outcome(args, home) -> dict`, `cmd_show(args, home) -> str`.

- [ ] **Step 1: Write failing tests**

Append to `test_evidence.py`:

```python
class AbandonOutcomeShowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.workspace = Path(self.directory.name)
        self.home = self.workspace / "home"
        self.repo = make_git_repo(self.workspace)
        self.skill = make_skill_root(self.workspace)
        self.run_id = start(self.home, self.repo, self.skill)

    def tearDown(self) -> None:
        self.directory.cleanup()

    def test_abandon_closes_a_pending_run_with_each_reason(self) -> None:
        for reason in ("user-cancelled", "input-changed", "scope-changed", "input-format-fixed", "other"):
            with self.subTest(reason=reason):
                run_id = start(self.home, self.repo, self.skill)
                code, out, err = run(["abandon", "--run-id", run_id, "--reason", reason], home=self.home, cwd=self.repo)
                self.assertEqual(code, 0, err)
                self.assertEqual(json.loads(out), {"run_id": run_id, "status": "abandoned"})
                record = load(self.home, run_id)
                self.assertEqual((record["status"], record["abandon_reason"]), ("abandoned", reason))
                self.assertIsInstance(record["elapsed_s"], int)
                self.assertIsNone(record["verdict"])

    def test_abandon_rejects_invalid_reason_and_finished_runs(self) -> None:
        code, _, err = run(["abandon", "--run-id", self.run_id, "--reason", "bored"], home=self.home, cwd=self.repo)
        self.assertEqual((code, error_code(err)), (2, "invalid-arguments"))
        self.assertEqual(finish(self.home, self.repo, self.run_id, finish_payload())[0], 0)
        code, _, err = run(["abandon", "--run-id", self.run_id, "--reason", "other"], home=self.home, cwd=self.repo)
        self.assertEqual((code, error_code(err)), (2, "already-finished"))

    def test_outcome_records_and_overwrites_a_label(self) -> None:
        self.assertEqual(finish(self.home, self.repo, self.run_id, finish_payload())[0], 0)
        code, out, err = run(["outcome", "--run-id", self.run_id, "--label", "good", "--note", "SDD completed"], home=self.home, cwd=self.repo)
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out), {"run_id": self.run_id, "outcome": "good"})
        first = load(self.home, self.run_id)["outcome"]
        self.assertEqual((first["label"], first["note"]), ("good", "SDD completed"))
        code, _, err = run(["outcome", "--run-id", self.run_id, "--label", "false-ready"], home=self.home, cwd=self.repo)
        self.assertEqual(code, 0, err)
        second = load(self.home, self.run_id)["outcome"]
        self.assertEqual((second["label"], second["note"]), ("false-ready", None))

    def test_outcome_rejects_pending_runs_false_ready_without_ready_and_long_notes(self) -> None:
        code, _, err = run(["outcome", "--run-id", self.run_id, "--label", "good"], home=self.home, cwd=self.repo)
        self.assertEqual((code, error_code(err)), (2, "schema-invalid"))
        revise = finish_payload(verdict="REVISE", findings=[finding(status="unresolved", repair_pass=None)])
        self.assertEqual(finish(self.home, self.repo, self.run_id, revise)[0], 0)
        code, _, err = run(["outcome", "--run-id", self.run_id, "--label", "false-ready"], home=self.home, cwd=self.repo)
        self.assertEqual((code, error_code(err)), (2, "schema-invalid"))
        code, _, err = run(["outcome", "--run-id", self.run_id, "--label", "noisy", "--note", "n" * 301], home=self.home, cwd=self.repo)
        self.assertEqual((code, error_code(err)), (2, "schema-invalid"))

    def test_show_prints_the_record_verbatim(self) -> None:
        code, out, err = run(["show", "--run-id", self.run_id], home=self.home, cwd=self.repo)
        self.assertEqual(code, 0, err)
        self.assertEqual(out, (self.home / "runs" / f"{self.run_id}.json").read_text(encoding="utf-8"))
        code, _, err = run(["show", "--run-id", "00000000-0000-4000-8000-000000000000"], home=self.home, cwd=self.repo)
        self.assertEqual((code, error_code(err)), (2, "run-not-found"))
        code, _, err = run(["show", "--run-id", "not-a-uuid"], home=self.home, cwd=self.repo)
        self.assertEqual((code, error_code(err)), (2, "invalid-arguments"))
```

- [ ] **Step 2: Run to verify failure**

Run the evidence discovery command. Expected: the new class fails with `invalid-arguments` ("... is not implemented").

- [ ] **Step 3: Implement the three commands**

Insert after `cmd_finish`:

```python
def cmd_abandon(args: argparse.Namespace, home: Path) -> dict[str, object]:
    record = _require_pending(home, args.run_id)
    completed_at = utc_now()
    record["status"] = "abandoned"
    record["abandon_reason"] = args.reason
    record["completed_at"] = completed_at
    record["elapsed_s"] = elapsed_seconds(str(record["started_at"]), completed_at)
    write_record(run_path(home, args.run_id), record)
    return {"run_id": args.run_id, "status": "abandoned"}


def cmd_outcome(args: argparse.Namespace, home: Path) -> dict[str, object]:
    record = load_record(home, args.run_id)
    if record["status"] != "completed":
        fail("schema-invalid", "outcome requires a completed run")
    if args.label == "false-ready" and record["verdict"] != "READY":
        fail("schema-invalid", "false-ready requires a READY verdict")
    note = _string(args.note, "note", 300, nullable=True)
    record["outcome"] = {"label": args.label, "note": note, "recorded_at": utc_now()}
    write_record(run_path(home, args.run_id), record)
    return {"run_id": args.run_id, "outcome": args.label}


def cmd_show(args: argparse.Namespace, home: Path) -> str:
    load_record(home, args.run_id)
    return read_bounded_bytes(run_path(home, args.run_id), RECORD_LIMIT).decode("utf-8")
```

In `main`, add branches:

```python
        elif args.command == "abandon":
            result = cmd_abandon(args, home)
        elif args.command == "outcome":
            result = cmd_outcome(args, home)
        elif args.command == "show":
            stdout.write(cmd_show(args, home))
            return 0
```

- [ ] **Step 4: Run to verify pass**

Run the evidence discovery command. Expected: `OK`.

- [ ] **Step 5: Commit**

```bash
git add skills/pre-sdd-review/evidence/evidence.py tests/products/pre-sdd-review/evidence/test_evidence.py
git commit -m "feat(pre-sdd-review): add abandon, outcome, and show to evidence.py"
```

---

### Task 5: `summary` as agent-readable JSON

**Files:**
- Modify: `skills/pre-sdd-review/evidence/evidence.py`
- Test: `tests/products/pre-sdd-review/evidence/test_evidence.py`

**Interfaces:**
- Produces: `summarize(records) -> dict` with exactly the keys `schema`, `runs`, `counts`, `cost`, `chains`, `findings`, `anomalies` as specified in the design (Decision 6); `cmd_summary(args, home) -> dict`.

- [ ] **Step 1: Write failing tests**

Append to `test_evidence.py` (also add `import evidence` after the `support` import — `support` already put the evidence directory on `sys.path`):

```python
class SummaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.workspace = Path(self.directory.name)
        self.home = self.workspace / "home"
        self.repo = make_git_repo(self.workspace)
        self.other = make_git_repo(self.workspace, name="other")
        self.skill = make_skill_root(self.workspace)

    def tearDown(self) -> None:
        self.directory.cleanup()

    def _summary(self, *extra: str) -> dict:
        code, out, err = run(["summary", *extra], home=self.home, cwd=self.repo)
        self.assertEqual(code, 0, err)
        return json.loads(out)

    def _mutate(self, run_id: str, **changes: object) -> None:
        record = load(self.home, run_id)
        record.update(changes)
        evidence.write_record(self.home / "runs" / f"{run_id}.json", record)

    def test_summary_on_empty_home_has_exact_keys(self) -> None:
        summary = self._summary()
        self.assertEqual(set(summary), {"schema", "runs", "counts", "cost", "chains", "findings", "anomalies"})
        self.assertEqual(summary["runs"], [])
        self.assertEqual(summary["counts"]["status"], {"completed": 0, "abandoned": 0, "pending": 0})
        self.assertEqual(summary["counts"]["verdict"], {"READY": 0, "REVISE": 0, "BLOCKED": 0})
        self.assertEqual(summary["counts"]["outcome"], {"recorded": 0, "good": 0, "false-ready": 0, "noisy": 0, "abandoned": 0})
        self.assertEqual(summary["cost"], {"elapsed_s": {"median": None, "max": None}, "review_passes_avg": None, "repair_passes_avg": None})
        self.assertEqual(summary["anomalies"], {
            "repair_without_repaired_finding": [],
            "head_changed_during_review": [],
            "design_unresolved_but_full_execution": [],
            "repo_reality_citing_documents_only": [],
        })
        self.assertFalse(self.home.exists())

    def test_summary_aggregates_chains_patterns_outcomes_and_anomalies(self) -> None:
        repo_reality = finding(id="PSDR-001", **{"class": "repo-reality"}, pattern="demo-npm-cwd", status="unresolved", repair_pass=None, evidence=["docs/plan.md"])
        first = start(self.home, self.repo, self.skill)
        self.assertEqual(finish(self.home, self.repo, first, finish_payload(verdict="REVISE", review_passes=2, findings=[repo_reality]))[0], 0)
        second = start(self.home, self.repo, self.skill)
        write(self.repo / "docs/plan.md", "# Plan\n\n**Spec:** docs/design.md\n\nfixed\n")
        commit_all(self.repo)
        repaired = finding(id="PSDR-002", **{"class": "repo-reality"}, pattern="demo-npm-cwd", evidence=["src/app.ts"])
        self.assertEqual(finish(self.home, self.repo, second, finish_payload(verdict="READY", review_passes=2, repair_passes=1, findings=[repaired]))[0], 0)
        self.assertEqual(run(["outcome", "--run-id", second, "--label", "good"], home=self.home, cwd=self.repo)[0], 0)
        abandoned = start(self.home, self.repo, self.skill)
        self.assertEqual(run(["abandon", "--run-id", abandoned, "--reason", "input-changed"], home=self.home, cwd=self.repo)[0], 0)
        pending = start(self.home, self.other, self.skill)
        unresolved_design = start(self.home, self.other, self.skill, design=False)
        self.assertEqual(finish(self.home, self.other, unresolved_design, finish_payload())[0], 0)
        self._mutate(unresolved_design, repair_passes=1, findings=[])
        legacy = self.home / "runs" / "2026" / "09" / "abc" / "review.json"
        legacy.parent.mkdir(parents=True)
        legacy.write_text('{"schema_version":1}\n', encoding="utf-8")
        (self.home / "runs" / "garbage.json").write_text("{not json", encoding="utf-8")
        (self.home / "runs" / "old.json").write_text('{"schema":1,"run_id":"x"}\n', encoding="utf-8")

        summary = self._summary()
        self.assertEqual([item["run_id"] for item in summary["runs"]], [first, second, abandoned, pending, unresolved_design])
        self.assertEqual(set(summary["runs"][0]), {"run_id", "started_at", "repo", "plan", "status", "verdict", "findings", "elapsed_s"})
        self.assertEqual(summary["counts"]["status"], {"completed": 3, "abandoned": 1, "pending": 1})
        self.assertEqual(summary["counts"]["verdict"], {"READY": 2, "REVISE": 1, "BLOCKED": 0})
        self.assertEqual(summary["counts"]["execution"], {"full": 3, "degraded": 0, "blocked": 0})
        self.assertEqual(summary["counts"]["abandon_reason"], {"input-changed": 1})
        self.assertEqual(summary["counts"]["outcome"], {"recorded": 1, "good": 1, "false-ready": 0, "noisy": 0, "abandoned": 0})
        self.assertEqual(summary["cost"]["review_passes_avg"], round((2 + 2 + 1) / 3, 1))
        self.assertEqual(summary["cost"]["repair_passes_avg"], round((0 + 1 + 1) / 3, 1))
        self.assertIsInstance(summary["cost"]["elapsed_s"]["median"], int)
        self.assertEqual(len(summary["chains"]), 2)
        repo_chain = next(chain for chain in summary["chains"] if chain["repo"] == "repo")
        self.assertEqual(repo_chain["plan"], "docs/plan.md")
        self.assertEqual(
            repo_chain["runs"],
            [
                {"run_id": first, "status": "completed", "verdict": "REVISE"},
                {"run_id": second, "status": "completed", "verdict": "READY"},
                {"run_id": abandoned, "status": "abandoned", "verdict": None},
            ],
        )
        self.assertEqual(summary["findings"]["total"], 2)
        self.assertEqual(summary["findings"]["by_severity"], {"IMPORTANT": 2})
        self.assertEqual(summary["findings"]["by_status"], {"unresolved": 1, "repaired": 1})
        self.assertEqual(summary["findings"]["by_class"], {"repo-reality": 2})
        self.assertEqual(
            summary["findings"]["repeated_patterns"],
            [{"class": "repo-reality", "pattern": "demo-npm-cwd", "count": 2, "run_ids": [first, second]}],
        )
        self.assertEqual(summary["anomalies"]["repair_without_repaired_finding"], [unresolved_design])
        self.assertEqual(summary["anomalies"]["head_changed_during_review"], [second])
        self.assertEqual(summary["anomalies"]["design_unresolved_but_full_execution"], [unresolved_design])
        self.assertEqual(summary["anomalies"]["repo_reality_citing_documents_only"], [{"run_id": first, "finding_id": "PSDR-001"}])

    def test_summary_filters_by_repo_and_last(self) -> None:
        first = start(self.home, self.repo, self.skill)
        self.assertEqual(finish(self.home, self.repo, first, finish_payload())[0], 0)
        second = start(self.home, self.other, self.skill)
        self.assertEqual(finish(self.home, self.other, second, finish_payload())[0], 0)
        third = start(self.home, self.other, self.skill)
        self.assertEqual([item["run_id"] for item in self._summary("--repo", "other")["runs"]], [second, third])
        self.assertEqual([item["run_id"] for item in self._summary("--last", "1")["runs"]], [third])
        self.assertEqual(self._summary("--last", "1")["counts"]["status"], {"completed": 0, "abandoned": 0, "pending": 1})
        code, _, err = run(["summary", "--last", "0"], home=self.home, cwd=self.repo)
        self.assertEqual((code, error_code(err)), (2, "invalid-arguments"))
```

- [ ] **Step 2: Run to verify failure**

Run the evidence discovery command. Expected: `SummaryTests` fail with `invalid-arguments`.

- [ ] **Step 3: Implement `summarize` and `cmd_summary`**

Insert after `cmd_show`:

```python
def _count(values: list[str], keys: tuple[str, ...] | None = None) -> dict[str, int]:
    counts: dict[str, int] = {key: 0 for key in keys} if keys else {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return counts


def summarize(records: list[dict[str, object]]) -> dict[str, object]:
    completed = [record for record in records if record["status"] == "completed"]
    runs_index: list[dict[str, object]] = []
    chains: dict[tuple[str, str], list[dict[str, object]]] = {}
    pattern_runs: dict[tuple[str, str], list[str]] = {}
    severities: list[str] = []
    statuses: list[str] = []
    classes: list[str] = []
    anomalies: dict[str, list[object]] = {
        "repair_without_repaired_finding": [],
        "head_changed_during_review": [],
        "design_unresolved_but_full_execution": [],
        "repo_reality_citing_documents_only": [],
    }
    for record in records:
        run_id = str(record["run_id"])
        plan = record["plan"]
        design = record["design"]
        assert isinstance(plan, dict)
        findings = record["findings"]
        assert isinstance(findings, list)
        runs_index.append({
            "run_id": run_id,
            "started_at": record["started_at"],
            "repo": record["repo"],
            "plan": plan["path"],
            "status": record["status"],
            "verdict": record["verdict"],
            "findings": len(findings),
            "elapsed_s": record["elapsed_s"],
        })
        chains.setdefault((str(record["repo"]), str(plan["path"])), []).append(
            {"run_id": run_id, "status": record["status"], "verdict": record["verdict"]}
        )
        if record["status"] != "completed":
            continue
        documents = {str(plan["path"])}
        if isinstance(design, dict):
            documents.add(str(design["path"]))
        for item in findings:
            assert isinstance(item, dict)
            severities.append(str(item["severity"]))
            statuses.append(str(item["status"]))
            classes.append(str(item["class"]))
            key = (str(item["class"]), str(item["pattern"]))
            runs_for_pattern = pattern_runs.setdefault(key, [])
            if run_id not in runs_for_pattern:
                runs_for_pattern.append(run_id)
            if item["class"] == "repo-reality" and set(item["evidence"]) <= documents:
                anomalies["repo_reality_citing_documents_only"].append({"run_id": run_id, "finding_id": item["id"]})
        if record["repair_passes"] and not any(item["status"] == "repaired" for item in findings):
            anomalies["repair_without_repaired_finding"].append(run_id)
        git_facts = record["git"]
        assert isinstance(git_facts, dict)
        if git_facts["head_start"] != git_facts["head_end"]:
            anomalies["head_changed_during_review"].append(run_id)
        if design is None and record["execution"] == "full":
            anomalies["design_unresolved_but_full_execution"].append(run_id)
    elapsed = [int(record["elapsed_s"]) for record in completed if isinstance(record["elapsed_s"], int)]
    outcomes = [record["outcome"] for record in completed if isinstance(record["outcome"], dict)]
    outcome_counts = {"recorded": len(outcomes)}
    outcome_counts.update(_count([str(item["label"]) for item in outcomes], OUTCOME_LABELS))
    return {
        "schema": SCHEMA,
        "runs": runs_index,
        "counts": {
            "status": _count([str(record["status"]) for record in records], ("completed", "abandoned", "pending")),
            "verdict": _count([str(record["verdict"]) for record in completed], VERDICTS),
            "execution": _count([str(record["execution"]) for record in completed], EXECUTIONS),
            "abandon_reason": _count([str(record["abandon_reason"]) for record in records if record["status"] == "abandoned"]),
            "outcome": outcome_counts,
        },
        "cost": {
            "elapsed_s": {
                "median": int(statistics.median(elapsed)) if elapsed else None,
                "max": max(elapsed) if elapsed else None,
            },
            "review_passes_avg": round(statistics.mean(int(record["review_passes"]) for record in completed), 1) if completed else None,
            "repair_passes_avg": round(statistics.mean(int(record["repair_passes"]) for record in completed), 1) if completed else None,
        },
        "chains": [
            {"repo": repo, "plan": plan_path, "runs": runs}
            for (repo, plan_path), runs in chains.items()
            if len(runs) >= 2
        ],
        "findings": {
            "total": len(severities),
            "by_severity": _count(severities),
            "by_status": _count(statuses),
            "by_class": _count(classes),
            "repeated_patterns": [
                {"class": key[0], "pattern": key[1], "count": len(run_ids), "run_ids": run_ids}
                for key, run_ids in sorted(pattern_runs.items())
                if len(run_ids) >= 2
            ],
        },
        "anomalies": anomalies,
    }


def cmd_summary(args: argparse.Namespace, home: Path) -> dict[str, object]:
    if args.last is not None and args.last < 1:
        fail("invalid-arguments", "--last must be a positive integer")
    records = iter_records(home)
    if args.repo is not None:
        records = [record for record in records if record["repo"] == args.repo]
    if args.last is not None:
        records = records[-args.last :]
    return summarize(records)
```

In `main`, add:

```python
        elif args.command == "summary":
            result = cmd_summary(args, home)
```

and delete the `else: fail("invalid-arguments", ...)` branch (argparse already rejects unknown commands).

- [ ] **Step 4: Run to verify pass**

Run the evidence discovery command. Expected: `OK`. Run `wc -l skills/pre-sdd-review/evidence/evidence.py` — must be under 600. Run the contract discovery command — `OK`.

- [ ] **Step 5: Commit**

```bash
git add skills/pre-sdd-review/evidence/evidence.py tests/products/pre-sdd-review/evidence/test_evidence.py
git commit -m "feat(pre-sdd-review): add agent-readable summary to evidence.py"
```

---

### Task 6: SKILL.md evidence section, reviewer-protocol sentence, cases, and contract pins

**Files:**
- Modify: `skills/pre-sdd-review/SKILL.md` (only `## Optional local evidence`)
- Modify: `skills/pre-sdd-review/references/reviewer-protocol.md` (Pass 2)
- Modify: `tests/products/pre-sdd-review/cases.json` (cases 15–19)
- Modify: `tests/products/pre-sdd-review/test_contract.py` (`INSTRUCTION_DOCUMENT_SHA256`, `CASE_IDS`, `test_optional_evidence_lifecycle_is_ordered_and_non_blocking`, `test_evidence_cases_cover_recorded_failure_review_only_blocked_and_handoff`, `test_evidence_guidance_stays_out_of_reviewer_protocol_and_mutation_authority`, new protocol test)

- [ ] **Step 1: Update the contract tests first (they will fail until the documents change)**

In `CASE_IDS`, replace `"evidence-combined-sdd-outcome"` with `"evidence-outcome-optional"`.

Replace the body of `test_optional_evidence_lifecycle_is_ordered_and_non_blocking` with:

```python
        body = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        evidence = section(body, "## Optional local evidence", "## Select reviewers")
        normalized = re.sub(r"\s+", " ", evidence)

        ordered = ("evidence.py\" --version", "start", "semantic review", "finish", "Evidence:", "abandon", "outcome")
        positions = tuple(normalized.index(item) for item in ordered)
        self.assertEqual(positions, tuple(sorted(positions)))
        for fact in (
            "without installing anything",
            "skill_name=pre-sdd-review",
            "schema=2",
            "actual loaded skill root",
            "primary plan",
            "does not parse `**Spec:**`",
            "controller-local",
            "default and `review-only` mode",
            "current repository locator",
            "exactly one `Evidence:` line",
            "never changes the semantic verdict",
            "never leave a run pending",
            "not a controller duty",
            "full reviewer response",
            "source body",
        ):
            self.assertIn(fact, normalized)
        self.assertIn("Evidence: recorded; run_id=<run-id>", evidence)
        self.assertIn("Evidence: not_recorded; reason=<code>", evidence)
        self.assertNotIn("pre-sdd-review-evidence", body)
        self.assertNotIn("record-outcome", body)
        self.assertNotIn("finish-review", body)
        self.assertRegex(
            normalized,
            re.compile(r"unavailable, malformed, incompatible, or permission.*continue.*review", re.IGNORECASE),
        )
```

Replace the body of `test_evidence_cases_cover_recorded_failure_review_only_blocked_and_handoff` with:

```python
        data = json.loads(CASES.read_text(encoding="utf-8"))
        cases = {case["id"]: tuple(case["expect"]) for case in data["cases"]}
        self.assertEqual(cases["evidence-cli-recorded"], ("start_before_review", "finish_after_verdict", "Evidence_recorded"))
        self.assertEqual(cases["evidence-cli-unavailable"], ("continue_review", "Evidence_not_recorded"))
        self.assertEqual(cases["evidence-review-only"], ("review_only_receipt", "no_document_mutation"))
        self.assertEqual(cases["evidence-resolution-blocked"], ("BLOCKED", "design_omitted_from_start", "design_recorded_null"))
        self.assertEqual(cases["evidence-outcome-optional"], ("verdict_unchanged", "outcome_not_controller_duty", "one_label_after_sdd"))
```

In `test_evidence_guidance_stays_out_of_reviewer_protocol_and_mutation_authority`, replace `self.assertNotIn("pre-sdd-review-evidence", protocol)` with:

```python
        self.assertNotIn("evidence.py", protocol)
        self.assertNotIn("pre-sdd-review-evidence", protocol)
```

and `self.assertNotIn("pre-sdd-review-evidence", repair_rules)` with `self.assertNotIn("evidence.py", repair_rules)`.

Add after `test_protocol_falsification_keeps_evidence_classes_distinct`:

```python
    def test_protocol_requires_repository_evidence_for_repo_reality(self) -> None:
        protocol = (SKILL / "references/reviewer-protocol.md").read_text(encoding="utf-8")
        grounding = section(protocol, "### Pass 2: repository grounding", "### Pass 3: cross-artifact consistency")
        self.assertIn(
            "A `repo-reality` finding must cite at least one repository path that is neither the reviewed design nor the reviewed plan.",
            re.sub(r"\s+", " ", grounding),
        )
```

- [ ] **Step 2: Run the contract tests to verify failure**

Run the contract discovery command. Expected: the four touched tests fail (missing facts, old case id, protocol sentence absent).

- [ ] **Step 3: Rewrite the SKILL.md evidence section**

Replace everything from `## Optional local evidence` up to (not including) `## Select reviewers` with:

```markdown
## Optional local evidence

Run `python3 "<skill-root>/evidence/evidence.py" --version` from the actual
loaded skill root without installing anything. Parse its canonical JSON and
record only when `skill_name=pre-sdd-review` and `schema=2`. When compatible,
call `start` before semantic review with the skill root, the repository, the
primary plan, the design path resolved from the plan's `**Spec:**` field, the
host client id, the host-reported model string (or `unknown`), and the mode.
If `**Spec:**` cannot be resolved, omit `--design` and return `BLOCKED`; the
recorder does not parse `**Spec:**`. Keep the returned `run_id`
controller-local and out of user documents. The same lifecycle applies to
default and `review-only` mode.

After the verdict and any repairs are final, call `finish` once with the
current repository locator and the review facts on stdin, then print exactly
one `Evidence:` line: `Evidence: recorded; run_id=<run-id>` or
`Evidence: not_recorded; reason=<code>`. An unavailable, malformed,
incompatible, or permission-failing recorder must continue the review and
never changes the semantic verdict. If the invocation ends before `finish`,
call `abandon` with one of `user-cancelled`, `input-changed`, `scope-changed`,
`input-format-fixed`, or `other`; never leave a run pending.

Recording an `outcome` is not a controller duty. After SDD or implementation
ends, the user or the SDD worker may record one label (`good`, `false-ready`,
`noisy`, `abandoned`) for the run. Never store a full reviewer response or
source body in evidence; use bounded paraphrases only.

```

- [ ] **Step 4: Add the reviewer-protocol sentence**

In `references/reviewer-protocol.md`, under `### Pass 2: repository grounding`, append to the paragraph so it ends:

```markdown
...Preserve and
report pre-existing dirty state when it makes a claim unresolvable. A
`repo-reality` finding must cite at least one repository path that is neither
the reviewed design nor the reviewed plan.
```

- [ ] **Step 5: Update `cases.json`**

Replace cases 15–19 (`evidence-cli-recorded` … `evidence-combined-sdd-outcome`) with:

```json
    {
      "id": "evidence-cli-recorded",
      "request": "$pre-sdd-review sample-app/design.md sample-app/plan.md with a compatible local evidence recorder",
      "expect": ["start_before_review", "finish_after_verdict", "Evidence_recorded"]
    },
    {
      "id": "evidence-cli-unavailable",
      "request": "$pre-sdd-review sample-app/design.md sample-app/plan.md without a compatible local evidence recorder",
      "expect": ["continue_review", "Evidence_not_recorded"]
    },
    {
      "id": "evidence-review-only",
      "request": "$pre-sdd-review review-only sample-app/design.md sample-app/plan.md with a compatible local evidence recorder",
      "expect": ["review_only_receipt", "no_document_mutation"]
    },
    {
      "id": "evidence-resolution-blocked",
      "request": "$pre-sdd-review sample-app/plan-without-spec.md with a compatible local evidence recorder",
      "expect": ["BLOCKED", "design_omitted_from_start", "design_recorded_null"]
    },
    {
      "id": "evidence-outcome-optional",
      "request": "$pre-sdd-review sample-app/design.md sample-app/plan.md and implement it with SDD",
      "expect": ["verdict_unchanged", "outcome_not_controller_duty", "one_label_after_sdd"]
    },
```

(Keep the file's existing indentation and key order `id`, `request`, `expect`.)

- [ ] **Step 6: Recompute the instruction digests**

Run the digest helper from the File Structure section and paste the two `INSTRUCTION` values into `INSTRUCTION_DOCUMENT_SHA256` in `test_contract.py`.

- [ ] **Step 7: Run the contract tests to verify pass**

Run the contract discovery command. Expected: `OK`, except `test_maintainer_testing_compatibility_and_release_stay_role_specific` and `testing_document_errors` ("case inventory differs") which now fail because `docs/maintainers/products/pre-sdd-review/testing.md` still lists `evidence-combined-sdd-outcome`. Fix that now: in `testing.md` `### Case inventory`, replace `- \`evidence-combined-sdd-outcome\`` with `- \`evidence-outcome-optional\``, rerun the digest helper, and paste the new `TESTING_CANONICAL_DIGEST`. Rerun the contract discovery command. Expected: `OK`.

- [ ] **Step 8: Commit**

```bash
git add skills/pre-sdd-review/SKILL.md skills/pre-sdd-review/references/reviewer-protocol.md tests/products/pre-sdd-review docs/maintainers/products/pre-sdd-review/testing.md
git commit -m "docs(pre-sdd-review): controller contract for evidence.py and repo-reality evidence rule"
```

---

### Task 7: Version 2.0.0 — release.toml, SKILL frontmatter, CHANGELOG, skill READMEs, evidence README

**Files:**
- Modify: `skills/pre-sdd-review/release.toml`, `SKILL.md` frontmatter, `CHANGELOG.md`, `README.md`, `README.en.md`
- Rewrite: `skills/pre-sdd-review/evidence/README.md`
- Modify: `tests/products/pre-sdd-review/test_contract.py` (`TARGET_VERSION`, `KOREAN_FACTS`, `ENGLISH_FACTS`, `INSTRUCTION_DOCUMENT_SHA256`, `README_CANONICAL_*`, `test_release_sources_target_v1_3_1`, `test_v1_2_docs_*`)
- Modify: `tests/repository/test_release_contract.py:52-56`, `tests/repository/test_release.py` (archive name)

- [ ] **Step 1: Update tests first**

In `test_contract.py`:
- `TARGET_VERSION = "2.0.0"`.
- In `KOREAN_FACTS` and `ENGLISH_FACTS`, replace `"pre-sdd-review-evidence"` with `"evidence.py"`.
- Rename `test_release_sources_target_v1_3_1` to `test_release_sources_target_v2_0_0` and change the changelog heading assertion to `f"## {TARGET_VERSION} - 2026-09-05"`.
- Replace `test_v1_2_docs_keep_evidence_local_bounded_non_audit_and_non_mutating` and `test_v1_2_docs_distinguish_label_derivation_from_observer_uncertainty` with:

```python
    def test_v2_docs_keep_evidence_local_bounded_optional_and_agent_readable(self) -> None:
        documents = (
            (SKILL / "README.md").read_text(encoding="utf-8"),
            (SKILL / "README.en.md").read_text(encoding="utf-8"),
            (SKILL / "evidence/README.md").read_text(encoding="utf-8"),
            (MAINTAINERS / "contract.md").read_text(encoding="utf-8"),
        )
        normalized = tuple(re.sub(r"\s+", " ", text) for text in documents)
        for text in normalized:
            self.assertIn("evidence.py", text)
            self.assertIn("~/.pre-sdd-review/", text)
            self.assertIn("audit log", text)
            self.assertIn("`summary`", text)
            self.assertIn("`outcome`", text)
            self.assertNotIn("pre-sdd-review-evidence", text.replace("`pre-sdd-review-evidence` launcher", ""))
            self.assertNotIn("record-outcome", text)
            self.assertNotIn("install.py", text)
            self.assertNotIn("--bin-dir", text)
        combined = " ".join(normalized)
        for phrase in (
            "`good`, `false-ready`, `noisy`, `abandoned`",
            "anomalies",
            "chains",
            "run_id",
            "source text",
            "prompts",
            "transcripts",
            "credentials",
            "schema 2",
        ):
            self.assertIn(phrase, combined)
```

In `tests/repository/test_release_contract.py` lines 52–56, change `"1.3.1"` to `"2.0.0"`, `"pre-sdd-review-v1.3.1"` to `"pre-sdd-review-v2.0.0"`, and `"pre-sdd-review-v1.3.1.zip"` to `"pre-sdd-review-v2.0.0.zip"`. In `tests/repository/test_release.py`, replace every `pre-sdd-review-v1.3.1` with `pre-sdd-review-v2.0.0`:

```bash
sed -i '' 's/pre-sdd-review-v1\.3\.1/pre-sdd-review-v2.0.0/g' tests/repository/test_release.py
```

- [ ] **Step 2: Run to verify failure**

Run the contract and repository discovery commands. Expected: version, changelog, README fact, and v2 docs tests fail.

- [ ] **Step 3: Bump version sources**

`skills/pre-sdd-review/release.toml`: `version = "2.0.0"`. `SKILL.md` frontmatter: `version: "2.0.0"`, `updated_at: "2026-09-05"`.

Insert into `CHANGELOG.md` directly under `## Unreleased` (leave that heading in place):

```markdown
## 2.0.0 - 2026-09-05

### Changed

- The evidence recorder is one standard-library script,
  `evidence/evidence.py`, run with `python3` from the loaded skill root. The
  `pre-sdd-review-evidence` launcher, installer, and package are removed.
- Records use schema 2: one file per run under `~/.pre-sdd-review/runs/`,
  and six commands `start`, `finish`, `abandon`, `outcome`, `show`, `summary`.
  Schema 1 receipts are not read.
- The controller passes the design path it resolved from `**Spec:**`; the
  recorder no longer parses that field. An unresolved design is recorded as
  null with a `BLOCKED` verdict.
- `finish` rejects a repair pass without a repaired finding. `summary` is
  agent-readable JSON with verdict counts, abandon reasons, per-plan chains,
  repeated finding patterns, outcome coverage, and anomalies, each carrying
  run IDs.
- `outcome` records one label (`good`, `false-ready`, `noisy`, `abandoned`)
  and an optional note, and may be re-recorded.
- Reviewer protocol: a `repo-reality` finding must cite a repository path
  other than the reviewed design or plan.

```

- [ ] **Step 4: Rewrite the evidence README**

Replace `skills/pre-sdd-review/evidence/README.md` with:

````markdown
# Pre-SDD review evidence recorder

`evidence.py` is the optional local recorder for `pre-sdd-review`. It needs
Python 3.11+ and the standard library only, makes no model, provider, or
network call, and is never installed: run it from the skill root.

```sh
python3 "<skill-root>/evidence/evidence.py" --version
```

## Data

Each run is one file, `~/.pre-sdd-review/runs/<run-id>.json`. The only
override for the root is a non-empty absolute `PRE_SDD_REVIEW_HOME`. Records
are schema 2 and at most 64 KiB; anything else under the root, including
schema 1 receipts, is ignored and never written.

## Commands

| Command | Arguments | Effect |
| --- | --- | --- |
| `--version` | none | Print `{"cli_version":"2.0.0","schema":2,"skill_name":"pre-sdd-review"}` |
| `start` | `--skill-root --repo --plan [--design] --client --model --mode` | Hash the documents, read Git state, write a `pending` record, print `run_id` |
| `finish` | `--run-id --repo` and one JSON object on stdin | Recompute end hashes and Git state, validate, write `completed` |
| `abandon` | `--run-id --reason` | Close a pending run; reason is `user-cancelled`, `input-changed`, `scope-changed`, `input-format-fixed`, or `other` |
| `outcome` | `--run-id --label [--note]` | Record `good`, `false-ready`, `noisy`, or `abandoned` on a completed run; may be re-recorded |
| `show` | `--run-id` | Print the record verbatim |
| `summary` | `[--repo NAME] [--last N]` | Print the aggregate JSON below |

`finish` reads exactly these keys: `execution` (`full`, `degraded`,
`blocked`), `reviewers` (0–2), `trigger` (`runtime-removal`,
`schema-migration`, `auth-boundary`, `data-boundary`, `external-side-effect`,
or null), `degraded_reasons` (list), `verdict`, `block_reason`,
`review_passes` (1–3), `repair_passes` (0–2), and `findings`. Each finding has
`id` (`PSDR-001`), `severity`, `class`, `pattern`, `status`, `repair_pass`,
`location` (`path`, `locator`), `evidence` (relative paths), `consequence`, and
`fix`. `READY` permits only repaired findings, `REVISE` needs an unresolved
one, `BLOCKED` needs `block_reason`, a repair pass needs a repaired finding,
and `review-only` permits no repair pass.

## Reading the log

The log is for agents. `summary` returns `runs`, `counts`, `cost`, `chains`
(plans reviewed more than once), `findings` (with `repeated_patterns`), and
`anomalies`; every entry carries `run_id` values for `show`. Start from
`anomalies` and `chains`.

## Boundary

Records hold repository-relative paths, a directory name, hashes, enum
values, integers, timestamps, and short paraphrases. Never put source text,
absolute paths, prompts, transcripts, command output, or credentials in a
note, consequence, or fix. Files are local and unsigned: self-improvement
evidence, not an audit log.

## Errors

Failures print one line to stderr, `{"error":{"code":"…","message":"…"}}`,
and exit 2. Codes: `invalid-arguments`, `schema-invalid`, `run-not-found`,
`not-git-repository`, `outside-repository`, `already-finished`,
`evidence-home-unwritable`.
````

- [ ] **Step 5: Rewrite the changed README sections (Korean)**

In `skills/pre-sdd-review/README.md`:

Replace the `## 설치` section body after the `$skill-installer` code block with:

```markdown
로컬 영수증 기록기는 따로 설치하지 않습니다. 스킬 폴더 안의 `evidence/evidence.py`를
Python 3.11+로 직접 실행하며, 컨트롤러는 이미 알고 있는 스킬 루트를 그대로 씁니다.

```bash
python3 "<skill-root>/evidence/evidence.py" --version
```
```

In `## 결과와 기본 흐름`, replace the last paragraph (starting `호환되는 로컬 CLI가 있으면`) with:

```markdown
호환되는 로컬 기록기가 있으면 의미 검토 전 `start`, 최종 판정 뒤 `finish`를
호출하고 `Evidence: recorded; run_id=<run-id>`를 출력합니다. 기록기가 없거나
호환되지 않거나 권한 오류가 나면 검토는 계속되고
`Evidence: not_recorded; reason=<code>`를 출력합니다. 설계 경로는 컨트롤러가
계획의 `**Spec:**`에서 해석한 값을 넘기며, 해석할 수 없으면 생략하고 `BLOCKED`로
끝냅니다. 도중에 끝나면 `abandon`으로 run을 닫습니다.
```

In `## 안전과 개인정보`, replace the last three paragraphs (from `영수증은 기본적으로` to the end of the section) with:

```markdown
영수증은 `~/.pre-sdd-review/runs/<run-id>.json`에 로컬로만 남습니다(schema 2).
저장소 상대 경로, 디렉터리 이름, 해시, 열거값, 짧은 paraphrase만 저장하며 source
원문(source text), 절대 경로, prompts, transcripts, credentials는 넣지 마세요.
기록기는 자동 비밀 탐지를 하지 않습니다.

로컬 파일 저장은 악의적인 로컬 변조를 막는 서명된 audit log가 아닙니다.
`outcome` 라벨(`good`, `false-ready`, `noisy`, `abandoned`)은 SDD가 끝난 뒤
사람이나 SDD 워커가 남기는 관찰이며 다시 기록해 정정할 수 있습니다. 라벨은
자기개선용 evidence이지 객관적·감사 등급 증거가 아닙니다.
```

Replace the `## 운영과 한계` section body with:

```markdown
명령은 `start`, `finish`, `abandon`, `outcome`, `show`, `summary` 여섯 개입니다.
정확한 인자, stdin 형식, 크기 제한은 [evidence 안내](evidence/README.md)를
따릅니다.

로그는 에이전트가 읽도록 만들어졌습니다. 개선점을 찾을 때는 에이전트에게
`summary`를 실행하게 하고 `anomalies`와 `chains`부터 보게 하세요. 모든 집계에
`run_id`가 붙어 있어 `show --run-id`로 바로 내려갈 수 있습니다. 후보 픽스처
자동 선정, 자동 스킬 변경, client/model ranking은 하지 않습니다.

버전 원본은 `release.toml`이고 `SKILL.md`의 `metadata.version`은 검증된 복제
값입니다. 기록기는 이전 `runs/<연>/<월>/` 영수증을 읽지 않으며, 영수증 삭제는
파일 삭제로 충분합니다.
```

In `## 호환성과 검증 수준`, replace the last paragraph (`공유 CLI는 현재 macOS native 경로와…`) with:

```markdown
기록기는 Python 3.11+ 표준 라이브러리만 쓰며 macOS에서 provider-free 테스트로
검증됐습니다. Linux와 native Windows는 각 환경에서 evidence 단계가 직접 실행될
때까지 `not_measured`입니다.
```

- [ ] **Step 6: Rewrite the changed README sections (English)**

In `skills/pre-sdd-review/README.en.md`:

Replace the `## Install` body after the `$skill-installer` code block with:

```markdown
The local evidence recorder is not installed. Run `evidence/evidence.py` from
the skill folder with Python 3.11+; the controller uses the skill root it
already loaded.

```bash
python3 "<skill-root>/evidence/evidence.py" --version
```
```

In `## Expected result`, replace the last paragraph (`When a compatible local CLI is present…`) with:

```markdown
When a compatible local recorder is present, the controller calls `start`
before semantic review, calls `finish` after the final verdict, and prints
`Evidence: recorded; run_id=<run-id>`. If the recorder is unavailable,
incompatible, or denied by permissions, review continues and it prints
`Evidence: not_recorded; reason=<code>`. The controller passes the design path
it resolved from the plan's `**Spec:**` field; when it cannot, it omits the
design and ends with `BLOCKED`. An invocation that ends early closes its run
with `abandon`.
```

In `## Safety and privacy`, replace the last three paragraphs (from `Receipts stay local` to the end of the section) with:

```markdown
Receipts stay local as `~/.pre-sdd-review/runs/<run-id>.json` (schema 2).
Records hold repository-relative paths, a directory name, hashes, enum values,
and short paraphrases only; never source text, absolute paths, prompts,
transcripts, or credentials. The recorder does not detect secrets.

Local file storage is not a signed audit log resistant to malicious local
tampering. An `outcome` label (`good`, `false-ready`, `noisy`, `abandoned`) is
an observation recorded by a person or the SDD worker after SDD ends and may be
re-recorded to correct it. Labels are self-improvement evidence, not objective
or audit-grade proof.
```

Replace the `## Operations and limits` body with:

```markdown
The command surface is `start`, `finish`, `abandon`, `outcome`, `show`, and
`summary`. For exact arguments, the stdin shape, and size limits, use the
[evidence guide](evidence/README.md).

The log is written for agents. To look for improvements, have an agent run
`summary` and read `anomalies` and `chains` first; every aggregate carries
`run_id` values so it can drop into `show --run-id`. There is no automatic
fixture selection, skill mutation, or client/model ranking.

The version source is `release.toml`; `SKILL.md` `metadata.version` is a
verified copy. The recorder ignores older `runs/<year>/<month>/` receipts, and
deleting a receipt is deleting its file.
```

In `## Supported hosts and verification`, replace the last paragraph (`The shared CLI has verified…`) with:

```markdown
The recorder uses only the Python 3.11+ standard library and is verified by
the provider-free suite on macOS. Linux and native Windows remain
`not_measured` until the evidence stage runs there.
```

- [ ] **Step 7: Recompute digests and run tests**

Run the digest helper; paste `INSTRUCTION SKILL.md` (frontmatter changed), both `README_CANONICAL_DOCUMENT_DIGESTS`, and all `README_CANONICAL_SECTION_DIGESTS` values into `test_contract.py`. Run the contract and repository discovery commands. Expected: `OK` except `test_maintainer_testing_compatibility_and_release_stay_role_specific`/`release_document_errors` (release.md still says `version 1.3.1`) and the v2 docs test (contract.md not yet updated) — both are fixed in Task 8. Everything else must pass.

- [ ] **Step 8: Commit**

```bash
git add skills/pre-sdd-review tests/products/pre-sdd-review/test_contract.py tests/repository
git commit -m "release(pre-sdd-review): 2.0.0 with single-file evidence recorder docs"
```

---

### Task 8: Maintainer documents

**Files:**
- Modify: `docs/maintainers/products/pre-sdd-review/contract.md` (`## Optional evidence contract`)
- Modify: `docs/maintainers/products/pre-sdd-review/testing.md` (evidence paragraphs)
- Modify: `docs/maintainers/products/pre-sdd-review/compatibility.md` (`## Evidence CLI compatibility`)
- Modify: `docs/maintainers/products/pre-sdd-review/release.md` (version and evidence paragraphs)
- Modify: `tests/products/pre-sdd-review/test_contract.py` (digests, `test_maintainer_testing_compatibility_and_release_stay_role_specific` facts)

- [ ] **Step 1: Update the test facts**

In `test_maintainer_testing_compatibility_and_release_stay_role_specific`, replace the fact `"pre-sdd-review-evidence"` in the `normalized_testing` loop with `"evidence.py"`, and replace

```python
        self.assertIn("## Evidence CLI compatibility", compatibility)
```

with

```python
        self.assertIn("## Evidence recorder compatibility", compatibility)
```

- [ ] **Step 2: Rewrite `contract.md` `## Optional evidence contract`**

Replace the section (up to `## Handoff`) with:

```markdown
## Optional evidence contract

Evidence recording is a separate optional contract and does not change the
authority order, reviewer protocol, repair allowlist, or verdict rules. The
controller runs `python3 "<skill-root>/evidence/evidence.py" --version` from
the loaded skill root, calls `start` before semantic review only when `schema`
is 2 and `skill_name` is `pre-sdd-review`, and calls `finish` once after the
verdict and repairs are final. It prints exactly one `Evidence:` line. Any
unavailable, malformed, incompatible, or permission-failing recorder remains
visible as `not_recorded` and cannot change `READY`, `REVISE`, or `BLOCKED`.

The controller resolves the design path from the plan's `**Spec:**` field and
passes it as `--design`; when it cannot, it omits `--design` and returns
`BLOCKED`. The recorder never parses `**Spec:**`. An invocation that ends
before `finish` calls `abandon` with one of `user-cancelled`, `input-changed`,
`scope-changed`, `input-format-fixed`, or `other`. `run_id` stays
controller-local and outside the reviewed documents.

The recorder owns paths, hashes, Git facts, validation, atomic file
replacement, and aggregation under `~/.pre-sdd-review/runs/`. The reviewer and
controller remain the only owners of semantic findings, repairs, protocol
observations, and verdicts. Records hold repository-relative paths, a
directory name, hashes, enum values, integers, timestamps, and bounded
paraphrases; never source text, absolute paths, prompts, provider
transcripts, command output, environment values, or credentials. Local files
are not a signed audit log.

`outcome` is not a controller duty. After SDD or implementation ends, the user
or the SDD worker records one label (`good`, `false-ready`, `noisy`,
`abandoned`) with an optional note; `false-ready` requires a `READY` verdict
and a label may be re-recorded. `summary` is JSON for agents: counts, cost,
per-plan chains, repeated finding patterns, and anomalies, each carrying
`run_id` values. No automatic skill mutation, fixture export, or client/model
ranking follows from it.

```

- [ ] **Step 3: Update `testing.md`**

Replace the paragraph beginning `공유 evidence CLI의 schema, repository identity…` and its code block and the following paragraph (`이 단계는 네트워크나 provider를 호출하지 않습니다…`) with:

````markdown
`evidence/evidence.py` 기록기의 schema 2 record, Git 사실, 불변식, 여섯 명령,
summary 집계 계약은 별도 provider-free 단계로 실행합니다. The recorder runs as
`python3 skills/pre-sdd-review/evidence/evidence.py` and is not installed.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests/products/pre-sdd-review/evidence -p 'test_*.py' -v
```

이 단계는 네트워크나 provider를 호출하지 않으며 DB나 index를 추가하지 않습니다.
````

Replace the final paragraph (`Evidence lifecycle 픽스처는…`) with:

```markdown
Evidence 테스트는 임시 Git 저장소와 합성 skill root만 사용하며 source text, raw
path, prompt, transcript, credential을 record에 넣지 않습니다. `outcome` label은
관찰자 입력이며 audit-grade proof가 아닙니다. native Windows, Linux, Claude Code,
Cursor, Grok은 각 native 또는 live 단계가 별도로 실행되기 전까지
`not_measured`입니다.
```

- [ ] **Step 4: Update `compatibility.md`**

Replace from `## Evidence CLI compatibility` through the end of `### CLI matrix` paragraph (`An injected native binding … must not be promoted to native support.`) with:

```markdown
## Evidence recorder compatibility

Recorder portability is independent of the semantic host matrix. Codex,
Claude Code, Cursor, and Grok run the same `evidence/evidence.py` from the
loaded skill root and share one `~/.pre-sdd-review/` data root. A recorder
pass does not prove independent read-only review or semantic quality on that
host.

### CLI matrix

| Runtime | Status | Evidence boundary |
| --- | --- | --- |
| macOS / Python 3.11+ | `verified` | provider-free evidence suite |
| Linux / Python 3.11+ | `not_measured` | no native run evidence |
| Windows / Python 3.11+ | `not_measured` | no native run evidence |

A `windows-portable` run on another OS verifies stage selection only. It must
not be promoted to native support.
```

- [ ] **Step 5: Update `release.md`**

Change `` `version 1.3.1` `` to `` `version 2.0.0` ``. Replace the sentence beginning `` `verify-download`는 fresh bytes… `` through `로컬 build output은 public-release evidence가 아닙니다.` with:

```markdown
`verify-download`는 fresh bytes, checksum, ZIP structure, extracted payload
hash, exact payload manifest, extracted `evidence.py --version` canonical JSON,
product verification을 확인합니다. 로컬 build output은 public-release evidence가
아닙니다.
```

Replace the paragraph `Release payload keeps the evidence package source files non-executable…` with:

```markdown
Release payload keeps `evidence/evidence.py` non-executable; it is run with
`python3` and never installed. Native Windows stays `not_measured` unless a
native Python 3.11 evidence run is recorded.
```

- [ ] **Step 6: Recompute digests and run tests**

Run the digest helper; paste `MAINTAINER_CANONICAL_DIGEST`, `TESTING_CANONICAL_DIGEST`, `COMPATIBILITY_CANONICAL_DIGEST`, and `RELEASE_CANONICAL_DIGEST` (the `### …` subsection digests are unchanged and must match the printed values). Run the contract discovery command. Expected: `OK`.

- [ ] **Step 7: Commit**

```bash
git add docs/maintainers/products/pre-sdd-review tests/products/pre-sdd-review/test_contract.py
git commit -m "docs(pre-sdd-review): maintainer contract for the schema 2 recorder"
```

---

### Task 9: User documents (ko/en) and public-doc pins

**Files:**
- Modify: `docs/users/ko/installation.md:19-43`, `docs/users/en/installation.md:19-44`
- Modify: `docs/users/ko/verification.md` (`## 오프라인 픽스처` evidence paragraphs), `docs/users/en/verification.md` (`## Offline fixtures`)
- Modify: `docs/users/ko/safety-and-privacy.md` (`## SDD 전 문서 검토`), `docs/users/en/safety-and-privacy.md` (`## Pre-SDD document review`)
- Modify: `tests/repository/test_public_docs.py` (`PRE_SDD_SHARED_SECTION_DIGESTS`, `test_pre_sdd_review_shared_guides_preserve_scope_and_evidence_limits`)

- [ ] **Step 1: Update the test pins**

In `test_pre_sdd_review_shared_guides_preserve_scope_and_evidence_limits`, replace

```python
        for text in (korean_installation, english_installation):
            self.assertIn("pre-sdd-review-evidence", text)
            self.assertIn("--bin-dir", text)
            self.assertIn("~/.pre-sdd-review/", text)
            self.assertIn("command -v pre-sdd-review-evidence", text)
```

with

```python
        for text in (korean_installation, english_installation):
            self.assertIn("python3 skills/pre-sdd-review/evidence/evidence.py --version", text)
            self.assertIn("~/.pre-sdd-review/", text)
            self.assertNotIn("--bin-dir", text)
            self.assertNotIn("install.py", text)
```

and, for the verification documents, add after the two existing `assertIn("pre-sdd-review-evidence", …)` lines (the stage name stays):

```python
        self.assertIn("evidence.py", korean_verification)
        self.assertIn("evidence.py", english_verification)
```

- [ ] **Step 2: Rewrite the installation sections**

`docs/users/ko/installation.md`, replace `## Pre-SDD Review evidence CLI` through the paragraph ending `Windows는 정확한 .cmd와 .pyz 두 대상을 검사합니다.` with:

````markdown
## Pre-SDD Review evidence 기록기

`pre-sdd-review`의 의미 검토 지원은 Codex로 유지됩니다. 선택적 로컬 기록기
`evidence/evidence.py`는 설치하지 않고 스킬 폴더에서 Python 3.11+로 직접
실행하며, Codex, Claude Code, Cursor, Grok이 같은 파일과 같은 데이터 루트를
씁니다. 이는 다른 호스트의 의미 검토 지원을 뜻하지 않습니다.

```bash
python3 skills/pre-sdd-review/evidence/evidence.py --version
```

영수증은 `~/.pre-sdd-review/runs/<run-id>.json`에 남습니다. 스킬 폴더를 지워도
영수증은 지워지지 않으며, 영수증 삭제는 파일 삭제로 충분합니다. 이전 버전이
설치한 `pre-sdd-review-evidence` launcher는 더 이상 쓰이지 않으므로 그 파일만
확인한 뒤 제거하세요.
````

`docs/users/en/installation.md`, replace `## Pre-SDD Review evidence CLI` through `On Windows, inspect the exact .cmd and .pyz targets.` with:

````markdown
## Pre-SDD Review evidence recorder

Semantic review support for `pre-sdd-review` remains Codex-only. The optional
local recorder `evidence/evidence.py` is not installed; run it from the skill
folder with Python 3.11+. Codex, Claude Code, Cursor, and Grok use the same
file and the same data root. That does not make the other hosts supported for
semantic review.

```bash
python3 skills/pre-sdd-review/evidence/evidence.py --version
```

Receipts live at `~/.pre-sdd-review/runs/<run-id>.json`. Removing the skill
folder does not delete receipts, and deleting a receipt is deleting its file.
The `pre-sdd-review-evidence` launcher installed by earlier versions is no
longer used; inspect that exact file, then remove it.
````

- [ ] **Step 3: Rewrite the verification evidence paragraphs**

`docs/users/ko/verification.md`, inside `## 오프라인 픽스처`, replace the two paragraphs `Evidence 단계는 …` and `현재 호스트의 native atomic path…` with:

```markdown
Evidence 단계는 `tests/products/pre-sdd-review/evidence/`에서 `evidence.py`의
schema 2 record, Git 사실, 불변식, 여섯 명령, summary 집계를 검증합니다.
네트워크, 모델, provider, telemetry를 호출하지 않으며 DB나 index를 쓰지
않습니다.

비-Windows의 `windows-portable` 통과는 native Windows 지원을 증명하지 않습니다. native Windows와 Linux는 각 Python 3.11 환경에서 evidence 단계가
실행되기 전까지 `not_measured`입니다. Claude Code, Cursor, Grok의 의미 검토도
별도 live receipt 없이는 `not_measured`입니다.
```

`docs/users/en/verification.md`, inside `## Offline fixtures`, replace `The evidence stage under …` and `The current host's native atomic path …` with:

```markdown
The evidence stage under `tests/products/pre-sdd-review/evidence/` validates
the schema 2 records, Git facts, invariants, six commands, and summary
aggregation of `evidence.py`. It makes no network, model, provider, or
telemetry call and uses no database or index.

A non-Windows `windows-portable` pass does not prove native Windows support. Native Windows and Linux remain `not_measured` until the
evidence stage runs under Python 3.11 there. Semantic review on Claude Code,
Cursor, and Grok also remains `not_measured` without a separate validated live
receipt.
```

(The pinned clause `비-Windows의 \`windows-portable\` 통과는 native Windows 지원을 증명하지 않습니다.` / `A non-Windows \`windows-portable\` pass does not prove native Windows support.` must appear exactly once in each section.)

- [ ] **Step 4: Rewrite the safety paragraphs**

`docs/users/ko/safety-and-privacy.md`, inside `## SDD 전 문서 검토`, replace paragraphs two and three (from `선택적 \`pre-sdd-review-evidence\`는…` to the end of the section) with:

```markdown
선택적 기록기 `evidence/evidence.py`는 Python 표준 라이브러리만 사용하고 설치하지
않으며, run마다 record 하나를 `~/.pre-sdd-review/runs/` 또는 명시한 절대
`PRE_SDD_REVIEW_HOME`에 둡니다. record에는 저장소 상대 경로, 디렉터리 이름, 해시,
열거값, 정수, 시각, 짧은 paraphrase만 들어갑니다. source 원문, 절대 경로, prompt,
provider transcript, command output, credential, 환경 변수 값은 짧게 제한된
note·consequence·fix에도 넣지 마세요. 기록기는 자동 비밀 탐지를 약속하지 않습니다.

원자적 로컬 저장은 협력하는 client 사이의 일관성을 제공할 뿐, 악의적인 로컬 변조를 막는 서명된 audit log가 아닙니다. `outcome` label(`good`, `false-ready`,
`noisy`, `abandoned`)은 SDD나 구현이 끝난 뒤 사람이나 SDD 워커가 남기는 관찰이며
다시 기록해 정정할 수 있습니다. label은 자기개선 evidence이지 객관적 품질 판정이나
감사 등급 증거가 아닙니다. 로그 읽기는 에이전트의 일입니다. `summary`는 JSON을
돌려주며 anomalies와 chains에 run_id가 붙어 있습니다.

```

`docs/users/en/safety-and-privacy.md`, inside `## Pre-SDD document review`, replace paragraphs two and three with:

```markdown
The optional recorder `evidence/evidence.py` uses only the Python standard
library, is not installed, and keeps one record per run under
`~/.pre-sdd-review/runs/` or an explicit absolute `PRE_SDD_REVIEW_HOME`.
Records hold repository-relative paths, a directory name, hashes, enum values,
integers, timestamps, and short paraphrases. Do not store source text,
absolute paths, prompts, provider transcripts, command output, credentials, or
environment-variable values, even inside a bounded note, consequence, or fix.
The recorder does not promise automatic secret detection.

Atomic local storage gives cooperating clients consistency; it is not a signed audit log resistant to malicious local tampering.
An `outcome` label (`good`, `false-ready`, `noisy`, `abandoned`) is an
observation recorded by a person or the SDD worker after SDD or implementation
ends and may be re-recorded to correct it. Labels are self-improvement
evidence, not objective quality judgments or audit-grade proof. Reading the log
is an agent's task: `summary` returns JSON whose anomalies and chains carry
run_id values.

```

- [ ] **Step 5: Recompute the shared-section digests**

```bash
python3 - <<'EOF'
import hashlib, re
from pathlib import Path
sections = {
    ("ko", "safety"): ("docs/users/ko/safety-and-privacy.md", "## SDD 전 문서 검토"),
    ("en", "safety"): ("docs/users/en/safety-and-privacy.md", "## Pre-SDD document review"),
    ("ko", "verification"): ("docs/users/ko/verification.md", "## 오프라인 픽스처"),
    ("en", "verification"): ("docs/users/en/verification.md", "## Offline fixtures"),
}
for key, (path, heading) in sections.items():
    text = Path(path).read_text(encoding="utf-8")
    owned = re.compile(rf"^{re.escape(heading)}\s*$.*?(?=^##\s|\Z)", re.M | re.S).findall(text)
    assert len(owned) == 1, key
    print(key, hashlib.sha256(owned[0].encode("utf-8")).hexdigest())
EOF
```

Paste the four values into `PRE_SDD_SHARED_SECTION_DIGESTS` in `tests/repository/test_public_docs.py`.

- [ ] **Step 6: Run the repository stage**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/repository -p 'test_*.py'`
Expected: `OK` (this also exercises broken-link and public-doc symmetry checks).

- [ ] **Step 7: Commit**

```bash
git add docs/users tests/repository/test_public_docs.py
git commit -m "docs(users): describe the uninstalled pre-sdd evidence recorder"
```

---

### Task 10: Full verification and release check

**Files:**
- None new. Verification only; fix anything that fails in the file that owns it.

- [ ] **Step 1: Run the full profile**

Run: `python3 scripts/verify.py --profile full`
Expected: every stage passes, including `pre-sdd-review-contract`, `pre-sdd-review-evidence`, and `python-compile` (which compiles `skills/pre-sdd-review/evidence/evidence.py`).

- [ ] **Step 2: Run the portable profile**

Run: `python3 scripts/verify.py --profile windows-portable`
Expected: passes; the evidence stage is excluded by design.

- [ ] **Step 3: Run the release check and a local build round-trip**

```bash
python3 scripts/release.py check --product pre-sdd-review
OUT=$(mktemp -d) && python3 scripts/release.py build --product pre-sdd-review --output "$OUT" && python3 scripts/release.py verify-download --product pre-sdd-review --input "$OUT"
```

Expected: `check` reports no errors (2.0.0 is greater than the 1.3.1 baseline, the dated changelog heading exists); `verify-download` passes including the `evidence.py --version` smoke. Do not tag, push, or publish.

- [ ] **Step 4: Confirm size and closure criteria**

```bash
wc -l skills/pre-sdd-review/evidence/evidence.py tests/products/pre-sdd-review/evidence/*.py
ls skills/pre-sdd-review/evidence
git status --short
```

Expected: `evidence.py` under 600 lines; the evidence tests directory under 800 lines total; `evidence/` contains exactly `README.md` and `evidence.py`; the working tree is clean after the commits above.

- [ ] **Step 5: Real round trip on the owner's machine (optional, outside CI)**

From any real repository with an approved plan and design, run one `pre-sdd-review` invocation from Codex and one from Claude Code with the new skill, then:

```bash
python3 skills/pre-sdd-review/evidence/evidence.py summary --last 2
```

Expected: two `completed` runs with `client.id` `codex` and `claude-code`, non-null `design`, `execution`, and findings, and an `anomalies` object with the four documented keys. Optionally remove the dead launcher after inspecting it:

```bash
ls -l "$HOME/.local/bin/pre-sdd-review-evidence" && rm "$HOME/.local/bin/pre-sdd-review-evidence"
```

This step records nothing in the repository and changes no host-support claim.

---

## Self-review against the spec

- **Decision 1 (one script, no installer, `--version` line):** Tasks 1, 2 (`--version`), 7 (README), 8 (release.md), 10 (smoke).
- **Decision 2 (data root, layout, `0o700/0o600`, temp + replace, 64 KiB):** Task 2 (`evidence_home`, `write_record`, `iter_records`), Task 3 size test.
- **Decision 3 (schema 2 fields and all eight invariants):** Task 2 (`start` shape), Task 3 (`validate_finish`, `validate_finding`, invariant subtests).
- **Decision 4 (six commands and their semantics, `--repo` mismatch = `outside-repository`):** Tasks 2–5.
- **Decision 5 (controller contract wording, protocol sentence):** Task 6.
- **Decision 6 (summary keys, rules, four anomalies, filters):** Task 5.
- **Decision 7 (privacy boundary):** Task 2 test asserts no absolute path; Tasks 7–9 documentation.
- **Decision 8 (error envelope and seven codes):** Task 1 envelope, Tasks 2–5 codes, Task 7 evidence README.
- **Decision 9 (2.0.0):** Task 7.
- **Package and repository impact table:** Task 1 (payload, release.py, repository tests), Task 6 (cases, contract pins), Task 7 (skill docs), Task 8 (maintainer docs), Task 9 (user docs).
- **Verification design:** every listed behaviour has a test in Tasks 1–5; AST contract in Task 1; release round-trip in Task 10.
- **Success criteria:** Task 10 checks size, directory contents, and profiles; Task 5 tests summary answers.
