# Pre-SDD Review

[English](README.en.md)

## 이 스킬이 해결하는 문제

승인된 설계와 구현 계획이 서로 맞고 현재 저장소에서 실행 가능한지 SDD 직전에
확인합니다. 기본 흐름은 **검토 → 문서 개선 → 재검토**입니다. 구현자가 빠진 제품
결정을 추측하지 않고도 계획을 실행할 수 있는지가 핵심입니다.

계획 경로가 주 입력입니다. 스킬은 계획의 `**Spec:**` 필드가 가리키는 해결된 설계
명세를 검토합니다. 경로를 해석할 수 없으면 가까운 파일을 추측하지 않고
`BLOCKED`를 반환합니다. 한 번의 호출은 계획 하나만 다루며, 여러 계획을 따로
검토한 결과를 합쳐 `READY`로 간주하지 않습니다.

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

로컬 영수증이 필요할 때만 검사한 스킬 복사본에서 선택적 CLI를 설치합니다.
`--bin-dir`은 이미 `PATH`에 사용하기로 한 기존 디렉터리여야 합니다. 실행 전에
정확한 대상을 확인하고 원격 스크립트를 셸로 파이프하지 마세요.

```bash
ls -ld "$HOME/.local/bin"
python3 skills/pre-sdd-review/evidence/install.py --bin-dir "$HOME/.local/bin"
pre-sdd-review-evidence --version
```

## 첫 호출

계획 경로를 주 입력으로 전달하고 설계 문서도 함께 명시합니다.

```text
$pre-sdd-review docs/history/specs/<design>.md docs/history/plans/<plan>.md
```

실제로는 계획의 `**Spec:**` 필드가 설계 명세를 결정합니다. 인자로 쓴 설계 경로가
이 권위를 덮어쓰지 않습니다.

`review-only`는 명시 모드입니다. 첫 판정만 받고 문서를 변경하지 않으려면 다음과
같이 호출합니다.

## 결과와 기본 흐름

기본 모드에서는 새 읽기 전용 검토자가 증거 기반 발견을 남기고, 제어 에이전트가
해결된 설계 명세와 구현 계획만 고친 뒤 변경 범위를 다시 검토합니다.
`review-only`는 같은 검토를 하지만 아무 파일도 변경하지 않습니다.

```text
$pre-sdd-review review-only docs/history/specs/<design>.md docs/history/plans/<plan>.md
```

구조 변경이 스키마, 타입, 상태 전이, 조건부 수정, 작업 인터페이스, 검증 의미,
데이터 경계에 영향을 주면 직접 소비자와 인접 작업만 포함한 영향 범위를 기록합니다.
문구나 단순 값만 고친 경우에는 만들지 않습니다.

수정 패스는 최대 두 번입니다. 최종 판정은 다음 셋 중 하나입니다.

- `READY`: 남은 문제를 추측하지 않고 구현을 시작할 수 있습니다.
- `REVISE`: 고칠 수 있는 중요한 문서 결함이 남았습니다.
- `BLOCKED`: 필요한 입력·권위·저장소 증거가 없습니다.

한 호출은 발견 1회와 제한된 재검토로 끝납니다. 권위를 보존하는 수정은 승인
없이 적용하고, 제품 결정이 필요할 때만 한 번에 묻습니다. `REVISE`나 `BLOCKED`
뒤에는 자동으로 다시 실행하지 않습니다.

런타임 제거, 스키마 마이그레이션·데이터 삭제, 인증·인가·보안 경계,
public/private 데이터 경계, 게시·과금·메시징·프로덕션 변경 같은 외부 부작용이
있을 때만 두 번째 집중 검토자를 부릅니다. 문서 지문이 바뀌면 다시 검토해야 하며,
문서 밖 Git 변경도 경로·명령·인터페이스·영향 범위 근거를 바꾸면 같은 규칙을
적용합니다. 새 제품 결정이 필요하면 `BLOCKED`입니다.

호환되는 로컬 CLI가 있으면 의미 검토 전 `start`, 최종 판정 뒤
`finish-review`를 호출하고 `Evidence: recorded; run_id=<run-id>`를 출력합니다.
CLI가 없거나 호환되지 않거나 권한 오류가 나면 검토는 계속되고
`Evidence: not_recorded; reason=<code>`를 출력합니다. 명시적으로 결합된 SDD
요청에만 `run_id`를 넘기며 downstream 작업이 terminal 상태일 때만
`record-outcome`을 사용합니다.

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

영수증은 기본적으로 `~/.pre-sdd-review/`에 로컬로 남습니다. bounded reason이나
finding에도 원문, 경로, 프롬프트, transcript, credential을 넣지 말고 짧게 바꿔
쓰세요. 제공자 없는 픽스처에는 사용자 문서나 전체 모델 응답을 저장하지 않습니다.

create-only 저장은 협력하는 로컬 클라이언트에 원자성과 일관성을 제공하지만,
악의적인 로컬 변조를 막는 서명된 audit log는 아닙니다. 구조화한 downstream
observation, assessment basis, confidence는 관찰자가 입력합니다. `good`,
`false-ready`, `noisy`, `prevented-rework` label은 CLI가 그 observation에서
결정적으로 파생합니다. 입력과 label은 자기개선용 evidence이지 객관적·감사 등급
증거가 아닙니다.

`record-outcome` 전에 알려진 모든 이견과 불확실성을 한 번의 구조화한 outcome
입력에 정직하게 담아야 합니다. finding 이견은 `disputed_findings`에 기록합니다.
confidence와 assessment basis는 결정적 label을 바꾸지 않습니다. `inconclusive`는
구조화한 downstream observation이 승인된 파생 fallback에 도달할 때만 나옵니다.
create-only outcome이 기록된 뒤에는 schema 1에서 정정하거나 amend할 수 없습니다.

## 운영과 한계

전체 명령은 `start`, `finish-review`, `abandon`, `show`, `pending`, `doctor`,
`resolve`, `record-outcome`, `summary`, `candidates`, `prune`입니다. 정확한 인자,
크기 제한, 복구·백업·삭제 절차는 [evidence CLI 안내](evidence/README.md)를
따릅니다. `candidates` 임계값은 사람이 볼 후보를 고르는 휴리스틱일 뿐 스킬 자동
변경, 자동 품질 판정, client/model ranking을 허가하지 않습니다.

업데이트나 제거 전에는 정확한 설치 대상을 확인하세요. 버전 원본은
`release.toml`이고 `SKILL.md`의 `metadata.version`은 검증된 복제 값입니다.
launcher 제거는 영수증을 지우지 않습니다. identity를 유지하려면 evidence root
전체를 백업하고, 영수증 삭제는 `prune --dry-run`과 동일 selection의 명시적 확정을
별도 작업으로 수행합니다.

## 호환성과 검증 수준

pre-sdd-review: Codex supported; other hosts not_measured.

Codex만 독립 읽기 전용 검토와 저장소 조사를 포함해 측정되었습니다. 제공자 없는
검증은 패키지·지시문·픽스처 계약만 증명하며 실제 모델 검토 품질을 증명하지
않습니다. 선택적 live 검사는 명시적이고 로컬에서만 하며 비용이 들 수 있습니다.

공유 CLI는 현재 macOS native 경로와 provider-free portable 구성이 검증됐습니다.
Linux와 native Windows는 각 Python 3.11+ 환경에서 직접 실행 증거가 생길 때까지
`not_measured`입니다. 다른 OS의 wrapper 테스트로 native 지원을 추론하지 않습니다.

## 변경 이력과 관리자 문서

- [CHANGELOG](CHANGELOG.md)
- [계약](../../docs/maintainers/products/pre-sdd-review/contract.md)
- [테스트](../../docs/maintainers/products/pre-sdd-review/testing.md)
- [호환성](../../docs/maintainers/products/pre-sdd-review/compatibility.md)
- [릴리스](../../docs/maintainers/products/pre-sdd-review/release.md)
