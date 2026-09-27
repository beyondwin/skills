# waygent 계약

이 문서는 waygent가 무엇을 소유하고, 언제 켜지고, 과제를 어떻게 돌리는지 정하는
규범입니다. 런타임 원본은 `skills/waygent/SKILL.md`이고, 이 문서는 그 가운데
테스트가 잠그는 약속만 적습니다. 동작을 바꾸기 전에 이 문서와 맨 아래 「함께 고칠
파일」을 확인하세요.

## 용어

| 말 | 뜻 |
| --- | --- |
| 호스트 | 스킬을 실행하는 프로그램입니다. `claude-code`, `codex`, `cursor`(Cursor Agent)입니다. |
| 컨트롤러 | `/waygent` 또는 `$waygent`를 받은 호스트 세션입니다. 코드를 쓰지 않고 과제를 보내고, 확인하고, 진행 파일을 적습니다. |
| 구현 서브에이전트 | 과제 하나를 맡는 새 서브에이전트입니다. |
| 가이드 파일 | `guide.md`. 명령과 계획 전체 규칙을 한 번 적어 모든 구현 서브에이전트가 읽습니다. |
| 진행 파일 | `progress.md`. 과제별 상태입니다. 커밋하지 않습니다. |

## 제품 정체

제품 ID, 스킬 `name`, 디렉터리 이름은 `waygent`입니다. 표시 이름은 `Waygent`입니다.
호출은 `/waygent [plan-file|request]`(Codex는 `$waygent [plan-file|request]`)이며,
메시지에 `/waygent`나 `$waygent`가 없으면 켜지지 않습니다. `agents/openai.yaml`은 `allow_implicit_invocation: false`입니다.

description은 `/waygent` 또는 `$waygent`로 켜지고, 가까운 요청(`/sddx`, Superpowers
`subagent-driven-development`, 브레인스토밍·스펙·계획 작성, 작은 수정 하나)을
제외한다고 적어야 합니다.

## 실행 약속

- 상태는 저장소 최상위 `.waygent/<plan-slug>/` 아래 `progress.md`, `guide.md`,
  `reviews/`에 둡니다. `.waygent/.gitignore`(`*`)로 커밋되지 않게 하고, 사용자
  `.gitignore`는 고치지 않습니다. 진행 파일이 없어도 트레일러 커밋에서 다시 만듭니다.
- 과제마다 새 구현 서브에이전트 하나. 동시에 둘을 띄우지 않습니다.
- 테스트를 먼저 쓰고 실패를 본 뒤 구현합니다(TDD).
- 과제 커밋에는 `Waygent-Task: N` 트레일러가 붙습니다. 재개할 때 HEAD에서 닿는
  트레일러 커밋이 있는 과제만 끝난 것으로 보고, 진행 파일을 그에 맞춥니다.
- 리뷰는 과제마다 한 번, 수정은 한 번이며 다시 리뷰하지 않습니다(no re-review).
- 마지막에 전체 리뷰를 한 번만 합니다.
- 실패하면 원인을 먼저 적고 한 번 다시 시도합니다. 두 번째 실패에서 멈춥니다.
- 구현 서브에이전트와 과제별 리뷰어는 컨트롤러와 같은 모델을 씁니다. 더 싼 모델이나
  낮은 effort로 바꾸지 않습니다. 호스트가 모델을 고를 수 있으면 최종 리뷰어와 실패 뒤
  재시도 구현자만 한 등급 위 모델을 씁니다. Codex는 모델 이름을 적지 않아 세션 모델을
  물려받게 하고, 한 등급 위는 `reasoning_effort`만 `xhigh`로 적습니다. 2026-09-27 실측에서
  Codex 조율자가 자기 모델을 잘못 알고 다른 모델을 적은 일이 있어서입니다.
- `main`, `master`에 커밋하지 않습니다. push, merge, PR은 요청이 없으면 하지 않습니다.
- `SKILL.md`는 140줄 미만입니다. 가벼움이 계약입니다.

## 일부러 빼는 것

브레인스토밍·스펙·설계 단계, 과제별 브리프·diff·보고서 파일, 재리뷰 반복, 구현
서브에이전트 병렬 실행과 worktree 풀, 과제마다 사람 확인. 이 선택의 근거는
[`docs/research/`](../../../research/README.md)의 하네스 비교 조사와 진행 중인 평가입니다.

## 함께 고칠 파일

- `skills/waygent/SKILL.md`, `release.toml`, `CHANGELOG.md`, `README.md`, `README.en.md`
- `tests/products/waygent/test_contract.py`
- 이 디렉터리의 `testing.md`, `compatibility.md`, `release.md`
- 호스트가 바뀌면 `products.toml`, 공유 호환성 문서, 저장소 테스트
