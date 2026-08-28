# graspic 릴리스

버전 원본은 `skills/graspic/release.toml`입니다. `SKILL.md` `metadata.version`은 검증된 복제 값입니다. 사람이 체감하는 이력은 같은 디렉터리의 `CHANGELOG.md`입니다. 공통 판정표는 [버저닝](../../repository/versioning.md)을 따릅니다.

공개 graspic 릴리스는 아직 없습니다. 이 제품은 `graspic 2.0.0`으로 공개되지 않았고 통합 `v2.0.0` GitHub Release에 포함되지 않았습니다. 첫 독립 공개 목표는 `3.0.0`입니다.

## SemVer 예시

- PATCH: 깨진 상대 링크, 설치 README 정정, 문서화된 dump gate를 회복하는 결함 수정
- MINOR: 기본 길 칸을 유지하는 새 선택 별칭
- MAJOR: 기본 산출을 터미널 스크롤백으로 되돌리거나, `/eli5`를 활성화하거나, 기본 칸을 바꾸는 변경
- 없음: 설치되지 않는 형태 픽스처 주석, 관리자 문서만의 변경

동작 변경은 SemVer를 올립니다. 문서 문구만 바꾸고 동작이 같으면 버전을 올리지 않습니다.

설치 페이로드가 바뀌면 `release.toml`과 `SKILL.md` 버전 결정과 제품 CHANGELOG 항목이 같은 변경에 있어야 합니다. 아티팩트 페이지 계약은 이미 커밋된 비호환 실행 계약이며 채팅 전용으로 되돌리지 않습니다.

## 검사, 빌드, 다운로드

```bash
python3 scripts/verify.py --skill graspic
python3 scripts/release.py check --product graspic
python3 scripts/release.py build --product graspic --output <new-empty-directory>
python3 scripts/release.py verify-download --product graspic --input <fresh-download-directory>
```

`check`는 깨끗한 추적 트리, SemVer, CHANGELOG, 태그 충돌, 제품 범위와 필수 검증을 확인합니다. `build`는 새 빈 출력 디렉터리만 쓰고 standalone ZIP 하나와 `SHA256SUMS`를 만듭니다. `verify-download`는 새로 받은 바이트의 checksum, ZIP 구조, 추출 payload hash, 제품 검증과 설치 smoke를 확인합니다. 로컬 `dist/`는 공개 증거가 아닙니다.

제품 태그는 `graspic-v<version>`입니다. 태그와 Draft는 명시적 출시 작업이며 로컬 빌드의 부수 효과가 아닙니다.

## 실패 복구

- 로컬 검증 실패: 파일, 버전, CHANGELOG 또는 테스트를 고치고 다시 검증합니다.
- 패키징 실패: 새 출력 디렉터리에서 다시 빌드합니다. 부분 결과를 재사용하지 않습니다.
- 태그 뒤 Draft 실패: 태그를 이동하지 않습니다. 같은 커밋의 정확한 아티팩트만 고쳐서 검증하거나, 코드 변경이 필요하면 새 버전을 준비합니다.
- 원격 검증 실패: Draft를 비공개로 유지합니다. 로컬 성공을 공개 증거로 대체하지 않습니다.
- 이 제품 실패: 다른 제품의 버전, 태그, Release와 카탈로그 lock을 바꾸지 않습니다.
