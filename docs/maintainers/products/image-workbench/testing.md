# image-workbench 테스트

예시 형식이나 판정 규칙을 바꾸려면 평가기 self-test와, 맞아야 하는 예시·
잘못 친 이름 예시를 먼저 고칩니다. 테스트가 실패하는 것을 본 뒤 구현합니다.
예시 경로는 `tests/products/image-workbench/`입니다.

## 결정적 픽스처

- 라우팅, 권한, ImageSpec, 핸드오프, inspector 기대는
  `tests/products/image-workbench/cases.json`과
  `tests/products/image-workbench/run.py`가 소유합니다.
- inspector 출력 변경은 `tests/products/image-workbench/test_inspect_asset.py`,
  평가기 full-scope 기대, 공개 문서를 함께 고칩니다. 동작이 바뀌면 SemVer를
  올립니다.
- 런타임 inspector는 `skills/image-workbench/scripts/inspect_asset.py`입니다.
  테스트는 `tests/products/image-workbench/test_inspect_asset.py`에 둡니다.
  런타임 스크립트에 unittest 스위트를 넣지 마세요.
- inspector는 실제 스킬 루트에서 호출합니다. 저장소 상대 `skills/` 경로로
  호출하지 마세요.
- 평가기 또는 inspector 명령·패키지 경로 변경은
  `tests/products/image-workbench/run.py`와 `python3 scripts/verify.py`와
  맞춥니다.
- `test_payload_docs.py`는 임시 standalone 복사본의 README 상대 링크가
  payload 안에서 해석되는지 확인합니다. 공개 docs URL은 저장소 안의 대응
  파일까지만 검사하며 원격 HTTP 응답을 증명하지 않습니다.
- evaluator는 기존 8개 mutation에 expected/candidate 동시 오염 9개를 더해
  읽기 전용 행동 경계를 검사합니다. 실제 이미지 호출 없이 실행합니다.

오프라인 예시는 32개입니다. 그림이 좋아 보인다는 증명이 아닙니다. 실제 Grok
확인 절차는 `tests/products/image-workbench/live/README.md`에 있으며 CI가
돌리지 않습니다. 오프라인 통과와 실제 그림 확인은 따로 적습니다.

## 명령

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --skill image-workbench
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py
PYTHONDONTWRITEBYTECODE=1 python3 tests/products/image-workbench/run.py --self-test
PYTHONDONTWRITEBYTECODE=1 python3 tests/products/image-workbench/run.py --scope full
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/image-workbench -p 'test_*.py'
IMAGE_WORKBENCH_EXTRACTED_ROOT=/path/to/extracted/image-workbench
IMAGE_WORKBENCH_INSPECTOR="$IMAGE_WORKBENCH_EXTRACTED_ROOT/scripts/inspect_asset.py" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/image-workbench -p 'test_*.py'
PYTHONDONTWRITEBYTECODE=1 python3 tests/products/image-workbench/run.py --scope full --skill-root "$IMAGE_WORKBENCH_EXTRACTED_ROOT"
git diff --check
```

마지막 두 명령은 공통 `verify-download`가 추출 payload에 적용하는 제품 smoke의
경계를 보여 줍니다. 동일 archive를 다시 수동 추출해 중복 검사하지 않습니다.

실제 그림 생성은 CI가 요구하지 않습니다. 로그인과 비용이 들 수 있습니다.
오프라인 통과를 “그림이 좋다”로 바꾸지 마세요.
