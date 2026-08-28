# Pre-SDD Review

[English](README.en.md)

## 이 스킬이 해결하는 문제

승인된 설계와 구현 계획이 서로 맞고 현재 저장소에서 실제로 실행 가능한지,
SDD 또는 계획 실행 직전에 검토합니다. 기본 흐름은 **검토 → 문서 개선 → 재검토**이며,
구현자가 기록되지 않은 제품 결정을 발명하지 않아도 되는지 확인하는 준비성 게이트입니다.

계획 경로가 주 입력입니다. 스킬은 그 계획의 `**Spec:**` 필드에서 해결된 설계 명세
경로를 찾습니다. `**Spec:**` 경로를 해석할 수 없으면 가까운 파일을 추측하지 않고
`BLOCKED`를 반환합니다.

## 사용해야 할 때와 사용하지 말아야 할 때

승인된 설계 명세와 구현 계획이 이미 있고, SDD 또는 계획 실행 전에 두 문서와
저장소 현실을 대조해야 할 때 사용합니다.

처음 설계나 계획을 작성할 때, 구현 코드·PR을 검토할 때, 출시 준비를 할 때,
교정하거나 일반 문서를 개선할 때는 사용하지 않습니다. 이 스킬은 외부 요청에
구현이 포함되지 않으면 SDD를 시작하지 않습니다.

## 1분 설치와 첫 호출

Codex는 공개 GitHub 경로를 가리키는 `$skill-installer`로 설치할 수 있습니다.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/pre-sdd-review
```

첫 호출에서는 계획 경로를 주 입력으로 삼고 설계 경로도 명시합니다.

```text
$pre-sdd-review docs/history/specs/<design>.md docs/history/plans/<plan>.md
```

실제 해석에서는 계획 경로가 primary이고, 그 계획의 `**Spec:**` 필드가 가리키는
해결된 설계 명세를 검토합니다. 인자로 쓴 설계 경로가 그 결정을 바꾸지 않습니다.

`review-only`는 명시 모드입니다.

```text
$pre-sdd-review review-only docs/history/specs/<design>.md docs/history/plans/<plan>.md
```

## 주요 흐름

기본 호출은 한 명의 새 읽기 전용 검토자가 증거 기반 발견을 내고, 제어 에이전트가
해결된 설계 명세와 해결된 구현 계획만 고친 뒤 범위를 좁혀 다시 검토합니다. 기본
호출은 이 두 문서만 변경합니다. `review-only`는 같은 검토를 하지만 아무 파일도
변경하지 않습니다.

수정 패스는 최대 두 번입니다. 최종 판정은 다음 중 하나입니다.

- `READY`: 기록된 증거로 구현을 시작할 수 있습니다.
- `REVISE`: 고칠 수 있는 중요한 문서 결함이 남았습니다.
- `BLOCKED`: 필요한 입력·권위·저장소 증거가 없어 안전하게 결정할 수 없습니다.

런타임/프레임워크 제거, 스키마 마이그레이션 또는 데이터 삭제, 인증·인가·보안
경계, public/private 데이터 경계, 게시·과금·메시징·프로덕션 변경 같은 외부 부작용이
있을 때만 두 번째 집중 검토자를 부릅니다. 설계나 계획 내용이 바뀌면 문서 지문이
무효화되어 다시 검토해야 합니다. 문서 밖 Git 변경도 경로·명령·인터페이스·영향 범위
근거를 바꾸면 다시 검토합니다.

## 안전과 개인정보

검토자는 읽기 전용입니다. 제어 에이전트는 기본 모드에서 해결된 설계 명세와 구현
계획만 수정하며, 승인된 ADR, 승인된 시각 권위, 애플리케이션 코드, 테스트, 설정,
생성물, 관련 없는 문서는 자동으로 바꾸지 않습니다. 승인된 제품 의도를 바꾸어야 하면
`BLOCKED`로 남깁니다.

제공자 없는 픽스처에는 사용자 문서나 전체 모델 응답을 저장하지 않습니다. 개인정보,
비공개 프롬프트, 공급자 트랜스크립트를 커밋하지 마세요.

## 호환성과 검증 수준

pre-sdd-review: Codex supported; other hosts not_measured.

Codex만 독립 읽기 전용 검토와 저장소 조사를 포함해 측정되었습니다. 제공자 없는
계약 검증은 패키지·지시문·픽스처 경계만 증명하며, 실제 모델 검토 품질이나 다른 호스트의
동등한 런타임을 증명하지 않습니다. 선택적 라이브 검사는 명시적이고 로컬에서만 하며
비용이 들 수 있고 CI가 요구하지 않습니다.

## 갱신과 버전 확인

업데이트나 제거 전에는 설치 대상이 정확히 이 스킬인지 확인하세요. 현재 버전 원본은
`release.toml`이고, 검증된 복제 값은 `SKILL.md`의 `metadata.version`입니다.
상위 `skills` 디렉터리나 홈 디렉터리를 삭제하지 마세요.

## 변경 이력과 관리자 문서

- [CHANGELOG](CHANGELOG.md)
- [계약](../../docs/maintainers/products/pre-sdd-review/contract.md)
- [테스트](../../docs/maintainers/products/pre-sdd-review/testing.md)
- [호환성](../../docs/maintainers/products/pre-sdd-review/compatibility.md)
- [릴리스](../../docs/maintainers/products/pre-sdd-review/release.md)
