# Changelog

All notable changes to this product are documented in this file.

## Unreleased

## 6.1.0 - 2026-10-01

### Fixed

- Reviewers start with no inherited conversation (Codex: `fork_turns: "none"`); the dispatch instruction is their only input. The controller sends a running reviewer nothing except the one missing-fields re-ask, and closes each reviewer once its records are in (Codex: `close_agent`). On Claude Code it prefers an agent type without edit tools. Before, some Codex runs forked the controller's conversation into the reviewer, so the reviewer was not independent.
- `execution` has one reading: it describes the review, not the verdict. It is `blocked` only when no independent primary review ran (an input gate, the required base, an unresolved `**Spec:**`, or no primary reviewer; `reviewers` 0, `review_passes` 0). A `BLOCKED` verdict reached after a review keeps `full` or `degraded`. Reuse now keys on the verdict: outside the decision path a `BLOCKED` result is never reused. Before, the same text produced both labels and a `BLOCKED` run labeled `full` could be reused.
- After a repair, the controller always runs one more closure review; it returns `REVISE` without that closure only when no fresh closure reviewer can be obtained. Before, `SKILL.md` allowed skipping the closure, which `repair_after_last_review` then flagged.
- After printing the final report, the controller stops: no code edit, branch, stash, commit, or new invocation without a new user turn that asks for it. A change the controller made does not count as a changed document. The SDD sentence now stands alone.
- `SKILL.md` and `evidence/README.md` say schema 2, 3, or 4 records are unsupported, and the recorder README says schema 4 (not 5) came from 4.0.0 through 5.1.0.
- `start --model ""` (or a multi-line or over-long model) fails with `invalid-arguments` like every other argument error, not `schema-invalid`.
- The Codex close step applies only when the host offers `close_agent` (Codex CLI 0.157.1 has none); a reviewer that returned its final answer is left alone.
- `SKILL.md` and the recorder README state the string limits that `finish` enforces: `block_reason` 100 characters, a finding's locator 200, consequence and fix 300. A live run lost a `finish` attempt to an unstated limit.
- `summary --repo` refuses `.`, `..`, or a value with a slash, with a message that it is the checkout's display name; before, such a value silently matched nothing. `summary --plan` drops a leading `./`.

### Changed

- The host claim reads "Supported host: Codex only" (support, not measurement). The README pair no longer says other hosts were never checked.
- The four recurring defect shapes in the reviewer protocol's Pass 3 have fixed `pattern` slugs: `addendum-half-folded`, `prose-only-verification`, `line-number-location`, and `closed-list-one-side`. Other slugs stay free.
- `block_reason` starts with `decision:`, `input:`, `evidence:`, or `reviewer:` by convention (not an enum), and `primary-role-not-obtained` is documented as recorded only on an `execution=blocked` run.
- `Evidence: not_recorded; reason=<code>` takes the failing recorder command's error code, `recorder-unavailable`, `recorder-incompatible`, `reused-prior-run`, or `previous-decision-checkpoint`.
- `--plan`, `--design`, and `--ledger` must be inside the `--repo` checkout; otherwise the review continues and prints `Evidence: not_recorded; reason=outside-repository`.
- Reuse and continuation compare the display name, plan path, document hashes, `git.head_end`, and the change list; `finish` and `abandon` enforce the checkout binding, so the controller does not recompute it. With a compatible recorder, `start` records the hashes and Git state; the controller hashes by hand only without it.
- `SKILL.md` names the recorder slug for each risk trigger, defines the finding ID format (`PSDR-` plus three or more digits; a record first raised in a closure takes the next number), and drops the Hard gate paragraph that repeated "Do not use this skill for". The continuation rows in the READMEs and the recorder README say "from a reusable run", and the recorder README says campaign `elapsed_s` is campaign wall time.

### Added

- `--help` and `-h`, on their own or after any command, print the recorder's command table on stdout and exit 0.
- `show` accepts `--repo` and ignores it, so it takes the same arguments as `finish` and `abandon`.
- A reusable `REVISE` with nothing changed and a request to fix what is left takes the continuation: `start`, the handoff's fixes as repair pass 1, then closure. Nothing reviewed is edited before `start` except the step-2 decision record and campaign pre-pass repairs. Its run is expected to show `repair_after_last_review`, because the repair comes before the only closure review.

### Notes

- Handshake `cli_version` is 6.1.0. Record schema stays 5, so 6.0.0 records stay readable.

## 6.0.0 - 2026-09-30

### Breaking

- The recorder reads schema 5 only. Schema 2, 3, and 4 records written by 5.1.0 and earlier are no longer read, migrated, or closed. `show`, `finish`, `abandon`, and `outcome` refuse such a run with `schema-unsupported` and leave the file unchanged. `summary` skips those files and counts them in the new `unsupported_records`. Old records never block `start`.
- To clear old records, delete the `<run-id>.json` files under `~/.pre-sdd-review/runs/` (or `PRE_SDD_REVIEW_HOME/runs/`) whose top-level `"schema"` is 2, 3, or 4. For example, find them with `grep -lE '"schema": ?[234][,}]' ~/.pre-sdd-review/runs/*.json`, check them, then delete them. A schema 3 or 4 run left pending cannot be closed; start a new run.
- Removed the error code `legacy-record-read-only` and the `summary` `binding` field (`runs[].binding`, `counts.binding`, `historical-unbound`, `checkout-bound`). The old-record exceptions (findings without `source`, free-string `degraded_reasons`) are gone too.
- `abandon` now requires `--repo` and refuses a run from another checkout with `outside-repository`, the same check `finish` makes. Before, one clone could close another clone's live run.
- Finding `status` is `repaired`, `partially-closed`, or `unresolved`. The undocumented `blocked-by-authority` and `accepted-as-is` are rejected.
- Schema 5: the record's `ledger` is `{path, sha_start, sha_end}`, like `plan` and `design`, and `finish` records the end hash. Schema 4 records (written before the schema-5 recorder) are refused like schema 2 and 3. Reuse now also requires an unchanged ledger.

### Fixed

- Two commands could hold the same run lock at once, so a `finish` and an `abandon` could both succeed. A command now deletes its lock file while still holding it, a waiter retries on the current file, and a failed acquire never deletes the file.
- `start` validates a record before writing it, so it can no longer leave a `pending` run that no command can close (for example, a checkout directory named with a backslash).
- Non-UTF-8 input to `finish` and a missing `git` return a one-line JSON error instead of a traceback.
- A `BLOCKED` run that dispatched no reviewer can be recorded with `review_passes: 0`.
- In a campaign, a design changed by another plan's repair no longer raises `document_changed_without_repair_pass`, including for the first plan (a run with a `ledger` counts as a campaign run).
- A repair that changes a shared design now marks every other plan that depends on it stale, whether that plan comes before or after it. Before, an earlier plan could keep a `READY` reviewed against a design that a later plan's repair had changed. A stale plan gets its closure after the repair that made it stale.
- `repo_reality_citing_documents_only` now counts the ledger as a document, as the reviewer protocol already said.
- `cases.json` grades a missing command (`nonexistent-command`) and a consumer-before-producer order (`task-interface-order`) as `IMPORTANT`: both are fixed by a plan edit. The live runs recorded in `testing.md` graded the missing command `IMPORTANT` on both hosts. `extension-collision` stays `BLOCKER`, and its request now says no authority decides which feature keeps the extension point.
- Reuse and continuation now see uncommitted and untracked changes: the change list is `git diff --name-only <git.head_end>` plus `git ls-files --others --exclude-standard`. Before, an uncommitted code edit let a stale handoff be reused.
- `start` is called whenever the plan path resolves, even when an input gate returns `BLOCKED`, so a gate-`BLOCKED` run is in the chain. Only a reprinted decision checkpoint and a reused result call no `start`.
- A continuation counts its passes from 1 and keeps the usual caps, and a run with no discovery records `trigger: null`. Before, the numbering could make `finish` reject the record and a continuation of a triggered plan was always mislabeled.
- A user decision given in the request is written into the design, then the review continues. Before, the controller could only reprint the same question.
- The `HEAD`-moved rule now applies to a single plan, not just a campaign.
- `BLOCKER` means the fix needs authority, input, or evidence that is unavailable or unresolvable, not merely evidence outside the documents. A ledger-only fix is `IMPORTANT`.
- An unmapped finding in closure ends the invocation; the contradicting "keep it visible and continue" sentence is gone. Machine-check results go to the closure reviewer as their own item, so they no longer make the residual pass unreachable.

### Changed

- `SKILL.md` opens with a six-step single-plan path. The reuse, continuation, and pending-decision rules are one ordered list ("Choose the path") instead of three copies. Multi-plan rules are marked "campaign" and grouped.
- `SKILL.md` shows the literal `start` command, the `finish` example lives in `evidence/README.md`, `pattern` and `review_passes` are defined, and the final report has a fixed order.
- "Dirty plan" is renamed "stale plan" so it is not confused with a dirty worktree. The `H0` and `H_git0` labels are gone.
- README sentences are shorter and plainer. Behavior is unchanged.
- `summary --plan <path>` limits the output to one plan, and `SKILL.md` uses it before `start`. `runs` lists at most the newest 50 records; the new `runs_total` counts them all.
- Two fixtures: `missing-command` (`IMPORTANT` `repo-reality`, `REVISE`) and `open-product-decision` (`BLOCKER`, `BLOCKED`).
- `SKILL.md` no longer describes the nonexistent `reviewer_count` field. The one record field is `reviewers` (0-2); a `full` run records 2 with a trigger and 1 without.
- Docs are English-first: `README.md` is the English user guide and `README.ko.md` is the separate Korean one (formerly `README.md` and `README.en.md`). `CHANGELOG.md` and the maintainer docs are in English. Behavior is unchanged.

### Notes

- Handshake `cli_version` is 6.0.0. Record schema is 5. No GitHub tag or GitHub Release is created.

## 5.1.0 - 2026-09-24

### Changed

- If the last verdict was `REVISE`, or `BLOCKED` on a user decision the documents now record, and only the design, plan, or ledger changed since, the review continues from closure with no new discovery. This needs a recorded run for the plan. A `BLOCKED` run continues once the user decision is recorded; while it is frozen, the controller does not call `start` and prints `Evidence: not_recorded; reason=previous-decision-checkpoint`.
- After the second closure, if no more than two original `IMPORTANT` records remain, each fixable at one site, the same invocation repairs them once more.
- `repair_passes` counts applied repair passes. `repaired` is used only for records a closure reviewer closed, and a run whose last action was a repair is not `READY`.
- An open `BLOCKER` means `BLOCKED`. The reviewer is not dispatched again while a user decision is unanswered, and three new decisions in a row send the design back.
- The focused risk role is dispatched only in a call that runs discovery. A `degraded` run whose only reason is `focused-role-not-obtained` does not bar reuse or continuation.

### Removed

- Costless repair accounting and `summary.counts.costless_repairs`.

### Notes

- The recorder gained the `repair_after_last_review` and `open_blocker_without_blocked_verdict` observation anomalies. `repair_without_repaired_finding` fires only when no record was repaired.
- Record schema stays 4 and accepts `repair_passes` 0..3 and `review_passes` 1..4. A three-repair record written by 5.1.0 cannot be read by the 5.0.0 recorder. Handshake `cli_version` is 5.1.0. No GitHub tag or GitHub Release is created.
- In `### Contract`, the `handoff` value `full-execution-only` became `reusable-execution-only`, a new `continuation` key (`docs-only-diff`, `closure-first`, `recorded-run-required`) was added, and `repair-passes` replaced `costless-repairs-uncounted` with `residual-pass-once` and `applied-passes-counted`.

## 5.0.0 - 2026-09-19

### Changed

- Discoveries of several plans may overlap; repairs run one at a time. Closure requires the repair diff.
- If a preceding repair changes files a later plan reads, closure runs even with zero findings.
- Discovery is split across as many reviewers as the host can run at once, and one reviewer is never reused for another plan.
- If the `HEAD` recorded at the campaign start moves, no `READY` is returned against it.
- A preceding `BLOCKED` plan does not stop later plans' discovery.

### Notes

- Record schema is 4. Handshake `cli_version` is 5.0.0. No GitHub tag or GitHub Release is created.

## 4.0.0 - 2026-09-18

### Added

- A verdict-less ledger pre-pass. A request naming two or more plans builds the
  shared-file ledger and execution order and runs the machine checks once,
  before the first verdict-bearing invocation.
- `Repository reality at this plan's turn`. Freshness gains baseline and
  ledger, and with preceding plans the reviewer states the baseline
  reconstruction.
- A reviewer brief contract. Discovery and closure briefs are separate; the
  closure brief carries the earlier round's records verbatim and the list of
  Tasks no record points to yet.
- Four recurring defect shapes and a proof table for compound constraints.
- `start` gained `--ledger` and a repeatable `--prior-plan` argument.
- Observation anomalies gained `head_start_not_ancestor_of_head_end` and
  `document_changed_without_repair_pass`.

### Changed

- The editable paths are three: design, plan, and ledger. The ledger is
  derived evidence, not authority.
- Partial closure is first-class. A remainder is the rest of the same record,
  not a new ID.
- A repair with an empty impact table, whose closure reviewer confirmed no
  consumers, does not use up a pass. `summary.counts.costless_repairs` counts
  these.
- A finding with the same `class` and shape as an original record is not
  unmapped, even at a different location.
- Only `full` runs have their handoff reused. If no independent primary
  reviewer is available, the verdict is `BLOCKED`, and one agent is never
  reused for an invocation on a different plan.

### Breaking

- Record schema and handshake are `4`. The canonical line is
  `{"cli_version":"4.0.0","schema":4,"skill_name":"pre-sdd-review"}`.
- Records gain `baseline` and `ledger`, `git` gains
  `head_start_is_ancestor_of_head_end`, and findings gain `source`.
- `finding.repair_pass` ranges 0..2, `finding.status` gains `partially-closed`,
  and `degraded_reasons` is an enum.
- Schema 2 and 3 are still read. Mutations accept schema 4 only; a pending
  schema 3 run allows only `abandon`.

### Notes

- No GitHub tag or GitHub Release is created.

## 3.0.4 - 2026-09-17

### Fixed

- `finish` returns this run's observation anomalies; controllers print that list as an `Anomalies:` line instead of searching a windowed `summary`.
- A handoff from an `execution=blocked` run is never reused; `full` and `degraded` handoffs are reused only when documents, `HEAD`, and the request are unchanged.
- Controllers re-ask an incomplete reviewer once for the missing fields only.
- Finding severity follows the minimal document fix: `BLOCKER` needs outside authority or evidence, `IMPORTANT` is repairable within the two documents.

### Changed

- The `missing-coverage` fixture expects `IMPORTANT`; the `ready` fixture design states the function returns its input unchanged.

### Notes

- Record schema and the `--version` handshake are unchanged. No GitHub tag or GitHub Release is created.

## 3.0.3 - 2026-09-16

### Fixed

- Controllers print this run's observation anomalies on `READY`. Anomalies do not change the verdict.
- Incomplete finding records are re-asked without naming suspected findings, paths, symbols, or fixes.
- Red flags name the observed reuse, extra-reviewer, seeded-retry, and document-only `repo-reality` failures.

### Notes

- No GitHub tag or GitHub Release is created.

## 3.0.2 - 2026-09-12

### Fixed

- Controllers consult `summary` before `start`, close same-plan pending runs, and reuse an unchanged `REVISE`/`BLOCKED` handoff.
- Split plan reviews on one host run one after another. A reused controller thread is not an independent primary.
- A first review with zero findings skips repair and closure.
- `repair_passes` counts only passes with a repaired finding.
- Mutation lock files are removed when the command releases them.

### Changed

- Product READMEs state the summary-before-start, serialize, and zero-finding skip rules.

### Notes

- No GitHub tag or GitHub Release is created.

## 3.0.1 - 2026-09-11

### Fixed

- Recorder JSON lines keep a single LF on Windows text stdout, so release
  smoke and `--version` match the Unix byte contract.

### Changed

- Product README language was simplified with no behaviour change.
- Standalone README now uses the shared heading set and points install procedures at the split user guides.

### Notes

- No GitHub tag or GitHub Release is created.

## 3.0.0 - 2026-09-08

### Changed

- New optional recorder schema 3 binds records to a locally salted checkout identity.
- Schema 2 remains readable as historical-unbound evidence and cannot be mutated.
- Run locks serialize finish, abandon, and outcome; reads isolate corrupt records.
- Structurally valid contradictory observations remain recorded and appear as anomalies.
- Installed README links resolve inside the payload or point to public repository docs.
- Reviewer roles, scalar risk triggers, two-document repairs, repair limits, and semantic verdicts are unchanged.
- This change does not publish a release or claim new native platform/model evidence.

## 2.0.0 - 2026-09-05

### Changed

- The evidence recorder is one standard-library script,
  `evidence/evidence.py`, run with `python3` from the loaded skill root. The
  `pre-sdd-review-evidence` launcher, installer, and package are removed.
- Records use schema 2: one file per run under `~/.pre-sdd-review/runs/`,
  and six commands `start`, `finish`, `abandon`, `outcome`, `show`, `summary`.
  Schema 1 receipts are not read.
- The controller passes the design path it resolved from `**Spec:**`; the
  recorder no longer parses that field. An unresolved design is recorded as
  null with a `BLOCKED` verdict.
- `finish` rejects a repair pass without a repaired finding. `summary` is
  agent-readable JSON with verdict counts, abandon reasons, per-plan chains,
  repeated finding patterns, outcome coverage, and anomalies, each carrying
  run IDs.
- `outcome` records one label (`good`, `false-ready`, `noisy`, `abandoned`)
  and an optional note, and may be re-recorded.
- Reviewer protocol: a `repo-reality` finding must cite a repository path
  other than the reviewed design or plan.

## 1.3.1 - 2026-09-02

### Changed

- Plans that explicitly name a required implementation base now block before
  reviewer dispatch when that base is unresolved or not an ancestor of the
  current `HEAD`.
- Provider-free coverage now includes the stale implementation-base boundary.

## 1.3.0 - 2026-08-30

### Changed

- Scoped re-review stops at unmapped material findings instead of widening the
  repair or starting another invocation.
- Each invocation uses at most a primary role and one triggered risk role;
  fresh closure agents do not add roles.
- Authority-preserving repairs need no approval. Unresolved product decisions
  are grouped into one checkpoint.
- Reporting now validates each receipt from the same bounded byte snapshot used
  for its size and SHA-256, avoiding repeated reads of one review/outcome pair.
- Source installation ignores only an ordinary `__pycache__` containing regular
  `.pyc` files; unsafe cache entries and runtime-manifest drift still fail.
- User and evidence guides now lead with installation and the basic workflow,
  then separate safety boundaries, operations, measured support, and residual
  limits.

## 1.2.0 - 2026-08-30

### Added

- The optional local `pre-sdd-review-evidence` CLI records provider-neutral,
  content-bounded review and outcome receipts. Recording is non-blocking and
  never changes a review verdict.
- The skill now starts compatible evidence before semantic review, finalizes
  it after the verdict, and hands a controller-local run ID only to an
  explicitly combined SDD flow.
- Product and maintainer guidance now documents explicit launcher install,
  local receipt privacy, immutable outcome limits, heuristic candidates, and
  the native-platform `not_measured` boundary.

## 1.1.0 - 2026-08-29

### Changed

- One invocation reviews exactly one implementation plan. Separate plan-local
  reviews never produce an aggregate `READY`.
- Structural document repairs now record a repair-impact map and receive a
  bounded regression re-review. The two-pass repair limit is unchanged.
- Final `REVISE` and `BLOCKED` reports include an unresolved handoff packet
  and a compact pass receipt. User documents and full model responses are not
  stored.

### Verification

- Added synthetic fixtures for schema-consumer drift, vacuous state
  verification, and conditional edit-surface drift.

## 1.0.0 - 2026-08-29

### Notes

- This is the first independent product release contract for Pre-SDD Review: a
  Codex-only readiness gate with provider-free contract evidence and
  documented maintainer protocols.
- This entry records the release contract only. It does not claim that a tag,
  published package, or GitHub Release exists.
