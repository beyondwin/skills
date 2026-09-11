# Documentation Structure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split user install docs, unify the four product README heading sets, and lock public-doc tests on facts instead of duplicated prose.

**Architecture:** Keep `docs/users/` vs `docs/maintainers/` and keep `skills/<name>/` install paths. `installation.md` stays as the chooser table. New `install-codex.md` and `install-local.md` own procedures. Product READMEs keep GitHub `blob/main` URLs and the How It Works Python installer block. Payload README edits are PATCH on each product; do not tag or publish.

**Tech Stack:** Markdown, `unittest`, `python3 scripts/verify.py`, `products.toml` registry, existing `scripts/lib/documentation.py` globs.

**Spec:** `docs/history/specs/2026-09-11-documentation-structure-design.md`

## Global Constraints

- Do not rename `docs/users/` or `docs/maintainers/` into verb folders.
- Do not rename `installation.md`, `safety-and-privacy.md`, or `verification.md` to `install.md` / `safety.md` / `verify.md`.
- Do not add redirect-only stubs.
- Do not restore How It Works install to `ln -s`.
- Do not edit `SKILL.md` instruction bodies. Frontmatter `metadata.version` and `updated_at` may change only for PATCH.
- Do not edit `catalog/` bodies.
- Do not merge maintainer `contract.md` / `testing.md` / `compatibility.md` / `release.md`.
- Do not create tags or GitHub Releases.
- Korean user docs are source; English matches order and facts (commands, host ids, product names, support sentences).
- Product README links to repo docs stay `https://github.com/beyondwin/skills/blob/main/...`. Do not introduce `](../../docs/` in `skills/how-it-works/`.
- `<!-- how-it-works-local-links -->` plus the Python fence must be byte-identical in the four documents named in spec decision 5. Copy the block; do not retype it.
- `docs/history/` active markdown is only `README.md`. Do not add this plan to `active_markdown_paths`.
- No `curl | sh` or `rm -rf` in public docs.

## File map

Create:

- `docs/users/ko/install-codex.md`
- `docs/users/en/install-codex.md`
- `docs/users/ko/install-local.md`
- `docs/users/en/install-local.md`

Modify (docs):

- `docs/users/ko/installation.md`, `docs/users/en/installation.md` — table only
- `docs/users/ko/verification.md`, `docs/users/en/verification.md` — drop per-product fixture path list; keep evidence-dimension phrases the tests already lock
- `docs/users/ko/compatibility.md`, `docs/users/en/compatibility.md` — drop current-version literals such as `2.0.0`; keep support sentences
- `docs/README.md`, `README.md`, `README.en.md` — route to the split install files
- `skills/*/README.md`, `skills/*/README.en.md` — unified H2 set
- `docs/maintainers/products/pre-sdd-review/contract.md` — own the machine-readable Contract list
- `docs/maintainers/products/<name>/testing.md` — own fixture paths
- `docs/maintainers/products/<name>/release.md` — drop duplicated check/build command blocks; point at `repository/release.md`
- `docs/maintainers/repository/architecture.md` — shorter Korean source
- `docs/history/README.md` — list this plan while it is in progress

Modify (versions, only in the README task):

- `skills/<name>/release.toml`, `SKILL.md` frontmatter, `CHANGELOG.md`
- korean-writing-editor `2.0.2` → `2.0.3`
- image-workbench `2.0.2` → `2.0.3`
- how-it-works `2.0.0` → `2.0.1`
- pre-sdd-review `3.0.0` → `3.0.1`
- `updated_at`: `2026-09-11`

Modify (tests):

- `tests/repository/test_public_docs.py`
- `tests/repository/test_installation_contract.py`
- `tests/repository/test_product_registry.py`
- `tests/repository/test_changed_targets.py`
- `tests/repository/test_release_contract.py`
- `tests/products/how-it-works/test_contract.py`
- `tests/products/pre-sdd-review/test_contract.py`
- `tests/products/korean-writing-editor/test_package.py`

Do not modify: `skills/*/SKILL.md` bodies, `catalog/**` bodies except if a link breaks (it should not), `docs/history/specs/2026-09-11-documentation-structure-design.md`.

---

### Task 1: Split user install docs

**Files:**

- Create: `docs/users/ko/install-codex.md`
- Create: `docs/users/en/install-codex.md`
- Create: `docs/users/ko/install-local.md`
- Create: `docs/users/en/install-local.md`
- Modify: `docs/users/ko/installation.md`
- Modify: `docs/users/en/installation.md`
- Modify: `docs/users/ko/compatibility.md` (nav may stay `installation.md`; drop `2.0.0` literal)
- Modify: `docs/users/en/compatibility.md` (same)
- Modify: `tests/repository/test_public_docs.py` (`USER_GUIDES`, install tests, four-file set, product-name cartesian)
- Modify: `tests/repository/test_installation_contract.py` (`DOCUMENTS`)
- Modify: `tests/repository/test_product_registry.py` (`test_korean_and_english_docs_share_registry_install_and_host_facts`)
- Modify: `tests/repository/test_changed_targets.py` (`test_shared_public_docs_select_every_target`)
- Test: the files above

**Interfaces:**

- Consumes: current `docs/users/*/installation.md` Codex / npx / clone / update sections and the How It Works Python block already in `skills/how-it-works/README.md`
- Produces: six user markdown files per language; `USER_GUIDES` lists all twelve paths; install-contract `DOCUMENTS` is the four How It Works files named in spec decision 5

- [ ] **Step 1: Write the failing inventory and ownership tests**

In `tests/repository/test_public_docs.py` replace `USER_GUIDES` with:

```python
USER_GUIDES = (
    ROOT / "docs" / "users" / "ko" / "installation.md",
    ROOT / "docs" / "users" / "ko" / "install-codex.md",
    ROOT / "docs" / "users" / "ko" / "install-local.md",
    ROOT / "docs" / "users" / "ko" / "compatibility.md",
    ROOT / "docs" / "users" / "ko" / "safety-and-privacy.md",
    ROOT / "docs" / "users" / "ko" / "verification.md",
    ROOT / "docs" / "users" / "en" / "installation.md",
    ROOT / "docs" / "users" / "en" / "install-codex.md",
    ROOT / "docs" / "users" / "en" / "install-local.md",
    ROOT / "docs" / "users" / "en" / "compatibility.md",
    ROOT / "docs" / "users" / "en" / "safety-and-privacy.md",
    ROOT / "docs" / "users" / "en" / "verification.md",
)
CODEX_PRODUCTS = (
    "korean-writing-editor",
    "image-workbench",
    "pre-sdd-review",
)
```

Replace `test_only_four_user_guides_exist_per_language` with:

```python
def test_six_user_guides_exist_per_language(self) -> None:
    expected = {
        "installation.md",
        "install-codex.md",
        "install-local.md",
        "compatibility.md",
        "safety-and-privacy.md",
        "verification.md",
    }
    for language in ("ko", "en"):
        self.assertEqual(
            {p.name for p in (ROOT / "docs/users" / language).glob("*.md")},
            expected,
        )
        self.assertFalse((ROOT / "docs" / language).exists())
```

Replace `test_shared_user_docs_link_back_to_all_product_readmes` so coverage matches ownership:

```python
def test_shared_user_docs_link_back_to_owned_product_readmes(self) -> None:
    all_products = tuple(product.name for product in REGISTRY.products)
    owned = {
        "installation.md": all_products,
        "compatibility.md": all_products,
        "safety-and-privacy.md": all_products,
        "verification.md": all_products,
        "install-codex.md": CODEX_PRODUCTS,
        "install-local.md": ("how-it-works",),
    }
    for language in ("ko", "en"):
        readme = "README.en.md" if language == "en" else "README.md"
        for filename, names in owned.items():
            text = _read(ROOT / "docs" / "users" / language / filename)
            for name in names:
                self.assertIn(
                    f"skills/{name}/{readme}",
                    text,
                    f"{language}/{filename} {name}",
                )
```

Replace `test_installation_covers_install_update_and_inspection` with two tests. `installation.md` must not contain `$skill-installer` command blocks, the How It Works marker, or `python3 scripts/verify.py`. It must link `install-codex.md`, `install-local.md`, and `skills/pre-sdd-review/evidence/README.md`.

```python
def test_installation_index_is_chooser_only(self) -> None:
    for language in ("ko", "en"):
        path = ROOT / "docs" / "users" / language / "installation.md"
        text = _read(path)
        self.assertNotIn("<!-- how-it-works-local-links -->", text)
        self.assertNotIn("$skill-installer https://github.com", text)
        self.assertNotIn("python3 scripts/verify.py", text)
        self.assertIn("install-codex.md", text)
        self.assertIn("install-local.md", text)
        self.assertIn("skills/pre-sdd-review/evidence/README.md", text)
        for name in REGISTRY.names:
            self.assertIn(name, text)

def test_install_codex_owns_codex_install_update_and_npx(self) -> None:
    for language in ("ko", "en"):
        text = _read(ROOT / "docs" / "users" / language / "install-codex.md")
        self.assertIn("$skill-installer", text)
        for name in CODEX_PRODUCTS:
            self.assertIn(INSTALLER_COMMANDS[name], text)
        self.assertNotIn(INSTALLER_COMMANDS["how-it-works"], text)
        self.assertNotIn("<!-- how-it-works-local-links -->", text)
        self.assertIn(OPTIONAL_NPX, text)
        self.assertIn(GIT_CLONE, text)
        self.assertTrue("inspect" in text.lower() or "확인" in text)
        self.assertTrue("third-party" in text.lower() or "제3자" in text)

def test_install_local_owns_how_it_works_links(self) -> None:
    for language in ("ko", "en"):
        rel = f"docs/users/{language}/install-local.md"
        text = _read(ROOT / rel)
        self.assertIn(HOW_IT_WORKS_MKDIR, text)
        self.assertTrue(installation_block(rel))
        self.assertIn(HOW_IT_WORKS_AGENTS_INVOCATION, text)
        self.assertIn(HOW_IT_WORKS_CLAUDE_INVOCATION, text)
        self.assertIn(HOW_IT_WORKS_UNLINK_AGENTS, text)
        self.assertIn(HOW_IT_WORKS_UNLINK_CLAUDE, text)
        self.assertNotIn("$skill-installer https://github.com/beyondwin/skills/tree/main/skills/korean-writing-editor", text)
```

Move How It Works primary-vs-local assertions in `test_how_it_works_install_and_remove_share_agents_destination` off `installation.md` and onto `install-codex.md` / `install-local.md`. Codex primary file must not contain the How It Works `$skill-installer` command. Local file must contain `~/.agents/skills/how-it-works` and the unlink commands. Keep the product-README half of that test unchanged in this task.

Change `test_pre_sdd_review_shared_guides_preserve_scope_and_evidence_limits` so the Codex installer command is asserted in `install-codex.md`, not `installation.md`. Assert `python3 skills/pre-sdd-review/evidence/evidence.py --version` in `skills/pre-sdd-review/evidence/README.md`, not in `installation.md`. Keep the `--bin-dir` / `install.py` / launcher forbidden strings on all user install files.

In `tests/repository/test_installation_contract.py` set:

```python
DOCUMENTS = (
    "skills/how-it-works/README.md",
    "skills/how-it-works/README.en.md",
    "docs/users/ko/install-local.md",
    "docs/users/en/install-local.md",
)
```

In `tests/repository/test_product_registry.py` `test_korean_and_english_docs_share_registry_install_and_host_facts`, stop iterating a fixed four-file list. For `installation.md`, `compatibility.md`, `safety-and-privacy.md`, and `verification.md` require every product name and `skills/<name>/README.md` (or `.en.md`). For `install-codex.md` require only the three Codex products. For `install-local.md` require only `how-it-works`.

In `tests/repository/test_changed_targets.py` `test_shared_public_docs_select_every_target`, add `"docs/users/ko/install-codex.md"` and `"docs/users/en/install-local.md"` to the path tuple (keep existing README and verification examples).

- [ ] **Step 2: Run the new tests and confirm they fail**

```bash
python3 -m unittest \
  tests.repository.test_public_docs.DocumentationArchitectureTests.test_six_user_guides_exist_per_language \
  tests.repository.test_public_docs.UserGuideFactTests.test_installation_index_is_chooser_only \
  tests.repository.test_installation_contract.InstallationContractTests.test_documented_link_installation_preserves_existing_targets
```

Expected: FAIL because `install-codex.md` / `install-local.md` are missing and `installation.md` still contains the installer block and marker.

- [ ] **Step 3: Write the four new files and shrink `installation.md`**

Korean `docs/users/ko/installation.md` (chooser only):

```markdown
# 설치

[English](../en/installation.md) · [호환성](compatibility.md) · [안전과 개인정보](safety-and-privacy.md) · [검증](verification.md)

설치할 스킬은 [`korean-writing-editor`](../../../skills/korean-writing-editor/README.md), [`image-workbench`](../../../skills/image-workbench/README.md), [`how-it-works`](../../../skills/how-it-works/README.md), [`pre-sdd-review`](../../../skills/pre-sdd-review/README.md)입니다. 라이선스는 Apache-2.0입니다. 어느 호스트가 되는지는 [호환성](compatibility.md)을 보세요.

| 스킬 | 방법 | 문서 |
| --- | --- | --- |
| `korean-writing-editor` | Codex `$skill-installer` | [Codex 설치](install-codex.md) |
| `image-workbench` | Codex `$skill-installer` | [Codex 설치](install-codex.md) |
| `pre-sdd-review` | Codex `$skill-installer` | [Codex 설치](install-codex.md). 기록기는 [evidence README](../../../skills/pre-sdd-review/evidence/README.md) |
| `how-it-works` | 저장소 로컬 링크 | [로컬 링크](install-local.md) |
```

English `docs/users/en/installation.md` uses `[한국어](../ko/installation.md)` and `README.en.md` product links, with the same four rows pointing at `install-codex.md` / `install-local.md` / `evidence/README.md`.

`install-codex.md` (both languages): take the current `installation.md` sections **기본 설치 (Codex)** / **Primary install (Codex)**, **선택적 제3자 설치기** / **Optional third-party installer**, **Codex 전용 Git 클론** / **Codex-only git clone**, and **갱신과 제거** / **Update and uninstall** except the How It Works `unlink` block. Keep the three `$skill-installer` commands, `OPTIONAL_NPX`, `GIT_CLONE`, target inspection, and the image-workbench / pre-sdd-review same-folder rule. Do not include the How It Works Python marker, `mkdir -p ~/.agents`, or `python3 scripts/verify.py`. Link `[로컬 링크](install-local.md)` once. Link all three Codex product READMEs. Nav line: language twin, `installation.md`, `compatibility.md`, `safety-and-privacy.md`, `verification.md`.

`install-local.md` (both languages): take the current How It Works local-link section plus the How It Works `unlink` block. Copy the Python fence from `skills/how-it-works/README.md` with `<!-- how-it-works-local-links -->` immediately before it. Include `HOW_IT_WORKS_MKDIR`, both here-document invocations, both unlink commands, `git clone https://github.com/beyondwin/skills.git`, and the `how-it-works` product README link. Do not include the three Codex `$skill-installer` commands. Nav line same as install-codex.

In `docs/users/ko/compatibility.md` replace `현재 2.0.0의 실제 실행은` with `현재 설치 파일의 실제 실행은`. In the English twin, remove the `2.0.0` current-run literal the same way. Leave the four support sentences untouched.

- [ ] **Step 4: Re-run Task 1 tests**

```bash
python3 -m unittest \
  tests.repository.test_public_docs.DocumentationArchitectureTests.test_six_user_guides_exist_per_language \
  tests.repository.test_public_docs.UserGuideFactTests \
  tests.repository.test_installation_contract \
  tests.repository.test_product_registry.RegistryDocumentationTests.test_korean_and_english_docs_share_registry_install_and_host_facts \
  tests.repository.test_changed_targets.TargetMappingTests.test_shared_public_docs_select_every_target
```

Expected: PASS. Product README heading tests are unchanged and should still pass.

- [ ] **Step 5: Commit**

```bash
git add docs/users tests/repository/test_public_docs.py tests/repository/test_installation_contract.py tests/repository/test_product_registry.py tests/repository/test_changed_targets.py
git commit -m "$(cat <<'EOF'
docs: split user install guides by method

Keep installation.md as the chooser table. Move Codex install and How It
Works local links into dedicated files, and point public-doc tests at
those owners.
EOF
)"
```

---

### Task 2: Unify product READMEs and PATCH versions

**Files:**

- Modify: `tests/repository/test_public_docs.py` (heading tuples, digest helpers, forbidden H2s, How It Works unlink owner, update-check owner)
- Modify: `tests/products/pre-sdd-review/test_contract.py` (headings, contract parser, README digests, `TARGET_VERSION`)
- Modify: `tests/products/how-it-works/test_contract.py` (version `2.0.1`)
- Modify: `tests/products/korean-writing-editor/test_package.py` (version `2.0.3`)
- Modify: `tests/repository/test_release_contract.py` (`EXPECTED` and how-it-works / pre-sdd identity tests)
- Modify: all eight `skills/*/README.md` and `README.en.md`
- Modify: `docs/maintainers/products/pre-sdd-review/contract.md` (add `### Contract` list)
- Modify: each product `release.toml`, `SKILL.md` frontmatter only, `CHANGELOG.md`
- Test: files above

**Interfaces:**

- Consumes: Task 1 `install-codex.md` / `install-local.md` paths; spec decision 4 heading lists; `README_CONTRACT` key tuples in `tests/products/pre-sdd-review/test_contract.py`
- Produces: four products with identical H2 order; Contract keys live in `contract.md`; PATCH versions as listed in the file map

- [ ] **Step 1: Write failing heading, forbidden-section, and contract-owner tests**

In `tests/repository/test_public_docs.py` delete `PRE_SDD_PRODUCT_HEADINGS`. Set:

```python
PRODUCT_README_HEADINGS = {
    "README.md": (
        "## 목적",
        "## 사용할 때와 사용하지 않을 때",
        "## 지원 호스트",
        "## 설치",
        "## 첫 호출",
        "## 예상 결과",
        "## 더 보기",
    ),
    "README.en.md": (
        "## Purpose",
        "## When to use and not use",
        "## Supported hosts",
        "## Install",
        "## First call",
        "## Expected result",
        "## See also",
    ),
}
FORBIDDEN_PRODUCT_README_H2 = {
    "README.md": (
        "## 안전과 개인정보",
        "## 검증",
        "## 업데이트와 제거",
        "## 변경 이력과 관리자 문서",
        "## 이 스킬이 해결하는 문제",
        "## 사용해야 할 때와 사용하지 말아야 할 때",
        "## 결과와 기본 흐름",
        "## 운영과 한계",
        "## 호환성과 검증 수준",
    ),
    "README.en.md": (
        "## Safety and privacy",
        "## Verification",
        "## Update and remove",
        "## Changelog and maintainer docs",
        "## Operations and limits",
        "## Supported hosts and verification",
    ),
}
```

`test_product_readmes_follow_common_information_order` must use `PRODUCT_README_HEADINGS` for every product, including `pre-sdd-review`. Add:

```python
def test_product_readmes_omit_shared_safety_verify_and_update_headings(self) -> None:
    for product in REGISTRY.products:
        for filename, forbidden in FORBIDDEN_PRODUCT_README_H2.items():
            text = _read(ROOT / product.skill_path / filename)
            for heading in forbidden:
                self.assertNotIn(heading, text, f"{product.name}/{filename} {heading}")
            self.assertNotIn("### Contract", text)
```

Delete `PRE_SDD_SHARED_SECTION_DIGESTS` and every test that requires a product README safety/verification section to match the user-guide digest (`pre_sdd_shared_contract_errors` on product READMEs). Keep `pre_sdd_shared_contract_errors` on `docs/users/*/safety-and-privacy.md` and `verification.md` only.

In `test_product_readmes_include_installer_support_and_maintainer_link` remove the `"inspect" in text.lower() or "확인"` assertion against product READMEs. Keep installer command, support sentence, CHANGELOG, and the four GitHub maintainer URLs. Assert `"inspect"` / `"확인"` on `install-codex.md` (already done in Task 1).

In `test_how_it_works_readmes_include_supported_host_install_call_and_result` keep mkdir, Python block, invocations, `$how-it-works`, `/how-it-works`, expected English phrases, and refuse-existing-target sentences. Move `HOW_IT_WORKS_UNLINK_AGENTS` / `HOW_IT_WORKS_UNLINK_CLAUDE` assertions to `install-local.md` only.

In `tests/products/pre-sdd-review/test_contract.py`:

- Set `TARGET_VERSION = "3.0.1"`.
- Replace `KOREAN_README_HEADINGS` / `ENGLISH_README_HEADINGS` with the unified seven H2s (한국어 uses `## 목적`, `## 사용할 때와 사용하지 않을 때`, `## 예상 결과`, `## 더 보기`).
- Delete `README_CANONICAL_SECTION_DIGESTS` and `README_CANONICAL_DOCUMENT_DIGESTS`.
- Change `parse_readme_contract` to parse `docs/maintainers/products/pre-sdd-review/contract.md` looking for `### Contract` (same `- \`key\`: \`values\`` grammar as today). Rename call sites accordingly.
- Rewrite `readme_contract_errors` so it (1) checks H2 order against the new tuples, (2) checks `pre_sdd_invocations` on `## 첫 호출` / `## First call` still equals `(DEFAULT_FIRST_CALL,)`, (3) does not SHA-256 the whole README, (4) does not require `### Contract` in the README.
- Keep `KOREAN_FACTS` / `ENGLISH_FACTS` assertions against the README bodies.
- Change `test_release_sources_target_v3_0_0` to accept `## 3.0.1 - 2026-09-11` in CHANGELOG (keep the `3.0.0 - 2026-09-08` historical heading in the file). Rename the test to `test_release_sources_target_current_patch`.

After `contract.md` gains `### Contract`, `maintainer_contract_errors` canonical digests will fail. Do not invent hashes. After Step 3, recompute with:

```bash
python3 - <<'PY'
from pathlib import Path
import tests.products.pre_sdd_review.test_contract as t
text = Path("docs/maintainers/products/pre-sdd-review/contract.md").read_text(encoding="utf-8")
print("doc", t.canonical_digest(text))
for heading, _ in t.MAINTAINER_CANONICAL_SUBSECTION_DIGESTS:
    print(heading, t.canonical_digest(t.subsection(text, heading)))
PY
```

Paste the new document digest into `MAINTAINER_CANONICAL_DIGEST`. Subsection digests stay if those headings are unchanged; only `### Contract` is new and does not need to join `MAINTAINER_CANONICAL_SUBSECTION_DIGESTS` unless a test iterates unknown headings.

In `tests/repository/test_release_contract.py` set:

```python
EXPECTED = {
    "korean-writing-editor": "2.0.3",
    "image-workbench": "2.0.3",
    "how-it-works": "2.0.1",
    "pre-sdd-review": "3.0.1",
}
```

Update `test_how_it_works_current_archive_identity` to `2.0.1` / `how-it-works-v2.0.1.zip`. Update `test_pre_sdd_review_current_archive_identity` to `3.0.1`. In `test_one_product_version_can_change_without_changing_neighbors` replace `version = "2.0.0"` with the current how-it-works version `2.0.1` and the mismatch string `2.0.2 != SKILL.md version 2.0.1`.

In `tests/products/how-it-works/test_contract.py` `test_v2_release_and_repeatable_install_contract` and `test_frontmatter_uses_portable_intersection`, expect `"2.0.1"`. Keep the `ln -s` ban and `](../../docs/` ban.

In `tests/products/korean-writing-editor/test_package.py` replace `2.0.2` with `2.0.3` in `test_release_target_and_skill_version_are_202` (rename to `..._203`) and `test_payload_declares_canonical_name_license_and_version`. If `test_repository.py` copies a live `2.0.2` string from korean SKILL.md as a mutation fixture, update that fixture to the new current version so the mismatch message still matches the file it mutated.

- [ ] **Step 2: Run heading tests and confirm they fail**

```bash
python3 -m unittest \
  tests.repository.test_public_docs.ProductReadmeOwnershipTests.test_product_readmes_follow_common_information_order \
  tests.repository.test_public_docs.ProductReadmeOwnershipTests.test_product_readmes_omit_shared_safety_verify_and_update_headings
```

Expected: FAIL on `pre-sdd-review` missing `## 목적` / `## 더 보기` and on remaining `## 안전과 개인정보` headings.

- [ ] **Step 3: Rewrite READMEs, move Contract, bump PATCH**

Shared `## 더 보기` / `## See also` shape (Korean example; English labels `Changelog`, `Contract`, `Testing`, `Compatibility`, `Release`):

```markdown
## 더 보기

- [안전과 개인정보](https://github.com/beyondwin/skills/blob/main/docs/users/ko/safety-and-privacy.md)
- [검증](https://github.com/beyondwin/skills/blob/main/docs/users/ko/verification.md)
- [CHANGELOG](CHANGELOG.md)
- [계약](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/<name>/contract.md)
- [테스트](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/<name>/testing.md)
- [호환성](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/<name>/compatibility.md)
- [릴리스](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/<name>/release.md)
```

English READMEs use `docs/users/en/...`. Pre-SDD adds `- [evidence README](evidence/README.md)` (payload-relative).

Install sections:

- Codex three: keep the `$skill-installer` command. Change the “rest of install” GitHub URL from `.../installation.md` to `.../docs/users/<lang>/install-codex.md`. Delete 업데이트와 제거 / Update and remove sections.
- How It Works: keep clone, mkdir, the marked Python block, both here-document invocations, and the `$skill-installer` GitHub path. Change the “rest of install” URL to `.../install-local.md`. Delete the unlink block and the 업데이트와 제거 section.

Delete H2s `안전과 개인정보`, `검증`, `업데이트와 제거`, `변경 이력과 관리자 문서` and English twins from all eight files. Keep one-sentence product-specific safety only if it already sits inside 목적 / 예상 결과; do not recreate a safety H2.

Pre-SDD Korean README: rename `## 이 스킬이 해결하는 문제` → `## 목적`, `## 사용해야 할 때와 사용하지 말아야 할 때` → `## 사용할 때와 사용하지 않을 때`, `## 결과와 기본 흐름` → `## 예상 결과`. Add `## 지원 호스트` containing `pre-sdd-review: Codex supported; other hosts not_measured.` and a compatibility GitHub link. Delete `## 운영과 한계` and `## 호환성과 검증 수준` (fold a one-line evidence pointer into 더 보기). Delete `### Contract`. Keep `READY` / `REVISE` / `BLOCKED` and `DEFAULT_FIRST_CALL` in 첫 호출 / 예상 결과. English: add `## Supported hosts`; keep `## Expected result` as the renamed default-flow section.

Append this block to `docs/maintainers/products/pre-sdd-review/contract.md` (same keys/values as the current README list):

```markdown
### Contract

- `primary-input`: `plan-primary`, `spec-resolves-design`
- `plan-cardinality`: `one-plan-per-invocation`, `no-aggregate-ready`
- `editable-surfaces`: `resolved-design-specification`, `resolved-implementation-plan`
- `review-only`: `no-mutation`
- `repair-flow`: `review-repair-bounded-impact-re-review`
- `repair-impact`: `structural-trigger-only`, `direct-consumers`
- `repair-passes`: `at-most-two`
- `verdicts`: `READY`, `REVISE`, `BLOCKED`
- `second-reviewer`: `conditional-only`
- `risk-triggers`: `framework-runtime-removal`, `schema-data-deletion`, `auth-security-boundary`, `data-boundary-change`, `external-side-effects`
- `freshness`: `fingerprints`, `content-change-invalidates`
- `required-base`: `pre-dispatch-ancestor-check`
- `handoff`: `unresolved-packet`
- `sdd`: `outer-request-implementation-only`
- `evidence`: `optional`, `non-blocking`, `controller-local-run-id`
```

Then run the digest snippet from Step 1 and update `MAINTAINER_CANONICAL_DIGEST`. If `TESTING_CANONICAL_DIGEST` is unchanged this task, leave it.

PATCH each product in the same commit as its README:

- `release.toml` `version`
- `SKILL.md` `metadata.version` and `updated_at: "2026-09-11"` only
- CHANGELOG: promote Unreleased into `## <new> - 2026-09-11` with `### Changed` “Standalone README now uses the shared heading set and points install procedures at the split user guides.” plus `### Notes` “No GitHub tag or GitHub Release is created.” Open a fresh `## Unreleased`. Keep prior version headings.

Do not edit SKILL.md instruction sections.

- [ ] **Step 4: Run product and public README tests**

```bash
python3 -m unittest \
  tests.repository.test_public_docs.ProductReadmeOwnershipTests \
  tests.repository.test_release_contract.ProductReleaseTests \
  tests.products.how_it_works.test_contract.HowItWorksPayloadTests \
  tests.products.korean_writing_editor.test_package \
  tests.products.pre_sdd_review.test_contract
```

Expected: PASS. If pre-sdd maintainer digest mismatches, paste the Step 1 snippet output and re-run. If image-workbench `test_payload_docs.py` fails, the README GitHub URL path does not exist yet (install-codex/local must already be on disk from Task 1).

- [ ] **Step 5: Commit**

```bash
git add skills tests/repository/test_public_docs.py tests/repository/test_release_contract.py tests/products docs/maintainers/products/pre-sdd-review/contract.md
git commit -m "$(cat <<'EOF'
docs: unify product README headings and patch versions

Move shared install, safety, and verification prose out of product
READMEs. Own the Pre-SDD Contract list in maintainer contract.md.
EOF
)"
```

---

### Task 3: Root README and docs index

**Files:**

- Modify: `README.md`
- Modify: `README.en.md`
- Modify: `docs/README.md`
- Modify: `tests/repository/test_public_docs.py` (`test_root_readmes_link_to_shared_guides_and_community_files`, `test_no_user_document_is_orphaned_from_the_root_catalog`)
- Test: `tests/repository/test_public_docs.py`

**Interfaces:**

- Consumes: Task 1 relative paths `docs/users/<lang>/install-codex.md` and `install-local.md`
- Produces: root still one screen; every `USER_GUIDES` path reachable by relative links from `README.md` / `README.en.md`

- [ ] **Step 1: Extend the root-link test**

Keep existing community hrefs. Add assertions that Korean root or `docs/README.md` (relative walk) can reach the new files. The orphan walker only follows relative hrefs, so `docs/README.md` must contain `users/ko/install-codex.md`, `users/ko/install-local.md`, `users/en/install-codex.md`, and `users/en/install-local.md`. Root README may keep linking only `docs/users/ko/installation.md` if the chooser links onward.

```python
def test_docs_index_links_split_install_guides(self) -> None:
    text = _read(ROOT / "docs" / "README.md")
    for href in (
        "users/ko/install-codex.md",
        "users/ko/install-local.md",
        "users/en/install-codex.md",
        "users/en/install-local.md",
        "users/ko/installation.md",
        "users/en/installation.md",
    ):
        self.assertIn(href, text)
```

- [ ] **Step 2: Run it and confirm fail**

```bash
python3 -m unittest tests.repository.test_public_docs.DocumentationArchitectureTests.test_docs_index_links_split_install_guides tests.repository.test_public_docs.RegistryDrivenPublicDocTests.test_no_user_document_is_orphaned_from_the_root_catalog
```

Expected: FAIL on missing docs index hrefs (orphan test may already pass via `installation.md` relative links from Task 1).

- [ ] **Step 3: Update indexes**

`docs/README.md` install section lists chooser plus Codex and local files for both languages. Do not add maintainer protocol into this page.

Root `README.md` / `README.en.md`: keep product table, three Codex installer lines, `python3 scripts/verify.py`, community links. Point How It Works at `docs/users/ko/install-local.md` (English twin uses `en`). Do not restore per-product do-not-use lists. Keep `test_readmes_follow_catalog_section_order` markers (`beyondwin-skills`, `actions/workflows/verify.yml`, first registry name, `$skill-installer`, `python3 scripts/verify.py`, `CONTRIBUTING.md`).

- [ ] **Step 4: Re-run**

```bash
python3 -m unittest tests.repository.test_public_docs.RootCatalogTests tests.repository.test_public_docs.DocumentationArchitectureTests.test_docs_index_routes_install_use_maintain_and_history tests.repository.test_public_docs.DocumentationArchitectureTests.test_docs_index_links_split_install_guides tests.repository.test_public_docs.RegistryDrivenPublicDocTests.test_no_user_document_is_orphaned_from_the_root_catalog
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add README.md README.en.md docs/README.md tests/repository/test_public_docs.py
git commit -m "docs: route root and docs index through split install guides"
```

---

### Task 4: Maintainer docs and verification fixture owners

**Files:**

- Modify: `docs/maintainers/repository/architecture.md`
- Modify: `docs/maintainers/products/korean-writing-editor/testing.md`
- Modify: `docs/maintainers/products/image-workbench/testing.md`
- Modify: `docs/maintainers/products/how-it-works/testing.md`
- Modify: `docs/maintainers/products/pre-sdd-review/testing.md`
- Modify: `docs/maintainers/products/*/release.md` (four files)
- Modify: `docs/users/ko/verification.md`
- Modify: `docs/users/en/verification.md`
- Modify: `tests/products/pre-sdd-review/test_contract.py` (`TESTING_CANONICAL_DIGEST` after testing.md edits)
- Test: `tests.repository.test_public_docs.MaintainerStructureTests`, `UserGuideFactTests.test_verification_owns_offline_live_evidence_and_profiles`, `test_shared_guides_name_current_evidence_dimensions`

**Interfaces:**

- Consumes: fixture path bullets currently in `docs/users/*/verification.md` lines listing `tests/products/<name>/`
- Produces: those paths in each `testing.md`; `verification.md` still contains `OFFLINE_EVIDENCE`, `LIVE_EVIDENCE`, profile flags, and the evidence-dimension phrases listed in `test_shared_guides_name_current_evidence_dimensions`

- [ ] **Step 1: Add owner assertions**

```python
def test_product_testing_docs_own_fixture_paths(self) -> None:
    expected = {
        "korean-writing-editor": "tests/products/korean-writing-editor/offline/",
        "image-workbench": "tests/products/image-workbench/",
        "how-it-works": "tests/products/how-it-works/",
        "pre-sdd-review": "tests/products/pre-sdd-review/",
    }
    for name, path in expected.items():
        text = _read(ROOT / "docs" / "maintainers" / "products" / name / "testing.md")
        self.assertIn(path, text, name)

def test_verification_guide_does_not_list_product_fixture_directories(self) -> None:
    for language in ("ko", "en"):
        text = _read(ROOT / "docs" / "users" / language / "verification.md")
        self.assertNotIn("tests/products/korean-writing-editor/offline/", text)
        self.assertNotIn("`tests/products/image-workbench/`", text)
```

Keep `test_verification_owns_offline_live_evidence_and_profiles` as-is (`OFFLINE_EVIDENCE`, `LIVE_EVIDENCE`, `python3 scripts/verify.py`, both profiles).

- [ ] **Step 2: Run and confirm fail**

```bash
python3 -m unittest tests.repository.test_public_docs.MaintainerStructureTests.test_product_testing_docs_own_fixture_paths tests.repository.test_public_docs.UserGuideFactTests.test_verification_guide_does_not_list_product_fixture_directories
```

Expected: FAIL on how-it-works/image paths missing from some `testing.md` files and/or still present in `verification.md`.

- [ ] **Step 3: Move paths and shorten maintainer pages**

Add the expected fixture directory string to each product `testing.md` if missing (`how-it-works` must contain `tests/products/how-it-works/`).

In both `verification.md` files delete the bullet list that names `tests/products/korean-writing-editor/offline/`, `tests/products/image-workbench/`, `tests/products/how-it-works/`, `tests/products/pre-sdd-review/`. Keep counts and phrases the evidence-dimension test locks (`33`, `normative=10`, `runner 18`, `31`, `17`, `14 cases / 17 repeats`, `119 / 3 / 122 / 38 / 160`, `hard`, `failed`, `partially_verified`, `fence/hop`, `loading`, `syntax`, `meaning`, `schema 2`, `schema 3`, `historical-unbound`, `checkout`, `LF`, and the canonical evidence JSON line). Point readers to maintainer `testing.md` in one sentence.

`architecture.md`: keep the install-vs-evidence table and `python3 scripts/verify.py`. Delete repeated user-install command blocks if present. Keep Korean H1 and first explanatory paragraph Korean.

Each product `release.md`: delete the duplicated four-command `check` / `build` / `verify-download` bash block. Replace with a link to `docs/maintainers/repository/release.md` and keep product-specific SemVer examples and tag prefix. Remove current-version literals such as how-it-works `` `2.0.0` `` and image-workbench `` `2.0.2` ``; say `release.toml` instead. Keep the exact English sentence `no tag or GitHub Release is created by these commands.` where tests require it (`RELEASE_NO_PUBLICATION`).

If `test_how_it_works_protocol_maps_contract_testing_compatibility_and_release` requires the four commands inside the product `release.md`, move that assertion to `repository/release.md` (already has them) or keep one line `python3 scripts/release.py check --product how-it-works` as a pointer, not the full four-command script.

Recompute `TESTING_CANONICAL_DIGEST` (and compatibility/release digests if those files changed) with the same `canonical_digest` helper after edits.

- [ ] **Step 4: Re-run maintainer and verification tests**

```bash
python3 -m unittest \
  tests.repository.test_public_docs.MaintainerStructureTests \
  tests.repository.test_public_docs.UserGuideFactTests.test_verification_owns_offline_live_evidence_and_profiles \
  tests.repository.test_public_docs.UserGuideFactTests.test_shared_guides_name_current_evidence_dimensions \
  tests.repository.test_public_docs.UserGuideFactTests.test_verification_guide_does_not_list_product_fixture_directories \
  tests.products.pre_sdd_review.test_contract
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add docs/maintainers docs/users/ko/verification.md docs/users/en/verification.md tests
git commit -m "docs: move fixture paths to maintainer testing guides"
```

---

### Task 5: Full provider-free verification

**Files:**

- Test: entire `python3 scripts/verify.py` (no source edits unless a leftover assertion fails)
- Modify: `docs/history/README.md` (add this plan to the in-progress list if not already listed)

**Interfaces:**

- Consumes: Tasks 1–4
- Produces: spec verification checklist all true

- [ ] **Step 1: Run the orchestrator**

```bash
python3 scripts/verify.py
git diff --check
```

Expected: exit 0. If a test still names `installation.md` as the How It Works Python owner, `PRE_SDD_PRODUCT_HEADINGS`, `2.0.2` as current korean/image version, `2.0.0` as current how-it-works version, or `3.0.0` as current pre-sdd version, fix that assertion in this task — do not revert the docs.

- [ ] **Step 2: Manual spec checklist**

Confirm by search, not by memory:

1. Four products’ H2 sets match spec decision 4. No `### Contract` in product READMEs.
2. `docs/users/ko` and `en` each have exactly the six markdown files. `installation.md`, `safety-and-privacy.md`, `verification.md` still exist.
3. `installation.md` has no `<!-- how-it-works-local-links -->`. The marker exists once in each of the four spec decision 5 files, and `installation_block()` of those four strings is equal.
4. Product READMEs have no `## 안전과 개인정보` / `## Safety and privacy` / `## 검증` / `## Verification`.
5. `products.toml` and maintainer four-file directories unchanged.
6. `git diff origin/main -- catalog skills/*/SKILL.md` shows only SKILL.md frontmatter version/`updated_at` for the four products, no catalog files, no SKILL.md body rewrites.
7. No new tag (`git tag --contains HEAD` should not add `*-v2.0.3` etc. in this work).

- [ ] **Step 3: Commit leftover test-only fixes if Step 1 required them**

```bash
git add tests docs/history/README.md
git commit -m "test: align remaining public-doc assertions with split guides"
```

Skip this commit if the working tree is clean.

---

## Spec coverage

| Spec item | Task |
| --- | --- |
| Reader paths / chooser table / split install files | 1, 3 |
| Keep `installation.md` / safety / verification names | 1 |
| Fact owners, no duplicated safety/verify essays in READMEs | 2 |
| Unified README H2s including pre-sdd | 2 |
| How It Works Python block four-file identity | 1, 2 |
| Contract list in `contract.md` | 2 |
| Maintainer paths unchanged; architecture shorten; testing paths; release dedup | 4 |
| Tests lock facts not section SHA on product READMEs | 1, 2 |
| GitHub blob URLs; no `](../../docs/` in how-it-works | 2 |
| PATCH versions, no tags | 2, 5 |
| `python3 scripts/verify.py` | 5 |
| SKILL.md body / catalog / no redirect stubs / no `ln -s` | all tasks, verified in 5 |
