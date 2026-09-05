# pre-sdd-review 릴리스

이 문서는 Pre-SDD Review의 독립 패키징 절차를 소유합니다.
version source is `skills/pre-sdd-review/release.toml`. `SKILL.md`의
`metadata.version`은 검증된 복사본이고 `CHANGELOG.md`는 사람이 읽는 계약
이력입니다.

제품 식별자는 `release.toml`의 `pre-sdd-review` `version 2.0.0`입니다.

## Check, build, and verify download

공급자 없는 제품 검증을 실행한 뒤 새 빈 디렉터리에 패키징하고, 따로 받은
디렉터리에서 바이트를 검증합니다.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests/products/pre-sdd-review -p 'test_contract.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests/products/pre-sdd-review/evidence -p 'test_*.py' -v
python3 scripts/release.py check --product pre-sdd-review
python3 scripts/release.py build --product pre-sdd-review --output <new-empty-directory>
python3 scripts/release.py verify-download --product pre-sdd-review --input <fresh-download-directory>
```

`check`는 tracked product scope, SemVer, changelog, 필수 verification을
확인합니다. `build`는 새 빈 출력 디렉터리에 standalone ZIP 하나와
`SHA256SUMS`만 씁니다. `verify-download`는 fresh bytes, checksum, ZIP structure, extracted payload
hash, exact payload manifest, extracted `evidence.py --version` canonical JSON,
product verification을 확인합니다. 로컬 build output은 public-release evidence가
아닙니다.

Release payload keeps `evidence/evidence.py` non-executable; it is run with
`python3` and never installed. Native Windows stays `not_measured` unless a
native Python 3.11 evidence run is recorded.

No tag or GitHub Release is created by these commands.

## Failure recovery

제품 파일, 버전 결정, changelog, 테스트를 고치고 실패한 명령을 다시
실행합니다. 부분 산출물을 재사용하지 말고 새 빈 디렉터리에서만 다시
빌드합니다. 태그와 공개는 별도의 명시적 릴리스 작업이며 이 절차의 범위
밖입니다.
