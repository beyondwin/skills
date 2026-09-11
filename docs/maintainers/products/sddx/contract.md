# sddx 계약

이 문서는 SDDx의 제품 정체, 오케스트레이터 호스트, implementer backend
해석을 소유합니다.

## 제품 정체

제품 ID, 스킬 `name`, 디렉터리 이름은 `sddx`입니다. 표시 이름은 `SDDx`입니다.
슬래시 호출은 Claude Code `/sddx`, Codex `$sddx`입니다.

지원 호스트는 `claude-code`와 `codex`뿐입니다. Cursor CLI와 Grok CLI는
구현 worker이지 호스트가 아닙니다. `cursor`와 `grok`을 `supported_hosts`에
넣지 않습니다.

Superpowers SDD는 worktree, ledger, task-brief, review-package, 리뷰어
프롬프트, fix loop, whole-branch review를 소유합니다. `sddx`는 인자 해석,
backend picker, `resolve_backend.py`, implementer argv, worker 제약만
소유합니다. SDD 본문을 이 스킬에 복사하지 않습니다.

## 하드 게이트

설치된 Superpowers `subagent-driven-development`를 그대로 따르고, implementer
dispatch만 바꿉니다. Superpowers 파일을 고치지 않습니다. 오케스트레이터
세션에서 구현하지 않습니다.

명시적인 `/sddx` 또는 `$sddx`, 또는 명시적인 외부 implementer 요청이 없으면
네이티브 SDD, executing-plans, writing-plans, `pre-sdd-review`로는
활성화하지 않습니다.

## 호출과 picker

인자는 `sddx <plan-file> [cursor|grok|c|g]`입니다. plan 경로가 없거나 파일이
아니면 추측하지 않고 멈춥니다. 한 호출은 계획 하나입니다.

backend 인자가 있으면 picker를 생략합니다. `c`는 `cursor`, `g`는 `grok`입니다.
인자가 없으면 이 계획에서 한 번만 고릅니다. Claude Code는 AskUserQuestion,
Codex는 번호 있는 선택지를 한 번 묻고 답을 기다립니다. task마다 backend를
다시 묻지 않습니다. 고른 값은 ledger에 `Backend: cursor|grok`로 적고 그
plan의 모든 task에 유지합니다.

사용 가능한 backend가 하나뿐이어도 그 사실과 빠진 backend `reason`을 보여
주고, argv가 없으면 확인을 받은 뒤에만 진행합니다. 하나뿐이라고 자동
선택하지 않습니다.

요청한 backend가 없으면 다른 쪽으로 바꾸지 않고 멈춥니다. 둘 다 없으면
`BLOCKED`입니다.

## 리뷰어와 effort

task reviewer, scoped re-reviewer, 최종 리뷰어는 호스트 네이티브입니다.
Claude Code는 Task, Codex는 `spawn_agent`입니다. 구현 worker만 외부
프로세스입니다.

구현 effort는 기본 High입니다. 복잡한 동시성, race, 얽힌 부작용, 또는 이
task에서 High 리뷰가 이미 실패한 경우에만 XHigh입니다. 설계 모호함은
XHigh가 아니라 오케스트레이터 ruling입니다. worker가 `NEEDS_CONTEXT` 또는
`BLOCKED`를 반환하면 ruling한 뒤 같은 backend로 다시 보냅니다.

새 task는 새 worker입니다. fix 라운드 1–3은 같은 worker session을
resume합니다. 라운드 4–5는 fresh worker와 XHigh입니다. worker에
`--worktree`를 넘기지 않습니다. cwd는 현재 Superpowers worktree입니다.

## Worker 부작용과 비밀

호스트 자격 증명이나 환경 값을 worker prompt나 `--prompt-file`에 넣지
않습니다. worker가 push, publish, 공유 브랜치 갱신처럼 호스트 밖 부작용을
필요로 하면 멈추고 `BLOCKED`입니다. 그 결과를 리뷰 통과 DONE으로 쓰지
않습니다.

## Grok worktree 프로파일과 완료 판정

Grok implementer dispatch는 worker 실행 직전에 `prepare_grok_sandbox.py
prepare`를 호출하고, 반환된 작업용 프로파일로 resolver `argv_prefix`의 기존
`--sandbox` 값 하나를 교체합니다. worker prompt 전체를 `--rules`로 넘깁니다.
prepare가 실패하면 worker를 시작하지 않습니다.

worker와 worker가 실행한 작업이 종료된 뒤에는 성공과 실패 모두에서
`prepare_grok_sandbox.py cleanup`을 호출합니다. 새 task와 resume은 같은
준비·실행·종료·정리 순서를 씁니다. 정리 실패 시 다른 파일을 덮어쓰지 않고
남은 차이와 상태 기록 위치를 ledger에 남깁니다. 생성 설정과 복원 상태는 제품
산출물이나 커밋 대상이 아닙니다.

프로세스 exit 0만으로 task를 완료 처리하지 않습니다. worker report의 테스트
결과, task 변경 커밋, 네이티브 리뷰를 확인해야 합니다. `BLOCKED`,
`NEEDS_CONTEXT`, 보고서 누락, 불명확한 결과는 `DONE`이 아닙니다.
`DONE_WITH_CONCERNS`는 기존 ruling 절차로 처리하며, 검증만 한 응답에는 새
커밋을 요구하지 않습니다.

## Backend 해석

컨트롤러는 로드된 스킬 루트에서 `scripts/resolve_backend.py`를 실행합니다.
네트워크를 쓰지 않고 worker를 띄우지 않습니다. 성공 시 stdout은 JSON 한
객체와 LF입니다. 없는 backend는 종료 코드 0과 `available: false`입니다.
잘못된 인자만 비0입니다. 종료 코드만으로 다른 backend를 고르지 않습니다.

Grok 후보는 PATH의 `grok`뿐입니다. `agent`는 Grok 후보가 아닙니다. Cursor
후보는 `cursor-agent`, 그다음 신원이 Cursor Agent CLI인 `cursor`입니다.
`agent`는 Cursor 후보가 아닙니다. Grok Build 신원을 Cursor로 채택하지
않습니다.

Grok resolver는 `--sandbox`, `--rules`, `--disable-web-search`를 포함한 필수
실행 플래그를 확인하고, 기본 `argv_prefix`에 `--sandbox workspace`를 넣습니다.
resolver 자체는 파일을 쓰거나 worker를 시작하지 않습니다.

## 함께 고칠 파일

동작 변경을 한 파일에만 넣지 마세요.

- 호스트 또는 backend 정체: `products.toml`, 이 계약, 제품 README, 공개
  호환성 안내, `tests/products/sddx/`
- 활성화·picker·하드 게이트: `skills/sddx/SKILL.md`,
  `skills/sddx/references/dispatch.md`,
  `skills/sddx/references/worker-prompt.md`,
  `tests/products/sddx/cases.json`, `tests/products/sddx/test_contract.py`
- `resolve_backend.py` 신원·플래그 규칙: `skills/sddx/scripts/resolve_backend.py`,
  `tests/products/sddx/test_resolve_backend.py`
- 버전과 설치 파일: `skills/sddx/release.toml`, `SKILL.md`, `CHANGELOG.md`
