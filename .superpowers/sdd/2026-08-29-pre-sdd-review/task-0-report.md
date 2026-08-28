# Task 0 report: repository-contract repair

## Implementation

- Added the empty, repository-owned `tests/__init__.py` marker so Python resolves
  `tests.repository` from this checkout rather than an installed `tests` package.
- Changed the test-layout contract to derive its roots from
  `git ls-files -- tests`, instead of filesystem directories. Untracked cache-only
  directories therefore do not participate, while a tracked legacy root remains
  a violation.
- Added a temporary real Git-repository regression case that first leaves
  `tests/contract/cache.py` untracked (accepted) and then tracks it (rejected).

## RED evidence

### Pre-existing full-profile failure

Command:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --profile full
```

Output (exit 1):

```text
==> repository-contract: /opt/homebrew/opt/python@3.14/bin/python3.14 -m unittest discover -s tests/repository -p test_*.py
................E
======================================================================
ERROR: test_catalog_contract (unittest.loader._FailedTest.test_catalog_contract)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_catalog_contract
Traceback (most recent call last):
  File "/Users/kws/source/private/skills/.worktrees/codex/pre-sdd-review/tests/repository/test_catalog_contract.py", line 25, in <module>
    from tests.repository.test_repository import EXPECTED_PLUGIN  # noqa: E402
ModuleNotFoundError: No module named 'tests.repository'

----------------------------------------------------------------------
Ran 286 tests in 15.485s

FAILED (errors=1)
FAILED stage: repository-contract
```

### Layout regression RED

After adding the regression assertion but before changing the filesystem-root
implementation, command:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.repository.test_repository.RepositoryContractTests.test_layout_contract_ignores_untracked_roots_but_rejects_tracked_legacy_roots
```

Output (exit 1):

```text
FAIL: test_layout_contract_ignores_untracked_roots_but_rejects_tracked_legacy_roots
AssertionError: Items in the first set but not the second:
'contract'

Ran 1 test in 0.063s

FAILED (failures=1)
```

The failure is the desired one: an untracked `tests/contract/` directory was
incorrectly included by the old `iterdir()` implementation.

## GREEN evidence

Focused commands:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.repository.test_repository.RepositoryContractTests
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/repository -p 'test_*.py'
```

Output:

```text
...
----------------------------------------------------------------------
Ran 3 tests in 0.101s

OK

----------------------------------------------------------------------
Ran 308 tests in 11.802s

OK
```

Final repository gate and complete verification command:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --profile full
```

Output (exit 0):

```text
repository-contract: Ran 308 tests in 11.567s — OK
korean-package: Ran 5 tests in 0.144s — OK
korean-offline: 31 cases; mutation checks PASS; skill tree PASS
korean-live-unit: Ran 212 tests in 16.914s — OK
korean-live-dry-run: approved_total_ceiling=160, baseline_calls=122, producer_calls=119, remediation_calls=38, reviewer_calls=3
image-contract: 31 cases; 8 mutation checks PASS; skill tree PASS
image-inspector: Ran 26 tests in 0.022s — OK
how-it-works-contract: Ran 34 tests in 0.013s — OK
python-compile: completed successfully
```

## Files changed

- `tests/__init__.py`
- `tests/repository/test_repository.py`
- `.superpowers/sdd/2026-08-29-pre-sdd-review/task-0-report.md`

## Self-review

- The marker is empty and is the smallest package-owned change that fixes the
  import-resolution defect.
- The contract reads tracked paths through Git rather than inspecting cache or
  ignored directories on disk.
- The regression uses real `git init` and `git add`, checks both untracked and
  tracked behavior, and does not change product payloads, catalog content, or
  approved design files.
- `git diff --check` was run before commit.

## Concerns

The repository-contract test run still emits an existing `zipfile` duplicate
member `UserWarning` from a catalog fixture. It is unrelated to this change;
the repository contract and full profile both exit successfully.
