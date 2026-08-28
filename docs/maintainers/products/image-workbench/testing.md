# image-workbench 테스트

픽스처 스키마나 판정 규칙을 바꾸려면 평가기 self-test와 긍정/near-miss 픽스처를 먼저 고쳐 RED를 확인한 뒤 구현합니다.

## 결정적 픽스처

- 라우팅, 권한, ImageSpec, 핸드오프, inspector 기대는 `tests/products/image-workbench/cases.json`과 `tests/products/image-workbench/run.py`가 소유합니다.
- inspector 출력 변경은 `tests/products/image-workbench/test_inspect_asset.py`, 평가기 full-scope 기대, 공개 문서를 함께 고칩니다. 동작이 바뀌면 SemVer를 올립니다.
- 런타임 inspector는 `skills/image-workbench/scripts/inspect_asset.py`입니다. 테스트는 `tests/products/image-workbench/test_inspect_asset.py`에 둡니다. 런타임 스크립트에 unittest 스위트를 넣지 마세요.
- inspector는 실제 스킬 루트에서 호출합니다. 저장소 상대 `skills/` 경로로 호출하지 마세요.
- 평가기 또는 inspector 명령·패키지 경로 변경은 `tests/products/image-workbench/run.py`와 `python3 scripts/verify.py`와 맞춥니다.

오프라인 픽스처는 이미지 품질 증명이 아닙니다. 라이브 이미지 카나리는 선택이며 이 오프라인 수락과 따로 보고합니다. 상태, 비용/동의 경계, 출력 증거를 구분하세요.

## 명령

```bash
python3 scripts/verify.py --skill image-workbench
python3 scripts/verify.py
python3 tests/products/image-workbench/run.py --self-test
python3 tests/products/image-workbench/run.py --scope full
python3 -m unittest discover -s tests/products/image-workbench -p 'test_*.py'
git diff --check
```

라이브 이미지 호출은 CI가 요구하지 않으며 자격 증명과 비용이 들 수 있습니다. 오프라인 통과를 라이브 시각 결과로 바꾸지 마세요.
