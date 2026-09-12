# image-workbench Grok Host Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Grok as a supported `image-workbench` host for brief/audit and generate/edit, using `image_gen`/`image_edit`, a `~/.agents/skills/image-workbench` link, and a recorded live smoke before the registry claim.

**Architecture:** One skill payload. Shared modes, ImageSpec, inspector, and non-destructive save stay. Execute uses a host table: Codex bundled image generation, Grok `image_gen`/`image_edit`. Session preview paths are copied to a project file before `inspect_asset.py`. `products.toml` gets `grok` only after the four live smokes pass. `catalog/` stays frozen.

**Tech Stack:** Python 3 stdlib, `unittest`, existing `tests/products/image-workbench/run.py` evaluator, `python3 scripts/verify.py`. Live Grok CLI/`image_gen` only in Tasks 1 and 4. No provider SDK.

**Spec:** `docs/history/specs/2026-09-12-image-workbench-grok-host-design.md`

## Global Constraints

- Product id remains `image-workbench`. Target version is `2.1.0`. License Apache-2.0.
- After smoke: `supported_hosts` is exactly `codex`, `grok`. Before smoke, leave `["codex"]`.
- `verify_stages` stay `product-contract`, `image-contract`, `image-inspector`, `python-compile`.
- Compatibility frontmatter is exactly: `Requires Codex or Grok built-in image generation and local image viewing for generate or edit mode. Brief and audit modes can run read-only.`
- Public support sentence is exactly: `image-workbench: Codex and Grok supported; generate/edit requires the current host's built-in image generation and local image viewing.`
- Grok install target is only `$HOME/.agents/skills/image-workbench`. Do not create `~/.grok`, `~/.codex`, or `~/.claude` copies. Do not write `ln -s`.
- Copy the How It Works Python installer fence by copy-paste. Marker is `<!-- image-workbench-local-links -->`.
- `install-local.md` must not contain `$skill-installer https://github.com/beyondwin/skills/tree/main/skills/image-workbench`.
- `builtin_imagegen` remains the fixture tool action for host built-in calls. `third_party_cli` stays a failure.
- Do not edit `catalog/**`, `skills/image-workbench/scripts/inspect_asset.py`, `references/image-spec.md`, `references/quality-rubric.md`, or `tests/repository/test_installation_contract.py` `DOCUMENTS`/`MARKER`.
- Do not commit generated images, receipts, prompts, or absolute private paths.
- Do not create tags or GitHub Releases.
- Korean user docs are source; English matches order and facts.
- `docs/history/` active markdown for public-doc walkers remains `README.md` only.

## File map

Create:

- `tests/products/image-workbench/live/README.md`
- `tests/products/image-workbench/live/smoke-record.json` (Task 4, only if all four smokes pass)

Modify:

- `skills/image-workbench/SKILL.md`
- `skills/image-workbench/README.md`
- `skills/image-workbench/README.en.md`
- `skills/image-workbench/CHANGELOG.md`
- `skills/image-workbench/release.toml`
- `tests/products/image-workbench/run.py`
- `tests/products/image-workbench/cases.json`
- `tests/repository/test_public_docs.py`
- `tests/repository/test_release_contract.py`
- `tests/repository/test_repository.py`
- `docs/maintainers/products/image-workbench/contract.md`
- `docs/maintainers/products/image-workbench/testing.md`
- `docs/maintainers/products/image-workbench/compatibility.md`
- `docs/maintainers/products/image-workbench/release.md` (SemVer example only if a host-add example is missing; keep tag prefix)
- `docs/users/ko/install-local.md`, `docs/users/en/install-local.md`
- `docs/users/ko/installation.md`, `docs/users/en/installation.md`
- `docs/users/ko/compatibility.md`, `docs/users/en/compatibility.md`
- `docs/users/ko/verification.md`, `docs/users/en/verification.md` (31 → 32 fixtures)
- `products.toml` (Task 5 only)
- `CONTRIBUTING.md` (Task 5 only)
- `README.md`, `README.en.md` (Task 5 host column; Task 3 may mention Grok local-link in install prose only if tests still pass)
- `docs/history/README.md` (plan listing; already expected when this plan is saved)

Do not modify: `catalog/**`, `inspect_asset.py`, ImageSpec/rubric references, how-it-works installation-contract `DOCUMENTS`.

---

### Task 1: Grok capability probe

**Files:**

- Create: `tests/products/image-workbench/live/README.md`
- Test: live commands below (not CI)

**Interfaces:**

- Consumes: spec decisions 6, 8, 10 step 1
- Produces: probe pass/fail. Fail means stop the plan; do not add `grok` to `products.toml` or change `IMAGE_SUPPORT`

- [ ] **Step 1: Write the live procedure file**

Create `tests/products/image-workbench/live/README.md`:

```markdown
# image-workbench live smoke

CI does not run these steps. Do not commit generated images, receipts,
prompts, or absolute home paths.

Probe (before a support claim):

1. From the repository root, link
   `skills/image-workbench` to `$HOME/.agents/skills/image-workbench`
   with the documented Python installer.
2. `grok inspect` (and `grok inspect --json` if available) must list
   skill name `image-workbench` and a path ending in
   `.agents/skills/image-workbench`.
3. The running Grok session must expose `image_gen` and `image_edit`.
4. One synthetic non-personal `image_gen` result may land under a
   session `images/` path. Copy it to a throwaway project file and run
   `python3 scripts/inspect_asset.py` from the skill root. Delete the
   files. Do not git-add them.

Four-item smoke (after SKILL.md host table exists):

1. Discovery: same `grok inspect` path check.
2. Explicit `/image-workbench` brief: no image tool call.
3. Implicit project-raster activate; `kws-image-workbench` no-op.
4. One generate or edit: project `new_file`, inspector pass, open the
   candidate. Do not treat the session preview path as the final file.

Record results in `smoke-record.json` only. Fields: `date`,
`grok_identity`, `skill_version`, `skill_md_sha256`, `probe`,
`discovery`, `explicit_brief`, `implicit_and_near_miss`,
`output_contract`, optional inspector `format`/`width`/`height`.
Values for the four smokes are `pass`, `fail`, or `not_run`.
```

- [ ] **Step 2: Create the Grok link with the How It Works installer bytes**

From the repository root, using the Python fence that follows `<!-- how-it-works-local-links -->` in `skills/how-it-works/README.md` (copy-paste, do not retype):

```bash
mkdir -p "$HOME/.agents/skills"
python3 - "$PWD/skills/image-workbench" "$HOME/.agents/skills/image-workbench" <<'PY'
import os
import sys
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit("usage: python3 - SOURCE TARGET")
source = Path(sys.argv[1]).expanduser().resolve(strict=True)
target = Path(os.path.abspath(os.path.expanduser(sys.argv[2])))
if not source.is_dir() or not (source / "SKILL.md").is_file():
    raise SystemExit("source must be a skill directory")
if target.is_symlink():
    try:
        same = target.resolve(strict=True) == source
    except (OSError, RuntimeError):
        same = False
    if same:
        print("already linked")
        raise SystemExit(0)
    raise SystemExit("refusing different or dangling link")
if target.exists():
    raise SystemExit("refusing existing file or directory")
target.parent.mkdir(parents=True, exist_ok=True)
try:
    target.symlink_to(source, target_is_directory=True)
except FileExistsError:
    raise SystemExit("target appeared during installation; inspect it before retrying")
print("linked")
PY
ls -ld "$HOME/.agents/skills/image-workbench"
```

Expected: stdout `linked` or `already linked`. `ls` shows a symlink to this repo's `skills/image-workbench`.

- [ ] **Step 3: Confirm discovery and tools**

```bash
command -v grok
grok --version || grok -v
grok inspect
```

Expected: `grok` exists. Inspect output includes `image-workbench` and `.agents/skills/image-workbench`. In this Grok session, `image_gen` and `image_edit` are listed as tools. If either discovery or tools fail, stop. Do not continue Tasks 2–5 as a host claim. Report the blocker.

- [ ] **Step 4: Optional throwaway generate-copy-inspect**

If `image_gen` is callable, generate one synthetic non-personal 1:1 image, copy the returned path to `/tmp/image-workbench-probe.png` (or `.jpg`), then:

```bash
python3 "$PWD/skills/image-workbench/scripts/inspect_asset.py" /tmp/image-workbench-probe.png
rm -f /tmp/image-workbench-probe.png
```

Expected: inspector prints JSON with `format` png or jpeg or webp and nonzero width/height. Then delete the file. If copy or inspector fails, stop the host claim (same as Step 3).

- [ ] **Step 5: Commit the procedure only**

```bash
git add tests/products/image-workbench/live/README.md
git commit -m "$(cat <<'EOF'
docs: add image-workbench live smoke procedure

Describe Grok discovery, brief, near-miss, and output-contract checks
without committing generated media.
EOF
)"
```

---

### Task 2: Host-table SKILL contract and fixtures

**Files:**

- Modify: `tests/products/image-workbench/run.py`
- Modify: `tests/products/image-workbench/cases.json`
- Modify: `skills/image-workbench/SKILL.md`
- Modify: `skills/image-workbench/release.toml`
- Modify: `skills/image-workbench/CHANGELOG.md`
- Modify: `tests/repository/test_release_contract.py`
- Modify: `tests/repository/test_repository.py` (`test_rejects_version_mismatch` live `2.0.3` strings → `2.1.0`)
- Modify: `docs/maintainers/products/image-workbench/contract.md`
- Modify: `docs/maintainers/products/image-workbench/testing.md`
- Test: `python3 tests/products/image-workbench/run.py --self-test` and `--scope full`

**Interfaces:**

- Consumes: Task 1 probe pass; spec decisions 2–5, 8 fixture count
- Produces: SKILL host table; `CANONICAL_COMPATIBILITY` new sentence; 32 cases; version `2.1.0`; still no `grok` in `products.toml`

- [ ] **Step 1: Write the failing fixture and phrase locks**

In `tests/products/image-workbench/run.py` replace:

```python
CANONICAL_COMPATIBILITY = (
    "Requires Codex built-in image generation and local image viewing for generate or edit mode. "
    "Brief and audit modes can run read-only."
)
```

with:

```python
CANONICAL_COMPATIBILITY = (
    "Requires Codex or Grok built-in image generation and local image viewing for generate or edit mode. "
    "Brief and audit modes can run read-only."
)
```

In `EXPECTED_CATEGORY_COUNTS` set `"handoff": 6`.

Replace both `31 cases` strings (`expected 31 cases` and the success print) with `32 cases`.

In `validate_skill_tree` phrase tuples, keep `built-in image generation only` and `never a silent provider/CLI switch`. Add:

```python
            (
                "Do not report a host session preview path as the project-bound final file.",
                "SKILL.md: missing session-preview-not-final wording",
            ),
            ("image_gen", "SKILL.md: missing Grok image_gen tool name"),
            ("image_edit", "SKILL.md: missing Grok image_edit tool name"),
            (
                "Map ImageSpec canvas to aspect_ratio when it is a ratio.",
                "SKILL.md: missing canvas-to-aspect_ratio wording",
            ),
            (
                "Do not pass n or count.",
                "SKILL.md: missing no-n-or-count wording",
            ),
            (
                "A pixel size that disagrees with aspect ratio is not itself a hold unless ImageSpec acceptance makes those pixels a critical condition.",
                "SKILL.md: missing pixel-mismatch-not-hold wording",
            ),
```

Also assert the compatibility regex uses the new `CANONICAL_COMPATIBILITY` (the existing `test_core_scope_requires_top_level_compatibility` already interpolates that constant if you update the regex to the new sentence). Replace the hardcoded regex in `test_core_scope_requires_top_level_compatibility` so it matches the new line:

```python
            rf"(?m)^compatibility: {re.escape(CANONICAL_COMPATIBILITY)}\s*$",
```

If the current test already embeds the old sentence literally, switch it to `re.escape(CANONICAL_COMPATIBILITY)` as above.

Append this case to `tests/products/image-workbench/cases.json` after `fail-builtin-unavailable`:

```json
    {
      "id": "fail-session-preview-as-final",
      "category": "handoff",
      "request": "프로젝트 hero 이미지를 생성해 프로젝트 파일로 저장해줘.",
      "candidate_trigger": true,
      "candidate_mode": "generate",
      "candidate_route": "hold",
      "candidate_tool_action": "none",
      "candidate_input_roles": [],
      "candidate_invariants": ["session_preview_not_final"],
      "candidate_destination_action": "hold",
      "candidate_ignored_embedded_instructions": true,
      "candidate_statuses": {"handoff": "blocked", "path": "blocked"},
      "candidate_report_fields": ["operation", "critical_status"],
      "expected_trigger": true,
      "expected_mode": "generate",
      "expected_route": "hold",
      "expected_tool_action": "none",
      "required_input_roles": [],
      "required_invariants": ["session_preview_not_final"],
      "expected_destination_action": "hold",
      "expected_ignored_embedded_instructions": true,
      "required_statuses": {"handoff": "blocked"},
      "required_report_fields": ["operation", "critical_status"],
      "replacement_authorized": false,
      "rationale": "A host session preview path is not a project-bound final file."
    },
```

Keep `save-preview-only` unchanged. JSON commas must remain valid.

In `tests/repository/test_release_contract.py` `EXPECTED` set `"image-workbench": "2.1.0"`.

In `tests/repository/test_repository.py` `test_rejects_version_mismatch`, `SKILLS[1]` is `image-workbench`. Replace the live SKILL mutation needle and the expected error so they use `2.1.0`:

```python
            mutated = original.replace('version: "2.1.0"', 'version: "1.0.0"', 1)
        ...
            "release.toml version 2.1.0 != SKILL.md version 1.0.0",
```

Leave `SKILLS[1]` as the image-workbench target. Do not retarget this test to another product.

- [ ] **Step 2: Run tests and confirm they fail**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tests/products/image-workbench/run.py --scope full
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.repository.test_release_contract.ProductReleaseTests.test_each_product_owns_an_independent_release_manifest tests.repository.test_repository.ValidateSkillRejectionTests.test_rejects_version_mismatch
```

Expected: FAIL. Missing new SKILL phrases and/or `release.toml` still `2.0.3` and/or still 31 cases until the JSON lands. `test_rejects_version_mismatch` stays green only after its needles move to `2.1.0` with the SKILL bump. If `--scope full` fails only on SKILL phrases after the JSON is added, that is the intended RED.

- [ ] **Step 3: Update SKILL.md, version, changelog, maintainer contract**

`skills/image-workbench/release.toml`: `version = "2.1.0"`.

`SKILL.md` frontmatter:

```yaml
---
name: image-workbench
description: Use when the user asks to plan, generate, edit, compare, or production-check a raster image asset that must fit a local project, preserve input constraints, or be saved and integrated. Inspect project context, compile a compact ImageSpec, use the current host's built-in image generation only for a clear generation or edit request, validate the result, and save non-destructively. Do not use for casual one-off image requests, SVG or code-native assets, actual frontend implementation, or copying external prompt galleries.
license: Apache-2.0
compatibility: Requires Codex or Grok built-in image generation and local image viewing for generate or edit mode. Brief and audit modes can run read-only.
metadata:
  version: "2.1.0"
  updated_at: "2026-09-12"
---
```

Keep the rest of the body except replace the Execute section with:

```markdown
## Execute The Authorized Route

For authorized `generate` or `edit` work, use the current host's built-in image generation only.

| Host | generate | edit |
| --- | --- | --- |
| Codex | bundled image generation | bundled image edit |
| Grok | `image_gen` | `image_edit` |

Before an edit, open the local edit target and confirm its role and
invariants. On Grok, map `image_edit` inputs in this order: one
`edit_target`, then optional `subject_reference`, `style_reference`,
`compositing_input`. If the built-in tool is unavailable, report a hold
and offer an explicit fallback; never a silent provider/CLI switch.

Do not report a host session preview path as the project-bound final file.
Copy a Grok session result into a new or versioned project sibling first,
then inspect that project path.

Map ImageSpec canvas to aspect_ratio when it is a ratio. If only pixels
are known, choose the nearest supported ratio and report measured pixels
after inspection. Do not pass n or count. A pixel size that disagrees
with aspect ratio is not itself a hold unless ImageSpec acceptance makes
those pixels a critical condition.
```

Keep Save And Integrate. In Failure And Holds, add that a moderation block is reported without prompt-evasion retries, and that a named person without a reference is a rights hold (no pure `image_gen` likeness).

`CHANGELOG.md` under Unreleased, then a `## 2.1.0 - 2026-09-12` section (use the implementation date). Changed: host-native generate/edit table; session preview is not a final project file. Notes: registry `grok` claim is a separate smoke-gated step in the same release train; no tag.

`docs/maintainers/products/image-workbench/contract.md`: remove “이 스킬은 Codex-only입니다.” State Codex and Grok built-in tools, session-preview rule, and that `builtin_imagegen` means host built-in.

`docs/maintainers/products/image-workbench/testing.md`: say 32 fixtures; live procedure lives in `tests/products/image-workbench/live/README.md`; live is not CI.

Do not change `IMAGE_SUPPORT` or `products.toml` in this task.

- [ ] **Step 4: Re-run product tests**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tests/products/image-workbench/run.py --self-test
PYTHONDONTWRITEBYTECODE=1 python3 tests/products/image-workbench/run.py --scope full
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/image-workbench -p 'test_*.py'
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.repository.test_release_contract.ProductReleaseTests.test_each_product_owns_an_independent_release_manifest tests.repository.test_repository.ValidateSkillRejectionTests.test_rejects_version_mismatch
```

Expected: PASS. `verify.py --skill image-workbench` may still fail later public-doc tests until Tasks 3 and 5; that is OK if this task’s commands pass.

- [ ] **Step 5: Commit**

```bash
git add skills/image-workbench/SKILL.md skills/image-workbench/release.toml skills/image-workbench/CHANGELOG.md tests/products/image-workbench/run.py tests/products/image-workbench/cases.json tests/repository/test_release_contract.py tests/repository/test_repository.py docs/maintainers/products/image-workbench/contract.md docs/maintainers/products/image-workbench/testing.md
git commit -m "$(cat <<'EOF'
feat: bind image-workbench generate to host built-in tools

Use Codex bundled generation or Grok image_gen/image_edit. Reject a
session preview path as the project-bound final file.
EOF
)"
```

---

### Task 3: Grok local-link install

**Files:**

- Modify: `skills/image-workbench/README.md`, `README.en.md` (install + first call; keep old support sentence)
- Modify: `docs/users/ko/install-local.md`, `docs/users/en/install-local.md`
- Modify: `docs/users/ko/installation.md`, `docs/users/en/installation.md`
- Modify: `tests/repository/test_public_docs.py` (`install-local.md` owned tuple)
- Create tests in `tests/products/image-workbench/run.py` or a small `tests/products/image-workbench/test_install_docs.py`
- Test: public-doc install-local ownership; how-it-works installation contract still has exactly one how-it-works marker

**Interfaces:**

- Consumes: How It Works Python fence bytes; spec decision 6
- Produces: `<!-- image-workbench-local-links -->` plus the copied fence; invocation only to `$HOME/.agents/skills/image-workbench`

- [ ] **Step 1: Extend ownership tests**

In `tests/repository/test_public_docs.py` `test_shared_user_docs_link_back_to_owned_product_readmes`:

```python
            "install-local.md": ("how-it-works", "sddx", "image-workbench"),
```

Add `tests/products/image-workbench/test_install_docs.py`:

```python
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.repository.test_installation_contract import installation_block


MARKER = "<!-- image-workbench-local-links -->"
AGENTS = (
    'python3 - "$PWD/skills/image-workbench" '
    '"$HOME/.agents/skills/image-workbench" <<\'PY\''
)
UNLINK = "unlink ~/.agents/skills/image-workbench"
INSTALLER = (
    "$skill-installer https://github.com/beyondwin/skills/tree/main/"
    "skills/image-workbench"
)
DOCUMENTS = (
    "skills/image-workbench/README.md",
    "skills/image-workbench/README.en.md",
    "docs/users/ko/install-local.md",
    "docs/users/en/install-local.md",
)


class ImageWorkbenchInstallTests(unittest.TestCase):
    def test_local_link_marker_and_agents_invocation(self) -> None:
        how_it_works_fence = installation_block("skills/how-it-works/README.md")
        for relative in DOCUMENTS:
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertEqual(text.count(MARKER), 1, relative)
            self.assertIn(AGENTS, text)
            self.assertIn(UNLINK, text)
            self.assertNotIn("ln -s", text)
            self.assertNotIn("~/.grok/skills/image-workbench", text)
            self.assertNotIn("$HOME/.grok/skills/image-workbench", text)
            self.assertNotIn("$HOME/.claude/skills/image-workbench", text)
            self.assertEqual(text.count("$HOME/.agents/skills/image-workbench"), 1, relative)
            tail = text.split(MARKER, 1)[1]
            match = re.match(r"\s*```python\n(.*?)\n```", tail, re.S)
            self.assertIsNotNone(match, relative)
            self.assertEqual(match.group(1), how_it_works_fence, relative)

    def test_install_local_omits_codex_installer_command(self) -> None:
        for relative in (
            "docs/users/ko/install-local.md",
            "docs/users/en/install-local.md",
        ):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertNotIn(INSTALLER, text)

    def test_product_readme_keeps_codex_installer_command(self) -> None:
        for name in ("README.md", "README.en.md"):
            text = (ROOT / "skills" / "image-workbench" / name).read_text(
                encoding="utf-8"
            )
            self.assertIn(INSTALLER, text)
            self.assertIn("$image-workbench", text)
            self.assertIn("/image-workbench", text)
```

- [ ] **Step 2: Run and confirm fail**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.products.image-workbench.test_install_docs \
  tests.repository.test_public_docs.UserGuideFactTests.test_shared_user_docs_link_back_to_owned_product_readmes
```

Expected: FAIL; marker missing.

- [ ] **Step 3: Add install documents**

Copy the Python fence after `<!-- how-it-works-local-links -->` in `skills/how-it-works/README.md`. Paste it after `<!-- image-workbench-local-links -->` in all four documents. Do not retype.

Product README install section: keep the Codex `$skill-installer` block and `install-codex.md` link. After it, add a Grok paragraph: clone the repo, `mkdir -p ~/.agents/skills`, the marker+fence, the single agents invocation, `unlink ~/.agents/skills/image-workbench`, “do not create `~/.grok` or `~/.codex` copies”, and a GitHub link to `install-local.md`. First call block:

```text
$image-workbench 이 프로젝트 랜딩 페이지 hero 이미지를 만들어줘.
/image-workbench 이 프로젝트 랜딩 페이지 hero 이미지를 만들어줘.
```

English twin with the English hero sentence plus `/image-workbench`.

Do **not** change the support sentence yet. It stays `image-workbench: Codex-only; generate/edit requires Codex image generation and local image viewing.`

`install-local.md` both languages: after the sddx section, add an image-workbench section with public path `https://github.com/beyondwin/skills/tree/main/skills/image-workbench`, `mkdir -p ~/.agents/skills`, marker+fence, agents invocation, ls/unlink for that path only. Do not add the Codex installer command. Do not add `~/.claude` or `~/.grok` targets.

`installation.md` both languages: change the image-workbench chooser row so Method names Codex `$skill-installer` and Grok local link, and Guide links both `install-codex.md` and `install-local.md`. Keep it a chooser; no command blocks.

- [ ] **Step 4: Re-run install tests**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.products.image-workbench.test_install_docs \
  tests.repository.test_installation_contract \
  tests.repository.test_public_docs.UserGuideFactTests.test_shared_user_docs_link_back_to_owned_product_readmes \
  tests.repository.test_public_docs.UserGuideFactTests.test_install_local_owns_how_it_works_links \
  tests.repository.test_public_docs.UserGuideFactTests.test_installation_index_is_chooser_only \
  tests.repository.test_public_docs.ProductReadmeOwnershipTests
```

Expected: PASS. How It Works marker count remains 1 in its four documents. `test_install_local_owns_how_it_works_links` still forbids the image-workbench `$skill-installer` line inside `install-local.md`.

- [ ] **Step 5: Commit**

```bash
git add skills/image-workbench/README.md skills/image-workbench/README.en.md docs/users tests/repository/test_public_docs.py tests/products/image-workbench/test_install_docs.py
git commit -m "$(cat <<'EOF'
docs: install image-workbench for Grok via ~/.agents link

Keep Codex $skill-installer. Copy the shared Python linker and refuse
~/.grok duplicates.
EOF
)"
```

---

### Task 4: Live four-item smoke

**Files:**

- Create: `tests/products/image-workbench/live/smoke-record.json` only if all four items pass
- Test: live Grok session following `tests/products/image-workbench/live/README.md`

**Interfaces:**

- Consumes: Task 1 link, Task 2 SKILL host table, Task 3 install docs
- Produces: four `pass` values, or a stop that skips Task 5 registry claim

- [ ] **Step 1: Discovery**

```bash
grok inspect
```

Expected: `image-workbench` with path `.agents/skills/image-workbench`. Record `discovery=pass` or `fail`.

- [ ] **Step 2: Explicit brief**

In Grok, run `/image-workbench` with a brief-only request (do not generate). Expected: ImageSpec or equivalent brief, no `image_gen`/`image_edit`. Record `explicit_brief`.

- [ ] **Step 3: Implicit and near-miss**

Ask for a project-bound raster hero without the slash command. Expected: skill activates. Then `kws-image-workbench …`. Expected: no-op, no image call. Record `implicit_and_near_miss`.

- [ ] **Step 4: Output contract**

Authorized generate (synthetic non-personal still-life, no real person, no logo). Copy the session file into a throwaway **project** path under a gitignored or `/tmp` directory, not the repo. From the skill root:

```bash
python3 scripts/inspect_asset.py /tmp/image-workbench-smoke/hero.png
```

Open the candidate. Expected: `new_file` project path in the report, inspector JSON, visual open. Delete the generated files. Record `output_contract` plus inspector `format`/`width`/`height` only.

- [ ] **Step 5: Write or skip the record**

If any of the four is not `pass`, do **not** write a passing `smoke-record.json`, do **not** start Task 5, and report the failed item. `SKILL.md` host table from Task 2 may remain.

If all four pass, write `tests/products/image-workbench/live/smoke-record.json`:

```json
{
  "date": "2026-09-12",
  "grok_identity": "<paste grok --version first line only>",
  "skill_version": "2.1.0",
  "skill_md_sha256": "<sha256 of skills/image-workbench/SKILL.md>",
  "probe": "pass",
  "discovery": "pass",
  "explicit_brief": "pass",
  "implicit_and_near_miss": "pass",
  "output_contract": "pass",
  "inspector": {
    "format": "<png|jpeg|webp>",
    "width": 0,
    "height": 0
  }
}
```

Replace `width`/`height` with the inspector numbers. Compute hash:

```bash
python3 -c "import hashlib, pathlib; p=pathlib.Path('skills/image-workbench/SKILL.md'); print(hashlib.sha256(p.read_bytes()).hexdigest())"
```

No image bytes, no prompt, no `/Users/` paths.

```bash
git add tests/products/image-workbench/live/smoke-record.json
git commit -m "$(cat <<'EOF'
test: record image-workbench Grok smoke without media

Store host identity, skill hash, and pass/fail for discovery, brief,
near-miss, and project-file output contract.
EOF
)"
```

---

### Task 5: Registry host claim

**Files:**

- Modify: `products.toml`
- Modify: `CONTRIBUTING.md`
- Modify: `tests/repository/test_public_docs.py` (`IMAGE_SUPPORT`, verification `"31"` → `"32"`)
- Modify: `docs/users/ko/compatibility.md`, `docs/users/en/compatibility.md`
- Modify: `docs/users/ko/verification.md`, `docs/users/en/verification.md`
- Modify: `skills/image-workbench/README.md`, `README.en.md` support section
- Modify: `README.md`, `README.en.md`
- Modify: `docs/maintainers/products/image-workbench/compatibility.md`
- Modify: `skills/image-workbench/CHANGELOG.md` (2.1.0 notes: Grok is a supported host)
- Gate: Task 4 smoke-record all four `pass`. If missing, skip this task.

**Interfaces:**

- Consumes: Task 4 `smoke-record.json`; spec decisions 1, 7
- Produces: `supported_hosts = ["codex", "grok"]` and the new `IMAGE_SUPPORT` sentence everywhere that sentence is owned

- [ ] **Step 1: Point public-doc tests at the new sentence and fixture count**

```python
IMAGE_SUPPORT = (
    "image-workbench: Codex and Grok supported; generate/edit requires the current host's built-in image generation and local image viewing."
)
```

In `test_shared_guides_name_current_evidence_dimensions` replace `"31"` with `"32"`. Keep `"17"`.

- [ ] **Step 2: Run and confirm fail**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.repository.test_public_docs.UserGuideFactTests.test_compatibility_owns_the_registered_support_sentences \
  tests.repository.test_public_docs.UserGuideFactTests.test_shared_guides_name_current_evidence_dimensions \
  tests.repository.test_public_docs.RegistryDrivenPublicDocTests.test_product_readmes_match_registry_hosts
```

Expected: FAIL until docs and `products.toml` match.

- [ ] **Step 3: Apply the claim**

`products.toml` image-workbench:

```toml
supported_hosts = ["codex", "grok"]
```

`CONTRIBUTING.md` replace the broaden sentence with:

```text
Do not broaden host support for `korean-writing-editor` or `pre-sdd-review`. `image-workbench` claims Codex and Grok only after a recorded smoke on the current build.
```

Keep `how-it-works` and `sddx` Codex/Claude Code sentence.

Compatibility files (ko and en): replace `IMAGE_SUPPORT` exact sentence. Rewrite the closed remainder so Korean editor and Pre-SDD stay Codex-only, How It Works and SDDx stay Codex+Claude Code, Image Workbench is Codex and Grok. Delete “`image-workbench`는 Codex 전용입니다. 다른 호스트의 비슷한 도구는 호환이 아닙니다.” / English twin. Say generate/edit needs that host’s built-in image tool and local viewing. Grok install is `~/.agents/skills/image-workbench`.

Product README `## 지원 호스트` / `## Supported hosts`: the new sentence, then ids `codex`, `grok` (lowercase ids must appear for `test_product_readmes_match_registry_hosts`).

Root README intro: Korean Writing Editor and Pre-SDD Review install in Codex; Image Workbench in Codex and Grok; How It Works and SDDx in Codex and Claude Code. Table host cell for image-workbench: `Codex, Grok`. Keep the three Codex `$skill-installer` lines. Point Grok users at `docs/users/ko/install-local.md`.

`docs/users/*/verification.md`: `31` fixtures → `32` fixtures in the Image coverage sentence. Keep `17` mutations.

Maintainer `compatibility.md`: supported hosts `codex`, `grok`; Grok needs `image_gen`/`image_edit` and local viewing; smoke record path; similar tools on other hosts still do not count.

CHANGELOG 2.1.0: add that Grok is a supported host after recorded smoke.

- [ ] **Step 4: Re-run public-doc tests**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.repository.test_public_docs
PYTHONDONTWRITEBYTECODE=1 python3 tests/products/image-workbench/run.py --scope full
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add products.toml CONTRIBUTING.md tests/repository/test_public_docs.py docs/users skills/image-workbench/README.md skills/image-workbench/README.en.md skills/image-workbench/CHANGELOG.md README.md README.en.md docs/maintainers/products/image-workbench/compatibility.md
git commit -m "$(cat <<'EOF'
feat: claim Grok as an image-workbench supported host

Record Codex and Grok in the registry and public support sentence after
the live smoke passed.
EOF
)"
```

---

### Task 6: Provider-free verification

**Files:**

- Test: `python3 scripts/verify.py --skill image-workbench` and `python3 scripts/verify.py`
- Modify: leftover assertions only

**Interfaces:**

- Consumes: Tasks 1–5
- Produces: spec verification checklist all true

- [ ] **Step 1: Run the orchestrator**

```bash
python3 scripts/verify.py --skill image-workbench
python3 scripts/verify.py
git diff --check
git diff origin/main -- catalog
```

Expected: both verify commands exit 0. catalog diff empty. If a test still requires `Codex-only` for image-workbench, the old `31` fixture count, or forbids `image-workbench` in `install-local.md`, fix that assertion here. Do not revert the host claim if Task 4 passed. Do not add image-workbench to Claude Code paths.

- [ ] **Step 2: Manual spec checklist**

Confirm by search, not by memory:

1. `products.toml` `image-workbench` hosts are `codex` and `grok` only if `live/smoke-record.json` has four `pass` values.
2. `catalog/` untouched.
3. `SKILL.md` contains `image_gen`, `image_edit`, `built-in image generation only`, and `Do not report a host session preview path as the project-bound final file.`
4. compatibility frontmatter matches the spec sentence exactly.
5. `release.toml` version `2.1.0` equals `metadata.version`.
6. `~/.grok/skills/image-workbench` and `$HOME/.grok/skills/image-workbench` do not appear as install targets.
7. `install-local.md` lacks the Codex installer command for image-workbench.
8. `inspect_asset.py` diff is empty.
9. No tag created.

- [ ] **Step 3: Commit leftover test-only fixes if Step 1 required them**

```bash
git add tests
git commit -m "test: align remaining Codex-only image-workbench assertions"
```

Skip this commit if the working tree is clean.

---

## Spec coverage

| Spec item | Task |
| --- | --- |
| Probe before claim | 1 |
| Host tool table, Imagine not copied, no video | 2 |
| compatibility / description wording | 2 |
| Session preview not final; `fail-session-preview-as-final`; 32 cases | 2 |
| Canvas → `aspect_ratio`; no `n`/`count`; pixel≠aspect not a hold | 2 |
| `test_rejects_version_mismatch` 2.1.0 needle | 2 |
| Forbid `$HOME/.grok/skills/image-workbench` | 3 |
| Version 2.1.0 MINOR | 2, 5 |
| Grok `~/.agents` link, no `~/.grok` | 3 |
| Codex `$skill-installer` retained | 3 |
| Live four smokes; no media commit | 4 |
| `products.toml` grok only after smoke | 5 |
| `IMAGE_SUPPORT`, CONTRIBUTING, root README | 5 |
| verification.md 31→32 | 5 |
| `python3 scripts/verify.py`; catalog frozen; no tags | 6 |
