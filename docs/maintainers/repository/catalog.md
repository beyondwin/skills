# 카탈로그 릴리스

마지막 공개 카탈로그 식별은 `beyondwin-skills` `2.0.0`입니다. 플러그인
메타데이터는 `catalog/plugin/.codex-plugin/plugin.json`에 있습니다. 저장소
루트에 두지 않습니다. 카탈로그는 제품 계약을 소유하지 않습니다. 이미 공개되어
원격 검증을 통과한 스킬 릴리스만 채택합니다.
Registry products do not automatically enter v2.0.0.
`products.toml`에 있는 현재 독립 제품이 카탈로그 lock이나 공개 `v2.0.0`
번들에 자동으로 들어가지 않습니다.

스킬 버전은 그 스킬의 계약 또는 런타임 파일이 바뀔 때만 올립니다. 카탈로그
버전은 채택한 lock 또는 패키지된 카탈로그 번들이 바뀔 때만 올립니다. 루트
문서만 바뀌면 카탈로그 릴리스가 필요하지 않습니다.

GitHub Release가 있다고 말하지 마세요. 공개 증명은 원격 다운로드 바이트입니다.
`v2.0.0`은 https://github.com/beyondwin/skills/releases/tag/v2.0.0 에 공개되어
있습니다. 플러그인 디렉터리 등록을 주장하지 않습니다. Archive 출처는
[migrations.md](migrations.md)입니다.

## lock 채택

`catalog/catalog.lock.json`은 채택한 스킬 릴리스의 불변 식별자를 고정합니다.
현재 `skills/` 개발 트리와 같을 필요는 없습니다. 카탈로그 ZIP은 현재
`skills/`를 복사하지 않습니다. lock과 일치하는 검증된 standalone ZIP을
입력으로 조립합니다.

채택 변경은 다음을 함께 수정합니다.

- lock 항목 (`name`, `version`, `tag`, `release_kind`, `source_commit`, `payload_sha256`)
- `catalog/CHANGELOG.md`
- 필요한 카탈로그 버전과 `catalog/plugin/.codex-plugin/plugin.json` 복제 값

`release_kind`는 `independent` 또는 `legacy-bundle`입니다. 새 릴리스는
`independent`만 사용합니다. `legacy-bundle`은 기존 `v2.0.0` 두 제품 이관에만
허용합니다. `how-it-works`와 `pre-sdd-review`는 공개 `v2.0.0`에 포함되지
않았고, 현재 lock에도 없습니다.

## 로컬 게이트

깨끗한 추적 트리에서 실행합니다.

```bash
python3 scripts/verify.py --catalog
git status --short --branch --untracked-files=all
git diff --check
```

소스 트리는 clean이어야 합니다. 생성 증거, 캐시, `dist/`는 추적하지 않습니다.

첫 카탈로그 릴리스가 만든 아티팩트:

```text
beyondwin-skills-v2.0.0.zip
korean-writing-editor-v2.0.0.zip
image-workbench-v2.0.0.zip
SHA256SUMS
```

`catalog.lock.json`은 두 standalone 스킬 ZIP을 태그 `v2.0.0`의
`legacy-bundle` 입력으로 고정합니다. 현재 `skills/` 개발과 미공개
`how-it-works`, `pre-sdd-review`는 카탈로그 ZIP에 복사되지 않습니다. 공유 버전
번들 빌더 `python3 scripts/build_release.py`는 폐기되었고 실패로 닫힙니다.

카탈로그 플러그인 메타데이터는 `catalog/plugin/.codex-plugin/plugin.json`에서
읽어 ZIP 루트 `.codex-plugin/plugin.json`으로 복사합니다. 각 standalone ZIP은
`LICENSE.txt`가 있는 최상위 스킬 디렉터리 하나입니다. 테스트, 라이브 하니스,
관리자 문서, 캐시, 증거는 목적 빌드 스킬 ZIP의 멤버가 아닙니다.

## archive, extract, checksum

공개 `v2.0.0` 아카이브는 추적된 일반 파일만 씁니다. zip 멤버를 정렬합니다.
심볼릭 링크와 특별 파일을 거절합니다. 모든 멤버를 `1980-01-01T00:00:00`으로
찍습니다. 일반 파일 `0644`와 실행 스크립트 `0755`를 사용했습니다.

공개 카탈로그는 현재 `skills/`가 아니라 새로 받은 standalone ZIP과 `SHA256SUMS`로
검증합니다.

```bash
python3 scripts/release.py check --catalog --input <fresh-download-directory>
python3 scripts/release.py build --catalog --input <fresh-download-directory> --output <new-empty-directory>
(cd "$RELEASE_DOWNLOAD_DIR" && shasum -a 256 -c SHA256SUMS)
```

추출 전에 절대 경로, `..`, 중복, 대소문자 충돌, 예상 밖 멤버를 거절합니다.
`SHA256SUMS`는 공개 릴리스 zip 파일을 나열합니다. checksum이 통과한 뒤 모든
아카이브를 새 임시 디렉터리에 풉니다. 추출한 한국어·이미지 페이로드와
추출한 inspector에 설치 smoke를 돌립니다.

## 원격 download

로컬 `dist/`는 공개 증거가 아닙니다. 공개 `v2.0.0`과 이후 릴리스는 다음 원격
바이트 게이트를 따릅니다.

1. 로컬 빌드 결과를 재사용하지 말고 원격 아티팩트를 새 디렉터리에 받습니다.
2. 받은 바이트의 checksum을 검증합니다.
3. 그 바이트에서 새 추출과 설치 smoke를 실행합니다.
4. 공개 README 링크와 소스 스킬 URL이 해석되는지 확인합니다.

```bash
python3 scripts/release.py verify-download --catalog --input <fresh-download-directory>
```

`scripts/build_release.py --verify-download`를 동작하는 카탈로그 검증기로
쓰지 마세요. 그 wrapper는 폐기되었습니다.

## Archive deletion 게이트

Archive 현재 트리를 바꾸기 전에 다음이 모두 성립해야 합니다. 빠진 조건은
삭제를 막습니다.

- 공개 `beyondwin/skills` `main`이 검토된 커밋을 가리킨다
- 태그 `v2.0.0`이 그 커밋을 가리킨다
- 필수 CI 작업이 모두 초록이다
- 네 릴리스 아티팩트를 공개 다운로드할 수 있다
- 릴리스 checksum이 새로 받은 바이트와 같다
- 플러그인과 개별 스킬 설치 smoke가 통과한다
- source-to-import 매니페스트가 설명된다
- Archive 소스 커밋과 마이그레이션 provenance가 기록된다
- 개인 경로, 비밀, 비공개 픽스처, 의도하지 않은 아티팩트가 없다
- 지원하지 않는 호환성·품질 주장이 없다

로컬 Archive 제거 커밋을 push하기 전에는 비파괴적으로 고치거나 되돌립니다.
push 뒤에는 그 제거 커밋을 `git revert`합니다. 이 게이트의 완료 기록은
[migrations.md](migrations.md)에 있습니다.

## 실패 복구

- 로컬 검증 실패: lock, CHANGELOG, 플러그인 버전 또는 입력을 고치고 다시
  검증합니다.
- 패키징 실패: 새 출력 디렉터리에서 다시 빌드합니다. 부분 결과를 재사용하지
  않습니다.
- 원격 검증 실패: Draft를 비공개로 유지합니다. 로컬 성공을 공개 증거로 대체하지
  않습니다.
- 한 제품 실패: 다른 제품의 버전, 태그, Release와 카탈로그 lock을 바꾸지
  않습니다.
