# how-it-works testing

Keep provider-free rule checks apart from optional live runs that may cost money. Never
commit user topics, provider conversations, or private logs as Git test fixtures.

Terms:

- fixture: a prepared test case under `tests/products/how-it-works/`.
- `current-bounded`: only the version and hash are bound.
- `not_measured`: not checked yet.

## Provider-free evidence

The required evidence is `python3 scripts/verify.py --skill how-it-works`.
`tests/products/how-it-works/cases.json` and
`tests/products/how-it-works/test_contract.py` prove shape and installed-file rules
only. They don't prove live model quality or identical behavior on each supported
host.

Deterministic fixtures (rungs by English label):

- `broad-slice`: a civilization-sized noun is cut into three slices with one question.
- `missing-rung`: `/how-it-works DNS` plus the Korean "flow" type word. Only the type
  is filled; it explains at default picture in the same turn and asks no closed depth
  question.
- `default-dns-picture`: `/how-it-works DNS` explains at default picture.
- `explicit-dns-path`: the six chat parts appear and no host tool is required.
- `implicit-positive`: activates as intended without being called by name (implicit).
- `near-miss-debug`, `near-miss-eli5`: similar requests that must not activate
  (near-miss). `/eli5` is not this skill.
- `jargon-rung`: an explicit "easy" alias beats jargon and selects picture.
- `no-renderer`: with no renderer, the mermaid source and numbered hop list remain,
  and this is not a failure.
- `no-fetched-source`: with no fetched URL, the citation heading is left out and no
  citation is invented.
- `explicit-fracture-jargon`, `explicit-path-jargon`: an explicit fracture or path
  beats the jargon default.
- `english-explicit-fracture`: pins an English fracture pick and English output.
- `jargon-without-depth`: with no depth pick, jargon keeps the skeleton default.
- `topic-number-is-not-depth`: the number in `Raft term 20` is not read as fracture.
- `explicit-numeric-depth`: only an explicitly picked number, like "depth 5", is read
  as the picture alias.
- `fracture-keeps-map`: fracture keeps the baseline Mermaid and numbered hops in the
  Map and puts the failure/regime table in the Body.
- `high-stakes-no-lookup`: respects "don't search", marks date- or
  jurisdiction-dependent claims unverified, and invents no statute ids.
- `high-stakes-english`: picks the English banner only.
- `high-stakes-comparison`: explains the tradeoff under the user's conditions and
  doesn't force a personal recommendation.

What these checks prove and don't prove:

- Passing the installed-file contract proves file identity, portable frontmatter, and
  forbidden strings only.
- They also reject exact returns of the old high-stakes banner and the old DNS jargon
  wording. That proves static agreement between docs and fixtures only.
- `test_skill_skeleton_mirrors_output_chrome` keeps the reply skeleton in `SKILL.md`
  equal to the one in `references/output.md`, and other pins keep the picture box rule
  and the hop id label rules the same in `output.md` and `visuals.md`. That proves the
  files agree, not that a model emits the skeleton or reads the references.
- Whether a real model follows the depth precedence is `not_measured`. So are the
  truth of the explanation, real Korean register, English output quality, the model
  producing all six parts, and Mermaid parser/renderer results.

`test_release_and_repeatable_install_contract` checks the product version, the
extraction marker in both READMEs, that the old direct `ln -s` command is gone, and
that no relative link points at docs outside the installed files. Product checks never
run the install code against the real HOME.

The integration owner's `tests/repository/test_installation_contract.py` runs the
install counterexamples. It uses temporary source/target paths with spaces: first
install, repeating the same link, a real directory, a different link, a dangling link,
and a race. First install and repeat must succeed; on refusal, source and target bytes
and links must be unchanged.

## Optional live smoke

Live runs are local, explicit, optional, and may cost money. CI never requires them.
Don't describe a payload contract pass as evidence of a live call.

Supported hosts stay Codex and Claude Code, and live evidence for the current
installed files is `not_measured`. Support scope and current measurement are judged
separately. No live record is committed.

The pure functions of the new evidence contract live in
`tests/products/how-it-works/live/evidence_contract.py` and are not part of the
installed payload. Inputs in `test_evidence_contract.py` are synthetic unit-test data,
not real run records. No real new record file is created.

- `observe_text` observes only these as `lexical` (string level): a closed, non-empty
  Mermaid fence; the same H1/H2 hop ids in source and body, where a branch id such as
  `H3a` in the source counts as `H3`; and duplicates in the numbered list.
- `skill_loading` needs a separate `host_event`, `mermaid_syntax` needs a real
  `parser` or `renderer` run, and `meaning` needs a `semantic_review`. Loading is never
  inferred from the skill name being mentioned or from output chrome.
- Every dimension has a `status` and a `method`; with no source it is
  `not_measured/not_run`. A near-miss judges invocation only and leaves the five output
  dimensions unmeasured; `record_binding` rejects a near-miss case with any other
  status. Case ids must come from `live/cases.json`, and `host` must be `codex` or
  `claude-code`.
- Schema 2 records the real product version, the hash from the existing
  `payload_sha256(Path)`, model, host, client/runner version, run date, and per-case
  invocation plus five dimensions. An unknown model is `null` and the result is
  `unbound`. Compute the hash after all payload edits are done, and take the real
  version from `load_product_release(Path).version`.
- A known model with matching version/hash is `current-bounded`; a mismatch is
  `different-payload`. That only means the submitted metadata agrees. It does not
  certify a real run or a quality pass, and the function does not certify that the
  declared method is true.

Direct unit checks cover: broken Mermaid is never promoted to a pass; hop mismatch,
duplicates, and absence; branch ids counted as their parent hop; unknown case ids,
retired hosts, and a measured near-miss dimension; null model; version/hash
mismatch; a real shared-hash change after a temporary reference edit; extra keys, bad
dates, missing dimensions, and boolean schema; and bad method declarations. Shape
alone never proves syntax, causality, rung changes, or accessibility. A parser or
renderer result is recorded only when one could already run; this work never requires
installing one.

The three existing synthetic prompts and the detailed schema and observation steps are
in `tests/products/how-it-works/live/README.md`. Its commands run only Codex and Claude
Code with JSON event output (`codex exec --json`, `claude --print --output-format
stream-json --verbose`), because `skill_loading` passes only on a host event read from
that stream. Never commit full responses, private
prompts, or credentials.

## Commands

```bash
python3 scripts/verify.py --skill how-it-works
python3 scripts/verify.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/how-it-works -p test_evidence_contract.py -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/how-it-works -p 'test_*.py' -v
git diff --check
```

The shared `how-it-works-contract` stage discovers `test_*.py` in
`tests/products/how-it-works`, so the `--skill` check runs both `test_contract.py` and
`test_evidence_contract.py`. Use the direct `unittest` commands to run one file
quickly. A pass of the product-level pure checks does not stand in for full
verification or for live model quality.
