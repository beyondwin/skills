# Skill trigger eval (2026-10-02)

Does a plain request load the right skill, and only that skill, when the host has the user's
whole skill set installed? This applies the eval-design advice in Anthropic's
"Automating eval design and hillclimbing with Claude" (claude.dev, 2026-09-28): tasks that
mirror production, near-misses drawn from the skills that actually compete, held-out cases,
two repeats to see noise, and no edits to a description unless the baseline has headroom.

## Setup

- **Skills under test:** the four with implicit activation: how-it-works, pre-sdd-review,
  korean-writing-editor and image-workbench. sddx and waygent start only on `/sddx` or
  `/waygent`, so a trigger eval would not tell us anything about them.
- **Hosts:**
  - Every skill's supported host, plus pre-sdd-review on Claude Code. Its host matrix says
    Codex only, but the user's own Claude Code sessions call it, so that cell is
    informational.
  - korean-writing-editor and image-workbench are turned off in the user's Claude Code
    (`skillOverrides`), so they ran on Codex only.
- **Claude Code environment:** a copy of the user's environment.
  - Every skill in `~/.claude/skills` except the ones `skillOverrides` turns off.
  - The eli5, claude-md-management and commit-commands plugins.
  - The superpowers SessionStart hook.
  - `opus` at effort high (the user's settings).
  - `--setting-sources project --strict-mcp-config`.
- **Codex environment:**
  - Every skill in `~/.agents/skills` and `~/.codex/skills`, and the user's plugins.
  - `gpt-6-astra` at high. `config.toml` names `gpt-6.1-sol`/low, but 12 of the user's last
    15 sessions ran astra/high, and a ChatGPT account rejects 6.1-sol.
  - Memories are off and every call is `--ephemeral`, so no call sees another.
- **Pinning:** the skill set is copied once per variant into `harness/homes/`, and every call
  copies from there. The target SHA-256 is recorded in `results/trigger-base-totals.json`:
  - how-it-works `4a5751e9`
  - pre-sdd-review `df71213a`
  - korean-writing-editor `16ce16cb`
  - image-workbench `95c1a397`
- **Fixture:** a fresh synthetic repository for every call (`harness/fixture.py`): a small
  rate-limited job queue, an approved spec and plan with a wrong test command, brand notes,
  PNG assets, and a CSV.
- **Prompts:** 12 positives and 12 near-misses per skill (`harness/prompts.json`).
  - They copy the style of real requests (short, Korean, typos, no skill name), taken
    locally from the user's own sessions. Only the written paraphrases are committed.
  - Near-misses are the requests the competing skills should take: ELI5, debugging, review,
    translation, a data chart, writing a spec or plan, implementing, proofreading, and so on.
  - Per skill and kind, 4 of the 12 are held out (seeded split).
- **Measurement:**
  - A call stops when the target skill loads (Claude Code: a `Skill` tool call; Codex: a
    command that opens `<skill>/SKILL.md`), when the host finishes, or after 180 s.
  - Only which skills loaded is kept. Task quality is not graded.
- **Repeats:** two per prompt.

## Results

| Host | Skill | Positives loaded | Near-misses that loaded it |
| --- | --- | --- | --- |
| Claude Code | how-it-works | 24/24 | 0/24 |
| Claude Code | pre-sdd-review | 24/24 | 0/24 |
| Codex | how-it-works | 24/24 | 0/24 |
| Codex | pre-sdd-review | 24/24 | 0/24 |
| Codex | korean-writing-editor | 24/24 | 0/24 |
| Codex | image-workbench | 24/24 | 0/24 |

- **Totals:**
  - Claude Code: 48/48 hits and 0/48 false triggers. The 95% Wilson lower bound for 48/48 is 0.93.
  - Codex: 96/96 hits and 0/96 false triggers (lower bound 0.96).
  - The held-out cases score the same as the train cases. Both repeats agree on every prompt.
- **Time to load:** the median is 4.3 s on Claude Code and 16.3 s on Codex. On Codex,
  `using-superpowers` loads first on almost every request.
- **What the near-misses loaded instead:** mostly the skill they were written for.
  - eli5 for the ELI5 request.
  - dataviz on Claude Code for the sales chart.
  - writing-plans for "write the plan".
  - brainstorming for "write a spec" and "brainstorm".
  - code-review for the diff review.
  - executing-plans for "implement the plan".
  - systematic-debugging for "fix the failing tests".
  - archify for the Mermaid diagram.
- **Codex positive cases:** image-workbench loaded together with `imagegen` on generation
  requests, as intended.

## Decision

The baseline has no headroom: every cell is at 100%. The article's rule fits: when a
baseline is saturated, a hillclimb should go after cost rather than quality, and an edit
here could only be measured as a regression. No description changed. New contract tests
keep every description trigger-only (sddx's `test_description_is_trigger_only`, now in all
six products).

## Limits

- **Fresh sessions only.** Every call is one turn in a fresh session. The user's real
  how-it-works calls mostly come mid-conversation, as "I don't get it, explain it simply"
  after a dense answer. Only one prompt here stands in for that, by pasting a dense
  paragraph first.
- **Who wrote the prompts.** The same author wrote both sides. Clear-cut cases were chosen,
  in line with the article's two-experts-agree rule, so the hard border cases are not
  measured: a bare "쉽게 설명해줘", or "그림으로" about a chart.
- **Sample size.** n = 2 repeats; 24 prompts per skill.
- **Cost.** It was not recorded: calls stopped at the trigger have no result line.
  Pre-stop costs on Claude Code are cents per call.
- **Codex isolation.** With memories off, Codex runs without the user's memory store, which
  real sessions have.

## Product probes run alongside

The same harness folder holds three regression probes for this round's text edits.

- **`format_probe.py`** compared how-it-works 3.0.2 (`4a5751e9`) and 3.0.3 (`91fa3aa9`).
  - It ran on Claude Code with the explicit `/how-it-works`: 3 Korean DNS prompts and
    1 English rebase prompt per model, on opus/high, sonnet and haiku.
  - It checks the Mermaid fence, matching hop ids, the `# … · <rung>` title, the four
    headings, and the next-move line.
  - Both texts scored 4/4 on every check for every model.
  - The reference reads (`references/output.md`) were 0/4 → 0/4 on opus, 3/4 → 4/4 on
    sonnet, and 0/4 → 3/4 on haiku. That is inside the noise at n = 4.
  - Results: `results/hiw-format-probe.json`.
- **`preserve_probe.py`** compared korean-writing-editor 2.0.6 (`16ce16cb`) and 2.0.7
  (`d8ccefa5`).
  - It ran on Codex gpt-6-astra/high with an isolated home holding only that skill: six
    sentences, each carrying one meaning invariant (negated obligation, modality, quantity
    with attribution, partial negation, a limit, negation with attribution), two repeats each.
  - Both texts kept every invariant, 12/12.
  - In 1 of the 12 runs on 2.0.7, the model answered without opening SKILL.md.
  - Results: `results/kwe-preserve-probe.json`.
- **`psr_probe.py`** compared pre-sdd-review 6.1.1 (`df71213a`) and 6.1.2 (`d621401f`) end
  to end on Codex: two single-plan runs and one two-plan campaign per text.
  - Both texts repaired the planted `npm test` in 3/3 runs, wrote a verdict, a `Handoff:` on
    every non-READY, and one recorder record per plan.
  - Verdicts split between BLOCKED and READY on one real gap in the fixture spec (no default
    delays) for both texts.
  - 6.1.2 opened the moved `references/campaign.md` in the campaign run only.
  - Results: `results/psr-probe.json`; details in the product's `testing.md`.

## Re-running

```bash
cd docs/research/2026-10-skill-trigger-eval/harness
python3 run.py <variant> claude --reps 2 --parallel 3
python3 run.py <variant> codex --reps 2 --parallel 6
python3 score.py <variant>
```

These calls run live models. `scripts/verify.py` and CI do not run this folder. Raw
streams, homes and runs are not committed (`harness/.gitignore`).
