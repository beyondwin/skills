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
| [Korean technical-writing policy](2026-10-ko-clear-writing-eval/README.md) | 2026-10-09 | Supplied-kit reproduction, independent boundary probes and a frozen three-condition Codex/Opus/Grok pilot |
| [Personal Korean technical-writing pilot](2026-10-personal-writing-pilot/README.md) | 2026-10-09 | Personal skill candidate; native discovery and evidence-reading comparison on synthetic repositories |
| [Korean writing readability revision](2026-10-writing-readability/README.md) | 2026-10-09 | Reader-centered revision, masked Codex comparison, Opus/Grok extension and observed-defect repair |
| [Korean writing superiority comparison](2026-10-writing-superiority/README.md) | 2026-10-09 | Frozen three-arm comparison on 12 new tasks, evaluator false positives, two bounded corrections; superiority not established |
| [Familiar Korean personal-writing revision](2026-10-writing-plain-language/README.md) | 2026-10-09 | Human terminology feedback, failed relative comparisons, separate personal-use criteria, native Codex0.5.1 with Opus/Grok audits and installed verification |
| [Ponytail value investigation](../learning/cases/2026-10-09-ponytail-value.md) | 2026-10-09 | Pinned 5.1.0 source audit, published benchmark recalculation, scorer and hook probes; Korean record with evidence limits, no live model calls |

- Raw transcripts, provider receipts, and generated task repositories are not committed. Only
  aggregated numbers and grading results are kept.
- The harnesses call live models. `scripts/verify.py` and CI do not run the code in this folder.
