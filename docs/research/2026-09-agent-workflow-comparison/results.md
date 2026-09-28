# Results

2026-09-27, Claude Opus 5.5, 10 conditions × 3 tasks = 30 runs. The method is in
[Method](method.md) and the raw data in [`results/summary-main.json`](results/summary-main.json).

## The baseline first

**Skills did not change the success rate.** Plain Claude Code (no skills) produced
working results on all three tasks.

- S1 (household-budget CLI): in all 10 conditions the 5 required features actually
  worked, using only the standard library, and the tests passed. The judge ran the CLI
  to confirm.
- S3 (boundary bug): all 10 conditions found the cause and added a regression test.
- S2 (coupon stacking): 8 of 10 conditions passed all 5 hidden checks. The other two
  are described below.

So what the tools changed in this comparison was the **process**: how much they ask,
how many times a human has to reply, how much money and time it takes, what they leave
in the repository, and whether they follow git instructions. This may be because the
tasks are small and the model is strong. Large repositories may differ.

## Per-task tables

Cost is the API-equivalent cost Claude Code reports. Resumed sessions report a running
total, so we took the last value. "Human replies" is the number of messages the user
sent (first request included). "Questions" was counted by the mock user and is approximate.

### S1 — a new household-budget CLI from a one-line request

| Tool | Cost | Time | Human replies | Questions | Confirmed by asking | Right without asking | Wrong assumptions | Missed | Tests | New docs/config | Subagents |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| Baseline (control) | $0.31 | 1.8 min | 4 | 1 | 0 | 8 | 0 | 1 | pass | 1 | 0 |
| superpowers | $3.89 | 17.4 min | 11 | 11 | 9 | 0 | 0 | 0 | pass | 4 | 1 |
| dryforge | $10.19 | 34.5 min | 6 | 20 | 9 | 0 | 0 | 0 | pass | 20 | 10 |
| workflow-orchestrator | $5.23 | 21.9 min | 2 | 6 | 7 | 2 | 0 | 0 | pass | 3 | 6 |
| mattpocock | $4.39 | 16.6 min | 9 | 27 | 9 | 0 | 0 | 0 | pass | 5 | 2 |
| gstack | $35.96 | 116.3 min | 29 | 28 | 9 | 0 | 0 | 0 | pass (pytest)* | 5 | 27 |
| BMAD | $2.93 | 10.4 min | 3 | 5 | 2 | 7 | 0 | 0 | pass | 2 | 4 |
| Spec Kit | $7.58 | 22.7 min | 9 | 11 | 2 | 7 | 0 | 0 | pass | 12 | 0 |
| OpenSpec | $3.48 | 12.7 min | 6 | 5 | 7 | 1 | 0 | 1 | pass | 9 | 0 |
| Ralph | $9.39 | 34.6 min | 2 | 14 | 9 | 0 | 0 | 0 | pass | 11 | 3 |

### S2 — coupon stacking in an existing module (hidden 30%/50% conflict)

| Tool | Cost | Time | Human replies | Questions | Asked about 30/50 conflict | Wrong assumptions | Hidden checks | Tests | git rules | New docs/config | Subagents |
| --- | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- | ---: | ---: |
| Baseline (control) | $0.27 | 1.9 min | 3 | 3 | yes | F1 | 5/5 | pass | kept | 0 | 0 |
| superpowers | $0.42 | 2.1 min | 5 | 4 | yes | F1 | 5/5 | pass | kept | 0 | 0 |
| dryforge | $4.07 | 12.2 min | 5 | 10 | yes | none | 5/5 | pass | kept | 15 | 5 |
| workflow-orchestrator | $1.64 | 6.2 min | 3 | 6 | yes | none | 5/5 | pass | fixed after correction | 0 | 6 |
| mattpocock | $0.52 | 3.6 min | 4 | 9 | yes | F5 | 2/5 | pass | kept | 1 | 0 |
| gstack | $14.48 | 42.1 min | 19 | 18 | yes | none | 5/5 | pass | kept | 1 | 13 |
| BMAD | $1.99 | 5.6 min | 3 | 4 | yes | none | 5/5 | pass | broken | 2 | 4 |
| Spec Kit | $5.21 | 17.1 min | 13 | 6 | no | none | 5/5 | pass | kept | 12 | 0 |
| OpenSpec | $1.07 | 4.7 min | 6 | 7 | yes | none | 5/5 | pass | kept | 6 | 0 |
| Ralph | $2.13 | 8.5 min | 3 | 12 | yes | none | 5/5 | pass | broken | 9 | 0 |

### S3 — the 50,000-won boundary bug

| Tool | Cost | Time | Human replies | Questions | Hidden checks | Tests | New docs/config | Subagents | Final location |
| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- |
| Baseline (control) | $0.13 | 0.7 min | 2 | 1 | 4/4 | pass | 0 | 0 | main |
| superpowers | $0.21 | 0.7 min | 2 | 1 | 4/4 | pass | 0 | 0 | main |
| dryforge | $3.14 | 8.6 min | 4 | 4 | 4/4 | pass | 20 | 5 | main |
| workflow-orchestrator | $0.58 | 2.2 min | 2 | 3 | 4/4 | pass | 0 | 3 | main |
| mattpocock | $0.20 | 1.1 min | 3 | 1 | 4/4 | pass | 1 | 0 | main |
| gstack | $1.73 | 5.7 min | 4 | 2 | 4/4 | pass | 0 | 1 | branch (broke no-push) |
| BMAD | $0.60 | 1.7 min | 1 | 0 | 4/4 | pass | 2 | 1 | main |
| Spec Kit | $0.47 | 2.2 min | 5 | 4 | 4/4 | pass | 4 | 0 | main |
| OpenSpec | $0.66 | 2.1 min | 5 | 1 | 4/4 | pass | 5 | 0 | branch |
| Ralph | $0.89 | 3.8 min | 2 | 9 | 4/4 | pass | 5 | 0 | main |

## Recurring patterns

A difference seen once may be chance, so only patterns that repeated across two or
more tasks are listed.

1. **For small fixes, the baseline and light tools were cheapest.** In S3 the baseline,
   superpowers, and mattpocock cost $0.13–0.21 and took about a minute. dryforge cost
   $3.14, took 8.6 minutes, and created 20 documents, because on its first cycle it
   generates the whole `CLAUDE.md`, `AGENTS.md`, and `docs/` harness. dryforge's README
   says it is not needed for small, already-clear fixes, and the harness is a one-time
   cost per repository. OpenSpec and Spec Kit also left 4–5 spec documents for a
   one-character fix.
2. **dryforge left the most documents in all three tasks (15–20).** In return it made
   no wrong assumptions in S2, asked about the 30%/50% conflict as its first question,
   committed to a feature branch, and asked before merging. The conditions that
   followed the git instructions in all three tasks without being corrected were the
   baseline, superpowers, dryforge, mattpocock, OpenSpec, and Spec Kit.
3. **Almost every condition caught the S2 30%/50% conflict.** Nine conditions asked the
   user. Spec Kit did not ask; it chose 30% from the "docs are right" principle in the
   constitution it had generated. The result was correct, but the tool made a decision
   that belonged to the user. The baseline agent asked too, but only after finishing
   the implementation.
4. **Only the baseline and superpowers wrongly assumed the "no two of the same type"
   rule without asking.** Both guessed "no duplicate code". superpowers classified the
   task as bounded and asked one question at a time, but never asked about the
   combination rule. The user corrected it at design approval.
5. **Even when tools asked, their recommended option was often wrong.** In S2, dryforge,
   mattpocock, OpenSpec, and Spec Kit asked about combination or order but recommended
   the option opposite to the user's intent. workflow-orchestrator's recommendation was
   explained so vaguely that the judge flagged it. The mock user answered from the
   facts, but a real user who just says "go with the recommendation" ends up where a
   guess would. A human reading and choosing matters as much as question quality.
6. **workflow-orchestrator, Ralph, and BMAD needed the least human effort.** In S1 they
   took 2–3 human replies. superpowers took 11 because it confirmed each design section,
   mattpocock 9 because of long question rounds, and Spec Kit 9 because each phase
   needs a typed command. gstack asked once per decision and took 29.
7. **gstack's planning phase is very long.** The gstack rows are reruns with a separate
   state folder per run (the first runs mixed records across tasks; see "Runs to read
   separately" below). S1 took 29 turns, 116 minutes, and $35.96. It confirmed all 9
   facts by asking and made no wrong assumptions. S2 took 42 minutes and $14.48, going
   office-hours → plan review → build → `/review`, and passed 5/5 hidden checks. It asked
   about the docs-vs-code 30/50 conflict in its first reply. But it asked many process
   questions (searching learning records, the requester, web search, Codex review), so
   the human replied 18 times. In the S1 plan review and the S3 `/review` it called the
   installed Codex CLI for an outside opinion.
8. **Some tools committed straight to main.** The S2 instruction was "commit to a local
   branch only". BMAD committed to main without asking. workflow-orchestrator committed
   to main and moved the commit when the user pointed it out. In the isolated reruns
   gstack kept the rule in S2, but in S3 it broke "no push", pushed to the local origin,
   and deleted it after being corrected. Ralph's loop has no channel for mid-run
   instructions, so it commits to main and creates tags. That is a property of its
   structure rather than a mistake.

## Runs to read separately

- **mattpocock S2 (hidden checks 2/5):** it renamed the existing `apply_coupon` to
  `apply_coupons`, which broke existing single-coupon calls. In this run, though, the
  mock user did not follow the documented order (`/to-spec` → `/implement`) and replied
  "나머지도 진행해줘" ("go ahead with the rest"). So implementation started without the
  spec step. This is hard to blame on the tool alone.
- **gstack first runs (contaminated, excluded from the tables):** in the first 30 runs,
  gstack S1–S3 shared one state folder outside the task repository. Every task
  repository was named `repo`, so the S1 judge noted that records from another project
  (coupon discounts) showed up, and S2 ran after losing part of its earlier planning
  record and ended at 4/5 hidden checks (coupon stacking not implemented). This was an
  isolation defect in my harness. I fixed the harness to give each run its own
  `GSTACK_HOME` and reran S1–S3 one at a time. S2 reached 5/5, and in S1 the wrong
  assumption of recommending Go went away. The original values are kept under
  `contaminated_original` in `results/summary-main.json`.
- **gstack S1 tests:** written for pytest, so the harness's unittest check did not run
  them. The judge reproduced 208 passing tests by hand (`pass (pytest)*` in the table).
- **Ralph:** its loop iteration reports were in English because the original prompts
  are in English. In the S1 requirements phase it put unneeded topics into the JTBD
  draft, and the user had to filter them.

## Coexistence experiment (S4)

superpowers 6.4.1 and dryforge 1.3.7 were loaded together and only the first turn on
the S2 repository was observed. The log is [`results/s4-coexist.json`](results/s4-coexist.json).

| First message | Runs | superpowers hook injected | Skill that actually ran | Behavior |
| --- | ---: | --- | --- | --- |
| `/dryforge:ready 쿠폰 두 장까지…` ("up to two coupons…") | 2 | yes | dryforge ready only | dryforge-style questions (conflict, combination, totals) |
| `쿠폰 두 장까지…` ("up to two coupons…", no command) | 2 | yes | superpowers:brainstorming | classified as bounded, then a design in chat |

- Explicitly calling `/dryforge:ready` let dryforge lead even with the superpowers hook present.
- Without a command, superpowers took over and dryforge did not start on its own
  (`disable-model-invocation: true`).
- We did not check whether superpowers' TDD and verification skills interfere in the `go` phase.

## Cost totals

- Agents $123.80, mock user $9.15, judging $7.16, 30 runs (the 3 gstack runs use the isolated rerun values)
- The 3 contaminated first gstack runs ($35.76) are excluded from the total.
- 4 coexistence runs: $1.18. Per-tool install checks (haiku) and the pilot were counted
  separately and are not in the total.
- Each cost comes from a single run, so we read differences as meaningful only when
  they were several-fold or larger.
