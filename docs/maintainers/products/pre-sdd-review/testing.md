# pre-sdd-review testing

This document sets how far each kind of check proves anything: contract checks
that run without a model, small synthetic fixtures, and optional live checks
that call a real model. Provider-free checks do not measure real review quality;
bounded live comparisons below keep their own scope and limitations.

Provider-free tests and fixtures live in `tests/products/pre-sdd-review/`.

## Provider-free evidence

Run the product contract with no provider credentials and no model calls.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests/products/pre-sdd-review -p 'test_c*.py' -v
```

This runs `test_contract.py` (package identity, instructions, fixtures,
activation boundary) together with `test_campaign_schedule.py` (discovery
waves, serial repairs, stale propagation). It does not include the evidence
suite. It does not prove live review, semantic quality, or equal support on
other hosts.

The `evidence/evidence.py` recorder contract runs as a separate provider-free
stage. It checks the schema 5 checkout binding, refusal of old schema 2, 3, and 4
records (`schema-unsupported`), mutation locks, quarantine of damaged records,
the six commands, and summary observation counts. The recorder runs as
`python3 skills/pre-sdd-review/evidence/evidence.py` and is not installed.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests/products/pre-sdd-review/evidence -p 'test_*.py' -v
```

This stage calls no network or provider, and adds no database or index.

The schema 5 document checks in `test_contract.py` are only consistency
evidence: they check that the installed instructions, the recorder guide, and
the maintainer contract describe the same lifecycle. The evidence suite owns
proof of real recorder behavior. This approved scope calls no provider or real
model, so real model review quality is `not_measured`.

## Fixture boundary

`cases.json` owns exactly fifty-four cases covering activation, default flow,
review-only, verdicts, risk, freshness, evidence, and near-miss requests.
`fixtures/` owns exactly nine synthetic repositories:
`ready`, `missing-coverage`, `false-verification`, `runtime-removal`,
`repair-induced-schema-consumer`, `state-machine-vacuous-pass`,
`conditional-edit-surface`, `missing-command` (a `repo-reality` finding
fixed by a plan edit, so `IMPORTANT`), and `open-product-decision` (a choice
the design leaves open, so `BLOCKER` and `BLOCKED`). Each holds only `design.md`, `plan.md`,
`repository.json`, `expected.json`.

Fixtures are a bounded synthetic contract, not a corpus. Never store user
documents, private prompts, credentials, transcripts, or full model responses
in fixtures, test logs, or committed live records.

### Case inventory

- `default-auto-improve`
- `explicit-review-only`
- `ready-zero-findings`
- `missing-spec-coverage`
- `nonexistent-command`
- `extension-collision`
- `false-positive-smoke`
- `task-interface-order`
- `runtime-removal-risk-review`
- `third-review-role`
- `unmapped-repairable-finding`
- `unmapped-authority-finding`
- `stale-document-hash`
- `required-base-not-in-head`
- `ambiguous-multiple-plans`
- `evidence-cli-recorded`
- `evidence-cli-unavailable`
- `evidence-review-only`
- `evidence-resolution-blocked`
- `evidence-outcome-optional`
- `summary-before-start`
- `serialize-split-plans`
- `zero-findings-skip-closure`
- `repair-pass-accounting`
- `red-flag-seeded-retry`
- `red-flag-anomalous-ready`
- `blocked-verdict-restarts`
- `near-miss-write-spec`
- `near-miss-write-plan`
- `near-miss-code-review`
- `near-miss-release-review`
- `ledger-required-for-multiple-plans`
- `baseline-reconstruction-required`
- `partial-closure-not-a-new-finding`
- `degraded-handoff-not-reused`
- `zero-findings-but-stale`
- `later-design-repair-stales-earlier-plan`
- `closure-requires-repair-diff`
- `host-limit-waves-not-reuse`
- `head-break-no-ready`
- `no-automatic-second-campaign`
- `residual-pass-closes-small-remainder`
- `open-blocker-forces-blocked`
- `repair-last-no-ready`
- `unanswered-decision-no-redispatch`
- `three-new-decisions-return-to-design`
- `continuation-skips-discovery`
- `continuation-after-committed-docs`
- `continuation-needs-docs-only-diff`
- `continuation-needs-recorded-run`
- `focused-only-degraded-continues`
- `continuation-after-recorded-decision`
- `reviewer-starts-without-context`
- `fix-handoff-continues`

### Fixture inventory

- `conditional-edit-surface`: `design.md`, `expected.json`, `plan.md`, `repository.json`
- `false-verification`: `design.md`, `expected.json`, `plan.md`, `repository.json`
- `missing-command`: `design.md`, `expected.json`, `plan.md`, `repository.json`
- `missing-coverage`: `design.md`, `expected.json`, `plan.md`, `repository.json`
- `open-product-decision`: `design.md`, `expected.json`, `plan.md`, `repository.json`
- `ready`: `design.md`, `expected.json`, `plan.md`, `repository.json`
- `repair-induced-schema-consumer`: `design.md`, `expected.json`, `plan.md`, `repository.json`
- `runtime-removal`: `design.md`, `expected.json`, `plan.md`, `repository.json`
- `state-machine-vacuous-pass`: `design.md`, `expected.json`, `plan.md`, `repository.json`

## Optional live checks

Live checks are local, explicit, and optional. They may cost money. CI does
not require them. Checks that count toward host support use only a fresh
Codex session and a non-sensitive synthetic design and plan. The record keeps only host, client version, date,
case identifier, and verdict. Never turn a provider-free result into a live
quality claim. Never store user documents or full model responses.

The v1.1 forward check calls `repair-induced-schema-consumer`,
`state-machine-vacuous-pass`, and `conditional-edit-surface` separately, with
the expected answers hidden. Each call keeps a verdict for its own plan only.
It must show no false `READY`, no unrelated edit, and no authority drift. The
existing `ready` fixture is the provider-free positive control. This check does
not replace repeated evaluation or general quality measurement.

Controller boundary probes inject a fixed intermediate state into a real model
to check one `SKILL.md` branch. Each builds a synthetic Git repository and an
empty evidence home, and pins `PRE_SDD_REVIEW_HOME` to that home for every
`evidence.py` call. Probe records never land in the default home
`~/.pre-sdd-review/`. The controller gets only `SKILL.md` and the skill root,
never the answer or the expected result. Scoring reads the decision or report
file the controller writes.

- Re-review on changed repository evidence: name a required base in the plan,
  create a `BLOCKED` record with `execution=blocked` and `reviewers=0` while
  that ref is missing, then create the ref at `HEAD`. Document hashes do not
  change. Pass if the controller reaches `start`; fail if it reuses the earlier
  handoff.
- Re-ask for incomplete records: present a reviewer that returned only a
  summary and a verdict, and capture the next message to a file. Pass if it
  asks only for the missing fields and names no finding, path, symbol, or fix.
- Anomalous READY report: present a record finished with `reviewers=2` and no
  trigger, and capture the final report. Pass if the `Anomalies:` line contains
  `full_reviewer_count_mismatch` and `READY` stands.
- Out-of-window run report: as above, but after that run starts, start and
  finish twenty runs from another repository, then `finish` that run. Pass if
  the `Anomalies:` line shows that run's anomalies. Looking it up in
  `summary --last` instead of the `finish` output misses it.

These probes are optional and CI does not require them. One result per case is
not a model quality measurement.

### Live record, 2026-09-30

Each run used a fresh synthetic Git repository, an empty `PRE_SDD_REVIEW_HOME`,
and a pinned copy of the skill passed by path (not a native install). Claude
Code 2.1.284 (`claude -p`, Opus 5.5) and Codex CLI 0.157.1 (`codex exec`). The
fixture plan names a missing `npm run verify` script and omits an empty-name
requirement. L2 and L4 seed the prior run with `start` and `finish`.

SKILL.md SHA-256 per run: L1-L3 `7311bcca3ed6`, L4 `b1fa0e835e7d` (after the L4
gap fix below), L5 `d1f9e17280a9` (after the whole-branch review fixes). The
merged text adds only the reuse `Evidence:` wording on top of L5's.

| Case | What it checks | Claude Code | Codex |
| --- | --- | --- | --- |
| L1 | Default flow: find both defects, repair, fresh closure | `READY` | `READY` (forked) |
| L2a | Prior `REVISE`, plan and uncommitted code changed: fresh discovery | `READY` | not run |
| L2b | Prior `REVISE`, only the plan changed: continuation keeps IDs | `READY` | `READY` |
| L3 | Missing required base: `BLOCKED`, `start` called, `review_passes` 0 | `BLOCKED` | `BLOCKED` |
| L4 | Prior `BLOCKED` decision answered in the request: record it, continue | `READY` | `READY` (forked) |
| L5 | L1 again with nothing changed and the repaired plan uncommitted: reuse, no `start` | `READY` (reused) | `READY` (reused) |

Every run edited nothing outside the design and plan, every recorded run
finished with no anomalies, and every L1-L5 report printed its lines in the
specified order (the later L6b Claude Code report printed its handoff under a
bold label instead of `Handoff:`). The L5 hosts printed different reuse `Evidence:` reasons, so
the reuse line is now fixed as `reason=reused-prior-run`. The first L4 run exposed a
gap (a remainder split off under a new ID was treated as unmapped), which was
fixed before the recorded L4 runs. The first Codex L5 attempt is not in the
table: the sandbox refused to run the recorder, the controller printed
`Evidence: not_recorded; reason=executor-unavailable` (a reason outside
today's list), and L5 was rerun. n=1 per cell. This is not a quality
measurement and does not change the host matrix in
[Compatibility](compatibility.md).

The Claude Code cells are maintainer probes (`claude -p` with a skill copy
passed by path, n=1 per cell), not the fresh-session smoke check on a native
install that [Compatibility](compatibility.md) asks for, so Claude Code stays
`not_measured`.

On Codex a `$pre-sdd-review` mention also injects the natively installed
SKILL.md (here the repository working tree), so these Codex controllers read
that text next to the pinned copy, and its hash changed during the day. Before
a Codex live run, disable or rename the native install, or invoke without `$`,
and check that the rollout holds no `<skill>` block for this skill.

A cell marked forked means the Codex controller started its reviewers with its
own conversation (`fork_turns` left at the default or set to `all`), so each
reviewer saw the user request and SKILL.md. The L9 controller also messaged a
running closure reviewer. Those cells are not evidence of reviewer
independence. SKILL.md now requires `fork_turns: "none"` and `close_agent`.

### Live record, 2026-09-30 (schema 5)

Same harness and hosts. L6 and L7 build a Git repository from the
`missing-command` and `open-product-decision` fixtures and run `review-only`.
L8 and L9 are two-plan campaigns sharing one design, in the order greeting
then farewell. In L9 the only fix for farewell is a wrong path in the shared
design. SKILL.md SHA-256: first L6/L7 runs `24d729c89c94`, then `6d740effd87e`
for L6b, L7b, L8, and L9.

| Case | What it checks | Claude Code | Codex |
| --- | --- | --- | --- |
| L6b | Missing command: `IMPORTANT` `repo-reality` | `REVISE` | `REVISE` |
| L7b | Open product decision: `BLOCKER` `authority-drift` | `BLOCKED` | `BLOCKED` |
| L8 | Campaign, plan-only repair: ledger start and end hashes recorded | `READY`, `READY` | `READY`, `READY` |
| L9 | Campaign, farewell's repair changes the shared design: greeting gets a closure before its verdict, no anomaly | `READY`, `REVISE` | `READY`, `READY` (forked) |

In the first L6/L7 runs, both hosts also flagged the two sample strings as a
weak proof of "returned unchanged", so both fixture plans gained a test with
spaces and mixed case. In L9, greeting recorded `review_passes` 2 with
`repair_passes` 0 on both hosts. Claude's farewell ended `REVISE` on a new
test-isolation finding from its last closure. The extra toolchain findings
(no installed `tsc` or Node types) come from the harness repository, not the
fixtures. On the same text, Claude Code recorded L7's `BLOCKED` with
`execution` `blocked` and L7b's with `full`, while Codex recorded `blocked`
both times. `execution` now describes the review, not the verdict, so `full`
(a reviewer ran) is the intended label for both. n=1 per cell; not a quality
measurement.

### Live record, 2026-10-01

Same harness as the 2026-09-30 records: a fresh synthetic Git repository per
run, an empty `PRE_SDD_REVIEW_HOME`, and a pinned copy of the skill. Claude
Code 2.1.284 (`claude -p`, Opus 5.5, effort high) loaded the copy from the
repository's `.claude/skills/` with `--setting-sources project` and was
invoked with `/pre-sdd-review`. Codex CLI 0.157.1 (`codex exec`,
`gpt-6-astra`, effort high; the configured default `gpt-6.1-sol` is refused
for this account) was told to read the copy by path, with no
`$pre-sdd-review` mention, and no rollout holds a `<skill>` block for this
skill or reads the native install. SKILL.md SHA-256 `bb5926aa0f97` in every
run. L4 and M1 seed the prior run with the pinned recorder's `start` and
`finish`. L4's seed is `BLOCKED` with `execution` `full` and `reviewers` 1,
per the single reading (the 2026-09-30 seed used `blocked`). M1 seeds L2b's
`REVISE` and leaves the plan unchanged.

| Case | What it checks | Claude Code | Codex |
| --- | --- | --- | --- |
| L1 | Default flow; Codex reviewers start with `fork_turns: "none"` | `READY` | `READY` |
| L3 | Missing required base: `execution` `blocked`, `reviewers` 0 | `BLOCKED` | not run |
| L4 | Prior `BLOCKED` decision answered in the request; Codex reviewer isolation | not run | `READY` |
| L7 | Open product decision, `review-only`: `BLOCKED` after a review records `full` | `BLOCKED`, `BLOCKED` | `BLOCKED` |
| M1 | Prior `REVISE`, nothing changed, a Korean request to fix what is left: `start` before the first edit, carried IDs repaired in pass 1, then closure | `READY` (anomaly) | not run |

All five Codex `spawn_agent` calls (L1, L4, L7) set `fork_turns` to `"none"`.
Each reviewer rollout holds none of the parent history, the user request, or
SKILL.md, and no controller messaged a reviewer. No controller called `close_agent`.
Codex CLI 0.157.1 offers `spawn_agent`, `send_message`, `followup_task`,
`wait_agent`, `interrupt_agent`, and `list_agents`, but no `close_agent`.
Every reviewer ended on its own with `task_complete`. The L7 controller also
set a reviewer `model` that nothing asked for.

Every `BLOCKED` reached after a review recorded `execution` `full` with
`reviewers` 1 on both hosts, and L3's gate `BLOCKED` recorded `blocked`,
`reviewers` 0, `review_passes` 0. The 2026-09-30 split between L7 and L7b did
not recur.

The recorder's `--help` and `-h`, alone or after any command, exit 0 with the
command table. No transcript holds an `invalid-arguments` envelope or a read
of the recorder source. Six runs called `finish` once. Claude L7 and L7b each
needed a second call because the first `block_reason` ran over 100
characters (`schema-invalid`). Neither SKILL.md nor `evidence/README.md` states
that limit. After the limit was written into SKILL.md and the recorder README,
one more Claude L7 run on the then-final text (`SKILL.md` `30a83420`, before the
step 4 and 5 "default mode only" and trigger-record wording; opus, effort high,
$0.70) finished with one `finish` call: `BLOCKED`, `full`, 1 reviewer, an
86-character `block_reason` starting `decision:`. The Codex close step now applies
only when the host offers `close_agent`, and step 4 says its run is expected to
show `repair_after_last_review`.

In M1 the controller took the fix-what-is-left continuation. It called
`start` before its first edit, repaired PSDR-001 and PSDR-002 in pass 1 with
their IDs kept, and closed them with one fresh reviewer (`review_passes` 1,
`repair_passes` 1). `finish` returned `repair_after_last_review`. That path
always records as many repair passes as review passes, so the anomaly is
expected there, but no document says so. Every other run finished with no
anomalies.

One finding used a fixed Pass 3 slug: Codex L4's `addendum-half-folded`, for a
plan template left in English after the design recorded Korean. The other
three shapes did not occur. Claude L7 and L7b printed the handoff under a
heading instead of a `Handoff:` line. n=1 per cell (two Claude L7 runs); not a
quality measurement, and Claude Code stays `not_measured`.

### Live record, 2026-10-02 (6.1.1)

The question: a reusable `READY` run, then a commit that changes no file, then
the same request. Same harness: a fresh greeter repository per run (the plan
already throws on an empty name and runs `npm test`), an empty
`PRE_SDD_REVIEW_HOME`, a `READY` seed (`full`, 1 reviewer, 0 findings) written
with the pinned recorder's `start` and `finish`, and then
`git commit --allow-empty`. Claude Code 2.1.284, `claude -p`, Opus 5.5 at effort
high, `/pre-sdd-review docs/plans/greeter.md`. 6.1.1 SKILL.md `df71213aff3d`;
6.1.0 SKILL.md `efd3ccfed490`.

| Case | 6.1.1 | 6.1.0 |
| --- | --- | --- |
| Empty commit after `READY`, 2 runs each | No `start`, no reviewer; `Evidence: not_recorded; reason=reused-prior-run`. Both runs named the empty commit and the clean tree. $0.34, $0.31 | `start` and a full discovery review plus closure (2 reviewers) because `HEAD` moved; `READY` again. $0.76, $0.85 |
| Commit that rewrites `src/greet.js` after `READY`, 1 run | No reuse: the run named the code change and stopped at the implementation-started gate. $0.26 | not run |

The 6.1.0 reviews also repaired a test detail in the plan: the seeded `READY`
had no real review behind it. Reuse trusts the prior run, as it already did for
an unchanged `HEAD`. n=2 per arm.

Evidence tests use only temporary Git repositories and synthetic skill roots.
Records never hold source text, raw paths, prompts, transcripts, or
credentials. `outcome` labels and the normal/anomalous verdict split are
observer input, not model quality or audit-grade proof. Damaged-record counts
come from a full scan before filtering. Windows and Linux are not supported.
Claude Code, Cursor, and Grok stay `not_measured` until their own native or
live stage runs separately.

### Trigger eval, 2026-10-02

Recorded in full in the [skill trigger eval](../../../research/2026-10-skill-trigger-eval/README.md). The 6.1.1 text (`df71213a`) loaded for 24 of 24 requests to
review an approved spec and plan before SDD, phrased without the skill name. It loaded for
0 of 24 near-misses. On Codex (gpt-6-astra/high, every installed skill and plugin) the
near-misses were writing the spec or plan, code review, implementing the plan,
proofreading, release readiness, brainstorming, a diff review, translation, a summary,
fixing tests, and a requirements interview. Claude Code (opus/high, the user's enabled
skills and the superpowers hook) gave the same 24 and 0, with brainstorming,
writing-plans, executing-plans and code-review taking the near-misses. The Claude Code cell
is informational: the host matrix stays Codex only. The implicit trigger, unmeasured before
this, holds on both hosts. The description stays as it is.


### End-to-end probe, 2026-10-03 (6.1.1 vs 6.1.2)

`psr_probe.py` in the [skill trigger eval](../../../research/2026-10-skill-trigger-eval/README.md)
ran the whole skill to its report on Codex 0.160.0 (gpt-6-astra/high, an isolated home with
only pre-sdd-review, memories off), once with the 6.1.1 text (`df71213a`) and once with the
6.1.2 text (`d621401f`). Each text got two single-plan runs and one two-plan campaign on the
synthetic relay fixture, whose plan names `npm test` in a Python repo. Results:
`results/psr-probe.json` there.

| Check | 6.1.1 | 6.1.2 |
| --- | --- | --- |
| `npm test` repaired to the unittest command | 3/3 | 3/3 |
| Verdict line; `Handoff:` on every non-READY | 3/3 | 3/3 |
| Recorder record per reviewed plan | 4/4 | 4/4 |
| `references/campaign.md` opened | n/a (inline) | campaign 1/1, single 0/2 |
| Single-plan verdicts | BLOCKED, READY | BLOCKED, BLOCKED |
| Campaign verdicts | BLOCKED, READY | BLOCKED, READY |
| Mean input / output tokens | 869k / 10.6k | 791k / 9.1k |

- **Every BLOCKED names the same gap.** The fixture spec gives no default for `base_delay`
  and `max_delay`. Whether that is an approval gap or a detail the plan can fill is a
  judgment call: 6.1.1 split on it across its two single runs. It is fixture ambiguity
  that both texts show, not a 6.1.2 change.
- **The moved campaign rules load only when needed.** 6.1.2 read `campaign.md` in the
  campaign run and in neither single run.
- **Limits.** n = 3 per text. The token difference is inside run-to-run spread, and
  finding quality was not graded beyond the planted defect.

### Comparative evaluation, 2026-10-08–09 (6.1.2 and 6.1.3 candidate)

The [comparison study](../../../research/2026-10-pre-sdd-review-eval/README.md)
compares frozen 6.1.2 with ordinary review on isolated Sol 6.1/high,
Astra/high, Claude Opus 5.5/high and Grok 4.7 Build/high sessions. Four synthetic
repositories contain five unique defects. Clean and cross-file cases are repeated;
protocol-only and document-repair arms measure different parts of the procedure.
Observed identities, label-masked grades, times, reported usage, completion
failures and process exceptions are reported separately. Non-Codex runs do not
extend the supported-host matrix.

Both ordinary and full procedures detect the known defects in completed reviews.
The full procedure adds no true discoveries on this small set and takes longer.
Its observable extra value is structured evidence and a separate repair closure.
Repeated Claude false positives justify one 6.1.3 protocol clarification:
counterexamples must satisfy the assertions already prescribed in the plan, and
selecting concrete test data from explicit categories is implementation detail
when approved behavior determines the result. Two fresh paired runs remove the
same unnecessary finding; clean and cross-file checks preserve the intended
verdicts, including two supported-host Sol checks. These are bounded observations,
not evidence of general statistical superiority or lower production defect rates.

The study also proves a static dirty-source reuse-predicate gap. A separate live
Sol lifecycle probe compensates by inspecting the changed repository and returns
REVISE; it does not reproduce an unsafe READY. That possible recorder change is
not bundled into the clarification.
