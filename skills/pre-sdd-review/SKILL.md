---
name: pre-sdd-review
description: Use when an approved design spec and implementation plan already exist and must be reviewed, automatically improved, and re-reviewed against repository reality immediately before SDD. Do not use for creating specs or plans, reviewing code, implementing changes, proofreading, or release readiness.
license: Apache-2.0
compatibility: Requires a local Git repository, readable design and plan files, and a host that can start a fresh read-only subagent for independent review. Supported host: Codex only.
metadata:
  version: "6.1.2"
  updated_at: "2026-10-02"
---

# Pre-SDD Review

Review an approved design and its implementation plan against each other and
repository reality before SDD. This is a readiness gate: repository reality is
evidence about feasibility and blast radius, never authority to replace an
approved product decision.

## Hard gate

Use this skill only when an approved design specification and implementation
plan exist, implementation has not started (or the user explicitly requests a
document reset before resuming), and the purpose is readiness review before
SDD or plan execution. Explicit `$pre-sdd-review` invocation is preferred;
implicit activation requires that purpose to be unambiguous.

### Single-plan path

Most runs review one plan. Skip every rule marked "campaign" and
[references/campaign.md](references/campaign.md) (a campaign is one outer
request that names two or more plans).

1. Resolve the plan, its `**Spec:**` design, and the required base.
2. Pick the path: reuse, continuation, or discovery (Choose the path).
3. Record freshness and call `start`.
4. Discovery: one independent reviewer that edits nothing, plus one focused
   reviewer only on a risk trigger.
5. Repair the documents, then a fresh closure review. Repeat within the caps.
6. Call `finish`, then print the final report.

## Resolve authoritative inputs

One verdict-bearing invocation reviews exactly one implementation plan.
Resolve the design path from that plan's `**Spec:**` field (relative to the
plan's directory unless it is repository-rooted), then read its binding
references: accepted ADRs, other explicit decision records, and any
user-approved visual or product authority. Also resolve the repository root.
If the plan has no resolvable `**Spec:**` path, do not guess among nearby
files: return `BLOCKED`.

If the input is ambiguous between multiple plans, ask for one exact plan when
the user is available; otherwise return `BLOCKED` instead of inventing an
aggregate verdict. Campaign: split, order, and stale rules are in
[references/campaign.md](references/campaign.md).

Interpret conflicts in this order:

1. User-approved direction and referenced visual authority.
2. Accepted ADRs and other explicitly binding decision records.
3. The approved design specification.
4. The implementation plan.
5. Repository reality at this plan's turn.

A plan's turn is the repository plus every preceding plan in the fixed order,
not whatever `HEAD` happens to be. When preceding plans exist, that baseline
exists nowhere on disk and must be reconstructed from them.

When repository evidence conflicts with an approved product decision, preserve
the conflict. Never silently narrow, replace, or invent product intent.

If the plan explicitly identifies a required implementation base branch, ref,
or commit, resolve it before dispatching any reviewer. Verify the current
checkout with `git merge-base --is-ancestor <required-base> HEAD`. If the base
does not resolve or is not an ancestor of `HEAD`, preserve the mismatch and
return `BLOCKED`; do not review or repair against a different checkout.

Campaign: run the shared-file ledger pre-pass in
[references/campaign.md](references/campaign.md) once, before the first plan's
invocation.

## Capture freshness

Before the first reviewer dispatch, record the repository-relative design and
plan paths and their SHA-256 hashes (`shasum -a 256`, not `git hash-object`);
Git `HEAD` (or `unborn`); and whether the worktree is clean or dirty
(`git status --porcelain`). Also record the baseline: `HEAD` alone when no
plan precedes this one, or `HEAD` with the ordered list of preceding plans
when they do. Record the ledger's repository-relative path and SHA-256 when a
ledger exists, at start and again at the verdict. With a compatible recorder,
`start` records these hashes and the Git state (`show` returns them); compute
them by hand only without it.
The final report adds the review timestamp and the final verdict.

Any content change to the resolved design or plan invalidates an earlier
`READY` verdict. Whether a Git change elsewhere forces a new review is decided
by the change list under Optional local evidence.

When preceding plans exist, carry that list and their paths in the reviewer
instruction and require a baseline-reconstruction statement on the response's
first line, so the reviewer does not quietly fall back to `HEAD`.

The freeze is the `HEAD` recorded here, or the campaign freeze in a campaign.
If `HEAD` moves off the freeze before the verdict, do not return `READY`:
abandon the run with `input-changed`, report the move and the findings so far, and stop. A new review
needs a new outer request.

## Optional local evidence

Run `python3 "<skill-root>/evidence/evidence.py" --version`, where
`<skill-root>` is the directory holding this `SKILL.md`, without installing
anything. Record only when its JSON says `skill_name=pre-sdd-review` and
`schema=5`. The command reference, including the `finish` input keys, is in
`<skill-root>/evidence/README.md`. When compatible, run
`summary --repo <repo display name> --plan <plan>` (the checkout
directory's name and the plan's repository-relative path) before `start`. Its
`runs` are this plan's newest 50 runs, oldest first; `runs_total` counts all
of them.

### Choose the path

The change list since a prior run is
`git diff --name-only <git.head_end>` plus
`git ls-files --others --exclude-standard`. It covers commits, uncommitted
edits, and untracked files. It is "docs-only" when it names no path besides
the resolved design, plan, and ledger. It decides between runs only; during a
run, any `HEAD` move counts (Capture freshness). Work down this list and take
the first match:

1. **Pending run.** Close any `pending` run for this plan with `abandon
   --repo <checkout> --reason input-changed` (or `other`) before anything
   else: a pending run can outlive the invocation that opened it and be
   mistaken for a new round. If `abandon` fails with `outside-repository`,
   that run belongs to another checkout; leave it.
2. **Waiting on a user decision.** The latest completed run is `BLOCKED` on a
   user decision:
   - If the outer request gives the decision, it is level-1 authority. In
     default mode, record it in the resolved design (the only repair allowed
     here). In `review-only`, make no edit: report the decision to record and
     stop as below.
   - If it is now recorded (by that repair or in an authority document), take
     the continuation when the change list is docs-only; otherwise run
     discovery. Plan text that must change to follow the decision is a direct
     mapped repair impact.
   - Otherwise dispatch no reviewer and make no repair: print the same
     checkpoint and stop. Call no `start`; print `Evidence: not_recorded;
     reason=previous-decision-checkpoint`. Other plans continue.
3. **Nothing changed.** The run's `execution` is reusable, `plan.sha_end`,
   `design.sha_end`, and `ledger.sha_end` (when recorded) match the current
   documents, the change list is docs-only (a moved `HEAD` with no code
   change still is), and the outer request does not ask for a re-review, ask
   to fix the handoff, or name changed authority or repository evidence. Reuse the prior
   result and handoff without a new review; call no `start`, and print
   `Evidence: not_recorded; reason=reused-prior-run` and
   `Anomalies: not_recorded`.
4. **Fix what is left.** The latest completed run is a reusable `REVISE`,
   nothing changed as step 3 defines it, and the outer request asks to fix the
   handoff. In default mode only, take the continuation: call `start`, apply
   the handoff's minimal fixes as repair pass 1, then run closure. Its record has
   one repair and one review, so `finish` reports `repair_after_last_review`;
   that anomaly is expected here.
5. **Only the documents changed.** In default mode only, take the
   continuation when the latest completed run is `REVISE` with a reusable `execution`, the
   change list is docs-only, the documents' diff since the run's `sha_end` can
   be produced, and the outer request does not ask for a full re-review.
6. **Otherwise** run discovery. Without a recorded run for this plan there is
   no reuse and no continuation.

A run is reusable when its `execution` is `full`, or `degraded` with
`focused-role-not-obtained` as its only reason. Outside step 2, a `BLOCKED`
verdict is never reused, and neither is any other `degraded` run; for those,
re-run the input gates and call `start` for a fresh full review. Reuse and
continuation compare the `repo` display name, plan path, document hashes,
`git.head_end`, and the change list; `finish` and `abandon` enforce the
checkout binding, so do not recompute it.

### Start and finish

Unless Choose the path ended the invocation without a review (steps 2 and 3),
call `start` once the plan path resolves, before any reviewer dispatch, even
when an input gate is about to return `BLOCKED`. Edit no reviewed document
before `start`, except the step-2 decision record and campaign pre-pass
repairs.

```sh
python3 "<skill-root>/evidence/evidence.py" start --skill-root "<skill-root>" \
  --repo . --plan <plan> --design <design> --client <host-id> \
  --model <host-reported-model-or-unknown> --mode default|review-only
```

If `**Spec:**` cannot be resolved, omit `--design`; the recorder does not
parse `**Spec:**`. Argument values, including `--client` and the
`outside-repository` case, are in the
[recorder README](evidence/README.md). In a campaign, pass the
ledger path with `--ledger` and each preceding plan with a repeated
`--prior-plan`. Keep the returned `run_id` controller-local and out of user
documents. The same lifecycle applies to default and `review-only` mode.

After the verdict and any repairs are final, call `finish --run-id <id>
--repo .` once with the review facts as one JSON object on stdin, then print
exactly one `Evidence:` line: `Evidence: recorded; run_id=<run-id>` or
`Evidence: not_recorded; reason=<code>`, with `<code>` from the recorder
README's Boundary section. An unavailable, malformed, incompatible, or
permission-failing recorder must continue the review and never changes the
semantic verdict. If the invocation ends before `finish`, call `abandon
--run-id <id> --repo . --reason <reason>` with a reason from the recorder
README; never leave a run pending.

`review_passes` counts reviewer dispatch rounds in this run: discovery is one,
each closure is one. It is `0` only for a `BLOCKED` run that dispatched no
reviewer (with `reviewers: 0`). `execution` describes the review, not the
verdict. It is `blocked` only when no independent primary review ran: an input
gate (the required base or an unresolved `**Spec:**`) stopped the run, or no
primary reviewer was obtained. A `BLOCKED` verdict reached after a review
keeps `full` or `degraded`.

A record from an earlier recorder fails with `schema-unsupported` and never
blocks `start`; leave it and start a new run. Recording an `outcome` is not a
controller duty; the user or the SDD worker may record one after SDD. Never
store a full reviewer response or source body in evidence; use bounded
paraphrases only.

The finding record's fields and their values are in the recorder README. A
record first raised in a closure round takes the next ID number after the
highest so far. `pattern` is a short lowercase slug the controller assigns to
the defect shape; keep the same slug for the same shape across rounds. The
four recurring shapes in the reviewer protocol's Pass 3 use its fixed slugs,
such as `closed-list-one-side`; other slugs are free.

## Select reviewers

Dispatch one fresh, independent, read-only reviewer using the
[reviewer protocol](references/reviewer-protocol.md), through the host's
subagent facility (a Codex subagent, or the Claude Code Agent tool with an
agent type that has no edit tools when one exists), and state in the
instruction that the reviewer is read-only. Start each reviewer with no
inherited conversation (Codex: `fork_turns: "none"`); its only input is the
dispatch instruction. Send nothing to a running reviewer except the one
missing-fields re-ask below, and close each reviewer once its records are in
(Codex: `close_agent` when the host offers it; a reviewer that returned its
final answer is left alone). Supported host: Codex only; on any other host, record
its real id with `--client`.

A second fresh reviewer is conditional, not routine: dispatch one focused reviewer only for
framework or runtime removal; schema migration or data deletion;
authentication, authorization, or security boundaries; public/private
data-boundary changes; or external side effects such as publishing, billing,
messaging, or production mutations. It examines only the triggered risk class.
Record the trigger as `runtime-removal`, `schema-migration`, `auth-boundary`,
`data-boundary`, or `external-side-effect`, respectively, matching the list
above. When more than one class applies, the focused reviewer examines each of
them and the record names the first in that list.

The controller deduplicates all findings by evidence and consequence before
repair. Reviewers never edit files.

If a reviewer returns a summary, or a record missing any PSDR field, ask that
reviewer once for the complete records, naming only the missing fields. Do not
name suspected findings, paths, symbols, or fixes in that request. Never
accept a summary as findings.

Across the entire invocation, use at most two review roles: one primary role
and, when triggered, one focused risk role. The focused risk role is required
only in an invocation that runs discovery. Closure rounds and continuations
do not dispatch it, and a run with no discovery records `trigger: null`. A
fresh re-review may replace the agent in either role, but it does not add a
review role or broaden the triggered risk class. Evidence `reviewers` (0–2)
counts distinct agents obtained for these logical roles, not intended roles
and not cumulative fresh agent calls; a `full` run records 2 when a trigger
applies and 1 otherwise.

If a fresh independent primary reviewer cannot be obtained, return `BLOCKED`
with `execution=blocked` and the degraded reason `primary-role-not-obtained`.
Do not use the controlling agent as a substitute independent primary and do
not run a short degraded round in its place. Reusing one agent for two
dispatches in this invocation is `execution=degraded` with
`agent-reused-within-invocation`, and its handoff is never reusable. When the
focused risk role was triggered in discovery but not obtained, the run is
`execution=degraded` with `focused-role-not-obtained`; that reason alone does
not bar reuse or continuation.

Campaign: discovery waves are in [references/campaign.md](references/campaign.md).

## Default mode: review -> repair documents -> scoped re-review

One invocation has at most one discovery stage (none in a continuation), at
most two repair passes plus one residual pass, and a terminal scoped closure.
The default controller state machine is:

```text
resolve plan -> resolve plan **Spec:** -> read binding references
-> verify required implementation base -> hash design and plan
-> record HEAD and dirty state
-> fresh read-only review -> controller deduplication
-> authority-preserving document repair -> original closure review
-> conditional bounded repair-impact regression -> optional second repair
-> fresh original closure review + conditional bounded repair-impact regression
-> optional residual repair -> fresh closure of those IDs only
-> READY | REVISE | BLOCKED
```

After the first review, repair only findings that have an
authority-preserving document correction. If the first review has zero findings
and the plan is not stale, skip repair and closure and return `READY`.
A stale plan still takes scoped closure.
`repair_passes` counts every repair pass the controller applied, whether or not
its closure closed anything. Pre-pass ledger and machine-check repairs keep
`repair_pass: 0` and are not a pass. Write `repaired` only when a closure
reviewer closed that record; a record the controller repaired but no closure
reviewer closed stays `unresolved`. Never return `READY` when the last action
was a repair: close it with one more closure review; return `REVISE` without
that closure only when no fresh closure reviewer can be obtained.

Closure disposition is `closed`, `partially-closed`, or `open`, recorded as
`repaired`, `partially-closed`, and `unresolved` respectively. Record the
remainder of a partial closure as the original record's remaining sites, never
as a new ID, so repair passes track defects rather than the sites a defect is
scattered across. A finding still `partially-closed` at the end counts as
unresolved for the verdict: it forces `REVISE`, or `BLOCKED` when it is a
`BLOCKER`. A record's `repair_pass` is the last pass that repaired it.

A new invocation does not copy a previous finding's `repair_pass`. A finding
this invocation did not repair uses `repair_pass` null, including an
unresolved handoff finding and one closed by a change made between
invocations.

If a repair changes a schema, type, interface, state transition, conditional
mutation surface, cross-task producer/consumer contract, verification meaning,
or public/private boundary, create a compact `repair-impact map` before
re-review. Record the modified claim; changed symbol, state, path, or command;
direct consumers and adjacent task interfaces; and each disposition as
`modify`, `verified-no-change`, or `unresolved`. Include one plausible
verification counterexample. Ordinary scalar corrections that trigger none of
these conditions do not require the map.

The closure instruction must include the repair diff of the resolved design,
plan, and ledger, even when the repair-impact map is empty.
Give a fresh reviewer the final repaired documents, original findings, and any
repair-impact map. It first checks original finding closure, then performs a
bounded repair-impact regression over the mapped consumers and adjacent
interfaces. This is not a new full review.

During scoped re-review, a material finding is eligible for the current repair
only when its source is an original finding or a direct mapped repair impact.
A finding whose `class` and `pattern` match an original record is not
unmapped, even at a different location. It shows the original record's
Location was incomplete: widen that Location and repair it inside the same
pass. Only a new defect shape is unmapped. An unmapped material finding ends
the invocation: repair nothing more, put it in the unresolved handoff, and
apply the existing verdict rules (`BLOCKED` when the fix needs authority, input, or
repository evidence that is unavailable or unresolvable; otherwise `REVISE`).

An optional second repair is allowed only when that re-review finds another
eligible repairable material defect. Before it, deduplicate remaining findings,
complete any triggered impact map, and confirm that the repair hides no
unresolved authority choice. Then run one final fresh closure and repair-impact
re-review. At most two repair passes are permitted, plus one residual pass:
when everything the second closure leaves open is an original record,
`IMPORTANT`, at most two records, each with a recorded fix at one site within
the reviewed documents, and the repair-impact map is empty, repair those
records once more and dispatch one fresh closure reviewer for those IDs only.
A new defect shape found there ends the invocation. If a material issue
remains, return `REVISE` with its evidence; do not downgrade it to finish the
loop.

### Continuation after `REVISE` or `BLOCKED`

A continuation replaces discovery with closure; Choose the path decides when
to take it. Call `start`, then dispatch one fresh read-only reviewer with the
closure dispatch, whose repair diff is the document diff since the prior run's
`sha_end`. Its open records are the prior unresolved handoff packet when this
conversation holds it, else the prior run's recorded findings from `show`;
their `id`, `severity`, `class`, `location`, and `evidence` are exact.
Reading a prior run's recorded findings as open records is not reusing its
handoff: the continuation reviews them again. Keep the prior finding IDs. A
carried record keeps its `id`, `severity`, and `class`. When closure finds a
remainder of a different severity or class, close or keep the carried record
on its own terms and record the remainder as a new record with a new ID.
That remainder's source is the carried record, so it is not unmapped and is
eligible for repair.

The flow then continues as after an original closure review: repair, closure,
the residual pass, verdict. A continuation is its own run: it counts its
passes from 1 and keeps the two-plus-residual cap. Only the number of
continuations is uncapped: text outside the diff already passed one
discovery, and closure's bounded regression covers the diff.

Campaign: the cross-plan schedule and the stale set are in
[references/campaign.md](references/campaign.md).

## Review-only mode

`review-only` is explicit. Make no file changes, use the same fresh read-only
review and controller deduplication, and return the first review's verdict.

Campaign `review-only` is in [references/campaign.md](references/campaign.md).

## Repair rules

The controlling agent may edit only the resolved design specification, the
resolved implementation plan, and the resolved shared-file ledger. Ordinary
evidence-backed corrections within that closed document boundary do not
require an approval checkpoint.

Any correction that changes approved product intent is forbidden and returns
`BLOCKED`. The mutation allowlist excludes accepted ADRs, approved visual authority,
application code, tests, configuration, generated artifacts, and unrelated documentation.
Do not introduce a new feature, dependency, host claim, or product decision while
repairing documents.

Authority-preserving repairs require no user checkpoint. When one or more
unresolved items require user authority, return one consolidated user
checkpoint with the exact decisions needed; do not split them into repeated
approval requests.

### Machine checks

Run these in the campaign pre-pass over every plan at once, and in every invocation
over the repaired documents before dispatching a closure reviewer. Pass the
results to the closure reviewer as their own dispatch item.

1. A declared count against the counted one: a task's stated passing count
   against its actual tests, a closed list's stated membership against its
   members.
2. The argument count and order at every site that builds the same constructor.
3. A literal against the constraint that receives it: length, range, enum.
4. An identifier embedded in a number or a name, at every site that carries it:
   a migration file's number against the number in the test that checks it.
5. Every face of a closed list, updated together: schema enums, exact-match key
   arrays, tests that count members.
6. Every backticked repository path in the plan exists at that plan's turn.
   Exclude paths any plan in the chain lists under `Create:`. Excluding only
   the current plan's `Create:` yields false positives.

These emit candidates. A candidate is not a defect until the repository
confirms it. Raising an unconfirmed candidate makes the gate spend a round trip
on a defect that is not there.

## Verdict and handoff

Return `READY` only when no unresolved finding requires invention or permits a
materially wrong implementation to pass the planned evidence. Return `REVISE`
for a material repairable document defect, including one still material after
the last pass. Return `BLOCKED` when required authority, input, or
repository evidence is unavailable, unresolvable, or would require a new
product decision, or when an independent primary reviewer cannot be obtained.
Name the cause in a one-line `block_reason` (prefix convention and length limit
in the recorder README); a `BLOCKED` run with a null `block_reason` is an
anomaly.
An open `BLOCKER`, including one still `partially-closed`, forces `BLOCKED`,
never `REVISE`.

For final `REVISE` or `BLOCKED`, include an `unresolved handoff packet`: the
unresolved finding, why it escaped an earlier pass when known, the bounded
next document scope, whether new authority or evidence is required, and the
next invocation scope. New authority implies `BLOCKED`, never `REVISE`. This
packet does not authorize another repair pass or certify its suggested scope
as complete.

When this run would end `BLOCKED` on a new product decision and the two
preceding runs of this plan in the recorder's chain did too, the handoff sends
the design back to be finished with all remaining decisions at once, and says
the next invocation should wait for that. Without a chain, report the count
you know and do not stop on it. Other plans continue.

For `READY`, print the exact resolved design and plan paths and their final
fingerprints, together with the freshness record. Print the `anomalies` list
that `finish` returned for this run as `Anomalies: <names>`, or
`Anomalies: none` when it is empty. When the recorder was not used or
`finish` failed, print `Anomalies: not_recorded`. Do not look this run up in
a windowed `summary`. Anomalies do not change the verdict.

Do not start SDD unless the outer request explicitly asks for implementation.
In that combined request, hand the SDD worker the final repaired documents,
not the pre-review copies.

Include a compact pass receipt in the final report. Do not persist user
documents or full model responses merely to create it. Print the final report
in this order:

```text
Verdict: READY | REVISE | BLOCKED
Freshness: design <path> <sha256>; plan <path> <sha256>; HEAD <sha|unborn>; worktree clean|dirty; baseline; ledger <path> <sha256>|none; reviewed_at <UTC>
Receipt: input and final document hashes; review_passes; repair_passes; finding IDs with class and status; triggered repair-impact categories
Handoff: the unresolved handoff packet (REVISE and BLOCKED only)
Evidence: recorded; run_id=<id> | not_recorded; reason=<code>
Anomalies: <names> | none | not_recorded (READY only)
```

After printing the report, stop. Do not automatically start another
invocation, and do not edit code, branch, stash, or commit, unless a new user
turn asks for it (SDD that the outer request asked for is the one exception).
A change this controller made does not count as a changed document; Choose the
path decides what a later invocation runs.

## Do not use this skill for

Do not use this skill to create designs or plans, implement or edit application
code, review a source diff, perform release readiness or security review,
proofread, publish a release, or make an accepted product decision.

## Gotchas

Recorded in live runs.

- Codex `spawn_agent` forks the parent conversation into the reviewer unless
  `fork_turns: "none"` is set, so a forked reviewer sees the user request and
  this file. Codex CLI 0.157.1 has no `close_agent`; its reviewers end on
  their own.
- `finish` rejects a `block_reason` over 100 characters as `schema-invalid`.
- Claude Code reports printed the handoff under a heading or a bold label
  instead of on the report's `Handoff:` line.

## Red flags

- Resume a reviewer by naming findings, paths, symbols, or fixes
- Start a new review when documents and the request are unchanged and the change list is docs-only since a reusable run
- Reuse a handoff from a `BLOCKED` run outside step 2, or reuse any handoff on document hashes alone
- Dispatch a second reviewer, or record `reviewers: 2`, with no risk trigger
- Return or accept a finding summary instead of complete PSDR records
- Print `READY` without the `Anomalies:` line from `finish`
- Commit before `finish`
- Cite `repo-reality` with only the reviewed design or plan paths
- Put source text in an evidence paraphrase
- Claim that a test covers something without locating that test
- Apply a textual repair without asserting the match is unique
- Reuse one reviewer across invocations that review different plans
- Reuse a handoff from a `degraded` run with any reason besides `focused-role-not-obtained`
- Overlap repairs of two plans on one host
- Reuse a reviewer to fill a discovery wave
- Print READY after HEAD moved from the freeze
- Skip closure for a stale plan with zero discovery findings
- Dispatch a reviewer while the plan waits on an unanswered user decision
- Return `READY` when the last action was a repair
- Run a fresh discovery when a continuation applies
- Take a continuation while the change list names a file outside the design, plan, and ledger
