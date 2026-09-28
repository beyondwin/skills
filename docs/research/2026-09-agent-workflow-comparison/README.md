# Agent workflow comparison (2026-09)

A measured check, not a README comparison, of whether a superpowers user has a
reason to switch to dryforge or another workflow tool.

- Nine tools: superpowers 6.4.1, dryforge 1.3.7, workflow-orchestrator 1.5.0
  (jha0313/skills_repo), mattpocock/skills 1.2.3, gstack 1.91.2.0, BMAD-METHOD 6.12.0,
  Spec Kit (`c00dc05`), OpenSpec 1.13.2, and the Ralph Wiggum loop (`88d488a`). The
  control is plain Claude Code.
- Runs: Claude Code 2.1.280, Opus 5.5. 3 tasks × 10 conditions = 30 runs, each taken to
  the end, plus 4 coexistence runs. Agent cost was $124 in total. The three gstack
  runs are reruns with a separate state folder per run; the first gstack runs were
  discarded because state leaked between tasks.

## Conclusion

**Keep using superpowers.** Nothing we measured is a reason to switch.

- Output quality was about the same across tools. All 10 conditions, plain Claude
  Code included, finished the new-CLI task and the bug-fix task correctly. Only 1 of
  30 runs had a functional defect (mattpocock S2); superpowers had none.
- On the existing-code task (S2, $0.42) and the bug fix (S3, $0.21) superpowers was
  in the cheapest group, alongside the baseline and mattpocock. On the new project
  (S1) it was mid-range at $3.89.
- mattpocock, BMAD, and Spec Kit (bug extension) also ship debugging, review, and
  verify-before-done skills. What sets superpowers apart is that its session-start
  hook turns those skills on without a human asking.
- This repository's `sddx` and `pre-sdd-review` currently take superpowers-shaped
  spec and plan files as input. We did not test whether they accept dryforge's
  `.dryforge/plan.md` (a YAML graph). Replacing the whole tool means re-checking that
  flow first.

We also saw superpowers' weak spots. In S2 it assumed the coupon-combination rule
wrongly instead of asking (the user caught it at design approval). In S1 it asked for
confirmation after every design section, so the human had to reply 11 times.

**Don't replace superpowers with dryforge; keep dryforge alongside it at most.** Call
it with `/dryforge:ready` only for new features or new projects where a mistake is
expensive.

- Good: no wrong assumptions in S2. Its first question was the conflict between the
  docs and the code, and it followed the git instructions in all three tasks.
- Cost: 2.6× (S1), 9.6× (S2), and 15× (S3) the cost of superpowers. It wrote 15–20
  documents per task, and it backs up and then rewrites `CLAUDE.md` and `AGENTS.md`.
  That does not fit a repository like this one, where `AGENTS.md` is maintained by hand.
- Coexistence: with both installed, calling `/dryforge:ready` let dryforge lead.
  Without a command, superpowers took over. We checked only the first turn and did
  not measure interference in the `go` phase.

## If you are in this situation

| Situation | Recommendation | Evidence |
| --- | --- | --- |
| Small bug or config fix | Baseline or superpowers | S3: $0.13–0.21, about 1 minute. Every condition added a regression test |
| Adding a feature to existing code | superpowers | S2: $0.42. It caught the conflict but guessed the combination rule, so read the design carefully at approval |
| Vague new feature where mistakes are expensive | Add dryforge `/ready` | S2: 0 wrong assumptions, asked about the conflict first, git discipline. About 10× the cost and many documents |
| Minimal human effort | workflow-orchestrator or BMAD | S1: 2–3 human replies. BMAD ignored the git instruction and committed to main |
| Deep review of every decision | gstack (with care) | Asks once per decision: 29 replies, 116 min, $36 in S1. Broke the no-push rule in S3. Calls Codex automatically |
| Teams that keep spec documents in the repo | OpenSpec | Cheaper than Spec Kit in S1 and S2 (S2: $1.07 vs $5.21) with fewer human replies. Spec Kit did not ask about the conflict and settled it with its constitution |
| Long unattended runs | Ralph | Automatic after the requirements conversation. Commits and tags main on every iteration; no channel for mid-run instructions |

## Documents

- [Method](method.md): static analysis, isolation, mock user, judging, pilot fixes, limits
- [Tools](tools.md): design, flow, size, and version of the nine tools
- [Results](results.md): per-task tables, recurring patterns, runs to read separately, coexistence
- [HTML report](report.html): all of the above on one page
- [`results/`](results/): aggregate numbers (`summary-main.json`), tables, coexistence log
- [`harness/`](harness/): code to rerun the study. It calls live models, so CI does not run it

## Rerunning

```bash
harness/fetch_tools.sh /tmp/probe-work        # fetch each tool at the measured commit
cd /tmp/probe-work/probe
python3 runner.py 8 s3:vanilla s3:superpowers  # task:condition list, 8 in parallel
./judge_all.sh && python3 aggregate.py main
```

- superpowers uses the 6.4.1 install at `~/.agents/plugins/superpowers`.
- gstack puts `GSTACK_HOME` inside each run folder (`$RUN` in `conditions.json`).
- Raw transcripts (`runs/`) and logs are not committed (`harness/.gitignore`).
