# 검증

[English](../en/verification.md) · [호환성](compatibility.md) · [안전과 개인정보](safety-and-privacy.md)

필수 검증은 자격 증명과 모델 없이 돌아갑니다. 통과는 “지금 저장소 규칙이 맞다”는 뜻입니다. 모델이 글을 잘 고치거나 그림을 잘 만든다는 뜻은 아닙니다.

```bash
python3 scripts/verify.py
```

이 명령은 `--profile full`과 같습니다.

단계는 아래 순서입니다. 첫 실패에서 멈춥니다.

- repository-contract
- korean-package
- korean-offline
- korean-live-unit
- korean-live-dry-run
- image-contract
- image-inspector
- how-it-works-contract
- pre-sdd-review-contract
- pre-sdd-review-evidence
- python-compile

`windows-portable`는 `image-contract`, `image-inspector`, `pre-sdd-review-evidence`를 뺍니다. 이식 가능한 `pre-sdd-review-contract`는 남깁니다. 라이브 `--execute`는 넣지 않습니다.

```bash
python3 scripts/verify.py --profile full
python3 scripts/verify.py --profile windows-portable
```

제품 안내는 [`korean-writing-editor`](../../../skills/korean-writing-editor/README.md), [`image-workbench`](../../../skills/image-workbench/README.md), [`how-it-works`](../../../skills/how-it-works/README.md), [`pre-sdd-review`](../../../skills/pre-sdd-review/README.md)를 보세요.

`pre-sdd-review`만 검증하려면 다음 명령을 씁니다.

```bash
python3 scripts/verify.py --skill pre-sdd-review
```

## 공유 증거 문장

Offline fixtures: deterministic contract evidence only.

Live execution: local, explicit, optional, potentially billable, and never required by CI.

## 오프라인 픽스처

오프라인 스위트는 결정적 계약만 증명합니다. 제품별 픽스처 경로는 각 제품 관리자 `testing.md`를 보세요.

현재 Korean 오프라인은 33개(`normative=10`)이며 나머지 픽스처 분류는 유지합니다. 새 Korean 라이브 증거는 runner 18을 사용하며 과거 runner 영수증은 runner 18 실행을 증명하지 않습니다. Image는 31개 픽스처와 17개 mutation을 검사합니다.

Korean 후보는 hard 실패가 있으면 `failed`가 우선합니다. hard 검사를 통과해도 의미·귀속·요청된 편집 실행이 미관측이면 `partially_verified`입니다. 오프라인 계약 성공만으로 라이브 상태를 부여하지 않습니다. How의 fence/hop, loading, syntax, meaning은 별도 증거가 필요합니다. 과거 smoke는 `historical-unbound`이며 현재 메타데이터 결속만으로 모델 실행을 증명하지 않습니다.

`pre-sdd-review`의 공급자 없는 픽스처는 지시와 패키지 계약만 검증합니다. 리뷰어 독립성, 의미 완전성, 라이브 리뷰 품질을 증명하지 않습니다.

Evidence 단계는 `tests/products/pre-sdd-review/evidence/`에서 `evidence.py`를 검사합니다. 네트워크, 모델, provider, telemetry를 호출하지 않습니다.

Pre-SDD는 schema 2 record를 `historical-unbound`로 읽기만 지원합니다. 변경 명령은 schema 3의 checkout 결속이 필요합니다. schema 2 pending record는 보존하고 새 run을 시작합니다. schema 3 `--version`은 canonical JSON `{"cli_version":"3.0.0","schema":3,"skill_name":"pre-sdd-review"}`과 마지막 LF 하나를 출력하며 evidence home을 만들지 않습니다.

비-Windows의 `windows-portable` 통과는 native Windows 지원을 증명하지 않습니다. native Windows와 Linux는 그 환경에서 evidence 단계가 돌기 전까지 `not_measured`입니다.

통과는 일반 품질을 증명하지 않습니다. 라이선스는 Apache-2.0입니다.

## 라이브 실행

Korean 라이브 범위는 14 cases / 17 repeats를 유지합니다.

라이브 평가는 로컬에서만 합니다. 명시 플래그, 이름 있는 런타임, 제한된 호출 예산, 추적 소스 밖의 증거 루트가 있을 때 합니다. CI는 라이브를 요구하지 않습니다. 공급자 프로세스를 조용히 바꾸지 않습니다.

상태 이름 뜻:

- `verified`: 확인됨
- `partially_verified`: 일부만 확인됨
- `failed`: 실패
- `blocked`: 실행 전에 막힘
- `not_measured`: 아직 이 환경에서 확인하지 않음

상태 어휘는 `verified`, `partially_verified`, `failed`, `blocked`, `not_measured`입니다. 오프라인 성공을 `partially_verified`로 바꾸지 마세요. 공급자 불가를 통과로 바꾸지 마세요.

한국어 라이브 한도는 관리자 문서의 119 / 3 / 122 / 38 / 160 예산을 따릅니다. 운영 절차는 `tests/products/korean-writing-editor/live/README.md`에 있습니다. 사용자 한국어 원문, 공급자 응답, 비공개 참조 이미지, 생성 이미지, 자격 증명, receipt는 커밋하지 않습니다.

## 한계

측정된 지원과 픽스처 결과만 보고하세요. 플러그인 디렉터리 등록, 모든 호스트 지원, 일반 품질, 라이브 이미지 품질, 권리 확정, 공급자 우월을 주장하지 마세요.
