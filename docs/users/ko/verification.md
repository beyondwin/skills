# 검증

[English](../en/verification.md) · [호환성](compatibility.md) · [안전과 개인정보](safety-and-privacy.md)

필수 검사는 자격 증명 없이 돌고 모델을 부르지 않습니다. 통과는 저장소가 자기 규칙을 지키고 있다는 뜻입니다. 모델이 글을 잘 고치거나 그림을 잘 만든다는 뜻은 아닙니다.

말 뜻: 픽스처는 미리 만들어 둔 검사 예시입니다. smoke는 실제로 한 번 돌려 본 기록입니다. `not_measured`는 아직 이 환경에서 확인하지 않음, `current-bounded`는 버전과 hash만 기록에 묶였다는 뜻입니다.

```bash
python3 scripts/verify.py
```

인자 없이 돌리면 아래 순서로 모든 단계를 돌리고 첫 실패에서 멈춥니다.

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
- sddx-contract
- waygent-contract
- python-compile

CI는 Ubuntu에서 이 검증을 돌립니다. Ubuntu CI 통과는 macOS 지원을 증명하지 않습니다.

스킬 하나만 검사하려면 이름을 넘깁니다. `product-contract`, 그 스킬의 단계, `python-compile`만 돕니다. 여섯 이름 모두 됩니다. 예:

```bash
python3 scripts/verify.py --skill pre-sdd-review
python3 scripts/verify.py --skill sddx
python3 scripts/verify.py --skill waygent
```

제품 안내: [`korean-writing-editor`](../../../skills/korean-writing-editor/README.ko.md), [`image-workbench`](../../../skills/image-workbench/README.ko.md), [`how-it-works`](../../../skills/how-it-works/README.ko.md), [`pre-sdd-review`](../../../skills/pre-sdd-review/README.ko.md), [`sddx`](../../../skills/sddx/README.ko.md), [`waygent`](../../../skills/waygent/README.ko.md).

## 공유 증거 문장

Offline fixtures: deterministic contract evidence only.

Live execution: local, explicit, optional, potentially billable, and never required by CI.

## 오프라인 픽스처

오프라인 검사는 고정된 계약만 증명합니다. 제품별 픽스처 경로는 각 제품 관리자 `testing.md`에 있습니다.

- Korean Writing Editor: 오프라인 33개(`normative=10 preservation=8 noop=6 voice=4 trigger=5`). 새 라이브 증거는 runner 18을 쓰며, 예전 runner 영수증은 거절됩니다.
- Image Workbench: 픽스처 32개와 mutation(일부러 망가뜨린 변형) 17개.
- 한국어 후보: hard 검사(필수 검사)가 하나라도 실패하면 `failed`입니다. hard 검사를 통과해도 의미·귀속·요청한 편집이 관측되지 않으면 `partially_verified`입니다. 오프라인 통과만으로 라이브 상태가 되지 않습니다.
- How It Works: fence/hop 유효성, loading, syntax, meaning은 각각 따로 증거가 필요합니다. 메타데이터가 맞는 것만으로 모델 실행을 증명하지 않습니다.

`pre-sdd-review`의 공급자 없는 픽스처는 지시와 패키지 계약만 검증합니다. 리뷰어 독립성, 의미 완전성, 라이브 리뷰 품질을 증명하지 않습니다.

`pre-sdd-review-evidence` 단계는 `tests/products/pre-sdd-review/evidence/`에서 `evidence.py`를 검사합니다. 네트워크, 모델, provider, telemetry를 부르지 않습니다.

Pre-SDD 기록기는 schema 4만 읽고 쓰며, 기록을 바꾸는 명령은 그 checkout 결속이 필요합니다. 6.0.0 전 기록기가 쓴 schema 2·schema 3 record는 모든 명령에서 `schema-unsupported`로 거절되고, `summary`는 `unsupported_records`로 셉니다. 새 run을 막지 않으며, 치우려면 그 파일을 지웁니다. `--version`은 `"schema":4,"skill_name":"pre-sdd-review"`가 든 canonical JSON 한 줄과 LF 하나를 출력하고 evidence home을 만들지 않습니다. 정확한 바이트는 [기록기 README](../../../skills/pre-sdd-review/evidence/README.md)를 보세요.

통과는 일반 품질을 증명하지 않습니다.

## 라이브 실행

라이브 실행은 로컬에서만 합니다. 명시 플래그, 이름 있는 런타임, 호출 상한, 추적 소스 밖의 증거 폴더가 있어야 합니다. CI는 라이브를 요구하지 않고, 공급자를 몰래 바꾸지 않습니다.

한국어 라이브 범위는 14 cases / 17 repeats입니다. 호출 상한은 관리자 문서의 119 / 3 / 122 / 38 / 160 예산을 따릅니다. 운영 절차는 `tests/products/korean-writing-editor/live/README.md`에 있습니다.

상태 이름:

- `verified`: 확인됨
- `partially_verified`: 일부만 확인됨
- `failed`: 실패
- `blocked`: 실행 전에 막힘
- `not_measured`: 아직 이 환경에서 확인하지 않음

오프라인 통과를 `partially_verified`로, 공급자를 쓸 수 없는 상황을 통과로 보고하지 마세요. 사용자 한국어 원문, 공급자 응답, 비공개 참조 이미지, 생성 이미지, 자격 증명, receipt는 커밋하지 않습니다.

## 한계

측정한 지원과 픽스처 결과만 보고하세요. 플러그인 디렉터리 등록, 모든 호스트 지원, 일반 품질, 라이브 이미지 품질, 권리 확정, 공급자 우월을 주장하지 마세요.
