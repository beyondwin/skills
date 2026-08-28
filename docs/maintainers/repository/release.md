# 독립 제품 릴리스

이 문서는 현재 독립 제품의 검사·빌드·다운로드 검증만 다룹니다. 현재 버전 숫자를 복제하지 않습니다. 제품 버전 원본은 `skills/<name>/release.toml`입니다. SemVer 판정은 [버저닝](versioning.md)을 따릅니다. 제품별 계약 예시는 `docs/maintainers/products/<name>/release.md`를 보세요.

카탈로그 번들 릴리스는 [카탈로그](catalog.md)의 별도 작업입니다. 제품 릴리스가 `catalog/` lock을 자동으로 바꾸지 않습니다.

## 검사, 빌드, 다운로드 검증

깨끗한 추적 트리에서 실행합니다.

```bash
python3 scripts/verify.py --skill <name>
python3 scripts/release.py check --product <name>
python3 scripts/release.py build --product <name> --output <new-empty-directory>
python3 scripts/release.py verify-download --product <name> --input <fresh-download-directory>
```

- `check`는 깨끗한 추적 트리, SemVer, CHANGELOG, 태그 충돌, 제품 범위와 필수 검증을 확인합니다.
- `build`는 새 빈 출력 디렉터리만 쓰고 standalone ZIP 하나와 `SHA256SUMS`를 만듭니다.
- `verify-download`는 새로 받은 바이트의 checksum, ZIP 구조, 추출 payload hash, 제품 검증과 설치 smoke를 확인합니다.

로컬 `dist/`는 공개 증거가 아닙니다. 제품 태그는 `<name>-v<version>` annotated tag입니다. 이미 있는 태그는 재사용하거나 이동하지 않습니다. 태그와 GitHub Release는 명시적 출시 작업이며 로컬 빌드의 부수 효과가 아닙니다.

## 실패 복구

- 로컬 검증 실패: 파일, 버전, CHANGELOG 또는 테스트를 고치고 다시 검증합니다.
- 패키징 실패: 새 출력 디렉터리에서 다시 빌드합니다. 부분 결과를 재사용하지 않습니다.
- 태그 뒤 Draft 실패: 태그를 이동하지 않습니다. 같은 커밋의 정확한 아티팩트만 고쳐서 검증하거나, 코드 변경이 필요하면 새 버전을 준비합니다.
- 원격 검증 실패: Draft를 비공개로 유지합니다. 로컬 성공을 공개 증거로 대체하지 않습니다.
- 한 제품 실패: 다른 제품의 버전, 태그, Release와 카탈로그 lock을 바꾸지 않습니다.
