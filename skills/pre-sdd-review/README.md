# Pre-SDD Review

[English](README.en.md)

## 이 스킬이 해결하는 문제

승인된 설계와 구현 계획이 서로 맞고, 지금 저장소에서 실행 가능한지 SDD 직전에
확인합니다. 기본 흐름은 **검토 → 문서 개선 → 재검토**입니다. 핵심은 구현자가
빠진 제품 결정을 추측하지 않고도 계획을 실행할 수 있는지입니다.

계획 경로가 주 입력입니다. 스킬은 계획의 `**Spec:**` 필드가 가리키는 해결된 설계
명세를 검토합니다. 경로를 해석할 수 없으면 가까운 파일을 추측하지 않고
`BLOCKED`를 반환합니다. 한 번의 호출은 계획 하나만 다룹니다. 여러 계획을 따로
검토한 결과를 합쳐 `READY`로 보지 않습니다.

계획이 필수 구현 베이스 branch, ref, commit을 명시하면 검토자를 부르기 전에
그 베이스가 현재 `HEAD`의 조상인지 확인합니다. 해석할 수 없거나 조상이 아니면
다른 checkout을 추측하지 않고 `BLOCKED`를 반환합니다.

## 사용해야 할 때와 사용하지 말아야 할 때

승인된 설계 명세와 구현 계획이 이미 있고, SDD나 계획 실행 직전에 두 문서와
저장소 현실을 대조할 때 사용합니다.

처음 설계나 계획을 작성할 때, 구현 코드·PR을 검토할 때, 출시 준비를 확인할 때,
일반 문서를 교정할 때는 사용하지 않습니다. 외부 요청에 구현이 포함되지 않으면
이 스킬은 SDD를 시작하지 않습니다.

## 설치

Codex에서는 공개 GitHub 경로를 `$skill-installer`에 전달합니다.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/pre-sdd-review
```

로컬 영수증 기록기는 설치하지 않습니다. 스킬 폴더의 `evidence/evidence.py`를
Python 3.11+로 직접 실행합니다. 컨트롤러는 이미 로드한 스킬 루트를 그대로 씁니다.

```bash
python3 "<skill-root>/evidence/evidence.py" --version
```

갱신하거나 지울 때는 설치 폴더를 먼저 확인하세요. 절차는
[설치](../../docs/users/ko/installation.md)를 보세요.

## 첫 호출

계획 경로를 주 입력으로 전달하고 설계 문서도 함께 적습니다.

```text
$pre-sdd-review docs/history/specs/<design>.md docs/history/plans/<plan>.md
```

실제로는 계획의 `**Spec:**` 필드가 설계 명세를 정합니다. 인자로 쓴 설계 경로는
이 권위를 덮어쓰지 않습니다.

`review-only`는 명시 모드입니다. 첫 판정만 받고 문서를 변경하지 않으려면 아래처럼
부릅니다.

## 결과와 기본 흐름

기본 모드에서는 새 읽기 전용 검토자가 증거 기반 발견을 남깁니다. 제어 에이전트가
해결된 설계 명세와 구현 계획만 고친 뒤, 바뀐 범위만 다시 검토합니다.
`review-only`는 같은 검토를 하지만 아무 파일도 변경하지 않습니다.

```text
$pre-sdd-review review-only docs/history/specs/<design>.md docs/history/plans/<plan>.md
```

구조 변경이 스키마, 타입, 상태 전이, 조건부 수정, 작업 인터페이스, 검증 의미,
데이터 경계에 영향을 주면 직접 소비자와 인접 작업만 포함한 영향 범위를
기록합니다. 문구나 단순 값만 고친 경우에는 만들지 않습니다.

수정 패스는 최대 두 번입니다. 최종 판정은 다음 셋 중 하나입니다.

- `READY`: 남은 문제를 추측하지 않고 구현을 시작할 수 있습니다.
- `REVISE`: 고칠 수 있는 중요한 문서 결함이 남았습니다.
- `BLOCKED`: 필요한 입력·권위·저장소 증거가 없습니다.

한 호출은 발견 1회와 제한된 재검토로 끝납니다. 권위를 보존하는 수정은 승인
없이 적용하고, 제품 결정이 필요할 때만 한 번에 묻습니다. `REVISE`나 `BLOCKED`
뒤에는 자동으로 다시 실행하지 않습니다.

런타임 제거, 스키마 마이그레이션·데이터 삭제, 인증·인가·보안 경계,
public/private 데이터 경계, 게시·과금·메시징·프로덕션 변경 같은 외부 부작용이
있을 때만 두 번째 집중 검토자를 부릅니다. 문서 지문이 바뀌면 다시 검토해야
하며, 문서 밖 Git 변경도 경로·명령·인터페이스·영향 범위 근거를 바꾸면 같은
규칙을 적용합니다. 새 제품 결정이 필요하면 `BLOCKED`입니다.

호환되는 로컬 기록기가 있으면 의미 검토 전 `start`, 최종 판정 뒤 `finish`를
호출하고 `Evidence: recorded; run_id=<run-id>`를 출력합니다. 기록기가 없거나
호환되지 않거나 권한 오류가 나면 검토는 계속되고
`Evidence: not_recorded; reason=<code>`를 출력합니다. 설계 경로는 컨트롤러가
계획의 `**Spec:**`에서 해석한 값을 넘기며, 해석할 수 없으면 생략하고 `BLOCKED`로
끝냅니다. 도중에 끝나면 `abandon`으로 run을 닫습니다.

### Contract

- `primary-input`: `plan-primary`, `spec-resolves-design`
- `plan-cardinality`: `one-plan-per-invocation`, `no-aggregate-ready`
- `editable-surfaces`: `resolved-design-specification`, `resolved-implementation-plan`
- `review-only`: `no-mutation`
- `repair-flow`: `review-repair-bounded-impact-re-review`
- `repair-impact`: `structural-trigger-only`, `direct-consumers`
- `repair-passes`: `at-most-two`
- `verdicts`: `READY`, `REVISE`, `BLOCKED`
- `second-reviewer`: `conditional-only`
- `risk-triggers`: `framework-runtime-removal`, `schema-data-deletion`, `auth-security-boundary`, `data-boundary-change`, `external-side-effects`
- `freshness`: `fingerprints`, `content-change-invalidates`
- `required-base`: `pre-dispatch-ancestor-check`
- `handoff`: `unresolved-packet`
- `sdd`: `outer-request-implementation-only`
- `evidence`: `optional`, `non-blocking`, `controller-local-run-id`

## 안전과 개인정보

검토자는 읽기 전용입니다. 자동 변경 범위는 위 `Contract`의 두 해결된 문서뿐입니다.
승인된 ADR·시각 권위, 애플리케이션 코드, 테스트, 설정, 생성물, 관련 없는 문서는
별도 제품 결정 없이는 변경하지 않습니다.

영수증은 `~/.pre-sdd-review/runs/<run-id>.json`에 로컬로만 남습니다(schema 2).
저장소 상대 경로, 디렉터리 이름, 해시, 열거값, 짧은 paraphrase만 저장합니다.
원문, 절대 경로, prompts, transcripts, credentials는 넣지 마세요. 기록기는
자동 비밀 탐지를 하지 않습니다.

로컬 파일 저장은 악의적인 로컬 변조를 막는 서명된 audit log가 아닙니다.
`outcome` 라벨(`good`, `false-ready`, `noisy`, `abandoned`)은 SDD가 끝난 뒤
사람이나 SDD 워커가 남기는 관찰이며 다시 기록해 정정할 수 있습니다. 라벨은
자기개선용 evidence이지 객관적·감사 등급 증거가 아닙니다.

자세한 내용은 [안전과 개인정보](../../docs/users/ko/safety-and-privacy.md)를 보세요.

## 운영과 한계

명령은 `start`, `finish`, `abandon`, `outcome`, `show`, `summary` 여섯 개입니다.
정확한 인자, stdin 형식, 크기 제한은 [evidence 안내](evidence/README.md)를
따릅니다.

로그는 에이전트가 읽도록 만들어졌습니다. 개선점을 찾을 때는 에이전트에게
`summary`를 실행하게 하고 `anomalies`와 `chains`부터 보게 하세요. 모든 집계에
`run_id`가 붙어 있어 `show --run-id`로 바로 내려갈 수 있습니다. 후보 픽스처
자동 선정, 자동 스킬 변경, client/model ranking은 하지 않습니다.

버전 원본은 `release.toml`이고 `SKILL.md`의 `metadata.version`은 검증된 복제
값입니다. 기록기는 이전 `runs/<연>/<월>/` 영수증을 읽지 않으며, 영수증 삭제는
파일 삭제로 충분합니다.

## 호환성과 검증 수준

pre-sdd-review: Codex supported; other hosts not_measured.

Codex만 독립 읽기 전용 검토와 저장소 조사를 포함해 측정되었습니다. 다른 호스트는
[호환성](../../docs/users/ko/compatibility.md)을 보세요.

제공자 없는 검증은 패키지·지시문·픽스처 계약만 증명하며 실제 모델 검토 품질을
증명하지 않습니다. 선택적 live 검사는 명시적이고 로컬에서만 하며 비용이 들 수
있습니다. 자세한 내용은 [검증](../../docs/users/ko/verification.md)을 보세요.

기록기는 Python 3.11+ 표준 라이브러리만 쓰며 macOS에서 provider-free 테스트로
검증됐습니다. Linux와 native Windows는 각 환경에서 evidence 단계가 직접 실행될
때까지 `not_measured`입니다.

## 변경 이력과 관리자 문서

- [CHANGELOG](CHANGELOG.md)
- [계약](../../docs/maintainers/products/pre-sdd-review/contract.md)
- [테스트](../../docs/maintainers/products/pre-sdd-review/testing.md)
- [호환성](../../docs/maintainers/products/pre-sdd-review/compatibility.md)
- [릴리스](../../docs/maintainers/products/pre-sdd-review/release.md)
