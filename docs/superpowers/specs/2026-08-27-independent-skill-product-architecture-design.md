# 독립 스킬 제품 구조와 릴리스 체계 설계

- 작성일: 2026-08-27
- 상태: 대화 설계 승인 완료, 작성된 명세 검토 대기
- 범위: 저장소 구조, 스킬별 버전, 문서 정보구조, 검증, 패키징, 릴리스
- 비범위: 스킬 동작 재설계, 새 스킬 추가, 실제 저장소 분리, 이번 문서에서의 공개 릴리스

## 1. 결정 요약

이 저장소는 모노레포를 유지하되 `korean-writing-editor`,
`image-workbench`, `graspic`을 서로 독립적인 제품으로 관리한다.
각 제품은 자체 SemVer, 변경 이력, 사용자 문서, 검증 명령, 배포 아티팩트,
Git 태그와 GitHub Release를 가진다.

`beyondwin-skills` Codex 플러그인은 제품 계약을 소유하지 않는다. 검증된
스킬 릴리스를 특정 버전으로 채택해 함께 설치하는 얇은 카탈로그이자 번들이다.
플러그인은 스킬과 별도의 버전 및 변경 이력을 가진다.

한국어를 사람 대상 문서의 원본 언어로 사용한다. 영어는 설치, 사용,
호환성, 안전처럼 공개 사용에 필요한 핵심 문서만 동등하게 제공한다.
에이전트가 소비하는 `SKILL.md` 실행 계약은 현재처럼 영어로 유지한다.

## 2. 현재 상태와 해결할 문제

설계 조사를 시작한 2026-08-27의 `main`은 `origin/main`과 일치하고 추적
변경사항이 없었다. 공개 태그는 레거시 통합 릴리스 `v2.0.0` 하나였다.
그 기준선에서 소스에는 세 스킬이 모두 있고 플러그인과 각 `SKILL.md`는
모두 `2.0.0`을 표기했다.

명세 작성 중 별도 작업으로 `graspic` 실행 계약과 버전 `3.0.0` 변경이 작업
트리에 추가되었고 사용자가 이를 다음 기준으로 승인했다. 이 설계는 그 변경을
되돌리거나 포함해 커밋하지 않으며, 마이그레이션 시 `graspic 3.0.0`을 첫 독립
공개 릴리스 목표로 사용한다.

현재 체계에는 다음 문제가 있다.

1. `docs/maintainers/release-process.md`는 스킬별 독립 버전을 설명하지만,
   `tests/contract/test_repository.py`는 하나의 `EXPECTED_VERSION`으로
   플러그인과 모든 스킬의 동일 버전을 강제한다.
2. 루트 README, 한영 공개 문서, 관리자 문서, 테스트가 같은 버전과 지원
   문장을 여러 번 소유한다. 새 스킬을 추가할 때 변경 범위가 넓고 누락되기 쉽다.
3. `graspic` 추가 뒤에도 일부 이슈 템플릿은 두 스킬만 허용한다. 카탈로그
   사실과 커뮤니티 표면이 이미 어긋났다.
4. 개별 스킬은 `SKILL.md`와 런타임 파일은 모여 있지만 자신의 README,
   CHANGELOG, 릴리스 매니페스트가 없다. 제품의 현재 상태를 한 위치에서
   파악하기 어렵다.
5. 기존 릴리스 도구는 한 번들 버전을 받아 플러그인과 모든 standalone ZIP을
   함께 만든다. 한 스킬만 검증하고 출시할 수 있는 제품 경계가 없다.
6. 로컬 빌드, 태그, 공개 GitHub Release, 원격 다운로드 검증의 상태가 문장에
   의존한다. 제품별 출시 완료 조건이 기계적으로 표현되지 않는다.

## 3. 목표와 비목표

### 3.1 목표

- 저장소 루트에서 각 스킬의 역할과 소유 파일을 빠르게 이해할 수 있다.
- 한 스킬의 변경이 다른 스킬 버전이나 CHANGELOG를 변경하지 않는다.
- 현재 버전, 태그 형식, 아티팩트 이름과 릴리스 검증 규칙에 단일 소유자가 있다.
- 사용자는 루트에서 두 번 이하의 링크 이동으로 설치와 첫 호출에 도달한다.
- 관리자는 한 스킬의 계약 변경 시 함께 수정할 문서와 테스트를 찾을 수 있다.
- 한국어와 영어 공개 문서의 필수 사실 불일치를 CI가 차단한다.
- 개별 스킬과 카탈로그를 서로 다른 시점에 안전하게 출시할 수 있다.
- 기존 공개 `v2.0.0`, 설치 URL, 전체 검증 명령을 보존한다.

### 3.2 비목표

- 세 스킬의 프롬프트, 활성화 경계, 기본 모드 또는 출력 계약 변경
- 네 번째 스킬 추가
- 스킬마다 별도 Git 저장소 생성
- 라이브 모델 또는 이미지 공급자 호출을 필수 CI로 승격
- 기존 태그 이동, 기존 GitHub Release 교체 또는 역사 재작성
- 설계 승인만으로 태그, GitHub Release 또는 외부 배포를 수행

## 4. 설계 원칙

### 4.1 제품은 독립적으로 소유한다

각 제품은 이름, 버전, 공개 안내, 변경 이력, 런타임 계약과 릴리스 결과를
스스로 소유한다. 공통 도구는 이를 검증할 수 있지만 제품 버전을 대신
결정하지 않는다.

### 4.2 한 사실에는 한 소유자만 둔다

- 현재 제품 버전: `skills/<name>/release.toml`
- 배포된 에이전트 메타데이터 버전: `SKILL.md`의 검증된 복제 값
- 사용자가 체감하는 변경 이력: 해당 제품의 `CHANGELOG.md`
- 실행 계약: 해당 제품의 `SKILL.md`와 직접 참조하는 런타임 파일
- 카탈로그가 채택한 제품 버전: `catalog/catalog.lock.json`
- 플러그인 버전: `catalog/release.toml`
- 지원 정책의 공통 정의: 한영 호환성 문서
- 릴리스 완료 증거: 원격 다운로드 checksum과 추출 설치 smoke 결과

README는 위 사실을 다시 정의하지 않는다. 사용자가 성공하는 경로를 설명하고
소유 문서로 연결한다.

### 4.3 설치 페이로드와 개발 증거를 구분한다

제품 README, 영어 핵심 README, CHANGELOG, `release.toml`, 라이선스와 실행에
필요한 파일은 제품 패키지에 포함할 수 있다. 테스트, 관리자 문서, 라이브
증거, 저장소 운영 도구는 설치 페이로드 밖에 둔다.

### 4.4 릴리스는 원격 바이트로 증명한다

로컬 테스트, 로컬 ZIP, 태그 또는 Draft Release만으로 출시 완료라고 하지
않는다. 공개할 아티팩트를 원격에서 다시 내려받아 checksum과 추출 설치
smoke를 통과한 뒤에만 공개 Release로 전환한다.

## 5. 목표 저장소 구조

```text
.
├── .codex-plugin/
│   └── plugin.json
├── catalog/
│   ├── README.md
│   ├── CHANGELOG.md
│   ├── release.toml
│   └── catalog.lock.json
├── skills/
│   ├── korean-writing-editor/
│   │   ├── SKILL.md
│   │   ├── README.md
│   │   ├── README.en.md
│   │   ├── CHANGELOG.md
│   │   ├── release.toml
│   │   ├── LICENSE.txt
│   │   ├── agents/
│   │   ├── references/
│   │   └── scripts/
│   ├── image-workbench/
│   │   └── ...
│   └── graspic/
│       └── ...
├── docs/
│   ├── users/
│   │   ├── ko/
│   │   │   ├── installation.md
│   │   │   ├── compatibility.md
│   │   │   ├── safety-and-privacy.md
│   │   │   └── verification.md
│   │   └── en/
│   │       └── ...
│   ├── maintainers/
│   │   ├── README.md
│   │   ├── repository/
│   │   │   ├── architecture.md
│   │   │   ├── versioning.md
│   │   │   └── catalog-release.md
│   │   ├── korean-writing-editor/
│   │   │   ├── contract.md
│   │   │   ├── testing.md
│   │   │   └── release.md
│   │   ├── image-workbench/
│   │   │   └── ...
│   │   ├── graspic/
│   │   │   └── ...
│   │   └── decisions/
│   └── superpowers/
├── scripts/
├── tests/
│   ├── contract/
│   ├── korean-writing-editor/
│   ├── image-workbench/
│   └── graspic/
├── README.md
└── README.en.md
```

`skills/<name>` GitHub 경로를 유지하므로 기존 `$skill-installer` 설치 URL은
바뀌지 않는다. 제품의 사용자 진입점과 변경 이력은 런타임 계약 옆에 두되,
무거운 테스트와 관리자 문서는 계속 설치 경계 밖에 둔다.

## 6. 제품 릴리스 매니페스트

각 `skills/<name>/release.toml`은 최소한 다음 값을 가진다.

```toml
schema_version = 1
name = "graspic"
version = "3.0.0"
tag_prefix = "graspic-v"
license = "Apache-2.0"
```

경로와 아티팩트 이름은 중복 기록하지 않고 위치와 규칙으로 유도한다.

- 제품 루트: 매니페스트가 있는 디렉터리
- 태그: `<tag_prefix><version>`
- standalone 아티팩트: `<name>-v<version>.zip`
- checksum 목록: 해당 Draft Release의 `SHA256SUMS`
- CHANGELOG: 같은 디렉터리의 `CHANGELOG.md`
- 런타임 계약: 같은 디렉터리의 `SKILL.md`

검증기는 다음 불일치를 실패로 처리한다.

- 디렉터리명, `release.toml` 이름, `SKILL.md` 이름 불일치
- 유효하지 않은 SemVer 또는 예상 태그 형식
- `release.toml`과 `SKILL.md metadata.version` 불일치
- 개발 중에는 `Unreleased` 변경 항목, 릴리스 준비 시에는 현재 버전과 날짜가
  있는 CHANGELOG 항목 부재
- 루트 라이선스와 제품 라이선스 불일치
- 허용되지 않은 파일, 심볼릭 링크, 특별 파일 또는 깨진 상대 링크

`SKILL.md metadata.version`은 Agent Skills 소비자가 읽을 배포용 복제 값이다.
사람과 도구가 버전을 변경할 때의 원본은 `release.toml`이며, CI가 두 값을
원자적으로 함께 변경하도록 강제한다. 자동 동기화로 소스 파일을 조용히
수정하지 않는다.

개발 중 `release.toml.version`은 다음 출시 목표 버전을 가리킨다. 설치 payload가
마지막 공개 제품 태그와 달라졌는데 버전이 그대로면 CI가 실패한다. 릴리스
준비 시 `Unreleased`의 출시 대상 항목을 `## <version> - <date>`로 확정하고
새 빈 `Unreleased` 섹션을 연다. 릴리스 빌드는 현재 버전의 날짜 있는 항목이
없으면 실패한다.

## 7. 카탈로그 모델

`beyondwin-skills`는 별도 제품이며 다음 파일을 소유한다.

- `catalog/release.toml`: 플러그인 이름, 버전, 태그 접두사
- `catalog/CHANGELOG.md`: 카탈로그 구성과 통합 표면 변경
- `catalog/README.md`: 카탈로그의 역할, 채택 규칙, 설치 안내
- `catalog/catalog.lock.json`: 채택한 스킬의 불변 릴리스 식별자
- `.codex-plugin/plugin.json`: Codex가 읽는 배포용 플러그인 메타데이터

`catalog.lock.json`의 각 항목은 다음 값을 가진다.

```json
{
  "schema_version": 1,
  "skills": [
    {
      "name": "graspic",
      "version": "3.0.0",
      "tag": "graspic-v3.0.0",
      "source_commit": "40-character-lowercase-git-commit",
      "payload_sha256": "64-character-lowercase-sha256"
    }
  ]
}
```

실제 파일에서는 구체적인 commit과 hash만 허용하며 설명용 자리 문자열은
허용하지 않는다. 항목은 제품 이름으로 정렬해 재현 가능한 직렬화를 유지한다.

카탈로그 검증기는 다음을 확인한다.

1. lock schema, 제품 이름 정렬, 항목 유일성과 SemVer·commit·hash 형식이 맞다.
2. `catalog/release.toml`과 `.codex-plugin/plugin.json` 버전이 같다.
3. 릴리스 입력 검증 단계에서 각 standalone ZIP의 이름, 내부
   `release.toml`, `SKILL.md`, payload hash가 lock 항목과 같다.
4. 원격 릴리스 검증 단계에서 lock의 태그, source commit, 공개 아티팩트와
   checksum이 모두 일치한다.

개별 스킬 릴리스가 카탈로그 lock을 자동으로 바꾸지 않는다. 별도 채택 변경과
통합 검증이 있어야 새 플러그인 번들에 들어간다.

lock은 현재 `main`의 제품 버전과 같을 필요가 없다. 최신 제품 소스가 앞으로
진행되어도 기존 카탈로그는 채택한 이전 릴리스를 계속 고정할 수 있어야 한다.
따라서 카탈로그 ZIP은 현재 `skills/`를 복사해 만들지 않고, lock과 일치하는
검증된 standalone 릴리스 ZIP들을 입력으로 조립한다. 저장소 루트의 플러그인
표면은 개발 중 발견과 통합 검증을 위한 작업 공간이며 공개 번들 증거가 아니다.

## 8. SemVer 정책

SemVer는 구현 파일 수가 아니라 외부에서 관찰 가능한 제품 계약의 영향을
기준으로 판단한다.

| 변경 | 스킬 버전 | 예시 |
| --- | --- | --- |
| 문서화된 계약을 회복하는 호환 결함 수정 | PATCH | 잘못된 분기, 깨진 상대 링크, 투명한 보안 강화 |
| 설치되는 README·CHANGELOG·패키지 메타데이터 변경 | PATCH | 설치법 정정, 릴리스 provenance 보강 |
| 기본 동작을 유지하는 명시적 opt-in 기능 | MINOR | 새 선택 모드, 새 선택 인자, 선택적 스크립트 |
| 활성화 또는 near-miss 경계의 비호환 변경 | MAJOR | 이전에 no-op이던 요청의 암묵 활성화 |
| 기본 모드·기본 출력·필수 입력 변경 | MAJOR | 기본 경로 변경, 출력 형식 제거 또는 이름 변경 |
| 필수 런타임·안전·데이터 처리 계약 변경 | MAJOR | 새 필수 공급자, 데이터 보존 정책 변경 |
| 설치되지 않는 테스트·관리자 문서·CI만 변경 | 없음 | 테스트 리팩터링, 내부 운영 문구 정리 |

`SKILL.md`, `agents/openai.yaml`, 런타임 `references/`와 `scripts/` 변경은 단순
문구 수정으로 자동 간주하지 않는다. 에이전트 동작에 영향을 줄 수 있으므로
계약 영향 평가와 최소 PATCH가 필요하다. 반대로 관리자 문서나 저장소 검증
도구만 바뀌고 배포 제품이 동일하면 스킬 버전을 올리지 않는다.

카탈로그 SemVer는 번들을 설치하는 사용자의 호환성 영향을 따른다.

- 채택한 스킬 중 MAJOR가 있으면 카탈로그 MAJOR
- 채택한 스킬 중 가장 높은 변경이 MINOR면 카탈로그 MINOR
- PATCH만 채택하면 카탈로그 PATCH
- 새 스킬 추가는 MINOR, 스킬 제거·이름 변경은 MAJOR
- 카탈로그 표시 문구나 호환 결함 수정은 PATCH

카탈로그 버전은 스킬 버전과 숫자를 맞출 필요가 없다.

## 9. 문서 정보구조

### 9.1 읽기 흐름

사용자는 다음 순서로 문서를 읽는다.

1. 루트 README에서 필요한 스킬을 선택한다.
2. `skills/<name>/README.md`에서 대상, 비대상, 설치, 첫 호출을 확인한다.
3. 필요한 경우에만 공통 호환성·안전·검증 문서로 이동한다.

관리자는 `docs/maintainers/README.md`에서 저장소 공통 규칙 또는 특정 제품의
계약, 테스트, 릴리스 문서로 이동한다.

### 9.2 문서별 책임

#### 루트 README

- 저장소 한 문장 설명
- 세 스킬의 선택표
- 기본 설치 진입점
- 공통 검증 명령
- 각 제품 README와 공통 정책 문서 링크

루트 README는 각 스킬의 현재 버전, 상세 모드, 계약 전문이나 릴리스 이력을
소유하지 않는다.

#### 제품 README

한국어 `README.md`는 다음 순서를 공통으로 사용한다.

1. 이 스킬이 해결하는 문제
2. 사용해야 할 때와 사용하지 말아야 할 때
3. 1분 설치와 첫 호출
4. 주요 모드 또는 작업 흐름
5. 안전, 개인정보, 권리 경계
6. 호환성과 검증 수준
7. 갱신과 버전 확인
8. CHANGELOG와 관리자 문서 링크

`README.en.md`는 같은 공개 핵심 사실과 명령을 제공하되 관리자 운영 설명을
번역하지 않는다.

#### SKILL.md

에이전트가 따라야 하는 실행 계약만 둔다. 기여 방법, 릴리스 절차, 저장소
마이그레이션 역사와 사람 대상 장문의 배경 설명을 넣지 않는다.

#### 관리자 문서

- `contract.md`: 어떤 외부 동작을 소유하며 변경 시 무엇을 함께 고치는가
- `testing.md`: 테스트 층, fixture 의미, 명령과 증거 한계
- `release.md`: 제품별 판정, 빌드, 원격 검증과 실패 복구
- `repository/`: 공통 구조, 버저닝과 카탈로그 릴리스
- `decisions/`: 여러 제품에 장기간 영향을 주는 결정만 기록

단순 수정마다 ADR을 만들지 않는다. 현재 코드와 문서만으로 이유를 잃기 쉬운
교차 제품 결정에만 ADR을 사용한다.

### 9.3 문서 품질 게이트

- 모든 내부 Markdown 링크와 앵커를 검사한다.
- 루트와 관리자 인덱스에서 도달하지 못하는 고아 문서를 차단한다.
- 제품 README의 필수 섹션을 검사한다.
- 한영 공개 핵심의 설치 명령, 제품 집합, 지원 상태와 안전 문구를 비교한다.
- 일반 README에 현재 버전 리터럴을 중복 기록하지 못하게 한다.
- 레거시 기록과 CHANGELOG는 역사적 버전 리터럴 검사의 예외로 둔다.
- `exactly two skills`처럼 현재 카탈로그와 충돌하는 문구를 계약 테스트로 찾는다.
- 문서에서 오프라인 픽스처를 라이브 품질 증거로 표현하지 못하게 한다.

## 10. 검증 구조

### 10.1 명령 표면

기존 전체 명령은 유지한다.

```bash
python3 scripts/verify.py
python3 scripts/verify.py --profile windows-portable
```

제품별 검증을 추가한다.

```bash
python3 scripts/verify.py --skill korean-writing-editor
python3 scripts/verify.py --skill image-workbench
python3 scripts/verify.py --skill graspic
python3 scripts/verify.py --catalog
```

스킬과 카탈로그 선택을 동시에 주면 실패한다. `--profile`은 선택한 대상 안에서
현재와 같은 플랫폼 제약을 적용한다.

### 10.2 검증 계층

1. 매니페스트, 버전, 이름, 라이선스, 링크의 정적 계약
2. 제품별 결정적 fixture와 단위 테스트
3. 아티팩트 허용 목록, 재현 가능한 ZIP과 checksum 검사
4. 추출한 제품의 설치 및 실행 smoke
5. 선택적 라이브 평가와 측정된 호환성 증거

1~4는 해당 제품의 독립 릴리스 필수 게이트다. 5는 명시적이고 잠재적으로
비용이 들며 CI 필수 조건이 아니다. 라이브 결과는 오프라인 통과 상태를
대체하거나 다른 제품의 릴리스를 승인하지 않는다.

### 10.3 CI 선택 규칙

- PR에서는 변경 경로에 해당하는 제품과 공통 계약을 실행한다.
- 공통 검증기, 패키저, 라이선스, 카탈로그 또는 문서 동등성 검사 변경은
  영향받을 수 있는 모든 제품을 실행한다.
- `main` push에서는 전체 provider-free 검증을 실행한다.
- 경로 선택 최적화가 전체 `main` 검증을 대체하지 않는다.
- Windows portable 프로필과 Codex 전용 이미지 검증의 현재 경계를 유지한다.

## 11. 개별 스킬 릴리스 흐름

### 11.1 준비

관리자는 제품의 `release.toml`, `SKILL.md metadata.version`, CHANGELOG 항목과
필요한 테스트를 함께 변경한다. 릴리스 도구가 버전을 추정하거나 소스를
조용히 수정하지 않는다.

다음 읽기 전용 검사를 먼저 실행한다.

```bash
python3 scripts/verify.py --skill <name>
python3 scripts/release.py check --product <name>
```

검사는 깨끗한 추적 트리, SemVer, CHANGELOG, 태그 충돌, 제품 범위와 필수
검증 결과를 확인한다.

### 11.2 패키징

```bash
python3 scripts/release.py build --product <name> --output <new-empty-directory>
```

빌드는 추적 파일만 읽고 다음을 보장한다.

- standalone ZIP 하나와 `SHA256SUMS`
- 정렬된 멤버와 고정 timestamp·mode
- 절대 경로, `..`, 중복, 대소문자 충돌, 심볼릭 링크와 특별 파일 거부
- 제품 패키지 허용 목록 밖의 테스트·관리자 자료·증거 제외
- 새 빈 출력 디렉터리만 사용하고 기존 결과를 덮어쓰지 않음
- 추출 후 제품 검증과 설치 smoke 재실행

### 11.3 태그와 Draft Release

제품 태그는 `<name>-v<version>` 형식의 annotated tag다. 이미 존재하는 태그는
재사용하거나 이동하지 않는다. 태그와 Draft Release 생성은 명시적인 출시
작업이며 로컬 빌드 명령의 부수 효과가 아니다.

Draft에 ZIP과 `SHA256SUMS`를 업로드한 뒤 새 디렉터리로 다시 내려받는다.

```bash
python3 scripts/release.py verify-download \
  --product <name> \
  --input <fresh-download-directory>
```

다운로드한 checksum, ZIP 구조, 추출 payload hash, 제품 검증과 설치 smoke가
모두 통과해야 Draft를 공개한다.

### 11.4 실패 처리

- 로컬 검증 실패: 파일, 버전, CHANGELOG 또는 테스트를 고치고 다시 검증한다.
- 패키징 실패: 새 출력 디렉터리에서 다시 빌드한다. 부분 결과를 재사용하지 않는다.
- 태그 뒤 Draft 실패: 태그를 이동하지 않는다. 같은 커밋의 정확한 아티팩트만
  고쳐서 검증하거나, 코드 변경이 필요하면 새 버전을 준비한다.
- 원격 검증 실패: Draft를 비공개로 유지한다. 로컬 성공을 공개 증거로 대체하지 않는다.
- 한 제품 실패: 다른 제품의 버전, 태그, Release와 카탈로그 lock을 바꾸지 않는다.

## 12. 카탈로그 채택과 릴리스

카탈로그 변경은 공개되고 원격 검증을 통과한 스킬 릴리스만 채택한다.
채택 변경은 lock 항목, 카탈로그 CHANGELOG, 필요한 플러그인 버전과
`.codex-plugin/plugin.json` 복제 값을 함께 수정한다.

카탈로그 릴리스 준비는 각 lock 항목의 standalone ZIP과 `SHA256SUMS`를 새
입력 디렉터리에 내려받는다. 이 입력은 개별 제품의 원격 검증을 다시 통과해야
한다. 카탈로그 빌드는 현재 `skills/`가 아니라 이 검증된 입력에서 제품
payload를 추출해 플러그인 ZIP을 조립한다.

카탈로그 빌드는 다음을 확인한다.

1. lock의 모든 제품 릴리스가 존재하고 공개 상태다.
2. 원격 아티팩트와 checksum이 lock의 payload hash와 일치한다.
3. 완성된 번들의 각 제품 payload와 입력 standalone payload가 byte-equivalent다.
4. 플러그인 ZIP에 lock에 없는 스킬이 없고 빠진 스킬도 없다.
5. 추출한 플러그인에서 세 스킬 발견과 설치 smoke가 통과한다.

스킬을 출시하는 작업과 카탈로그가 그 버전을 채택하는 작업은 별도다.
독립 스킬 릴리스가 카탈로그 버전을 자동으로 올리거나 공개하지 않는다.

## 13. 마이그레이션

### 13.1 기준선 고정

- 기존 `v2.0.0` 태그와 공개 Release URL을 기록한다.
- 원격 standalone ZIP과 plugin ZIP을 새 디렉터리에 내려받아 checksum과 payload
  hash를 기록한다.
- 현재 `main`의 세 제품 payload hash와 전체 provider-free 검증 결과를 기록한다.
- `v2.0.0` 태그 이후 추가된 `graspic`을 기존 릴리스에 포함됐다고 표현하지 않는다.

### 13.2 제품 계약 분리

- 세 제품에 `release.toml`, README, 영어 핵심 README, CHANGELOG를 추가한다.
- 기존 통합 CHANGELOG에서 각 제품에 해당하는 사실을 옮기되 역사와 공개
  상태를 바꾸지 않는다.
- 루트 CHANGELOG는 `catalog/CHANGELOG.md`로 역할을 좁힌다.
- 모든 스킬이 같은 `EXPECTED_VERSION`을 가져야 하는 테스트를 제품별
  매니페스트 기반 검증으로 교체한다.

### 13.3 문서 재구성

- 루트 README를 짧은 카탈로그 입구로 줄인다.
- 기존 `docs/ko`와 `docs/en`의 공통 사용자 문서를 `docs/users`로 이동한다.
- 기존 공개 경로에는 한 카탈로그 minor 릴리스 동안 새 위치 안내 stub을 둔다.
- 관리자 문서를 저장소 공통 문서와 제품별 contract/testing/release로 분리한다.
- 이슈 템플릿과 PR 템플릿의 제품 목록을 카탈로그와 일치시킨다.

### 13.4 검증과 릴리스 도구 분리

- `verify.py`에 제품과 카탈로그 선택을 추가한다.
- 기존 인자 없는 전체 검증의 동작과 종료 코드를 유지한다.
- 독립 제품 build/check/verify-download 흐름을 추가한다.
- 기존 `build_release.py` 명령은 한 카탈로그 minor 동안 새 명령을 안내하는
  호환 wrapper로 유지한다.
- 계약, 결정적 아카이브, 실패 원자성과 원격 다운로드 검증 테스트를 추가한다.

### 13.5 첫 독립 릴리스

| 제품 | 첫 독립 릴리스 | 근거 |
| --- | --- | --- |
| `korean-writing-editor` | `2.0.1` | 기존 `v2.0.0` standalone ZIP을 계승하는 호환 패키지·문서 변경 |
| `image-workbench` | `2.0.1` | 기존 `v2.0.0` standalone ZIP을 계승하는 호환 패키지·문서 변경 |
| `graspic` | `3.0.0` | 승인된 비호환 실행 계약 변경을 포함한 최초 독립 공개 릴리스 |
| `beyondwin-skills` | `2.1.0` | 세 번째 제품 채택과 새 lock 기반 카탈로그 체계 |

기존 `v2.0.0`에 소급해서 개별 제품 태그를 만들지 않는다. 기존 태그와
Release는 레거시 통합 기준선으로 보존하고 각 CHANGELOG에서 provenance를
명확히 설명한다. `graspic 2.0.0`은 공개 제품 릴리스였다고 기록하지 않는다.
승인된 현재 작업이 그대로 통합된다는 전제에서 `graspic 3.0.0`이 첫 독립
공개 버전이다.

독립 스킬을 원격 검증까지 완료한 뒤 카탈로그 `2.1.0`을 출시한다. 공개
작업은 구현 계획과 별도의 명시적 승인 대상이다.

## 14. 호환성과 롤백

### 14.1 유지할 호환성

- `skills/<name>` 설치 URL
- `python3 scripts/verify.py` 전체 검증 명령
- 세 스킬의 현재 활성화, 기본 모드, 출력과 안전 계약
- Apache-2.0 루트 및 standalone 라이선스
- provider-free 필수 CI와 선택적 live 경계

### 14.2 단계별 롤백

구현은 다음 경계로 나누고 각 단계는 독립 검증과 되돌릴 수 있는 커밋을 가진다.

1. 기준선과 매니페스트 스키마
2. 제품 문서와 CHANGELOG
3. 문서 정보구조와 호환 stub
4. 제품별 검증
5. 독립 패키징과 원격 검증
6. 카탈로그 lock과 채택 검증

공개 태그 전에는 해당 단계 커밋을 수정하거나 revert할 수 있다. 공개 태그
후에는 태그를 이동하거나 Release 바이트를 교체하지 않는다. 수정이 필요하면
새 제품 버전을 준비한다.

## 15. 완료 기준

다음 조건이 모두 충족되어야 구조 개편 구현이 완료다.

- [ ] 루트에서 두 번 이하의 링크 이동으로 각 제품의 설치와 첫 호출에 도달한다.
- [ ] 각 제품 루트에 README, 영어 핵심 README, CHANGELOG, `release.toml`이 있다.
- [ ] 한 제품만 검증하고 패키징할 수 있다.
- [ ] 한 제품 버전 변경이 다른 제품 파일이나 버전을 요구하지 않는다.
- [ ] `release.toml`, `SKILL.md`, CHANGELOG 불일치를 CI가 차단한다.
- [ ] 루트 README와 일반 사용자 문서에 현재 버전 리터럴이 중복되지 않는다.
- [ ] 한영 공개 핵심의 명령, 제품 집합, 지원 상태, 안전 사실을 CI가 비교한다.
- [ ] 고아 문서, 깨진 링크와 오래된 두 스킬 전용 템플릿이 없다.
- [ ] 기존 설치 URL과 인자 없는 전체 검증 명령이 유지된다.
- [ ] 독립 ZIP은 재현 가능하며 허용된 제품 파일만 포함한다.
- [ ] 원격 다운로드 checksum과 추출 설치 smoke 없이는 공개 완료로 표시되지 않는다.
- [ ] 기존 `v2.0.0` 태그와 Release 기록이 변경되지 않는다.
- [ ] 전체 provider-free 검증과 `git diff --check`가 통과한다.

## 16. 승인 기록

대화에서 다음 결정이 순서대로 승인되었다.

1. 스킬을 완전히 독립된 제품으로 버전·문서·테스트·릴리스한다.
2. 모노레포는 유지하고 제품별 경계를 강화한다.
3. `beyondwin-skills`는 얇은 카탈로그 플러그인으로 유지한다.
4. 한국어 문서를 원본으로 하고 영어는 공개 핵심만 제공한다.
5. 기존 `2.0.0` 버전과 이력을 보존한다.
6. 기존 설치 경로를 지키는 제품 중심 디렉터리 구조를 사용한다.
7. 문서 정보구조, 독립 릴리스·검증 흐름과 단계적 마이그레이션을 적용한다.
8. 명세 작성 중 시작된 `graspic 3.0.0` 작업을 보존하고 첫 독립 공개 버전
   목표를 `3.0.0`으로 조정한다.

이 문서가 검토 승인된 뒤에만 상세 구현 계획을 작성한다.
