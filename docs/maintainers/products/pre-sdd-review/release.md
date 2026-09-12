# pre-sdd-review 릴리스

이 문서는 Pre-SDD Review의 독립 패키징 절차를 소유합니다.
version source is `skills/pre-sdd-review/release.toml`. `SKILL.md`의
`metadata.version`은 검증된 복사본입니다. `CHANGELOG.md`는 사람이 읽는 계약
이력입니다.

## Check, build, and verify download

공급자 없는 제품 검증을 실행한 뒤 새 빈 디렉터리에 패키징합니다. 따로 받은
디렉터리에서 바이트를 검증합니다. 공통 check / build / verify-download 명령은
[`docs/maintainers/repository/release.md`](../../repository/release.md)를
보세요. 제품 검사는 `python3 scripts/release.py check --product pre-sdd-review`입니다.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests/products/pre-sdd-review -p 'test_contract.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests/products/pre-sdd-review/evidence -p 'test_*.py' -v
```

`check`는 추적된 제품 범위, SemVer, changelog, 필수 검증을 확인합니다.
`build`는 새 빈 출력 디렉터리에 standalone ZIP 하나와 `SHA256SUMS`만 씁니다.
`verify-download`는 새로 받은 바이트, checksum, ZIP 구조, 추출 payload hash,
정확한 payload 목록, 추출한 `evidence.py --version` 정규 JSON, 제품 검증을
확인합니다. 로컬 빌드 결과는 공개 릴리스 증거가 아닙니다.

릴리스 payload의 `evidence/evidence.py`는 실행 비트가 없습니다. `python3`로
돌리고 설치하지 않습니다. native Python 3.11 evidence 실행을 기록하기 전까지
native Windows는 `not_measured`입니다.

no tag or GitHub Release is created by these commands.

## Failure recovery

제품 파일, 버전 결정, changelog, 테스트를 고치고 실패한 명령을 다시
실행합니다. 부분 산출물을 재사용하지 마세요. 새 빈 디렉터리에서만 다시
빌드합니다. 태그와 공개는 별도의 명시적 릴리스 작업입니다. 이 절차의 범위
밖입니다.
