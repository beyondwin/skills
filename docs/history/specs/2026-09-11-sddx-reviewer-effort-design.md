# SDDx 리뷰어 모델 상속과 effort 승급 설계

날짜: 2026-09-11
대상 제품: `skills/sddx` (현재 1.0.1)
목표 버전: 1.1.0 (단일 릴리스, 1.0.2 없음)

## 문제

SDDx는 외부 implementer worker에만 effort 규칙을 둡니다.

> Effort for the implementer is High unless the task is hard implementation
> (concurrency, races, tangled side effects, or High already failed review
> on this task), then XHigh.

네이티브 리뷰어(task reviewer, scoped re-reviewer, whole-branch final reviewer)에는
대응 규칙이 없습니다. 1.0.1 라이브 검증에서 오케스트레이터는 리뷰어마다 *모델*만
골랐습니다(작은 리뷰는 Sonnet, 최종 whole-branch 리뷰는 Opus). Claude Code의 Agent
호출이 노출하는 유일한 조절 손잡이가 모델이기 때문입니다.

요구: 리뷰와 최종 리뷰도 오케스트레이터의 모델을 쓰고, effort를 난이도에 따라
High 또는 XHigh로 지정한다.

## 제약

Claude Code의 Agent 도구에는 호출별 `model` 인자가 있으나 **호출별 effort 인자가
없습니다.** `effort`(low|medium|high|xhigh|max)는 서브에이전트 *정의* 파일의 YAML
frontmatter 필드이며, 기본값은 세션 effort 상속입니다.

따라서 실제 effort 승급은 sddx가 에이전트 정의 파일을 함께 배포해야 가능합니다.

## 실증 (spike)

2026-09-11, Claude Code, macOS Darwin 25.5.0에서 대조군과 함께 확인한 뒤 흔적을
제거했습니다.

| 검사 | 결과 |
| --- | --- |
| 대조군: 프로젝트 `.claude/agents/nested/` 실디렉터리 | 발견됨 |
| 프로젝트 `.claude/agents/` 아래 심볼릭 링크 디렉터리 | 발견됨 |
| 사용자 `~/.claude/agents/` 아래 심볼릭 링크 디렉터리 | 발견됨 |
| `effort: xhigh`와 `disallowedTools` frontmatter | 거부 없이 파싱됨 |
| 별도 headless 세션에서 `subagent_type` dispatch | 동작함 |
| `.claude-plugin/plugin.json`을 가진 스킬 폴더의 `agents/` 번들 | 발견됨 |
| 그 스킬 폴더가 `~/.claude/skills/` 심링크일 때 | 발견됨 |
| `agents/claude-code/` 하위 디렉터리 | 발견됨 |
| 옆에 비-`.md` 파일(`openai.yaml`) 공존 | 무해 |
| 플러그인화 후 스킬 호출 이름 | 네임스페이스 없이 그대로 |

마지막 네 줄이 설계를 결정합니다. 기존 `~/.claude/skills/sddx` 심링크 하나가 정의
파일을 그대로 실어 나르므로 **새 설치 단계가 필요 없습니다.**

이 spike는 임시 프로브 파일로 한 것이고, 배포되는 제품 파일로 같은 경로를 확인한
것이 아닙니다. 제품 파일 기준 재확인은 구현 계획의 첫 단계입니다.

## 설계

### 전달 수단

- `skills/sddx/.claude-plugin/plugin.json` 추가.
- `skills/sddx/agents/claude-code/sddx-reviewer-xhigh.md` 추가.

기존 설치 링크 두 개는 그대로입니다. 설치 문서, 설치 블록, 설치 계약 테스트,
`products.toml`은 바뀌지 않습니다. 기존 사용자는 저장소를 갱신하면 다음 세션에
정의를 받습니다.

`agents/openai.yaml`은 Codex 표시 메타데이터로 남고, Claude Code 런타임 정의는
`agents/claude-code/` 아래에 둡니다. 두 호스트 산출물이 같은 디렉터리에서
충돌하지 않음은 spike에서 확인했습니다.

### 정의 파일

```yaml
---
name: sddx-reviewer-xhigh
description: SDDx XHigh 리뷰 승급 전용. SDDx 오케스트레이터가 명시적으로 띄웁니다.
effort: xhigh
disallowedTools: Edit, Write, NotebookEdit
---
```

- `model`을 두지 않습니다. 그래야 오케스트레이터 모델을 상속합니다.
- `-high` 정의를 만들지 않습니다. 세션 기본 effort가 이미 high인 환경에서는 no-op이고,
  세션을 xhigh나 max로 올려 둔 사용자에게는 리뷰어 effort를 **낮춥니다.** High는
  정의 없이 평소대로 dispatch하는 것을 뜻합니다.
- `disallowedTools`는 리뷰어가 구조적으로 파일을 고칠 수 없게 합니다. 이 항목은
  effort와 달리 관측 가능한 보장입니다.

### 디스패치 규칙

- High 리뷰: SDD가 쓰던 일반 리뷰어 subagent를 그대로 쓰고 `model` 인자를 넘기지
  않습니다. 모델과 effort를 모두 상속합니다. sddx 정의를 쓰지 않는다는 뜻이지,
  리뷰어 프롬프트나 역할이 달라진다는 뜻이 아닙니다.
- XHigh 리뷰: `subagent_type`을 `sddx-reviewer-xhigh`로 하고 `model` 인자를 넘기지
  않습니다. 모델을 상속하고 effort만 승급합니다.
- 승급은 바닥이지 천장이 아닙니다. 세션 effort가 이미 xhigh 이상이면 일반 dispatch가
  그 조건을 이미 만족하므로 승급 정의를 쓰지 않습니다. 쓰면 max 세션을 xhigh로
  끌어내립니다.
- `model` 오버라이드를 넘기지 않는 것이 모델 상속의 집행 수단입니다. Superpowers
  SDD의 저비용 리뷰어 모델 선택과 최종 최상위 모델 선택보다 이 규칙이 우선합니다.
- 호스트가 모델 상속이나 요청 effort를 지원하지 않으면 그 한계를 보고합니다.
  임의의 다른 모델이나 effort로 대체하지 않습니다.

### effort 선택

| 리뷰 범위 | effort |
| --- | --- |
| 명확한 요구사항, 국소 변경, 단순 통합 | High |
| lock·순서·공유 상태 변경, auth·권한·secret·sandbox 경계 변경, round 4–5 재리뷰, 반복해서 놓친 결함 | XHigh |

판단 근거는 review-package의 stat, task brief, 변경 파일 경로, ledger입니다. **diff
본문을 읽어 effort를 정하지 않습니다.** 그것은 컨트롤러가 리뷰를 미리 하는 것이고
컨트롤러 문맥을 오염시킵니다.

trigger가 아닌 것: 파일 수, 줄 수, 구현이 어려웠다는 사실, diff가 짧다는 사실,
최종 리뷰라는 사실. 재리뷰는 원래 결함의 위험도를 유지하며, diff가 작아졌다는
이유만으로 낮추지 않습니다.

round 4–5 조항은 implementer 규칙의 "High가 이미 이 task의 리뷰에서 실패했다"와
대칭입니다. 세 번의 재리뷰가 결함을 닫지 못했다는 것은 관측된 사실이고, 4–5 라운드는
드물어 비용이 한정됩니다.

### ledger

모든 리뷰 dispatch를 기록합니다. 부담은 비대칭입니다.

- High: `Task N review: sddx default — high`
- XHigh: `Task N review: sddx-reviewer-xhigh — <trigger>: <파일 경로 또는 brief 문구>`

trigger와 구체 경로를 대지 못하면 High입니다. 이 형식이면 유지보수자가 ledger의
리뷰 줄을 `review-*.diff`의 stat 헤더와 사후 대조할 수 있습니다.

### Red flags

`SKILL.md`의 기존 목록에 리뷰어 항목을 더합니다. 양방향으로 막아야 합니다.

- diff가 길어서 리뷰어 XHigh
- diff가 짧아서 리뷰어 High
- worker가 XHigh였으니 리뷰어도 XHigh
- 최종 리뷰라서 XHigh
- 안전하게 가려고 XHigh
- effort를 정하려고 diff 본문 읽기
- `Cannot verify from diff` 항목을 XHigh 재dispatch로 떠넘기기
- effort가 XHigh니 모델을 낮추기
- trigger와 경로 없는 `sddx-reviewer-xhigh` ledger 줄
- 리뷰어에 `model` 오버라이드 넘기기
- 실행 중 정의 파일 편집, 또는 세션에서 정의 파일 새로 만들기

기존 목록의 맺음말("stop, restore the overlay, continue SDD with the external
worker")은 리뷰어 항목에 맞지 않습니다. 리뷰어 항목의 처치는 올바른 정의로
재dispatch하고 ledger에 적는 것이므로, 목록을 나누거나 맺음말을 하나 더 둡니다.

### 호스트 조건

이 절은 Claude Code에만 적용됩니다. Codex에는 정의 파일이 없으므로 effort 승급을
지정할 수 없고, 그 한계를 보고한 뒤 진행합니다. 정의 부재를 이유로 실행을
BLOCKED로 세우지 않습니다. `supported_hosts`는 `["claude-code", "codex"]`로
유지하고, 호스트 조건은 산문으로 표현합니다.

### 관측 한계

Claude Code는 서브에이전트에 실제로 적용된 effort를 관측할 수단을 노출하지
않습니다. 증거 사슬은 frontmatter가 거부 없이 파싱된다는 것, transcript에
`subagent_type`이 남는다는 것, ledger 줄까지입니다. `testing.md`에 적용 effort를
`not_measured`로 기록합니다.

## 1.0.2 작업 흡수

`.worktrees/sddx-review-inheritance`(브랜치 `codex/sddx-review-inheritance`)에
커밋되지 않은 15개 파일 변경이 있습니다. 그 내용은 1.1.0에 함께 싣고 1.0.2라는
중간 버전은 만들지 않습니다. sddx는 태그를 만들지 않는 제품이고 `sddx*` 태그가
존재하지 않으므로, 중간 버전 번호를 없애는 데 드는 비용이 없습니다.

흡수할 내용:

- worker dispatch가 완결된 task 문맥을 주고, 전체 계획 조회 금지 경계를 shell과
  검색 도구를 포함해 반복 명시합니다.
- 완료 판정이 tool-call/results 증거와 worker의 scope 이탈 보고를 대조합니다.
  증거가 없으면 준수로 치지 않습니다.
- 테스트 보고가 wrapper 명령 전문을 보존하고 test exit와 wrapper exit를 구분합니다.
- 리뷰어 모델 상속과 위험도 기반 effort 선택. 이 항목만 본 설계로 대체합니다.
  그 브랜치의 규칙은 effort를 실제로 걸 수단이 없어 Claude Code에서 항상 "한계
  보고"로 떨어집니다. 정의 파일이 그 구멍을 메웁니다.

그 브랜치의 `cases.json` 신규 id 7개도 함께 가져옵니다. 작업 기준 패치는
구현 시작 전에 확보합니다.

## 바뀌지 않는 것

- 설치 링크 두 개와 공유 설치 블록.
- `products.toml`의 `verify_stages`. `sddx-contract` 단계가 이미
  `tests/products/sddx/test_*.py`를 glob하므로 새 테스트는 그대로 수집됩니다.
  단계를 추가하면 `tests/repository/test_verify.py`와 `docs/users/*/verification.md`가
  깨집니다.
- `supported_hosts`, catalog lock, archive manifest.
- implementer effort 규칙.
- `SDDX_SUPPORT` 지원 문장(계약 테스트가 문자 단위로 고정).

## 검증

공급자 없는 증거:

- 정의 파일 계약 테스트: `agents/claude-code/`에 `.md`가 정확히 하나, `name`이 파일명
  stem과 일치, `effort`가 `xhigh`, `model` 키 없음, `disallowedTools`에 Edit·Write·
  NotebookEdit 포함. 이 검사가 없으면 그 디렉터리에 떨어진 파일이 유령 에이전트가
  됩니다.
- `plugin.json` 계약 테스트: 필수 키와 제품명 일치.
- 기존 페이로드 계약: 상대 링크 없음, `/Users/` 없음, 이식 가능한 frontmatter.

행동 probe(`tests/products/sddx/behavior-probes.md`): baseline과 안내 적용본을 각각
독립 문맥에서 판정하며, 문자열 포함 검사는 통과로 치지 않습니다. 최소한 다음
상황을 양방향으로 덮습니다.

- 42 파일 대규모 기계적 rename → High
- 1 파일 18줄이지만 lock 획득 순서 변경 → XHigh, ledger에 trigger와 경로
- worker가 XHigh였으나 diff는 문자열 포맷 변경 → High
- CLI 인자 길이 검증 추가, 인증·권한 파일 무변경 → High
- 최종 whole-branch 리뷰, CRUD와 문서 → High
- fix round 4 진입, 같은 finding이 3회 미해결 → XHigh
- 세션 effort가 이미 xhigh 이상 → 승급 에이전트를 띄우지 않음

## 위험

- 정의 파일이 오는 경로가 플러그인 로딩이라, Claude Code가 스킬 폴더 플러그인
  취급 방식을 바꾸면 조용히 사라집니다. 계약 테스트는 파일 존재만 증명하고 로딩을
  증명하지 못합니다. 릴리스 전 실제 로딩 확인을 `testing.md` 절차에 남깁니다.
- 전역 에이전트 이름 공간을 쓰므로, 사용자의 프로젝트 `.claude/agents/`에 같은
  이름의 파일이 있으면 그쪽이 이깁니다. 이름에 제품 접두사를 두는 것 외에 방어
  수단이 없으며, 이 한계를 `compatibility.md`에 적습니다.
- XHigh 선택은 오케스트레이터 판단이라 결정적으로 검증할 수 없습니다. ledger의
  trigger와 경로가 사후 대조 수단의 전부입니다.
