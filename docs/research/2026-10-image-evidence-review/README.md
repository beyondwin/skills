# Evidence-based image review redesign

Started: 2026-10-23. Status: development in progress; no improvement claim yet.

The [preceding repair](../2026-10-image-review-repair/README.md) retained
correction-condition preservation but failed to improve count, occlusion and
false-rejection errors. The user requested a redesigned review method, actual
Grok comparisons, further improvement until useful, and incremental commits.
The [decision case](../../learning/cases/2026-10-23-image-evidence-review.md)
records the alternatives and adoption decision.

## Direction and target

The skill must change acceptance decisions, not merely lengthen prompts or make
more image calls. Separate three responsibilities: interpret the original
requirements, record what the image shows, and decide whether that evidence
violates a requirement. Required counts and complete visibility remain different.
Object parts, background surfaces and independent props must not be conflated.
Every rejection needs a requirement and localized image evidence; an unresolved
critical condition remains unverified, not an invented failure or pass.

Candidate A uses an instance inventory before count comparison, an explicit
foreground-boundary check, and a check of the benign interpretation before a
candidate is rejected. Aesthetic ranking happens only among eligible candidates.
It adds no provider, helper, compulsory second agent, or image-generation budget.
The previous crop-heavy variants are not revived.

## Comparison fixed before candidate results

The control is the complete 2.1.5 product at commit `6e9eef6`. Both arms use a
frozen complete payload, isolated fresh Grok homes, the same CLI 1.0.67 executable,
requested `grok-4.7/high`, identical original requirements, anonymous source
images, report contract and budget. Actual model and effort come from native
history. No generation is allowed in review sessions. Input and delivered image
hashes, payload integrity, normal completion and credential cleanup are checked.

The 22 images from the prior historical and transfer comparisons are now all
development data. They are grouped by scene while preserving selection pools;
each session has at most 30 turns and 900 seconds. Candidate development needs
at least 20/22 correct eligibility decisions, fewer count and occlusion errors,
no increase in false accepts or false rejects, and no regression in pool
decisions. All-failing pools must be held. Missing results and unresolved labels
do not earn correct decisions; rejecting or holding a known valid candidate is
a false rejection. Each revision and failed result is retained.

Clarified before the first completed development verdict: the count domain
includes total-object counts and required visible-part counts; both subtypes
are also reported separately. If the concurrent control makes zero errors in a
stratum, the candidate must retain zero errors there. Improvement below zero is
impossible, and a ceiling tie is not described as improvement. The other gates
remain unchanged.

The equal budget is per contemporaneous control/candidate block: six fresh
sessions allocate 180 turns and 5,400 seconds per arm. The earlier two combined
studies allocated 60 turns and 1,800 seconds. Splitting context and increasing
the total review allowance can improve the control too; do not attribute that
shared procedural change to the new skill or compare elapsed time directly with
the earlier study.

After a development candidate is frozen, generate 24 new originals across four
scene families, with one image call each and no corrective retry. Each family
includes three intended valid variations and three intended contrasts: incorrect
count, required-visibility failure, and a prohibited independent object. Intent
is not ground truth. Two independent reviewers see anonymous originals and
original acceptance conditions, without source prompts, version labels, prior
verdicts or expected defects. Their agreement defines clear labels; disagreements
remain separately reported, with all originals retained in the denominator.

The locked control and candidate review the same new images in two fresh
repetitions with equal budgets and counterbalanced arm order. Repetitions are
not independent images. Report each repetition, agreement, all candidate
decisions, false accepts, false rejects, count/visibility/extra-object strata,
all-failing and eligible selection pools, calls, turns, time and reported cost.
Reported orchestration cost may omit image billing.

The prospective fresh-image target is at least 90% correct on clear labels in
each repetition, no increase in either false accepts or false rejects or in any
defect stratum, and at least two net additional correctly classified unique images
against the control in each repetition. Both normal-candidate retention and
failure detection must improve somewhere across development and fresh images.
Unverified cases cannot supply an improvement. Report paired discordances and
an exact paired test; a small effect is not statistical or general superiority.
If the holdout informs another revision, it becomes development data and a new
untouched comparison is required. Do not reuse it as an independent final test.

Finally rerun the original generation tasks under the original two-image-call
limit. Inspect every generated original with blinded reviewers, preserve
correction conditions, and require no loss in usable delivery or increase in
unnecessary corrections versus the control. Successful review is distinct from
better aesthetics; a quality tie cannot be called an aesthetic win.

## Evidence and verification boundary

Private prompts, generated images, native histories, isolated homes and raw
provider receipts stay outside Git in `/tmp/image-workbench-review-20261023`.
Only aggregate methods, results and safe decision records are committed.
Offline contracts establish packaging and authorization behavior, not visual
accuracy. Product and full repository checks follow the final runtime change;
they are separate from the live comparisons above.

## Development decisions

Candidate A's two boat blocks completed normally. Control and A each classified
4/6 correctly, including two occlusion false accepts, and selected correctly in
2/3 pools. A therefore fails the mandatory all-failing-pool hold criterion and
is not eligible for adoption. The remaining frozen queue continues so its full
results and cost are retained.

Both A runs received the complete frozen SKILL and rubric text, and source image
bytes were delivered intact. On the two missed occlusions the final report
substituted countability and being inside the frame for the required complete
boundary. This does not establish whether perception or applying the observation
was the limiting step. Candidate B therefore requires a compact observation row
for every critical condition before its status, including positive boundary
evidence for a pass. It first screens the same two development failures under the
same block budget. A failure stops B's full comparison; a pass permits the other
frozen development blocks. The screen is not unseen evidence or an extra retry.
Evidence claims are inspected against pixels as well as scoring the verdict.

B's two-image screen completed normally at 1/2 correct. It still accepted and
selected one image with a hidden required boundary, now claiming an unobstructed
contact that the image does not show. B is rejected without dispatching its other
five prepared blocks. A fresh independent reviewer, given only anonymous originals
and the original conditions, confirmed both full-visibility failures. More detailed
prose does not by itself make the observation reliable.

The next development pilot separates observation from acceptance in fresh
contexts. A neutral observer receives only images and physical inventory/contact
questions, without the original request, expected count, eligibility task, skill,
prior judgment or answer key. A decision context receives the unchanged original
requirements, images and unedited observation record. The two stages share the
original total 30-turn/900-second block allowance; both use the same pinned Grok
model and no image calls. Screen the two occlusion negatives and four table images
so retaining normal candidates remains necessary. Only a grounded 6/6 result
permits expansion. External staged execution is a workflow hypothesis test, not
evidence that the installed skill invokes a native independent observer; adoption
also requires that actual execution path and summed child usage to be verified.

Pilot C did not reach acceptance decisions. Both neutral observers exhausted
their 12-turn allocation while exploring crop tools and image libraries, without
producing a normal observation record; neither decision session was dispatched.
The failures are retained and do not measure the perception hypothesis. The next
pilot, D, gives the observer only `read_file` and `write_file`, restricting it to
original images and a compact observation record. It uses the same six development
images and the same cumulative block allowance. The restricted observer runner is
frozen separately before execution. Tool restriction is part of this intervention,
not an invisible shared harness improvement; an eventual comparison must give
the control the same available capabilities and account for both stages.

The original full development queue also exposed scope failures in both pebble
blocks. A attempted reads at guessed paths outside its private temporary directory;
the reads failed. The control wrote a path pointer into the shared temporary
directory. Neither block earns verified primary decisions. Supplemental visual
scores remain explicitly separate; no failed block is replaced by a retry.

The D runtime audit found that CLI allowlists use different names from some
transcript tools. Unknown names made the CLI retain its broad tool set. This also
affected the original control/A queue, B and C: their actual image-call count was
zero, but image tools were not structurally unavailable as intended. Both arms of
the original comparison had the same broad availability. That distinction is
retained in the results. D additionally exposed bundled skill descriptions in one
observer, despite empty preparation-time discovery; its decisions are not
dispatched and it cannot qualify a candidate. New dispatch pauses for corrected
tool identifiers, bundled-skill exclusion and a minimal native-init canary. Static
discovery alone did not establish the execution profile.

The first runner check falsely rejected native records lacking a legacy memory
metadata key. Its raw failure is preserved. The pinned CLI's local guide states
that `GROK_MEMORY=0` forces memory off; the runner set that variable and both config
flags to false. The reviewed normalization additionally requires exact config,
native v2=false, a missing or exactly false legacy key, empty agent/persona lists
and no memory data in the fresh home. It rejects missing v2 or contradictory
values. This is a corrected evidence check, not a successful rerun or weakened
visual scoring rule.

### Completed A comparison and subsequent screens

The complete A comparison does not qualify. The primary denominator stays 22:
control has 9 correct, 4 incorrect and 9 unverified decisions; A has 12 correct,
5 incorrect and 5 unverified. Besides the two pebble scope failures, the control's
four carafe decisions are unverified because it inspected contrast, brightness and
saturation transformations despite the original-pixel inspection contract.
These unequal verified subsets are not a quality improvement comparison.

For diagnosis only, scoring every raw report regardless of those scope failures
gives the following results. This table cannot override the primary failures.

| Supplemental raw-report measure | Control 2.1.5 | A |
| --- | ---: | ---: |
| Correct eligibility decisions | 16/22 | 17/22 |
| False accepts | 2 | 2 |
| False rejects | 4 | 3 |
| Correct pool choices | 6/8 | 5/8 |
| Actual turns | 108 | 121 |
| Sum of run seconds | 2,705.750 | 3,182.866 |
| Reported orchestration cost, USD | 1.2975182 | 1.74992696 |
| Actual image calls | 0 | 0 |

Even the supplemental result misses 20/22, retains both occlusion false accepts,
regresses pool selection and costs more. A is rejected.

After the corrected read-only canary, E isolated each original in its own neutral
observation session, capped at three turns and 100 seconds with compact JSON.
All six runs had the intended tool and skill profile, intact delivered originals
and the same actual model/effort. Only two completed normally; four timed out, so
neither decision stage ran. The two normal table observations still undercounted
supports. A tuple/list representation mismatch in an additional model check is
recorded separately from both the timeouts and visual errors. The common verifier
now tests that representation, the empty-MCP meta-tool exception, actual tool
calls, unexpected skills, CLI warnings, missing finals, JSON and timeout cases.

F is the final focused Grok observation pilot before considering a separately
controlled Codex review path. It asks one physical question per image, selected
from the original request: table-support endpoints and their floor/attachment
relations, or leaf boundaries at contacts. It provides no requested number,
eligibility condition, prior verdict or known coordinates. Every image in a
family gets the same question. The response is capped at 120 words; each observer
has at most three turns and 200 seconds. Observation and decision still share
30 turns and 900 seconds per block, with no additional correction or retry.
Failure cannot qualify a candidate. A change of reviewing host would require a
new same-host control/candidate comparison; gains across hosts cannot be called
skill effects.

The rejected B working-tree changes were removed from the active installed product.
Its frozen experimental payload and patch remain private, and all running jobs use
their pinned copies. The installed product remains the committed retention-only
2.1.5 until a new candidate qualifies; no experimental 2.1.6 is released.

F completed all six focused observations normally, but both decision sessions
exhausted their remaining turns. Including observers, the boat block used exactly
30 turns and 772.788 seconds; the table block used 30 turns and 786.194 seconds.
The original observations were copied byte-for-byte and actually read by both
decision sessions, with identical actual `grok-4.7-build/high` throughout. The
boat decision also inspected enlarged diagnostics, violating the original-pixel
inspection contract. Neither block qualifies for primary quality scoring. The
table's unfinished report rejected all four candidates, including the three valid
ones; it is diagnostic evidence only. F improved observation completion over E,
not demonstrated perception accuracy or final review. Further prompt-only Grok
review iterations stop here.

### Separate Codex review comparison

Before any Codex quality result, prepare a distinct comparison of the same control
2.1.5 and frozen B content under Codex CLI 0.163.0, `gpt-6-astra/ultra` in both
arms. That model/effort is verified in the current user's native host record.
The first screen uses the same two boat and four table originals, original
requirements and report contract. Each block allows 30 completed native model
responses and 900 seconds, with zero image calls. Completed responses are counted
by unique native response identity; they are not equated to Grok's turn field.
Full skill content and resources are pinned explicitly, with matching tools,
fresh homes, memories disabled and no current installed-copy injection.

The screen needs all six candidate decisions correct, grounded final evidence and
no false-accept or false-reject regression. It is still historical development
data. A control ceiling tie is not a skill gain. The remaining development blocks
may check whether that ceiling extends to other requirements; they cannot turn a
tie into an improvement. Do not pool Codex and Grok judgments. Native delivery and
configuration canaries are infrastructure checks without eligibility questions;
their outputs cannot contribute to quality scores. A content-injection comparison
does not establish native skill discovery or activation, which needs its own smoke.

All four Codex screen runs passed independent execution and original-byte audits.
Both arms classified 4/6 correctly, with zero false accepts, two false rejects and
2/3 correct pool choices. B fails its 6/6 screen; no skill gain was observed.
Control used 10 completed responses and 230.535 summed seconds; B used 13 and
313.182 seconds. Both correctly identified the two hidden leaf boundaries. Both
also explicitly counted four feet in two valid table candidates, then rejected
them because a rear leg's full outline was not exposed. In these runs, the error
was strengthening the requested visibility, not failing to perceive a fourth foot.

An audit of the original task, original blind judging, later corpus and current
Codex inputs found unchanged brief and compact-condition bytes. The original
judges explicitly described the partial overlap while accepting the separately
visible legs and feet. No reference labels are changed. Natural-language scope
still permits disagreement; this historical screen cannot establish an infallible
answer key or general quality advantage.

Candidate G therefore replaces the broad full-visibility priming with a scoped
requirement check: whole-subject framing, directly visible named parts, and
explicitly unobstructed targets are distinct. It retains original qualifiers,
counts observed instances, and grounds rejection at the strength actually asked
for. It adds no witness table, observer stage, image transformation or generator
change. The complete original correction base remains unchanged. Its private
11-file pin is frozen before new calls; installed 2.1.5 stays unchanged.

G first screens the same six originals with the same Codex profile and budgets.
The existing control is a development comparator, not an independent replication.
The candidate must classify all six correctly with grounded reasons and all three
pool choices correct; in particular it must retain the actual occlusion and
missing-part rejections. A pass permits a fresh paired 22-image development run
with both arms, then the separately frozen fresh-pixel test. Failure remains in
the record. Neither a screen win nor changing hosts alone qualifies adoption.

G passed that screen: 6/6 correct, zero false accepts or false rejects, and 3/3
correct pool choices, against the historical control's 4/6 and 2/3. Its reasons
identified the separately visible rear feet while retaining both leaf-rim and
the missing-foot rejection. Both new runs passed independent runtime and original
image audits, using nine completed responses and 180.276 summed seconds. These
six reused images supply a development signal, not an independent replication
or general superiority. The paired 22-image comparison now executes both arms
afresh with unchanged G, budgets and input bytes.

Before G scores were opened, the scoring adapter was strengthened to bind the
on-disk report back to the already-audited native final and final-output file.
The prior adapter and amendment hashes remain preserved; five negative checks,
including report, final-file and rollout tampering, passed independently on
macOS Python 3.9. No question, model run or eligibility criterion changed.

The fresh-pixel comparison also includes a plain Codex review arm, as named in
the frozen generation design. All three arms receive the same task, original
pixels, schema, budgets and host profile; only plain omits skill content and
resources. G versus 2.1.5 remains primary. G versus plain is a separate comparison
and must meet the same prospective benefit gates before claiming a benefit over
ordinary review. It cannot replace a failed primary comparison. Report both
repetitions without treating repeated judgments as additional unique images.

Before fresh generation or labels, fix the pool-construction rule as follows.
Within each family, sort anonymous identifiers. If at least two originals have
clear negative consensus, place the first two in one all-failing pool and every
remaining original in a second pool; omit an empty remainder. Otherwise use one
pool for that family. Every successful original, including disputed ones, appears
exactly once per arm and repetition. The model sees neither labels nor this
construction rule. Record actual pool coverage; intended generation targets never
determine eligibility or pool membership. This stratification tests withholding
selection as well as retaining eligible images without dropping hard cases.

### Fresh paired development result

The [safe aggregate](development-codex-g.json) records this development stage.
Both arms completed six fresh Codex sessions on the same 22 historical originals.
All 12 sessions and the final score bindings passed independent audits. The
control classified 19/22 correctly versus G's 22/22; false accepts stayed at zero,
false rejects fell from three to zero, and pool choices improved from 7/8 to 8/8.
The control's three errors were two separately visible table-leg cases and one
known-valid carafe held because surface detail could not be confirmed. This last
hold counts as a false rejection under the fixed metric, not a missing run.
Count, missing-foot and occlusion cases were already correct in both arms; their
ceiling was maintained rather than improved. Unique paired improvements were
three, regressions zero (exact two-sided paired p = 0.25).

The control used 33 completed responses and 666.873 summed seconds; G used 31 and
644.564 seconds. Actual model/effort matched, original bytes and final reports
matched, temporary authentication was removed, and image-generation calls were
zero. The development gate passes. These historical images do not establish
fresh-image performance, ordinary-review superiority, native activation or image
quality. G stays frozen for the already planned 24 fresh Grok generation attempts.

Before fresh annotations are opened, disputed-reference scoring is fixed. A shared
failed condition gives a clear negative only when no other condition has a
pass/fail contradiction between reviewers; uncertainty on another condition is
retained in the disagreement table but cannot cancel a shared demonstrated
failure. A positive requires all four conditions to pass in both records and the
canvas check to pass. Every other reference is disputed. Item scores report the
clear denominator and pessimistic/optimistic bounds over all successful originals.
A selected known-positive candidate is a correct pool choice even if another
candidate is disputed. A selected disputed candidate is unresolved; withholding
selection is correct only when every candidate is a clear negative, incorrect if
a known positive exists, and otherwise unresolved. Report bounds and unresolved
pools explicitly; they cannot be counted as a successful gate. Both repetitions
and both comparisons retain the previously specified benefit gates.

### Fresh generation inspection deviation

The initial dispatcher stopped after two of the 24 planned calls. Both calls
produced one native original and an exact project copy, but the generator omitted
its separate `read_file` inspection. Both original protocol failures remain
recorded. No image or annotation was opened before this amendment: continue only
the 22 untouched jobs with unchanged prompts, model, budgets and runtime, without
replacing either initial image. The continuation tolerates only this precise
inspection omission; any other error halts dispatch. All originals still require
independent source and path audits and direct inspection by the blind reviewers.
This distinguishes valid raster sources for a review experiment from a successful
generator output workflow. The omitted generator inspections cannot pass the
original output-contract gate or support an end-to-end product claim.

### End-to-end execution plan

The final generation check uses the unchanged lamp, pebbles and carafes briefs
from the preceding delivery study: one task per plain/control/G arm, nine tasks
total, at most two image attempts each. Codex performs planning and review under
the same pinned profile in all arms; the user's expressly requested Grok CLI
performs drawing. This explicit provider choice is common to all arms, not a new
silent-fallback rule in the product. Native skill activation is verified separately
from the content-pinned comparison.

A common relay leaves provider credentials outside the Codex workspace. It
records each request once, reserves the two-attempt budget before dispatch, runs
each drawing call in a fresh Grok home, and returns the unchanged original.
Failures consume attempts. Submitted prompt and ratio are compared with actual
native image-tool arguments; candidate and final-file hashes are traced to the
provider original. All generated candidates must be opened and retained. A
watchdog can detect an extra provider call after dispatch; it does not prove an
extra call was physically impossible. Such a violation remains a protocol failure.

Each task has at most 30 Codex responses and 900 total seconds including Grok
waiting. Each nested Grok session has at most 12 turns and the smaller of 600
seconds or the task's remaining time. Parent and nested response usage are reported
separately without equating model turn definitions. Cancellation must terminate
and reap every registered child and remove temporary authentication files.

Two fresh blinded reviewers score every original against the unchanged brief.
Usable delivery requires agreed hard compliance, matching canvas and mean craft
of at least 4/5. G must not lose usable delivery or increase corrections of an
already usable first candidate versus the control. Report all three tasks per arm,
first-candidate quality, chosen final quality, unnecessary correction, condition
retention and failures separately. Initial drawing variation is not attributed
to a review rule. Nine small tasks are an execution and regression check, not a
general aesthetic-superiority study. No new scene or retry replaces a failure.
