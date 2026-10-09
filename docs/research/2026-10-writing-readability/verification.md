# Verification record — 2026-10-09

Scope: personal skill payloads and research/learning records. The repository's
supported product payloads, registry, global instructions and release metadata
were not changed. Existing unrelated working-tree changes were preserved.

- Candidate 0.2.0, revision 0.2.1, final 0.2.2 and installed skill passed skill-creator
  structural validation. This does not establish output quality.
- Every new Python runner and summarizer compiled with stock macOS Python 3.9.
- Ten synthetic repository fixtures built successfully before the main runs.
- Generation and regression dry runs dispatched no provider calls.
- The four result sets reproduced exactly from private archives. Their summarizers
  checked frozen hashes, unique dispatch ledgers, response/receipt hashes, runtime
  identity evidence, judge schemas and copied-credential removal.
- Source judgments and model judgments remain separate. The path-masking false
  positive, unknown/missing results, rejected candidates and transport retries are
  explicitly recorded. Controls are excluded from candidate preference counts.
- Final JSON keys and the null/false values passed deterministic parsing checks.
- The installed native smoke read the final skill and document reference, preserved
  the source's numbers and limits, and left its synthetic workspace unchanged.
- All six installed files match the frozen 0.2.2 manifest. The previous 0.1.0 copy was
  checked before replacement and backed up outside Git.
- No copied auth.json remained in any of the four private run archives at completion.
- Local Markdown links passed. New final-payload and report whitespace passed.
  The frozen 0.2.0 and 0.2.1 SKILL.md files each retain one historical trailing space so
  their tested hashes remain exact. No live payload carries that space.
- `git diff --check` passed for tracked changes.
- `python3 -m unittest discover -s tests/repository -p test_public_docs.py -q`:
  **65 tests passed**.

No full product verification, merge, commit, publication, human reading study,
write-enabled generated workflow or native Claude/Cursor installation test was run.
The supported product payloads were unchanged and no merge was requested.
Raw responses, prompts, receipts and credential copies never entered Git.

See [study summary](study-summary.json), [results](README.md),
[final author grades](final-author-grades.json), and [installation](installation.json).
