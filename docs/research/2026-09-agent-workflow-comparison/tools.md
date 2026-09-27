# 도구별 특징

2026-09-27에 받은 저장소를 직접 읽고 설치해 본 결과입니다. 분량은 설치되는 지침
파일(`.md`, `.yaml`, `.toml`) 줄 수를 같은 방식으로 셌습니다. 스타 수는 같은 날
`gh api`로 읽은 값입니다.

## 한눈에

| 도구 | 버전·커밋 | 성격 | 시작 방식 | 사람 확인 지점 | 테스트 방식 | 서브에이전트 | git | 지침 분량 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| superpowers | 6.4.1 · `5bf4e78` | 스킬 묶음 + 세션 시작 훅 | 자동. 훅이 모든 작업에 스킬 사용을 강제 | 경로별 승인. spike/bounded/architectural | TDD 철칙: 실패하는 테스트 먼저 | 계획 실행 시 작업마다 구현자 + 리뷰어 | 워크트리, 끝나면 통합 방식 질문 | 15개 스킬, 8,856줄 |
| dryforge | 1.3.7 · `904f257` | ready → go 두 단계 | 수동 `/ready`, `/go` | 의도 승인 1번 + 결과 수락 1번 | 위험도별. RISKY만 test-first | 병렬 작업과 독립 검사에만 | 기존 프로젝트는 기능 브랜치, 머지 전 질문 | 3개 스킬, 4,479줄 |
| workflow-orchestrator | 1.5.0 · `900d395` | 조율자만. 모든 일을 작업자에게 위임 | 자연어 "workflow-orchestrator로" | 결과를 바꾸는 미지수만 짧은 인터뷰 | GATE(결정적 검사) + VERIFY(독립 검증) | 필수. 조사·구현·검증을 모두 위임 | 병렬 수정은 워크트리, 전달 범위 엄수 | 1개 스킬, 1,259줄 |
| mattpocock/skills | 1.2.3 · `c55ee46` | 작게 조합하는 스킬 | 수동 `/grill-with-docs` → `/to-spec` → `/implement` | 번호 질문 라운드, 각 질문에 추천안 | 합의한 지점만 red-green TDD | 사실 조사·코드 리뷰에 사용 | 현재 브랜치에 커밋, PR 없음 | 스킬 38개, 4,222줄 |
| gstack | 1.91.2.0 · `01593aa` | 역할별 가상 팀. CEO·엔지니어링·QA·릴리스 | 수동 `/office-hours` → `/plan-*` → `/review` → `/ship` | 결정마다 한 번씩 결정 요약 | 테스트 우선 아님. 계획에 테스트 표, `/ship`에서 커버리지 감사 | 리뷰에 전문 리뷰어와 외부 모델 | `/ship`은 확인 없이 push와 PR까지 | 스킬 54개, SKILL.md만 37,719줄 |
| BMAD-METHOD | npm 6.12.0 · 저장소 `5e33d3c` | 애자일 페르소나 + 작업 규모별 트랙 | 수동 `/bmad-build`. 설명이 넓어 자동으로도 켜질 수 있음 | 질문 묶음 1번 + 스펙 체크포인트 | 스펙의 경계 사례 표마다 테스트 감사 | 구현자와 리뷰어 3명 병렬 | 더러운 트리면 중단, 로컬 커밋 1개, push 없음 | 설치 250개 파일, 13,996줄 |
| Spec Kit | `c00dc05` (v1.0.12 이후) | 헌법 + 명세 주도 개발 | 수동 `/speckit-constitution` → `specify` → `clarify` → `plan` → `tasks` → `implement` | 명세 질문 최대 3개, clarify 최대 5개 | 테스트 작업은 선택. 요청할 때만 | 없음 | 기본은 브랜치·커밋 안 함 | 설치 43개 파일, 4,273줄 |
| OpenSpec | 1.13.2 · `79b6aa9` | 변경 제안 + 델타 명세 | 수동 `/opsx:propose` → `/opsx:apply` → `/opsx:archive` | 제안 검토, archive 메뉴 | TDD 없음. 작업마다 검증 방법 명시 | 없음 | 커밋 안 함 | 2,622줄 + `openspec` CLI |
| Ralph Wiggum | `88d488a` | bash 루프. 매 반복 새 컨텍스트 | 사람이 루프 실행 | 처음 요구사항 대화뿐 | 매 반복 테스트로 역압 | 프롬프트가 수백 개 병렬 서브에이전트를 권함 | 매 반복 커밋·태그·push(여기선 push 차단) | 파일 5개, 120줄 |

기본 Claude Code(스킬 없음)를 대조군으로 함께 돌렸습니다.

## superpowers — obra/superpowers 6.4.1

- 무엇: TDD, 디버깅, 브레인스토밍, 계획 작성, 서브에이전트 실행, 코드 리뷰, 브랜치
  마무리까지 개발 전 과정을 덮는 스킬 15개입니다. 세션 시작 훅이
  "관련 스킬이 1%라도 있으면 반드시 쓴다"는 규칙을 주입합니다.
- 흐름: brainstorming이 요청을 spike, bounded, architectural 셋 중 하나로 분류합니다.
  bounded는 채팅으로 짧은 설계를 보여 주고 승인을 받습니다. architectural은 스펙
  문서 → 승인 → writing-plans → 실행 방식 선택 → subagent-driven-development 순서입니다.
- 강점: 디버깅(systematic-debugging), 리뷰 받기와 반영, 완료 전 검증처럼 계획 밖의
  장면까지 덮습니다. 비슷한 스킬은 mattpocock(`diagnosing-bugs`, `code-review`), BMAD
  (`code-review`, `correct-course`), Spec Kit 버그 확장, gstack에도 있습니다. 차이는
  세션 시작 훅이 사람이 부르지 않아도 이 스킬들을 켠다는 점입니다.
- 약점: 훅이 모든 작업에 끼어듭니다. 사람 승인 단계가 여러 번 있습니다.
- 다른 도구와 관계: 이 저장소의 `sddx`와 `pre-sdd-review`는 지금 superpowers 모양의
  스펙·계획 파일을 입력으로 받습니다. 다른 도구의 계획 파일을 받는지는 시험하지 않았습니다.

## dryforge — prekuter/dryforge 1.3.7

- 무엇: `ready`(의도 파악·승인), `go`(구현·검증), `migration`(기존 저장소 1회 전환)
  세 스킬입니다. 스킬 설명에 `disable-model-invocation: true`가 있어 사람이 직접
  불러야만 동작합니다.
- 원칙: "이 결정은 누구의 것인가"입니다. 코드로 알 수 있는 것은 묻지 않고, 사용자가
  정할 것은 짐작하지 않습니다. 출처끼리 다르면 반드시 묻습니다. 자기 채점을 믿지
  않고, 끝났다는 판정은 실제로 돌린 검사가 정합니다.
- 산출물: `.dryforge/`(handoff·spec·plan, 로컬)와, 첫 사이클이 끝나면
  `CLAUDE.md`/`AGENTS.md` + `docs/`(architecture, business-rules, security, standards 등)
  "하네스"를 저장소에 씁니다.
- 전제: git, 깨끗한 작업 트리, push된 main이 필요합니다. v1.1.1이 2026-06-12에 나온
  1인 저자 프로젝트입니다. 스타 282개입니다.

## workflow-orchestrator — jha0313/skills_repo 1.5.0

- 무엇: 조율자는 직접 코드를 읽거나 고치지 않습니다. 조사·계획·구현·검증·리뷰를
  모두 작업자 서브에이전트에게 맡기고, 의존성과 근거만 관리합니다. Firstmate에서
  영감을 받았습니다.
- 검증: GATE(빌드·테스트 같은 결정적 검사)와 VERIFY(구현하지 않은 검증자의 실제
  동작 확인)를 나눕니다. 검사를 못 돌렸으면 PASS가 아니라 미검증으로 보고합니다.
- 같은 저장소의 다른 스킬 `eval-writer`, `skill-evaluator`는 평가 도구라서 이번
  개발 흐름 비교에는 넣지 않았습니다.

## mattpocock/skills 1.2.3

- 무엇: "진짜 엔지니어를 위한 스킬"을 내겁니다. 프로세스를 도구가 쥐는
  GSD·BMAD·Spec-Kit을 비판하고, 사용자가 단계마다 주도권을 갖는 작은 스킬을 조합합니다.
- 흐름: `grill-with-docs`(질문 라운드 + `CONTEXT.md`·ADR 기록) → `to-spec` →
  (필요하면 `to-tickets`) → `implement`(TDD → 타입체크 → 테스트 → 코드 리뷰 → 커밋)입니다.
- 특징: 질문마다 번호와 추천 답을 붙입니다. 사실 확인은 사용자에게 묻지 않고
  서브에이전트가 조사합니다.
- 설치 전제: 저장소별 1회 설정 스킬이 먼저 돌아야 합니다. 실측에서는 그 스킬이
  쓰는 파일을 스크립트로 똑같이 만들었습니다.

## gstack — garrytan/gstack 1.91.2.0

- 무엇: CEO, 엔지니어링 매니저, 디자이너, 스태프 리뷰어, QA, 보안, 릴리스 엔지니어
  역할의 스킬 54개입니다. Think → Plan → Build → Review → Test → Ship → Reflect 스프린트를 돕니다.
- 특징: 단일 스킬이 4만~5만 토큰에 이릅니다. 브라우저 QA용 바이너리(bun 빌드)가 있습니다.
- git: `/ship`은 base를 머지하고 커밋한 뒤 확인 없이 push와 PR까지 합니다.
  실측에서는 `/ship`을 쓰지 않고, 로컬 bare 저장소를 origin으로 두었습니다.
- 실측에서 발견한 것: 계획 검토(S1)와 `/review`(S3)가 설치돼 있는 Codex CLI를
  "외부 의견"으로 불렀습니다. 격리한 Claude 세션 밖의 다른 공급자 호출입니다. S2에서는
  외부 전송 여부를 먼저 물었습니다.

## BMAD-METHOD — npm bmad-method 6.12.0

- 무엇: 분석가·PM·아키텍트·개발자·UX 페르소나와, 작업 규모에 따른 트랙(한 세션
  build / epic / 전체 프로젝트)을 가진 애자일 방법론입니다.
- `bmad-build`: clarify → plan(스펙 작성) → 승인 체크포인트 → 서브에이전트 구현 →
  리뷰어 3명 병렬(blind-hunter, edge-case-hunter, verification-gap) → 보고입니다.
  작고 열린 질문이 없으면 체크포인트를 건너뛰는 oneshot 경로를 탑니다.
- 버전 주의: 저장소 HEAD(6.13.0-next)는 설치 방식이 바뀌는 중입니다. 실측은 npm
  `latest`인 6.12.0으로 했습니다.

## Spec Kit — github/spec-kit

- 무엇: 명세를 진실의 원천으로 두고 계획·작업·코드를 거기서 파생합니다. 프로젝트
  원칙은 `.specify/memory/constitution.md`(헌법)에 둡니다.
- 흐름: constitution → specify → clarify → plan → tasks → (analyze) → implement →
  converge입니다. converge는 구현이 명세에 수렴할 때까지 남은 일을 `tasks.md`에 추가합니다.
- 특징: 명령이 이제 `/speckit-*` 스킬(하이픈)입니다. 테스트 작업은 명세나 헌법이
  요구할 때만 생깁니다. 버그 확장(`bug-assess`, `bug-fix`, `bug-test`)은 선택입니다.

## OpenSpec — @fission-ai/openspec 1.13.2

- 무엇: 변경마다 `openspec/changes/<name>/`에 proposal, 델타 명세(ADDED/MODIFIED),
  design, tasks를 둡니다. archive하면 델타가 `openspec/specs/`에 합쳐집니다.
- 특징: propose는 같은 턴에 구현하지 못하게 막혀 있습니다. 모든 명령이 `openspec`
  CLI를 호출합니다. git 커밋은 하지 않습니다.

## Ralph Wiggum — ghuntley/how-to-ralph-wiggum

- 무엇: `while :; do cat PROMPT.md | claude -p; done` 루프입니다. 매 반복이 새
  컨텍스트이고, 디스크의 `IMPLEMENTATION_PLAN.md`만 상태로 이어집니다. 실제 내용은
  Clayton Farr가 정리한 "Ralph Playbook"이고, 라이선스 파일이 없습니다.
- 흐름: 사람과 요구사항 대화 → `specs/*.md` → 계획 루프 1~2회 → 구현 루프
  (가장 중요한 항목 1개 → 테스트 → 커밋 → 태그)입니다.
- 실측에서 바꾼 것: push 줄을 지우고 `git push` 도구 호출을 막았습니다. 반복 횟수에
  상한을 두고, 변화가 없으면 멈추게 했습니다. 프롬프트 본문은 원문 그대로입니다.
