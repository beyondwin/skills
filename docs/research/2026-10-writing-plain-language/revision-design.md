# 0.4.1 correction, frozen before calls

The 0.4.0 author review rejected unexplained central terms in the schema handoff
and metric definition, and unnecessary repeated explanation in the permission
case. Its planned judgments and adoption checks were skipped once author review
failed; no pairwise preference result is claimed for that version. All twelve
completed generations and the rejection remain available.

0.4.1 requires explaining the actual work or measurement, rather than merely
translating or formatting a term. It also removes examples that repeat a rule,
retaining unique conditions in the one explanation. Trigger and Git contracts
remain unchanged. The resource tree is frozen separately.

Generate the same six development cases once with the revision, explicitly reusing
the six 0.2.2 responses from the first batch. This is a within-session development
comparison, not six new independent tasks or an independent holdout. Add two fresh
author-designed transfer cases (replica reads and upload idempotency) with Codex
and Opus. Generate these only with the revision to test meaning and unfamiliar
terminology; they do not estimate a comparative effect.

Blind cross-provider comparison uses both A/B orders for the six pairs. Retain the
same personal adoption bar: at least four consistent candidate wins, no consistent
incumbent win, all eight outputs pass author meaning/readability review, all three
native regressions pass, then an installed native smoke and exact resource match.
This is still not statistical superiority or human preference evidence. A reader
may prefer either version even after these checks.

Maximum 24 new calls: eight writes, twelve judgments, three regressions, one installed
smoke. No automatic retries. Missing or conflicting votes remain undecided. Stop
adoption on a material error. Back up 0.2.2 and restore it if installed smoke fails.
Raw data and provider logs stay outside Git. Reused response hashes and scorer code
are pinned here so reuse cannot be mistaken for a new generation.
