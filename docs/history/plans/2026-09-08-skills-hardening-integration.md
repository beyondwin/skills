# Skills Hardening Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 네 제품의 수정, 공유 설치 문서, standalone 배포와 검증을 하나의 일관된 계약으로 마무리한다.

**Architecture:** [공통 기반](2026-09-08-repository-hardening.md)과 네 제품 계획의 결과를 소비하는 최종 통합 단계다. 공통 writer 한 명이 공유 파일을 수정하고, 제품 writer는 해당 제품 경계 안에서만 검토 결과를 반영한다.

**Tech Stack:** Python 3.11+ 표준 라이브러리, unittest, Markdown, Git, 기존 ZIP release CLI.

**Spec:** `docs/history/specs/2026-09-08-skills-hardening-design.md` §4.3, §6–8, R4–R5 및 전 제품 통합.

## Global Constraints

- 새 스킬, 범용 프레임워크, 필수 외부 공급자, 텔레메트리, 저장소 분할을 추가하지 않는다.
- catalog의 불변 두 제품 번들을 자동으로 갱신하지 않는다. 현재 지원 호스트 범위를 넓히지 않는다.
- 실제 모델·이미지 생성·배포는 포함하지 않는다. 실제 사용자 설치 경로에서 시험하지 않는다.
- 제품별 검사만 통과한 상태를 전체 완료로 보고하지 않는다. 새 실패·변경이 없으면 동일 전체 검증을 반복하지 않는다.
- R6의 물리적 모듈 추출·규범 digest 제거와 P5의 역할·trigger 확대는 이 계획의 완료 조건이 아니다.
- 제품 목표 버전은 image-workbench 2.0.2, korean-writing-editor 2.0.2, how-it-works 2.0.0, pre-sdd-review 3.0.0이다.
- 모든 명령은 저장소 루트에서 실행한다. 네 제품의 reviewed diff를 통합 담당이 직렬 커밋한 후 이 계획을 실행한다.

## File Structure

| 소유 파일 | 책임 |
| --- | --- |
| `scripts/lib/product_contract.py` | README도 standalone 내부 링크 계약으로 검사 |
| `scripts/release.py` | schema 3 추출본 버전 smoke |
| `scripts/lib/verification.py` | 새 How evidence 테스트를 stage discovery에 포함 |
| `tests/repository/test_verify.py` | 실제 How stage의 테스트 선택 검증 |
| `tests/repository/test_installation_contract.py` (신규) | 게시할 설치 코드 블록을 임시 경로에서 실행 |
| `tests/repository/test_product_contract.py` (신규) | README의 payload 밖 상대 링크 반례 |
| `tests/repository/test_public_docs.py` | 새 문서 사실, 규범·극성·모순 보호 유지 |
| `tests/repository/test_release.py` | 현행 제품 버전과 변이 배포 계약 |
| `tests/repository/test_release_contract.py` | 현행 네 제품 버전 pin과 날짜 변이 fixture |
| `tests/repository/test_repository.py` | 현행 Image 버전 불일치 반례의 실제 변이 |
| `tests/repository/test_catalog_release.py` | 현행 How 아카이브를 소비하는 independent 합성 fixture의 버전·태그 |
| `docs/users/ko/installation.md`, `docs/users/en/installation.md` | 안전한 링크, clone 소스 경로 |
| `docs/users/ko/compatibility.md`, `docs/users/en/compatibility.md` | 지원 대상과 현재 증거 범위 |
| `docs/users/ko/verification.md`, `docs/users/en/verification.md` | 측정 차원과 runner/recorder 형식 |
| `docs/users/ko/safety-and-privacy.md`, `docs/users/en/safety-and-privacy.md` | schema 3의 salt·HMAC·과거 기록 경계 |
| `docs/maintainers/repository/products-registry.md` | R3의 필수 목록 계약 |
| `docs/maintainers/repository/architecture.md` | R1의 공통 matrix 계약 |
| `docs/maintainers/repository/release.md` | R2의 소스 결속 및 검증 순서 |

제품 README, CHANGELOG, release.toml, SKILL.md와 제품 테스트는 해당 제품 계획의 소유다. 누락을 발견하면 담당 writer에게 구체적 파일/반례를 반환하고, 공유 writer가 동시에 제품 파일을 수정하지 않는다. `catalog/`, 전역 설치본, archive source manifest는 수정하지 않는다.

### Task 1: 실제 게시할 설치 코드와 standalone 링크 검사

**Interfaces:**
- Consumes: How It Works 제품 README 두 언어에 있는 `<!-- how-it-works-local-links -->` 직후의 Python fenced block. block은 `sys.argv[1:3]`로 source와 target을 받고, 성공/동일 링크에는 0, 충돌에는 비영(非零) 종료한다.
- Consumes: `_check_relative_links(skill_root: Path, relative_path: str, text: str) -> list[str]`, `stage_product(skill_root: Path, destination: Path, registry: ProductRegistry) -> Path`.
- Produces: 네 문서의 동일 설치 block, `test_installation_contract.py`의 실행 회귀 검사. 필수 설치 도구나 payload 파일을 새로 만들지 않는다.

- [ ] 신규 테스트 모듈을 다음 기반으로 작성한다. block을 재구현한 테스트가 아니라 문서에서 추출한 코드를 실행한다.

```python
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCUMENTS = (
    "skills/how-it-works/README.md",
    "skills/how-it-works/README.en.md",
    "docs/users/ko/installation.md",
    "docs/users/en/installation.md",
)
MARKER = "<!-- how-it-works-local-links -->"

def installation_block(relative: str) -> str:
    text = (ROOT / relative).read_text(encoding="utf-8")
    if text.count(MARKER) != 1:
        raise AssertionError(f"one installation block required: {relative}")
    tail = text.split(MARKER, 1)[1]
    match = re.match(r"\s*```python\n(.*?)\n```", tail, re.S)
    if match is None:
        raise AssertionError(f"Python block must follow marker: {relative}")
    return match.group(1)

class InstallationContractTests(unittest.TestCase):
    def test_documented_link_installation_preserves_existing_targets(self):
        for document in DOCUMENTS:
            block = installation_block(document)
            for state in ("absent", "same", "directory", "other", "dangling"):
                with self.subTest(document=document, state=state), tempfile.TemporaryDirectory() as tmp:
                    base = Path(tmp)
                    source = base / "source with spaces" / "how-it-works"
                    source.mkdir(parents=True)
                    (source / "SKILL.md").write_text("name: how-it-works\n", encoding="utf-8")
                    other = base / "other source"
                    other.mkdir()
                    target = base / "target with spaces" / "how-it-works"
                    target.parent.mkdir()
                    try:
                        if state == "same":
                            target.symlink_to(source, target_is_directory=True)
                        elif state == "directory":
                            target.mkdir()
                            (target / "keep.txt").write_bytes(b"keep")
                        elif state == "other":
                            target.symlink_to(other, target_is_directory=True)
                        elif state == "dangling":
                            target.symlink_to(base / "missing", target_is_directory=True)
                    except OSError as exc:
                        if os.name == "nt" and getattr(exc, "winerror", None) == 1314:
                            self.skipTest("symlink privilege unavailable on this Windows runner")
                        raise
                    link_before = os.readlink(target) if target.is_symlink() else None
                    result = subprocess.run(
                        [sys.executable, "-c", block, str(source), str(target)],
                        capture_output=True, text=True, check=False,
                    )
                    if state in ("absent", "same"):
                        if os.name == "nt" and "WinError 1314" in result.stderr:
                            self.skipTest("symlink privilege unavailable on this Windows runner")
                        self.assertEqual(result.returncode, 0, result.stderr)
                        self.assertTrue(target.is_symlink())
                        self.assertEqual(target.resolve(), source.resolve())
                        again = subprocess.run(
                            [sys.executable, "-c", block, str(source), str(target)],
                            capture_output=True, text=True, check=False,
                        )
                        self.assertEqual(again.returncode, 0, again.stderr)
                        self.assertFalse((source / "how-it-works").exists())
                    else:
                        self.assertNotEqual(result.returncode, 0)
                        if link_before is not None:
                            self.assertEqual(os.readlink(target), link_before)
                        else:
                            self.assertEqual((target / "keep.txt").read_bytes(), b"keep")
                    self.assertEqual((source / "SKILL.md").read_bytes(), b"name: how-it-works\n")
```

- [ ] 신규 `test_product_contract.py`에 아래 테스트를 작성한다.

```python
import tempfile
import unittest
from pathlib import Path
from scripts.lib.product_contract import _check_relative_links

class StandaloneLinkTests(unittest.TestCase):
    def test_readme_cannot_escape_standalone_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = root / "sample"
            payload.mkdir()
            (root / "outside.md").write_text("repository-only", encoding="utf-8")
            errors = _check_relative_links(payload, "README.md", "[guide]" "(../outside.md)")
            self.assertTrue(errors)
            self.assertEqual(_check_relative_links(
                payload, "README.md", "[guide]" "(https://github.com/beyondwin/skills/blob/main/docs/README.md)"
            ), [])
```

- [ ] RED: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.repository.test_installation_contract tests.repository.test_product_contract` 실행. 공유 설치 문서에 marker가 없고 README의 escape 예외가 있어 실패해야 한다.
- [ ] 제품 How 계획의 검토된 Python block을 공유 설치 문서 두 언어에 그대로 복사한다. 사용자 실행법도 block 앞에 `python3 - "$PWD/skills/how-it-works" "$HOME/.agents/skills/how-it-works" <<'PY'`, 뒤에 단독 `PY` 줄을 붙이는 here-document 방식으로 맞춘다. Claude Code 호출은 target 인수만 `"$HOME/.claude/skills/how-it-works"`로 바꾼다. 기존 `mkdir -p ~/.agents/skills ~/.claude/skills`와 정확한 두 목적지, 검사 후 unlink 안내를 유지한다. 기존 raw `ln -s` 설치 명령을 남겨 두지 않는다.
- [ ] 두 언어의 Codex 전용 clone 예제에서 `git clone` 다음에 `cd skills`를 삽입한다.

```bash
git clone https://github.com/beyondwin/skills.git
cd skills
SKILL_SOURCE="$PWD/skills/korean-writing-editor"
SKILL_TARGET="${CODEX_HOME:-$HOME/.codex}/skills/korean-writing-editor"
ls -ld "$SKILL_SOURCE"
ls -ld "$SKILL_TARGET"
```

- [ ] `_check_relative_links`의 `except ValueError`에서 README 두 이름을 특별 허용하는 두 줄만 제거한다. 내부 링크 존재 검사는 유지한다. 제품 README의 저장소 외부 상대 링크는 제품 writer가 공개 URL로 바꾼다.

```python
try:
    resolved.relative_to(skill_root.resolve())
except ValueError:
    errors.append(f"broken relative link in {relative_path}: {target}")
    continue
```

- [ ] `test_public_docs.py`의 `HOW_IT_WORKS_AGENTS_LINK`·`HOW_IT_WORKS_CLAUDE_LINK` literal 포함 검사만 새 실행 계약으로 교체한다. 테스트는 `installation_block(relative)`를 import하여 존재를 확인하고, 실제 행동 검사는 신규 모듈에 둔다. `mkdir`, 정확한 목적지, 제거 검사, 기존 설치 덮어쓰기 금지 단언은 유지한다. `ProductReadmeOwnershipTests`는 저장소 밖 문서의 기대 링크만 공개 URL로 바꾼다.
- [ ] GREEN: `tests.repository.test_installation_contract`와 `tests.repository.test_product_contract`를 실행한다. 공개 문서의 제품 사실 갱신은 Task 2에서 완료한 뒤 `test_public_docs` 전체를 실행한다. URL 도달 여부를 측정했다고 기록하지 않는다.
- [ ] 통합 담당이 Task 1의 정확한 파일만 stage하고 `git diff --cached --check` 뒤 `fix: make documented skill installs idempotent`로 커밋한다.

### Task 2: 새 제품 사실과 공유 배포 계약 연결

**Interfaces:**
- Consumes: Pre-SDD `--version`의 canonical JSON `{"cli_version":"3.0.0","schema":3,"skill_name":"pre-sdd-review"}`와 마지막 LF. 옵션 조회는 evidence home을 만들지 않는다.
- Consumes: 각 제품 `release.toml`과 SKILL metadata, Korean 신규 runner identity, How의 historical-unbound/current evidence 분리.
- Produces: 공유 사용자 문서와 release smoke가 위 계약을 그대로 설명·검증한다. 기존 catalog v2.0.0 fixture는 바꾸지 않는다.

- [ ] `tests/repository/test_release.py`의 현행 Pre-SDD smoke 테스트가 새 CLI에서 RED인지 기록한다. 기존 schema 2의 과거 읽기 fixture를 버전 실패로 오인하지 않는다.
- [ ] `test_verify.py`의 How stage 테스트에 아래 단언을 추가한다. 현재 `test_contract.py`만 선택하므로 RED다. 신규 evidence 테스트가 생겼는데 실행되지 않는 성공을 막는다.

```python
stage = next(item for item in stages(ROOT, "full", self.registry, skill="how-it-works")
             if item.name == "how-it-works-contract")
self.assertEqual(stage.argv[stage.argv.index("-p") + 1], "test_*.py")
```

- [ ] `scripts/lib/verification.py`의 `how-it-works-contract`에만 `-p test_contract.py`를 `-p test_*.py`로 바꾸고 해당 기존 test_verify 단언도 맞춘다. Pre-SDD의 별도 evidence stage와 다른 제품 stage는 그대로 둔다.
- [ ] `scripts/release.py`의 `_smoke_pre_sdd_review`에서 두 상수만 아래로 바꾼다. 실패 상태·canonical bytes·HOME 무변경 검사를 유지한다.

```python
expected_version = {"cli_version": "3.0.0", "schema": 3, "skill_name": "pre-sdd-review"}
expected_bytes = b'{"cli_version":"3.0.0","schema":3,"skill_name":"pre-sdd-review"}\n'
```

- [ ] `tests/repository/test_release_contract.py`의 `EXPECTED`를 아래 목표값으로 맞춘다. How의 `test_how_it_works_first_archive_identity`는 current identity 검사로 이름을 바꾸고 2.0.0 tag/archive를 검사한다. Pre-SDD current identity는 3.0.0을 검사한다.

```python
EXPECTED = {
    "korean-writing-editor": "2.0.2",
    "image-workbench": "2.0.2",
    "how-it-works": "2.0.0",
    "pre-sdd-review": "3.0.0",
}
```

- [ ] 같은 파일의 version mismatch 반례는 현재 manifest의 `2.0.0`을 `2.0.1`로 바꾸어 metadata `2.0.0`과 충돌시킨다. 날짜 반례는 고정된 2026-08-28 옛 항목 대신 `re.sub(r"(?m)^## 2\.0\.0 - [0-9]{4}-[0-9]{2}-[0-9]{2}\n", "", text, count=1)`으로 현행 2.0.0 dated heading만 지운다. 제거 후 문자열이 달라졌는지 단언하고 `missing dated release heading for 2.0.0` 오류를 확인한다. `import re`를 추가한다.

- [ ] `test_release.py`에서 **현재 제품 build/download를 지칭하는** 고정 artifact 이름을 registry와 `load_product_release`로 얻는다. 예를 들어 현재 How 정상 출력 기대값은 다음과 같다. 공격 fixture의 잘못된 이름, catalog의 v2.0.0, schema 2 과거 record는 그대로 둔다.

```python
expected = release.load_product_release(ROOT / "skills" / "how-it-works")
self.assertEqual({path.name for path in self.output.iterdir()}, {expected.artifact_name, "SHA256SUMS"})
```

- [ ] 직접 소비자에서 추가로 확인된 현행 버전 변이를 맞춘다. `test_repository.py::test_rejects_version_mismatch`의 Image 원본 버전과 기대 오류를 2.0.2로 맞추고 원본이 실제로 달라졌는지 단언한다. `test_release.py`의 날짜 반례는 현행 How 2.0.0 dated heading을 제거하고, ZIP metadata 변이는 현행 2.0.0을 9.9.9로 바꾸었는지 각 대상에서 단언한다. `test_release_contract.py`의 Korean invalid-SemVer 반례도 현행 2.0.2를 2.0으로 바꾸고 실제 변이를 확인한다.
- [ ] `test_catalog_release.py::CatalogIndependentFixtureTests`는 현행 How 빌드를 사용하는 합성 fixture이므로 버전과 qualified tag를 현행 source release에서 얻는다. `release.toml`이 삭제된 공격 ZIP에서도 fixture를 구성해야 하므로 손상된 추출본에서 버전을 읽도록 바꾸지 않는다. negative tag는 의도적으로 unqualified 상태를 유지한다. 이 변경은 `catalog/`와 `fixtures/legacy-bundle-v2.0.0/`의 불변 이력을 수정하지 않는다.

- [ ] 아래 내용을 기존 공유 문서의 해당 제품 절에 반영한다. 제품 README와 관리자 계약을 원본으로 사용하며 문서별 유지 대상은 정확히 다음과 같다.

| 문서 쌍 | 반영할 사실 |
| --- | --- |
| `compatibility.md` | 지원 대상은 유지. How 과거 smoke는 historical-unbound이며 현재 payload/model 실행 증거와 별개. 새 native Windows 측정 없음 |
| `verification.md` | Korean은 hard 실패 우선, 의미·귀속·실행 미관측은 partially_verified. How fence/hop·loading·syntax·meaning은 별도 증거. Pre-SDD schema 2 읽기만 지원·schema 3의 checkout 결속 |
| `safety-and-privacy.md` | recorder 선택성, 원시 절대 경로 미기록, 로컬 비공개 salt와 HMAC, 별도 clone/worktree·경로 이동은 별개 identity. receipt 오류가 semantic verdict를 바꾸지 않음 |
| `products-registry.md` | 정확한 정수 schema, 허용 최상위 키, 비어 있지 않은 필수 목록·중복 거부, 빈 runner 실패 |
| `architecture.md` | 공통·unknown·빈 diff·diff 실패 PR은 selector 없는 전체 검사, 제품 전용은 좁은 검사 |
| `release.md` | checksum → archive checks → extract → metadata → 신뢰 소스 hash → smoke, checksum 단독 인증 아님 |

현행 수치가 등장하는 공유 문서·검사에서는 Korean offline 33개(`normative=10`, 나머지 기존 분류 유지), runner 18, Image fixture 31개·mutation 17개를 실제 제품 결과와 맞춘다. Korean live 14 cases/17 repeats와 `119/3/122/38/160` 호출 예산은 유지한다. 과거 실행의 수치는 새 값으로 덮어쓰지 않는다.

- [ ] `test_public_docs.py`의 Pre-SDD 규범 digest는 제거하지 않는다. 바뀐 해당 절을 읽고 규범·극성·추가 모순 방어가 그대로인지 검토한 뒤 **승인된 새 절의 digest만** 갱신한다. 기존 `pre_sdd_shared_contract_errors` 및 변이 검사를 유지한다. digest 계산은 해당 함수와 같은 `_owned_section`을 사용한다.

```python
import hashlib
from tests.repository.test_public_docs import _owned_section

def section_digest(document, heading):
    text = document.read_text(encoding="utf-8")
    return hashlib.sha256(_owned_section(text, heading).encode("utf-8")).hexdigest()
```

- [ ] GREEN: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.repository.test_verify tests.repository.test_release_contract tests.repository.test_public_docs tests.repository.test_release tests.repository.test_repository tests.repository.test_catalog_release` 실행. 이어 `PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --skill how-it-works`에서 새 evidence 테스트가 실행되는지 확인한다. 이 시점의 제품 코드는 인덱스에 반영된 커밋과 일치해야 한다.
- [ ] Task 2의 정확한 공유 파일만 stage하고 `git diff --cached --check` 뒤 `docs: align shared contracts with hardened skill releases`로 커밋한다.

### Task 3: 통합 반례·추출본 검증과 독립 리뷰

**Files:** 새로운 제품 파일 수정은 없다. 검증 로그는 gitignored `.evidence/` 아래에 기록하고, 결함 수정이 생기면 소유 계획과 파일로 돌아간다.

**Interfaces:**
- Consumes: `scripts/verify.py`의 `--profile full`, `--profile windows-portable`, 제품 selector 및 `scripts/release.py build|verify-download --product NAME`.
- Produces: 실행 HEAD, 명령·종료 코드, 새 테스트 수, 환경, 미측정 항목을 갖는 closeout 기록. 명령을 적었다는 사실은 실행 성공의 증거가 아니다.

- [ ] `git status --short`와 `git diff --check`로 실행 기준을 확인한다. 각 제품 version/SKILL/CHANGELOG 날짜가 목표와 같고 catalog가 변하지 않았는지 확인한다. 제품 수정이 pending이면 ZIP 검증을 시작하지 않는다.
- [ ] 전체 full profile을 한 번 실행하고 로그를 보존한다.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --profile full
```

Expected: exit 0, 공통 repository-contract 포함. 예전 700개 수치를 그대로 완료 증거에 복사하지 않고 실제 실행 수를 기록한다.

- [ ] portable profile을 한 번 실행한다.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --profile windows-portable
```

Expected: exit 0. 로컬 macOS에서 이 profile을 통과해도 native Windows 실행 또는 recorder 잠금 지원을 주장하지 않는다.

- [ ] Git 인덱스에서 실제 ZIP을 빌드하고 별도 임시 폴더의 다운로드를 검증한다. Python orchestration은 이미 존재하는 CLI만 호출한다.

```python
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from scripts.lib.product_registry import load_registry

root = Path.cwd()
environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
with tempfile.TemporaryDirectory(prefix="skills-download-review-") as tmp:
    for name in load_registry(root / "products.toml").names:
        output = Path(tmp) / name
        subprocess.run([sys.executable, "scripts/release.py", "build", "--product", name,
                        "--output", str(output)], env=environment, check=True)
        subprocess.run([sys.executable, "scripts/release.py", "verify-download", "--product", name,
                        "--input", str(output)], env=environment, check=True)
```

Expected: 네 제품 build/verify-download 모두 exit 0. 새 날짜 changelog가 있어야 build가 통과한다. README 링크·변이 archive·추출본 smoke가 포함되며 실제 사용자 HOME이나 provider를 호출하지 않는다.

- [ ] 통합 diff를 독립 read-only reviewer에게 전달한다. 검토 범위는 설계 §7의 반례와 바로 연결된 소비자다. 승인되지 않은 R6/P5를 필수 조건으로 추가하지 않는다. 구체적 재현이 있는 실패만 담당 writer에게 반환한다.
- [ ] 새 수정이 있으면 해당 제품/공유 범위의 회귀 검사를 먼저 실행한다. 전체 source 기준이 바뀌어 앞선 통합 증거가 무효가 된 경우에만 영향을 받는 최종 gate를 다시 실행한다. 변경 없는 전체 반복은 하지 않는다.
- [ ] 최종 기록에 `verified`와 `not_measured`를 분리한다. 실모델 품질, 실제 이미지 생성, 외부 URL 응답, 원격 CI, native 신규 플랫폼·Mermaid 의미 평가는 실행하지 않았으면 `not_measured`다. tag·push·공개·사용자 설치 갱신을 수행하지 않는다.
