# 저장소 구조

이 저장소는 독립 스킬 제품 모노레포이며, 별도 버전을 가진 카탈로그 플러그인 `beyondwin-skills`를 함께 둡니다.

현재 독립 제품은 `products.toml`이 가리키는 `korean-writing-editor`, `image-workbench`, `how-it-works`, `pre-sdd-review`입니다. 마지막 공개 카탈로그 `2.0.0`은 공개 `v2.0.0`의 두 스킬만 lock합니다. Apache-2.0은 루트와 각 standalone 스킬에 적용됩니다.

저장소 루트는 개별 스킬 GitHub 경로 설치를 위한 작업 공간이며 플러그인 메타데이터를 소유하지 않습니다. The repository root does not own plugin metadata. 카탈로그 플러그인 메타데이터는 `catalog/plugin/.codex-plugin/plugin.json`에 있고, 카탈로그 릴리스 때 플러그인 ZIP 루트로 복사됩니다. 지원되는 카탈로그 아티팩트는 공개된 플러그인 ZIP뿐입니다.

## 설치 페이로드와 개발 증거

GitHub 경로 설치의 스킬 페이로드는 `skills/<name>/`입니다. 제품 README, 영어 핵심 README, CHANGELOG, `release.toml`, 라이선스와 실행에 필요한 파일은 설치 페이로드에 포함됩니다. 테스트, 관리자 문서, 라이브 증거, 저장소 운영 도구는 설치 경계 밖에 둡니다.

| 트리 | 역할 | 설치? |
| --- | --- | --- |
| `skills/<name>/SKILL.md`, `references/`, `agents/`, `LICENSE.txt`, 런타임 `scripts/` | 실행 계약과 런타임 | 예 |
| `skills/<name>/README.md`, `README.en.md` | 제품 사용자 안내 | 예 |
| `skills/<name>/CHANGELOG.md` | 제품 변경 이력 | 예 |
| `skills/<name>/release.toml` | 제품 버전 원본 | 예 |
| `catalog/plugin/.codex-plugin/plugin.json` | 마지막 공개 카탈로그 플러그인 매니페스트 소스 | 플러그인 번들만 |
| `catalog/catalog.lock.json` | 카탈로그가 채택한 불변 스킬 릴리스 | 아니오 |
| `catalog/release.toml` | 카탈로그 식별 (`beyondwin-skills` `2.0.0`) | 아니오 |
| `tests/repository/` | 매니페스트, 링크, 패키징, 공개 문서 사실 | 아니오 |
| `tests/products/korean-writing-editor/offline/` | 결정적 트리거·모드·보존·출력 픽스처 | 아니오 |
| `tests/products/korean-writing-editor/live/` | 합성 라이브 하니스, 단위 테스트, dry-run, 운영 안내 | 아니오 |
| `tests/products/image-workbench/` | 라우팅, 권한, 증거, inspector 테스트 | 아니오 |
| `tests/products/how-it-works/` | 합성 DNS·rebase 계약과 페이로드 픽스처 | 아니오 |
| `tests/products/pre-sdd-review/` | 합성 설계·계획 계약 픽스처 | 아니오 |
| `docs/README.md` | 설치·사용·관리·기록 라우팅 | 아니오 |
| `docs/users/` | 공유 설치·호환성·안전·검증 안내 | 아니오 |
| `docs/maintainers/` | 구조, 레지스트리, 버저닝, 릴리스, 카탈로그, 마이그레이션, 제품 프로토콜 | 아니오 |
| `docs/history/` | 시점 기록. 현재 계약을 정의하지 않음 | 아니오 |
| `scripts/verify.py` | 공급자 없는 검증 오케스트레이터 | 아니오 |

페이로드 디렉터리에는 `CHANGE_PROTOCOL.md`, `evals/`, `tests/`를 두지 않습니다. `README.md`, `README.en.md`, `CHANGELOG.md`, `release.toml`은 허용되며 필수입니다. `image-workbench` inspector `skills/image-workbench/scripts/inspect_asset.py`는 런타임 코드이며, 테스트는 `tests/products/image-workbench/`에 둡니다. inspector는 스킬 루트에서 `python3 scripts/inspect_asset.py`로 호출하고, 저장소 상대 `skills/` 경로로 호출하지 않습니다.

## 인터페이스

- 플러그인 발견: `catalog/plugin/.codex-plugin/plugin.json`이 카탈로그 매니페스트 소스입니다. 공개 플러그인 ZIP은 이 파일을 `.codex-plugin/plugin.json`에 두고 `./skills/`를 나열하며 MCP 서버, apps, hooks를 선언하지 않습니다.
- 카탈로그 식별: `catalog/release.toml`과 카탈로그 플러그인 매니페스트는 이름 `beyondwin-skills`와 버전 `2.0.0`을 공유합니다. `catalog/catalog.lock.json`은 채택한 스킬 릴리스를 고정하며 현재 `skills/` 버전과 같을 필요가 없습니다.
- 스킬 식별: 디렉터리 이름, `SKILL.md` `name`, 해당 제품 `release.toml` 이름이 같아야 하고, `release.toml` 버전과 `SKILL.md` `metadata.version`이 같아야 합니다. `license: Apache-2.0`은 최상위 frontmatter입니다.
- 한국어 오프라인 러너: `tests/products/korean-writing-editor/offline/run.py --skill-root PATH`, 케이스는 러너 옆에 둡니다.
- 이미지 평가기: `tests/products/image-workbench/run.py --skill-root PATH`, 케이스는 러너 옆에 둡니다.
- inspector: 실제 스킬 루트에서 `python3 scripts/inspect_asset.py`를 해석합니다.
- 라이브 하니스: 소스 스킬은 `<repo>/skills/korean-writing-editor`이며, 보고서는 명시된 무시 증거 루트 아래에 둡니다.
- pre-sdd-review 계약: `tests/products/pre-sdd-review/test_contract.py`. 케이스는 같은 디렉터리의 `cases.json`과 `fixtures/`입니다.
- 공개 사실: 한영 사용자 문서는 명령, 지원 상태, 한계가 일치해야 합니다. 현재 버전 리터럴은 제품 `release.toml`이 소유합니다.

## 검증 경계

필수 로컬 검증:

```bash
python3 scripts/verify.py
```

이 명령은 자격 증명과 공급자가 없습니다. 제품만 검증하려면 `python3 scripts/verify.py --skill <name>`을, 카탈로그만 검증하려면 `python3 scripts/verify.py --catalog`를 씁니다. 한국어 라이브 평가는 명시적인 로컬 작업입니다.

제품 프로토콜은 [korean-writing-editor](../products/korean-writing-editor/contract.md), [image-workbench](../products/image-workbench/contract.md), [how-it-works](../products/how-it-works/contract.md), [pre-sdd-review](../products/pre-sdd-review/contract.md)를 보세요. 레지스트리는 [products-registry.md](products-registry.md), 독립 릴리스는 [release.md](release.md), 카탈로그는 [catalog.md](catalog.md), Archive 출처는 [migrations.md](migrations.md)입니다.
