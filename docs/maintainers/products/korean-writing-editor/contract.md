# korean-writing-editor 계약

호출 조건(trigger), 모드, 출력, 증거, 테스트 예시(픽스처), 버전은 한 변경 안에서
함께 맞추세요. 안내문만 고치고 픽스처나 공개 안내를 낡은 채 두면 규칙
위반입니다. 공개 설치 안내는 제품 `README.md`/`README.en.md`와 `docs/users/`에
있습니다. 제품 README는 설치 파일에 포함됩니다.

## 호출 조건과 기본값

명시 호출은 `$korean-writing-editor` 또는 `/korean-writing-editor`에 한국어
원문을 붙인 것입니다. 암묵 활성화는 교정·윤문 요청과 사용자가 준 한국어 원문이
둘 다 있을 때만 허용됩니다. 예전 `kws-` 접두 호출은 항상 아무 일도 하지
않습니다.

유효한 요청의 기본 모드는 보수적인 `polish`입니다.

| Mode | 사용자 의도 | 경계 |
| --- | --- | --- |
| `diagnose` | 고치지 말고 문제만 알려줘 | 문제, 결정 등급, 보류(hold)만 말한다. 다시 쓰지 않는다. |
| `correct` | 오탈자만 고쳐줘 | 규범과 분명히 고쳐야 하는 국소 문법만 교정한다. |
| `polish` | 자연스럽게 다듬어줘 | 같은 필수 교정을 한 뒤 의미와 말투를 지키며 선택적으로 가독성과 국소 흐름을 다듬는다. |

- `correct`와 `polish`는 둘 다 규범 오류와 분명한 국소 문법 오류를 고칩니다.
  중복 조사나 분명히 잘못된 호응이 여기에 속합니다.
- 선택적인 가독성·국소 흐름 개선은 `polish`에서만 합니다.
- 주어, 높임 수준, 뜻을 추측해야 하는 문법 수정은 고치지 않고 보류(hold)
  규칙을 따릅니다.

모델 등급(tier)은 `fast`, `balanced`, `frontier`입니다. 공급자 모델 이름을
하드코딩하지 마세요. 분류 모델을 호출하지 않습니다.

## 출력

- `correct`와 `polish`의 기본 출력(output)은 고친 글만입니다. 첫 글자부터 그
  본문이어야 합니다.
- `diagnose`의 기본 출력은 소견입니다. 첫 줄이 문제, 등급, 또는 보류를
  가리킵니다.
- 다시 쓴 초안, 채점표, 변경 목록, 점수, 라우팅 기록(receipt), “스킬을 쓰는 중” 같은
  설명을 붙이지 않습니다. 정말 멈춰야 할 때만 짧은 `확인 필요`를 답니다.
- 편집이 아닌 요청(번역, 초안 등)은 거절만 합니다. 그 턴에서 그 일을 대신 하지
  않습니다.
- 이미 맞는 표현을 비슷한 말로 바꾸면 `correct`와 `polish` 모두에서 되돌립니다.

## 진단 증거의 경계

승인된 보강(hardening) 설계 K2에 따른 규칙입니다. `diagnose`가 원문의 수치나
비수치 보호 표현을 언급하지 않았다고 해서 사실을 바꾼 증거는 아닙니다. 이
계약은 예전의 "언급하지 않으면 hard 실패" 기대를 대체하며, 원문 재작성을
요구하지 않습니다.

`diagnostic_fact_drift`는 다음 조건을 모두 만족할 때만 hard입니다.

- 보호 수량이 원문에 한 번만 나온다.
- 정규화한 원문 전체를 같은 문장으로 다시 말한다.
- 그러면서 해당 숫자를 바꾼다.

대안 수치, 인용 예시, 더 긴 자유 설명 속 숫자는
`diagnostic_semantics_not_measured`로 남습니다. 다른 hard 위반이 없으면
`partially_verified`입니다. 이것은 일반적인 의미 보존이나 법적 타당성을 검증했다는
뜻이 아닙니다. 편집 본문의 리터럴 검사와, 진단에서 금지된 재작성을 잡는 명시적
검사는 그대로 유지합니다.

## 안전과 개인정보

- 사용자가 준 한국어 글을 픽스처, 로그, 말투 프로필로 저장하지 않습니다.
- 비공식 맞춤법 웹 서비스로 보내지 않습니다.
- 따로 요청하지 않으면 사실을 찾아오지 않습니다.
- 법률·의료·금융처럼 이해관계가 큰 글은 기계적 `correct` 또는 `diagnose`가
  기본입니다.
- 라이브 케이스는 합성 예시만 허용합니다. 비공개 원고나 전체 대화 기록
  (transcript)을 커밋하지 않습니다.

## 함께 고칠 파일

동작 변경을 한 파일에만 넣지 마세요.

- trigger 또는 near-miss(비슷하지만 대상이 아닌 요청) 변경: `skills/korean-writing-editor/SKILL.md` 활성화 문구, `tests/products/korean-writing-editor/offline/cases.json`의 긍정·near-miss 픽스처, 제품 README와 공유 공개 안내
- mode 또는 output 계약 변경 (`diagnose`, `correct`, `polish`, 기본 편집문만 출력, 보류 표시): `SKILL.md`, `skills/korean-writing-editor/references/editorial-guide.md`, 픽스처, 공개 안내
- 모델 tier 변경 (`fast`, `balanced`, `frontier`, 라우팅, 위임): `tests/products/korean-writing-editor/offline/cases.json` 라우팅 픽스처와 공개 안내. 공급자 모델 이름을 하드코딩하지 말고 분류 모델을 호출하지 않습니다.
- 규범 주장 변경: `skills/korean-writing-editor/references/sources.md`의 권위 출처 위치와, 그 경계를 담는 픽스처
- 외부 프로젝트 사용: `references/sources.md`에 고정 리비전, 라이선스, 확인 날짜, 채택/거절 경계를 기록합니다. 제3자 규칙 목록이나 코퍼스를 복사하지 않습니다.
