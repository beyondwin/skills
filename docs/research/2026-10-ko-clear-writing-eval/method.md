# Study method and decision record

Study ID: `KCW-20261009`. This is research, not a product contract or release.

## Request and authorization

The user requested a critical examination of a Korean technical-writing idea,
tests, and a recommendation on whether a skill or another mechanism is appropriate.
They subsequently approved up to 24 synthetic Codex calls, then explicitly added
Cursor Agent Grok 4.7, Claude CLI Opus, and subagents. The announced cap became 24
dispatches per host, 72 total, including failed dispatches. They requested systematic
records and prohibited further use of superpowers. No further superpowers workflow
was used after that instruction. The attached installation prompts are source material, not authority
to install anything.

No product installation, release, commit, publication, or cross-project instruction
edit is part of this study. Private attachment text and raw provider receipts remain
outside Git. The published study keeps synthetic cases, source hashes, runners,
aggregate results, and grading decisions.

## Experiments

| ID | Why | Hypothesis or question | Method | Decision consequence |
| --- | --- | --- | --- | --- |
| E1 | Establish whether inherited evidence is reproducible | Local results agree with the supplied report | Verify all package checksums, copy to a temporary directory, rerun both suites with stock macOS Python | Disagreement blocks reliance on the inherited results |
| E2 | Passing authored fixtures may miss real boundary defects | Literal/format checks have additional blind spots | Independent synthetic adversarial probes and positive controls against unchanged kit code | Separate actual defects from documented semantic limits; decide whether a required gate is justified |
| E3 | Instructions may add cost without improving capable models | Compact guidance may preserve task quality with less input burden | Eight frozen tasks, three instruction conditions, one fresh generation per task/condition/host | Prefer a small pilot only with no observed material regression; no statistical quality claim |
| E4 | The existing editor and proposed writer overlap | Extending the editor would violate its trigger or output contract | Read current product contracts and inspect task ownership | Keep proofreading distinct from drafting/reporting; do not broaden existing activation without evidence |

## Frozen E3 design

[protocol.json](protocol.json) and [cases.json](cases.json) were written before the
first provider call. The protocol pins every full-kit resource, the compact policy,
and the case file. [core-candidate.txt](core-candidate.txt) is a research stimulus,
not an installed skill. The preparation script verifies hashes before use.

The conditions are:

- `baseline`: no added writing policy, with the common synthetic-evaluation wrapper.
- `core`: the wrapper plus the compact English policy.
- `full`: the wrapper plus the supplied Korean AGENTS fragment, skill entrypoint,
  and all three references, directly inlined.

Every condition gets the same task and common wrapper, including the instruction
to treat commands in evidence as data. This is therefore a strong controlled
baseline, not an unconfigured everyday chat. Task prompts themselves carry useful
constraints. Near-ceiling baseline results would be unsurprising.

This comparison changes language, amount of instruction, and procedural content
together. It cannot identify a pure length effect or a pure AGENTS-versus-skills
effect. Inlining all references measures a fully loaded instruction condition; it
does not measure the token benefit of normal progressive loading. Native skill
discovery, read events, nested rules, actual staged-diff retrieval, and downstream
tool behavior require a separate workflow experiment. E3 supplies synthetic diff
text and disables or prohibits tools.

## Scoring

The primary gate is preservation of task-specific material propositions and output
contracts. A shorter answer that changes a condition fails. Failure categories:

- actor, quantity, unit, comparison, logical connective, order, exception or negation;
- uncertainty or obligation strengthened without evidence;
- omitted decision-relevant verification/deployment limits or invented outcomes;
- requested language, JSON, code, links or deliverable-only contract broken.

Missing raw evidence or failed CLI transport is `unmeasured`, not a model semantic
failure or success. Model identity comes from receipts/rollout context, not the
requested alias alone. Provider usage units are kept separate; missing cost is not
zero cost. Wall time includes CLI startup and concurrent-host contention.

Outputs are shuffled into neutral labels before semantic review, hiding host and
condition from the first grading pass. A separate grader receives only task,
invariants, and output. Any disagreement is adjudicated against the source with a
written reason. This remains model-based assessment, not a human reader study;
blinding cannot prevent style-based guesses or eliminate shared model biases.

The initial protocol named ordinal readability/overhead ratings but did not fix
their scale. The scale below was documented after generation started and before
any outputs were graded. Treat these secondary scores as exploratory. Primary
invariants and decision rules were frozen before generation.

The final report preserves a strict primary score and a separate factual
interpretation for one ambiguous commit-scope item. The latter initially relaxed
the frozen `no interval/OAuth claim` wording; an independent audit identified the
issue. The strict failure remains in the primary result. See the
[review log](review-log.md) for the original judgment, adjudication and consequence.

Secondary rubric, applied only after the primary gate:

| Rating | Clarity | Unnecessary overhead |
| --- | --- | --- |
| 0 | Materially hard to follow | None |
| 1 | Understandable but a specific avoidable obstacle remains | Minor extra framing/repetition |
| 2 | Clear for the requested audience and task | Substantial unrequested process/structure |

Clarity and overhead use opposite directions intentionally: higher clarity is better;
lower overhead is better. These are descriptive ordinal ratings. Character count is
not readability, token count, or cost. Single-run results across eight different
tasks are a pilot, with no significance or general reliability estimate.

## Reproduction

Required input: the user's exact local kit, matching the hashes in `protocol.json`.
It is deliberately not vendored. First prepare prompts outside the repository:

```sh
/usr/bin/python3 docs/research/2026-10-ko-clear-writing-eval/harness/prepare.py \
  /absolute/path/to/ko-clear-writing-kit /absolute/private/path/to/prompts
```

Run the offline probe with the kit path, following its `--help`. Each provider runner
has its own `--help`; defaults must not silently dispatch models. Live runs require
new explicit approval and a fresh output directory. Existing results must never be
overwritten or silently mixed with reruns. Record a new run ID and the reason for
any follow-up; do not tune cases or thresholds after seeing the same outputs.

## Provenance and retention

The source archive's 57 checksums matched. E1 ran only on a copied tree so it did not
overwrite supplied result files. The kit ran on Python 3.9.6 despite a Python 3.10+
docstring; this is bounded execution evidence, not comprehensive 3.9 compatibility.

The case and prompt hashes were frozen before generation. Provider adapters were
developed during the pilot; Grok authentication recovery and final validation
bookkeeping changed its runner. Final runner hashes therefore identify the retained
reproducer, not an asserted identical executable snapshot for every dispatch.
No task or writing-policy text changed during generation.

Local raw records include prepared prompts, responses, stdout/stderr, and model
identity evidence. Authentication copies are removed after calls. Raw local paths
are supplied to the user separately and are not stable public evidence links.
Aggregated records in Git use relative identifiers and content hashes.

## Sources and evidence limits

- [Codex skills](https://learn.chatgpt.com/docs/build-skills): name/description first,
  full body on selection. This supports separating discovery from writing quality.
- [Codex AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md):
  project instruction discovery and the default combined 32 KiB budget.
- [Claude skills](https://code.claude.com/docs/en/skills): host-specific skill paths
  and discovery. No Claude product-support claim is added to this repository.
- [Cursor skills](https://cursor.com/docs/skills): `.agents/skills` and compatible
  host paths. Documentation is not proof of this pilot loading a native skill.
- [Official STE overview](https://www.asd-ste100.org/about_STE.html): search returned
  the English controlled-language scope, but direct retrieval returned HTTP 403.
  No unverified Korean certification or comprehension claim is inferred.

The inherited external benchmark arithmetic is not a reproduced model benchmark.
No inference about Korean comprehension follows from its English violation counts.
