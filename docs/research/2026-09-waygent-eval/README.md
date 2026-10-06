# waygent design and evaluation (2026-09)

`waygent` is a light implementation skill that wraps a model. This folder records where its
design came from and how it did when we ran it.

- Skill: [`skills/waygent/SKILL.md`](../../../skills/waygent/SKILL.md) (measured as 0.1.0, 0.2.0, 0.3.0, and 0.3.2 routing cells; each measured copy was under 140 lines)
- Design basis: the 30 runs in the [agent workflow comparison](../2026-09-agent-workflow-comparison/README.md),
  the user's own v26/v27 comparison, and independent designs from four models (Opus 5.5,
  Fable 5.1, Grok 4.7, GPT-5.6 Sol)
- Evaluation: one 10-Task plan job, 13 condition-model cells, 22 runs (plus 2 separate pilot
  runs). Claude Code 2.1.280 (opus, fable) and Cursor Agent 2026.09.23 (grok-4.7-high), plus
  3 runs on Codex 0.154.0 (gpt-5.6-sol high) and 1 opus run with revised wording

## Findings

1. **At this scale the output was nearly the same without a harness.** Plain Claude Code
   (opus) passed 63 of 64 hidden tests in 6.5 minutes for $1.44. superpowers passed 64 for
   $15.38 in 87 minutes. With a well-written plan and design doc, the model gets almost
   everything right on its own.
2. **The difference was one hidden defect.** When a deleted prompt is re-created, the old form
   overwrites it. All 5 runs where a single session implemented everything left this defect.
   Runs with a fresh implementer and a review per Task fixed it in 11 of 14. In the 6 runs
   where we could read the progress file, the review found the defect every time; whether it
   got fixed came down to the main agent's judgment.
3. **At this scale, review per Task only doubled the cost.** The variant with only a final
   review gave the same quality at half the cost ($4.02 vs $7.50) and half the time (17.5 vs
   33.6 minutes), and had the smallest main context (55k tokens, vs 69k for plain). Larger
   plans may differ, so the skill's default stays review per Task, as requested. Removing
   step 4 turns it into final-review-only.
4. **Resume and coexistence worked.** After a forced session kill it did not redo finished
   Tasks, and with superpowers also installed, `/waygent` stayed in charge.
5. **It also ran on Codex.** gpt-5.6-sol high finished all 10 Tasks (63/64, 62/64). The
   orchestrator did not know its own model name, so we changed the skill to leave the model
   unset and inherit it ([results, section 11](results.md)).
6. **Switching models was expensive.** fable cost 2.8-3.5x as much as opus for the same result.
   Cursor grok-4.7 followed the skill as written but was very slow.
7. **0.2.0 on a multi-layer app task (n=6 per condition).** When the design stated the rules,
   every condition caught every trap. With the rules left out, vanilla missed a trap in 3 of 6
   runs, waygent 0.1.0 in 1 of 6, and 0.2.0 in 0 of 6. Against 0.1.0, 0.2.0 cost about a third
   more and took about 60% longer (means of 6). The one 0.1.0 miss came from the "note for user"
   exit that 0.2.0 closed; 0 vs 1 of 6 is too close to call ([results, section 12](results.md)).

8. **0.3.0 (10 app2 runs, 2 library runs, 180 decision-probe calls).** One trap was missed:
   a final reviewer questioned a correct billing ruling, and the fix went in without
   re-review. Rules written to stop that did nothing (B) or stopped it but also parked a
   correct Task 1 High 25-30% of the time (C), so none shipped. Cost and time were about 19%
   and 26% below 0.2.0, two thirds of it in the final phase, where Lows are no longer fixed.
   A resume right after a commit ran the missed review. `progress.md` now shows each step's
   model and effort ([results, section 13](results.md)).

9. **Model routing cells (20 app2 runs, rules written before the batch).** A final reviewer on
   opus/xhigh instead of fable cut final-review cost from $1.69 to $1.08 with no loss.
   Claude Code's Agent tool cannot set effort, so 0.4.0 ships it as an agent definition.
   Per-task reviewers on opus/high were not adopted (one real hidden failure, fewer fixes).
   Sonnet implementers were $0.74 cheaper with no loss, measured at ceiling and at an effort
   the shipped text could not set, so nothing changed. Base's one 11/12 was a scorer artifact
   ([results, section 14](results.md)).

## What went into the skill and what was left out

| Included | Evidence |
| --- | --- |
| One fresh implementer per Task, a short brief (about 1,300 characters in 0.1.0, about 2,000 now) + one shared guide | v27 was 16% faster and 37% cheaper than v26. All four models recommended it |
| Tests first (implement after seeing the failure) | User requirement. Every run left 53-195 of its own tests |
| One review per Task, no re-review | User requirement. v26's review round trips took 2.4 hours |
| One final full review | In v26 only the final review caught cross-task problems. In this task too, the final review alone caught the same defect |
| When fixing, try the smallest fix that keeps the plan's names and signatures first | The judgment that separated fixed runs from unfixed runs in this evaluation |
| Reject High and Medium findings only after trying to reproduce them | The 1 run in this evaluation where the main agent rejected a correct finding |
| Resume from a progress file and commit trailers | Resumed without duplicates after a forced kill. Measured with `.git/waygent/`, then moved to a self-ignoring `.waygent/` like superpowers ([model routing and record location](model-routing.md)) |
| Pin the same model; stop at the rate limit | In v26 the stretch on a cheaper model wasted 5 hours and $128 |
| Only the final review and retries after failure go one tier up | The 9-harness survey and this evaluation ([model routing and record location](model-routing.md)). Quality effect not measured; the routing cells measured cost only ([results, section 14](results.md)) |
| No commits on main/master, no push or PR | In the previous comparison BMAD, Ralph, and others committed to main |

Left out: brainstorming and spec stages, per-Task brief and report files, re-review loops,
parallel implementers, human confirmation per Task, doc generation, and edits to `CLAUDE.md`
or `AGENTS.md`.

## Documents

- [Method](method.md): design basis, the four model analyses, task, conditions, isolation, grading, limits
- [Results](results.md): per-condition tables, defects, review cost, context, resume, coexistence, Cursor, Codex
- [Model routing and record location](model-routing.md): orchestrator, implementer, and reviewer models across the 9 harnesses; record location
- [analysis/](analysis/): the four models' original design proposals and the shared prompt
- [results/](results/): per-run numbers as JSON
- [harness/](harness/): task, hidden tests, reference implementation, driver, grader

## Re-running

```bash
cd docs/research/2026-09-waygent-eval/harness
BENCH_TAG=mine python3 bench.py vanilla opus 1      # condition model run
BENCH_TAG=mine python3 bench.py waygent opus 1
BENCH_TAG=mine python3 bench.py waygent sol 1       # Codex (gpt-5.6-sol high)
BENCH_TAG=mine ./run_batch.sh 4 jobs-main.txt        # several at once
BENCH_FIXTURE=app2 BENCH_TAG=mine ./run_batch.sh 4 jobs-app2.txt   # multi-layer app task
python3 judge.py mine                                # blind defect grading (needs codex)
python3 aggregate.py mine && python3 summarize.py mine
```

- This calls live models. `scripts/verify.py` and CI do not run the code in this folder.
- The superpowers condition uses `~/.agents/plugins/superpowers` (6.4.1).
- Raw transcripts (`runs/`), logs, and grading copies are not committed (`harness/.gitignore`).
