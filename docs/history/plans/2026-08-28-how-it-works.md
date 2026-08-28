# How It Works Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the unpublished explanation skill with one `how-it-works` 1.0.0 payload that produces a complete portable explanation and is locally usable in Codex, Claude Code, Grok, and Cursor without legacy aliases or cloud upload support.

**Architecture:** Rename the single canonical payload and its mirrored tests/docs in place, then make its frontmatter and required output use only the four-host portable intersection. Provider-free contracts prove identity, activation boundaries, output shape, safety, docs, and release bytes; explicit fresh-session smoke supplies the separate live support evidence. Codex, Grok, and Cursor share one `~/.agents/skills/how-it-works` link, while Claude Code uses `~/.claude/skills/how-it-works`.

**Tech Stack:** Agent Skills Markdown/YAML frontmatter, Mermaid, Python 3.11+ standard library and `unittest`, TOML, Git, Codex CLI, Claude Code CLI, Grok CLI, Cursor desktop.

**Spec:** `docs/history/specs/2026-08-28-how-it-works-repository-architecture-design.md`

## Global Constraints

- Start only after `docs/history/plans/2026-08-28-repository-architecture.md` is complete and every foundation acceptance command passes.
- `how-it-works` is the only active product ID, directory name, frontmatter name, release name, test name, documentation name, and invocation name.
- Do not create an alias, redirect skill, deprecation directory, compatibility command, or old-name local link.
- Display name is `How It Works`; Python identifier form is `how_it_works`.
- First public target is `1.0.0`; tag prefix is `how-it-works-v`; archive is `how-it-works-v1.0.0.zip`.
- Supported hosts are exactly `codex`, `claude-code`, `grok`, and `cursor` for local or repository-based use.
- Claude.ai, Cowork, Skills API upload, cloud synchronization, marketplace publication, and host-specific payload copies are out of scope.
- The shared `SKILL.md` frontmatter contains only `name`, `description`, `license`, `compatibility`, and `metadata`; remove `argument-hint`.
- `agents/openai.yaml` may provide optional Codex presentation metadata but cannot be required by runtime behavior.
- Required output is complete in chat: one-sentence claim, Mermaid source, numbered textual hop list, rung-specific body, uncovered adjacent slices, and one next move.
- Artifact, Canvas, browser, page URL, temporary file, or Mermaid rendering is never required. Optional preview failure cannot fail a complete common response.
- Preserve the `slice`, `type`, `rung`, and `language` gate, one-question rule, stable hop IDs, monotonic rung truth, high-stakes banners, and fetched-source-only citation rule.
- Do not persist user topics, private prompts, complete provider responses, generated media, credentials, or billing receipts.
- Live smoke is optional, potentially billable, never CI, and must receive explicit confirmation immediately before execution.
- Never point user-level skill links at a disposable Git worktree. If implementation runs in an isolated worktree, Task 7 pauses until the user authorizes integration into `/Users/kws/source/private/skills`; use `superpowers:finishing-a-development-branch` for that decision, then continue from the canonical checkout.
- Do not tag, push, publish, create a GitHub Release, or mutate `catalog/`.
- Historical old-name mentions remain factual under `docs/history/`; the only other allowed match is one explicit migration note in `skills/how-it-works/CHANGELOG.md`.

---

## Locked File Map

```text
products.toml
  replaces the current explanation product row with how-it-works and four hosts

skills/how-it-works/
  SKILL.md                     portable activation, gate, state machine, complete output
  README.md                    Korean user guide in the common product order
  README.en.md                 English user guide in the same information order
  CHANGELOG.md                 Unreleased plus dated 1.0.0 and the sole active migration note
  release.toml                 name=how-it-works, version=1.0.0, tag_prefix=how-it-works-v
  agents/openai.yaml           optional Codex display metadata and $how-it-works prompt
  references/output.md         common Markdown/Mermaid/hop/rung output contract
  references/visuals.md        Mermaid design and renderer-independent fallback
  references/korean.md         Korean voice rules
  references/stakes.md         exact high-stakes banners
  references/sources.md        fetched-source-only citation policy

tests/products/how-it-works/
  cases.json                   synthetic gate/trigger/near-miss/output cases
  test_contract.py             payload, frontmatter, behavior, and archive contract
  live/README.md               manual live-smoke procedure; no provider transcript
  live/cases.json              synthetic explicit/implicit/near-miss cases
  live/smoke-record.json       host/version/date/case/verdict only, created after approval

docs/maintainers/products/how-it-works/
  contract.md                  activation, slots, output, safety, coupled-file map
  testing.md                   provider-free and optional live evidence procedures
  compatibility.md             four-host support boundary and current smoke metadata
  release.md                   1.0.0 check/build/verify procedure without publication

scripts/lib/stale_identifiers.py
  tracked-file stale identifier scan with exact history/changelog allowlist
tests/repository/test_stale_identifiers.py
  active-source zero-match enforcement without spelling the old ID contiguously
```

Shared interfaces introduced in this plan:

```python
@dataclasses.dataclass(frozen=True)
class IdentifierHit:
    path: str
    location: str  # "path" or "content"

def tracked_identifier_hits(
    root: pathlib.Path,
    identifier: str,
    *,
    allowed_prefixes: tuple[str, ...] = ("docs/history/",),
    allowed_files: frozenset[str] = frozenset({"skills/how-it-works/CHANGELOG.md"}),
) -> tuple[IdentifierHit, ...]: ...
```

### Task 1: Rename the registered product and release identity

**Files:**
- Move: `skills/graspic/` -> `skills/how-it-works/`
- Move: `tests/products/graspic/` -> `tests/products/how-it-works/`
- Move: `docs/maintainers/products/graspic/` -> `docs/maintainers/products/how-it-works/`
- Modify: `products.toml`
- Modify: `skills/how-it-works/release.toml`
- Modify: `skills/how-it-works/SKILL.md` frontmatter identity only
- Modify: `skills/how-it-works/agents/openai.yaml`
- Modify: `tests/products/how-it-works/test_contract.py`
- Modify: `tests/repository/test_product_registry.py`, `test_release.py`, `test_verify.py`, `test_changed_targets.py`, `test_community_and_ci.py`, `test_public_docs.py`

**Interfaces:**
- Consumes: registry and mirrored structure from the foundation plan.
- Produces: registry product `how-it-works`, release identity `1.0.0`, verification stage `how-it-works-contract`, and no current old-name directory.

- [ ] **Step 1: Verify the four old links before the repository path moves**

Run:

```bash
test -L /Users/kws/.codex/skills/graspic
test -L /Users/kws/.claude/skills/graspic
test -L /Users/kws/.grok/skills/graspic
test -L /Users/kws/.agents/skills/graspic
test "$(readlink /Users/kws/.codex/skills/graspic)" = "/Users/kws/source/private/skills/skills/graspic"
test "$(readlink /Users/kws/.claude/skills/graspic)" = "/Users/kws/source/private/skills/skills/graspic"
test "$(readlink /Users/kws/.grok/skills/graspic)" = "/Users/kws/source/private/skills/skills/graspic"
test "$(readlink /Users/kws/.agents/skills/graspic)" = "/Users/kws/.grok/skills/graspic"
for old_skill_link in /Users/kws/.codex/skills/graspic /Users/kws/.claude/skills/graspic /Users/kws/.grok/skills/graspic /Users/kws/.agents/skills/graspic; do
  test "$(python3 -c 'import pathlib,sys; print(pathlib.Path(sys.argv[1]).resolve(strict=True))' "$old_skill_link")" = "/Users/kws/source/private/skills/skills/graspic" || exit 1
done
```

Expected: all checks exit 0. Any mismatch stops the rename before links become
dangling; no local path is changed in this step.

- [ ] **Step 2: Change the registry expectation first**

```python
def test_repository_registry_preserves_product_order(self) -> None:
    self.assertEqual(
        self.registry.names,
        ("korean-writing-editor", "image-workbench", "how-it-works"),
    )

def test_explanation_product_has_four_supported_hosts(self) -> None:
    product = self.registry.require("how-it-works")
    self.assertEqual(product.display_name, "How It Works")
    self.assertEqual(product.supported_hosts, ("codex", "claude-code", "grok", "cursor"))
```

- [ ] **Step 3: Run the focused registry test and confirm the old identity fails**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.repository.test_product_registry -v`

Expected: FAIL because the registry still contains the working name and old paths.

- [ ] **Step 4: Perform the three Git-aware directory renames**

Use `git mv` for the skill, product-test, and maintainer-doc directories. Do not create an old-name directory or symlink inside the repository.

- [ ] **Step 5: Replace the registry row**

```toml
[[products]]
name = "how-it-works"
display_name = "How It Works"
skill_path = "skills/how-it-works"
test_path = "tests/products/how-it-works"
maintainer_docs = "docs/maintainers/products/how-it-works"
supported_hosts = ["codex", "claude-code", "grok", "cursor"]
owned_paths = [
  "skills/how-it-works/",
  "tests/products/how-it-works/",
  "docs/maintainers/products/how-it-works/",
]
verify_stages = ["product-contract", "how-it-works-contract", "python-compile"]
```

- [ ] **Step 6: Change the independent release identity**

```toml
schema_version = 1
name = "how-it-works"
version = "1.0.0"
tag_prefix = "how-it-works-v"
license = "Apache-2.0"
```

Change only `name` and `metadata.version` in `SKILL.md` at this step. Set `agents/openai.yaml` to display `How It Works` and use `$how-it-works` in `default_prompt`. Behavioral/frontmatter portability edits belong to Task 2.

- [ ] **Step 7: Update Python identifiers and paths**

Rename `GraspicPayloadTests` to `HowItWorksPayloadTests`, `SKILL` and `CASES` roots to the new path, stage ID `graspic-contract` to `how-it-works-contract`, and all active target/path assertions. Replace catalog exclusion assertions that name the unpublished product with a generic assertion that catalog members equal the lock names.

Replace identity-only occurrences inside the moved skill, its READMEs,
maintainer guides, product fixtures, current root/user docs, and community
templates so the new invocation and paths work immediately. Preserve the
existing page/output semantics until Task 3 and preserve document structure
until Task 4; this step changes identity tokens and links, not behavior prose.

- [ ] **Step 8: Run identity, registry, routing, release, and verify tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/how-it-works -p 'test_*.py'
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.repository.test_product_registry tests.repository.test_changed_targets tests.repository.test_verify -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.repository.test_release tests.repository.test_release_contract -v
```

Expected: all commands exit 0. Hyphenated product directories are always run
with `unittest discover`, never as a dotted module name.

- [ ] **Step 9: Verify the new selector and old selector rejection**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --skill how-it-works
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --skill graspic
```

Expected: first exits 0; second exits 2 with argparse `invalid choice` and does not run stages.

- [ ] **Step 10: Commit the identity cutover**

```bash
git add products.toml skills tests docs/maintainers/products
git commit -m "feat: rename explanation product to how-it-works"
```

### Task 2: Enforce portable frontmatter and four-host invocation metadata

**Files:**
- Modify: `skills/how-it-works/SKILL.md`
- Modify: `skills/how-it-works/agents/openai.yaml`
- Modify: `scripts/lib/product_contract.py`
- Modify: `tests/products/how-it-works/test_contract.py`
- Modify: `tests/repository/test_release_contract.py`

**Interfaces:**
- Consumes: `parse_skill_frontmatter(text)` and registry host claims.
- Produces: exact portable frontmatter keys and host invocation examples without host-runtime dependencies.

- [ ] **Step 1: Add exact frontmatter tests**

```python
PORTABLE_FIELDS = {"name", "description", "license", "compatibility", "metadata"}

def test_frontmatter_uses_portable_intersection(self) -> None:
    frontmatter = parse_skill_frontmatter((SKILL / "SKILL.md").read_text(encoding="utf-8"))
    self.assertEqual(set(frontmatter), PORTABLE_FIELDS)
    self.assertEqual(frontmatter["name"], "how-it-works")
    self.assertEqual(frontmatter["license"], "Apache-2.0")
    self.assertEqual(frontmatter["metadata"]["version"], "1.0.0")

def test_frontmatter_has_no_host_tool_requirement(self) -> None:
    frontmatter = parse_skill_frontmatter((SKILL / "SKILL.md").read_text(encoding="utf-8"))
    compatibility = str(frontmatter["compatibility"]).lower()
    for forbidden in ("artifact", "canvas", "browser", "imagegen", "artifact-design"):
        self.assertNotIn(forbidden, compatibility)
```

- [ ] **Step 2: Run the contract and confirm `argument-hint` and Artifact compatibility fail**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/how-it-works -p 'test_*.py'`

Expected: FAIL showing the extra field and host-specific compatibility text.

- [ ] **Step 3: Replace the frontmatter**

```yaml
---
name: how-it-works
description: Use when the user wants to understand how a mechanism or flow works visually, asks for a diagram or step-by-step path, names 그림/길/뼈대/허점, invokes the skill explicitly, or asks 원리부터, 그림으로, 어떻게 돌아가, or 감이 안 와. Do not use for debugging, implementation, review, translation, one-line factual lookup, child-register explanation, or ELI5 requests.
license: Apache-2.0
compatibility: Requires an Agent Skills host that can read this directory and return Markdown text.
metadata:
  version: "1.0.0"
  updated_at: "2026-08-28"
---
```

The explicit invocation names remain in the body and READMEs rather than adding a non-portable frontmatter field.

- [ ] **Step 4: Tighten the generic product contract**

Add an optional registry rule: when a product declares more than one supported host, reject frontmatter keys outside the portable set. Always reject a directory/frontmatter/release name mismatch. Keep `agents/openai.yaml` optional presentation behavior but validate its `$how-it-works` default prompt against the current product name.

- [ ] **Step 5: Add four-host invocation assertions**

Assert that active product documentation contains `$how-it-works` for Codex, `/how-it-works` for Claude Code and Grok, and both `/how-it-works` plus optional `@how-it-works` for Cursor. Assert that no runtime instruction says `agents/openai.yaml` is required.

- [ ] **Step 6: Run product and generic contracts**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/how-it-works -p 'test_*.py'
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.repository.test_release_contract -v
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --skill how-it-works
```

Expected: all exit 0.

- [ ] **Step 7: Commit portable metadata**

```bash
git add skills/how-it-works/SKILL.md skills/how-it-works/agents/openai.yaml scripts/lib/product_contract.py tests/products/how-it-works/test_contract.py tests/repository/test_release_contract.py
git commit -m "feat: make how-it-works metadata portable"
```

### Task 3: Replace the page contract with a complete portable output

**Files:**
- Modify: `skills/how-it-works/SKILL.md`
- Modify: `skills/how-it-works/references/output.md`
- Modify: `skills/how-it-works/references/visuals.md`
- Modify: `skills/how-it-works/references/korean.md`
- Modify: `skills/how-it-works/references/stakes.md` only if a link or product name changes
- Modify: `skills/how-it-works/references/sources.md`
- Modify: `tests/products/how-it-works/cases.json`
- Modify: `tests/products/how-it-works/test_contract.py`

**Interfaces:**
- Consumes: existing four-slot gate, rungs, type recipes, hop stability, safety banners, and source policy.
- Produces: one renderer-independent chat deliverable and optional preview enhancement.

- [ ] **Step 1: Add required-output and forbidden-dependency tests**

```python
def test_required_deliverable_is_complete_in_chat(self) -> None:
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    required = section(text, "## Required deliverable", "## Optional preview")
    for phrase in ("one-sentence claim", "Mermaid", "numbered hop list", "rung-specific body", "adjacent slices", "one next move"):
        self.assertIn(phrase, required)
    for forbidden in ("Artifact", "Canvas", "browser", "URL", "file"):
        self.assertNotIn(forbidden, required)

def test_payload_has_no_mandatory_page_contract(self) -> None:
    corpus = "\n".join(path.read_text(encoding="utf-8") for path in SKILL.rglob("*.md"))
    for forbidden in ("artifact-design", "published page", '<pre class="mermaid">', "same file path"):
        self.assertNotIn(forbidden, corpus)
```

Implement `section(text, start_heading, end_heading)` in the test module so headings must exist and appear in order.

- [ ] **Step 2: Add behavior fixture coverage**

Replace `cases.json` with synthetic DNS/rebase cases whose IDs and assertions cover:

```json
{
  "cases": [
    {"id":"broad-slice","prompt":"/how-it-works 인터넷","must":["three_slices","one_question"],"forbidden":["explanation"]},
    {"id":"missing-rung","prompt":"/how-it-works DNS 흐름","must":["one_closed_question"],"forbidden":["silent_rung"]},
    {"id":"explicit-dns-path","prompt":"/how-it-works DNS 길","must":["claim","mermaid","numbered_hops","body","adjacent_slices","next_move"],"forbidden":["host_tool_required"]},
    {"id":"implicit-positive","prompt":"DNS 요청이 브라우저에서 어디를 거쳐 주소가 되는지 길로 보여줘","must":["activate"],"forbidden":["debug"]},
    {"id":"near-miss-debug","prompt":"DNS resolver 테스트 실패를 고쳐줘","must":["do_not_activate"],"forbidden":["explanation_gate"]},
    {"id":"near-miss-eli5","prompt":"/eli5 DNS","must":["do_not_activate"],"forbidden":["rung_picker"]},
    {"id":"jargon-rung","prompt":"rebase 쉽게 설명해줘","must":["skeleton_default"],"forbidden":["picture_default"]},
    {"id":"no-renderer","prompt":"/how-it-works DNS 길, Mermaid 렌더러 없음","must":["mermaid_source","numbered_hops"],"forbidden":["failure"]},
    {"id":"no-fetched-source","prompt":"/how-it-works DNS 길, 검색하지 마","must":["omit_citations"],"forbidden":["invented_citation"]}
  ]
}
```

- [ ] **Step 3: Run the product contract and confirm old page behavior fails**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/how-it-works -p 'test_*.py'`

Expected: FAIL on mandatory Artifact/page language and missing portable deliverable headings.

- [ ] **Step 4: Rewrite the runtime state machine and deliverable**

Retain classification and slot logic, but make the body order explicit:

```text
request
  -> fill slice, type, rung, language
  -> emit one intent line
  -> read focused references
  -> emit complete Markdown + Mermaid source + numbered hop list
  -> offer one next move
```

Add `## Required deliverable` with the six exact items tested above. Add `## Optional preview` stating that a host page, Canvas, or visual preview may be added only after the complete output, never replaces it, and its failure is non-fatal. Remove every instruction to load `artifact-design`, write HTML, publish a page, preserve a URL, or keep the explanation out of chat.

- [ ] **Step 5: Rewrite `references/output.md` around common Markdown**

Use this authoritative order:

````markdown
# {slice} · {그림|길|뼈대|허점}

{high-stakes banner or omit}

## 한 줄 / One sentence

## 지도 / Map

```mermaid
{diagram source}
```

1. **H1** — {what moves or changes}
2. **H2** — {what moves or changes}

## 본문 / Body

## 지금 다루지 않은 것 / Adjacent slices

다음 / Next: {exactly one move}
````

State that hop identifiers in Mermaid labels and the numbered list must agree and survive rung changes. Mermaid rendering is enhancement only; source plus hop list is the fallback.

- [ ] **Step 6: Align visual, Korean, safety, and source references**

`visuals.md` owns diagram selection and bans HTML boxes as substitutes. `korean.md` keeps one-language and register rules. `stakes.md` retains exact mechanism-only banners. `sources.md` says only URLs fetched in the current turn may appear as verified sources; when none were fetched, omit the citation heading. None may require a host-specific tool.

- [ ] **Step 7: Run product tests and scan removed dependencies**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/how-it-works -p 'test_*.py'
rg -n 'artifact-design|published page|<pre class="mermaid">|same file path|Artifact tool' skills/how-it-works tests/products/how-it-works
```

Expected: tests PASS and `rg` returns exit 1 with no matches.

- [ ] **Step 8: Commit the portable behavior contract**

```bash
git add skills/how-it-works tests/products/how-it-works
git commit -m "feat: make how-it-works output complete in chat"
```

### Task 4: Rewrite user and maintainer documentation for four hosts

**Files:**
- Rewrite: `skills/how-it-works/README.md`
- Rewrite: `skills/how-it-works/README.en.md`
- Modify: `README.md`, `README.en.md`
- Modify: `docs/users/{ko,en}/{installation,compatibility,safety-and-privacy,verification}.md`
- Rewrite: `docs/maintainers/products/how-it-works/{contract,testing,compatibility,release}.md`
- Modify: `docs/README.md`, `docs/maintainers/README.md`, `CONTRIBUTING.md`
- Modify: `.github/ISSUE_TEMPLATE/bug.yml`, `.github/ISSUE_TEMPLATE/documentation.yml`, `.github/pull_request_template.md`
- Modify: `tests/repository/test_public_docs.py`, `test_community_and_ci.py`

**Interfaces:**
- Consumes: registry host claims and the completed portable behavior contract.
- Produces: paired readable docs with one consistent install/use/support story and no cloud-upload claim.

- [ ] **Step 1: Add information-order and support-boundary tests**

```python
PRODUCT_README_HEADINGS = {
    "README.md": (
        "## 목적",
        "## 사용할 때와 사용하지 않을 때",
        "## 지원 호스트",
        "## 설치",
        "## 첫 호출",
        "## 예상 결과",
        "## 안전과 개인정보",
        "## 검증",
        "## 업데이트와 제거",
        "## 변경 이력과 관리자 문서",
    ),
    "README.en.md": (
        "## Purpose",
        "## When to use and not use",
        "## Supported hosts",
        "## Install",
        "## First call",
        "## Expected result",
        "## Safety and privacy",
        "## Verification",
        "## Update and remove",
        "## Changelog and maintainer docs",
    ),
}

def test_how_it_works_readmes_follow_common_information_order(self) -> None:
    for filename in ("README.md", "README.en.md"):
        text = (ROOT / "skills/how-it-works" / filename).read_text(encoding="utf-8")
        positions = [text.index(marker) for marker in PRODUCT_README_HEADINGS[filename]]
        self.assertEqual(positions, sorted(positions), filename)

def test_docs_exclude_cloud_upload_support(self) -> None:
    active = "\n".join(path.read_text(encoding="utf-8") for path in active_markdown_paths(ROOT))
    for unsupported in ("skills api upload supported", "cowork supported", "claude.ai supported"):
        self.assertNotIn(unsupported, active.lower())
```

The test compares authored Korean headings with Korean and authored English
headings with English; it does not require machine-translated heading text.

- [ ] **Step 2: Run documentation tests and confirm old name/order/support failures**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.repository.test_public_docs tests.repository.test_community_and_ci -v`

Expected: FAIL on old product links, Codex-only root language, and missing four-host installation details.

- [ ] **Step 3: Rewrite both product READMEs in the approved order**

The shortest repository-based install is:

```bash
git clone https://github.com/beyondwin/skills.git
cd skills
mkdir -p ~/.agents/skills ~/.claude/skills
ln -s "$PWD/skills/how-it-works" ~/.agents/skills/how-it-works
ln -s "$PWD/skills/how-it-works" ~/.claude/skills/how-it-works
```

Explain that the first link serves Codex, Grok, and Cursor; the second serves Claude Code; `ln -s` fails instead of overwriting an existing target. Provide explicit calls `$how-it-works` and `/how-it-works`, Cursor's optional `@how-it-works`, one expected output skeleton, and safe exact-link removal commands. Link shared details rather than duplicating them.

- [ ] **Step 4: Rewrite shared compatibility and installation facts**

Use “current standalone products” for three products. State that only How It Works has the four-host claim; keep Korean Writing Editor and Image Workbench claims exactly as registered. State that Claude.ai/Cowork/Skills API upload and marketplace publication are not supported. Do not imply that the immutable catalog contains How It Works.

- [ ] **Step 5: Rewrite maintainer guides**

`contract.md` maps triggers, slots, output, safety, and coupled files. `testing.md` distinguishes provider-free tests from optional billable smoke and lists the exact smoke criteria. `compatibility.md` owns discovery paths and invocation syntax. `release.md` lists check/build/verify-download for 1.0.0 and ends with “no tag or GitHub Release is created by these commands.”

- [ ] **Step 6: Update community surfaces**

Replace old skill choices, paths, and examples in issue templates and PR checklist. Add a checklist item requiring registry/docs/test updates for host-support changes. Keep CI provider-free language.

- [ ] **Step 7: Run docs and community contracts**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.repository.test_public_docs tests.repository.test_community_and_ci -v
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --skill how-it-works
```

Expected: all exit 0; all active Markdown links resolve.

- [ ] **Step 8: Commit readable product documentation**

```bash
git add README.md README.en.md CONTRIBUTING.md .github docs skills/how-it-works/README.md skills/how-it-works/README.en.md tests/repository
git commit -m "docs: document how-it-works across four local hosts"
```

### Task 5: Enforce zero stale active identity matches

**Files:**
- Create: `scripts/lib/stale_identifiers.py`
- Create: `tests/repository/test_stale_identifiers.py`
- Modify: active files identified by the new scanner
- Modify: `skills/how-it-works/CHANGELOG.md`
- Modify: `scripts/lib/verification.py` and `products.toml` to register the repository stage if it is not already covered by repository discovery

**Interfaces:**
- Consumes: tracked Git paths, `docs/history/`, and the exact changelog allowlist.
- Produces: `tracked_identifier_hits(...) -> tuple[IdentifierHit, ...]` and a full-suite stale-identity gate.

- [ ] **Step 1: Add the scanner tests without spelling the stale ID contiguously in active test source**

```python
STALE_ID = "gra" + "spic"

def test_active_tree_has_no_stale_identity(self) -> None:
    self.assertEqual(tracked_identifier_hits(ROOT, STALE_ID), ())

def test_history_and_migration_note_are_the_only_allowances(self) -> None:
    with tempfile.TemporaryDirectory() as directory:
        repository = make_git_fixture(Path(directory))
        write_and_commit(repository, "docs/history/plans/old.md", STALE_ID)
        write_and_commit(repository, "skills/how-it-works/CHANGELOG.md", STALE_ID)
        self.assertEqual(tracked_identifier_hits(repository, STALE_ID), ())
        write_and_commit(repository, "README.md", STALE_ID)
        self.assertEqual(tracked_identifier_hits(repository, STALE_ID)[0].path, "README.md")
```

- [ ] **Step 2: Run the test and confirm the missing scanner failure**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.repository.test_stale_identifiers -v`

Expected: FAIL because `scripts.lib.stale_identifiers` does not exist.

- [ ] **Step 3: Implement a tracked-file path/content scanner**

Use `git -C ROOT ls-files -z` so `.git`, untracked provider output, and local caches are outside the contract. Normalize paths, skip the exact allowed prefix and file, report identifier matches in either path or UTF-8 text, tolerate binary files, sort/deduplicate hits, and fail if an allowlisted changelog path moves unexpectedly.

- [ ] **Step 4: Add the sole active migration note**

Under `## 1.0.0 - 2026-08-28`, state that the unpublished working identity was replaced before first public release, that no alias exists, and that users install/invoke only `how-it-works`. This changelog is the only active file allowed to spell the prior ID.

- [ ] **Step 5: Remove every scanner hit outside the allowlist**

Rewrite active assertions, community templates, docs, module identifiers, and filenames. Do not edit factual history. Do not add exceptions for tests, catalog code, or comments.

- [ ] **Step 6: Run the stale gate and full repository suite**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.repository.test_stale_identifiers -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/repository -p 'test_*.py'
```

Expected: both exit 0.

- [ ] **Step 7: Independently scan active paths**

Run:

```bash
git ls-files -z | while IFS= read -r -d '' tracked_path; do
  case "$tracked_path" in
    docs/history/*|skills/how-it-works/CHANGELOG.md) continue ;;
  esac
  if [[ "$tracked_path" == *gra''spic* ]] || LC_ALL=C grep -I -n 'gra''spic' "$tracked_path" >/dev/null 2>&1; then
    print -r -- "$tracked_path"
  fi
done
```

Expected: no output. The split shell literals prevent this plan's own active source from adding a contiguous scanner exception before it is moved under history.

- [ ] **Step 8: Commit stale-identity enforcement**

```bash
git add scripts/lib/stale_identifiers.py tests/repository/test_stale_identifiers.py skills/how-it-works/CHANGELOG.md products.toml scripts/lib/verification.py README.md README.en.md docs skills tests .github
git commit -m "test: reject stale explanation product identity"
```

### Task 6: Build and verify the standalone 1.0.0 bytes

**Files:**
- Modify only release/product contract files implicated by a failing test.
- Do not commit the generated ZIP or `SHA256SUMS`.

**Interfaces:**
- Consumes: `release.toml`, dated changelog, registry-backed release CLI, deterministic archive functions.
- Produces: verified local `how-it-works-v1.0.0.zip` and checksum evidence in a temporary directory only.

- [ ] **Step 1: Add exact artifact-name and extraction assertions**

```python
def test_how_it_works_first_archive_identity(self) -> None:
    product = load_product_release(ROOT / "skills/how-it-works")
    self.assertEqual(product.version, "1.0.0")
    self.assertEqual(product.tag, "how-it-works-v1.0.0")
    self.assertEqual(product.artifact_name, "how-it-works-v1.0.0.zip")
```

Update release archive tests to use the current registry product and assert the extracted root is exactly `how-it-works/`.

- [ ] **Step 2: Run release tests**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.repository.test_release tests.repository.test_release_contract -v`

Expected: PASS after Task 1 identity edits; any old artifact expectation fails and is corrected without adding compatibility behavior.

- [ ] **Step 3: Commit any release-test correction before building**

```bash
git add tests/repository/test_release.py tests/repository/test_release_contract.py scripts/release.py scripts/lib
git commit -m "test: lock how-it-works release artifact identity"
```

Skip the commit when no tracked correction exists. The release check requires the product and shared release paths to be clean.

- [ ] **Step 4: Run product check**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 scripts/release.py check --product how-it-works`

Expected: exit 0, no existing-tag error, no dirty-product error, and no baseline-version error.

- [ ] **Step 5: Build into a fresh temporary directory**

Run:

```bash
how_it_works_release_root="$(mktemp -d)"
how_it_works_release_output="$how_it_works_release_root/output"
PYTHONDONTWRITEBYTECODE=1 python3 scripts/release.py build --product how-it-works --output "$how_it_works_release_output"
find "$how_it_works_release_output" -maxdepth 1 -type f -print | sort
```

Expected: exactly `how-it-works-v1.0.0.zip` and `SHA256SUMS` are printed.

- [ ] **Step 6: Verify the exact downloaded bytes and extraction**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/release.py verify-download --product how-it-works --input "$how_it_works_release_output"
python3 -m zipfile -l "$how_it_works_release_output/how-it-works-v1.0.0.zip"
```

Expected: verify-download exits 0; every ZIP member is rooted at `how-it-works/`; no tests, maintainer docs, live records, symlinks, bytecode, or host-specific copies appear.

- [ ] **Step 7: Rebuild and compare deterministic hashes**

Run:

```bash
how_it_works_release_second="$how_it_works_release_root/second"
PYTHONDONTWRITEBYTECODE=1 python3 scripts/release.py build --product how-it-works --output "$how_it_works_release_second"
shasum -a 256 "$how_it_works_release_output/how-it-works-v1.0.0.zip" "$how_it_works_release_second/how-it-works-v1.0.0.zip"
```

Expected: both SHA-256 values are identical.

- [ ] **Step 8: Confirm no release artifact entered the worktree**

Run: `git status --short --branch`

Expected: no ZIP or `SHA256SUMS` under the repository. Record the temporary output path only in the execution report; do not commit it.

### Task 7: Safely replace the four old local links with two shared links

**Files:**
- External symlink create: `/Users/kws/.agents/skills/how-it-works`
- External symlink create: `/Users/kws/.claude/skills/how-it-works`
- External symlink remove after verification: `/Users/kws/.codex/skills/graspic`
- External symlink remove after verification: `/Users/kws/.claude/skills/graspic`
- External symlink remove after verification: `/Users/kws/.grok/skills/graspic`
- External symlink remove after verification: `/Users/kws/.agents/skills/graspic`

**Interfaces:**
- Consumes: canonical repository target `/Users/kws/source/private/skills/skills/how-it-works` and the four currently observed old-name links.
- Produces: one shared `.agents` link for Codex/Grok/Cursor, one `.claude` link for Claude Code, and no legacy links.

- [ ] **Step 1: Require the implementation in the canonical checkout**

If the current implementation path is an isolated worktree and
`/Users/kws/source/private/skills/skills/how-it-works` does not exist, do not
create user-level links to the worktree. Invoke
`superpowers:finishing-a-development-branch`, present the verified integration
options, and continue this task only after the user explicitly authorizes an
integration that places the implementation in the canonical checkout.

Then verify the canonical target:

Run:

```bash
test -d /Users/kws/source/private/skills/skills/how-it-works
test ! -L /Users/kws/source/private/skills/skills/how-it-works
```

Expected: both exit 0.

- [ ] **Step 2: Inspect every existing link without changing it**

Run:

```bash
for skill_link in \
  /Users/kws/.codex/skills/graspic \
  /Users/kws/.claude/skills/graspic \
  /Users/kws/.grok/skills/graspic \
  /Users/kws/.agents/skills/graspic \
  /Users/kws/.agents/skills/how-it-works \
  /Users/kws/.claude/skills/how-it-works
do
  if test -L "$skill_link"; then
    print -r -- "$skill_link -> $(readlink "$skill_link")"
  elif test -e "$skill_link"; then
    print -r -- "NON_LINK $skill_link"
  else
    print -r -- "MISSING $skill_link"
  fi
done
```

Expected: the four old paths are symlinks; new paths are missing or already exact links. Any `NON_LINK` or unexpected target stops this task and leaves that path untouched.

- [ ] **Step 3: Revalidate the exact raw targets captured before the rename**

Run:

```bash
test -L /Users/kws/.codex/skills/graspic
test -L /Users/kws/.claude/skills/graspic
test -L /Users/kws/.grok/skills/graspic
test -L /Users/kws/.agents/skills/graspic
test "$(readlink /Users/kws/.codex/skills/graspic)" = "/Users/kws/source/private/skills/skills/graspic"
test "$(readlink /Users/kws/.claude/skills/graspic)" = "/Users/kws/source/private/skills/skills/graspic"
test "$(readlink /Users/kws/.grok/skills/graspic)" = "/Users/kws/source/private/skills/skills/graspic"
test "$(readlink /Users/kws/.agents/skills/graspic)" = "/Users/kws/.grok/skills/graspic"
```

Expected: all exit 0. The old links may be dangling after an in-place rename or
may still resolve while work happened in an isolated worktree. Raw target
identity, not current resolution, is the deletion guard. Any changed raw target
stops the task and remains untouched.

- [ ] **Step 4: Create or verify only the two new links**

Run:

```bash
mkdir -p /Users/kws/.agents/skills /Users/kws/.claude/skills
ensure_how_it_works_link() {
  destination="$1"
  canonical_target="/Users/kws/source/private/skills/skills/how-it-works"
  if test -L "$destination"; then
    test "$(readlink "$destination")" = "$canonical_target"
  elif test -e "$destination"; then
    print -u2 -r -- "refusing non-link destination: $destination"
    return 1
  else
    ln -s "$canonical_target" "$destination"
  fi
}
ensure_how_it_works_link /Users/kws/.agents/skills/how-it-works
ensure_how_it_works_link /Users/kws/.claude/skills/how-it-works
```

Expected: missing links are created; existing exact links are accepted; a
different symlink or real path fails without overwrite.

- [ ] **Step 5: Unlink only the four already verified old symlinks**

Run:

```bash
unlink /Users/kws/.codex/skills/graspic
unlink /Users/kws/.claude/skills/graspic
unlink /Users/kws/.grok/skills/graspic
unlink /Users/kws/.agents/skills/graspic
```

Expected: each exact symlink is removed; no parent directory is deleted.

- [ ] **Step 6: Verify final link state**

Run:

```bash
test "$(python3 -c 'import pathlib; print(pathlib.Path("/Users/kws/.agents/skills/how-it-works").resolve(strict=True))')" = "/Users/kws/source/private/skills/skills/how-it-works"
test "$(python3 -c 'import pathlib; print(pathlib.Path("/Users/kws/.claude/skills/how-it-works").resolve(strict=True))')" = "/Users/kws/source/private/skills/skills/how-it-works"
for old_skill_link in /Users/kws/.codex/skills/graspic /Users/kws/.claude/skills/graspic /Users/kws/.grok/skills/graspic /Users/kws/.agents/skills/graspic; do test ! -e "$old_skill_link" && test ! -L "$old_skill_link" || exit 1; done
```

Expected: all exit 0. This external state is reported but not committed.

### Task 8: Run explicit fresh-session smoke on Codex, Claude Code, Grok, and Cursor

**Files:**
- Create: `tests/products/how-it-works/live/README.md`
- Create: `tests/products/how-it-works/live/cases.json`
- Create after approved execution: `tests/products/how-it-works/live/smoke-record.json`
- Modify: `docs/maintainers/products/how-it-works/compatibility.md`

**Interfaces:**
- Consumes: the two local links, installed host clients, synthetic cases, and the complete portable output contract.
- Produces: metadata-only evidence for discovery, explicit use, intended implicit use, near-miss non-use, and output completeness.

- [ ] **Step 1: Add synthetic live cases and a metadata-only schema**

```json
{
  "schema_version": 1,
  "cases": [
    {"id":"explicit-dns-path","prompt_codex":"$how-it-works DNS가 브라우저 요청에서 IP 주소가 되는 길을 보여줘","prompt_slash":"/how-it-works DNS가 브라우저 요청에서 IP 주소가 되는 길을 보여줘","expect":["discovered","explicit","claim","mermaid","numbered_hops","body","adjacent_slices","next_move"]},
    {"id":"implicit-dns-path","prompt":"DNS 요청이 브라우저에서 어디를 거쳐 IP 주소가 되는지 길로 보여줘","expect":["implicit","claim","mermaid","numbered_hops"]},
    {"id":"near-miss-debug","prompt":"DNS resolver 테스트 실패를 고쳐줘. 동작 설명은 하지 마.","expect":["not_activated"]}
  ]
}
```

`smoke-record.json` records only:

```json
{"schema_version":1,"executed_on":"2026-08-28","hosts":[{"host":"codex","client_version":"0.150.0","cases":{"explicit-dns-path":"pass","implicit-dns-path":"pass","near-miss-debug":"pass"},"verdict":"supported"}]}
```

The actual record must include all four hosts and execution-time versions; the shown Codex row defines shape, not a value to copy without running.

- [ ] **Step 2: Document evaluation rules before running providers**

`live/README.md` must define pass/fail from observable output, forbid private/user prompts, forbid committed full responses, use fresh sessions, state that calls may consume subscription/API quota, and require unsupported documentation when any host fails. Store temporary outputs outside the repository and delete them after scoring.

- [ ] **Step 3: Run provider-free checks before asking for live authorization**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --skill how-it-works
codex --version
claude --version
grok --version
/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' /Applications/Cursor.app/Contents/Info.plist
```

Expected: product verification exits 0 and all four client versions are captured.

- [ ] **Step 4: Pause and obtain explicit approval for potentially billable live calls**

Show the user the three synthetic prompts, the planned total of nine CLI calls plus three Cursor chats, and the no-transcript retention policy. Continue only after explicit approval in that execution turn. If approval is declined, leave all four hosts as `not_measured`; do not claim support from provider-free tests.

- [ ] **Step 5: Run three fresh ephemeral Codex calls**

Use a new `codex exec --ephemeral --sandbox read-only --cd
/Users/kws/source/private/skills` process for every case. Single quotes prevent
shell expansion of `$how-it-works`. Save output only in a temporary directory
outside the repository for scoring.

```bash
how_it_works_smoke_tmp="$(mktemp -d)"
codex exec --ephemeral --sandbox read-only --cd /Users/kws/source/private/skills '$how-it-works DNS가 브라우저 요청에서 IP 주소가 되는 길을 보여줘' | tee "$how_it_works_smoke_tmp/codex-explicit.txt"
codex exec --ephemeral --sandbox read-only --cd /Users/kws/source/private/skills 'DNS 요청이 브라우저에서 어디를 거쳐 IP 주소가 되는지 길로 보여줘' | tee "$how_it_works_smoke_tmp/codex-implicit.txt"
codex exec --ephemeral --sandbox read-only --cd /Users/kws/source/private/skills 'DNS resolver 테스트 실패를 고쳐줘. 동작 설명은 하지 마.' | tee "$how_it_works_smoke_tmp/codex-near-miss.txt"
```

- [ ] **Step 6: Run three fresh non-persistent Claude Code calls**

Use a separate `claude --print --no-session-persistence --permission-mode plan`
process per case and the slash form for explicit invocation.

```bash
claude --print --no-session-persistence --permission-mode plan '/how-it-works DNS가 브라우저 요청에서 IP 주소가 되는 길을 보여줘' | tee "$how_it_works_smoke_tmp/claude-explicit.txt"
claude --print --no-session-persistence --permission-mode plan 'DNS 요청이 브라우저에서 어디를 거쳐 IP 주소가 되는지 길로 보여줘' | tee "$how_it_works_smoke_tmp/claude-implicit.txt"
claude --print --no-session-persistence --permission-mode plan 'DNS resolver 테스트 실패를 고쳐줘. 동작 설명은 하지 마.' | tee "$how_it_works_smoke_tmp/claude-near-miss.txt"
```

- [ ] **Step 7: Run three fresh Grok calls**

Use a separate `grok --single --permission-mode plan --max-turns 1` process per
case. Run `grok inspect --json` first and confirm the shared `.agents`
discovery path is present.

```bash
grok inspect --json
grok --single '/how-it-works DNS가 브라우저 요청에서 IP 주소가 되는 길을 보여줘' --permission-mode plan --max-turns 1 | tee "$how_it_works_smoke_tmp/grok-explicit.txt"
grok --single 'DNS 요청이 브라우저에서 어디를 거쳐 IP 주소가 되는지 길로 보여줘' --permission-mode plan --max-turns 1 | tee "$how_it_works_smoke_tmp/grok-implicit.txt"
grok --single 'DNS resolver 테스트 실패를 고쳐줘. 동작 설명은 하지 마.' --permission-mode plan --max-turns 1 | tee "$how_it_works_smoke_tmp/grok-near-miss.txt"
```

- [ ] **Step 8: Run three fresh Cursor desktop chats**

Use the `computer-use:computer-use` skill, announcing that it is required for the installed desktop-only host. In a fresh Cursor window/session, verify the skill appears through `/how-it-works` or `@how-it-works`, then run explicit, implicit, and near-miss cases in separate new chats. Do not paste or commit complete responses; score only the specified observable criteria.

- [ ] **Step 9: Record verdicts, repair failures, and reconcile support claims**

Write one metadata-only row per host with execution-time version, date, the
three case verdicts, and final `supported` only when all required criteria
pass. If a host fails, invoke `superpowers:systematic-debugging`, identify a
portable in-scope cause, add a provider-free regression test, fix it, and rerun
the failed host in a fresh session. If the same build still fails after the
fix/retest loop, change `products.toml` and all active docs to remove that host
before committing; never weaken the common output or invent a passing verdict.

- [ ] **Step 10: Run privacy and JSON-shape checks**

Add product-contract assertions that live fixtures contain only allowed case fields and records contain only `host`, `client_version`, `cases`, and `verdict`. Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/how-it-works -p 'test_*.py'
git status --short
```

Expected: tests PASS; no provider transcript, screenshot, generated media, credential, or receipt is present.

After scoring and before committing, remove temporary transcripts only after
verifying the path was created by `mktemp`:

```bash
case "$how_it_works_smoke_tmp" in
  /tmp/*|/private/tmp/*|/var/folders/*|/private/var/folders/*)
    rm -rf -- "$how_it_works_smoke_tmp"
    ;;
  *)
    print -u2 -r -- "refusing unexpected temporary path: $how_it_works_smoke_tmp"
    exit 1
    ;;
esac
```

- [ ] **Step 11: Commit smoke procedure and metadata**

```bash
git add tests/products/how-it-works/live docs/maintainers/products/how-it-works/compatibility.md products.toml README.md README.en.md docs/users skills/how-it-works/README.md skills/how-it-works/README.en.md
git commit -m "test: record how-it-works host smoke"
```

### Task 9: Run the final acceptance matrix without publishing

**Files:**
- Modify only files implicated by a failing acceptance command.
- Do not modify local links again unless Task 7's exact-state check fails.

**Interfaces:**
- Consumes: identity, portable behavior, docs, stale gate, release bytes, links, and live evidence.
- Produces: implementation-ready local state with honest support claims and no remote publication.

- [ ] **Step 1: Verify the product registry and stale gate**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.repository.test_product_registry tests.repository.test_stale_identifiers -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/repository -p 'test_*.py'
```

Expected: all exit 0.

- [ ] **Step 2: Run product, catalog, and both provider-free profiles**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --skill how-it-works
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --catalog
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --profile full
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --profile windows-portable
```

Expected: all exit 0; no provider call runs.

- [ ] **Step 3: Re-run standalone release check and byte verification**

Run:

```bash
how_it_works_acceptance_root="$(mktemp -d)"
how_it_works_acceptance_output="$how_it_works_acceptance_root/output"
PYTHONDONTWRITEBYTECODE=1 python3 scripts/release.py check --product how-it-works
PYTHONDONTWRITEBYTECODE=1 python3 scripts/release.py build --product how-it-works --output "$how_it_works_acceptance_output"
PYTHONDONTWRITEBYTECODE=1 python3 scripts/release.py verify-download --product how-it-works --input "$how_it_works_acceptance_output"
python3 -m zipfile -l "$how_it_works_acceptance_output/how-it-works-v1.0.0.zip"
```

Expected: all commands exit 0; the archive is
`how-it-works-v1.0.0.zip`, checksum verification passes, and every archive
member is rooted at `how-it-works/`.

- [ ] **Step 4: Verify documentation links and host facts**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.repository.test_public_docs tests.repository.test_community_and_ci -v`

Expected: PASS; Korean and English product names, install commands, invocation forms, and host claims agree with `products.toml`.

- [ ] **Step 5: Verify local links and absence of old links**

Run:

```bash
test "$(python3 -c 'import pathlib; print(pathlib.Path("/Users/kws/.agents/skills/how-it-works").resolve(strict=True))')" = "/Users/kws/source/private/skills/skills/how-it-works"
test "$(python3 -c 'import pathlib; print(pathlib.Path("/Users/kws/.claude/skills/how-it-works").resolve(strict=True))')" = "/Users/kws/source/private/skills/skills/how-it-works"
for old_skill_link in /Users/kws/.codex/skills/graspic /Users/kws/.claude/skills/graspic /Users/kws/.grok/skills/graspic /Users/kws/.agents/skills/graspic; do
  test ! -e "$old_skill_link" && test ! -L "$old_skill_link" || exit 1
done
```

Expected: two new links resolve to the canonical payload and four old paths are absent.

- [ ] **Step 6: Inspect tracked and untracked state**

Run:

```bash
git status --short --branch
git diff --check
git diff --stat origin/main...HEAD
git log --oneline --decorate -20
```

Expected: only approved source/docs/test/tooling changes; no ZIP, checksum, provider output, generated media, credentials, billing record, or unrelated file.

- [ ] **Step 7: Confirm no publication occurred**

Run:

```bash
git tag --list 'how-it-works-v*'
gh release list --repo beyondwin/skills --limit 20
```

Expected: no `how-it-works-v*` tag and no How It Works GitHub Release. These are read-only checks, not publication commands.

- [ ] **Step 8: Commit acceptance-only corrections if present**

If acceptance exposed tracked defects, stage only the scoped project paths and commit:

```bash
git add products.toml scripts tests docs skills/how-it-works README.md README.en.md CONTRIBUTING.md .github
git commit -m "fix: close how-it-works acceptance gaps"
```

If no tracked correction exists, do not create an empty commit.

---

## Completion Gate

Completion means the old identity is absent from active paths, `how-it-works` 1.0.0 is the only current identity, the portable output is complete without a host tool, current documentation and registry agree, archive bytes verify from a fresh directory, exact local links are migrated, all four host claims have matching fresh-session evidence, and no tag, push, GitHub Release, cloud upload, or marketplace action occurred.
