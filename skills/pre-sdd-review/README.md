# Pre-SDD Review

[English](README.en.md)

## 이 스킬이 해결하는 문제

승인된 설계와 구현 계획이 서로 맞고, 지금 저장소에서 실제로 실행 가능한지
SDD 직전에 검토합니다. 기본 흐름은 **검토 → 문서 개선 → 재검토**입니다.
구현자가 적히지 않은 제품 결정을 만들지 않아도 되는지 확인합니다.

계획 경로가 주 입력입니다. 스킬은 그 계획의 `**Spec:**` 필드에서 해결된 설계 명세
경로를 찾습니다. `**Spec:**` 경로를 해석할 수 없으면 가까운 파일을 추측하지 않고
`BLOCKED`를 반환합니다.

한 번의 호출은 구현 계획 하나만 검토합니다. 여러 계획 중 어느 것인지 분명하지
않으면 `BLOCKED`입니다. 계획을 나눠 여러 번 호출해도 전체를 묶은 `READY`는 내지
않습니다.

## 사용해야 할 때와 사용하지 말아야 할 때

승인된 설계 명세와 구현 계획이 이미 있고, SDD 또는 계획 실행 전에 두 문서와
저장소 현실을 대조해야 할 때 씁니다.

처음 설계나 계획을 작성할 때, 구현 코드·PR을 검토할 때, 출시 준비를 할 때,
교정하거나 일반 문서를 고칠 때는 쓰지 않습니다. 이 스킬은 외부 요청에
구현이 포함되지 않으면 SDD를 시작하지 않습니다.

## 1분 설치와 첫 호출

Codex는 공개 GitHub 경로를 가리키는 `$skill-installer`로 설치할 수 있습니다.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/pre-sdd-review
```

로컬 영수증을 남기려면 검사한 스킬 복사본에서 선택적 CLI를 별도로 설치합니다.
`--bin-dir`은 이미 `PATH`에 쓰기로 한 기존 디렉터리여야 하며, 실행 전 정확한
대상을 `ls -ld`로 확인합니다. 원격 스크립트를 셸로 파이프하지 마세요.

```bash
ls -ld "$HOME/.local/bin"
python3 skills/pre-sdd-review/evidence/install.py --bin-dir "$HOME/.local/bin"
pre-sdd-review-evidence --version
```

Codex, Claude Code, Cursor, Grok은 사용 가능할 때 모두 같은
`pre-sdd-review-evidence` 명령을 호출합니다. CLI 이식성과 의미 검토 호스트
지원은 별도 계약입니다.

첫 호출에서는 계획 경로를 주 입력으로 삼고 설계 경로도 명시합니다.

```text
$pre-sdd-review docs/history/specs/<design>.md docs/history/plans/<plan>.md
```

`review-only`는 명시 모드입니다. 변경 없이 첫 판정만 원할 때는 주요 흐름의
`review-only` 호출을 사용합니다.

실제 해석에서는 계획 경로가 primary이고, 그 계획의 `**Spec:**` 필드가 가리키는
해결된 설계 명세를 검토합니다. 인자로 쓴 설계 경로가 그 결정을 바꾸지 않습니다.

## 주요 흐름

기본 호출은 한 명의 새 읽기 전용 검토자가 증거 기반 발견을 내고, 제어 에이전트가
해결된 설계 명세와 해결된 구현 계획만 고친 뒤 범위를 좁혀 다시 검토합니다. 기본
호출은 이 두 문서만 변경합니다. `review-only`는 같은 검토를 하지만 아무 파일도
변경하지 않습니다.

문서 수리가 스키마, 타입, 상태 전이, 조건부 수정, 작업 인터페이스, 검증 의미,
데이터 경계를 바꾸면 직접 쓰는 쪽과 이웃 작업만 적은 영향 범위 표를 만듭니다.
새 검토자는 기존 발견이 닫혔는지와 이 범위만 다시 확인합니다. 문구·값만 고친
경우에는 이 표를 만들지 않습니다.

수정 패스는 최대 두 번입니다. 최종 판정은 다음 중 하나입니다.

- `READY`: 기록된 증거로 구현을 시작할 수 있습니다.
- `REVISE`: 고칠 수 있는 중요한 문서 결함이 남았습니다.
- `BLOCKED`: 필요한 입력·권위·저장소 증거가 없어 안전하게 결정할 수 없습니다.

런타임/프레임워크 제거, 스키마 마이그레이션 또는 데이터 삭제, 인증·인가·보안
경계, public/private 데이터 경계, 게시·과금·메시징·프로덕션 변경 같은 외부 부작용이
있을 때만 두 번째 집중 검토자를 부릅니다. 설계나 계획 내용이 바뀌면 문서 지문이
무효화되어 다시 검토해야 합니다. 문서 밖 Git 변경도 경로·명령·인터페이스·영향 범위
근거를 바꾸면 다시 검토합니다.

`REVISE`와 `BLOCKED`는 남은 문제와 다음에 볼 범위를 짧게 남깁니다. 새 제품 결정이
필요하면 `BLOCKED`입니다.

호환되는 로컬 CLI가 있으면 의미 검토 전에 `start`, 최종 판정 뒤에
`finish-review`를 호출하고 `Evidence: recorded; run_id=<run-id>`를 한 줄
출력합니다. 사용할 수 없거나 호환되지 않거나 권한 오류가 나면 판정은 그대로
진행하고 `Evidence: not_recorded; reason=<code>`를 출력합니다. 명시적으로 결합된
SDD 요청에만 로컬 `run_id`를 넘기며, downstream 작업이 terminal 상태일 때만
`record-outcome`을 씁니다. 같은 evidence 흐름은 기본 모드와 `review-only`에 모두
적용됩니다.

전체 로컬 명령은 `start`, `finish-review`, `abandon`, `show`, `pending`, `doctor`,
`resolve`, `record-outcome`, `summary`, `candidates`, `prune`입니다. 정확한 인자는
각 `--help`와 [evidence CLI 안내](evidence/README.md)를 따릅니다.

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
- `handoff`: `unresolved-packet`
- `sdd`: `outer-request-implementation-only`
- `evidence`: `optional`, `non-blocking`, `controller-local-run-id`

`review-only`는 명시 모드이며 아무 파일도 변경하지 않습니다.

```text
$pre-sdd-review review-only docs/history/specs/<design>.md docs/history/plans/<plan>.md
```

## 안전과 개인정보

검토자는 읽기 전용입니다. 자동 변경의 권한 경계는 주요 흐름의 `Contract` 목록이
유일한 기준입니다. 승인된 ADR, 승인된 시각 권위, 애플리케이션 코드, 테스트, 설정,
생성물, 관련 없는 문서는 별도 제품 결정을 요구합니다. 승인된 제품 의도를 바꾸어야 하면
`BLOCKED`로 남깁니다.

제공자 없는 픽스처에는 사용자 문서나 전체 모델 응답을 저장하지 않습니다. 개인정보,
비공개 프롬프트, 공급자 트랜스크립트를 커밋하지 마세요.

영수증은 `~/.pre-sdd-review/`에 로컬로 남고, 비어 있지 않은 절대 경로
`PRE_SDD_REVIEW_HOME`만 대체 위치로 쓸 수 있습니다. `review.json`은 16 KiB
soft/32 KiB hard, `outcome.json`은 4 KiB soft/8 KiB hard, 완료 run은 40 KiB
hard limit입니다. bounded reason이나 finding에도 원문, 경로, 프롬프트,
transcript, credential을 넣지 말고 짧게 바꿔 쓰세요.

create-only 저장은 협력하는 로컬 클라이언트의 원자성과 일관성을 제공하지만,
악의적인 로컬 변조를 막는 서명된 audit log는 아닙니다. `good`, `false-ready`,
`noisy`, `prevented-rework`, confidence는 관찰자가 입력한 자기개선용 evidence이며
객관적·감사 등급 증거가 아닙니다. schema 1은 outcome 정정이나 amendment를
지원하지 않습니다. 잘못 입력했다면 덮어쓰지 말고 finding은
`disputed_findings`, 불확실한 평가는 `inconclusive` 경계를 사용하세요.
`candidates` 임계값은 사람이 볼 후보를 고르는 휴리스틱이며 스킬 자동 변경,
자동 품질 판정, client/model ranking을 허가하지 않습니다.

## 호환성과 검증 수준

pre-sdd-review: Codex supported; other hosts not_measured.

Codex만 독립 읽기 전용 검토와 저장소 조사를 포함해 측정되었습니다. 제공자 없는
계약 검증은 패키지·지시문·픽스처 경계만 증명하며, 실제 모델 검토 품질이나 다른 호스트의
동등한 런타임을 증명하지 않습니다. 선택적 라이브 검사는 명시적이고 로컬에서만 하며
비용이 들 수 있고 CI가 요구하지 않습니다.

공유 CLI는 macOS의 현재 native 경로와 provider-free portable 경계만 검증됐습니다.
Linux와 native Windows 실행은 해당 Python 3.11 환경에서 실제 evidence 및 installer
단계가 통과하기 전까지 `not_measured`이며, 다른 OS에서 만든 Windows wrapper 테스트로
지원을 추론하지 않습니다.

## 갱신과 버전 확인

업데이트나 제거 전에는 설치 대상이 정확히 이 스킬인지 확인하세요. 현재 버전 원본은
`release.toml`이고, 검증된 복제 값은 `SKILL.md`의 `metadata.version`입니다.
상위 `skills` 디렉터리나 홈 디렉터리를 삭제하지 마세요.

CLI launcher를 제거하기 전에는 `command -v pre-sdd-review-evidence`와 정확한
파일을 확인하세요. launcher 제거는 영수증을 지우지 않습니다. 저장소 identity를
유지하려면 `identity.key`와 `config.json`을 포함한 evidence root 전체를 백업합니다.
영수증 삭제는 `prune --dry-run` 결과를 확인하고 같은 selection을 명시적으로
확정하는 별도 작업입니다.

## 변경 이력과 관리자 문서

- [CHANGELOG](CHANGELOG.md)
- [계약](../../docs/maintainers/products/pre-sdd-review/contract.md)
- [테스트](../../docs/maintainers/products/pre-sdd-review/testing.md)
- [호환성](../../docs/maintainers/products/pre-sdd-review/compatibility.md)
- [릴리스](../../docs/maintainers/products/pre-sdd-review/release.md)
