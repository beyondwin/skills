# how-it-works 계약

트리거, 칸, 출력, 안전, 함께 고칠 파일을 같이 유지하세요. 프롬프트만 고치고 픽스처나 공개 안내를 낡은 상태로 두면 계약 위반입니다. 공개 설치 안내는 제품 `README.md`/`README.en.md`와 `docs/users/`에 있습니다.

## 트리거와 기본값

명시 호출은 Codex에서 `$how-it-works`, Claude Code에서 `/how-it-works`입니다. 원리부터, 그림으로, 어떻게 돌아가, 감이 안 와도 활성화입니다. `/eli5`와 “explain like I’m 5”는 다른 스킬이며 이 스킬에서 no-op입니다.

설명 전에 `slice`, `type`, `rung`, `language`를 채웁니다. 칸은 그림, 길, 뼈대, 허점입니다. 기본 칸은 길입니다. jargon(`rebase`, `TTL`, `Raft`)은 그림이라는 단어를 쓰지 않는 한 뼈대입니다. `쉽게`는 그림이 아닙니다. 한 번에 질문 하나, 채워진 칸은 다시 묻지 않습니다.

## 출력

필수 산출은 채팅에서 완료됩니다. 호스트 페이지, Canvas, 브라우저, URL, 파일, mermaid 렌더러는 필수가 아닙니다. 렌더러가 없어도 실패가 아닙니다. 미리보기는 완전한 답 뒤에만 붙일 수 있고, 미리보기 실패는 치명적이지 않습니다.

필수 여섯 가지는 다음과 같습니다.

1. one-sentence claim
2. Mermaid
3. numbered hop list
4. rung-specific body
5. adjacent slices
6. one next move

크롬과 홉 ID 규칙은 `skills/how-it-works/references/output.md`가 소유합니다. mermaid가 시각 채널입니다. 손으로 그린 HTML 상자는 다이어그램이 아닙니다.

## 안전

사용자 주제를 픽스처나 로그로 저장하지 않습니다. 인용은 그 턴에서 가져온 URL만 보이며 비공개 코퍼스가 아닙니다. 의료·법률·금융 슬라이스는 메커니즘만 설명하고 조언이 아닙니다. 정확한 배너 바이트는 `skills/how-it-works/references/stakes.md`가 소유합니다. `korean-writing-editor`를 호출하지 않습니다.

## 함께 고칠 파일

동작 변경을 한 파일에만 넣지 마세요.

- trigger 또는 near-miss 변경 (`$how-it-works`, `/how-it-works`, 원리부터, `/eli5` no-op): `skills/how-it-works/SKILL.md` 활성화 문구, `tests/products/how-it-works/cases.json`, `tests/products/how-it-works/test_contract.py`, 제품 README와 공유 공개 안내
- 칸 기본값 또는 별칭 변경 (`slice`, `type`, `rung`, `language`, 길 default, jargon to 뼈대, 쉽게 is not 그림): `SKILL.md` dump gate, 픽스처, 공개 안내
- 출력 크롬, 유형 레시피, 홉 ID: `skills/how-it-works/references/output.md`와 해당 픽스처 id
- 시각 채널: `skills/how-it-works/references/visuals.md`. mermaid 소스와 번호 있는 홉 목록을 유지합니다.
- 한국어 목소리: `skills/how-it-works/references/korean.md`. `korean-writing-editor`를 호출하지 않습니다.
- 이해관계 배너: `skills/how-it-works/references/stakes.md`의 정확한 배너 바이트
- 출처 또는 인용 정책: `skills/how-it-works/references/sources.md`. 논문 ID를 만들지 않습니다.
