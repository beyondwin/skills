# kws-book-writer testing

Activation is explicit-only. Live evidence is in the
[2026-11-20 evaluation](../../../research/2026-11-kws-book-writer-eval/README.md); book quality
for readers is `not_measured` until a user judges a pilot.

## Provider-free evidence

The required evidence is `python3 scripts/verify.py --skill kws-book-writer`. It runs
`product-contract`, the `kws-book-writer-contract` stage, and `python-compile`. The
contract stage discovers `test_*.py` in `tests/products/kws-book-writer/`; those tests
own the checks on `SKILL.md`, its references, and `scripts/book_check.py`, using
synthetic fixtures only.

The release smoke in `scripts/release.py` also checks that `SKILL.md` is explicit-only,
has "Use when" and `/kws-book-writer`, and that the payload carries `LICENSE.txt`,
`agents/openai.yaml`, `references/workflow.md`, `references/acceptance.md`, and
`scripts/book_check.py`, and no test file.

These prove file shape and the mechanical check only. They do not prove that a run
writes a good or accurate book.

## Live runs

Recorded on 2026-11-20 with `claude -p` on macOS, opus at high effort, pinned payloads
(details and decision rules in the
[evaluation](../../../research/2026-11-kws-book-writer-eval/README.md)):

- Smoke: a 3-chapter synthetic book ran end to end, held both stops, and passed
  `check --final`. It exposed the table-of-contents bug fixed before release.
- Seeded defects: the plain-review gate with workspace inputs found 24/24; the earlier
  eight-criterion brief showed no measured difference from a plain review.
- Pilot: a 6-chapter private book (51,742 characters, about $47.70) reached `check --final`;
  a fresh session resumed it from the workspace. Reader adoption is `not_measured`.

A live run uses synthetic sources, or private sources kept outside this repository.
Private manuscripts and transcripts are never committed. An ACCEPT is not evidence of a
defect-free book: the accepted smoke book still had two real errors.
