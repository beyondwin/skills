# Pre-SDD Review Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a registered Codex skill that defaults to reviewing, automatically repairing, and re-reviewing approved design and implementation-plan documents against repository reality before SDD begins.

**Architecture:** `pre-sdd-review` is a fourth independent product with one installable Markdown payload and provider-free contract fixtures. The controlling agent owns document repair; fresh reviewer agents remain read-only, a second reviewer is conditional on five high-risk classes, and the workflow stops with fingerprinted `READY`, `REVISE`, or `BLOCKED`. Existing registry, release, documentation, and verification infrastructure is extended without changing cached Superpowers files or the immutable catalog.

**Tech Stack:** Agent Skills Markdown/YAML frontmatter, JSON fixtures, Python 3.11+ standard library and `unittest`, TOML, Git, Codex subagents.

**Spec:** `docs/history/specs/2026-08-29-pre-sdd-review-design.md`

## Global Constraints

- Product ID and frontmatter name are exactly `pre-sdd-review`; display name is `Pre-SDD Review`.
- First public target is `1.0.0`; tag prefix is `pre-sdd-review-v`; license is Apache-2.0.
- `codex` is the only supported host at launch; every other host is `not_measured`.
- Default invocation means review, repair the resolved design and implementation plan, and scoped re-review. `review-only` must be explicitly requested.
- Independent reviewers are read-only. Only the controlling agent edits documents.
- Default repair is limited to the resolved design and plan. Do not auto-edit accepted ADRs, approved visual authority, application code, tests, configuration, or unrelated documentation.
- Allow at most two repair passes. Preserve unresolved material issues as `REVISE` or `BLOCKED`.
- Do not invent a missing product decision, broaden scope, add dependencies, or reduce severity to finish.
- Use only `BLOCKER` and `IMPORTANT` findings and only the five specified finding classes.
- One reviewer is normal. Dispatch a second focused reviewer only for runtime/framework removal, schema/data mutation, auth/security, public/private data boundaries, or external side effects.
- Zero findings is valid; do not require a finding count.
- `READY` records design SHA-256, plan SHA-256, Git `HEAD`, dirty state, timestamp, and exact paths.
- Stop after the readiness report unless the outer user request explicitly includes implementation.
- Do not add runtime scripts in version `1.0.0`.
- Do not modify cached Superpowers, add the product to `catalog/`, publish, tag, push, or create a GitHub Release.
- Provider-free tests prove package and instruction contracts only; they do not prove live review quality.

---

## Locked File Map

```text
products.toml
  registers pre-sdd-review as the fourth Codex product

skills/pre-sdd-review/
  SKILL.md                       activation and controller workflow
  README.md                      Korean installation and usage contract
  README.en.md                   English installation and usage contract
  CHANGELOG.md                   Unreleased plus dated 1.0.0 entry
  release.toml                   name/version/tag/license source
  LICENSE.txt                    Apache License 2.0
  agents/openai.yaml             Codex display metadata and implicit policy
  references/reviewer-protocol.md exact reviewer prompt, passes, findings, verdicts

tests/products/pre-sdd-review/
  cases.json                     positive, risk, repair, and near-miss cases
  test_contract.py               deterministic payload and workflow assertions
  fixtures/ready/                valid design/plan/repository manifest
  fixtures/missing-coverage/     design requirement absent from plan
  fixtures/false-verification/   weak evidence accepts a wrong implementation
  fixtures/runtime-removal/      high-risk condition requiring reviewer two

docs/maintainers/products/pre-sdd-review/
  contract.md                    behavior, authority, mutation, and output contract
  testing.md                     provider-free evidence and optional live procedure
  compatibility.md               Codex-only measured support boundary
  release.md                     independent 1.0.0 release checks without publication

scripts/lib/verification.py
  registers pre-sdd-review-contract

tests/repository/test_product_registry.py
tests/repository/test_release_contract.py
tests/repository/test_verify.py
tests/repository/test_public_docs.py
  extend exact repository facts to the fourth product

README.md
README.en.md
docs/README.md
docs/maintainers/README.md
docs/users/{ko,en}/{installation,compatibility,safety-and-privacy,verification}.md
  expose the fourth product and evidence limits
```

The product-level test consumes this stable JSON shape:

```json
{
  "cases": [
    {
      "id": "default-auto-improve",
      "request": "$pre-sdd-review docs/design.md docs/plan.md",
      "expect": ["review", "repair", "re-review", "fingerprints"]
    }
  ]
}
```

The reviewer emits this stable finding shape:

```text
ID: PSDR-001
Severity: BLOCKER
Class: repo-reality
Location: docs/plan.md — Task 2
Evidence: the named command is absent from package scripts
Consequence: the worker cannot execute the acceptance step
Minimal document fix: replace it with the repository's verified command
```

### Task 1: Register the fourth product and establish its release identity

**Files:**
- Modify: `products.toml`
- Create: `skills/pre-sdd-review/SKILL.md`
- Create: `skills/pre-sdd-review/README.md`
- Create: `skills/pre-sdd-review/README.en.md`
- Create: `skills/pre-sdd-review/CHANGELOG.md`
- Create: `skills/pre-sdd-review/release.toml`
- Create: `skills/pre-sdd-review/LICENSE.txt`
- Create: `skills/pre-sdd-review/agents/openai.yaml`
- Create: `skills/pre-sdd-review/references/reviewer-protocol.md`
- Create: `tests/products/pre-sdd-review/cases.json`
- Create: `tests/products/pre-sdd-review/test_contract.py`
- Create: `docs/maintainers/products/pre-sdd-review/contract.md`
- Create: `docs/maintainers/products/pre-sdd-review/testing.md`
- Create: `docs/maintainers/products/pre-sdd-review/compatibility.md`
- Create: `docs/maintainers/products/pre-sdd-review/release.md`
- Modify: `tests/repository/test_product_registry.py`
- Modify: `tests/repository/test_release_contract.py`

**Interfaces:**
- Consumes: `Product`, `ProductRegistry`, `validate_registry()`, and `validate_product()` from `scripts/lib/`.
- Produces: registry product `pre-sdd-review`, release identity `pre-sdd-review-v1.0.0`, and mirrored product/test/maintainer directories accepted by repository validation.

- [ ] **Step 1: Write failing registry and release expectations**

Change the registry-order assertion to:

```python
self.assertEqual(
    registry.names,
    (
        "korean-writing-editor",
        "image-workbench",
        "how-it-works",
        "pre-sdd-review",
    ),
)
```

Add this registry assertion:

```python
class ProductRegistryTests(unittest.TestCase):
    def test_pre_sdd_review_is_codex_only(self) -> None:
        product = load_registry(ROOT / "products.toml").require("pre-sdd-review")
        self.assertEqual(product.display_name, "Pre-SDD Review")
        self.assertEqual(product.supported_hosts, ("codex",))
        self.assertEqual(
            product.verify_stages,
            ("product-contract", "pre-sdd-review-contract", "python-compile"),
        )
```

Extend `EXPECTED` in `tests/repository/test_release_contract.py`:

```python
EXPECTED = {
    "korean-writing-editor": "2.0.1",
    "image-workbench": "2.0.1",
    "how-it-works": "1.0.0",
    "pre-sdd-review": "1.0.0",
}
```

Add the archive identity assertion:

```python
class ReleaseContractTests(unittest.TestCase):
    def test_pre_sdd_review_first_archive_identity(self) -> None:
        product = load_product_release(ROOT / "skills/pre-sdd-review")
        self.assertEqual(product.version, "1.0.0")
        self.assertEqual(product.tag, "pre-sdd-review-v1.0.0")
        self.assertEqual(product.artifact_name, "pre-sdd-review-v1.0.0.zip")
```

- [ ] **Step 2: Run the focused tests and confirm the missing product failure**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.repository.test_product_registry \
  tests.repository.test_release_contract -v
```

Expected: FAIL because `pre-sdd-review` is not registered and its payload does not exist.

- [ ] **Step 3: Add the exact registry row**

Append this fourth product to `products.toml`:

```toml
[[products]]
name = "pre-sdd-review"
display_name = "Pre-SDD Review"
skill_path = "skills/pre-sdd-review"
test_path = "tests/products/pre-sdd-review"
maintainer_docs = "docs/maintainers/products/pre-sdd-review"
supported_hosts = ["codex"]
owned_paths = [
  "skills/pre-sdd-review/",
  "tests/products/pre-sdd-review/",
  "docs/maintainers/products/pre-sdd-review/",
]
verify_stages = ["product-contract", "pre-sdd-review-contract", "python-compile"]
```

- [ ] **Step 4: Create a complete, valid payload scaffold**

Use this exact `release.toml`:

```toml
schema_version = 1
name = "pre-sdd-review"
version = "1.0.0"
tag_prefix = "pre-sdd-review-v"
license = "Apache-2.0"
```

Use this exact frontmatter at the beginning of `SKILL.md`:

```yaml
---
name: pre-sdd-review
description: Use when an approved design spec and implementation plan already exist and must be reviewed, automatically improved, and re-reviewed against repository reality immediately before SDD. Do not use for creating specs or plans, reviewing code, implementing changes, proofreading, or release readiness.
license: Apache-2.0
compatibility: Requires a local Git repository, readable design and plan files, and Codex subagent support for independent review.
metadata:
  version: "1.0.0"
  updated_at: "2026-08-29"
---
```

Use this exact `agents/openai.yaml`:

```yaml
interface:
  display_name: "Pre-SDD Review"
  short_description: "Review, repair, and re-review specs and plans before SDD"
  default_prompt: "Use $pre-sdd-review to review, improve, and re-review the approved design and implementation plan before SDD."
policy:
  allow_implicit_invocation: true
```

Create `CHANGELOG.md` with `# Changelog`, `## Unreleased`, and
`## 1.0.0 - 2026-08-29`. Duplicate the repository's tracked Apache 2.0
license text into `LICENSE.txt` byte-for-byte. Create the Korean and English
README files with the repository-required heading order and concise statements
that the default is review-repair-re-review, `review-only` is explicit, Codex
is the only measured host, and the skill never starts SDD by itself. Create the
four maintainer documents with their exact filenames and a concise paragraph
identifying their final ownership: behavior, testing, compatibility, or
release. Tasks 3 and 4 expand these already truthful documents and lock their
details in tests. Create `references/reviewer-protocol.md`, `cases.json`, and
`test_contract.py` as valid UTF-8 files with the identities above so registry
validation can inspect the mirrored directories. Do not add `scripts/` to the
payload.

- [ ] **Step 5: Run the focused registry and release tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.repository.test_product_registry \
  tests.repository.test_release_contract -v
```

Expected: PASS. If public-document tests fail because the new README content is not complete, leave those failures for Task 4 and do not weaken their assertions.

- [ ] **Step 6: Commit the registered product scaffold**

```bash
git add products.toml skills/pre-sdd-review tests/products/pre-sdd-review \
  docs/maintainers/products/pre-sdd-review \
  tests/repository/test_product_registry.py \
  tests/repository/test_release_contract.py
git commit -m "feat: register pre-sdd review skill"
```

### Task 2: Lock the default review-repair-re-review behavior

**Files:**
- Modify: `skills/pre-sdd-review/SKILL.md`
- Modify: `skills/pre-sdd-review/references/reviewer-protocol.md`
- Modify: `tests/products/pre-sdd-review/test_contract.py`

**Interfaces:**
- Consumes: exact authority, workflow, mutation, finding, and verdict rules from the design specification.
- Produces: controller instructions and one reusable read-only reviewer protocol with no implementation side effects.

- [ ] **Step 1: Write failing workflow contract tests**

In `test_contract.py`, parse frontmatter with
`scripts.lib.product_contract.parse_skill_frontmatter` and add these tests:

```python
class PreSddReviewContractTests(unittest.TestCase):
    def test_default_is_review_repair_and_re_review(self) -> None:
        body = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for phrase in (
            "Default mode: review -> repair documents -> scoped re-review",
            "At most two repair passes",
            "review-only",
            "Do not start SDD unless the outer request explicitly asks for implementation",
        ):
            self.assertIn(phrase, body)

    def test_reviewer_is_read_only_and_controller_owns_repairs(self) -> None:
        protocol = (SKILL / "references/reviewer-protocol.md").read_text(encoding="utf-8")
        self.assertIn("Reviewer mutation policy: read-only", protocol)
        self.assertIn("The controlling agent applies document repairs", protocol)
        self.assertIn("Never edit application code", protocol)

    def test_accepted_authority_cannot_be_auto_edited(self) -> None:
        body = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for phrase in ("accepted ADR", "approved visual authority", "BLOCKED"):
            self.assertIn(phrase, body)

    def test_no_minimum_finding_quota(self) -> None:
        protocol = (SKILL / "references/reviewer-protocol.md").read_text(encoding="utf-8")
        self.assertIn("Zero findings is valid", protocol)
        self.assertNotRegex(protocol, r"(?i)(at least|minimum)\s+[0-9]+\s+findings")
```

- [ ] **Step 2: Run the workflow tests and verify the missing-contract failure**

Use unittest discovery because the product directory contains hyphens:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests/products/pre-sdd-review -p 'test_contract.py' -v
```

Expected: FAIL because the scaffold does not yet contain the workflow phrases.

- [ ] **Step 3: Implement the controller state machine in `SKILL.md`**

Write these sections in order:

```text
# Pre-SDD Review
## Hard gate
## Resolve authoritative inputs
## Capture freshness
## Select reviewers
## Default mode: review -> repair documents -> scoped re-review
## Review-only mode
## Repair rules
## Verdict and handoff
## Do not use this skill for
```

The state machine must require:

```text
resolve plan -> resolve plan **Spec:** -> read binding references
-> hash design and plan -> record HEAD and dirty state
-> fresh read-only review -> controller deduplication
-> authority-preserving document repair -> scoped re-review
-> optional second repair -> READY | REVISE | BLOCKED
```

State explicitly that ordinary evidence-backed corrections do not require an
approval checkpoint, but any correction that changes approved product intent
is forbidden and returns `BLOCKED`. State that code, tests, configuration, and
accepted ADRs are outside the mutation allowlist.

- [ ] **Step 4: Implement the exact reviewer protocol**

`references/reviewer-protocol.md` must contain:

```text
Reviewer mutation policy: read-only
The controlling agent applies document repairs
Pass 1: authority trace
Pass 2: repository grounding
Pass 3: cross-artifact consistency
Pass 4: verification falsification
Pass 5: readiness verdict
Zero findings is valid
```

Define the five finding classes exactly as
`authority-drift`, `repo-reality`, `coverage`, `ordering`, and
`verification-gap`. Define only `BLOCKER` and `IMPORTANT`. Include the complete
seven-field finding record from the spec and instruct the reviewer to cite an
exact path plus heading or line for every finding.

The falsification pass must ask for a concrete wrong implementation that could
pass each planned acceptance check. It must distinguish static contract, unit,
integration, browser/device, and external-side-effect evidence.

- [ ] **Step 5: Run the product contract tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests/products/pre-sdd-review -p 'test_contract.py' -v
```

Expected: PASS.

- [ ] **Step 6: Commit the runtime contract**

```bash
git add skills/pre-sdd-review/SKILL.md \
  skills/pre-sdd-review/references/reviewer-protocol.md \
  tests/products/pre-sdd-review/test_contract.py
git commit -m "feat: define pre-sdd review workflow"
```

### Task 3: Add deterministic review fixtures and activation boundaries

**Files:**
- Modify: `tests/products/pre-sdd-review/cases.json`
- Modify: `tests/products/pre-sdd-review/test_contract.py`
- Create: `tests/products/pre-sdd-review/fixtures/ready/design.md`
- Create: `tests/products/pre-sdd-review/fixtures/ready/plan.md`
- Create: `tests/products/pre-sdd-review/fixtures/ready/repository.json`
- Create: `tests/products/pre-sdd-review/fixtures/ready/expected.json`
- Create: `tests/products/pre-sdd-review/fixtures/missing-coverage/design.md`
- Create: `tests/products/pre-sdd-review/fixtures/missing-coverage/plan.md`
- Create: `tests/products/pre-sdd-review/fixtures/missing-coverage/repository.json`
- Create: `tests/products/pre-sdd-review/fixtures/missing-coverage/expected.json`
- Create: `tests/products/pre-sdd-review/fixtures/false-verification/design.md`
- Create: `tests/products/pre-sdd-review/fixtures/false-verification/plan.md`
- Create: `tests/products/pre-sdd-review/fixtures/false-verification/repository.json`
- Create: `tests/products/pre-sdd-review/fixtures/false-verification/expected.json`
- Create: `tests/products/pre-sdd-review/fixtures/runtime-removal/design.md`
- Create: `tests/products/pre-sdd-review/fixtures/runtime-removal/plan.md`
- Create: `tests/products/pre-sdd-review/fixtures/runtime-removal/repository.json`
- Create: `tests/products/pre-sdd-review/fixtures/runtime-removal/expected.json`

**Interfaces:**
- Consumes: finding and verdict vocabulary from Task 2.
- Produces: synthetic, private-data-free examples that contract tests can validate without calling a model.

- [ ] **Step 1: Write the complete case matrix**

Set case IDs in this exact order:

```python
CASE_IDS = (
    "default-auto-improve",
    "explicit-review-only",
    "ready-zero-findings",
    "missing-spec-coverage",
    "nonexistent-command",
    "extension-collision",
    "false-positive-smoke",
    "task-interface-order",
    "runtime-removal-risk-review",
    "stale-document-hash",
    "near-miss-write-spec",
    "near-miss-write-plan",
    "near-miss-code-review",
    "near-miss-release-review",
)
```

Each `cases.json` item must contain `id`, `request`, and `expect`. The first
case expects `review`, `repair`, `re-review`, and `fingerprints`; the explicit
review-only case expects `read_only` and `single_verdict`; every near miss
expects `not_activated`.

- [ ] **Step 2: Create four bounded fixture sets**

Use a fictional `sample-app` repository in every fixture. Do not copy user
paths, prompts, or source. Each `repository.json` contains only:

```json
{
  "head": "0123456789abcdef0123456789abcdef01234567",
  "dirty": false,
  "paths": ["package.json", "src/app.ts", "tests/app.test.ts"],
  "commands": ["npm test", "npm run build"]
}
```

The `ready` design requires `renderMessage(input: string): string`; its plan
creates that exact function and verifies the returned value. Its expected
verdict is `READY` with an empty findings array.

The `missing-coverage` design additionally requires empty-input rejection, but
its plan only covers normal input. Its expected finding is `PSDR-001`,
`BLOCKER`, class `coverage`.

The `false-verification` plan claims success from `npm run build` alone even
though the design requires the rendered string `hello`. Its expected finding
is `PSDR-001`, `IMPORTANT`, class `verification-gap`.

The `runtime-removal` plan removes `src/app.ts` and replaces the application
runtime. Its expected JSON sets `risk_reviewer_required` to `true` with trigger
`framework-or-runtime-removal`.

- [ ] **Step 3: Add fixture integrity tests**

Add:

```python
class PreSddReviewFixtureTests(unittest.TestCase):
    def test_case_ids_and_near_misses_are_exact(self) -> None:
        data = json.loads(CASES.read_text(encoding="utf-8"))
        self.assertEqual(tuple(case["id"] for case in data["cases"]), CASE_IDS)
        near_misses = [case for case in data["cases"] if case["id"].startswith("near-miss-")]
        self.assertTrue(near_misses)
        self.assertTrue(all(case["expect"] == ["not_activated"] for case in near_misses))

    def test_ready_fixture_allows_zero_findings(self) -> None:
        expected = json.loads((FIXTURES / "ready/expected.json").read_text(encoding="utf-8"))
        self.assertEqual(expected, {"verdict": "READY", "findings": []})

    def test_runtime_removal_requires_focused_second_reviewer(self) -> None:
        expected = json.loads((FIXTURES / "runtime-removal/expected.json").read_text(encoding="utf-8"))
        self.assertEqual(expected["risk_reviewer_required"], True)
        self.assertEqual(expected["risk_trigger"], "framework-or-runtime-removal")

    def test_fixtures_contain_no_personal_paths_or_credentials(self) -> None:
        text = "\n".join(path.read_text(encoding="utf-8") for path in FIXTURES.rglob("*.*"))
        for forbidden in ("/Users/", "source/private", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
            self.assertNotIn(forbidden, text)
```

- [ ] **Step 4: Run the fixture contract**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests/products/pre-sdd-review -p 'test_contract.py' -v
```

Expected: PASS. This proves fixture structure and instruction presence only;
do not describe it as live reviewer-quality evidence.

- [ ] **Step 5: Commit the fixture suite**

```bash
git add tests/products/pre-sdd-review
git commit -m "test: cover pre-sdd review readiness cases"
```

### Task 4: Complete product and maintainer documentation

**Files:**
- Modify: `skills/pre-sdd-review/README.md`
- Modify: `skills/pre-sdd-review/README.en.md`
- Modify: `skills/pre-sdd-review/CHANGELOG.md`
- Modify: `docs/maintainers/products/pre-sdd-review/contract.md`
- Modify: `docs/maintainers/products/pre-sdd-review/testing.md`
- Modify: `docs/maintainers/products/pre-sdd-review/compatibility.md`
- Modify: `docs/maintainers/products/pre-sdd-review/release.md`
- Modify: `tests/products/pre-sdd-review/test_contract.py`

**Interfaces:**
- Consumes: final behavioral contract and fixtures from Tasks 2–3.
- Produces: bilingual user instructions and four maintainer protocols with no support overclaim.

- [ ] **Step 1: Add failing documentation assertions**

Add tests that require the repository-standard heading order and these facts:

```python
KOREAN_FACTS = (
    "$pre-sdd-review",
    "검토 → 문서 개선 → 재검토",
    "review-only",
    "최대 두 번",
    "READY",
    "REVISE",
    "BLOCKED",
    "Codex",
    "not_measured",
)

ENGLISH_FACTS = (
    "$pre-sdd-review",
    "review -> repair documents -> scoped re-review",
    "review-only",
    "at most two repair passes",
    "READY",
    "REVISE",
    "BLOCKED",
    "Codex",
    "not_measured",
)
```

Require the maintainer contract to name authority order, the mutation
allowlist, five passes, five finding classes, two severities, five risk
triggers, freshness fields, and the no-automatic-SDD boundary.

- [ ] **Step 2: Run the product test and confirm documentation failures**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests/products/pre-sdd-review -p 'test_contract.py' -v
```

Expected: FAIL on the missing bilingual facts and maintainer contract details.

- [ ] **Step 3: Write the two product READMEs**

Use the exact repository heading orders from
`tests/repository/test_public_docs.py`. The Korean first-call section must use:

```text
$pre-sdd-review docs/history/specs/<design>.md docs/history/plans/<plan>.md
```

Explain that the plan path is primary and the design is verified from its
`**Spec:**` field. State that default invocation changes only the resolved
design and plan, while `review-only` changes nothing. Show the three verdicts,
two-pass bound, second-reviewer triggers, fingerprint invalidation, and the
fact that the skill does not start SDD unless the outer request includes
implementation.

The English README must carry the same facts and order rather than being a
shorter summary.

- [ ] **Step 4: Write the maintainer protocols**

`contract.md` owns activation, input resolution, authority order, reviewer
isolation, repair allowlist, passes, findings, verdicts, freshness, and handoff.
`testing.md` owns the provider-free command, exact fixture limits, optional
fresh-session live checks, and the prohibition on storing user documents or
full model responses. `compatibility.md` states Codex supported and every
other host `not_measured`. `release.md` uses `release.toml` as version source
and documents check/build/verify-download without tagging or publishing.

- [ ] **Step 5: Complete the changelog and run product tests**

Record version `1.0.0` as the first independent product release contract dated
2026-08-29. Do not claim that a tag or release exists.

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests/products/pre-sdd-review -p 'test_contract.py' -v
```

Expected: PASS.

- [ ] **Step 6: Commit product documentation**

```bash
git add skills/pre-sdd-review docs/maintainers/products/pre-sdd-review \
  tests/products/pre-sdd-review/test_contract.py
git commit -m "docs: define pre-sdd review product contract"
```

### Task 5: Register verification and update shared documentation

**Files:**
- Modify: `scripts/lib/verification.py`
- Modify: `tests/repository/test_verify.py`
- Modify: `tests/repository/test_public_docs.py`
- Modify: `README.md`
- Modify: `README.en.md`
- Modify: `docs/README.md`
- Modify: `docs/maintainers/README.md`
- Modify: `docs/users/ko/installation.md`
- Modify: `docs/users/ko/compatibility.md`
- Modify: `docs/users/ko/safety-and-privacy.md`
- Modify: `docs/users/ko/verification.md`
- Modify: `docs/users/en/installation.md`
- Modify: `docs/users/en/compatibility.md`
- Modify: `docs/users/en/safety-and-privacy.md`
- Modify: `docs/users/en/verification.md`

**Interfaces:**
- Consumes: `pre-sdd-review-contract` named by `products.toml`.
- Produces: an executable verification stage and discoverable, support-bounded public documentation.

- [ ] **Step 1: Write failing verification-stage assertions**

In `tests/repository/test_verify.py`, assert:

```python
class VerifySelectionTests(unittest.TestCase):
    def test_pre_sdd_review_selects_its_registered_stages(self) -> None:
        product = self.registry.require("pre-sdd-review")
        selected = stages(ROOT, "full", self.registry, skill=product.name)
        self.assertEqual(
            tuple(stage.name for stage in selected),
            ("product-contract", "pre-sdd-review-contract", "python-compile"),
        )
```

In `tests/repository/test_public_docs.py`, add:

```python
PRE_SDD_REVIEW_SUPPORT = (
    "pre-sdd-review: Codex supported; other hosts not_measured."
)
```

Add it to `SUPPORT_BY_PRODUCT` and require the Korean and English user guides
to distinguish deterministic contract evidence from live review quality.

- [ ] **Step 2: Run the focused repository tests and verify the unknown-stage failure**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.repository.test_verify \
  tests.repository.test_public_docs -v
```

Expected: FAIL because `pre-sdd-review-contract` is not registered and shared
documentation does not yet route to the fourth product.

- [ ] **Step 3: Register the verification stage**

Add this entry to `_stage_catalog()` in `scripts/lib/verification.py`:

```python
"pre-sdd-review-contract": Stage(
    "pre-sdd-review-contract",
    _python(
        "-m",
        "unittest",
        "discover",
        "-s",
        _posix("tests", "products", "pre-sdd-review"),
        "-p",
        "test_contract.py",
    ),
    cwd=root,
),
```

Do not add provider calls or exclude the stage from `windows-portable`; the
contract is Markdown/JSON/Python and must run in both profiles.

- [ ] **Step 4: Update every shared product route**

Add `pre-sdd-review` after `how-it-works` in root and docs product lists. Use
the exact support sentence:

```text
pre-sdd-review: Codex supported; other hosts not_measured.
```

Installation documentation uses the repository's standard `$skill-installer`
form:

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/pre-sdd-review
```

Safety documentation states that the skill reads local design, plan, ADR, and
repository files; edits only the resolved design and plan in default mode;
does not transmit, persist, or fixture user documents in repository-owned
tests; and never starts code implementation without an explicit outer request.

Verification documentation adds:

```bash
python3 scripts/verify.py --skill pre-sdd-review
```

It must say that offline fixtures validate instruction and package contracts,
not agent independence, semantic completeness, or live review quality.

- [ ] **Step 5: Run focused and product verification**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.repository.test_verify \
  tests.repository.test_public_docs -v
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --skill pre-sdd-review
```

Expected: PASS.

- [ ] **Step 6: Commit verification and public documentation**

```bash
git add scripts/lib/verification.py tests/repository/test_verify.py \
  tests/repository/test_public_docs.py README.md README.en.md docs
git commit -m "docs: publish pre-sdd review usage and verification"
```

### Task 6: Verify the complete product and repository

**Files:**
- Review: all files changed by Tasks 1–5
- Modify only when a failing check identifies a concrete contract mismatch

**Interfaces:**
- Consumes: the complete registered product.
- Produces: provider-free evidence that the new product and existing products remain valid, with no release or catalog mutation.

- [ ] **Step 1: Run product verification**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --skill pre-sdd-review
```

Expected: all three registered product stages PASS.

- [ ] **Step 2: Run both repository profiles**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --profile full
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --profile windows-portable
```

Expected: PASS with no provider or billable calls.

- [ ] **Step 3: Check release payload without publishing**

Read `docs/maintainers/products/pre-sdd-review/release.md` and run its
documented check/build/verify-download sequence in a temporary directory.
Confirm the artifact name is `pre-sdd-review-v1.0.0.zip`, its contents come
only from `skills/pre-sdd-review/`, and no tag, push, catalog mutation, or
GitHub Release occurs.

- [ ] **Step 4: Review scope and whitespace**

```bash
git status --short --branch
git diff --check
git diff --stat
git diff -- products.toml skills/pre-sdd-review tests/products/pre-sdd-review \
  docs/maintainers/products/pre-sdd-review scripts/lib/verification.py \
  tests/repository README.md README.en.md docs/users docs/README.md \
  docs/maintainers/README.md
```

Expected: only the approved fourth-product implementation and its design/plan
records are changed. `catalog/` and the three existing product payloads remain
unchanged.

- [ ] **Step 5: Perform the final spec-to-plan self-review**

Confirm every design section maps to an implemented task, scan the plan and
payload for incomplete instructions, and verify that all exact names remain
`pre-sdd-review`, `pre-sdd-review-contract`, `1.0.0`, and `codex`. Confirm that
default auto-improvement, two-pass limit, reviewer read-only policy, mutation
allowlist, conditional risk reviewer, finding schema, fingerprints, and
no-automatic-SDD boundary are each asserted by a test and explained in both
languages.

- [ ] **Step 6: Commit verification corrections if any were required**

If Steps 1–5 required tracked corrections, stage only those exact files and
commit:

```bash
git commit -m "test: close pre-sdd review verification gaps"
```

If no correction was required, do not create an empty commit.

## Completion boundary

This plan is complete only when `pre-sdd-review` is a registered fourth
product, `$pre-sdd-review` defaults to review-repair-re-review, explicit
`review-only` is non-mutating, all document changes remain inside the approved
allowlist, risk-based second review is conditional, clean inputs may return
zero findings, fingerprints invalidate stale readiness, product and full
provider-free verification pass, and neither SDD nor release publication has
been triggered as a side effect.
