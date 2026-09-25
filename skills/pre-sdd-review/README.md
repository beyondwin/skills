# Pre-SDD Review

[English](README.en.md)

## 목적

SDD(계획 실행) 직전에, 승인된 설계와 구현 계획이 서로 맞는지, 지금 저장소에서
그대로 실행할 수 있는지 확인합니다. 기본 흐름은 **검토 → 문서 개선 → 재검토**입니다.
묻는 것은 하나입니다. 구현자가 빠진 제품 결정을 추측하지 않고 계획대로 만들 수
있는가.

계획 경로가 주 입력입니다. 설계는 계획의 `**Spec:**` 필드가 가리키는 문서, 즉
해결된 설계 명세를 씁니다. 그 경로를 찾을 수 없으면 비슷한 파일을 추측하지 않고
`BLOCKED`를 냅니다.

- 판정을 내는 한 호출은 계획 하나만 다룹니다. 여러 계획의 결과를 합쳐 `READY`
  하나로 내지 않습니다.
- 요청에 계획이 둘 이상 있거나 사용자가 따로 요청하면, 판정을 내는 첫 호출 전에
  공유 파일 원장(여러 계획이 함께 건드리는 파일 목록)을 만드는 판정 없는 선행
  패스를 한 번 돌립니다.
- 계획이 필수 베이스(branch, ref, commit)를 적었는데 찾을 수 없거나 현재 `HEAD`의
  조상이 아니면, 검토 전에 `BLOCKED`입니다.

## 사용할 때와 사용하지 않을 때

- 사용: 승인된 설계와 구현 계획이 이미 있고, SDD나 계획 실행 직전일 때.
- 사용하지 않음: 설계·계획을 처음 쓸 때, 코드·PR 검토, 출시 준비 확인, 일반 문서
  교정.
- 요청에 구현이 없으면 이 스킬은 SDD를 시작하지 않습니다.

## 지원 호스트

pre-sdd-review: Codex supported; other hosts not_measured.

지금은 Codex에서만 지원합니다. 다른 호스트는 아직 확인하지 않았습니다. 자세한 내용은
[호환성](https://github.com/beyondwin/skills/blob/main/docs/users/ko/compatibility.md)을 보세요.

## 설치

Codex에서 공개 GitHub 경로를 `$skill-installer`에 넘깁니다.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/pre-sdd-review
```

선택 기록기는 따로 설치하지 않습니다. 스킬 폴더에서 바로 실행합니다.

```bash
python3 "<skill-root>/evidence/evidence.py" --version
```

다른 설치 방법은 [설치](https://github.com/beyondwin/skills/blob/main/docs/users/ko/install-codex.md)를 보세요.

## 첫 호출

설계와 계획 경로를 함께 적습니다.

```text
$pre-sdd-review docs/history/specs/<design>.md docs/history/plans/<plan>.md
```

설계 경로를 적어도, 실제로 검토할 설계는 계획의 `**Spec:**` 필드가 정합니다.

`review-only`는 명시 모드입니다. 문서를 고치지 않고 첫 판정만 받으려면 아래 예상
결과의 `review-only` 예를 보세요.

## 예상 결과

### 한 번 실행하면

1. 새 읽기 전용 검토자가 근거와 함께 문제(발견)를 찾습니다.
2. 제어 에이전트가 해결된 설계 명세, 구현 계획, 공유 파일 원장만 고친 뒤, 새
   검토자가 고친 곳만 다시 확인합니다(종결). 종결에는 수리 diff가 필요합니다.
3. 수정 패스는 최대 두 번입니다. 그 뒤 원래 지적 중 `IMPORTANT` 2건 이하가 한 자리
   수정으로 남으면, 같은 호출에서 한 번 더 고치고 그 지적만 다시 봅니다.

첫 검토에서 문제가 없으면 고치지 않고 바로 `READY`입니다. 단, 앞 계획의 수정이 이
계획이 읽는 파일을 바꿨으면 문제가 0건이어도 종결 재검토를 합니다.

원장은 유도된 증거일 뿐 권위가 아니며, 계획의 `Files:`와 어긋나면 계획이 이기고
원장을 다시 만듭니다. 스키마, 타입, 상태 전이, 조건부 수정, 작업 인터페이스, 검증
의미, 데이터 경계를 바꾸는 수정은 직접 쓰는 곳과 이웃 작업을 적은 영향 범위를 남겨
재검토에 함께 넘깁니다. 문구나 단순 값 수정에는 만들지 않습니다.

`review-only`는 같은 검토를 하지만 아무 파일도 변경하지 않습니다.

```text
$pre-sdd-review review-only docs/history/specs/<design>.md docs/history/plans/<plan>.md
```

### 판정

- `READY`: 남은 문제를 추측하지 않고 구현을 시작할 수 있습니다.
- `REVISE`: 고칠 수 있는 중요한 문서 결함이 남았습니다.
- `BLOCKED`: 필요한 입력·권위·저장소 증거가 없거나, 새 제품 결정이 필요합니다.

마지막 동작이 수리이면 `READY`가 아니고, 열린 `BLOCKER`가 있으면 `BLOCKED`입니다.
`READY` 보고에는 최종 문서 경로와 지문(SHA-256)을 적습니다. `finish`가 돌려준
관찰 이상(기록기가 본 어긋난 점)도 `Anomalies:` 줄로 적습니다. 이상이 판정을
바꾸지는 않습니다. 제품 의도를 지키는 수정은 묻지 않고 적용하고, 사용자 결정이
필요한 것만 한 번에 모아 묻습니다.

### 다음 실행

`REVISE`나 `BLOCKED` 뒤에는 자동으로 다시 실행하지 않습니다. 다시 부르면:

| 지난 판정 뒤 상황 | 이번 호출 |
| --- | --- |
| 문서, `HEAD`, 요청이 모두 그대로 | 다시 검토하지 않고 지난 인계(남은 문제 목록)를 그대로 씁니다 |
| `REVISE`였거나, 사용자 결정을 이제 문서에 적은 `BLOCKED`였고, 설계·계획·원장만 바뀜 | 새 발견 없이 종결부터 이어 검토합니다. 이 계획의 실행 기록(run)이 있어야 합니다 |
| 사용자 결정에 아직 답하지 않은 `BLOCKED` | 검토자를 부르지 않고 같은 질문을 다시 보여 주며 `Evidence: not_recorded; reason=previous-decision-checkpoint`를 출력합니다 |
| 그 밖의 경우(다른 파일도 바뀜, 전체 재검토 요청, 기록 없음) | 처음부터 새로 검토합니다 |

`execution`이 `full`인 run과 사유가 `focused-role-not-obtained`뿐인 `degraded` run의
인계만 재사용하며, 다른 `degraded`나 `blocked`인 run의 인계는 재사용하지 않습니다.
`degraded`는 역할마다 새 검토자를 구하지 못했거나 한 검토자를 겹쳐 쓴 run입니다.
새 사용자 결정 때문에 세 번 연속 `BLOCKED`가 나오면, 남은 결정을 한꺼번에
정하도록 설계로 돌려보냅니다.

### 여러 계획과 추가 검토자

나눈 계획의 발견은 겹칠 수 있고 수리는 겹치지 않습니다. 앞 계획이 `BLOCKED`여도 뒤
계획의 발견은 이어집니다. 시작할 때 찍은 `HEAD`가 도중에 바뀌면 그 기준으로 `READY`를
내지 않습니다.

두 번째 집중 검토자는 위험한 변경이 있을 때, 발견하는 호출에서만 부릅니다. 런타임
제거, 스키마 마이그레이션·데이터 삭제, 인증·인가·보안 경계, public/private 데이터
경계, 게시·과금·메시징·프로덕션 변경 같은 외부 부작용이 그 경우입니다. 한 검토자를
다른 계획 검토에 다시 쓰지 않습니다.

문서 지문이 바뀌면 이전 `READY`는 무효이고 다시 검토해야 합니다. 문서 밖 Git 변경도
경로·명령·인터페이스·영향 범위 근거를 바꾸면 같습니다.

### 선택 기록기

handshake가 정확히 `skill_name=pre-sdd-review`와 `schema=4`일 때만 호환입니다.
정규 handshake 줄의 정확한 바이트는 [evidence README](evidence/README.md)를 보세요.

- 호환되는 기록기가 있으면 먼저 `summary`로 이 계획의 지난 run을 보고, 검토 전
  `start`, 최종 판정 뒤 `finish`를 부른 다음 `Evidence: recorded; run_id=<run-id>`를
  출력합니다. `run_id`는 사용자 문서에 적지 않습니다.
- 끝나지 않은 같은 계획의 run과 도중에 멈춘 호출은 `abandon`으로 닫습니다.
- 기록기가 없거나 호환되지 않거나 권한 오류가 나도 검토는 계속되고
  `Evidence: not_recorded; reason=<code>`를 출력합니다. 판정은 바뀌지 않습니다.

기록은 `~/.pre-sdd-review/`에 로컬로만 남습니다. 로컬 파일 저장은 서명된 audit
log가 아닙니다. `outcome`(SDD 뒤 붙이는 결과 표시)과 `summary`는
[evidence README](evidence/README.md)를 보세요.

## 더 보기

- [안전과 개인정보](https://github.com/beyondwin/skills/blob/main/docs/users/ko/safety-and-privacy.md)
- [검증](https://github.com/beyondwin/skills/blob/main/docs/users/ko/verification.md)
- [CHANGELOG](CHANGELOG.md)
- [계약](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/pre-sdd-review/contract.md)
- [테스트](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/pre-sdd-review/testing.md)
- [호환성](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/pre-sdd-review/compatibility.md)
- [릴리스](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/pre-sdd-review/release.md)
- [evidence README](evidence/README.md)
