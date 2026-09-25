# image-workbench 테스트

예시 경로는 `tests/products/image-workbench/`입니다. 예시 형식이나 판정 규칙을
바꾸려면 먼저 평가기 self-test와 예시(맞아야 하는 예시, 잘못 친 이름 예시)를
고칩니다. 테스트가 실패하는 것을 확인한 뒤 구현합니다.

## 결정적 픽스처

결정적 픽스처는 실제 이미지 호출 없이 항상 같은 결과를 내는 오프라인
예시입니다.

- 라우팅, 권한, ImageSpec, 핸드오프, inspector 기대값은
  `tests/products/image-workbench/cases.json`과
  `tests/products/image-workbench/run.py`가 정합니다.
- 런타임 inspector는 `skills/image-workbench/scripts/inspect_asset.py`입니다.
  테스트는 `tests/products/image-workbench/test_inspect_asset.py`에 둡니다.
  런타임 스크립트에 unittest 스위트를 넣지 마세요.
- inspector 출력이 바뀌면 `tests/products/image-workbench/test_inspect_asset.py`,
  평가기 full-scope 기대값, 공개 문서를 함께 고칩니다. 동작이 바뀌면 SemVer를
  올립니다.
- inspector는 실제 스킬 루트에서 호출합니다. 저장소 기준 `skills/` 경로로
  호출하지 마세요.
- 평가기 또는 inspector의 명령·패키지 경로가 바뀌면
  `tests/products/image-workbench/run.py`와 `python3 scripts/verify.py`를
  맞춥니다.
- `test_payload_docs.py`는 임시 standalone 복사본에서 README 상대 링크가
  payload 안에서 풀리는지 확인합니다. 공개 docs URL은 저장소 안의 대응
  파일까지만 검사하며 원격 HTTP 응답을 증명하지 않습니다.
- evaluator는 기존 8개 mutation에 expected/candidate 동시 오염 9개를 더해
  읽기 전용 행동 경계를 검사합니다. 실제 이미지 호출 없이 실행합니다.

오프라인 예시는 32개입니다. 그림이 좋아 보인다는 증명은 아닙니다. 실제 Grok
확인 절차는 `tests/products/image-workbench/live/README.md`에 있으며 CI는 돌리지
않습니다. 오프라인 통과와 실제 그림 확인 결과는 따로 적습니다.

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

마지막 두 명령은 공통 `verify-download`가 압축을 푼 payload에 적용하는 제품
확인(smoke)의 범위를 보여 줍니다. 같은 archive를 다시 손으로 풀어 중복 검사하지
않습니다.

실제 그림 생성은 CI가 요구하지 않습니다. 로그인과 비용이 들 수 있습니다.
오프라인 통과를 "그림이 좋다"로 바꿔 말하지 마세요.
