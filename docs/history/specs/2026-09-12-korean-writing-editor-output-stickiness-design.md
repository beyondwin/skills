# korean-writing-editor 출력 고정과 near-miss 설계

날짜: 2026-09-12
대상 제품: `skills/korean-writing-editor` (현재 2.0.3)
목표 버전: 2.0.4 (PATCH)

## 문제

2.0.3의 오프라인 계약은 통과한다. 2026-09-12 Cursor `auto` 프로브에서 실제
응답은 명시 `correct`/`polish`에서만 출력 계약을 지켰다. 암묵 호출과
`diagnose`, 제외 과제에서는 같은 모델이 계약을 깼다.

관측 (throwaway, runner 18 영수증 아님):

| 요청 | 관측 | 깨진 계약 |
| --- | --- | --- |
| 명시 `/…` + 오탈자 (`사용할수`) | `이 기능은 사용할 수 있지만 반드시 켤 필요는 없습니다.` | 없음 |
| 명시 `/…` + `반영을 해서` | `…반영해서 초안을 다시 정리했습니다.` | 없음 |
| 명시 `/…` + 이미 자연한 문장 | 원문 그대로 | 없음 |
| 암묵 `다듬어줘` + `반영을 해서` | 영문 서문 + 같은 교정 | 출력은 편집문만 |
| 암묵 `다듬어줘` + `출시하지 않을 수 있다` | 서문 + `출시하지 않을 수도 있다` | 이미 맞는 국소 표현 보존 |
| 명시 `diagnose` | 띄어쓰기는 짚음, 앞에 `Using … diagnose mode` | 소견만, 과정 서술 금지 |
| 명시 번역 near-miss | 편집기는 거절한 뒤 영어로 번역 | 제외 과제를 같은 턴에 수행하지 않음 |

금지 문장(“과정 서술을 붙이지 마라”)은 이미 `SKILL.md`에 있다. 라이브에서
모델은 그 금지를 협상하고 서문을 붙인다. 오프라인 33개에는 `expected_mode:
diagnose` 케이스가 없고, 영문 `Using the … skill` 서문 변이도 없다.

## 제약

- 모드는 `diagnose`, `correct`, `polish` 그대로다. 새 모드를 만들지 않는다.
- `supported_hosts`는 `["codex"]` 그대로다. Cursor 프로브는 기록된 smoke가
  아니므로 호스트 지원을 넓히지 않는다.
- 라이브 하니스(`live_matrix.py` argv, `--trust`, 122회 `--execute`)는 이
  릴리스 범위가 아니다.
- 사용자 한국어 원문, 공급자 응답, 자격 증명을 픽스처나 커밋에 넣지 않는다.
  새 오프라인 케이스는 기존 합성 문장만 쓴다.
- 금지 목록을 늘려 출력을 고치지 않는다. 출력 **레시피**(답이 무엇인지)로
  고친다.
- `SKILL.md`에 공급자 모델 이름을 두지 않는다.
- 비공식 맞춤법 API, 형태소 분석기, 외부 검색을 추가하지 않는다.

## 설계

### 출력 레시피

`SKILL.md` `## Output Contract`를 금지 나열이 아니라 양성 레시피로 교체한다.
기존 표제 `## Output Contract`는 유지한다.

`correct`와 `polish`:

- 응답은 편집된 한국어 본문(또는 고칠 것이 없으면 원문) **그 자체**다.
- 첫 비공백 문자는 그 본문에 속한다.
- 모드 이름, 스킬 이름, “Using … skill”, “한국어 교정 스킬을 확인한 뒤” 같은
  과정 서술을 앞뒤에 두지 않는다.

`diagnose`:

- 응답은 소견이다.
- 첫 줄은 문제, 결정 등급, 또는 hold를 가리킨다.
- 모드를 다시 말하지 않고, 다시 쓴 초안을 붙이지 않는다.

루브릭, 변경 로그, 점수, 라우팅 영수증은 계속 금지다. 실질 hold에만 짧은
`확인 필요` 주를 단다. 왜 물음에 대한 네 항목 목록은 유지한다.

`## Default Interaction`의 “default reply is the edited text only”는 레시피와
중복되므로 레시피를 가리키는 한 줄로 줄인다. 장르·청중 질문 규칙과 원문
비저장 규칙은 남긴다.

### 이미 맞는 국소 표현

`## Preservation Gate`의 “replace an already standard, grammatical local
expression with a synonym in `correct`”를 `correct`와 `polish` 모두에
적용한다. `polish`의 선택 윤문은 어색한 국소 흐름만 다룬다. 이미 문법적인
가능성·의무·부정 구를 가까운 동의어로 바꾸지 않는다.

규범 예: `출시하지 않을 수 있다`를 `출시하지 않을 수도 있다`로 바꾸지 않는다.
`수 있다`는 이미 맞는 가능성 구이고, `수도 있다`는 다른 명제다.

`## Editing Pass` 6단계는 이미 “synonym replacement of an already-correct
local form”을 되돌리라고 하므로 그 문장은 유지한다. Gate 문장만 `correct`에
한정하지 않게 고친다.

### Near-miss no-op

제외 near-miss에서 편집 워크플로를 시작하지 않는 규칙은 유지한다. 빈 구멍을
막는다: **같은 턴에서 그 제외 과제를 대신 수행하지 않는다.**

handoff는 “이 편집기는 적용하지 않는다”고 말할 수 있다. 그 응답에서 번역,
초안, 요약, 코드 리뷰, 저자 판별, 이름 있는 작가 흉내를 하지 않는다.

`## Refuse Or Hold`의 “Excluded near miss” 행을 이 문장과 맞춘다.
`## Activation Gate`의 “do not start an editing workflow” 뒤에 같은 경계를
한 줄로 둔다.

### 호출 안내

제품 `README.md` / `README.en.md` 첫 호출은 기본 모드 `polish`를 보여 준다.
오탈자만 고치는 `correct`는 두 번째 예시다.

호출 접두는 이식 가능한 표기로 `$korean-writing-editor`와
`/korean-writing-editor`를 함께 적는다. 측정된 호스트는 Codex라는 기존
문장을 바꾸지 않는다. Cursor를 지원 호스트로 적지 않는다.

### 오프라인 증거

카테고리 집합 `{normative, preservation, noop, voice, trigger}`는 유지한다.
케이스는 33에서 34로 늘린다. 새 케이스는 `trigger`에 둔다
(`trigger=6`).

새 통과 케이스 `trigger-diagnose-06`:

- 요청: `고치지 말고 어색한 부분만 알려줘: 지금 상태에선 배포할수 있다.`
- `expected_mode`: `diagnose`
- `expected_trigger`: true
- `expected_noop`: false (소견은 원문과 다른 문자열이다)
- `required_substrings`: `배포할수`
- `forbidden_substrings`: 다시 쓴 문장 `지금 상태에선 배포할 수 있다.`,
  `Using the`, `Using korean-writing-editor`, `한국어 교정 스킬`
- 후보는 띄어쓰기 문제를 가리키는 짧은 소견이며 다시 쓴 초안이 아니다.

기존 통과 케이스의 `candidate` 본문은 바꾸지 않는다. 서문 변이가 실패하려면
`evaluate_candidate`가 `forbidden_substrings`를 봐야 하므로,
`norm-spacing-can-01`의 금지 바늘에 `Using the`와 `한국어 교정 스킬`을 더하는
것은 허용한다. 기존 `요청은 오탈자` 바늘과 같은 방식이다. 아래 변이는
`evaluate_candidate`가 오류를 내야 한다.

| 원 케이스 | 변이 | 잡아야 할 구멍 |
| --- | --- | --- |
| `norm-spacing-can-01` | 영문 서문 `Using the Korean writing editor skill to correct typos.`를 본문 앞에 붙임 | 출력 레시피 |
| `norm-spacing-can-01` | 한글 서문 `한국어 교정 스킬을 확인한 뒤 오탈자만 고치겠습니다.`를 본문 앞에 붙임 | 암묵 호출 서문 |
| `meaning-negation-01` | `출시하지 않을 수 있다` → `출시하지 않을 수도 있다` | polish 동의어 |
| `trigger-translation-03` | 거절 문장 뒤에 `There is a meeting tomorrow morning.`를 붙임 | near-miss가 번역을 대신 수행 |

기존 `요청은 오탈자` 서문 변이와 부정 반전 변이는 유지한다.

스킬 트리 검사에 정착 문자열을 더한다. `SKILL.md`에 `first non-whitespace`,
`excluded task`, 그리고 동의어 게이트 문구 `correct` or `polish`가 있어야
한다. 이 검사가 없으면 레시피나 polish 동의어 문장을 빼도 오프라인이
통과한다.

### 함께 고칠 계약 파일

34개와 `trigger=6`을 잠그는 파일:

- `tests/products/korean-writing-editor/offline/run.py`
  (`EXPECTED_CATEGORY_COUNTS`, 요약 출력)
- `tests/products/korean-writing-editor/test_package.py` (`EXPECTED_SUMMARY`, `len(payload["cases"]) == 34`)
- `docs/maintainers/products/korean-writing-editor/testing.md`
- `docs/maintainers/products/korean-writing-editor/release.md`
- `docs/maintainers/products/korean-writing-editor/contract.md` (출력·near-miss·동의어)
- `docs/users/ko/verification.md`, `docs/users/en/verification.md` (`33` → `34`)
- `tests/repository/test_public_docs.py`는 `verification.md`의 `34`를 읽는다.
  구문 `33`만 `34`로 바꾼다. `normative=10`은 유지한다.

버전 2.0.4를 잠그는 파일:

- `skills/korean-writing-editor/release.toml`
- `skills/korean-writing-editor/SKILL.md` `metadata.version`과 `updated_at`
- `skills/korean-writing-editor/CHANGELOG.md`
- `tests/repository/test_release_contract.py` `EXPECTED["korean-writing-editor"]`
- `tests/products/korean-writing-editor/test_package.py`의 2.0.3 단언

`editorial-guide.md` Compact Examples에 출력 레시피, `수 있다` 보존,
near-miss가 번역하지 않는 예를 하나씩 추가한다.

## 바뀌지 않는 것

- 모드 집합, tier 집합, 활성화 게이트의 긍정·암묵 조건, `kws-` no-op
- `products.toml`의 `supported_hosts`, `verify_stages`, owned paths
- 라이브 14 cases / 17 repeats, 예산 119 / 3 / 122 / 38 / 160
- runner 18 스키마, 라이브 합성 케이스 본문
- `references/sources.md` 권위 출처
- catalog lock, archive manifest, 설치 블록
- 공유 지원 문장 `korean-writing-editor: Codex supported; Agent Skills contract portable; other hosts only supported after a recorded smoke.`

## 검증

공급자 없는 증거:

```bash
python3 scripts/verify.py --skill korean-writing-editor
python3 scripts/verify.py
```

통과 조건:

- 오프라인 요약이 `34 cases: normative=10 preservation=8 noop=6 voice=4 trigger=6`
- `mutation checks: PASS` (새 서문·동의어·번역 변이 포함)
- `skill tree (full): PASS` (`first non-whitespace`, `excluded task`,
  `correct` or `polish` 포함)
- 제품 패키지·릴리스 계약이 2.0.4
- 사용자 `verification.md`가 `34`와 `normative=10`을 포함

오프라인 통과는 라이브 품질을 증명하지 않는다. 이 릴리스는 새 runner 18
`--execute`를 요구하지 않는다.

## 위험

- 출력 레시피는 결정적 픽스처로만 잠긴다. 모델이 서문을 붙이는지는 라이브
  없이 증명하지 못한다. 이 한계를 CHANGELOG Notes와 testing.md에 적는다.
- `first non-whitespace` 문자열 검사는 레시피 문장이 있는지만 본다. 모델
  준수를 보지 않는다.
- 케이스 수를 34로 올리면 사용자 검증 안내와 `test_public_docs.py`가 함께
  바뀌지 않으면 저장소 계약이 실패한다. 구현 계획은 그 파일들을 한 작업에
  묶는다.
- diagnose 후보가 원문과 다르므로 `expected_noop`는 false다. true로 두면
  오프라인이 즉시 실패한다.
