# korean-writing-editor 테스트

`tests/products/korean-writing-editor/offline/cases.json`과 `tests/products/korean-writing-editor/offline/run.py`에서 서른한 개 속성 케이스와 변이 검사를 그대로 유지하세요.

## 결정적 픽스처

- trigger 작업은 긍정 기록과 near-miss 기록이 모두 필요합니다.
- mode, output, 보존, tier 작업은 맞는 `expected_mode`, `expected_tier`, `expected_noop` 기록이 필요합니다.
- 말투 케이스는 작은 어조·태도 구간을 보호합니다. 후보 문자열 전체가 원문과 같아야 한다고 요구하지 마세요.
- 혼합 규범 케이스는 이미 올바른 의무·양태 구간을 국소 철자 수정과 같은 기록에서 보호할 수 있습니다.
- 과정 서문이 있는 후보는 교체된 `norm-spacing-can-01` 속성에 실패해야 합니다.
- 픽스처 통과는 오프라인 오라클 계약만 증명합니다. 라이브 모델 품질을 증명하지 않습니다.

라이브 하니스 변경은 `tests/products/korean-writing-editor/live/live_cases.json`, `live_matrix.py`, `test_live_matrix.py`, `tests/products/korean-writing-editor/live/README.md`를 함께 맞춥니다. 라이브 케이스는 합성입니다. 이 아티팩트에 비공개 원고나 전체 트랜스크립트를 넣지 않습니다.

라이브 예산 변경은 119-producer, 3-reviewer, 122-baseline, 38-remediation, 160-total dry-run과 파서 단언을 동기화합니다. 보고서가 있는 resume 변경은 보고서가 없던 첫 발행과, 보고서 발행 뒤 크래시에 대한 실제 임시 Git 테스트가 필요합니다.

Remediation은 정규 전체 계획 순서의 불변 planned producer call ID를 하나 이상 런 식별에 묶습니다. 따로 승인된 reviewer 메커니즘이 설계되기 전에는 reviewer 호출을 보내지 않습니다. 유료 dispatch 전에 보고서 대상과 맞는 상태를 예약하세요. 최종 보고서 쓰기를 첫 소유 주장으로 쓰지 마세요.

## 라이브 하니스 불변

Dry-run은 `producer_calls=119`, `reviewer_calls=3`, `baseline_calls=122`, `remediation_calls=38`, `approved_total_ceiling=160`을 내야 합니다. 여러 사이클을 시작해도 승인된 160-call 결과 하나가 되지 않습니다.

모든 Codex 또는 Cursor 공급자 프로세스 호출 전에 러너는 CLI 가용성, argv, 불변 런 식별, 활성 보고서 임대를 검증한 뒤, 프로세스 호출 직전에 불변 시도 예약을 내구성 있게 기록합니다. 예약은 완전한 런 식별, 논리·실제 호출 ID, 공백 없는 양의 전역 호출 번호, producer 또는 reviewer 종류, 호스트, 요청 모델, 케이스 ID, 반복 인덱스를 묶습니다. 진짜 공급자 없는 `not_measured` 영수증만 예약 없이 호출 번호 0을 쓸 수 있습니다. `verified`, `partially_verified`, `failed`, `blocked` 영수증은 양의 예약 하나와 정확히 맞아야 하며, reviewer 영수증은 producer 예약과 맞을 수 없습니다. 크래시만 있는 예약은 청구된 채로 남고 고유 `:attempt-N` 재시도 ID를 만들며 예산과 보고서에 포함됩니다.

producer dispatch 뒤, 그리고 baseline의 reviewer dispatch 뒤에, 컨트롤러는 디스크에서 시도 예약과 영수증을 다시 읽고 정확한 연결을 검증하며, 계획된 논리 호출마다 내구성 있는 종료 영수증 하나를 요구합니다. 리뷰 패킷, 보고서, 상태, 횟수는 다시 읽은 내구성 아티팩트만 쓰고 메모리 속 dispatch 반환값을 쓰지 않습니다. Remediation은 producer만 보내며 reviewer 계획이 없습니다.

Dispatcher 반환은 완료 주장일 뿐입니다. 반환된 영수증은 다시 읽은 내구성 영수증 하나의 정확한 정규 바이트와 맞아야 합니다. 정규화된 producer 또는 reviewer 본문은 그 영수증의 정확한 양의 호출 경로가 소유하고 `response_sha256`과 맞아야 합니다.

하나의 `ReportLease`는 pending 보고서 예약부터 모든 producer·reviewer 호출과 최종 발행까지 대상 파일 FD 하나(`O_RDWR`, `O_NOFOLLOW`)와 증거 루트 `reports` 디렉터리 FD 하나를 유지합니다. 보고서는 `<evidence-root>/reports/`에 두며 추적 문서에 두지 않습니다. 임대는 보고서 경로 이름을 바꾸지 않습니다.

## 명령

```bash
python3 scripts/verify.py --skill korean-writing-editor
python3 scripts/verify.py
python3 tests/products/korean-writing-editor/offline/run.py --scope full
python3 tests/products/korean-writing-editor/live/live_matrix.py --dry-run
git diff --check
```

라이브 카나리는 선택이며 따로 보고합니다. 오프라인 픽스처 결과를 라이브 호출이나 모델 품질 증거로 설명하지 마세요. `SKILL.md`에 공급자 ID를 두지 마세요. 라이브 실행은 로컬, 명시적, 선택적, 비용이 들 수 있으며 CI가 요구하지 않습니다.
