# 0.4.3 correction, frozen before calls

0.4.2 failed cross-provider review. Grok correctly identified that the SDK handoff
quoted a planned UI label as current screen text; the implementing assistant had
missed it. Opus preferred the old schema handoff because the new prose lost the
operational names and delayed the urgent paused/read-disabled status. Its metric
review also noted an implicit rather than explicit all-options-fail conclusion.
These findings are retained, not reclassified to pass the candidate.

0.4.3 corrects the example that invited a guessed UI label, explicitly separates
planned labels from current observed text, preserves operational names beside
plain explanations, keeps conditions scannable and requires the actual comparison
conclusion. Trigger, Git, formats and runtime host scope remain unchanged.

Use the same eight known development cases, six reused incumbent responses and
reversed-label cross-provider comparisons. Keep the prior engineering adoption
rule unchanged: at least four concordant wins, no concordant loss, complete
judgments, author meaning/readability pass on all eight, three native regressions,
then installation match and one native installed smoke. These are development
cases, not an independent holdout. No general superiority or human preference is
inferred. The scorer representation correction applies uniformly from the start.

Maximum 24 new calls: 8 generation, 12 judgments, 3 regression, 1 smoke. No automatic
retry. All responses and failed versions are preserved. Restore the backed-up
incumbent if installed verification fails. Raw text and receipts stay outside Git.
