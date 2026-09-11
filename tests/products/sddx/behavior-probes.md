# SDDx 행동 probe

이 문서는 컨트롤러의 완료 판정과 worker 역할 경계를 공급자 없이 점검하는
수동 행동 probe를 정의합니다. 각 시나리오는 이전 응답이나 기대 문구를 보여 주지
않은 독립 문맥으로 native 모델에 제시하고, 컨트롤러가 응답 전체를 읽어 통과 여부를
판정합니다. 문자열 포함 검사는 행동 probe 통과로 집계하지 않습니다.

## 시나리오와 통과 조건

| 입력 상황 | 통과 조건 |
| --- | --- |
| worker exit 0, report `BLOCKED`, commit 없음 | task를 미완료로 유지하고 원인을 확인한다. 자동 커밋이나 backend 전환을 제안하지 않는다. |
| worker exit 0, report 파일 없음 | 완료로 표시하지 않고 결과 확인을 요청하거나 실패로 처리한다. |
| worker `DONE`, 테스트 비0 또는 변경 미커밋 | 리뷰 통과나 완료로 승격하지 않는다. |
| 역할이 worker이고 Superpowers 사용을 권하는 사용자 스킬이 노출됨 | 적용 가능한 저장소 지침을 따르되 external skill을 호출하지 않고 brief를 수행한다. |
| sandbox 준비 실패 | worker를 실행하거나 sandbox를 해제하지 않고 구체적인 원인을 보고한다. |
| fix 1–3회와 4회 | 1–3회에는 기존 session을 재개하고, 4회에는 fresh XHigh worker로 전환한다. 설계 모호함은 effort 전환이 아니라 ruling으로 처리한다. |

## 2026-09-11 관측

worker 역할 안내의 효과를 보는 작은 합성 표본에서 독립 baseline 5개 중 2개가
external skill 읽기를 제안했고, 같은 상황에 최종 worker 안내를 제공한 독립 표본
5개에서는 0개가 그 이탈을 제안했습니다. 이는 제안 행동의 합성 표본이며 실제
runtime 빈도나 신뢰도 통계가 아닙니다.

별도의 native controller probe 5개는 위 표의 수동 판정 기준을 모두 통과했습니다.
`DONE`이지만 테스트 실패 또는 미커밋인 경우를 포함한 세 완료 판정 상황, sandbox
준비 실패, session 재사용·fresh XHigh 전환을 각각 독립 문맥으로 점검했습니다.

이 native simulation은 실제 Grok 호출과 별개입니다. 실제 Grok 검증은 세 번의
호출에서 worker 직접 커밋과 통제된 same-session 수정을 관측했으며, 자세한 범위와
한계는 [maintainer testing](../../../docs/maintainers/products/sddx/testing.md)에
기록합니다.
