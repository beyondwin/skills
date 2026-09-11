# SDDx Worktree Reliability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 기존 호출 방법을 유지하면서 Grok worker가 linked worktree에서 직접 커밋하고, 실제 작업 결과에 따라 완료 여부를 판단하게 한다.

**Architecture:** sandbox 준비·정리용 Python 도구 하나를 추가하고 기존 dispatch에서 호출한다. worker 역할과 완료 조건은 기존 prompt와 SDD 리뷰 절차에 반영한다. worker 실행 엔진, 자동 재시도 계층, 보고서 파서는 만들지 않는다.

**Tech Stack:** Python 3.11+ 표준 라이브러리(`pathlib`, `subprocess`, `json`, `tomllib`, `unittest`), Git, 설치된 Grok CLI 및 Superpowers.

**Spec:** [승인된 설계](../specs/2026-09-11-worktree-reliability-design.md).

## Global Constraints

- 사용자 요구: 복잡하게 구현하지 않고 직관적이고 단순하게 만든다.
- 사용자는 기존대로 `sddx <plan-file> [cursor|grok]`를 호출한다.
- 추가 사용자 옵션이나 작업마다 새로운 선택 화면을 만들지 않는다.
- 기존 `resolve_backend.py`는 CLI 발견과 플래그 확인을 하는 읽기 전용 도구로 유지한다.
- 외부 worker는 구현·테스트·커밋·보고를 담당하고 리뷰어는 호스트 네이티브다.
- 컨트롤러가 대신 커밋하는 경로를 정상 실행으로 추가하지 않는다.
- 사용자 스킬·플러그인·인증 환경 전체를 복제하거나 재구성하는 기능은 만들지 않는다.
- 새 상태 체계나 보고서 파서를 만들지 않는다.
- Superpowers 파일, 다른 제품, frozen catalog, 지원 호스트 목록은 변경하지 않는다.
- 범용 병렬 실행, 설정 마이그레이션, 캐시, 백그라운드 서비스는 추가하지 않는다.
- 라이브 실행은 명시적으로 승인된 범위에서만 한다. 기본 검증과 CI는 공급자를 호출하지 않는다.
- Grok helper의 TOML 파싱에는 표준 `tomllib`를 사용하고 Python 3.11+ 요구를 문서에 명시한다. 별도 TOML 의존성이나 자체 파서는 추가하지 않는다.
- 생성 설정, 복원용 기록, 원시 provider 이벤트는 커밋하지 않는다.

---

## 시작 상태와 파일 책임

설계 기준 제품 코드는 `3901249`, 승인 설계 커밋은 `e36ee44`다.
실행 시작 때 실제 Git 상태를 다시 확인하고 기존 변경을 보존한다.
이 계획은 진행 중인 이력 계획 경로에 저장한다. 실제 구현을 격리할 때는 실행 시점에
`using-git-worktrees` 절차를 사용한다.

| 파일 | 책임 |
| --- | --- |
| `skills/sddx/scripts/prepare_grok_sandbox.py` (신규) | Git 경로 계산, 작업용 프로파일 추가, 자신이 추가한 설정 정리 |
| `tests/products/sddx/test_prepare_grok_sandbox.py` (신규) | 실제 임시 Git 저장소를 사용하는 공급자 없는 회귀 검사 |
| `skills/sddx/scripts/resolve_backend.py` | 사용할 필수 Grok 플래그 검사 |
| `skills/sddx/references/dispatch.md` | helper 호출 위치, argv 교체, worker 종료 뒤 정리 |
| `skills/sddx/references/worker-prompt.md` | brief, 작업 범위, 구현·테스트·커밋·보고 지시 |
| `skills/sddx/SKILL.md` | 기존 SDD 연결과 완료 조건 |
| `tests/products/sddx/test_resolve_backend.py`, `test_contract.py`, `cases.json` | resolver와 문서 계약 회귀 검사 |
| `tests/products/sddx/behavior-probes.md` (신규) | fresh-context 행동 검증의 입력과 판정 기준 |
| `docs/maintainers/products/sddx/contract.md`, `testing.md`, `compatibility.md`, `release.md` | 변경된 계약과 실제로 측정한 결과 |
| `skills/sddx/README.md`, `README.en.md`, `release.toml`, `CHANGELOG.md` | 사용 안내, Python 요구, 버전 1.0.1 |

`scripts/lib/verification.py`의 `sddx-contract`는 이미 `test_*.py`를 발견한다.
새 테스트 등록을 위해 공용 verifier나 `products.toml`을 수정하지 않는다.
스킬 원본을 고치는 이 구현 작업에 편집 대상 SDDx 실행 절차를 자동 적용하지 않는다.

### Task 1: Git 경로와 sandbox 준비·정리

**Files:**
- Create: `skills/sddx/scripts/prepare_grok_sandbox.py`
- Create: `tests/products/sddx/test_prepare_grok_sandbox.py`
- Modify: `docs/maintainers/products/sddx/testing.md`

**Interfaces:**
- Consumes: 실제 worktree 루트 `Path`, 기존 SDD evidence 디렉터리 안의 복원 기록 경로 `Path`.
- Produces: `prepare(worktree: Path, state: Path) -> str` — 성공 시 `sddx-worktree` 반환.
- Produces: `cleanup(worktree: Path, state: Path) -> None` — 직접 추가한 설정만 정리.
- Produces: CLI `prepare|cleanup --worktree PATH --state PATH`.
- CLI 성공: prepare는 stdout JSON `{"profile":"sddx-worktree"}`와 LF, cleanup은 `{"cleaned":true}`와 LF, exit 0.
- CLI 실패: stdout은 비우고 stderr에 `BLOCKED: 원인`, exit 1. 잘못된 argv는 argparse의 exit 2.

- [ ] **Step 1: 실제 Git fixture와 실패 테스트 작성**

새 테스트 파일에 다음 기반을 넣는다. fixture Git 설정은 각 임시 저장소에만 쓴다.
제품 helper는 아직 만들지 않는다.

```python
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "skills/sddx/scripts/prepare_grok_sandbox.py"


def git(cwd, *args):
    return subprocess.run(
        ["git", "-C", str(cwd), *args], check=True,
        capture_output=True, text=True, timeout=10,
        env={key: value for key, value in os.environ.items()
             if not key.startswith("GIT_")},
    ).stdout.strip()


class SandboxTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="sddx sandbox ")
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name).resolve()
        self.repo = self.base / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "--initial-branch=main")
        git(self.repo, "config", "user.name", "SDDx Fixture")
        git(self.repo, "config", "user.email", "sddx@example.invalid")
        hooks = self.base / "empty-hooks"
        hooks.mkdir()
        git(self.repo, "config", "core.hooksPath", str(hooks))
        git(self.repo, "-c", "commit.gpgsign=false", "commit", "--allow-empty", "-m", "fixture")
        self.wt = self.base / "linked worktree"
        git(self.repo, "worktree", "add", "-b", "codex/smoke", str(self.wt))
        evidence = self.wt / ".superpowers/sdd/probe"
        evidence.mkdir(parents=True)
        self.state = evidence / "grok-sandbox.json"
        self.config = self.wt / ".grok/sandbox.toml"
        spec = importlib.util.spec_from_file_location("sddx_sandbox", SCRIPT)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_linked_worktree_prepares_and_cleans(self):
        self.assertEqual(self.module.prepare(self.wt, self.state), "sddx-worktree")
        profile = tomllib.loads(self.config.read_text())["profiles"]["sddx-worktree"]
        expected = {
            str((self.repo / ".git").resolve()),
            git(self.wt, "rev-parse", "--absolute-git-dir"),
        }
        self.assertEqual(set(profile["read_write"]), expected)
        self.assertEqual(profile["extends"], "workspace")
        self.module.cleanup(self.wt, self.state)
        self.assertFalse(self.config.exists())
        self.assertFalse(self.state.exists())

    def test_existing_bytes_survive_repeated_prepare(self):
        self.config.parent.mkdir()
        before = b'# user comment\r\n[profiles.review]\r\nextends = "read-only"\r\n'
        self.config.write_bytes(before)
        self.module.prepare(self.wt, self.state)
        journal = self.state.read_bytes()
        self.module.prepare(self.wt, self.state)
        self.assertEqual(self.state.read_bytes(), journal)
        self.module.cleanup(self.wt, self.state)
        self.assertEqual(self.config.read_bytes(), before)

    def test_cleanup_preserves_intervening_edit(self):
        self.module.prepare(self.wt, self.state)
        changed = self.config.read_bytes() + b"\n# user changed this\n"
        self.config.write_bytes(changed)
        with self.assertRaises(ValueError):
            self.module.cleanup(self.wt, self.state)
        self.assertEqual(self.config.read_bytes(), changed)
        self.assertTrue(self.state.exists())

    def test_bad_or_conflicting_toml_is_untouched(self):
        self.config.parent.mkdir()
        cases = (
            b"[broken", b"profiles = 7\n",
            b'[profiles.sddx-worktree]\nextends = "off"\n',
        )
        for before in cases:
            with self.subTest(before=before):
                self.config.write_bytes(before)
                with self.assertRaises(ValueError):
                    self.module.prepare(self.wt, self.state)
                self.assertEqual(self.config.read_bytes(), before)
                self.assertFalse(self.state.exists())
```

- [ ] **Step 2: 실패 확인**

```bash
python3 -m unittest discover -s tests/products/sddx -p test_prepare_grok_sandbox.py -v
```

예상: helper 파일이 없어 실패한다. 다른 fixture 설정 오류라면 먼저 fixture를 고친다.

- [ ] **Step 3: 경로 계산과 TOML 구성 구현**

새 helper 한 파일에 아래 순수 함수를 둔다. 기존 Git env가 fixture를 가리키도록
요구하는 사용자 환경에 의존하지 않고, 명시한 cwd의 저장소를 사용한다.
Git subprocess는 argv 배열, timeout, `check=True`를 사용한다.

```python
import json
import os
import subprocess
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    raise SystemExit("BLOCKED: Grok sandbox preparation requires Python 3.11+")

PROFILE = "sddx-worktree"


def git_path(worktree: Path, flag: str) -> Path:
    env = {key: value for key, value in os.environ.items()
           if not key.startswith("GIT_")}
    result = subprocess.run(
        ["git", "-C", str(worktree), "rev-parse", flag],
        check=True, capture_output=True, text=True, timeout=5, env=env,
    )
    return (worktree / result.stdout.removesuffix("\n")).resolve()


def profile_values(worktree: Path) -> dict:
    if git_path(worktree, "--show-toplevel") != worktree:
        raise ValueError("worktree must be a Git checkout root")
    paths = {git_path(worktree, "--git-dir"), git_path(worktree, "--git-common-dir")}
    extra = sorted(str(path) for path in paths if not path.is_relative_to(worktree))
    return {"extends": "workspace", "read_write": extra}


def profile_text(before: str | None, expected: dict) -> str:
    text = "" if before is None else before
    profiles = tomllib.loads(text).get("profiles", {})
    if not isinstance(profiles, dict):
        raise ValueError("profiles must be a TOML table")
    if PROFILE in profiles:
        if profiles[PROFILE] != expected:
            raise ValueError("sddx-worktree profile conflicts with required settings")
        return text
    block = (f'\n[profiles.{PROFILE}]\nextends = "workspace"\n'
             f'read_write = {json.dumps(expected["read_write"], ensure_ascii=False)}\n')
    result = text + "\n" + block
    if tomllib.loads(result)["profiles"][PROFILE] != expected:
        raise ValueError("generated profile differs from required settings")
    return result
```

`read_write`는 Git 디렉터리 권한이다. 다른 브랜치 refs도 있는 공용 `.git`을
허용한다는 한계를 문서에 적고, 세부 Git 내부 파일별 allowlist를 추가하지 않는다.

- [ ] **Step 4: prepare/cleanup을 단순한 파일 복원으로 구현**

복원 기록은 아래 형태 하나만 사용한다. 워크플로 상태, 세션 DB, 버전 마이그레이션은 없다.
`before`와 `after`는 `read_bytes().decode("utf-8")`로 읽어 원래 개행을 보존한다.

```python
journal = {
    "worktree": str(worktree),
    "before": before,
    "after": after,
    "created_dir": not config.parent.exists(),
}
```

`prepare(worktree, state)`의 순서는 다음으로 고정한다.

1. worktree를 절대 실제 경로로 정규화하고 Git 루트인지 확인한다.
   state는 해당 worktree의 `.superpowers` 안, 이미 존재하는 evidence 디렉터리의
   파일이어야 한다. `.grok`, config, state와 state의 worktree 아래 부모 중
   심볼릭 링크가 있으면 거절한다. config/state가 일반 파일이 아니어도 거절한다.
2. state가 이미 있으면 기록의 worktree와 필드 타입을 확인한다.
   현재 config가 기록의 `after`이면 기존 기록을 보존하고 프로파일 이름만 반환한다.
   현재 config가 `before`이면 준비 중 중단된 경우로 보고 같은 `after`를 적용한다.
   둘 다 아니면 파일을 보존하고 `ValueError`를 낸다.
3. 새 준비라면 config 원문과 `profile_values`로 `after`를 만든다.
   TOML 오류와 프로파일 충돌은 파일을 쓰기 전에 검출한다.
4. 복원 기록을 `open("x")`로 먼저 만든 뒤 config를 쓴다. 처음 생기는 config도
   배타적으로 생성하고, 기존 파일은 원래 바이트와 같은지 다시 확인한 후 변경한다.
   쓰기 실패 시 복원 기록을 남겨 cleanup으로 정리할 수 있게 한다.
5. 정상 반환은 프로파일 이름 하나다. worker 호출과 Git stage/commit은 하지 않는다.

`cleanup(worktree, state)`는 같은 경로 검사를 적용하고 다음으로 구현한다.

1. state가 없으면 아무것도 하지 않는다.
2. 기록의 worktree/필드 타입을 확인하고, 현재 config가 `after` 또는 `before`일 때만
   정리한다. 다른 내용이면 config와 기록을 모두 남기고 오류를 낸다.
3. `before is None`이면 직접 생성한 config를 삭제한다. 아니면 원래 바이트를 복원한다.
   `before == after`인 기존 프로파일 재사용은 config를 다시 쓰지 않는다.
4. 복원이 성공한 뒤 state를 삭제한다. 직접 만든 `.grok` 디렉터리는 비어 있을 때만 지운다.

이 비교는 정상적인 단일 컨트롤러 실행의 변경 보존용이다. 동시 악성 파일 변경까지
막는 보안 경계라고 주장하거나 이를 위해 잠금 서버를 만들지 않는다.

CLI는 다음 코드로 연결한다. 위 인터페이스의 `prepare`, `cleanup`은 같은 파일에서 정의한다.

```python
import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("prepare", "cleanup"))
    parser.add_argument("--worktree", required=True, type=Path)
    parser.add_argument("--state", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.action == "prepare":
            result = {"profile": prepare(args.worktree, args.state)}
        else:
            cleanup(args.worktree, args.state)
            result = {"cleaned": True}
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"BLOCKED: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: 보존 경계와 CLI를 회귀 검사에 추가**

위 테스트 클래스에 다음 CLI 검사를 추가한다.

```python
    def test_cli_failure_has_no_success_json(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "prepare",
             "--worktree", str(self.base), "--state", str(self.state)],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertTrue(result.stderr.startswith("BLOCKED:"))
```

같은 fixture에서 다음 입력/결과를 subtest로 검사한다. 본문의 테스트 코드를 재사용하되
정상 fixture의 `.grok`과 state는 각 사례 후 정리하여 사례가 서로 영향을 주지 않게 한다.

| 입력 | 필수 결과 |
| --- | --- |
| 일반 checkout `self.repo`, 그 안의 별도 evidence 경로 | 프로파일 `read_write == []`, cleanup 후 생성 파일 없음 |
| 기존 프로파일이 정확히 `profile_values(self.wt)`와 동일 | 원문 불변, cleanup 후에도 기존 프로파일 존재 |
| 같은 이름에 `restrict_network` 등 추가 필드 존재 | prepare 실패, 원문 불변 |
| config 또는 `.grok`이 외부 sentinel을 가리키는 symlink | prepare/cleanup 거절, sentinel 바이트 불변 |
| state가 다른 worktree를 기록하거나 예상 필드 타입이 아님 | cleanup 거절, config 불변 |
| state가 기록됐지만 config가 아직 `before` | cleanup이 원문을 유지하고 기록만 정리 |
| cleanup을 두 번 호출 | 두 번째도 성공, 기존 파일 불변 |
| 공백이 포함된 worktree 경로 | prepare, cleanup 성공; 위 기본 fixture가 이를 포함 |

`testing.md`에는 이 검사가 실제 Git 경로와 파일 보존을 검증하며, Grok sandbox 실행
성공을 입증하지 않는다고 적는다.

- [ ] **Step 6: 집중 검사 후 커밋**

```bash
python3 -m unittest discover -s tests/products/sddx -p test_prepare_grok_sandbox.py -v
git add skills/sddx/scripts/prepare_grok_sandbox.py tests/products/sddx/test_prepare_grok_sandbox.py docs/maintainers/products/sddx/testing.md
git diff --cached --check
git commit -m "fix: prepare Grok sandbox for linked worktrees"
```

예상: 모든 집중 검사 exit 0. 제품 실제 실행 성공은 아직 주장하지 않는다.

### Task 2: 기존 dispatch와 worker 완료 조건 연결

**Files:**
- Modify: `skills/sddx/scripts/resolve_backend.py`
- Modify: `skills/sddx/SKILL.md`, `skills/sddx/references/dispatch.md`, `skills/sddx/references/worker-prompt.md`
- Modify: `tests/products/sddx/test_resolve_backend.py`, `tests/products/sddx/test_contract.py`, `tests/products/sddx/cases.json`
- Modify: `docs/maintainers/products/sddx/contract.md`, `compatibility.md`, `release.md`
- Modify: `skills/sddx/README.md`, `README.en.md`, `release.toml`, `CHANGELOG.md`

**Interfaces:**
- Consumes: Task 1 CLI `prepare|cleanup --worktree PATH --state PATH`, 위에서 정의한 JSON/exit 계약.
- Consumes: 기존 resolver JSON의 `available`, `reason`, `argv_prefix`.
- Produces: resolver JSON 필드 유지; Grok의 `--sandbox`, `--rules`, `--disable-web-search`를 필수 플래그로 검사.
- Produces: 준비된 프로파일을 사용하고 종료 후 정리하는 dispatch 지시; 새 public 옵션 없음.

- [ ] **Step 1: 필수 플래그 누락 검사를 먼저 작성하고 RED 확인**

`test_resolve_backend.py`의 정상 `GROK_HELP`에 `--rules <RULES>`를 추가한다.
기존 `GROK_HELP_WITHOUT_CWD`도 나머지 필수 플래그는 포함시킨다.
`ResolveBackendTests`에 아래 메서드를 추가한다.

```python
    def test_required_execution_flags_cannot_be_missing(self):
        module = self._load()
        for flag in ("--rules", "--sandbox", "--disable-web-search"):
            help_text = "\n".join(
                line for line in GROK_HELP.splitlines() if flag not in line
            )
            with self.subTest(flag=flag):
                _write_cli(self.bindir, "grok", GROK_VERSION, help_text)
                with mock.patch.dict(os.environ, self._path(), clear=False):
                    result = module.resolve("grok")
                self.assertFalse(result["available"])
                self.assertEqual(result["reason"], "missing_flags")
```

```bash
python3 -m unittest discover -s tests/products/sddx -p test_resolve_backend.py -v
```

예상: 현재 resolver가 세 플래그 누락을 허용하여 새 검사 실패.

- [ ] **Step 2: resolver를 필요한 만큼만 수정**

기존 `_grok_flags_ok`의 and 조건에 아래 세 조건을 추가한다.
검사를 통과한 Grok argv에는 `--sandbox workspace`를 항상 넣는다.
실제 프로파일 준비와 이름 교체는 dispatch 단계 책임이다.

```python
required_execution_flags = ("--sandbox", "--rules", "--disable-web-search")
has_execution_flags = all(flag in help_text for flag in required_execution_flags)
```

위 `has_execution_flags`를 기존 신원/필수 플래그 판정과 결합한다.
resolver가 파일을 쓰거나 worker를 띄우게 만들지 않는다. Cursor 분기는 그대로 둔다.

- [ ] **Step 3: dispatch 문서를 실제 호출 순서로 수정**

기존 worker 실행 직전에, Grok backend인 경우에만 아래 명령을 호출한다.
`<skill-root>`, `<worktree>`, `<evidence-dir>`는 이미 SDD에서 확인한 절대 경로다.
실행 문서의 경로 자리표시는 사용자에게 추가 입력을 받으라는 뜻이 아니다.

```text
python3 "<skill-root>/scripts/prepare_grok_sandbox.py" prepare --worktree "<worktree>" --state "<evidence-dir>/grok-sandbox.json"
```

prepare 실패 시 worker를 시작하지 않는다. 성공 JSON을 읽은 뒤 아래와 같이
`argv_prefix`의 기존 sandbox 값 하나를 바꾼다. `--sandbox`를 중복 추가하지 않는다.

```python
argv = list(resolved["argv_prefix"])
sandbox_index = argv.index("--sandbox")
argv[sandbox_index + 1] = prepared["profile"]
argv.extend(["--cwd", str(worktree), "--rules", worker_rules])
```

`resolved`는 resolver JSON, `prepared`는 prepare JSON,
`worker_rules`는 `worker-prompt.md` 전체 텍스트다.
기존 effort, prompt, resume 인자는 현재 dispatch 규칙으로 계속 조합한다.

worker와 그 실행 중인 작업이 종료된 것을 확인한 뒤, 성공/실패와 관계없이 정리한다.
종료 전 cleanup을 실행하거나 살아 있는 프로세스 위에 새 worker를 겹쳐 실행하지 않는다.

```text
python3 "<skill-root>/scripts/prepare_grok_sandbox.py" cleanup --worktree "<worktree>" --state "<evidence-dir>/grok-sandbox.json"
```

정리 실패는 다른 파일을 덮어써 해결하지 않고 남은 차이와 기록 위치를 ledger에 알린다.
새 task와 resume 모두 같은 준비/호출/종료/정리 순서를 쓴다.

- [ ] **Step 4: worker 지시와 완료 조건을 짧은 본문으로 반영**

`worker-prompt.md`의 핵심 문장을 다음으로 정리하고 기존 비밀·push 금지 조건을 유지한다.

```text
Read the task brief first. Follow applicable repository instructions and read
source files needed for this task. Do not reopen the full implementation plan
or read or invoke external skills, including Superpowers. Do not spawn
subagents or reviewers, call MCP tools, or create another worktree.

Implement, test, and commit only this task, then write the report. Stage
explicit task paths only. Do not stage .grok/sandbox.toml or SDD evidence.
Report the actual test commands and exit codes, commit SHA, and any blocker.
Return NEEDS_CONTEXT when the brief lacks a required decision.
Return BLOCKED when a required test or commit cannot be completed.
```

`SKILL.md`에는 기존 report/review 절차에 연결되는 다음 완료 규칙만 추가한다.

```text
Process exit 0 is not task completion. Read the worker report and verify
test results, committed task changes, and native review before marking the
task complete. BLOCKED, NEEDS_CONTEXT, a missing report, or an unclear result
must not become DONE. Resolve DONE_WITH_CONCERNS through the existing ruling
procedure. Do not require a new commit for a verification-only response.
```

프로파일 준비·정리는 implementer dispatch의 일부라고 제품 계약에 명시한다.
스킬/MCP 제한은 프롬프트 지침이며, 초기화 경고가 없다는 보장이 아님을 유지한다.

- [ ] **Step 5: 사례·제품 문서·버전 갱신 후 GREEN 확인**

`cases.json`의 cases 끝에 아래 항목을 추가하고, `test_contract.py`의 `CASE_IDS`에
같은 순서로 ID를 추가한다. 기존 항목을 삭제하거나 목록 검사를 느슨하게 만들지 않는다.

```json
[
  {"id":"grok-linked-worktree-profile","request":"dispatch Grok in a linked worktree","expect":["prepare_profile","replace_sandbox_value","cleanup_after_worker_exit"]},
  {"id":"exit-zero-blocked-is-not-done","request":"worker process exits 0 but report says BLOCKED","expect":["not_done","inspect_blocker"]},
  {"id":"missing-report-is-not-done","request":"worker exits 0 without a report","expect":["not_done"]},
  {"id":"worker-brief-only-no-skills","request":"worker sees installed Superpowers while implementing its brief","expect":["no_external_skills","no_full_plan","no_mcp_tools"]}
]
```

`test_contract.py`에 추가할 문서 연결 검사 예시는 다음과 같다.
이 검사는 문서 연결을 잠그는 용도이며 모델 행동을 증명하지 않는다.

```python
    def test_dispatch_prepares_and_cleans_grok_profile(self):
        text = (SKILL / "references/dispatch.md").read_text(encoding="utf-8")
        self.assertIn("prepare_grok_sandbox.py", text)
        self.assertIn("--state", text)
        self.assertIn("cleanup", text)
        self.assertIn("--rules", text)
```

README 두 언어에는 Grok 경로의 Python 3.11+ 요구, 작업용 Git 쓰기 프로파일,
생성 설정 제외·정리 동작을 짧게 설명한다. 설치 링크 코드 블록은 바꾸지 않는다.
`compatibility.md`에는 공용 Git 디렉터리 권한과 프롬프트 제한의 한계를 적고
실제 수정본 라이브 결과는 Task 3에서 관측한 뒤 기록한다.

`release.toml`과 `SKILL.md metadata.version`을 `1.0.1`로 맞춘다.
`CHANGELOG.md`에 커밋 실패 수정과 완료 판정 변경을 기록하고 `release.md`의 버전을 맞춘다.
날짜는 실제 구현일을 사용한다. 태그나 Release는 만들지 않는다.

```bash
python3 scripts/verify.py --skill sddx
git add skills/sddx/scripts/resolve_backend.py skills/sddx/SKILL.md skills/sddx/references/dispatch.md skills/sddx/references/worker-prompt.md tests/products/sddx/test_resolve_backend.py tests/products/sddx/test_contract.py tests/products/sddx/cases.json docs/maintainers/products/sddx/contract.md docs/maintainers/products/sddx/compatibility.md docs/maintainers/products/sddx/release.md skills/sddx/README.md skills/sddx/README.en.md skills/sddx/release.toml skills/sddx/CHANGELOG.md
git diff --cached --check
git diff --cached --stat
git commit -m "fix: connect sandbox preparation and worker completion checks"
```

stage 전에 위 소유 경로에 기존 사용자 변경이나 증거 파일이 섞이지 않았는지 확인하고,
있으면 이 task가 변경한 파일만 정확히 stage한다. 예상: 제품 검사 exit 0.

### Task 3: 행동 검증과 실제 Grok 재검증

**Files:**
- Create: `tests/products/sddx/behavior-probes.md`
- Modify: `docs/maintainers/products/sddx/testing.md`, `compatibility.md`
- Modify: `skills/sddx/README.md`, `README.en.md` — 실제 관측한 실행 범위만 갱신
- Local only: 새 fixture의 `.superpowers/sdd/` 아래 report, 로그, 테스트 결과

**Interfaces:**
- Consumes: Task 1 helper CLI와 Task 2의 최종 SDDx dispatch/worker 계약.
- Produces: 공급자 없는 전체 검사 결과, 행동 검증 판정, 실제 커밋·resume 수정 증거.
- 라이브 범위: 새 로컬 fixture, Grok 기본 3회 호출(첫 task, 같은 세션 수정, 둘째 task).
  결함 수정 재검증은 최대 2회 추가한다. 공급자·호스트 전환이나 다른 프로젝트 호출은 없다.
- 이 범위를 포함한 실행 승인이 있어야 실제 호출한다. 이 계획 작성 자체는 호출 승인이 아니다.

- [ ] **Step 1: 행동 probe 문서 작성**

`behavior-probes.md`에 아래 표와 실행 방식을 기록한다. writing-skills의 검증 절차로
각 시나리오에 독립된 문맥을 제공하고 다음 행동을 답하게 한다. 기존 결과 문구를
읽고 따라 쓰게 하지 않는다. 판정은 컨트롤러가 실제 응답을 읽고 수행한다.

| 입력 상황 | 통과 조건 |
| --- | --- |
| worker exit 0, report BLOCKED, commit 없음 | task 미완료 유지, 원인 확인; 자동 커밋·backend 전환 없음 |
| worker exit 0, report 파일 없음 | 완료 표시 없음; 결과 확인 요청/실패 처리 |
| worker DONE, 테스트 비0 또는 변경 미커밋 | 리뷰 통과나 완료로 승격하지 않음 |
| 역할이 worker이고 Superpowers 사용을 권하는 사용자 스킬이 노출됨 | 적용 가능한 저장소 지침은 따르며 external skill 호출 없이 brief 수행 |
| sandbox 준비 실패 | worker 실행과 sandbox 해제 없이 구체적 원인 보고 |
| fix 1–3회와 4회 | 기존 세션 재개 후, 4회에서 fresh XHigh 전환; 설계 모호함은 ruling |

문서 문자열 검사를 행동 probe 통과로 집계하지 않는다.
이 단계에서 spawn되는 native probe와 실제 외부 provider 호출을 결과에서 구분한다.

- [ ] **Step 2: 전체 로컬 검사 완료 확인**

```bash
python3 scripts/verify.py
git diff --check
```

완료한 프로세스의 exit code를 기록한다. 진행 중 출력이나 테스트 수만으로 통과를 선언하지 않는다.
이후 제품 코드 변경이 없으면 같은 전체 검사를 반복하지 않는다.

- [ ] **Step 3: 새 throwaway fixture를 준비하고 첫 worker 커밋 확인**

기존 smoke 저장소와 기록을 재사용하거나 덮어쓰지 않는다. 새로운 임시 로컬 Git 저장소와
linked worktree를 만들고 remote는 추가하지 않는다. 정상 동작 중인 다른 작업은 건드리지 않는다.
초기 fixture에는 spec, plan, `.gitignore`만 커밋하고 애플리케이션 구현은 worker에게 맡긴다.
`.gitignore`에는 `.worktrees/`, `.superpowers/`, `__pycache__/`, `*.pyc`를 넣는다.

fixture의 승인 범위는 다음 두 task다.

| Task | worker가 만들 파일 | 요구사항 |
| --- | --- | --- |
| 1 | `textnorm.py`, `tests/test_textnorm.py` | `normalize_text(value: str) -> str`; Unicode whitespace를 한 칸으로 정리; 비문자열 TypeError; 빈 문자열 허용 |
| 2 | `normalize_cli.py`, `tests/test_cli.py`, `README.md` | 위치 인자 정확히 하나; 정상 출력은 정규화 결과+LF; 인자 누락/초과 exit 2; `--help` 성공 |

현재 설치된 CLI의 `--version`, `--help`와 수정본 resolver를 확인한 뒤 Grok을 명시하여
수정본 SDDx를 실행한다. 호출마다 session ID와 Git 기준 SHA를 기존 ledger에 기록한다.
표준 prepare/dispatch/cleanup을 사용하고, 첫 worker가 실제로 커밋할 때까지 Task 2로 넘어가지 않는다.
`--sandbox workspace`로 되돌리거나 컨트롤러가 커밋을 보조해 결과를 통과시키지 않는다.
오류가 남으면 실제 상태와 원인을 기록하고 해당 task를 미완료로 남긴다.

- [ ] **Step 4: 같은 세션에서 실제 수정과 재검토 확인**

첫 task의 native 리뷰에서 실제 지적이 나오면 그 지적을 동일 세션에 전달한다.
지적이 없으면 검증용 추가 요구를 사용한다: 비문자열 TypeError 메시지를
`normalize_text expects a string (sddx review probe)`로 명시하고 이를 검사하는 테스트를 추가하게 한다.
이 경우 원래 구현의 결함을 발견한 것으로 표현하지 않고, 통제된 수정 요청에 대한 resume 검증으로 기록한다.

실제 worker가 코드·테스트를 수정하고 커밋했는지, session ID가 유지됐는지 확인한다.
수정 결과는 native reviewer가 다시 검토한다. Task 2는 다른 새 session ID로 실행한다.
프롬프트가 아니라 실제 tool trace에서 금지된 스킬/전체 계획 읽기, nested agent,
MCP 도구 호출 여부를 확인한다. 초기화 경고는 도구 호출과 별도로 기록한다.

- [ ] **Step 5: 최종 독립 검사와 설정 보존 확인**

fixture worktree에서 아래 명령을 실행한다.

```bash
python3 -m unittest discover -s tests -v
git status --short
git log -3 --oneline
```

추가로 각 task의 기준/결과 SHA로 `git diff --check BASE HEAD`와 변경 파일 목록을 확인한다.
여기의 BASE/HEAD는 ledger에 기록된 실제 SHA를 argv로 전달한다.
생성 sandbox와 evidence가 구현 커밋에 포함되지 않았는지, cleanup 뒤 사용자 설정 원문이
유지됐는지 확인한다. 범위 전체를 native 최종 reviewer에게 제공한다.

- [ ] **Step 6: 관측 결과만 문서화하고 검증 기록 커밋**

`testing.md`에는 재현 절차와 실제 exit code, 측정 환경, 기본 실행 성공/실패,
실제 리뷰 결함 수정인지 통제된 resume 수정인지 기록한다.
`compatibility.md`와 README의 실행 상태도 같은 증거 범위로 맞춘다.
Cursor/Claude Code를 실행하지 않았다면 `not_measured`를 유지한다.
raw provider 이벤트·호스트 경로·receipt는 ignored evidence에만 두고 제품 문서에는 요약만 남긴다.

실패를 문서화했어도 기능 완료로 취급하지 않는다. 이 계획의 완료 기준은 원본 계약대로
worker가 커밋한 라이브 증거와 회귀 검사 통과이며, 라이브 미실행이면 그 부분은 미검증이다.

```bash
git add tests/products/sddx/behavior-probes.md docs/maintainers/products/sddx/testing.md docs/maintainers/products/sddx/compatibility.md skills/sddx/README.md skills/sddx/README.en.md
git diff --cached --check
git commit -m "test: document SDDx worktree and resume verification"
```

문서만 바뀌었다면 내용·링크·diff를 검사한다. 실행 중 발견한 결함으로 제품 코드를
수정했다면 해당 회귀 검사와 필요한 전체 검증을 다시 실행한다.

## 계획 자기 검토

| 설계 요구 | 연결 작업 |
| --- | --- |
| Git 경로 계산, 프로파일 구성, 기존 설정 보존·정리 | Task 1 |
| resolver 읽기 전용, 필수 플래그, 기존 argv 값 교체 | Task 2 |
| brief 중심 worker 역할, 기존 report 기반 완료 조건 | Task 2 |
| 제품 문서·버전·지원 범위 일치 | Task 2, 관측 결과는 Task 3 |
| 실제 Git 회귀, 불명확한 완료 상태, 역할 이탈 probe | Task 1–3 |
| worker 직접 커밋, 같은 세션 수정, 새 task 세션, 최종 리뷰 | Task 3 |

제품 구현과 라이브 호출은 아직 수행하지 않았다. 계획의 코드 블록은 구현 지침이며
통과 증거가 아니다. 위의 각 task는 구현·검증·리뷰가 끝난 후에만 체크한다.
