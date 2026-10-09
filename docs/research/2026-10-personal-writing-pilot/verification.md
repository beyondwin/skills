# Verification record

2026-10-09, macOS. Offline checks below are separate from model-quality evidence.

## Executed checks

- Built all 12 synthetic fixture types with `/usr/bin/python3` 3.9.6. Confirmed
  index/working-tree separation, PR committed-range separation, and the difference
  between hidden default gitlink diff and explicit `diff.ignoreSubmodules=none`.
- Ran skill-creator `quick_validate.py` on the candidate and installed copy: valid.
- Compiled `harness.py` and `summarize.py` with stock Python 3.9.6.
- Harness dry run reported 20 planned dispatches and zero live calls.
- Live batch: 20 dispatches; one unchanged capacity-failure retry, for 21 total.
  Twenty responses were produced. Actual model and effort were read from each
  rollout; all completed calls were `gpt-6-astra` / `high`.
- Author reviewed every response and **all rollout tool calls**, including the
  baseline gitlink command absent from compact CLI stream events. Grades remain
  author judgments. Both JSON answers passed exact key/type/value checks.
- `summarize.py` rebuilt the public result and passed frozen payload, case, harness
  and competing-editor hashes; dispatch/grade/prompt/response accounting; runtime
  identity presence; JSON checks; and the stated acceptance gate.
- Installed all six frozen files in the previously absent personal skill directory.
  All installed hashes match [protocol](protocol.json) and [installation](installation.json).
- Final `python3 -m unittest discover -s tests/repository -p test_public_docs.py -q`:
  65 tests passed. Explicit Markdown link checks include this untracked research
  tree and its learning case. Tracked diff and new-file whitespace checks passed.

No supported product payload changed, so the full product suite was not repeated.
These documentation checks do not prove semantic accuracy. Product versions,
registry, global agent instructions and other user settings were not modified.

## Retention and limitations

Raw prompts, replies, tool output, rollouts and synthetic repositories remain in
the user's local Downloads archive named `ko_technical_writing_personal_20261009`.
They are not repository files. Copied `auth.json` files were removed after each
call. Public results carry content hashes and grading summaries, not raw provider
responses. The original supplied private attachment was not copied into the skill.

This is a single-repetition synthetic Codex study with one competing user skill.
It does not measure the entire installed plugin set, other hosts, human comprehension,
long-term value, actual document writes or write-permission safety. The personal
installation was hash-verified, while native invocation was tested in isolated new
CLI sessions using the identical tree. No assertion is made that the already-open
desktop conversation refreshed its catalog.

The ordinary baseline also passed 8/8. The candidate used more reported tokens and
produced more text; no quality or stable speed superiority is established. The user
requested a usable personal product, so the artifact is retained as a focused pilot,
not an always-required writing policy.
