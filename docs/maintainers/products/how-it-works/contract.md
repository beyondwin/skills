# how-it-works 계약

이 문서는 how-it-works의 호출 조건(trigger), 설명 칸, 출력, 안전 규칙, 함께 고칠
파일을 정합니다. 동작을 바꾸면 안내문, 테스트 예시, 공개 안내를 같은 변경에서 함께
고칩니다. 하나라도 낡은 채로 두면 규칙 위반입니다. 공개 설치 안내는 제품
`README.md`/`README.en.md`와 `docs/users/`에 있습니다.

## 트리거와 기본값

명시 호출은 Codex에서 `$how-it-works`, Claude Code에서 `/how-it-works`입니다.
"원리부터", "그림으로", "어떻게 돌아가", "감이 안 와" 같은 말에도 활성화됩니다.
`/eli5`와 "explain like I'm 5"는 다른 스킬의 몫이며, 이 스킬은 아무 일도 하지
않습니다.

설명 전에 네 칸 `slice`(설명할 조각), `type`(설명 유형), `rung`(깊이),
`language`(답 언어)를 채웁니다. type과 language는 추론합니다.

깊이(rung)는 그림, 길, 뼈대, 허점 넷입니다. 깊이 선택지(picker)에서 먼저 추천하는
칸은 그림입니다. 깊이는 다음 순서로 정합니다.

`explicit rung > explicit depth alias > existing jargon default > default 그림`

- 명시한 그림/길/뼈대/허점 또는 picture/path/skeleton/fracture가 가장 먼저
  적용됩니다.
- `쉽게`/`한눈에`/`한 장`/`감이 안 와`는 jargon(`rebase`, `TTL`, `Raft`)이 있어도
  그림입니다.
- jargon이 있을 때의 기본 뼈대는 명시한 rung이나 깊이 별칭이 없을 때만
  적용합니다.
- 숫자 별칭 `5→그림`, `10→길`, `15→뼈대`, `20→허점`은 깊이를 명시적으로 고른
  경우에만 해석합니다. `Raft term 20`, `HTTP/2`, `5개 노드`의 숫자는 주제
  데이터입니다.
- 이미 채워진 칸은 바꾸지 않습니다.
- 깊이가 비어 있으면 기본 그림을 첫 안내 줄(intent)에 알리고 같은 턴에서
  설명합니다.

## 출력

필수 결과는 채팅 답 안에서 끝납니다. 호스트 페이지, Canvas, 브라우저, URL, 파일,
mermaid 렌더러는 필수가 아닙니다. 렌더러가 없어도 실패가 아닙니다. 미리보기는
완전한 답 뒤에만 붙일 수 있고, 미리보기가 실패해도 치명적이지 않습니다.

필수 여섯 가지는 다음과 같습니다.

1. one-sentence claim — 한 줄로 무엇이 도는지
2. Mermaid — 그림
3. numbered hop list — 번호 매긴 단계
4. rung-specific body — 고른 깊이의 본문
5. adjacent slices — 지금 다루지 않은 옆 설명
6. one next move — 다음에 할 일 하나

그림 깊이에서는 지도(Map)에 번호 단계(홉)가 Mermaid 소스보다 먼저 나옵니다. 그림
본문은 그 단계를 다시 따라가지 않습니다.

- 답의 틀(크롬)과 홉 ID 규칙은 `skills/how-it-works/references/output.md`가
  소유합니다.
- 시각 채널은 mermaid입니다. 손으로 그린 HTML 상자는 도표가 아닙니다.
- 모든 깊이의 Map에는 기준 Mermaid와 `H1`, `H2` 형식의 번호 있는 홉 목록이
  남습니다. 깊이가 바뀌어도 같은 ID를 유지하고, 추가 설명은 같은 홉에 붙입니다.
- 허점의 실패/적용 범위 표는 Mermaid를 대신하지 않으며 Body에 둡니다.

제목, intent, 본문, 배너, 다음 이동은 선택한 언어 하나로만 출력합니다. 공통
템플릿의 `한 줄 / One sentence` 같은 표기는 두 언어를 함께 쓰라는 뜻이 아니라
현재 언어에 맞는 한쪽을 고르라는 뜻입니다.

비교는 사용자가 제시한 조건 아래에서 tradeoff를 설명합니다. 의료·법률·금융 비교에
개인 행동 추천을 필수로 요구하지 않습니다.

## 안전

- 사용자 주제를 픽스처(미리 만든 검사 예시)나 로그로 저장하지 않습니다.
- 그 턴에서 실제로 가져온 URL만 검증한 출처로 표시할 수 있습니다. 비공개
  자료 모음(코퍼스)이 아닙니다.
- 안정적인 일반 원리는 불필요하게 조회하지 않습니다.
- 날짜·관할·중대한 불확실성에 기대는 주장은 검증하거나 미확인으로 명시합니다.
  호스트 정책과 사용자 제약이 허용하면 1차 출처를 확인합니다. 조회할 수 없거나
  사용자가 금지하면 날짜/관할 한계와 함께 미확인으로 표시합니다.
- 논문·법령 식별자를 지어내지 않습니다. 근거 제목을 생략해도 미확인 주석은
  허용됩니다.

의료·법률·금융 슬라이스는 일반 메커니즘만 설명하고 개인 조언을 하지 않습니다.
선택한 언어의 정확한 한국어/영어 배너는
`skills/how-it-works/references/stakes.md`가 소유합니다.
`korean-writing-editor`를 호출하지 않습니다.

## 버전과 설치

현재 제품 계약 버전은 `3.0.0`입니다. 원본은
`skills/how-it-works/release.toml`이며, `SKILL.md`의 `metadata.version`은 같은
값을 복제합니다. `metadata.updated_at`과 `CHANGELOG.md`의 버전 날짜는 실제
구현일 `2026-09-12`입니다. 이 메타데이터는 tag, 공개, GitHub Release가 생겼다는
뜻이 아닙니다.

두 제품 README는 `<!-- how-it-works-local-links -->` 바로 뒤의 Python 블록을
바이트 단위로 같게 유지합니다. 이 블록의 규칙은 다음과 같습니다.

- source와 target 두 인자를 받고, source가 실제로 있는지와 `SKILL.md`를 먼저
  검사합니다.
- 같은 symlink는 성공입니다.
- 다른 symlink, 깨진 symlink, 파일, 디렉터리, 검사 뒤 나타난 target은 바꾸지
  않고 거부합니다.

README의 실행 예시는 따옴표로 감싼 here-document와 따옴표로 감싼 source/target
인자를 쓰며, Codex와 Claude Code target을 따로 호출합니다. 실제 HOME에서는
검증하지 않습니다. 공백이 있는 임시 경로에서의 동작 반례는 공통 설치 계약 검사가
소유합니다.

## 함께 고칠 파일

동작 변경을 한 파일에만 넣지 마세요.

- trigger 또는 near-miss(비슷하지만 호출하면 안 되는 요청) 변경
  (`$how-it-works`, `/how-it-works`, 원리부터, `/eli5` no-op):
  `skills/how-it-works/SKILL.md` 활성화 문구,
  `tests/products/how-it-works/cases.json`,
  `tests/products/how-it-works/test_contract.py`, 제품 README와 공유 공개 안내
- 칸 기본값 또는 별칭 변경 (`slice`, `type`, `rung`, `language`, 명시 rung/별칭
  우선, 조건부 jargon 기본, 숫자 주제 데이터): `SKILL.md`의 dump gate(설명을
  바로 쏟아내지 않게 막는 확인 표), 픽스처, 공개 안내
- 출력 크롬, 유형 레시피, 홉 ID, 허점 Body 표, 비교 정책:
  `skills/how-it-works/references/output.md`와 해당 픽스처 id
- 시각 채널: `skills/how-it-works/references/visuals.md`. 모든 깊이에서 기준
  mermaid 소스와 번호 있는 홉 목록을 유지합니다.
- 한국어 목소리와 intent/그림 예시: `skills/how-it-works/references/korean.md`.
  `korean-writing-editor`를 호출하지 않습니다.
- 이해관계 배너와 고위험 확인 정책: `skills/how-it-works/references/stakes.md`의
  언어별 정확한 배너 바이트
- 출처 또는 인용 정책: `skills/how-it-works/references/sources.md`. 검증/미확인을
  구분하고 논문·법령 ID를 지어내지 않습니다.
- 버전, 설치 블록, 설치 파일(payload) 안팎 링크:
  `skills/how-it-works/release.toml`, `SKILL.md`, `CHANGELOG.md`, 두 제품 README,
  `tests/products/how-it-works/test_contract.py`. 공통 설치 실행 반례와 공유
  version pin은 통합 담당이 소유합니다.
