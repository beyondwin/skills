# waygent 릴리스

이 문서는 waygent의 버전을 올리는 기준과 릴리스 검사 방법을 정합니다. 버전 원본은
`skills/waygent/release.toml`입니다. `SKILL.md` `metadata.version`은 검증된 복제
값입니다. 사람이 읽는 변경 이력은 같은 디렉터리의 `CHANGELOG.md`입니다. 공통
판정표는 [버저닝](../../repository/versioning.md)을 따릅니다.

아직 공개된 waygent 릴리스는 없습니다. tag, 공개(publication), GitHub Release는
만들지 않았습니다.

## SemVer 예시

- PATCH: 깨진 링크, README 정정, 문서화된 규칙을 되살리는 결함 수정
- MINOR: 기존 흐름을 유지하는 새 선택 입력
- MAJOR: 트레일러 형식, 진행 파일 위치, 리뷰 횟수, 브랜치 규칙을 바꾸는 변경
- 올리지 않음: 설치되지 않는 테스트나 관리자 문서만의 변경

설치 파일이 바뀌면 `release.toml`과 `SKILL.md`의 버전, 제품 CHANGELOG 항목이 같은
변경에 있어야 합니다.

## 검사, 빌드, 다운로드

공통 check / build / verify-download 명령은
[`docs/maintainers/repository/release.md`](../../repository/release.md)를 보세요. 제품
검사는 `python3 scripts/release.py check --product waygent`입니다. 제품 태그는
`waygent-v<version>`입니다.

이 명령은 태그 또는 GitHub Release를 만들지 않습니다.
