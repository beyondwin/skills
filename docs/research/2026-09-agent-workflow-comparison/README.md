# 에이전트 워크플로 비교 (2026-09)

superpowers를 쓰는 사람이 dryforge나 다른 워크플로 도구로 바꿀 이유가 있는지,
README가 아니라 실측으로 확인한 기록입니다.

- 대상 9개: superpowers 6.4.1, dryforge 1.3.7, workflow-orchestrator 1.5.0
  (jha0313/skills_repo), mattpocock/skills 1.2.3, gstack 1.91.2.0, BMAD-METHOD 6.12.0,
  Spec Kit(`c00dc05`), OpenSpec 1.13.2, Ralph Wiggum 루프(`88d488a`). 대조군은 기본 Claude Code입니다.
- 실측: Claude Code 2.1.280, Opus 5.5. 과제 3개 × 조건 10개 = 30회를 끝까지 돌렸고,
  공존 실험 4회를 더했습니다. 에이전트 비용은 합계 $124입니다. gstack 3건은 과제끼리
  상태가 섞인 첫 실행을 버리고, 실행마다 상태 폴더를 따로 두고 다시 돌린 값입니다.

## 결론

**superpowers를 그대로 쓰세요.** 바꿀 근거가 나오지 않았습니다.

- 결과 품질은 도구마다 거의 같았습니다. 기본 Claude Code를 포함한 10개 조건이
  새 CLI 과제와 버그 수정 과제를 모두 맞게 끝냈습니다. 기능 결함은 30회 중
  1회(mattpocock S2)뿐이었고, superpowers는 0회였습니다.
- 기존 코드 과제(S2 $0.42)와 버그 수정(S3 $0.21)에서 가장 싼 축이었습니다. 기본,
  mattpocock과 같은 급입니다. 새 프로젝트(S1)에서는 $3.89로 중간이었습니다.
- 디버깅·리뷰·완료 전 검증 스킬은 mattpocock, BMAD, Spec Kit(버그 확장)에도 있습니다.
  superpowers의 차이는 세션 시작 훅이 이 스킬들을 사람이 부르지 않아도 켠다는 점입니다.
- 이 저장소의 `sddx`와 `pre-sdd-review`는 지금 superpowers 모양의 스펙·계획 파일을
  입력으로 받습니다. dryforge의 `.dryforge/plan.md`(YAML 그래프)를 받는지는 시험하지
  않았습니다. 도구를 통째로 바꾸면 이 흐름부터 다시 확인해야 합니다.

superpowers의 약점도 확인했습니다. S2에서 쿠폰 조합 규칙을 묻지 않고 틀리게
가정했습니다(설계 승인 때 사용자가 잡음). S1에서는 설계 절마다 확인을 받아 사람이
11번 답해야 했습니다.

**dryforge는 바꾸지 말고 옆에 두는 정도가 맞습니다.** 틀리면 비싼 새 기능이나 새
프로젝트에서만 `/dryforge:ready`로 부르세요.

- 좋았던 점: S2에서 틀린 가정이 없었습니다. 문서와 코드의 충돌을 첫 질문으로 물었고,
  세 과제 모두 git 지시를 지켰습니다.
- 대가: superpowers보다 2.6배(S1), 9.6배(S2), 15배(S3) 비쌌습니다. 과제마다 문서를
  15~20개 만들었고, `CLAUDE.md`와 `AGENTS.md`를 백업한 뒤 다시 씁니다. 이 저장소처럼
  `AGENTS.md`를 직접 관리하는 곳에는 맞지 않습니다.
- 공존: 둘을 함께 설치해도 `/dryforge:ready`로 부르면 dryforge가 주도했습니다.
  명령 없이 말하면 superpowers가 켜집니다. 첫 턴만 확인했고, `go` 단계의 간섭은
  재지 않았습니다.

## 내 상황이라면

| 상황 | 추천 | 근거 |
| --- | --- | --- |
| 작은 버그·설정 수정 | 기본 또는 superpowers | S3에서 $0.13~0.21, 1분 안팎. 모두 회귀 테스트 추가 |
| 기존 코드에 기능 추가 | superpowers | S2 $0.42. 충돌은 잡았지만 조합 규칙은 짐작했으니 설계 승인 때 꼼꼼히 읽기 |
| 요구가 모호한 새 기능, 틀리면 비쌈 | dryforge `/ready` 추가 | S2 틀린 가정 0, 충돌 선질문, git 규율. 비용 약 10배, 문서 많음 |
| 사람 손을 최소로 | workflow-orchestrator 또는 BMAD | S1 사람 답변 2~3번. BMAD는 git 지시를 어기고 main에 커밋함 |
| 결정마다 깊게 검토받고 싶음 | gstack(신중히) | 결정마다 한 번씩 물어 S1 29번 답변, 116분, $36. S3에서 push 금지를 어김. Codex를 자동 호출 |
| 명세 문서를 저장소에 남기는 팀 | OpenSpec | S1·S2에서 Spec Kit보다 쌌고(S2 $1.07 대 $5.21) 사람 답변도 적었음. Spec Kit은 충돌을 묻지 않고 헌법으로 정함 |
| 사람 없이 오래 돌리기 | Ralph | 요구사항 대화 뒤 자동. 매 반복 main 커밋·태그, 중간 지시 통로 없음 |

## 문서

- [조사 방법](method.md): 정적 분석, 격리, 모의 사용자, 채점, 파일럿에서 고친 것, 한계
- [도구별 특징](tools.md): 9개 도구의 설계와 흐름, 분량, 버전
- [실측 결과](results.md): 과제별 표, 반복 패턴, 따로 볼 실행, 공존 실험
- [보고서 HTML](report.html): 위 내용을 한 페이지로 본 것
- [`results/`](results/): 집계 수치(`summary-main.json`), 표, 공존 실험 기록
- [`harness/`](harness/): 다시 돌리는 코드. 라이브 모델을 부르므로 CI에서 돌지 않습니다

## 다시 돌리려면

```bash
harness/fetch_tools.sh /tmp/probe-work        # 도구를 측정한 커밋으로 받기
cd /tmp/probe-work/probe
python3 runner.py 8 s3:vanilla s3:superpowers  # 과제:조건 목록, 동시 8개
./judge_all.sh && python3 aggregate.py main
```

- superpowers는 `~/.agents/plugins/superpowers`에 설치된 6.4.1을 씁니다.
- gstack은 실행마다 `GSTACK_HOME`을 실행 폴더 안에 둡니다(`conditions.json`의 `$RUN`).
- 원시 대화(`runs/`)와 로그는 커밋하지 않습니다(`harness/.gitignore`).
