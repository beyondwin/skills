# waygent 설계와 실측 (2026-09)

`waygent`는 모델을 감싸는 가벼운 구현 스킬입니다. 이 폴더는 그 설계가 어디서 왔고,
실제로 돌려 보니 어땠는지를 적습니다.

- 스킬: [`skills/waygent/SKILL.md`](../../../skills/waygent/SKILL.md) (0.1.0, 약 140줄)
- 설계 근거: [에이전트 워크플로 비교](../2026-09-agent-workflow-comparison/README.md)의 30회
  실측, 사용자가 잰 v26/v27 비교, 네 모델(Opus 5.5, Fable 5.1, Grok 4.7, GPT-5.6 Sol)의
  독립 설계안
- 실측: 10-Task 계획 과제 하나, 조건과 모델 13칸, 22회(파일럿 2회는 따로). Claude Code 2.1.280(opus, fable)과
  Cursor Agent 2026.09.23(grok-4.7-high), 추가로 Codex 0.154.0(gpt-5.6-sol high) 3회와 바뀐 문구 opus 1회

## 결론

1. **이 규모에서는 하네스 없이도 결과물이 거의 같았습니다.** 기본 Claude Code(opus)가
   6.5분, $1.44에 숨긴 테스트 64개 중 63개를 통과했습니다. superpowers는 $15.38, 87분에
   64개였습니다. 계획과 설계서가 잘 적혀 있으면 모델이 혼자서도 거의 다 맞힙니다.
2. **차이가 난 곳은 숨은 결함 하나였습니다.** 지운 프롬프트를 다시 만들면 옛 폼이 덮어쓰는
   결함을, 한 세션이 혼자 구현한 5회는 모두 남겼습니다. Task마다 새 구현자와 리뷰를 둔
   실행은 14회 중 11회 고쳤습니다. 진행 파일을 본 6회에서는 리뷰가 매번 결함을 찾았고,
   고칠지 말지는 메인의 판단이 갈랐습니다.
3. **Task마다 리뷰는 이 규모에서 비용만 두 배였습니다.** 끝 리뷰만 둔 변형이 같은 품질을
   절반 비용($4.02 대 $7.50), 절반 시간(17.5분 대 33.6분)에 냈고, 메인 컨텍스트도 가장
   작았습니다(5.5만 토큰, 기본 6.9만). 큰 계획에서는 다를 수 있어, 스킬 기본값은 요청대로
   Task마다 리뷰로 두었습니다. 4번 단계를 지우면 끝 리뷰만 하는 방식이 됩니다.
4. **이어 하기와 공존은 됐습니다.** 세션을 강제로 끊어도 끝난 Task를 다시 하지 않았고,
   superpowers와 함께 설치해도 `/waygent`가 주도했습니다.
5. **Codex에서도 돌았습니다.** gpt-5.6-sol high로 10개 Task를 끝까지 했고(63/64, 62/64),
   조율자가 자기 모델 이름을 몰라서 모델을 적지 않고 물려받게 고쳤습니다([실측 결과 11절](results.md)).
6. **모델을 바꾸면 비쌌습니다.** fable은 같은 결과에 opus보다 2.8~3.5배 비쌌습니다.
   Cursor grok-4.7은 스킬을 그대로 따랐지만 매우 느렸습니다.

## 스킬에 들어간 것과 뺀 것

| 넣음 | 근거 |
| --- | --- |
| Task마다 새 구현자 하나, 짧은 지시(약 1,300자) + 공통 지침 한 장 | v27이 v26보다 16% 빠르고 37% 쌌음. 네 모델 모두 권함 |
| 테스트 먼저(실패를 본 뒤 구현) | 사용자 요구. 모든 실행이 자기 테스트를 53~195개 남김 |
| Task마다 리뷰 한 번, 재리뷰 없음 | 사용자 요구. v26 리뷰 왕복이 2.4시간 |
| 끝 전체 리뷰 한 번 | v26에서 Task 사이 문제는 끝 리뷰만 잡음. 이번 과제에서도 끝 리뷰만으로 같은 결함을 잡음 |
| 고칠 때 계획의 이름·시그니처를 지키는 가장 작은 고침 먼저 | 이번 실측에서 고친 실행과 못 고친 실행을 가른 판단 |
| High·Medium은 재현해 본 뒤에만 기각 | 이번 실측에서 메인이 맞는 지적을 기각한 1회 |
| 진행 파일과 커밋 트레일러로 이어 하기 | 강제로 끊은 뒤 중복 없이 이어 감. 측정은 `.git/waygent/`에서 했고, 뒤에 superpowers처럼 스스로 무시되는 `.waygent/`로 옮김([모델 배치와 기록 위치](model-routing.md)) |
| 같은 모델 고정, 한도면 멈춤 | v26에서 싼 모델로 바꾼 구간이 5시간, $128을 버림 |
| 끝 리뷰와 실패 뒤 재시도만 한 등급 위 | 하네스 9개 조사와 이번 실측([모델 배치와 기록 위치](model-routing.md)). 효과는 재지 않음 |
| main/master에 커밋 안 함, push·PR 안 함 | 지난 비교에서 BMAD, Ralph 등이 main에 커밋 |

뺀 것: 브레인스토밍·스펙 단계, Task별 지시·보고 파일, 재리뷰 고리, 병렬 구현자, Task마다
사람 확인, 문서 생성, `CLAUDE.md`·`AGENTS.md` 수정.

## 문서

- [조사 방법](method.md): 설계 근거, 네 모델 분석, 과제, 조건, 격리, 채점, 한계
- [실측 결과](results.md): 조건별 표, 결함, 리뷰 비용, 컨텍스트, 이어 하기, 공존, Cursor, Codex
- [모델 배치와 기록 위치](model-routing.md): 하네스 9개의 조율자·구현자·리뷰어 모델, 기록 위치
- [analysis/](analysis/): 네 모델의 설계안 원문과 공통 프롬프트
- [results/](results/): 실행별 수치 JSON
- [harness/](harness/): 과제, 숨긴 테스트, 기준 구현, 드라이버, 채점기

## 다시 돌리려면

```bash
cd docs/research/2026-09-waygent-eval/harness
BENCH_TAG=mine python3 bench.py vanilla opus 1      # 조건 모델 회차
BENCH_TAG=mine python3 bench.py waygent opus 1
BENCH_TAG=mine python3 bench.py waygent sol 1       # Codex (gpt-5.6-sol high)
BENCH_TAG=mine ./run_batch.sh 4 jobs-main.txt        # 여러 개를 동시에
python3 judge.py mine                                # 블라인드 결함 채점(codex 필요)
python3 aggregate.py mine && python3 summarize.py mine
```

- 라이브 모델을 부릅니다. `scripts/verify.py`와 CI는 이 폴더의 코드를 돌리지 않습니다.
- superpowers 조건은 `~/.agents/plugins/superpowers`(6.4.1)를 씁니다.
- 원시 대화(`runs/`), 로그, 채점 사본은 커밋하지 않습니다(`harness/.gitignore`).
