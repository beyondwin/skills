# Method

## The question

When you already use superpowers, is there a reason to switch to dryforge or another
workflow tool? README claims alone could not settle that, so we ran the same tasks
under the same conditions to the end and compared the results.

## Step 1: static analysis

- Each repository was fetched with `git clone --depth 1`, and we read its README and
  every skill and command file. Commits and dates are in [Tools](tools.md).
- Six tools (mattpocock, gstack, BMAD, Spec Kit, OpenSpec, Ralph) were each handled by
  one subagent. Each agent analyzed the repository, wrote an isolated install script,
  and ran one install check with the haiku model (does the skill list show up).
- superpowers was the 6.4.1 already installed on this machine, used as is.

## Step 2: probe runs

### Ten conditions

Plain Claude Code (control), superpowers, dryforge, workflow-orchestrator, mattpocock,
gstack, BMAD, Spec Kit, OpenSpec, and Ralph. The conditions are defined in
[`harness/conditions.json`](harness/conditions.json).

### Isolation

Every session ran with Claude Code 2.1.280 `claude -p`.

- Model: `opus` (Claude Opus 5.5), the model the user normally uses.
- `--setting-sources project`: user settings, `~/.claude/skills`, and global hooks are
  not read. The superpowers session-start hook is present only in the superpowers
  condition.
- `--plugin-dir`: only that condition's plugin is loaded. Tools that install into the
  project (BMAD, Spec Kit, OpenSpec, gstack, Ralph) were installed inside the task
  repository and recorded as an "install" commit before the run started.
- `--strict-mcp-config`: keeps claude.ai account connectors out. In the pilot, runs
  without this flag had connector sign-in prompts mixed into the answers.
- `--disallowedTools AskUserQuestion`: `-p` mode has no choice UI. Every condition was
  blocked the same way so that all questions come as plain text.
- `--permission-mode bypassPermissions`: used only on throwaway repositories in a
  scratch directory.
- Check: for each condition, haiku was asked to "list the available skills" to confirm
  that only that tool's skills were visible.

### Three tasks

| ID | Repository | First request | What it tests |
| --- | --- | --- | --- |
| S1 | Empty repository | "가계부 CLI 하나 만들어줘" ("Build me a household-budget CLI") | How many of 9 hidden requirements it uncovers from a one-line request |
| S2 | Coupon and shipping-fee module (5 tests) | "쿠폰 두 장까지 같이 쓸 수 있게 해줘" ("Let people use up to two coupons together") | Whether it catches and asks about the conflict between the docs (30% discount cap) and the code (50%), and whether it asks about combination and order rules |
| S3 | Same module with a `>` instead of `>=` bug | "딱 50,000원 주문에 배송비가 붙었대. 고쳐줘" ("An order of exactly 50,000 won got charged shipping. Fix it") | Process and cost for a small fix, and the regression test |

The task repositories are in [`harness/fixtures/`](harness/fixtures/).

### Mock user

A human cannot hold 30 conversations, so a separate model (Sonnet) played the user.

- Each task has a sheet of facts only the user knows ([`harness/personas/`](harness/personas/)).
  Examples from S2: "정률 1장 + 정액 1장만" (only one percent coupon plus one fixed
  coupon), "정률 먼저" (percent first), "상한은 문서의 30%가 맞음" (the docs' 30% cap is correct).
- Rules: answer only what is asked, and do not volunteer facts that were not asked
  about. The exception: if a design shown for approval clearly contradicts the facts,
  correct it as a real user would. These were recorded separately as "user correction".
- Each tool came with the usage order (playbook) given in its docs. For example, with
  dryforge the mock user types `/dryforge:go` when approving the intent document. With
  Spec Kit it types `specify → clarify → plan → tasks → implement → converge` in turn.
- The git rules are on the fact sheet too. For S2: commit to a local branch only; no
  merge, push, or PR.
- The mock user can read repository files (Read, Grep, Glob) so that it can review
  spec documents before approving them.

### Running to the end

[`harness/driver.py`](harness/driver.py) sends the first message, passes the agent's
answer to the mock user, and sends the mock user's reply back with `--resume`. It stops
when the mock user decides the work is done or at 14 turns. Only gstack hit the
14-turn cap, so the isolated gstack reruns used a 30-turn cap (`PROBE_MAX_TURNS=30`).
The first gstack runs were continued in the same session for 16 more turns
([`harness/continue_gstack.sh`](harness/continue_gstack.sh)). For Ralph, once the
requirements conversation ended, the harness ran 2 planning loops and the build loop
(capped at 8 iterations for S1, 6 for S2, 4 for S3) with no human, as its docs describe.

### Judging

[`harness/judge.py`](harness/judge.py) scores in two ways.

1. Hidden deterministic checks import the resulting code directly. S2 checks whether
   "a single 50% coupon is capped at 30%", "existing single-coupon calls still work",
   "free shipping at 50,000 won", and "the docs' '주문당 1장만' (one per order) rule was
   updated". S3 checks the boundary value and that a regression test was added. If the
   result was committed to a branch, the checks run against that commit.
2. An independent judge, an Opus session that took no part in the conversation, runs
   the code in a copy of the repository and scores it against a rubric. Each fact is
   classified as "got by asking / confirmed from docs or code / assumed correctly
   without asking / assumed wrongly / missed". The judge also counts unnecessary
   questions, checks whether verification claims are true, and checks git-rule compliance.

### Fixed during the pilot

- claude.ai connectors leaking in → added `--strict-mcp-config`. Pilot results were discarded.
- Two bugs in the hidden checks: the "1장만" (only one) string check also matched the
  new rule sentence ("정률 1장 + 정액 1장만 허용", one percent plus one fixed allowed),
  and results committed to another branch were not found. Both were fixed and the
  checks were re-applied to every run.
- Projects with a `src/` layout need `PYTHONPATH=src` for tests to run. The hidden test
  check had been counting those as failures; this was fixed.
- Cost: `claude -p --resume` reports `total_cost_usd` as a running total for the
  session. We confirmed this with a 3-turn haiku control (0.0157 → 0.0182 → 0.0207).
  At first we summed the turns and overcounted. Now we take the session's last value
  and only sum loops like Ralph that start a fresh session each time.

## What this study does not prove

- Each condition × task ran once. Model output varies between runs, so a single
  difference should not be read as a fixed property of a tool. Only patterns that
  recurred made it into the conclusions.
- The mock user is not a real person. It sometimes left the usage order (for example,
  in mattpocock S2 it replied "나머지도 진행해줘" ("go ahead with the rest") instead of
  `/to-spec`, which went straight to implementation). Such cases are noted in the results.
- Cost is the `total_cost_usd` Claude Code reports (API-price equivalent, cache
  included). It may differ from subscription usage. Mock-user and judge costs are
  excluded and listed separately.
- gstack called the installed Codex CLI for outside opinions. That cost and its effect
  are not measured.
- gstack keeps records in a state folder outside the task repository. In the first
  runs the tasks shared that folder and their records mixed. We changed the harness to
  give each run folder its own `GSTACK_HOME` and reran S1–S3 one at a time. The gstack
  rows in the tables are the rerun values.
- The tasks are small (one Python module, one CLI). Differences in large repositories,
  multi-day work, or team collaboration were not measured.
- The judge is also a Claude model. The hidden deterministic checks cover part of that gap.
