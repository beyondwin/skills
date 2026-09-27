# 모델 배치와 기록 위치 조사

사용자가 세 가지를 물었습니다. 리뷰 모델이 구현 모델보다 좋아야 하는지, 구현 effort를
난이도에 따라 바꿀지, 기록을 최상위 `.waygent/`에 둘지입니다. 조사한 하네스 9개의
원본(버전·커밋은 [도구별 특징](../2026-09-agent-workflow-comparison/tools.md)과 같음)을
2026-09-27에 다시 읽었고, 이번 실측과 맞춰 봤습니다.

## 하네스별 모델 배치

| 하네스 | 조율자 | 구현자 | 리뷰어 | 출처 |
| --- | --- | --- | --- | --- |
| superpowers | 세션 | 난이도별 최저 등급. 1~2파일·완전한 스펙은 싼 모델, 여러 파일은 표준, 설계 판단은 최상위. 리뷰어와 산문 계획 구현자는 중간 등급이 바닥 | Task 리뷰는 diff의 크기·위험도에 맞춤. 끝 리뷰는 최상위. 고침 4~5라운드는 한 등급 위 | `skills/subagent-driven-development/SKILL.md` "Model Selection" |
| dryforge | 세션 | 세션 | 세션 | `go/references/orchestration.md` BLOCKED 사다리: 맥락 추가 → 더 강한 모델 → 사용자 |
| BMAD | 세션 | 서브에이전트. 설정으로 다른 모델이나 외부 도구로 바꿀 수 있음 | "세션과 같은 성능" 명시 | `bmad-build/step-04-review.md`, `customize.toml` |
| gstack | 세션 | 세션 | Claude 리뷰 + Codex 적대적 리뷰(`codex review`, effort high, `--xhigh`로 올림) | `review/sections/adversarial.md`, `codex/SKILL.md` |
| Ralph | Opus | 읽기는 Sonnet 병렬, 빌드·테스트는 Sonnet 1개, 디버깅·설계는 Opus | 없음 | `files/PROMPT_build.md`, `files/loop.sh` |
| workflow-orchestrator | 규칙 없음 | 규칙 없음 | 규칙 없음 | `workflow-orchestrator/SKILL.md` |
| mattpocock/skills | 규칙 없음 | 규칙 없음 | 규칙 없음. 질문 단계는 "가장 좋은 모델"을 권함 | `docs/engineering/grill-me.md` |
| Spec Kit | 규칙 없음 | 규칙 없음 | 없음 | — |
| OpenSpec | 규칙 없음 | 고성능 추론 모델 권장 | 없음 | `README.md` "Model selection" |

- 구현을 싼 모델로 내리는 하네스는 superpowers와 Ralph입니다. superpowers는 같은 절에
  "가장 싼 모델은 여러 단계 작업에서 턴이 2~3배라 오히려 비싸다"고 적었습니다.
- 모든 리뷰를 구현보다 강한 모델로 하는 하네스는 없습니다. 끝 리뷰만 올리거나
  (superpowers), 다른 회사 모델을 붙입니다(gstack).

## 이번 실측과 맞춰 본 판단

| 질문 | 판단 | 근거 |
| --- | --- | --- |
| 리뷰어를 더 좋은 모델로 | 끝 리뷰만 한 등급 위 | 진행 기록을 본 6회 모두 같은 모델 Task 리뷰어가 재생성 결함을 찾음. 놓친 회차는 조율자가 기각하거나 미룬 경우. 끝 리뷰는 한 번이라 비용 상한이 분명하고, Task 사이 문제는 끝 리뷰만 잡음(v26, 이번 `waygent_fo`) |
| 구현 effort를 난이도별로 | 낮추지 않음. 실패 뒤 재시도만 한 등급 위 | Claude Code는 호출 때 모델만 고르고 effort는 에이전트 정의 파일에서만 정함. 결함은 쉬워 보이는 저장소 Task에 있었고, v26 높음 7건도 상태·비동기였음. v26에서 싼 모델 구간이 5시간, $128을 버림 |
| 다른 회사 모델 리뷰 | 기본에 넣지 않음 | 블라인드 채점에서 GPT-5.6 Sol이 Claude 조건이 놓친 결함 4종을 찾았지만, 루프 안의 리뷰로 잰 적이 없고 설치가 하나 더 필요함 |

Codex에서 "한 등급 위"는 같은 모델에 `reasoning_effort: "xhigh"`만 적는 것입니다.
`spawn_agent`에서 모델을 비우면 자식이 세션 모델과 effort를 물려받고, effort만 적으면 같은
모델에 그 effort가 걸리는 것을 격리 시험으로 확인했습니다(sol high 세션 → 자식 sol high,
sol xhigh). 실측에서 Codex 조율자는 자기 모델과 effort를 몰랐습니다. 1회차는 자기를
`gpt-6-astra / xhigh`로 적고 모든 자식을 그 모델로 띄웠고, 2회차는 자기를 "GPT-5"로 적고 끝
리뷰어에 `high`를 줬습니다. 그래서 Codex에서는 이름을 적지 않고 `xhigh`를 고정값으로 씁니다.

## 기록 위치

| 하네스 | 위치 | git에서 빼는 방법 |
| --- | --- | --- |
| superpowers | `.superpowers/sdd/<plan>/` | 폴더 안에 `*` 한 줄짜리 `.gitignore`를 씀 (`scripts/sdd-workspace`) |
| dryforge | `.dryforge/` | 사용자에게 `.gitignore` 추가를 권함 |
| gstack | `~/.gstack/projects/` | 저장소 밖 |
| waygent 0.1.0 초안 | `.git/waygent/` | git 디렉터리 안 |

waygent는 superpowers 방식을 따라 `.waygent/<plan-slug>/`와 `.waygent/.gitignore`(`*`)로
옮겼습니다. 구현자가 `git add -A`를 해도 기록이 섞이지 않고, 사용자의 `.gitignore`는
그대로입니다. `git clean -fdx`는 이 폴더를 지우지만, 완료 판단은 커밋 트레일러로 하므로
진행 파일을 다시 만들 수 있습니다.

## 재지 않은 것

끝 리뷰 한 등급 위, 재시도 한 등급 위, 리뷰 원문 파일은 이 과제로 효과를 가를 수
없습니다. 기본 opus가 이미 64개 중 63개를 맞혀 더 잡을 결함이 거의 없습니다. 16-Task 규모의
과제가 필요합니다.
