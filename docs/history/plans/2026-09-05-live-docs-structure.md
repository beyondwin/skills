# Live Docs Structure and Voice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite live docs so each fact has one owner, the prose is everyday language, dead recorder names are gone, finished history is deleted after still-binding reasons are absorbed, and `.gitignore` gains only a real recurring artifact if one is missing.

**Architecture:** Keep the audience tree and the two front doors. Rewrite bodies in place. Move digest and fact pins in the same commit as the page they pin. Do not add a docs framework, a new docs directory, or a product-shaped tree.

**Tech Stack:** Markdown, existing `unittest` digest pins (`tests/repository/test_public_docs.py`, `tests/products/pre-sdd-review/test_contract.py`), `python3 scripts/verify.py`.

**Spec:** `docs/history/specs/2026-09-05-live-docs-structure-design.md`

## Global Constraints

- Physical layout stays `docs/users/`, `docs/maintainers/`, `docs/history/`, `skills/<name>/README.md`. No `docs/maintainers/docs.md`, no MkDocs, no `docs/superpowers/`.
- Product README heading sets stay exactly as pinned in `PRE_SDD_PRODUCT_HEADINGS` and `PRODUCT_README_HEADINGS`. Rewrite bodies, not section names.
- Korean is the original for maintainer docs and Korean user/product pages. English siblings carry the same facts. Commands, paths, identifiers, enums, and JSON keys stay English. Machine-readable lists that tests pin stay in their current English form.
- Voice: short sentences, everyday words, one idea per sentence. Do not pack an English clause into a Korean sentence unless it is a command, path, or token.
- `SKILL.md` and `references/reviewer-protocol.md` do not change. `products.toml` host support and verify stages do not change. Evidence recorder behaviour and schema 2 do not change.
- Forbidden in live docs (active markdown outside `docs/history/` and outside dated CHANGELOG entries): `install.py`, `--bin-dir`, `record-outcome`, `finish-review`, `~/.local/bin/pre-sdd-review-evidence`, and any “remove the old launcher” procedure. The verify stage name `pre-sdd-review-evidence` stays in verification docs. `schema 2` stays as the current record schema.
- Pinned installer/support strings stay: `$skill-installer` URLs, How It Works `ln -s` / `unlink` commands, `SUPPORT_BY_PRODUCT` one-liners, maintainer `contract.md`/`testing.md`/`compatibility.md`/`release.md` links, and a short confirm-before-update sentence (`확인` / `inspect`).
- A rewritten pinned page and its digest/fact pins land in the same commit.
- Do not bump product versions unless `python3 scripts/release.py check --product <name>` requires it. Add a CHANGELOG `Unreleased` note when that product’s installed README body changes. No tag, push, GitHub Release, or `catalog/` mutation.
- Do not inspect, migrate, or delete `~/.local/bin/pre-sdd-review-evidence` or schema 1 files under `~/.pre-sdd-review/`.
- Run tests with `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s <dir> -p '<pattern>'` from the repository root.
- Keep this spec and this plan. Delete the finished history files listed in Task 7, not these two.

---

## File Structure

| Path | Responsibility |
| --- | --- |
| `docs/maintainers/README.md` | Job index plus the docs-maintenance rules (front doors, one owner, language, pins, history) |
| `docs/history/README.md` | In-progress-only, non-authoritative |
| `docs/users/{ko,en}/*.md` | Shared install / compatibility / safety / verification |
| `docs/maintainers/products/<name>/{contract,testing,compatibility,release}.md` | Product protocol; pre-sdd-review gains `## 함께 고칠 파일` and `## 하지 않는 것` |
| `docs/maintainers/repository/*.md` | Repo protocol; history row matches in-progress-only |
| `docs/README.md`, `README.md`, `README.en.md`, `catalog/README.md` | Route; do not own procedures |
| `skills/<name>/README.md`, `README.en.md` | Skill front door |
| `skills/pre-sdd-review/evidence/README.md` | Current recorder only |
| `skills/<name>/CHANGELOG.md` | `Unreleased` note if that README body changes; dated entries untouched |
| `tests/repository/test_public_docs.py` | Dead-name assertions, shared-section digests, history README facts |
| `tests/products/pre-sdd-review/test_contract.py` | README/maintainer digests; hard-forbid dead recorder names |
| `.gitignore` | Add a pattern only if inspection finds a recurring uncovered artifact |
| `docs/history/specs/` (old), `plans/` (old), `field-notes/` | Delete after absorb |

Digest helper (run from the repository root after rewriting a pinned page; paste the printed values):

```bash
python3 - <<'EOF'
import hashlib, re, sys
from pathlib import Path
sys.path.insert(0, "tests/products/pre-sdd-review")
import test_contract as t

def shared_section(path: Path, heading: str) -> str:
    text = path.read_text(encoding="utf-8")
    owned = re.compile(rf"^{re.escape(heading)}\s*$.*?(?=^##\s|\Z)", re.M | re.S).findall(text)
    assert len(owned) == 1, (path, heading)
    return owned[0]

print("README_CANONICAL_DOCUMENT_DIGESTS ko", t.whole_document_digest((t.SKILL / "README.md").read_text(encoding="utf-8")))
print("README_CANONICAL_DOCUMENT_DIGESTS en", t.whole_document_digest((t.SKILL / "README.en.md").read_text(encoding="utf-8")))
text_ko = (t.SKILL / "README.md").read_text(encoding="utf-8")
text_en = (t.SKILL / "README.en.md").read_text(encoding="utf-8")
for heading, _ in t.README_CANONICAL_SECTION_DIGESTS["ko"]:
    print("README_CANONICAL_SECTION_DIGESTS ko", heading, t.canonical_digest(t.markdown_section(text_ko, heading)))
for heading, _ in t.README_CANONICAL_SECTION_DIGESTS["en"]:
    print("README_CANONICAL_SECTION_DIGESTS en", heading, t.canonical_digest(t.markdown_section(text_en, heading)))
contract = (t.MAINTAINERS / "contract.md").read_text(encoding="utf-8")
print("MAINTAINER_CANONICAL_DIGEST", t.canonical_digest(contract))
for heading, _ in t.MAINTAINER_CANONICAL_SUBSECTION_DIGESTS:
    print("MAINTAINER_CANONICAL_SUBSECTION_DIGESTS", heading, t.canonical_digest(t.subsection(contract, heading)))
for name in ("testing", "compatibility", "release"):
    print(f"{name.upper()}_CANONICAL_DIGEST", t.whole_document_digest((t.MAINTAINERS / f"{name}.md").read_text(encoding="utf-8")))
sections = {
    ("ko", "safety"): ("docs/users/ko/safety-and-privacy.md", "## SDD 전 문서 검토"),
    ("en", "safety"): ("docs/users/en/safety-and-privacy.md", "## Pre-SDD document review"),
    ("ko", "verification"): ("docs/users/ko/verification.md", "## 오프라인 픽스처"),
    ("en", "verification"): ("docs/users/en/verification.md", "## Offline fixtures"),
}
for key, (path, heading) in sections.items():
    print("PRE_SDD_SHARED_SECTION_DIGESTS", key, hashlib.sha256(shared_section(Path(path), heading).encode("utf-8")).hexdigest())
EOF
```

Rewrite checklist (every docs task): keep pinned headings and exact test strings; short everyday sentences; English only for commands/paths/tokens; no forbidden dead names; link to the owner page instead of restating its procedure; recompute any digest this page owns in the same commit.

---

### Task 1: Dead-name tests, maintainer maintenance rules, history README, gitignore inspect

**Files:**
- Modify: `tests/repository/test_public_docs.py`
- Modify: `docs/maintainers/README.md`
- Modify: `docs/history/README.md`
- Modify: `docs/users/ko/installation.md`, `docs/users/en/installation.md` (delete the launcher-removal paragraph only)
- Modify: `.gitignore` only if inspection finds a recurring uncovered artifact
- Local only (not committed): delete leftover `skills/pre-sdd-review/evidence/pre_sdd_review_evidence/` and `__pycache__` under `evidence/`

**Interfaces:**
- Produces: `DEAD_RECORDER_STRINGS` in `test_public_docs.py`; live docs (except verification stage name, dated CHANGELOG, and `docs/history/`) must not contain them.
- Produces: maintainer index owns the docs-maintenance rules from spec Decisions 1, 2, 3, 5, 6.
- Produces: history README still satisfies `test_history_is_visibly_non_authoritative`.

- [ ] **Step 1: Write the failing dead-name test**

In `tests/repository/test_public_docs.py`, add next to `HISTORY_PREFIXES`:

```python
DEAD_RECORDER_STRINGS = (
    "install.py",
    "--bin-dir",
    "record-outcome",
    "finish-review",
    "~/.local/bin/pre-sdd-review-evidence",
)
DEAD_LAUNCHER_PHRASES = (
    "pre-sdd-review-evidence launcher",
    "`pre-sdd-review-evidence` launcher",
)
```

Add to `DocumentationArchitectureTests`:

```python
    def test_live_docs_omit_removed_evidence_installer_names(self) -> None:
        skip = {
            (ROOT / "catalog" / "CHANGELOG.md").resolve(),
            (ROOT / "skills/pre-sdd-review/CHANGELOG.md").resolve(),
        }
        for document in PUBLIC_DOC_PATHS:
            if document.resolve() in skip:
                continue
            relative = document.relative_to(ROOT).as_posix()
            if relative.startswith("docs/history/"):
                continue
            text = _read(document)
            for fragment in DEAD_RECORDER_STRINGS:
                self.assertNotIn(fragment, text, f"{relative} contains {fragment!r}")
            for phrase in DEAD_LAUNCHER_PHRASES:
                self.assertNotIn(phrase, text, f"{relative} contains {phrase!r}")

    def test_maintainer_index_owns_docs_maintenance_rules(self) -> None:
        text = _read(MAINTAINER_INDEX)
        normalized = re.sub(r"\s+", " ", text)
        for fact in (
            "제품 README",
            "docs/users/",
            "docs/maintainers/",
            "사실 하나",
            "한국어가 원본",
            "digest",
            "함께 고칠 파일",
            "진행 중",
        ):
            self.assertIn(fact, normalized)
        self.assertIn("docs/history/", text)
```

In `test_pre_sdd_review_shared_guides_preserve_scope_and_evidence_limits`, after the installation `assertNotIn("install.py")` lines, add:

```python
            self.assertNotIn("pre-sdd-review-evidence launcher", text)
            self.assertNotIn("~/.local/bin/pre-sdd-review-evidence", text)
```

Keep the verification assertions that require the stage name `pre-sdd-review-evidence`.

- [ ] **Step 2: Run to verify failure**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/repository -p 'test_public_docs.py'`

Expected: `test_live_docs_omit_removed_evidence_installer_names` fails on `docs/users/ko/installation.md` and `docs/users/en/installation.md` (launcher-removal paragraph). `test_maintainer_index_owns_docs_maintenance_rules` fails (missing facts).

- [ ] **Step 3: Rewrite `docs/history/README.md`**

Replace the file with:

```markdown
# 기록 / History

이 디렉터리는 **진행 중인** 설계와 구현 계획만 둡니다. 옛 이름과 경로가 남아
있을 수 있으며, 현재 계약을 정의하지 않습니다.

Files here are in-progress specs and plans. They may contain old names and
paths, and they do not define the current contract. They are point-in-time
records.

끝난 계획, 쓰이지 않는 현장 관찰, 이미 산 문서가 대신하는 스펙은 두지 않습니다.
지금 쓰는 안내와 계약은 [`docs/README.md`](../README.md),
[`docs/users/`](../users/), [`docs/maintainers/`](../maintainers/), 각 제품
README를 보세요.
```

Keep the facts `test_history_is_visibly_non_authoritative` pins: `현재 계약을 정의하지`, Latin letters, `point-in-time` / `point in time`, and `old` with `name` or `path`.

- [ ] **Step 4: Add the maintenance section to `docs/maintainers/README.md`**

Keep the existing job-index tables. After the opening language sentence, add a `## 문서 유지` section before `## 할 일`:

```markdown
## 문서 유지

문은 두 개입니다. 제품 README는 그 스킬을 고르고 호출할 때, `docs/users/`와
이 인덱스는 설치·검증·변경·릴리스를 할 때 봅니다. 파일은 청중 트리에만 둡니다.

사실 하나는 한 문서가 소유합니다. 다른 페이지는 링크로 보냅니다. 공개 설치는
`docs/users/`, 제품 동작은 해당 `contract.md`와 `SKILL.md`, 기록기 명령은
`skills/pre-sdd-review/evidence/README.md`가 소유합니다.

관리자 문서는 한국어가 원본입니다. 명령, 파일 경로, 계약 식별자는 영어로 둡니다.
문장은 짧게, 일상어로 씁니다.

산 문서를 바꾸면 같은 변경에서 digest 핀과 사실 단언을 맞춥니다. 제품 동작
변경은 해당 계약의 `함께 고칠 파일`을 따릅니다.

`docs/history/`는 진행 중인 설계·계획만 둡니다. 현재 계약을 정의하지 않습니다.
```

Change the job-index row `과거 결정 확인` to `진행 중인 설계·계획` pointing at `[기록](../history/)`.

Add `함께 고칠 파일` to the pre-sdd-review contract bullet so the index matches the other products:

```markdown
- [계약](products/pre-sdd-review/contract.md) — 권위 순서, 판정, 함께 고칠 파일
```

- [ ] **Step 5: Delete the launcher-removal paragraphs so the new test can pass**

In `docs/users/ko/installation.md`, delete the sentence that begins
`이전 버전이 설치한 \`pre-sdd-review-evidence\` launcher` (keep the rest of
`## Pre-SDD Review evidence 기록기`).

In `docs/users/en/installation.md`, delete the sentence that begins
`The \`pre-sdd-review-evidence\` launcher installed by earlier versions`
(keep the rest of `## Pre-SDD Review evidence recorder`).

Recompute `PRE_SDD_SHARED_SECTION_DIGESTS` only if those deletions sit
inside a pinned shared section. They do not: they sit in installation.md,
which has no shared-section digest. Do not change `PRE_SDD_SHARED_SECTION_DIGESTS`
in this task.

- [ ] **Step 6: Inspect `.gitignore` and leftover local trees**

```bash
git status --ignored --short
ls -la skills/pre-sdd-review/evidence
```

Expected: bytecode and `.superpowers/` already ignored. If
`skills/pre-sdd-review/evidence/pre_sdd_review_evidence/` exists, delete it
locally (`rm -rf skills/pre-sdd-review/evidence/pre_sdd_review_evidence
skills/pre-sdd-review/evidence/__pycache__`). Do not add that package name
to `.gitignore`. Add a pattern only when a recurring local artifact is not
already covered. If nothing is missing, do not touch `.gitignore`.

- [ ] **Step 7: Run the repository public-docs tests**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/repository -p 'test_public_docs.py'`

Expected: `OK`, including the new dead-name test, history README facts, and
maintainer maintenance facts.

- [ ] **Step 8: Commit**

```bash
git add docs/maintainers/README.md docs/history/README.md docs/users/ko/installation.md docs/users/en/installation.md tests/repository/test_public_docs.py
# git add .gitignore   # only if Step 6 added a pattern
git commit -m "docs(maintainers): record how live docs stay consistent"
```

---

### Task 2: Shared user guides (ko + en)

**Files:**
- Modify: `docs/users/ko/installation.md`, `docs/users/en/installation.md`
- Modify: `docs/users/ko/compatibility.md`, `docs/users/en/compatibility.md`
- Modify: `docs/users/ko/safety-and-privacy.md`, `docs/users/en/safety-and-privacy.md`
- Modify: `docs/users/ko/verification.md`, `docs/users/en/verification.md`
- Modify: `tests/repository/test_public_docs.py` (`PRE_SDD_SHARED_SECTION_DIGESTS`)

**Interfaces:**
- Consumes: `DEAD_RECORDER_STRINGS` from Task 1.
- Produces: user guides that pass `UserGuideFactTests`, pre-sdd shared-section digest pins, and the dead-name test.

- [ ] **Step 1: Rewrite installation.md (ko and en)**

The launcher-removal paragraph is already gone from Task 1. Rewrite the
rest of both files for everyday language. Keep the evidence recorder
section: uninstalled `evidence/evidence.py`, the exact command
`python3 skills/pre-sdd-review/evidence/evidence.py --version`,
`~/.pre-sdd-review/`, and the sentence that removing the skill folder does
not delete receipts.

Keep every string `test_installation_covers_install_update_and_inspection`
and `test_how_it_works_install_and_remove_share_agents_destination` pin:

- `$skill-installer`
- each `PRIMARY_INSTALL_PATHS` URL
- `npx skills add beyondwin/skills --skill korean-writing-editor`
- `git clone https://github.com/beyondwin/skills`
- `python3 scripts/verify.py`
- `확인` (ko) / `inspect` (en)
- `제3자` (ko) / `third-party` (en)
- `mkdir -p ~/.agents/skills ~/.claude/skills`
- both `ln -s` commands and both `unlink` commands
- headings `## 기본 설치 (Codex)` / `## Primary install (Codex)` and
  `## How It Works 로컬 링크` / `## How It Works local links`
- How It Works installer URL must **not** appear in the primary Codex block
- no `${CODEX_HOME:-$HOME/.codex}/skills/how-it-works` or
  `$CODEX_HOME/skills/how-it-works`

Shorten surrounding prose. Do not restate product contracts.

- [ ] **Step 2: Rewrite compatibility, safety, and verification (ko and en)**

Keep headings. Keep pinned facts:

Compatibility: each `SUPPORT_BY_PRODUCT` line exactly; `claude.ai`, `cowork`,
`skills api`; `marketplace`/`마켓플레이스`; `catalog`/`카탈로그`. Do not claim
How It Works is Codex-only portable.

Safety: `hash`, `provenance`, `consent`, `rights`/`권리`, no-telemetry
sentence, `법률`/`legal`, `의료`/`medical`, `금융`/`financial`,
`` `how-it-works`의 해당 슬라이스 `` / `` `how-it-works` slices ``. Pre-SDD
section keeps `evidence.py`, `~/.pre-sdd-review/`, `PRE_SDD_REVIEW_HOME`,
`summary`, `outcome`, `audit log` (the “not a signed audit log” sentence),
and the outcome labels. Drop any launcher-removal wording.

Verification: keep `Offline fixtures: deterministic contract evidence only.`
and `Live execution: local, explicit, optional, potentially billable, and never required by CI.`
exactly once each. Keep `python3 scripts/verify.py`, `--profile full`,
`--profile windows-portable`, `python3 scripts/verify.py --skill pre-sdd-review`,
stage name `pre-sdd-review-evidence`, `evidence.py`, and
`비-Windows의 \`windows-portable\` 통과는 native Windows 지원을 증명하지 않습니다.` /
`A non-Windows \`windows-portable\` pass does not prove native Windows support.`
exactly once in the offline section. Keep live budgets `119`, `3`, `122`,
`38`, `160` if they are already in the Korean live section.

- [ ] **Step 3: Recompute shared-section digests**

Run the digest helper. Paste the four `PRE_SDD_SHARED_SECTION_DIGESTS` values
into `tests/repository/test_public_docs.py`.

- [ ] **Step 4: Run the public-docs tests**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/repository -p 'test_public_docs.py'`

Expected: `OK`.

- [ ] **Step 5: Commit**

```bash
git add docs/users tests/repository/test_public_docs.py
git commit -m "docs(users): ease shared guides and keep one owner per fact"
```

---

### Task 3: pre-sdd-review README, English README, evidence README

**Files:**
- Modify: `skills/pre-sdd-review/README.md`, `README.en.md`, `evidence/README.md`
- Modify: `skills/pre-sdd-review/CHANGELOG.md` (`## Unreleased` note only)
- Modify: `tests/products/pre-sdd-review/test_contract.py` (digests; hard-forbid dead names)

**Interfaces:**
- Consumes: dead-name policy from Task 1; user-guide owner pages from Task 2.
- Produces: product front door that still matches `README_CONTRACT`,
  `KOREAN_FACTS` / `ENGLISH_FACTS`, heading order, first-call paths, and
  `test_v2_docs_keep_evidence_local_bounded_optional_and_agent_readable`.

- [ ] **Step 1: Tighten the v2 docs test so the launcher exception goes away**

In `test_v2_docs_keep_evidence_local_bounded_optional_and_agent_readable`,
replace

```python
            self.assertNotIn("pre-sdd-review-evidence", text.replace("`pre-sdd-review-evidence` launcher", ""))
```

with

```python
            self.assertNotIn("pre-sdd-review-evidence", text)
```

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/pre-sdd-review -p 'test_contract.py'`

Expected: still `OK` if those four documents already omit the launcher; if
not, FAIL and fix the documents in Step 2.

- [ ] **Step 2: Rewrite the three README bodies**

Keep heading order and the `### Contract` token block byte-for-byte
(`README_CONTRACT`). Keep `DEFAULT_FIRST_CALL` and the `review-only` call
that uses `docs/history/specs/<design>.md` and `docs/history/plans/<plan>.md`.
Keep `KOREAN_FACTS` / `ENGLISH_FACTS`, `SUPPORT_BY_PRODUCT["pre-sdd-review"]`
exactly (`pre-sdd-review: Codex supported; other hosts not_measured.`), the
installer URL, maintainer four-file links, `확인`/`inspect`, `evidence.py`,
`~/.pre-sdd-review/`, `audit log`, `` `summary` ``, `` `outcome` ``, outcome
labels, `schema 2`, `anomalies`, `chains`, `run_id`.

Install section: keep the `$skill-installer` snippet, then one sentence that
the recorder is not installed and the `python3 "<skill-root>/evidence/evidence.py" --version`
block, then a link to `docs/users/ko/installation.md` / English sibling for
update and remove. Do not restate the full update procedure.

`evidence/README.md`: current commands and schema 2 only. Do not mention
schema 1 receipt directories, `install.py`, or the old launcher. “Readers
consider only `runs/*.json` with `schema` 2” is enough.

CHANGELOG: under `## Unreleased`, add one `### Changed` bullet that the
product README language was simplified with no behaviour change. Do not
edit the dated `## 2.0.0 - 2026-09-05` entry.

- [ ] **Step 3: Recompute README digests**

Run the digest helper. Paste `README_CANONICAL_DOCUMENT_DIGESTS` and every
`README_CANONICAL_SECTION_DIGESTS` value into `test_contract.py`.

- [ ] **Step 4: Run product contract and public-docs tests**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/pre-sdd-review -p 'test_contract.py'
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/repository -p 'test_public_docs.py'
```

Expected: `OK`.

- [ ] **Step 5: Commit**

```bash
git add skills/pre-sdd-review/README.md skills/pre-sdd-review/README.en.md skills/pre-sdd-review/evidence/README.md skills/pre-sdd-review/CHANGELOG.md tests/products/pre-sdd-review/test_contract.py
git commit -m "docs(pre-sdd-review): ease product READMEs without changing headings"
```

---

### Task 4: Other product READMEs

**Files:**
- Modify: `skills/korean-writing-editor/README.md`, `README.en.md`
- Modify: `skills/image-workbench/README.md`, `README.en.md`
- Modify: `skills/how-it-works/README.md`, `README.en.md`
- Modify: each product `CHANGELOG.md` (`## Unreleased` only)

**Interfaces:**
- Produces: the three skill front doors still match
  `test_product_readmes_follow_common_information_order`,
  `test_product_readmes_include_installer_support_and_maintainer_link`,
  `test_how_it_works_readmes_include_supported_host_install_call_and_result`,
  and How It Works live README markers.

- [ ] **Step 1: Run the public-docs product README tests (baseline green)**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/repository -p 'test_public_docs.py'`

Expected: `OK` from Task 3. This task must stay green after the rewrite.

- [ ] **Step 2: Rewrite the six README bodies**

Keep `PRODUCT_README_HEADINGS` order and `# {display_name}` titles.
Keep each product’s `INSTALLER_COMMANDS` URL and `SUPPORT_BY_PRODUCT` line
exactly. Keep maintainer four-file links. Keep `확인`/`inspect`.

How It Works additionally keep, exactly:

- `mkdir -p ~/.agents/skills ~/.claude/skills`
- both `ln -s` commands and both `unlink` commands
- `$how-it-works`, `/how-it-works`
- `codex` and `claude-code`
- `one-sentence claim`, `Mermaid`, `numbered hop list`, `rung-specific body`,
  `adjacent slices`, `one next move`
- `덮어쓰지 않고 실패` / `fails instead of overwriting`
- live markers: `pass/fail from observable output`, `Do not use private or user prompts`,
  `Do not commit full responses`, `fresh session`, `subscription/API quota`,
  `unsupported`, `outside the repository`, `delete them after scoring`

Do not add `@how-it-works`, `Registered hosts:`, `artifact-design`,
`브라우저에서 여는 페이지`, or `page you open in a browser`.

Install sections: snippet plus link to `docs/users/` for the rest. Do not
copy the full shared installation procedure.

CHANGELOG: one `Unreleased` / `Changed` bullet per product whose README
body changed. Do not rewrite dated entries. Do not bump `release.toml`.

- [ ] **Step 3: Run public-docs and how-it-works contract tests**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/repository -p 'test_public_docs.py'
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/how-it-works -p 'test_contract.py'
```

Expected: `OK`.

- [ ] **Step 4: Commit**

```bash
git add skills/korean-writing-editor/README.md skills/korean-writing-editor/README.en.md skills/korean-writing-editor/CHANGELOG.md skills/image-workbench/README.md skills/image-workbench/README.en.md skills/image-workbench/CHANGELOG.md skills/how-it-works/README.md skills/how-it-works/README.en.md skills/how-it-works/CHANGELOG.md
git commit -m "docs(skills): ease remaining product READMEs and point to shared guides"
```

---

### Task 5: Maintainer product protocols

**Files:**
- Modify: `docs/maintainers/products/pre-sdd-review/{contract,testing,compatibility,release}.md`
- Modify: `docs/maintainers/products/korean-writing-editor/{contract,testing,compatibility,release}.md`
- Modify: `docs/maintainers/products/image-workbench/{contract,testing,compatibility,release}.md`
- Modify: `docs/maintainers/products/how-it-works/{contract,testing,compatibility,release}.md`
- Modify: `tests/products/pre-sdd-review/test_contract.py` (maintainer digests and fact strings that the easier Korean still must include)

**Interfaces:**
- Produces: pre-sdd-review `## 함께 고칠 파일` and `## 하지 않는 것`; pinned
  English subsection lists unchanged; easier Korean around them.

- [ ] **Step 1: Add failing contract facts for the new pre-sdd-review sections**

In `test_maintainer_testing_compatibility_and_release_stay_role_specific`
(or a new adjacent test in the same class), assert:

```python
        contract = (MAINTAINERS / "contract.md").read_text(encoding="utf-8")
        self.assertIn("## 함께 고칠 파일", contract)
        self.assertIn("## 하지 않는 것", contract)
        for fact in (
            "closure-only input schema",
            "shared-design invalidation map",
            "program ledger",
            "evidence probe cache",
        ):
            self.assertIn(fact, contract)
```

Run the contract discovery command. Expected: FAIL (`## 하지 않는 것` missing).

- [ ] **Step 2: Rewrite `docs/maintainers/products/pre-sdd-review/contract.md`**

Keep these subsections **byte-stable** (they have subsection digest pins):

- `### Authority order`
- `### Editable paths`
- `### Excluded surfaces`
- `### Review passes`
- `### Severities`
- `### Finding classes`
- `### Conditional risk triggers`
- `### Verdicts`
- `### Freshness`
- `### SDD handoff`

Rewrite the Korean prose around them into short everyday sentences. Do not
change the optional evidence contract’s commands, schema, or verdict rules.

Append before `## Handoff` (or after Handoff if that keeps heading order
stable — prefer after `## Optional evidence contract` and before `## Handoff`):

```markdown
## 함께 고칠 파일

동작 변경을 한 파일에만 넣지 마세요.

- 권위 순서, 판정, repair 한도, reviewer role: `skills/pre-sdd-review/SKILL.md`,
  `references/reviewer-protocol.md`, 이 계약, `tests/products/pre-sdd-review/cases.json`,
  제품 README
- 기록기 명령·schema 2: `skills/pre-sdd-review/evidence/evidence.py`,
  `evidence/README.md`, `tests/products/pre-sdd-review/evidence/`
- 호스트 지원: `products.toml`, `compatibility.md`, 공개 안내, 해당 테스트.
  이 작업에서 호스트 지원을 넓히지 않습니다.

## 하지 않는 것

아래는 명시적으로 추가하지 않습니다.

- closure-only input schema
- shared-design invalidation map
- program ledger
- evidence probe cache
```

If adding those headings changes `MAINTAINER_CANONICAL_DIGEST` but not the
pinned subsections, that is expected. If a subsection digest changes, you
changed a frozen list — revert that list.

- [ ] **Step 3: Rewrite the other pre-sdd-review maintainer pages and the other three products**

Keep commands, case ids, fixture names, version source sentences, and
compatibility tables that tests pin. For pre-sdd-review specifically keep:

- `exactly twenty-four개의`
- `## Evidence recorder compatibility`
- `| Linux / Python 3.11+ | \`not_measured\` |`
- `| Windows / Python 3.11+ | \`not_measured\` |`
- `Codex is supported` and `Every other host is \`not_measured\``
- `version source is \`skills/pre-sdd-review/release.toml\``
- the three `python3 scripts/release.py … --product pre-sdd-review` commands
- `no tag or GitHub Release is created by these commands.`

how-it-works / image-workbench / korean-writing-editor contracts already
have `## 함께 고칠 파일`. Ease the Korean; do not drop those maps.

- [ ] **Step 4: Recompute maintainer digests**

Run the digest helper. Paste `MAINTAINER_CANONICAL_DIGEST`, the ten
subsection digests (must match the previous values), and
`TESTING` / `COMPATIBILITY` / `RELEASE` whole-document digests.

- [ ] **Step 5: Run tests**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/pre-sdd-review -p 'test_contract.py'
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/repository -p 'test_public_docs.py'
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/how-it-works -p 'test_contract.py'
```

Expected: `OK`. Subsection digests for the ten frozen lists must be unchanged.

- [ ] **Step 6: Commit**

```bash
git add docs/maintainers/products tests/products/pre-sdd-review/test_contract.py
git commit -m "docs(maintainers): ease product protocols and add pre-sdd change maps"
```

---

### Task 6: Repository maintainer docs and arrival pages

**Files:**
- Modify: `docs/maintainers/repository/{architecture,versioning,products-registry,release,catalog,migrations}.md`
- Modify: `docs/README.md`, `README.md`, `README.en.md`, `catalog/README.md`
- Modify: `CONTRIBUTING.md` only if it contradicts the two-front-door or dead-name rules (likely no change)

**Interfaces:**
- Produces: architecture still lists `docs/history/` as non-authoritative /
  not installed; arrival pages still route; no new procedure owners.

- [ ] **Step 1: Run architecture and root README tests (baseline)**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/repository -p 'test_public_docs.py'
```

Expected: `OK`.

- [ ] **Step 2: Rewrite repository maintainer pages**

Keep every string `test_architecture_owns_payload_and_test_separation` and
the versioning/registry/release/catalog/migrations tests pin, including:

- `skills/`, `tests/`, `beyondwin-skills`, `python3 scripts/verify.py`,
  `2.0.0`, `catalog/plugin/.codex-plugin/plugin.json`,
  `catalog/catalog.lock.json`, `does not own plugin metadata`,
  `README.md`, `CHANGELOG.md`, `release.toml`, `docs/README.md`,
  `docs/history/`, `catalog.md`, `migrations.md`, each product name,
  `tests/products/<name>/`
- SemVer `PATCH` / `MINOR` / `MAJOR`
- registry schema field names: `schema_version`, `name`, `display_name`,
  `skill_path`, `test_path`, `maintainer_docs`, `supported_hosts`,
  `owned_paths`, `verify_stages`

Change the architecture history row from “시점 기록” to make the
in-progress-only rule visible, without dropping `docs/history/` or the
“현재 계약을 정의하지 않음” meaning. Suggested cell text:
`진행 중인 설계·계획. 현재 계약을 정의하지 않음`.

Ease Korean. Do not move facts off their owner pages.

- [ ] **Step 3: Rewrite arrival pages**

`docs/README.md`: keep routing to users / product READMEs / maintainers /
history. Keep Korean and English. Do not add procedures.

Root `README.md` / `README.en.md`: keep section order (`README_ORDER_KO` /
`README_ORDER_EN`), product README links, shared-guide links, community
file links, `현재 독립 제품` / `current standalone products`, `Claude Code`,
`Codex`, `Apache-2.0`, `python3 scripts/verify.py`. Do not say all products
are Codex-only. English README must have no Hangul except `[한국어](README.md)`.

`catalog/README.md`: catalog does not own skill contracts; last published
catalog `2.0.0`; how-it-works and pre-sdd-review are not catalog sources.

- [ ] **Step 4: Run public-docs tests**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/repository -p 'test_public_docs.py'`

Expected: `OK`.

- [ ] **Step 5: Commit**

```bash
git add docs/maintainers/repository docs/README.md README.md README.en.md catalog/README.md
git commit -m "docs: ease repository guides and keep arrival pages as routers"
```

---

### Task 7: Absorb remaining history reasons and delete finished history

**Files:**
- Delete: all finished specs, plans, and field notes listed below
- Modify: none of the live pages unless a grep shows a link to a file being deleted (fix that link in this task)

**Interfaces:**
- Consumes: Task 5 `## 하지 않는 것` (the four field-note rejections).
- Produces: `docs/history/` contains only `README.md`,
  `specs/2026-09-05-live-docs-structure-design.md`, and
  `plans/2026-09-05-live-docs-structure.md`.

- [ ] **Step 1: Confirm live docs do not link at the files to delete**

```bash
git grep -n -E 'docs/history/(specs|plans|field-notes)/2026-' \
  -- ':!docs/history/**' '*.md'
```

Expected: no hits except pre-sdd-review first-call **examples** that use the
placeholders `docs/history/specs/<design>.md` and
`docs/history/plans/<plan>.md` (keep those). If a live page links to a
concrete dated history file, retarget that link to the live owner page
before deleting.

- [ ] **Step 2: Delete finished history**

```bash
git rm -q \
  docs/history/plans/2026-08-26-public-skills-repository.md \
  docs/history/plans/2026-08-27-graspic.md \
  docs/history/plans/2026-08-27-independent-skill-product-architecture.md \
  docs/history/plans/2026-08-28-how-it-works.md \
  docs/history/plans/2026-08-28-repository-architecture.md \
  docs/history/plans/2026-08-29-pre-sdd-review.md \
  docs/history/plans/2026-08-30-pre-sdd-review-evidence-loop.md \
  docs/history/plans/2026-09-05-pre-sdd-review-evidence-simplification.md \
  docs/history/specs/2026-08-26-public-skills-repository-design.md \
  docs/history/specs/2026-08-27-graspic-design.md \
  docs/history/specs/2026-08-27-independent-skill-product-architecture-design.md \
  docs/history/specs/2026-08-28-how-it-works-repository-architecture-design.md \
  docs/history/specs/2026-08-29-pre-sdd-review-design.md \
  docs/history/specs/2026-08-30-pre-sdd-review-evidence-loop-design.md \
  docs/history/specs/2026-09-05-pre-sdd-review-evidence-simplification-design.md \
  docs/history/field-notes/2026-08-30-pre-sdd-review-v1.2.0-convergence.md \
  docs/history/field-notes/README.md
```

Do **not** delete `docs/history/specs/2026-09-05-live-docs-structure-design.md`
or `docs/history/plans/2026-09-05-live-docs-structure.md`.

- [ ] **Step 3: Run stale-identity, public-docs, and archive tests**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/repository -p 'test_stale_identifiers.py'
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/repository -p 'test_public_docs.py'
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/repository -p 'test_archive_manifest.py'
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/repository -p 'test_*.py'
```

Expected: `OK`. Graspic remains only in `skills/how-it-works/CHANGELOG.md`
(allowlisted). Archive tests use their own fixture paths, not these files.

- [ ] **Step 4: Commit**

```bash
git add -A docs/history
git commit -m "docs(history): keep only in-progress specs and plans"
```

---

### Task 8: Full verification and release check

**Files:**
- None new. Fix anything that fails in the file that owns it.

- [ ] **Step 1: Full profile**

Run: `python3 scripts/verify.py --profile full`

Expected: every stage passes, including `pre-sdd-review-contract` and
`pre-sdd-review-evidence`.

- [ ] **Step 2: Portable profile**

Run: `python3 scripts/verify.py --profile windows-portable`

Expected: passes.

- [ ] **Step 3: Release check for each product whose installed README changed**

```bash
python3 scripts/release.py check --product korean-writing-editor
python3 scripts/release.py check --product image-workbench
python3 scripts/release.py check --product how-it-works
python3 scripts/release.py check --product pre-sdd-review
```

Expected: no errors. If a product reports `payload changed from baseline …
but version did not advance`, bump that product PATCH, add a dated
CHANGELOG heading per `versioning.md`, and update `SKILL.md`
`metadata.version` in the same commit — only then. Do not tag or publish.

- [ ] **Step 4: Confirm history closure and working tree**

```bash
ls docs/history docs/history/specs docs/history/plans
test ! -e docs/history/field-notes
git status --short
```

Expected: history has `README.md`, this spec, this plan; no `field-notes/`;
working tree clean.

---

## Self-review against the spec

- **Decision 1 (audience tree, two front doors, no new page):** Tasks 1, 6.
- **Decision 2 (one owner per fact, pinned installer strings):** Tasks 2–4;
  product READMEs keep installer/support/inspect pins and link out.
- **Decision 3 (language, frozen machine-readable lists):** Tasks 2–6;
  Task 5 keeps the ten subsection digest pins unchanged.
- **Decision 4 (dead names):** Task 1 test plus launcher-paragraph delete,
  Task 3 hard-forbid in product docs. Verify stage name kept.
- **Decision 5 (history prune + absorb):** Task 5 `하지 않는 것`, Task 7
  delete list. This spec/plan kept.
- **Decision 6 (pins + 함께 고칠 파일):** Tasks 1, 3, 5. Digests travel
  with the page.
- **Decision 7 (gitignore additive):** Task 1 Step 6.
- **Decision 8 (frozen contracts, versioning):** Global Constraints; Task 8
  release check. SKILL.md never in a Files list except “do not change”.
- **Decision 9 (owner-machine leftovers):** Global Constraints; live docs
  must not mention them (Task 1/2).
- **Success criteria:** Task 8 ls + full verify.
