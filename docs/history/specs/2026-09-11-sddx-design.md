# SDDx 설계

**Status:** Approved on 2026-09-11

**Scope:** 이 저장소의 다섯 번째 독립 제품 `sddx`. Superpowers
`subagent-driven-development`는 포크·복사하지 않고, 구현 worker만 외부
CLI로 바꾸는 얇은 런타임 오버레이. 오케스트레이터 호스트는 Claude Code와
Codex. 구현 backend는 신원 확인된 Cursor Agent CLI와 Grok Build CLI.

**Out of scope:** Superpowers 원본 수정, `catalog/` 변경, MCP/라우터/세션
DB, backend 자동 전환, task마다 backend 선택, 라이브 모델·CLI를 기본
verify에 넣기, `pre-sdd-review` 필수화, Cursor/Grok를
`supported_hosts`에 넣기, 여섯 번째 스킬.

이 파일은 진행 중인 설계이다. 현재 계약을 정의하지 않는다. 산 계약은 구현
후 제품 README와 `docs/maintainers/products/sddx/`에 있다.

## Context

핸드오프는 user-level `sddx` 런처를 원했다. 이 작업은 같은 런타임을 이
저장소의 독립 제품으로 둔다. 제품이 되면 `products.toml`, 설치 파일,
관리자 네 문서, 공급자 없는 계약 테스트, 공개 문서의 제품 목록이 한
변경에 따라간다. `catalog/` 고정 묶음은 그대로다.

로컬 PATH의 `grok`과 `agent`는 둘 다 Grok Build TUI(1.0.25)이다. Cursor
`cursor-agent`는 이 환경에 없다. `agent`를 Cursor로 취급하면 잘못된
worker를 띄운다.

Superpowers SDD는 이미 worktree, ledger, task brief, review package,
task review, fix loop, whole-branch review를 소유한다. `sddx`가 이
루프를 다시 쓰면 원본과 갈라진다.

## Goals

1. 현재 Claude Code 또는 Codex 세션 모델이 오케스트레이터·리뷰어로 남는다.
2. 설치된 Superpowers SDD를 그대로 실행하고, implementer dispatch만 외부
   CLI로 바꾼다.
3. backend는 plan 시작 때 한 번 고르고 그 plan 동안 유지한다.
4. 구현 난이도는 task마다 High / XHigh만 고른다. 설계 모호함은 effort가
   아니라 오케스트레이터 ruling이다.
5. 기본 검증은 자격 증명과 공급자 호출이 없다. CLI 신원 충돌은 픽스처로
   막는다.
6. 공개 카탈로그는 바꾸지 않는다. 여섯 번째 스킬은 여전히 기본 거절이다.

## Non-goals

- Superpowers `SKILL.md`·프롬프트·스크립트를 수정하거나 저장소에 복사하지
  않는다.
- generic model router, OpenRouter, MCP orchestration server를 만들지
  않는다.
- worker가 다시 SDD·브레인스토밍·서브에이전트를 돌리게 하지 않는다.
- worker에게 `--worktree`를 넘겨 중첩 worktree를 만들지 않는다.
- Cursor quota 부족 때 Grok으로 자동 전환하지 않는다.
- 라이브 Grok/Cursor 품질을 `verify.py` 통과로 주장하지 않는다.

## Decisions

### 1. 제품 정체

| 필드 | 값 |
| --- | --- |
| `name` | `sddx` |
| `display_name` | `SDDx` |
| `supported_hosts` | `claude-code`, `codex` |
| `skill_path` | `skills/sddx` |
| `test_path` | `tests/products/sddx` |
| `maintainer_docs` | `docs/maintainers/products/sddx` |
| `verify_stages` | `product-contract`, `sddx-contract`, `python-compile` |
| 초판 버전 | `1.0.0` |
| 라이선스 | Apache-2.0 |

슬래시 호출은 Claude Code `/sddx`, Codex `$sddx`이다. 제품 ID와 스킬
`name`과 디렉터리 이름은 같다.

`supported_hosts`는 이 스킬을 **오케스트레이터로 실행하는** 호스트다.
Cursor CLI와 Grok CLI는 구현 worker이지 호스트가 아니다. `cursor`와
`grok`을 `supported_hosts`에 넣지 않는다.

v1.0.0의 호스트 실행 증거는 `not_measured`이다. 지원 주장은 제품 결정이고,
과거 smoke가 없어도 how-it-works와 같이 지원 범위를 적는다. 새 호스트를
더하려면 실제 관측과 같은 변경의 레지스트리·문서·테스트가 필요하다.

### 2. 소유 경계

| 소유 | 내용 |
| --- | --- |
| Superpowers SDD | worktree, ledger 본체, task-brief, review-package, 리뷰어 프롬프트, fix loop 한도, whole-branch review, finishing-a-development-branch |
| `sddx` | 인자 해석, backend picker, `resolve_backend.py`, implementer argv, worker 제약, High/XHigh, ledger의 backend·session 두 줄, 호스트별 picker/대기 |

컨트롤러는 SDD를 “읽고 따른다”. SDD 본문을 `sddx` SKILL에 붙여 넣지
않는다. 예외는 한 문장으로 적는다: implementer를 네이티브 서브에이전트로
보내지 말고 `resolve_backend.py`가 만든 argv로 보낸다.

리뷰어·재리뷰어·최종 리뷰어는 호스트 네이티브 서브에이전트다. Claude Code는
Task, Codex는 `spawn_agent`. 구현 worker만 외부 프로세스다.

### 3. 호출과 발견

인자:

```text
sddx <plan-file> [cursor|grok|c|g]
```

plan 인자가 없거나 파일이 없으면 추측하지 않고 멈춘다. 여러 plan을 한
호출에서 돌리지 않는다.

backend 인자가 있으면 picker를 생략한다. 별칭: `c` → `cursor`, `g` →
`grok`. 인자가 없으면 plan당 한 번만 고른다.

- Claude Code: 호스트 질문 UI (AskUserQuestion).
- Codex: 번호 있는 선택지를 한 번 묻고 답을 기다린다.

사용 가능한 backend가 하나면 그 사실과 빠진 backend 이유를 보여 주고, 인자
없이 진행할 때도 확인을 받는다. 하나뿐이라고 자동 선택하지 않는다. 인자가
가리키는 backend가 없으면 다른 쪽으로 바꾸지 않고 멈춘다. 둘 다 없으면
`BLOCKED`다.

암묵 호출은 약하다. description은 `/sddx`, `$sddx`, 외부 implementer,
Cursor Grok, Grok CLI worker, 현재 세션을 오케스트레이터로 유지하는 요청만
트리거한다. “이 플랜 실행해”, `subagent-driven-development`,
`pre-sdd-review`만으로는 활성화하지 않는다.
`agents/openai.yaml`의 `allow_implicit_invocation`은 `true`다. 이 저장소
`product_contract`가 모든 제품 yaml에 `true`를 요구한다. near-miss는 yaml이
아니라 SKILL description과 본문이 막는다.

`pre-sdd-review`는 선택 선행이다. `sddx`가 READY를 요구하지 않는다.
pre-sdd-review의 호스트 범위를 이 작업에서 넓히지 않는다.

### 4. 런타임 루프

```text
현재 세션 모델 = Orchestrator / Reviewer
        │
 /sddx <plan> [backend]
        │
 backend 1회 선택 → ledger `Backend: cursor|grok`
        │
 Superpowers SDD 실행 (원본)
        │
 task N:
   effort High|XHigh
   resolve_backend → argv
   fresh worker (같은 task fix 1–3은 resume)
   코드 + 테스트 + commit + report file
   네이티브 task review
   실패 시 worker 수정, 컨트롤러가 직접 고치지 않음
        │
 whole-branch review (네이티브, 가장 유능한 모델)
        │
 finishing-a-development-branch
```

SDD의 연속 실행·ruling·네 가지 정지 조건·ledger 복구는 그대로다.
컨트롤러는 구현을 가져가지 않는다.

Compaction 뒤에도 backend와 worker session id는 ledger에 있다. SDD
workspace 디렉터리를 따로 만들지 않는다.

### 5. Effort

기본은 High. 구현 자체가 어려울 때만 XHigh: 복잡한 동시성, race,
트랜잭션 경계, 여러 서브시스템 연동, 비정형 코드에서의 깊은 추론, High로
같은 task review가 반복 실패한 경우.

애매함은 XHigh가 아니다. worker가 설계 선택지를 물으면
`NEEDS_CONTEXT` / `BLOCKED`로 보고하고, 오케스트레이터가 ruling한 뒤 같은
backend으로 다시 보낸다.

SDD Model Selection의 cheap/standard/capable는 **구현 worker에 적용하지
않는다**. 구현은 High/XHigh 두 단뿐이다. 리뷰어 모델 선택은 SDD 규칙을
호스트 네이티브 서브에이전트에 그대로 쓴다.

Fix 라운드 1–3: 같은 worker session resume, 같은 effort. 라운드 4–5:
fresh worker + XHigh (SDD의 “더 유능한 모델”에 해당). 그 뒤에도 남으면
SDD breaker로 오케스트레이터가 판정한다. 그 이상 effort 단계는 없다.

### 6. Worker 제약

공통 프롬프트는 `references/worker-prompt.md`가 소유한다. Superpowers
implementer-prompt의 보고 계약(DONE / DONE_WITH_CONCERNS / BLOCKED /
NEEDS_CONTEXT, report file)을 재사용한다. SDD 템플릿을 저장소에 복사하지
않고, 추가 금지와 작업 디렉터리만 덧붙인다.

Worker는 다음을 하지 않는다.

- brainstorm, 새 implementation plan, SDD/Superpowers 호출
- 서브에이전트·리뷰어 spawn
- architecture 재설계, scope 확장
- 새 git worktree 생성 (`using-git-worktrees` 포함)
- 다른 구현 에이전트 오케스트레이션

Grok Build 호출은 최소한 `--cwd <current-sdd-worktree> --no-plan
--no-subagents --always-approve`를 쓴다. `--worktree`는 넘기지 않는다.
`--continue`는 쓰지 않는다. 새 task는 새 session, fix 1–3은 `--resume
<id>`.

Cursor 호출은 headless 쓰기(`--print`/`-p`와 `--force`/`--trust` 계열)와
workspace 경로를 쓴다. Cursor가 effort flag를 주지 않으면 사용 가능한
Grok 모델 id를 조회해 고르고, XHigh는 이름에 더 높은 reasoning이 있는
variant가 있을 때만 올리고 없으면 같은 모델에 worker 프롬프트로만 구분한다.
Grok 모델 id가 없으면 그 backend는 없는 것과 같다.

무인 실행을 위해 도구 자동 승인은 허용한다. 파일 접근은 workspace
sandbox가 있으면 켠다. Grok worker는 `--disable-web-search`를 붙인다.
Cursor worker는 `--plugin-dir`를 붙이지 않고, 컨트롤러가 MCP를 승인하지
않는다. 컨트롤러 세션의 자격 증명·환경 값을 worker 프롬프트나
`--prompt-file`에 붙여 넣지 않는다. 라이브 worker는 계획과 worktree 내용을
선택한 Cursor 또는 xAI 공급자에게 보낸다. 기본 `verify.py`는 그 CLI를
호출하지 않는다.

### 7. `resolve_backend.py`

설치 페이로드의 런타임 스크립트다. 컨트롤러는 로드된 스킬 루트에서 실행한다.

```bash
python3 "<skill-root>/scripts/resolve_backend.py" --backend <cursor|grok|c|g> --json
```

설치하지 않는다. 네트워크를 쓰지 않는다. worker를 띄우지 않는다.
`--version` / `--help`만 본다.

성공 시 stdout은 JSON 한 객체와 LF다.

```json
{
  "backend": "cursor",
  "available": true,
  "executable": "/abs/path",
  "identity": "version line",
  "argv_prefix": ["/abs/path", "..."],
  "reason": null
}
```

`available`이 false면 `executable`/`argv_prefix`는 null이고 `reason`은
`not_found` | `identity_mismatch` | `missing_flags` | `no_grok_model`
중 하나다. 종료 코드는 잘못된 인자일 때만 비0, 없는 backend는 0 +
`available: false`다. 컨트롤러가 종료 코드만으로 다른 backend를 고르지
않는다.

신원 규칙:

- `grok` 후보는 PATH의 `grok`뿐이다. `agent`는 Grok 후보가 아니다. PATH에
  `agent`만 있고 그것이 Grok Build여도 `not_found`다.
- `cursor` 후보는 `cursor-agent`, 그다음 신원이 Cursor Agent CLI인
  `cursor`이다. `agent`는 Cursor 후보가 아니다.
- `--version` 또는 `--help`가 Grok Build / xAI Grok이면 Cursor로 채택하지
  않는다.

필수 능력은 `--help`로 확인한다. 없으면 `missing_flags`다.

Grok: `--cwd`, no-plan, no-subagents, reasoning-effort 또는 effort, headless
prompt, resume, always-approve. `--cwd`가 help에 없으면 `missing_flags`다.
Cursor: headless print, force/yolo, trust, workspace/cwd, model, resume.

`argv_prefix`는 실행 파일과 고정 플래그만 담는다. Grok 고정 플래그에
`--disable-web-search`를 포함한다. prompt 파일, effort 값, resume id,
`--cwd`/`--workspace`는 컨트롤러가 붙인다.

테스트는 PATH에 가짜 바이너리를 넣어 이 규칙을 잠근다. `cursor-agent`만이
아니라 신원이 Cursor Agent CLI인 `cursor` 후보도 잠근다. 실제 Cursor/Grok
계정을 쓰지 않는다.

### 8. 실패와 정지

멈추고 사용자에게 맡기는 경우:

- plan 경로 없음/모호/없음
- 요청한 backend 없음 (자동 전환 없음)
- 두 backend 모두 없음
- worker가 호스트 밖 부작용(push, publish, 공유 브랜치)을 필요로 함
- SDD가 정지하라고 한 네 가지

멈추지 않고 오케스트레이터가 처리하는 경우:

- `NEEDS_CONTEXT` / `BLOCKED` → ruling 후 재dispatch
- review 실패 → 같은 session resume
- worker가 서브에이전트나 SDD를 돌림 → 결함. 그 결과를 리뷰 통과로
  쓰지 않고 수정 라운드에 넣는다
- worker가 추가 worktree를 만듦 → 그 task 실패
- 실행 중 backend 장애 → 사용자에게 중단 또는 명시적 전환. 침묵 전환
  없음

긴 worker는 짧게 폴링하지 않는다. Claude Code는 긴 셸 대기를 한 번에
쓰고, Codex의 `wait_agent`는 네이티브 리뷰어에만 쓴다. 외부 CLI 대기는
셸 작업의 완료다.

### 9. 설치

how-it-works와 같이 저장소 로컬 링크다. `$skill-installer` 세 Codex 전용
제품 목록(`install-codex.md`의 세 명령)에 넣지 않는다. how-it-works처럼
제품 README에는 공개 GitHub 경로를 가리키는 `$skill-installer
https://github.com/beyondwin/skills/tree/main/skills/sddx` 한 줄을 둔다.
이 줄은 Codex 전용 설치기가 아니라 공개 경로 이름이다.

```text
skills/sddx/
├─ ~/.agents/skills/sddx  → Codex
└─ ~/.claude/skills/sddx  → Claude Code
```

`~/.codex`와 `~/.grok`에 복사본을 만들지 않는다. 링크 설치 Python 블록은
how-it-works와 같은 계약이다: source/target 인자, 실재하는 스킬 디렉터리,
같은 링크는 `already linked`, 다른 링크·파일·디렉터리는 거부.

`docs/users/*/install-local.md`는 how-it-works만의 문서가 아니라 듀얼
호스트 로컬 링크 문서가 된다. how-it-works 마커와 블록은 유지하고, sddx
섹션과 `<!-- sddx-local-links -->` 블록을 더한다. 제품 README 한영에도 같은
블록이 있다.

### 10. 파일

설치 페이로드 (`skills/sddx/`):

```text
SKILL.md
README.md
README.en.md
CHANGELOG.md
LICENSE.txt
release.toml
agents/openai.yaml
references/dispatch.md
references/worker-prompt.md
scripts/resolve_backend.py
```

SKILL.md는 활성화, 하드 게이트, SDD 참조, picker, effort, ledger 두 줄,
빨간 깃발만 둔다. CLI 플래그 레시피는 `dispatch.md`, worker 문장은
`worker-prompt.md`. description은 트리거만 적고 워크플로를 요약하지 않는다.

저장소 계약:

```text
tests/products/sddx/test_contract.py
tests/products/sddx/test_resolve_backend.py
tests/products/sddx/cases.json
tests/products/sddx/fixtures/binaries/
docs/maintainers/products/sddx/{contract,testing,compatibility,release}.md
```

같이 고치는 거버넌스 (catalog 제외):

- `products.toml`
- `CONTRIBUTING.md` — 다섯 제품을 나열하고 “new skills are not accepted
  by default”는 유지
- 루트 README, `docs/maintainers/repository/architecture.md`
- `docs/users/ko|en/{installation,install-local,compatibility}.md`
- `scripts/lib/verification.py`에 `sddx-contract` 단계
- 제품 목록을 잠근 공개 문서·커뮤니티 테스트

이슈/PR 템플릿은 `REGISTRY.names`를 도는 테스트가 있으므로 제품 등록과
함께 이름을 넣는다.

### 11. 검증

기본:

```bash
python3 scripts/verify.py --skill sddx
python3 scripts/verify.py
```

`sddx-contract`는 패키지 정체, frontmatter, 활성화/near-miss 사례,
호스트≠backend, `agent`≠Cursor, 자동 전환 금지, `--worktree` 금지,
catalog 비포함, `resolve_backend.py` 픽스처를 본다. 라이브 CLI, 과금,
모델 품질은 보지 않는다.

`cases.json` 사례 (정확한 집합, 구현 때 테스트가 이 id를 잠근다):

- `explicit-slash-sddx`
- `explicit-codex-sddx`
- `argv-cursor`
- `argv-grok`
- `argv-alias-c`
- `argv-alias-g`
- `picker-once-per-plan`
- `missing-requested-backend-no-failover`
- `agent-binary-is-not-cursor`
- `worker-no-nested-worktree`
- `ambiguity-is-ruling-not-xhigh`
- `reviewer-stays-native`
- `near-miss-native-sdd`
- `near-miss-pre-sdd-review`
- `catalog-excludes-sddx`
- `one-available-backend-still-confirms`
- `worker-no-host-outside-side-effects`
- `no-credentials-in-worker-prompt`

선택 라이브 점검은 로컬·명시적·CI 밖이다. 통과한 오프라인을 호스트 품질로
설명하지 않는다.

제품 README 제목 순서는 기존 네 제품과 같다.

### 12. 하지 않는 것

- Superpowers fork
- catalog lock/플러그인에 sddx 추가
- 세션 레지스트리 JSON/DB
- backend 비용 라우터
- CLAUDE.md에 모델명 하드코딩
- 라이브 worker 트랜스크립트를 픽스처로 커밋
- Windows native Cursor/Grok 지원 주장

## Implementation order

코드와 산 문서는 이 스펙이 승인된 뒤에만 바꾼다.

1. `sddx-contract`와 `resolve_backend` 픽스처 테스트를 먼저 두어 실패하게
   한다.
2. `skills/sddx/` 페이로드와 `resolve_backend.py`를 넣어 테스트를 통과시킨다.
3. `products.toml`과 `sddx-contract` verify 단계를 등록한다.
4. 관리자 네 문서와 제품 README를 같은 계약으로 맞춘다.
5. 거버넌스·사용자 문서의 네 제품 목록을 다섯으로 바꾼다. catalog는 건드리지
   않는다.
6. `python3 scripts/verify.py`가 공급자 없이 통과해야 끝이다.

## Verification

완료 조건:

1. `python3 scripts/verify.py`와 `--skill sddx`가 공급자 없이 통과한다.
2. `products.toml`에 `sddx`가 있고 `supported_hosts`는 `claude-code`,
   `codex`뿐이며 catalog lock에 sddx가 없다.
3. Superpowers 설치 파일과 `catalog/` 본문이 이 작업으로 바뀌지 않는다.
4. `resolve_backend.py`가 Grok 신원의 `agent`를 Cursor로 채택하지 않는다.
5. SKILL description이 SDD 루프를 요약하지 않는다.
6. `git diff --check`가 통과한다.

## Recovery

- 에이전트가 SDD를 `sddx`에 복사하기 시작하면 그 본문을 지우고 참조
  문장으로 되돌린다.
- `agent`를 Cursor로 쓰는 레시피가 생기면 `resolve_backend` 픽스처가
  실패로 닫는다.
- 라이브 CLI 없이 품질을 주장하면 문서를 `not_measured`로 되돌린다.
- 공개 문서가 네 제품만 말하면 다섯 제품 목록과 테스트를 같이 고친다.
- 설치 페이로드가 바뀌면 같은 변경에서 `release.toml`, SKILL
  `metadata.version`, CHANGELOG를 맞춘다. 초판은 `1.0.0`이다. 이 스펙
  승인과 구현 계획만으로는 태그를 만들지 않는다.
