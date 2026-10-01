# Waygent

[English](README.md)

## 목적

구현 계획을 끝까지 맡기는 가벼운 스킬입니다. 과제마다 새 서브에이전트가 테스트부터
쓰고 구현합니다. 과제마다 리뷰가 한 번 있고, 끝에 전체 리뷰를 한 번 합니다. 메인 세션은
직접 코드를 쓰지 않고 일을 나눠 주고 확인만 해서, 컨텍스트가 작게 유지됩니다.

```text
/waygent docs/plan.md
  │
  ├─ Task 1 ─ 구현자(새 서브에이전트): 실패하는 테스트 → 구현 → 커밋
  │           리뷰어: 한 번 보고 High·Medium만 한 번 고침 (재리뷰 없음)
  ├─ Task 2 ─ …
  │
  └─ 끝 ───── 전체 리뷰 한 번(한 등급 위 모델) → 고침 → 앱 확인 → 테스트 → 15줄 보고
```

이렇게 만든 이유는 실측입니다. 10-Task 과제로 스킬 없는 세션, superpowers, waygent를
격리해 비교했습니다([설계와 실측](https://github.com/beyondwin/skills/blob/main/docs/research/2026-09-waygent-eval/README.md)).

- 요즘 모델은 혼자서도 대부분 맞힙니다. 그래서 규칙은 모델이 혼자 틀리는 곳에만 넣었습니다.
- 한 세션이 혼자 구현하면 숨은 상태 결함을 5번 모두 남겼습니다. 과제마다 새 구현자와
  리뷰를 두면 14번 중 11번 고쳤습니다.
- superpowers와 품질은 같았고, 비용과 시간은 절반 이하였습니다.

| 말 | 뜻 |
| --- | --- |
| 메인 세션 | `/waygent`를 받은 세션입니다. 일을 나눠 주고, 결과를 확인하고, 기록을 남깁니다. |
| 구현자 | 과제 하나만 맡는 새 서브에이전트입니다. 테스트를 먼저 쓰고 커밋까지 합니다. |
| 리뷰어 | 과제의 diff를 한 번 보고 High·Medium·Low로 지적하는 새 서브에이전트입니다. |

## 사용할 때와 사용하지 않을 때

- 쓸 때: 과제가 여러 개인 구현을 맡길 때입니다. 메시지에 `/waygent`(Codex는
  `$waygent`)를 적어야만 켜집니다. 계획 파일이 없으면 요청으로 과제 목록을 만들고 한 번
  확인받습니다.
- 쓰지 않을 때: 아이디어 정리, 설계·스펙·계획 작성, 작은 수정 하나. `/sddx`나
  Superpowers `subagent-driven-development`를 쓸 때도 쓰지 않습니다.

## 지원 호스트

waygent: Claude Code, Codex, Cursor Agent, and Grok Build supported for local or repository-based use.

| 호스트 | 호출 | 설치 위치 | 서브에이전트 |
| --- | --- | --- | --- |
| Claude Code (`claude-code`) | `/waygent` | `~/.claude/skills/waygent` | Agent 도구 |
| Codex (`codex`) | `$waygent` | `~/.agents/skills/waygent` | `spawn_agent`. `~/.codex/config.toml`에 `[features]` `multi_agent = true`가 있어야 함 |
| Cursor Agent (`cursor`) | `/waygent` | `~/.cursor/skills/waygent` | Task 도구 |
| Grok Build (`grok`) | `/waygent` | 위 세 링크 중 아무거나; 따로 걸 필요 없음 | `spawn_subagent` |

- macOS에서, Git 저장소 안에서만 씁니다.
- 호스트별 실측 기록은 [호환성](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/waygent/compatibility.md)에 있습니다.
  공통 한계는 [호환성 안내](https://github.com/beyondwin/skills/blob/main/docs/users/ko/compatibility.md)를 보세요.

## 설치

저장소를 받고, 쓰는 호스트마다 바로가기(심볼릭 링크)를 하나씩 만듭니다.

```bash
git clone https://github.com/beyondwin/skills.git
cd skills
mkdir -p ~/.claude/skills ~/.agents/skills ~/.cursor/skills
```

아래 블록이 링크 하나를 만듭니다. 이미 같은 링크가 있으면 그대로 두고, 다른 파일이나
링크가 있으면 건드리지 않고 멈춥니다.

<!-- waygent-local-links -->
```python
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
```

실행할 때 첫 줄만 호스트에 맞게 바꿉니다. 그다음 줄부터 위 블록을 붙이고, 마지막 줄에
`PY`만 적습니다.

- Claude Code: `python3 - "$PWD/skills/waygent" "$HOME/.claude/skills/waygent" <<'PY'`
- Codex: `python3 - "$PWD/skills/waygent" "$HOME/.agents/skills/waygent" <<'PY'`
- Cursor Agent: `python3 - "$PWD/skills/waygent" "$HOME/.cursor/skills/waygent" <<'PY'`

링크라서 저장소를 `git pull`하면 바로 최신이 됩니다. 지울 때는 확인한 뒤 링크만 지웁니다.

```bash
ls -ld ~/.claude/skills/waygent ~/.agents/skills/waygent ~/.cursor/skills/waygent
unlink ~/.claude/skills/waygent
unlink ~/.agents/skills/waygent
unlink ~/.cursor/skills/waygent
```

공개 경로는 아래와 같습니다. Codex에서도 `~/.codex`에 복사본을 만들지 말고, 위의
`~/.agents/skills` 링크를 쓰세요.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/waygent
```

더 자세한 링크 안내는 [로컬 링크](https://github.com/beyondwin/skills/blob/main/docs/users/ko/install-local.md)에 있습니다.

## 첫 호출

```text
/waygent docs/plan.md
$waygent docs/plan.md
/waygent 로그인 폼에 비밀번호 표시 버튼을 추가해 줘
```

- 계획 파일이 있으면 그 과제 순서대로 돌고, 없으면 과제 목록부터 보여 줍니다.
- 중간에 끊겼으면 같은 명령을 다시 부르세요. 끝난 과제는 건너뜁니다.
  `/waygent`만 부르면 끝나지 않은 실행 하나를 이어 가고, 여러 개면 한 번 묻습니다.
- 끝난 실행은 보고만 합니다. 새 일은 새 `/waygent <요청>`으로 부르세요.
- 계획에 테스트 명령과 지켜야 할 규칙이 적혀 있을수록 결과가 좋습니다.

## 예상 결과

**git**
- `main`이나 `master`에 있으면 `waygent/<계획이름>` 브랜치를 먼저 만듭니다.
- 과제마다 저장소 커밋 형식으로 커밋이 하나 이상 생기고, 마지막 커밋 끝에 `Waygent-Task: N`이 붙습니다.
- push, merge, PR은 하지 않습니다.

**기록** (git에 안 잡힘)

```text
.waygent/
  .gitignore              # "*" 한 줄. 폴더 전체를 git에서 뺍니다.
  <계획이름>/
    progress.md           # 과제별 진행, 판단, 실패 원인
    guide.md              # 명령, 앱 실행 방법, 공통 규칙. 구현자가 먼저 읽습니다.
    reviews/task-N.md     # 리뷰어의 지적 전문
    reviews/final.md
```

**`progress.md` 모양**: 단계마다 한 줄씩 남고, 누가 했는지(`모델/effort`)도 적힙니다.
`inherit`는 메인 세션이 값을 정하지 않았다는 뜻입니다. 이때 한 등급 위 서브에이전트는
세션 값이 아니라 그 모델에 설정된 effort로 돌 수 있습니다. 머리의 `model:`은 세션 자신의
모델이고, effort는 정해져 있을 때만 붙습니다.

```text
model: opus/high
task 1: start base=3f2a1c0
task 1: low: usage/store.py:41 loop reads each row twice
task 1: done 8c1d2e4 impl=opus/inherit review=fixed 2 reviewer=opus/inherit tests=43 passed
task 2: start base=8c1d2e4
task 2: failure: suite red after commit — cause: stale import — next: fix the import
task 2: retry impl=fable/inherit
task 2: done 5b7a9d2 impl=fable/inherit review=clean reviewer=opus/inherit tests=45 passed
final: start
final: done 9e0f3a1 impl=opus/inherit reviewer=fable/inherit fixed=1 walk=ok tests=47 passed
```

리뷰 칸은 `clean`, `fixed K`, `overruled K`, `skipped (<이유>)`, `unknown`(기록을 잃고
다시 만든 경우) 중 하나입니다. `walk=none (<이유>)`는 앱을 확인하지 않은 이유를 적습니다.

**끝났을 때**: 15줄 이내로 보고합니다. 끝낸 과제와 커밋, 고치거나 기각한 지적, 마지막
테스트 결과, 확인하지 못한 것을 적습니다.

**문제가 생기면**
- 과제가 실패하면 원인을 한 줄 적고 한 번만 다시 시도합니다. 또 실패하면 멈추고 이유를
  보고합니다. 끝 수정 뒤 테스트가 깨져도 똑같이 합니다.
- 서브에이전트가 잠깐 요청 한도 오류(429)를 받으면 한 번 다시 보냅니다. 세션 자체가
  사용량 한도에 걸리면 `paused: limit`을 적고 멈춥니다. 다시 부르면 이어서 합니다.
- 중간에 끊기면 다시 부르세요. 이번 실행에서 커밋된 과제는 다시 하지 않고, 리뷰 전에
  끊긴 과제는 리뷰부터, 끊긴 끝 단계는 그 리뷰나 수정부터 이어 갑니다. 커밋 안 된 변경은
  버리지 않습니다. `.waygent/`가 지워졌으면 `/waygent`만 부르세요. 이번 실행의
  `Waygent-Task` 커밋으로 진행을 다시 만듭니다. 실행 도중 브랜치 기록이 바뀌었으면(예:
  squash) 멈추고 그렇게 알립니다.

**리뷰**
- 리뷰어의 High·Medium은 한 번 고칩니다. 메인 세션이 기각하려면 리뷰어가 준 재현을
  직접 돌려 코드가 맞게 도는 것을 봐야 합니다.
- Low는 기록만 합니다. 끝 리뷰가 참고하지만 자동으로 고치지는 않습니다.
- 배포 순서나 과금 정책처럼 저장소만으로 정할 수 없는 지적은 보고에 메모로 남겨 직접
  정하게 합니다.

**모델**
- 구현자와 과제별 리뷰어는 지금 세션과 같은 모델을 씁니다. 싼 모델로 내리지 않습니다.
- 끝 전체 리뷰와 실패 뒤 재시도만 한 등급 위를 씁니다. Claude Code는 sonnet → opus →
  fable 순이고, Codex는 같은 모델에 `reasoning_effort`만 `xhigh`로 올립니다. Cursor와
  Grok Build는 모델을 고를 수 없어 같은 모델을 씁니다.
- 서브에이전트는 리뷰어를 포함해 한 번에 하나만 돕니다. Claude Code에서는 서브에이전트가
  백그라운드로 돌 수 있고, 메인 세션은 그 끝을 기다립니다. 실행이 끝날 때까지 세션을 열어
  두세요. 닫혔으면 같은 명령을 다시 부르세요.

**앱 확인**: 구현자는 테스트만 돌리고, 앱 실행 방식을 바꾸는 과제일 때만 앱을 띄웁니다.
`guide.md`에는 앱 실행 방법이나 앱이 없는 이유가 적힙니다. 끝에 끝 수정 담당이 앱을 한 번
띄워 바뀐 흐름을 실제 데이터로 확인하고, 찾은 문제를 고치고, 앱을 끕니다.

**하지 않는 것**: 브레인스토밍·스펙 단계, 재리뷰 반복, 서브에이전트 병렬 실행, 과제마다 사람
확인, `CLAUDE.md`·`AGENTS.md` 수정.

**한계**: 고친 코드는 끝 리뷰에서만 다시 봅니다. 결과는 모델과 계획의 질에 달려 있습니다.

## 더 보기

- [설계와 실측](https://github.com/beyondwin/skills/blob/main/docs/research/2026-09-waygent-eval/README.md): 왜 이렇게 만들었는지, 숫자
- [CHANGELOG](CHANGELOG.md)
- [계약](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/waygent/contract.md) · [테스트](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/waygent/testing.md) · [호환성](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/waygent/compatibility.md) · [릴리스](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/waygent/release.md)
- [안전과 개인정보](https://github.com/beyondwin/skills/blob/main/docs/users/ko/safety-and-privacy.md)
