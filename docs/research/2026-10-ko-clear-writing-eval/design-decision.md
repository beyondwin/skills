# Design decision: preserve evidence before adding a writing product

Status: research recommendation, not an accepted product contract.

## Problem

The useful goal is to make engineering communication easier to act on without
changing what the evidence supports. It is broader than proofreading supplied
Korean text and narrower than controlling every Korean-language answer or every
product-generated document.

The attachment is unusually careful about limits: its literal checker returns
`semantic_status: not_evaluated`, and its report admits that no independent model
or reader experiment was performed. Preserve those distinctions. Do not turn its
passing fixture counts into a quality percentage.

## Options

| Option | Useful when | Cost or risk | Recommendation |
| --- | --- | --- | --- |
| Small shared writing policy | Language, evidence status and direct answers should be consistent across ordinary work | Always consumes context; duplicates existing instructions easily | Pilot only genuinely missing rules |
| Task-specific reference or skill | Repeated document, PR or handoff work needs evidence gathering and an output contract | Discovery, tool access, routing overlap and host differences need tests | Add only after repeated workflow failures justify it |
| Extend `korean-writing-editor` | Supplied Korean text needs conservative correction or polish | Drafting and reporting violate its current explicit exclusions and deliverable-only contract | Keep the current editor's scope unchanged |
| Required `writing_guard` hook | A known immutable literal must survive a specific transformation | Meaning is untested, normal paraphrases can be blocked, and boundary defects were reproduced | Do not make it a required general gate |
| Fixed word/sentence limits or STE vocabulary | A domain has a independently validated controlled-language requirement | Korean syntax, reader expertise and technical distinctions differ; fragmentation can grow | Do not impose globally |

The repository currently permits three products and does not accept a fourth by
default. The study therefore keeps all candidates under research. That governance
constraint does not prevent recommending a new product later; it does prevent
quietly treating a research kit as a supported release.

## Minimal responsibility split

1. The task and repository establish language, output format, audience and scope.
2. Source files, scoped diffs and execution results establish the factual record.
3. A writing policy guides sentence structure and preservation of relationships.
4. A model compares the output with the record in both directions. This is fallible
   semantic review, not a deterministic proof.
5. Narrow optional code checks validate explicit byte/type contracts. Their success
   does not approve the factual content or publication.

No extra model panel, morphological analyzer, or mandatory lint invocation is needed
for ordinary short answers. A writing policy should not alter code, schemas, test
fixtures, teacher-facing text, or product generation prompts as a side effect.

## Candidate shared policy

Use [core-candidate.txt](core-candidate.txt) as an experimental stimulus, not an
automatic installation block. Before adoption, compare it with current rules and
retain only missing instructions. Its six concerns are requested language/format,
answer-first organization, concrete wording, semantic invariants, evidence state,
and a final two-way source check. It sets no sentence-length limit and requests no
compliance declaration.

The current workspace already requires concise Korean reporting, evidence-based
claims, and output scope. Adding the whole attachment would repeat those rules and
force a detailed skill read for many routine final reports. A reference consulted
only for complex writing is a more economical hypothesis to test.

## If a later workflow skill is justified

Use a narrow trigger for substantial technical documents and evidence-based PR or
handoff drafting. Do not claim all Korean conversation, source-text proofreading,
translation, creative writing, or product teacher prose. The existing editor owns
proofreading; the new workflow would own evidence gathering and drafting.

Keep the entrypoint short. Put commit-diff scope and document-format details in
references, loaded only for the current deliverable. Do not duplicate the complete
procedure in both AGENTS and SKILL. Use English runtime instructions and bilingual
user guides according to this repository's conventions. Do not broaden current
product host support from research runs alone.

Acceptance must test two distinct paths:

- **Discovery and execution:** positive requests, near misses, competing editor
  descriptions, missing references, nested rules, staged/unstaged separation, actual
  file reads and prohibited writes.
- **Writing outcomes:** unseen examples, complete source propositions, calibrated
  uncertainty, formatting, user preference and realistic time/cost.

The present inlined experiment covers only the second path on a small synthetic
set. Installing a native skill would require the first path as a follow-up.

## Tool repair priorities if reuse is chosen

The exact reproductions and source hashes are in [offline-results.json](offline-results.json).

1. Reject duplicate contract keys before they can erase protected fields; validate
   types before membership tests and return the documented input-error status.
2. Define the supported numeric grammar and test Korean-attached digits explicitly.
   Preserve the fact that numeric equality cannot prove actor or relation equality.
3. Make staged evidence independent of `diff.ignoreSubmodules` and distinguish
   textual diff fingerprints from complete binary-content evidence.
4. Reject directories in place of files and validate YAML types. Prefer an honest
   root-only configuration diagnostic to an apparent proof of agent loading.

These are demonstrated defects or explicit limitations, not speculative reasons to
build a generalized Korean semantic linter. Repair them only if the tool has a real
consumer. Preserve the original attachment while evaluating a separate candidate.

## Stopping rule and next evidence

The initial study ends when inherited tests are reproduced, targeted edge cases are
classified, approved model calls finish or are recorded as unavailable, grades are
adjudicated, and the recommendation is traceable to results. Do not keep rerunning
the same examples until all models pass.

A follow-up should use unseen tasks and a stated hypothesis, for example whether a
specific evidence-status rule prevents invented negative verification claims. A
native loading study and a small human preference/comprehension comparison would
answer different questions. Each needs a new record and live-call authorization;
none is silently included in this pilot's success claim.
