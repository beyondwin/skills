# how-it-works 첫 화면 그림과 게이트 제거 설계

**Status:** Draft for review. Approved in conversation on 2026-09-12: approach B,
interaction section, 그림 quality section, SemVer 3.0.0, live quality out of
scope.

**Scope:** 기존 제품 `how-it-works`의 설명 전 깊이 질문과 그림 레시피. 첫 답의
기본 칸을 **그림**으로 바꾸고, 같은 턴에서 설명한다. 필수 여섯 산출과
`/eli5` near-miss는 유지한다.

**Out of scope:** `/eli5` 활성화, 어린이 말투·동물·`여러분`/`답니다`, 호스트
지원 확대, 라이브 모델 호출·schema 2 기록 작성, `catalog/`, 태그·GitHub
Release, `korean-writing-editor` 호출.

이 파일은 진행 중인 설계이다. 현재 계약을 정의하지 않는다. 산 계약은 구현 후
제품 README와 `docs/maintainers/products/how-it-works/`에 있다.

## Context

현재 페이로드는 `2.0.1`이다. 설명 전에 `slice`, `type`, `rung`, `language`를
채운다. 픽커는 **길**을 `(default)`로 적어 놓고, 같은 파일에서 깊이를 조용히
고르지 말라고 막는다. 그래서 `/how-it-works DNS`, `/how-it-works DNS 흐름`,
`감이 안 와, HTTP가 어떻게 돌아가`는 닫힌 깊이 질문 한 턴을 쓴다. 픽스처
`missing-rung`이 그 대기를 잠근다.

출력은 한 줄, 머메이드 소스, 번호 홉, 본문, 옆 슬라이스, 다음 이동 여섯
가지다. 지도 절은 머메이드가 홉보다 앞이다. Codex와 Claude Code 터미널은
머메이드를 그림이 아니라 소스 펜스로 보여 준다. 라이브 품질은
`not_measured`이다. 사용자 보고는 쓰기가 ELI5보다 번거롭고, 나온 답이
ELI5보다 아쉽다는 것이다.

정체성은 유지한다: 같은 기계, 고른 칸, 그림이 거짓이 되지 않음, 나이를 내리지
않음. ELI5는 다른 스킬이다.

승인된 제품 결정:

- 기본 칸은 그림이다. 명시한 칸·별칭·전문어 기본(rebase/TTL/Raft → 뼈대)은
  그대로 이긴다.
- 깊이가 비면 묻지 않는다. intent 한 줄로 그림이라고 알리고 같은 턴에서
  설명한다.
- 필수 여섯 산출은 유지한다. 그림 지도는 홉을 머메이드보다 앞에 둔다.
- 라이브 호출은 이 작업에서 하지 않는다. CHANGELOG는 품질 측정을 주장하지
  않는다.

## Goals

1. 잘린 기계 이름만 있으면 한 턴에 그림 설명이 끝난다.
2. 첫 화면은 훅 → 참인 한 줄 → 번호 홉 → 머메이드 → 재진술 없는 본문 →
   한계 → 다음 칸(길)이다.
3. `/eli5`, 디버그·구현, 문명 명사 자르기, 고위험 멈춤은 지금과 같다.
4. 오프라인 계약이 새 게이트와 그림 레시피를 잠근다. 라이브 품질은
   `not_measured`로 남는다.

## Non-goals

- `/eli5`나 “explain like I’m 5”로 이 스킬을 활성화하지 않는다.
- 그림에서 머메이드나 옆 슬라이스를 빼지 않는다.
- 기본 칸을 길로 남겨 두지 않는다.
- Grok·Cursor 지원을 이 변경으로 주장하거나 삭제하지 않는다.
- 오프라인 통과를 모델 품질·해요체 준수·Mermaid 렌더 증거로 확대하지 않는다.
- 라이브 schema 2 기록을 만들지 않는다. 보존된 schema 1
  `live/smoke-record.json` 바이트는 그대로다.

## Decisions

### 1. 버전

| 필드 | 값 |
| --- | --- |
| 현재 | `2.0.1` |
| 목표 | `3.0.0` (MAJOR) |
| `updated_at` | 구현일의 `YYYY-MM-DD` |
| 지원 호스트 | `codex`, `claude-code` 유지 |

MAJOR인 이유: 기본 칸이 길→그림이고, 필수 입력 `rung`이 더 이상 설명을 막지
않는다. `release.md` 예시(“기본 칸을 바꾸는 변경”)와
`versioning.md`(기본 모드·필수 입력)에 해당한다.

이 스펙과 이후 구현 계획만으로 태그나 GitHub Release를 만들지 않는다.

### 2. 상호작용

HARD-GATE는 잘못된 스킬, 문명 덩어리, 고위험 멈춤, 빠진 크롬을 막는다.
**깊이가 비었다는 이유로 설명을 막지 않는다.**

런타임:

```text
request
  -> 스킬이 맞나 (디버그/구현/리뷰/번역/한 줄 조회/eli5면 활성화하지 않음)
  -> slice가 문명 덩어리면 자르기만
  -> type·language는 추론
  -> rung은 아래 우선순위로 채움
  -> intent 한 줄로 고른 칸을 알림
  -> 같은 턴에서 설명
  -> 다음 이동 하나 (그림의 기본 다음은 길)
```

깊이 우선순위 (앞이 이김):

1. 명시한 칸 — 그림/길/뼈대/허점, picture/path/skeleton/fracture
2. 명시한 별칭 — `쉽게`/`한눈에`/`한 장`/`감이 안 와` → 그림; `따라가` → 길;
   `내부`/`실무`/`속` → 뼈대; `한계`/`깊게`/`예외`/`반례` → 허점; 명시 숫자
   깊이 `5`/`10`/`15`/`20`
3. 전문어 기본 — `rebase`/`TTL`/`Raft`이고 칸·별칭이 없으면 **뼈대**
4. **기본 그림** — 묻지 않음. intent에 **그림**이라고 씀

`Do not silently pick a depth`와 우선순위 끝의 `one necessary question`은
폐기한다. 남는 금지: **이미 채운 칸을 덮지 않는다.** 고른 칸은 intent에
밝힌다. `Type inference does not fill rung`은 유지한다. `흐름`은 유형이지
길이 아니다.

경로:

| 경로 | 언제 | 하는 일 |
| --- | --- | --- |
| 바로 | slice가 잘린 기계 | 우선순위로 칸을 채우고 같은 턴에 설명 |
| 하나 | slice가 없거나 칸이 서로 충돌하거나 KO/EN 혼용이 출력을 바꿈 | 닫힌 질문 하나 |
| 자르기 | 인터넷/AI/자본주의처럼 문명 명사 | 조각 셋 + Other. 설명 없음 |

고위험(의료·법률·금융)과 뜻밖의 슬라이스는 지금처럼 멈추고 `stakes.md`를
읽는다. 기본 그림으로 설명하는 일반 주제는 고개를 끄덕일 때까지 기다리지
않는다.

한 턴이 되는 예: `/how-it-works DNS`, `/how-it-works DNS 흐름`, `감이 안 와,
HTTP가 어떻게 돌아가`. 명시 칸이 이기는 예: `DNS 길` → 길, `Raft 원리부터` →
뼈대, `rebase 쉽게` → 그림. 다턴이 남는 예: `/how-it-works 인터넷`(자르기),
주제 없는 `쉽게 설명해줘`(slice 질문).

### 3. 그림 출력

필수 여섯 가지는 모든 칸에서 유지한다. 그림에서만 지도 절 순서를 바꾼다.

```markdown
# {slice} · 그림

## 한 줄

## 지도

1. **H1** — {무엇이 움직이거나 바뀌는지}
2. **H2** — {무엇이 움직이거나 바뀌는지}

```mermaid
{diagram source}
```

## 본문

## 지금 다루지 않은 것

다음: 길 — {홉 ID가 누구를 어떤 순서로 묻는지}
```

그림 레시피:

- **한 줄**은 훅과 주장을 겸한다. 산 현상 한 호흡 뒤에, 허점에서도 참인 관절
  하나. 설명 안 된 원인을 상자 수보다 적게 둔다.
- **홉이 사람 지도**다. 4–6개. 각 줄은 움직임 하나. 라벨은 동사와 한 번
  gloss한 손잡이. 머메이드 노드 문구는 그 홉과 같다.
- **머메이드**는 같은 절의 뒤, 같은 홉 ID. 렌더러는 필수가 아니다. 소스를
  빼지 않는다.
- **본문**은 홉을 다시 걷지 않는다. 정체·쓰임, 선택 비유 하나. 비유는 경로를
  보여 준 뒤에만. 깨지는 지점은 그 비유를 한 번 쓴 다음이다. 비유 없으면
  깨지는 지점 절을 만들지 않는다.
- **지금 다루지 않은 것**은 이 그림이 비운 것 한 줄과 옆 이름 2–3개. 두 번째
  에세이가 아니다.
- **다음**은 기본이 길이고 홉 ID를 가리킨다.

길·뼈대·허점은 지금 오버레이를 유지한다. 허점은 기준 머메이드와 번호 홉을
지도에 남기고 실패 표를 본문에 둔다. 홉 ID는 칸이 바뀌어도 같다. 허점을 세
문장으로 줄이면 그림과 같은 영화여야 한다. 나중 칸이 “그림이 틀렸다”고 하지
않는다.

한국어 양성 목소리 (`korean.md`): 해요체, 원인 동사(묻다, 맡기다, 적어 두다,
만료되다), 한 번 gloss. 금지 유지: `여러분`, `당신`, `우리`, `답니다`,
동물, `쉽게 말하면`, `즉`, `다시 말해`, `이제 설명해볼게요`. 그림 금지 예
(전화번호부 + `여러분이` + `답니다`)는 그대로 둔다. 그림 목표는 조회 + 가까운
기억 + 만료가 같은 영화에 있게 고친다. 옛 금지 문자열 `컴퓨터는 숫자 주소를
본다`를 되살리지 않는다.

유형 레시피: 그림의 **흐름** 본문은 홉을 다시 걷지 않는다. 정체·쓰임만. 길의
흐름은 지금처럼 시퀀스를 걷는다.

### 4. 안전과 트리거

유지:

- description의 `ELI5` 제외 문구, `/eli5` 문자열 없음, `near-miss-eli5`
- 디버그·구현·리뷰·번역·한 줄 조회 near-miss
- 문명 명사 자르기 (`broad-slice`)
- 고위험 배너 바이트 (`stakes.md`)
- 가져온 URL만 검증함, 법령·논문 ID 만들지 않음
- `korean-writing-editor` 비호출
- 사용자 주제를 픽스처로 저장하지 않음

Dump gate에서 “설명해줘 → 한 질문”은 폐기한다. 잘못된 슬라이스·문명 명사·칸
충돌만 질문이다. Red flag “칸이 비었는데 같은 턴에 에세이”는 **slice가 없을
때**로 좁힌다.

### 5. 오프라인 증거

필수 증거는 계속 `python3 scripts/verify.py --skill how-it-works`와 전체
`python3 scripts/verify.py`다. 라이브 호출은 이 릴리스의 완료 조건이 아니다.

`cases.json`:

- `missing-rung` id는 유지한다. prompt는 `/how-it-works DNS 흐름` 그대로.
  `must`는 그림 설명의 여섯 산출(`claim`, `mermaid`, `numbered_hops`, `body`,
  `adjacent_slices`, `next_move`)과 그림 칸(`picture_default`). `forbidden`은
  `one_closed_question`, `skeleton_default`. `silent_rung` 금지는 이 행에서
  뺀다. 알리지 않은 기본은 여전히 실패다. intent에 그림을 밝히는 것은 실패가
  아니다.
- 새 행 `default-dns-picture`: prompt `/how-it-works DNS`. `must`는
  `picture_default`와 여섯 산출. `forbidden`은 `one_closed_question`,
  `skeleton_default`.
- `broad-slice`, `near-miss-eli5`, `near-miss-debug`, `jargon-rung`,
  `jargon-without-depth`, `explicit-dns-path`(명시 길), 고위험 행은 기대값을
  유지한다.

`test_contract.py`가 잠글 문자열 교체:

- 우선순위 끝: `one necessary question` → `default 그림`
- `Do not silently pick a depth` 삭제. `Never replace a filled rung`과
  intent 알림을 잠근다.
- `OUTPUT_CHROME` 지도 절: 번호 홉, 그다음 머메이드 펜스.
- `CASE_IDS`에 `default-dns-picture` 추가. `HOW_IT_WORKS_FIXTURE_IDS`에도
  같은 id를 넣는다.
- 버전 핀 `2.0.1` → `3.0.0` (`test_contract.py`,
  `tests/repository/test_release_contract.py`).

`testing.md`: `missing-rung` 설명을 “DNS 흐름은 유형만 채우고 기본 그림으로
같은 턴에 설명한다”로 바꾼다. 페이로드 통과가 라이브 품질이 아님을 유지한다.

라이브 디렉터리: `live/cases.json`의 세 합성 프롬프트, schema 1
`smoke-record.json` 바이트, `LIVE_CASE_IDS` 세 개는 유지한다. 새 그림
프롬프트를 라이브 케이스에 넣지 않는다. `meaning`은 `not_measured`로 둔다.

### 6. 함께 고칠 파일

페이로드:

- `skills/how-it-works/SKILL.md` — HARD-GATE, 경로, 우선순위, dump gate, red
  flags, Runtime, `metadata.version` `3.0.0`
- `skills/how-it-works/references/output.md` — 지도 절 순서, 그림 본문 레시피,
  흐름 유형의 그림 행
- `skills/how-it-works/references/visuals.md` — 그림에서 홉이 사람 지도,
  머메이드는 같은 절의 뒤
- `skills/how-it-works/references/korean.md` — 양성 목소리, 그림 목표 문장
- `skills/how-it-works/README.md`, `README.en.md` — 첫 호출 예에 `$how-it-works
  DNS` / `/how-it-works DNS` (그림). 기존 `DNS 길` 예는 명시 칸 예로 남긴다.
  설치 파이썬 블록 바이트는 건드리지 않는다.
- `skills/how-it-works/CHANGELOG.md` — `3.0.0` Breaking: 기본 칸 그림, 깊이
  질문 제거. Notes: 라이브 품질 `not_measured`.
- `skills/how-it-works/release.toml` — `3.0.0`

계약·테스트:

- `docs/maintainers/products/how-it-works/{contract,testing,release}.md`
- `tests/products/how-it-works/cases.json`
- `tests/products/how-it-works/test_contract.py`
- `tests/repository/test_release_contract.py`
- `tests/repository/test_public_docs.py` (`HOW_IT_WORKS_FIXTURE_IDS`, 필요하면
  첫 호출 예 문구)

만지지 않는 것: `catalog/**`, `live/smoke-record.json`, 다른 제품 `SKILL.md`,
설치 링커 파이썬 펜스, `products.toml` 호스트 목록, `stakes.md` 배너 바이트.

## 바뀌지 않는 것

- 여섯 산출 집합, 홉 ID 안정, 허점 지도 유지
- `/eli5` no-op, 어린이 말투 금지
- 자르기, 고위험 배너, 출처 정책
- Codex·Claude Code 지원 문장, Grok 과거 실패를 현재 증거로 승격하지 않음
- 라이브 세 합성 프롬프트와 schema 1 기록

## Verification

공급자 없는 완료 조건:

```bash
python3 scripts/verify.py --skill how-it-works
python3 scripts/verify.py
git diff --check
```

통과 조건:

- `release.toml`과 `metadata.version`이 `3.0.0`
- `missing-rung`과 `default-dns-picture`가 그림 설명이지 깊이 질문이 아님
- `near-miss-eli5`와 `broad-slice`가 지금과 같음
- `jargon-without-depth`가 뼈대
- `explicit-dns-path`가 길
- 그림 지도 크롬이 홉 다음 머메이드
- CHANGELOG `3.0.0`이 기본 칸 변경과 라이브 미측정을 말함
- `catalog/` diff가 비어 있음
- 태그와 GitHub Release를 만들지 않음

오프라인 통과는 모델이 그림을 ELI5보다 잘 뽑는다는 증거가 아니다.

## Recovery

- `Do not silently pick a depth`를 남겨 두면 `missing-rung` 새 기대와
  충돌한다. 그 문장을 우선순위 기본 그림으로 교체한다.
- 설치 파이썬 블록을 건드리면 제품 README 바이트 계약이 실패한다. 블록은
  되돌린다.
- `live/smoke-record.json`을 다시 쓰면 schema 1 바이트 검사가 실패한다.
  그 파일은 되돌린다.
- `/eli5`를 description에 넣으면 `test_description_excludes_eli5_and_workflow`와
  `scripts/release.py`가 실패한다. near-miss로 되돌린다.
- 공개 문서가 라이브 품질 향상을 주장하면 testing.md의 `not_measured` 문장과
  맞추어 주장을 뺀다.

## 구현 순서

코드와 산 문서는 이 스펙이 승인된 뒤에만 바꾼다. 다음 단계는 writing-plans다.

1. RED: `cases.json`·`test_contract.py`·버전 핀을 3.0.0/기본 그림으로 바꿔
   오프라인을 실패시킨다.
2. `SKILL.md` 게이트와 우선순위.
3. `output.md` / `visuals.md` / `korean.md` 그림 레시피.
4. README·계약·CHANGELOG.
5. `python3 scripts/verify.py --skill how-it-works`와 전체 verify.
6. 라이브 호출 없음.
