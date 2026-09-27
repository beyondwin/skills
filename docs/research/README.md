# 조사 / Research

다른 저장소의 스킬과 워크플로를 직접 설치해 돌려 본 조사 기록입니다. 이 저장소
제품의 계약을 정하지 않습니다. 결론은 조사한 날짜, 버전, 모델에 묶여 있습니다.

These are point-in-time research records on third-party skills. They do not
define any contract for this repository's products.

| 조사 | 날짜 | 무엇 |
| --- | --- | --- |
| [에이전트 워크플로 비교](2026-09-agent-workflow-comparison/README.md) | 2026-09-27 | superpowers, dryforge 등 9개 도구와 기본 Claude Code를 같은 과제 3개로 실측 |
| [waygent 설계와 실측](2026-09-waygent-eval/README.md) | 2026-09-27 | 위 조사로 만든 `waygent` 스킬을 기본, superpowers와 10-Task 과제로 22회 실측 |

- 원시 대화 기록, 공급자 영수증, 생성된 과제 저장소는 커밋하지 않습니다.
  집계한 수치와 채점 결과만 남깁니다.
- 실측 하네스는 라이브 모델을 호출합니다. `scripts/verify.py`와 CI는 이 폴더의
  코드를 실행하지 않습니다.
