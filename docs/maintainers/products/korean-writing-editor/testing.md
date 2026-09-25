# korean-writing-editor 테스트

오프라인 픽스처(모델 없이 규칙을 잠그는 고정 테스트 예시)는
`tests/products/korean-writing-editor/offline/`에 있습니다. 그 안의 `cases.json`과
`run.py`에서 서른네 개 속성 케이스(`normative=10 preservation=8 noop=6 voice=4 trigger=6`)와
변이 검사를 그대로 유지하세요. 변이 검사는 일부러 망가뜨린 후보가 실패하는지
확인합니다.

이 문서의 숫자 한도는 라이브 호출 예산입니다.

## 설치본 검사

`--scope full`은 `README.md`와 `README.en.md`도 필수 payload(설치되는 파일 묶음)
파일로 읽습니다. 그리고 복사한 독립 설치본(standalone payload)에서 모든 로컬 링크가
payload 안의 실제 파일로 이어지는지 검사합니다. 저장소 문서 링크는 절대 GitHub
URL이므로 네트워크로 응답 상태를 확인하지 않습니다.

제품 패키지 회귀 테스트는 `release.toml`, `SKILL.md`, 날짜가 있는 CHANGELOG
항목, 깨진 README 링크의 거부를 함께 확인합니다.

## 결정적 픽스처

- trigger 작업에는 긍정 기록과 near-miss(비슷하지만 대상이 아닌 요청) 기록이 모두
  필요합니다.
- mode, output, 보존, tier 작업에는 맞는 `expected_mode`, `expected_tier`,
  `expected_noop` 기록이 필요합니다.
- 말투 케이스는 작은 어조·태도 구간을 보호합니다. 후보 문자열 전체가 원문과
  같아야 한다고 요구하지 마세요.
- 혼합 규범 케이스는 이미 올바른 의무·양태 구간을 국소 철자 수정과 같은
  기록에서 보호할 수 있습니다.
- 과정 서문이 있는 후보는 교체된 `norm-spacing-can-01` 속성에 실패해야 합니다.
- `norm-grammar-particle-correct-09`와 `norm-grammar-particle-polish-10`은 같은
  명백한 중복 조사 오류가 두 모드에서 모두 교정되는지 확인합니다. 원문 오류를
  그대로 둔 후보와, 양가적인 마지막 절을 확신으로 바꾼 후보는 각자의 독립 변이
  검사에 실패해야 합니다.
- `trigger-diagnose-06`은 diagnose 소견입니다. 다시 쓴 초안이나 과정 서문이
  있으면 실패합니다.
- 다음 변이도 각각 실패해야 합니다: `norm-spacing-can-01`의 영문·한글 스킬 사용
  서문, `meaning-negation-01`의 `수도 있다` 치환, `trigger-translation-03`의
  거절 후 번역.
- 픽스처 통과는 오프라인 오라클(정답 판정기) 계약만 증명합니다. 라이브 모델
  품질을 증명하지 않습니다.

## 라이브 증거의 한계

운영 절차의 원본은 `tests/products/korean-writing-editor/live/README.md`입니다.
예약(reservation), 실행 기록(receipt), 보고서 점유(lease), 상태 이름은 그 문서가
정합니다.

라이브 하니스(실제 모델 호출 평가 도구)를 바꾸면
`tests/products/korean-writing-editor/live/live_cases.json`, `live_matrix.py`,
`test_live_matrix.py`, `tests/products/korean-writing-editor/live/README.md`를 함께
맞춥니다. 라이브 케이스는 합성 예시입니다. 이 파일들에 비공개 원고나 전체 대화
기록(transcript)을 넣지 않습니다.

이번 보강 작업(hardening series)의 제품 증거는 runner 18(라이브 실행기 버전
18)로 새로 만들어야 합니다. runner 10부터 17까지의 과거 실행 기록은 읽을 수
있지만, runner 18 실행을 재개하거나 건너뛰는 근거로 쓰지 않습니다.

### 예산

라이브 예산을 바꾸면 119-producer, 3-reviewer, 122-baseline, 38-remediation,
160-total dry-run과 파서 단언을 함께 맞춥니다. producer는 편집 결과를 만드는
호출, reviewer는 그 결과를 검토하는 호출, remediation은 따로 승인된 보완
실행입니다.

Dry-run(호출 없이 계획만 출력)은 `producer_calls=119`, `reviewer_calls=3`,
`baseline_calls=122`, `remediation_calls=38`, `approved_total_ceiling=160`을
내야 합니다. 사이클을 여러 번 시작해도 승인된 160-call 결과 하나가 되지
않습니다.

### 재개와 보완 실행

- 보고서가 있는 resume(중단된 실행 재개) 변경에는 실제 임시 Git 테스트 두 가지가
  필요합니다. 보고서가 없던 첫 발행, 그리고 보고서 발행 뒤의 크래시입니다.
- Remediation은 정규 전체 계획 순서의 불변 planned producer call ID를 하나 이상
  run 식별에 묶습니다.
- 따로 승인된 reviewer 메커니즘이 설계되기 전에는 reviewer 호출을 보내지
  않습니다.
- 유료 호출(dispatch) 전에 보고서 대상과 맞는 상태를 예약하세요. 최종 보고서
  쓰기를 첫 소유 주장으로 쓰지 마세요.

## 명령

```bash
python3 scripts/verify.py --skill korean-writing-editor
python3 scripts/verify.py
python3 tests/products/korean-writing-editor/offline/run.py --scope full
python3 tests/products/korean-writing-editor/live/live_matrix.py --dry-run
git diff --check
```

라이브 카나리(소규모 실제 호출 확인)는 선택이며 따로 보고합니다. 오프라인 픽스처
결과를 라이브 호출이나 모델 품질의 증거로 설명하지 마세요. `SKILL.md`에 공급자
ID를 두지 마세요. 라이브 실행은 로컬에서, 명시적으로, 선택으로만 하며 비용이 들
수 있고, CI가 요구하지 않습니다.
