# 문서 구조 설계

**Status:** Approved on 2026-09-11

**Scope:** 사용자·제품·관리자 문서의 역할 분리, `docs/users/` 설치 문서 분할, 제품 README 제목 통일, 공개 문서 테스트가 장문이 아니라 사실을 잠그게 바꾸기.

**Out of scope:** `skills/<name>/` 설치 경로 변경, `SKILL.md` 본문, `catalog/` 본문, 관리자 제품 문서 네 파일 합치기, 태그·GitHub Release. `docs/history/README.md`는 이 설계를 진행 중 목록에 넣는 것만 허용한다.

이 파일은 진행 중인 설계이다. 현재 계약을 정의하지 않는다. 산 계약은 제품 README, `docs/users/`, `docs/maintainers/`에 있다.

## Context

2026-08 이후 독자 트리는 이미 나뉘어 있다. `docs/users/`, `docs/maintainers/`, `docs/history/`. 남은 마찰은 폴더 이름이 아니라 한 페이지가 여러 일을 겸하고, 같은 장문이 여러 파일에 있으며, 테스트가 그 중복을 해시로 잠근다는 점이다.

현재 `docs/users/*/installation.md`는 Codex 설치기, How It Works 로컬 링크, evidence 기록기, `npx`, git clone, 갱신·제거, 검증을 한 파일에 둔다. 제품 README 세 개는 `목적` 제목이고 `pre-sdd-review`만 다른 제목과 machine-readable `Contract` 목록을 사용자 문서에 둔다. `test_public_docs.py`는 Pre-SDD 전용 제목, 공유 섹션 SHA-256, 언어당 사용자 가이드 네 파일을 요구한다.

How It Works 로컬 설치는 `ln -s`가 아니다. `<!-- how-it-works-local-links -->` 뒤 Python 블록이 페이로드 계약이다. `tests/repository/test_installation_contract.py`와 `tests/products/how-it-works/test_contract.py`가 이 블록을 잠그고 `ln -s` 안내를 금지한다. 제품 README는 `](../../docs/` 상대 링크를 쓰지 않고 GitHub `blob/main` URL을 쓴다.

## Goals

1. 페이지 하나당 질문 하나. 설치·사용·변경·과거가 섞이지 않는다.
2. 사실 하나당 주인 문서 하나. 다른 곳은 한 줄과 링크만 둔다. 실행 가능한 설치 블록만 예외다.
3. 네 제품 README가 같은 제목 순서다.
4. 이미 설치된 스킬 README가 가리키는 `installation.md`, `safety-and-privacy.md`, `verification.md` 이름은 `main`에서 사라지지 않는다.
5. 공개 문서 테스트는 명령·호스트·제품명·금지 주장을 잠그고, 장문 복사와 Pre-SDD 전용 제목 템플릿은 잠그지 않는다.

## Non-goals

- `docs/users/`와 `docs/maintainers/` 이름을 작업 동사 폴더로 바꾸지 않는다.
- `safety.md`, `verify.md`, `install.md`로 이름을 바꾸지 않는다.
- 리다이렉트 전용 스텁을 만들지 않는다.
- How It Works 설치를 `ln -s`로 되돌리지 않는다.
- `SKILL.md`, 카탈로그 본문, 제품 동작을 바꾸지 않는다.
- 관리자 `contract.md` / `testing.md` / `compatibility.md` / `release.md`를 한 파일로 합치지 않는다.

## Decisions

### 1. 읽는 길

| 질문 | 입구 | 하지 않는 일 |
| --- | --- | --- |
| 뭐가 있지? | 루트 `README.md` / `README.en.md` | 설치 절차, 계약, 안전 장문 |
| 어떻게 설치하지? | `docs/users/<lang>/installation.md`와 `install-*.md` | 사용법, 관리자 프로토콜 |
| 어떻게 쓰지? | `skills/<name>/README.md` | 공유 설치 절차, SemVer, 픽스처 경로 |
| 어떻게 고치지? | `docs/maintainers/` | 사용자 설치 안내 |
| 진행 중인 설계는? | `docs/history/` | 현재 계약 정의 |

루트 README는 한 화면이다. 제품 표(역할·호스트·제품 README 링크), Codex 설치 세 줄, How It Works는 설치 문서 링크, `python3 scripts/verify.py`, 문서 색인. 제품별 사용 금지 목록 전체를 다시 쓰지 않는다. 텔레메트리 없음 한 줄과 안전 문서 링크로 충분하다.

`docs/README.md`는 라우터만 유지한다. 새 설치 파일을 가리킨다.

### 2. 사용자 문서 트리

언어 쌍은 유지한다. `ko`가 원본이고 `en`은 같은 순서와 같은 사실(명령, 호스트 id, 제품명, 지원 문장)을 담는다.

```text
docs/users/ko|en/
  installation.md            # 스킬 → 방법 표. 이름 유지
  install-codex.md           # 새 파일
  install-local.md           # 새 파일
  compatibility.md
  safety-and-privacy.md      # 이름 유지
  verification.md            # 이름 유지
```

| 파일 | 소유 | 넣지 않음 |
| --- | --- | --- |
| `installation.md` | 네 스킬 → 방법 표, 아래 파일로 가는 링크 | 명령 블록, Python 설치 블록, 갱신 절차 |
| `install-codex.md` | `$skill-installer` 세 제품, 대상 확인, 갱신/제거, `npx`(korean-writing-editor만), clone 복사 대안 | How It Works 로컬 링크, evidence 실행 절차 |
| `install-local.md` | How It Works 클론, 표시된 Python 블록, 해제, `~/.codex` 금지 | Codex 설치기 |
| `compatibility.md` | 네 지원 문장과 호스트 한계 | 설치 절차 |
| `safety-and-privacy.md` | 공유 안전·개인정보 장문 | 제품 사용법 |
| `verification.md` | `verify.py`, 프로필, 오프라인/라이브 한 줄, 통과가 증명하지 않는 것 | 제품별 픽스처 경로 |

`installation.md` 표는 네 행이다.

| 스킬 | 방법 | 문서 |
| --- | --- | --- |
| `korean-writing-editor` | Codex `$skill-installer` | `install-codex.md` |
| `image-workbench` | Codex `$skill-installer` | `install-codex.md` |
| `pre-sdd-review` | Codex `$skill-installer` | `install-codex.md`. 기록기는 `skills/pre-sdd-review/evidence/README.md` |
| `how-it-works` | 저장소 로컬 링크 | `install-local.md` |

### 3. 사실의 주인

| 사실 | 주인 | 다른 곳 |
| --- | --- | --- |
| 네 지원 문장 | `compatibility.md` | 제품 README는 자기 한 줄만 인용 |
| 안전 장문 | `safety-and-privacy.md` | 제품 README는 링크 |
| 검증 명령과 증거 한계 | `verification.md` | 제품 README는 링크 |
| 제품별 픽스처 경로 | 해당 `docs/maintainers/products/<name>/testing.md` | `verification.md`에 나열하지 않음 |
| 버전 숫자 | `release.toml`, `SKILL.md` `metadata.version` | 일반 문서에 버전 리터럴 없음 |
| evidence 기록기 명령 | `skills/pre-sdd-review/evidence/README.md` | 제품 README와 `installation.md`는 한 줄 링크 |
| How It Works Python 설치 블록 | 결정 5의 네 문서가 동일 사본 | `installation.md`에는 없음 |
| Pre-SDD machine-readable `Contract` | `docs/maintainers/products/pre-sdd-review/contract.md` | 제품 README에 목록을 두지 않음 |

허용하는 짧은 반복: 제품 README의 설치 명령 한 줄(또는 How It Works Python 블록)과 해당 `install-*.md`. 같은 안전·검증 장문을 제품 README에 다시 쓰면 테스트가 실패한다.

### 4. 제품 README 템플릿

경로는 `skills/<name>/README.md`와 `README.en.md`로 둔다. 네 제품 모두 아래 제목 순서다. Pre-SDD의 `이 스킬이 해결하는 문제`, `운영과 한계`, `호환성과 검증 수준` 제목은 없앤다.

한국어:

1. `## 목적`
2. `## 사용할 때와 사용하지 않을 때`
3. `## 지원 호스트`
4. `## 설치`
5. `## 첫 호출`
6. `## 예상 결과`
7. `## 더 보기`

영어:

1. `## Purpose`
2. `## When to use and not use`
3. `## Supported hosts`
4. `## Install`
5. `## First call`
6. `## Expected result`
7. `## See also`

`## 안전과 개인정보`, `## 검증`, `## 업데이트와 제거`, `## 변경 이력과 관리자 문서`는 제품 README에서 없앤다. 그 링크는 `더 보기` / `See also`로 모은다. 대상은 안전 문서, 검증 문서, `CHANGELOG.md`, 관리자 네 파일이다. Pre-SDD는 여기에 `evidence/README.md`를 더한다.

설치 절: Codex 세 제품은 `$skill-installer` 한 명령과 `install-codex.md`의 GitHub URL. How It Works는 클론·`mkdir`와 표시된 Python 블록을 유지하고 `install-local.md`를 가리킨다. 갱신·제거 절차 문단은 제품 README에 두지 않는다. How It Works 해제는 `install-local.md`가 소유한다.

예상 결과: 모드와 사용자가 받는 산출만. How It Works의 여섯 가지 산출과 골격은 남긴다. Pre-SDD는 `READY` / `REVISE` / `BLOCKED`와 기본 흐름 요약만 남기고 `### Contract` 목록은 관리자 `contract.md`로 옮긴다. 그 목록의 키와 값은 지금 README에 있는 항목을 빠짐없이 `contract.md`가 소유해야 한다. 이미 `contract.md`에 있는 설명과 중복되면 README 쪽 목록만 제거하고 계약 문서를 보강한다.

제품 README의 사용자·관리자 문서 링크는 GitHub `https://github.com/beyondwin/skills/blob/main/...` 를 유지한다. how-it-works 페이로드 테스트가 `](../../docs/` 를 금지하므로 상대 경로로 바꾸지 않는다. 다른 제품도 같은 URL 형태를 쓴다. 새 설치 파일을 가리킬 때도 `blob/main/docs/users/<lang>/install-codex.md` 또는 `install-local.md`다.

### 5. How It Works 설치 블록

다음 네 문서는 `<!-- how-it-works-local-links -->` 마커를 정확히 하나 가지고, 바로 뒤에 오는 Python 코드 펜스가 서로 같아야 한다.

- `skills/how-it-works/README.md`
- `skills/how-it-works/README.en.md`
- `docs/users/ko/install-local.md`
- `docs/users/en/install-local.md`

`docs/users/*/installation.md`에서는 이 마커와 블록을 제거한다. `test_installation_contract.py`의 `DOCUMENTS`는 위 네 경로로 바꾼다. 블록 내용과 충돌 시 거부 동작은 바꾸지 않는다.

### 6. 관리자 문서

`docs/maintainers/products/<name>/{contract,testing,compatibility,release}.md`와 `docs/maintainers/repository/`는 경로를 유지한다. `products.toml`의 `maintainer_docs`도 유지한다.

- `architecture.md`: 한국어 원본으로 설치 경계 표와 검증 명령만 남긴다. 사용자 설치 절차를 반복하지 않는다.
- 각 제품 `testing.md`: `verification.md`에서 빼 온 픽스처 경로를 받는다.
- 각 제품 `release.md`: 그 제품 SemVer 예시와 태그. 공통 `check` / `build` / `verify-download` 명령은 `repository/release.md`가 주인이다. 제품 `release.md`는 그 문서로 보낸다.
- 관리자 인덱스는 할 일 표를 유지한다. 사용자 설치 안내를 늘리지 않는다.
- 관리자 문서는 한국어가 원본이다. 명령, 경로, 식별자는 영어다.

문서 사실이 바뀔 때 같이 고친다.

| 바뀌는 것 | 같이 고침 |
| --- | --- |
| 설치 명령·대상 경로 | 제품 README, `install-codex.md` 또는 `install-local.md`, 루트 README 입구, 설치 계약 테스트 |
| 호스트 지원 | `products.toml`, `compatibility.md`, 그 제품 README 한 줄, 제품 `compatibility.md`, 테스트 |
| 안전 장문 | `safety-and-privacy.md`만 |
| 검증 명령·증거 한계 | `verification.md`만 |
| 제품 동작 | 이번 패스에서 `SKILL.md` 본문은 유지. `contract.md`와 픽스처. README는 사용 결과만 맞춘다 |

### 7. 테스트

`tests/repository/test_public_docs.py`와 관련 공개 문서 테스트가 잠그는 것:

- 네 제품 README가 위 제목 순서를 가진다. Pre-SDD 전용 제목 튜플은 삭제한다.
- 설치 명령, 지원 문장, 호스트 id, 제품명이 한영·`products.toml`과 일치한다.
- `installation.md`, `safety-and-privacy.md`, `verification.md`가 각 언어에 남아 있다.
- `install-codex.md`와 `install-local.md`가 각 언어에 있다. 언어당 파일 집합은 여섯 개다. `docs/ko/`, `docs/en/` 리다이렉트 트리는 없다.
- 상대 링크가 저장소 안에서 해석된다.
- 금지 주장, `curl | sh`, `rm -rf` 안내, 일반 문서의 버전 리터럴은 없다.
- 관리자 제품 디렉터리마다 네 파일이 있다.
- `docs/history/`에서 `active_markdown_paths`에 들어가는 파일은 `README.md`뿐이다.

푸는 것:

- 제품 README와 사용자 문서 사이 장문 SHA-256 (`PRE_SDD_SHARED_SECTION_DIGESTS`와 같은 장문을 두 곳에 요구하는 단언).
- “사용자 가이드 네 파일 각각에 네 제품명이 모두 있어야 한다”는 카테시안 요구. 이후에는 파일 소유에 맞게: `installation.md`는 네 제품, `install-codex.md`는 세 Codex 제품, `install-local.md`는 `how-it-works`, `compatibility.md` / `safety-and-privacy.md` / `verification.md`는 네 제품.

새로 잠그는 것:

- 제품 README의 `## 안전과 개인정보` / `## Safety and privacy` 절, `## 검증` / `## Verification` 절, `## 업데이트와 제거` / `## Update and remove` 절이 없다.
- 그 장문이 제품 README 본문에 다시 있으면 실패한다.
- `installation.md`에 `<!-- how-it-works-local-links -->`가 없다.

`scripts/lib/documentation.py`의 `docs/users/<lang>/*.md` glob은 새 파일을 자동으로 집어넣는다. `USER_GUIDES`와 `PUBLIC_DOC_PATHS` 상수는 여섯 파일에 맞게 고친다. `test_changed_targets.py` 픽스처 경로가 옛 `installation.md`만 가리키면 새 파일도 사용자 문서 변경으로 라우팅되는지 확인한다.

### 8. 깨진 링크

리다이렉트 스텁은 없다. 저장소 안 상대 링크와 제품 README의 GitHub URL은 같은 변경에서 새 `install-*.md`를 가리킨다. `docs/history/` 본문은 이 설계 파일과 `README.md` 목록 외에는 건드리지 않는다. `SKILL.md`와 `catalog/` 본문은 링크가 깨질 때만 고친다.

이미 설치된 옛 제품 README는 `installation.md`를 가리킬 수 있다. 그 파일은 표로 남아 새 설치 문서로 보낸다.

## Implementation order

코드와 산 문서는 이 스펙이 승인된 뒤에만 바꾼다. 순서:

1. 공개 문서 테스트를 새 제목 순서, 여섯 사용자 파일, 장문 중복 금지, 설치 계약 `DOCUMENTS` 네 경로로 바꿔 실패하게 한다.
2. `docs/users/ko|en/`에 `install-codex.md`, `install-local.md`를 만들고 `installation.md`를 표로 줄인다. 안전·검증 문서는 이름을 유지한 채 픽스처 경로를 뺀다.
3. 제품 README 네 쌍을 새 템플릿으로 맞춘다. How It Works Python 블록은 유지한다. Pre-SDD `Contract` 목록은 `contract.md`로 옮긴다. 설치 페이로드가 바뀌므로 각 제품은 PATCH (`release.toml`, `SKILL.md` `metadata.version`, CHANGELOG)다. 태그는 만들지 않는다.
4. 루트 README와 `docs/README.md`를 입구만 남긴다.
5. 관리자 `architecture.md`를 줄이고, `testing.md`에 픽스처 경로를 옮기고, 제품 `release.md`의 공통 명령 중복을 줄인다.
6. `python3 scripts/verify.py`가 통과해야 끝이다.

## Verification

완료 조건:

1. `python3 scripts/verify.py`가 공급자 없이 통과한다.
2. 네 제품 한국어·영어 README의 H2가 결정 4의 일곱 개 제목이고 그 순서다. `### Contract`는 없다.
3. `docs/users/ko`와 `en`에 여섯 markdown 파일이 있고, 옛 세 이름이 포함된다.
4. How It Works Python 설치 블록이 네 문서에서 같고, `installation.md`에는 없다.
5. 제품 README에 안전·검증 장문 절이 없다.
6. `products.toml`과 관리자 네 파일 경로가 그대로다.
7. `SKILL.md`와 `catalog/` 본문이 의도 없이 바뀌지 않았다.
8. `git diff --check`가 통과한다.

통과한 패키지 테스트는 라이브 호스트 품질이나 공개 릴리스 증거가 아니다. 이 작업은 태그를 만들지 않는다.

## Recovery

- 공개 문서 테스트가 장문 해시나 옛 제목을 요구해 실패하면, 산 문서를 되돌리지 말고 테스트를 이 계약에 맞춘다.
- How It Works 링크 설치가 기존 대상을 바꾸면, Python 블록을 복구하고 `ln -s`를 다시 넣지 않는다.
- 한 제품 README만 새 제목이면 실패로 닫고 네 제품을 맞춘다.
- 링크가 저장소 밖이거나 없으면 `verify.py`가 실패로 닫는다.
- 설치되는 제품 README가 바뀌면 `versioning.md`대로 해당 제품은 PATCH다. 같은 변경에 `release.toml`, `SKILL.md` `metadata.version`, CHANGELOG를 올린다. 태그와 GitHub Release는 만들지 않는다.
- 관리자 문서·`docs/users/`·테스트만 바뀌는 커밋은 스킬 버전을 올리지 않는다.
