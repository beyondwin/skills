# Research

Records of hands-on runs of skills and workflows, including this repository's retired products. They do not define
any contract for this repository's products. Each conclusion is tied to the date, versions, and
models it was measured with.

For the decisions around a study and later product changes, see
[learning cases](../learning/README.md). A study's result is not automatically the
reason a product was created or retired.

| Study | Date | What |
| --- | --- | --- |
| [First-image visual direction with Grok alone](2026-10-image-first-direction/README.md) | 2026-10-23 | Four fresh one-call pairs: candidate 1 win, 2 losses, 1 disagreement; craft 4.30 vs 4.25, confirmed compliance 4/4 vs 3/4; no product change |
| [Fresh image transfer and one stop-rule repair](2026-10-image-fresh-transfer/README.md) | 2026-10-23 | Four new requests: no-skill 4/4, 2.1.6 3/4, development repair 2.1.7 4/4; valid retention ties, count/occlusion failure denominators zero; no superiority claim |
| [Focused image repair and final delivery](2026-10-image-focused-repair/README.md) | 2026-10-23 | 2.1.6 fixes one reproduced Codex false rejection (2/3→3/3); three final assets pass critical/composition checks, clay texture unverified; Grok autonomous review still fails |
| [Evidence-based image review redesign](2026-10-image-evidence-review/README.md) | 2026-10-23 | G not adopted: fresh supplemental scores improved from 21/23 to 23/23 twice, but adoption gates failed and one execution-scope failure closed the official score |
| [Image review and correction repair](2026-10-image-review-repair/README.md) | 2026-10-22–23 | Retention-only 2.1.5 ties baseline at 3/3 usable delivery; selection accuracy regresses 10/12 to 9/12, broader repair criteria fail |
| [Image delivery within a two-call budget](2026-10-image-delivery/README.md) | 2026-10-22 | Three new briefs, all seven candidates judged, and five read-only selection probes; inventory correction rejected and self-review limits documented |
| [Image generation quality comparison](2026-10-image-quality/README.md) | 2026-10-22 | Ordinary Grok versus image-workbench, blinded first-candidate judgments, rejected prompt expansion and targeted constraint repairs; no overall craft advantage established |
| [Agent workflow comparison](2026-09-agent-workflow-comparison/README.md) | 2026-09-27 | 9 tools, including superpowers and dryforge, plus plain Claude Code, measured on the same 3 tasks |
| [waygent design and evaluation](2026-09-waygent-eval/README.md) | 2026-09-27 | The `waygent` skill built from the study above, measured 22 times against plain Claude Code and superpowers on a 10-Task job |
| [Pre-SDD Review versus ordinary review](2026-10-pre-sdd-review-eval/README.md) | 2026-10-08–09 | Frozen 6.1.2 versus ordinary review on Sol, Astra, Opus and Grok; protocol ablation, repair, process audit and a bounded 6.1.3 correction |
| [Korean technical-writing policy](2026-10-ko-clear-writing-eval/README.md) | 2026-10-09 | Supplied-kit reproduction, independent boundary probes and a frozen three-condition Codex/Opus/Grok pilot |
| [Personal Korean technical-writing pilot](2026-10-personal-writing-pilot/README.md) | 2026-10-09 | Personal skill candidate; native discovery and evidence-reading comparison on synthetic repositories |
| [Korean writing readability revision](2026-10-writing-readability/README.md) | 2026-10-09 | Reader-centered revision, masked Codex comparison, Opus/Grok extension and observed-defect repair |
| [Korean writing superiority comparison](2026-10-writing-superiority/README.md) | 2026-10-09 | Frozen three-arm comparison on 12 new tasks, evaluator false positives, two bounded corrections; superiority not established |
| [Readable personal-skill rename](2026-10-readable-rename/README.md) | 2026-10-09 | Current personal name and installation: Readable 0.6.0; unchanged writing instructions, offline rename verification |
| [Familiar Korean personal-writing revision](2026-10-writing-plain-language/README.md) | 2026-10-09 | Human terminology feedback, failed relative comparisons, separate personal-use criteria, native Codex0.5.1 with Opus/Grok audits and installed verification |
| [Ponytail value investigation](../learning/cases/2026-10-09-ponytail-value.md) | 2026-10-09 | Pinned 5.1.0 source audit, published benchmark recalculation, scorer and hook probes; Korean record with evidence limits, no live model calls |

- [Anti-slop skill source audit](2026-10-slop-skill-audit/README.md): pinned sources,
  gate and lint counterexamples, and bounded Korean editor changes; no model calls.

- Raw transcripts, provider receipts, and generated task repositories are not committed. Only
  aggregated numbers and grading results are kept.
- The harnesses call live models. `scripts/verify.py` and CI do not run the code in this folder.
