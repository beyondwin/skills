# Research

Records of hands-on runs of skills and workflows from other repositories. They do not define
any contract for this repository's products. Each conclusion is tied to the date, versions, and
models it was measured with.

| Study | Date | What |
| --- | --- | --- |
| [Agent workflow comparison](2026-09-agent-workflow-comparison/README.md) | 2026-09-27 | 9 tools, including superpowers and dryforge, plus plain Claude Code, measured on the same 3 tasks |
| [waygent design and evaluation](2026-09-waygent-eval/README.md) | 2026-09-27 | The `waygent` skill built from the study above, measured 22 times against plain Claude Code and superpowers on a 10-Task job |

- Raw transcripts, provider receipts, and generated task repositories are not committed. Only
  aggregated numbers and grading results are kept.
- The harnesses call live models. `scripts/verify.py` and CI do not run the code in this folder.
