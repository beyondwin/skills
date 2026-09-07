# korean-writing-editor 계약

트리거, 모드, 출력, 증거, 픽스처, 버전을 함께 유지하세요. 프롬프트만 고치고
픽스처나 공개 안내를 낡은 상태로 두면 계약 위반입니다. 공개 설치 안내는 제품
`README.md`/`README.en.md`와 `docs/users/`에 있습니다. 제품 README는 설치
파일에 포함됩니다.

## 트리거와 기본값

명시 호출은 `$korean-writing-editor` 또는 `/korean-writing-editor`와 한국어
원문입니다. 암묵 활성화는 교정·윤문 요청과 공급된 한국어 원문이 모두 있을
때만 허용됩니다. 예전 `kws-` 접두 호출은 항상 아무 일도 하지 않습니다.

유효한 요청의 기본 모드는 보수적 `polish`입니다. `diagnose`는 고치지 않고
문제만 말합니다. `correct`는 규범·문법의 국소 교정만 합니다.

| Mode | 사용자 의도 | 경계 |
| --- | --- | --- |
| `diagnose` | 고치지 말고 문제만 알려줘 | 문제, 결정 등급, hold만 말한다. 다시 쓰지 않는다. |
| `correct` | 오탈자만 고쳐줘 | 규범과 분명한 문법의 국소 교정만 한다. |
| `polish` | 자연스럽게 다듬어줘 | 의미와 말투를 지키며 국소 가독성만 다듬는다. |

모델 등급은 `fast`, `balanced`, `frontier`입니다. 공급자 모델 이름을
하드코딩하지 마세요. 분류 모델을 호출하지 않습니다.

## 출력

`correct`와 `polish`의 기본 출력은 편집된 글만입니다. `diagnose`의 기본 출력은
소견입니다. 다시 쓴 초안을 붙이지 않습니다. 루브릭, 변경 로그, 점수, 라우팅
영수증, 과정 서술을 붙이지 않습니다. 실질 hold에만 짧은 `확인 필요` 주를
답니다.

## 진단 증거의 경계

승인된 hardening 설계 K2에 따라 `diagnose`에서 원문의 수치나 비수치 보호
표현을 단순히 언급하지 않은 것은 사실 변경의 증거가 아닙니다. 기존의
미언급 hard 실패 기대를 이 계약으로 대체하며 원문 재작성을 요구하지 않습니다.

`diagnostic_fact_drift`는 보호 수량이 원문에 한 번만 나오고, 정규화한 원문
전체를 같은 문장으로 재진술하면서 해당 숫자를 바꾼 경우에만 hard입니다.
대안 수치, 인용 예시, 더 긴 자유형 설명 속 숫자는
`diagnostic_semantics_not_measured`로 남습니다. 다른 hard 위반이 없으면
`partially_verified`이며, 일반적인 의미 보존이나 법적 타당성이 검증된 것은
아닙니다. 편집 본문의 리터럴 검사와 진단의 명시적 금지 재작성 검사는 유지합니다.

## 안전과 개인정보

사용자가 준 한국어 글을 픽스처, 로그, 말투 프로필로 저장하지 않습니다.
비공식 맞춤법 웹 서비스로 보내지 않습니다. 따로 요청하지 않으면 사실을
찾아오지 않습니다. 법률·의료·금융처럼 이해관계가 큰 글은 기계적 `correct`
또는 `diagnose`가 기본입니다. 라이브 케이스는 합성만 허용합니다. 비공개
원고나 전체 트랜스크립트를 커밋하지 않습니다.

## 함께 고칠 파일

동작 변경을 한 파일에만 넣지 마세요.

- trigger 또는 near-miss 변경: `skills/korean-writing-editor/SKILL.md` 활성화 문구, `tests/products/korean-writing-editor/offline/cases.json`의 긍정·near-miss 픽스처, 제품 README와 공유 공개 안내
- mode 또는 output 계약 변경 (`diagnose`, `correct`, `polish`, 기본 편집문만 출력, hold 주): `SKILL.md`, `skills/korean-writing-editor/references/editorial-guide.md`, 픽스처, 공개 안내
- 모델 tier 변경 (`fast`, `balanced`, `frontier`, 라우팅, 위임): `tests/products/korean-writing-editor/offline/cases.json` 라우팅 픽스처와 공개 안내. 공급자 모델 이름을 하드코딩하지 말고 분류 모델을 호출하지 않습니다.
- 규범 주장 변경: `skills/korean-writing-editor/references/sources.md`의 권위 출처 위치와, 그 경계를 담는 픽스처
- 외부 프로젝트 사용: `references/sources.md`에 고정 리비전, 라이선스, 확인 날짜, 채택/거절 경계를 기록합니다. 제3자 규칙 목록이나 코퍼스를 복사하지 않습니다.
