# 관리자 문서

저장소를 고치는 사람을 위한 안내입니다. 아래 [할 일](#할-일) 표에서 작업을 찾으면
고칠 곳, 같이 바꿀 것, 검증 명령이 한 줄에 있습니다. 트리가 어떻게 나뉘는지는
[구조](repository/architecture.md)를 보세요. 사용자 설치 안내는 각 제품 README와
`docs/users/`에 있습니다.

## 할 일

| 작업 | 고칠 곳 | 같이 바꿀 것 | 검증 |
| --- | --- | --- | --- |
| 제품 동작 바꾸기 | `skills/<name>/` | 해당 제품 [계약](products/) `contract.md`의 `함께 고칠 파일`, `testing.md`, 필요하면 버전 | `python3 scripts/verify.py --skill <name>` |
| 호스트 지원 추가 | 해당 제품 [호환성](products/) `compatibility.md` | `products.toml`, 공개 안내, 테스트 | `python3 scripts/verify.py` |
| 제품 등록 | `products.toml` | `skills/<name>/`, `tests/products/<name>/`, `docs/maintainers/products/<name>/`. 절차는 [제품 목록](repository/products-registry.md) | `python3 scripts/verify.py` |
| 버전 올리기 | `skills/<name>/release.toml` | `SKILL.md` `metadata.version`, `CHANGELOG.md`. 판정은 [버저닝](repository/versioning.md) | `python3 scripts/verify.py --skill <name>` |
| 제품 릴리스 | `skills/<name>/CHANGELOG.md`의 `Unreleased` 확정 | 해당 제품 `release.md`. 절차는 [독립 제품 릴리스](repository/release.md) | `python3 scripts/release.py check --product <name>` (깨끗한 트리에서) |
| 불변 카탈로그 확인 | `catalog/` | lock, `catalog/CHANGELOG.md`, 플러그인 버전. 절차는 [카탈로그](repository/catalog.md) | `python3 scripts/verify.py --catalog` |
| 마이그레이션·Archive 확인 | 없음 (끝난 기록) | 절차는 [마이그레이션](repository/migrations.md) | `python3 scripts/capture_archive_manifest.py verify` (인자는 해당 문서) |
| 진행 중인 설계·계획 | `docs/history/` | 끝나면 지움. [기록](../history/) | 없음 |

어떤 작업이든 머지 전에는 `python3 scripts/verify.py`를 돌립니다.

## 문서 쓰는 규칙

- 관리자 문서는 한국어가 원본입니다. 명령, 파일 경로, 계약 식별자는 영어로 둡니다.
- `SKILL.md`와 런타임 `references/`는 에이전트가 읽는 실행 계약이라 영어를 유지합니다.
- 독자는 둘입니다. 스킬을 고르고 호출하는 사람은 제품 README를 봅니다. 설치·검증·변경·릴리스는
  `docs/users/`와 `docs/maintainers/`의 이 인덱스를 봅니다. 파일은 그 독자 트리에만 둡니다.
- 사실 하나는 한 문서가 소유합니다. 다른 페이지는 링크로 보냅니다. 공개 설치는
  `docs/users/`, 제품 동작은 해당 `contract.md`와 `SKILL.md`, 기록기 명령은
  `skills/pre-sdd-review/evidence/README.md`가 소유합니다.
- 문장은 짧게, 일상어로 씁니다.
- 지금 쓰는 문서를 바꾸면 같은 변경에서 테스트의 문구·사실 단언을 맞춥니다. 관리자·사용자
  문서를 향한 테스트는 정확한 문구, 사실, 목록, 순서, 구조(필요한 절이 있는지)만 확인하고
  문서 전체나 절 전체의 해시는 확인하지 않습니다.
- 제품 동작 변경은 해당 계약의 `함께 고칠 파일`을 따릅니다.
- `docs/history/`는 진행 중인 설계·계획만 둡니다. 현재 계약을 정의하지 않습니다.

## 저장소 공통 문서

| 문서 | 다루는 것 |
| --- | --- |
| [구조](repository/architecture.md) | 설치 파일과 개발 증거의 경계, 검사 범위 |
| [제품 목록](repository/products-registry.md) | `products.toml` 스키마와 등록 절차 |
| [버저닝](repository/versioning.md) | 제품·카탈로그 SemVer 판정표와 태그 |
| [릴리스](repository/release.md) | 독립 제품 check/build/verify-download |
| [카탈로그](repository/catalog.md) | lock 채택과 원격 다운로드 검증 |
| [마이그레이션](repository/migrations.md) | Archive에서 가져온 출처 고정값(pin)과 기록 |

## 제품별 문서

각 제품은 계약, 테스트, 호환성, 릴리스 문서 네 개를 가집니다. 한 제품의 동작 변경이
다른 제품 버전을 요구하지 않습니다.

| 제품 | 계약 | 테스트 | 호환성 | 릴리스 |
| --- | --- | --- | --- | --- |
| korean-writing-editor | [contract](products/korean-writing-editor/contract.md) | [testing](products/korean-writing-editor/testing.md) | [compatibility](products/korean-writing-editor/compatibility.md) | [release](products/korean-writing-editor/release.md) |
| image-workbench | [contract](products/image-workbench/contract.md) | [testing](products/image-workbench/testing.md) | [compatibility](products/image-workbench/compatibility.md) | [release](products/image-workbench/release.md) |
| how-it-works | [contract](products/how-it-works/contract.md) | [testing](products/how-it-works/testing.md) | [compatibility](products/how-it-works/compatibility.md) | [release](products/how-it-works/release.md) |
| pre-sdd-review | [contract](products/pre-sdd-review/contract.md) | [testing](products/pre-sdd-review/testing.md) | [compatibility](products/pre-sdd-review/compatibility.md) | [release](products/pre-sdd-review/release.md) |
| sddx | [contract](products/sddx/contract.md) | [testing](products/sddx/testing.md) | [compatibility](products/sddx/compatibility.md) | [release](products/sddx/release.md) |

문서마다 담는 것:

- 계약: 트리거, 기본값, 출력, 안전, 함께 고칠 파일
- 테스트: 결정적 검사 예시(픽스처), 명령, 증거의 한계
- 호환성: 현재 호스트, 능력, 증거 경계, 새 지원 규칙
- 릴리스: 버전 원본, SemVer 예시, check/build/download, 실패 복구

제품마다 다른 점:

- pre-sdd-review: 계약은 권위 순서와 판정도 다룹니다. 테스트는 공급자 없는 계약 픽스처와
  선택적 라이브 절차의 증거 한계를 적습니다. 호환성은 Codex 측정 지원과 다른 호스트
  `not_measured` 경계입니다. 릴리스는 비게시 경계를 둡니다.
- sddx: 계약은 호스트와 실행 백엔드(backend)의 구분, 시도 조회(`status`)를 다룹니다.
  테스트는 공급자 없는 신원 픽스처를 씁니다. 호환성은 Claude Code와 Codex 오케스트레이터이며,
  작업 CLI(worker)는 호스트가 아닙니다. 릴리스는 비게시 경계를 둡니다.
