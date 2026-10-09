# Research

Records of hands-on runs of skills and workflows, including this repository's retired products. They do not define
any contract for this repository's products. Each conclusion is tied to the date, versions, and
models it was measured with.

For the decisions around a study and later product changes, see
[learning cases](../learning/README.md). A study's result is not automatically the
reason a product was created or retired.

| Study | Date | What |
| --- | --- | --- |
| [Agent workflow comparison](2026-09-agent-workflow-comparison/README.md) | 2026-09-27 | 9 tools, including superpowers and dryforge, plus plain Claude Code, measured on the same 3 tasks |
| [waygent design and evaluation](2026-09-waygent-eval/README.md) | 2026-09-27 | The `waygent` skill built from the study above, measured 22 times against plain Claude Code and superpowers on a 10-Task job |
| [Pre-SDD Review versus ordinary review](2026-10-pre-sdd-review-eval/README.md) | 2026-10-08–09 | Frozen 6.1.2 versus ordinary review on Sol, Astra, Opus and Grok; protocol ablation, repair, process audit and a bounded 6.1.3 correction |
| [Ponytail value investigation](../learning/cases/2026-10-09-ponytail-value.md) | 2026-10-09 | Pinned 5.1.0 source audit, published benchmark recalculation, scorer and hook probes; Korean record with evidence limits, no live model calls |

- Raw transcripts, provider receipts, and generated task repositories are not committed. Only
  aggregated numbers and grading results are kept.
- The harnesses call live models. `scripts/verify.py` and CI do not run the code in this folder.
