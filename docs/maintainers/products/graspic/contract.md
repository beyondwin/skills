# graspic 계약

트리거, 칸 기본값, 출력 크롬, 시각, 한국어 목소리, 이해관계, 픽스처, 버전을 함께 유지하세요. 프롬프트만 고치고 픽스처나 공개 안내를 낡은 상태로 두면 계약 위반입니다. 공개 설치 안내는 제품 `README.md`/`README.en.md`와 `docs/users/`에 있습니다.

## 트리거와 기본값

`/graspic`, 원리부터, 그림으로, 어떻게 돌아가, 감이 안 와가 활성화입니다. `/eli5`와 “explain like I’m 5”는 다른 스킬이며 이 스킬에서 no-op입니다.

설명 전에 `slice`, `type`, `rung`, `language`를 채웁니다. 칸은 그림, 길, 뼈대, 허점입니다. 기본 칸은 길입니다. jargon(`rebase`, `TTL`, `Raft`)은 그림이라는 단어를 쓰지 않는 한 뼈대입니다. `쉽게`는 그림이 아닙니다.

## 출력

기본 산출은 게시된 페이지이며 터미널 스크롤백이 아닙니다. mermaid가 시각 채널입니다. 아티팩트가 그림을 그리고, 터미널은 소스를 출력합니다.

1. 파일을 쓰기 전에 매번 `artifact-design`을 읽습니다.
2. `skills/graspic/references/output.md` 크롬을 하나의 HTML 페이지로 씁니다. 모든 지도는 `<pre class="mermaid">` 블록에 둡니다. HTML은 페이지 프레임만 담당합니다. 손으로 그린 HTML 상자는 다이어그램이 아닙니다.
3. Artifact 도구로 게시합니다. `<title>`은 `{slice}`와 칸 단어뿐입니다.
4. 채팅에는 의도 한 줄, 한 줄 요약, 링크만 남깁니다.

한 조각은 한 아티팩트입니다. 그림 → 길 → 뼈대 → 허점으로 올라갈 때 같은 파일 경로를 다시 게시해 URL을 유지합니다. 칸마다 새 URL을 만들지 않습니다. `image_gen`으로 구조를 그리지 않습니다.

사용자가 `채팅으로만` 또는 `페이지 말고`를 요청한 경우에만 터미널 마크다운으로 내리고 게시를 건너뜁니다. 이 예외는 기본 계약을 채팅 전용으로 되돌리지 않습니다.

## 안전

사용자 주제를 픽스처나 로그로 저장하지 않습니다. 인용은 그 턴에서 가져온 URL만 보이며 비공개 코퍼스가 아닙니다. 의료·법률·금융 슬라이스는 메커니즘만 설명하고 조언이 아닙니다. 정확한 배너 바이트는 `skills/graspic/references/stakes.md`가 소유합니다. `korean-writing-editor`를 호출하지 않습니다.

## 함께 고칠 파일

동작 변경을 한 파일에만 넣지 마세요.

- trigger 또는 near-miss 변경 (`/graspic`, 원리부터, `/eli5` no-op): `skills/graspic/SKILL.md` 활성화 문구, `tests/products/graspic/cases.json`, `tests/products/graspic/test_contract.py`, 제품 README와 공유 공개 안내
- 칸 기본값 또는 별칭 변경 (길 default, jargon to 뼈대, 쉽게 is not 그림): `SKILL.md` dump gate, 픽스처, 공개 안내
- 출력 크롬, 유형 레시피, 은유 테스트: `skills/graspic/references/output.md`와 해당 픽스처 id
- 시각 채널: `skills/graspic/references/visuals.md`. 페이지 프레임 HTML과 mermaid 지도를 유지하고, 구조에 `image_gen`을 쓰지 않습니다.
- 한국어 목소리: `skills/graspic/references/korean.md`. `korean-writing-editor`를 호출하지 않습니다.
- 이해관계 배너: `skills/graspic/references/stakes.md`의 정확한 배너 바이트
- 출처 또는 인용 정책: `skills/graspic/references/sources.md`. 논문 ID를 만들지 않습니다.
