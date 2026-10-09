# Verification record

Date: 2026-10-09. This file records executed checks, not proposed tests.

## Source and study checks

- All 57 source-package checksums matched before execution. Source tests ran only
  in a temporary copy; original supplied files were not changed.
- Both inherited suites passed under `/usr/bin/python3` 3.9.6 on macOS. Results and
  log fingerprints are in [reproduction-results.json](reproduction-results.json).
- The 15-probe offline audit ran under the same stock runtime. Findings, controls,
  exact expectations and observed results are in [offline-results.json](offline-results.json).
- The retained prompt preparation script reproduced all 24 prompt hashes exactly.
- All 72 CLI dispatches are accounted for: 71 outputs and one pre-generation
  authentication failure. Runtime identity and zero tool-use checks cover all
  completed generations. Nine JSON outputs passed shape and fixed-value checks.
- Independent blinded grades cover every generated output; one adjudication is
  recorded explicitly. Semantic grades are model judgments, not deterministic proof.

## Repository checks

The initial `python3 scripts/verify.py` in the original checkout stopped at registry
validation because ignored residue kept these retired directories present:
`skills/pre-sdd-review`, `skills/sddx`, `tests/products/pre-sdd-review`,
`tests/products/sddx`, and `tests/products/waygent`. No product tests ran in that
attempt. The residue and concurrent unrelated changes were preserved.

`python3 scripts/verify.py` then passed in a disposable macOS Git clone containing
current tracked files and the intended untracked documentation, with files staged
for index-based packaging checks. The clone excluded ignored residue. Runtime was
Homebrew Python 3.14.7. Results: 641 unit tests (246 repository, 11 Korean package,
255 live-runner unit, 65 image inspector, 64 explanation contract), 35 Korean and 32
image fixture cases, mutation checks, provider-free runner dry-run and compilation.
The full check made no provider calls.

The later report audit changed only study aggregation code/data and documentation;
the existing product/test bytes did not change. After those corrections, the study's
accounting validator passed again: frozen hashes, unique dispatches/grades, strict
and secondary scores, matched denominators, JSON checks and offline classifications.
All research harnesses compiled under stock Python 3.9.6. Retained input preparation
reproduced all 24 prompt hashes. Aggregation can run from the persistent raw archive.
The final focused public-document suite passed all 65 tests after the report audit;
the staged disposable-copy diff also passed `git diff --cached --check`. No unchanged
full product suite was repeated for these report-only corrections.

## Evidence retention

Raw evidence was copied into the user's local Downloads evaluation archive with a
SHA-256 artifact index. It contains reproduction logs, input
prompts, outputs, receipts, rollout contexts and blinded grading records. Runtime
HOME/config/auth directories were not copied; no auth-named file is present. This
is a local private archive, not part of Git. Public aggregates identify each output
by hash and host/case/condition so it can be traced into that archive.

## Not established

Human reading comprehension, production use, native skill discovery, tool-driven
evidence retrieval, other operating systems, stable cross-model rankings, statistical
equivalence, or the effect of the proposed evidence-status refinement. No installed
product file, product version or supported-host declaration changed.
