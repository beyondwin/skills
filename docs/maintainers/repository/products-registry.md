# 제품 레지스트리

`products.toml`은 현재 독립 제품의 유일한 순서 있는 색인입니다. 버전, 태그,
셸 명령을 소유하지 않습니다. 제품 버전 원본은 각 `skills/<name>/release.toml`입니다.

카탈로그 `catalog/`는 레지스트리와 별개입니다. 레지스트리에 제품을 넣는 것만으로
`catalog/` lock이나 공개 플러그인 번들이 바뀌지 않습니다.

## 스키마

최상위와 각 `[[products]]` 항목의 필드만 허용합니다. 추가 키, 누락 키, 잘못된
타입은 로드가 실패합니다.

| 필드 | 위치 | 의미 |
| --- | --- | --- |
| `schema_version` | 최상위 | 반드시 `1` |
| `name` | 제품 | 디렉터리·`SKILL.md` `name`·`release.toml` 이름과 같은 제품 ID. `^[a-z0-9]+(?:-[a-z0-9]+)*$` |
| `display_name` | 제품 | 사람이 읽는 이름 |
| `skill_path` | 제품 | 설치 파일 디렉터리. 저장소 상대, `..`와 절대 경로 금지 |
| `test_path` | 제품 | 제품 테스트 디렉터리 |
| `maintainer_docs` | 제품 | 제품 관리자 문서 디렉터리 |
| `supported_hosts` | 제품 | 허용 값: `codex`, `claude-code`, `grok`, `cursor` |
| `owned_paths` | 제품 | 변경 라우팅 접두사. 디렉터리 항목은 끝 `/`가 필요 |
| `verify_stages` | 제품 | 코드에 등록된 검증 단계 식별자. 셸 명령이 아님 |

`version`, `tag_prefix`, `command` 필드는 없습니다. 제품 순서와 중복
이름·경로 거부는 파서가 강제합니다.

## 등록 절차

새 현재 독립 제품을 넣으려면 같은 변경에 다음이 있어야 합니다.

1. `products.toml`에 제품 항목을 추가한다
2. `skills/<name>/`, `tests/products/<name>/`, `docs/maintainers/products/<name>/`를 만든다
3. 관리자 문서 네 파일(`contract.md`, `testing.md`, `compatibility.md`, `release.md`)을 둔다
4. 등록된 검증 단계 식별자를 `verify_stages`에 적는다
5. 레지스트리 검증이 통과한다

등록되지 않은 `skills/`, `tests/products/`, `docs/maintainers/products/` 자식,
알 수 없는 호스트·단계, 이름 불일치는 실패로 닫힙니다.

## 검증 명령

레지스트리 로드와 `validate_registry`는 모든 공급자 없는 검증의 앞단입니다.

```bash
python3 scripts/verify.py
python3 scripts/verify.py --skill <name>
python3 scripts/verify.py --catalog
```

어느 선택자를 써도 `products.toml`을 읽고 등록된 단계 이름에 대해
검증합니다. 오류가 있으면 단계 실행 전에 종료 코드 1로 멈춥니다.
