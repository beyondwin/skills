# 관리자 문서

이 인덱스는 할 일을 고르는 안내입니다. 사용자 설치 안내는 각 제품 README와 `docs/users/`에 있습니다.

관리자 문서는 한국어가 원본입니다. 명령, 파일 경로, 계약 식별자는 영어로 둡니다.

## 할 일

| 작업 | 문서 |
| --- | --- |
| 제품 동작 바꾸기 | [계약](products/)과 해당 제품 `contract.md`, `testing.md` |
| 호스트 지원 추가 | 해당 제품 [호환성](products/) `compatibility.md`. `products.toml`, 공개 안내, 테스트를 함께 고칩니다 |
| 제품 등록 | [제품 레지스트리](repository/products-registry.md) |
| 검증 | `python3 scripts/verify.py`, 해당 제품 `testing.md` |
| 릴리스 | [독립 제품 릴리스](repository/release.md), 해당 제품 `release.md` |
| 불변 카탈로그 확인 | [카탈로그](repository/catalog.md), `catalog/` |
| 마이그레이션·Archive | [마이그레이션](repository/migrations.md) |
| 과거 결정 확인 | [기록](../history/) |

## 저장소 공통

| 문서 | 소유 |
| --- | --- |
| [구조](repository/architecture.md) | 설치 페이로드와 개발 증거 경계 |
| [제품 레지스트리](repository/products-registry.md) | `products.toml` 스키마와 등록 |
| [버저닝](repository/versioning.md) | 제품·카탈로그 SemVer 판정표 |
| [릴리스](repository/release.md) | 독립 제품 check/build/verify-download |
| [카탈로그](repository/catalog.md) | lock 채택과 원격 바이트 게이트 |
| [마이그레이션](repository/migrations.md) | Archive pin과 provenance |

## 제품 프로토콜

각 제품은 계약, 테스트, 호환성, 릴리스 문서를 가집니다. 한 제품의 동작 변경이 다른 제품 버전을 요구하지 않습니다.

### korean-writing-editor

- [계약](products/korean-writing-editor/contract.md) — 트리거, 기본값, 출력, 안전, 함께 고칠 파일
- [테스트](products/korean-writing-editor/testing.md) — 결정적 픽스처, 명령, 증거 한계
- [호환성](products/korean-writing-editor/compatibility.md) — 현재 호스트, 능력, 증거 경계, 새 지원 규칙
- [릴리스](products/korean-writing-editor/release.md) — 버전 원본, SemVer 예시, check/build/download, 실패 복구

### image-workbench

- [계약](products/image-workbench/contract.md) — 트리거, 기본값, 출력, 안전, 함께 고칠 파일
- [테스트](products/image-workbench/testing.md) — 결정적 픽스처, 명령, 증거 한계
- [호환성](products/image-workbench/compatibility.md) — 현재 호스트, 능력, 증거 경계, 새 지원 규칙
- [릴리스](products/image-workbench/release.md) — 버전 원본, SemVer 예시, check/build/download, 실패 복구

### how-it-works

- [계약](products/how-it-works/contract.md) — 트리거, 기본값, 출력, 안전, 함께 고칠 파일
- [테스트](products/how-it-works/testing.md) — 결정적 픽스처, 명령, 증거 한계
- [호환성](products/how-it-works/compatibility.md) — 현재 호스트, 능력, 증거 경계, 새 지원 규칙
- [릴리스](products/how-it-works/release.md) — 버전 원본, SemVer 예시, check/build/download, 실패 복구

### pre-sdd-review

- [계약](products/pre-sdd-review/contract.md) — 권위 순서, 기본 문서 개선 흐름, 변이 경계, 판정
- [테스트](products/pre-sdd-review/testing.md) — 공급자 없는 계약 픽스처와 선택적 라이브 절차의 증거 한계
- [호환성](products/pre-sdd-review/compatibility.md) — Codex 측정 지원과 다른 호스트 `not_measured` 경계
- [릴리스](products/pre-sdd-review/release.md) — 독립 제품 check/build/verify-download와 비게시 경계
