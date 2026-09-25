# image-workbench 릴리스

버전 원본은 `skills/image-workbench/release.toml`입니다. `SKILL.md`
`metadata.version`은 검증된 복사본입니다. 사람이 읽는 변경 이력은 같은
디렉터리의 `CHANGELOG.md`입니다. 공통 판정표는
[버저닝](../../repository/versioning.md)을 따릅니다.

현재 독립 버전은 `release.toml`이 정합니다. 로컬 검사가 통과해도 태그 생성,
push, GitHub Release 공개가 끝났다는 증거는 아닙니다.

## SemVer 예시

- PATCH: inspector 경로 안내 정정, 깨진 상대 링크, 문서화된 권한 경계를 되살리는 결함 수정
- MINOR: 기본 `brief`/`audit` 읽기 전용을 유지하는 새 선택 스크립트
- MAJOR: 기본 모드를 생성으로 바꾸거나, `brief`가 이미지 호출을 승인하게 하는 변경
- 없음: 설치되지 않는 테스트 리팩터링, 채택/거절 경계와 동작을 유지하는 공급자 출처 갱신

동작이 바뀌면 SemVer를 올립니다. 문서 문구만 바뀌고 동작이 같으면 올리지
않습니다. 채택/거절 경계와 동작을 유지하는 공급자 출처 갱신만으로도 올리지
않습니다.

설치 파일이 바뀌면 같은 변경에 다음이 모두 있어야 합니다: `release.toml`과
`SKILL.md`의 버전 결정, 제품 CHANGELOG 항목.

## 검사, 빌드, 다운로드

공통 check / build / verify-download 명령은
[`docs/maintainers/repository/release.md`](../../repository/release.md)를
보세요. 제품 검사는 `python3 scripts/release.py check --product image-workbench`입니다.

압축을 푼 결과물의 기본 동작 확인(추출 smoke)은 추출한 inspector를 스킬
루트에서 호출해야 합니다. checksum 검증과, 로컬에서 신뢰하는 source payload
hash 비교를 구현하는 공통 release 코드는 통합 담당이 소유합니다. 제품 문서만
바뀐 상태를 그 공통 계약이 구현됐다는 증거로 쓰지 않습니다.

제품 태그는 `image-workbench-v<version>`입니다. 옛 standalone ZIP은 통합 태그
`v2.0.0`의 GitHub Release에 남아 있습니다. 제품 한정 태그
`image-workbench-v2.0.0`은 없습니다.

## 실패 복구

- 로컬 검증 실패: 파일, 버전, CHANGELOG, 테스트를 고치고 다시 검증합니다.
- 패키징 실패: 새 출력 디렉터리에서 다시 빌드합니다. 부분 결과를 재사용하지 않습니다.
- 태그 뒤 Draft 실패: 태그를 옮기지 않습니다. 같은 커밋의 정확한 아티팩트만 고쳐서 검증하거나, 코드 변경이 필요하면 새 버전을 준비합니다.
- 원격 검증 실패: Draft를 비공개로 둡니다. 로컬 성공을 공개 증거로 대신하지 않습니다.
- 이 제품 실패: 다른 제품의 버전, 태그, Release를 바꾸지 않습니다.
