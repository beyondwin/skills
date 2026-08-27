# 검증

[English](../en/verification.md) · [호환성](compatibility.md) · [안전과 개인정보](safety-and-privacy.md)

필수 검증은 자격 증명과 모델 없이 돌아갑니다.

```bash
python3 scripts/verify.py
```

이 명령은 `--profile full`과 같습니다. 단계는 contract, korean-offline, image-contract, image-inspector, korean-live-unit, korean-live-dry-run, python-compile 순서이며, 첫 실패 단계에서 멈춥니다. `windows-portable`는 Codex 전용 `image-contract`와 `image-inspector`를 제외합니다. 라이브 `--execute`는 포함하지 않습니다.

```bash
python3 scripts/verify.py --profile full
python3 scripts/verify.py --profile windows-portable
```

제품 안내는 [`korean-writing-editor`](../../../skills/korean-writing-editor/README.md), [`image-workbench`](../../../skills/image-workbench/README.md), [`graspic`](../../../skills/graspic/README.md)를 보세요.

## 공유 증거 문장

Offline fixtures: deterministic contract evidence only.

Live execution: local, explicit, optional, potentially billable, and never required by CI.

## 오프라인 픽스처

오프라인 스위트는 결정적 계약만 증명합니다.

- `korean-writing-editor`: `tests/korean-writing-editor/offline/`의 트리거·모드·보존·출력 픽스처
- `image-workbench`: `tests/image-workbench/`의 라우팅·권한·ImageSpec·핸드오프·inspector 픽스처
- `graspic`: `tests/graspic/cases.json` 형태 픽스처와 `tests/contract/test_graspic.py` 페이로드 계약

통과는 일반 한국어 편집 품질, 의미 동등, 라이브 이미지 품질, 상업 허가, 더 나은 공급자, 런타임 동등성을 증명하지 않습니다. 라이선스는 Apache-2.0입니다.

## 라이브 실행

라이브 평가는 로컬에서만 하며, 명시 플래그, 이름 있는 런타임, 제한된 호출 예산, 추적 소스 밖의 증거 루트가 있을 때 합니다. CI는 라이브를 요구하지 않습니다. 공급자 프로세스를 조용히 바꾸지 않습니다.

상태 어휘는 `verified`, `partially_verified`, `failed`, `blocked`, `not_measured`입니다. 오프라인 성공을 `partially_verified`로 바꾸지 말고, 공급자 불가를 통과로 바꾸지 마세요.

한국어 라이브 한도는 maintainer 문서의 119 / 3 / 122 / 38 / 160 예산을 따릅니다. 운영 절차는 `tests/korean-writing-editor/live/README.md`에 있습니다. 사용자 한국어 원문, 공급자 응답, 비공개 참조 이미지, 생성 이미지, 자격 증명, receipt는 커밋하지 않습니다.

## 한계

측정된 지원과 픽스처 결과만 보고하세요. 플러그인 디렉터리 등록, 모든 호스트 지원, 일반 품질, 라이브 이미지 품질, 권리 확정, 공급자 우월을 주장하지 마세요.
