# how-it-works 테스트

공급자 없는 계약과 선택적 유료 smoke를 섞지 마세요. 사용자 주제, 공급자 트랜스크립트, 비공개 로그를 Git 픽스처로 커밋하지 마세요.

## 공급자 없는 증거

필수 증거는 `python3 scripts/verify.py --skill how-it-works`입니다.
`tests/products/how-it-works/cases.json`과
`tests/products/how-it-works/test_contract.py`는 형태와 페이로드 계약만
증명합니다. 라이브 모델 품질과 지원 호스트 런타임 동등은 증명하지 않습니다.

결정적 픽스처:

- `broad-slice`는 문명 명사를 세 조각으로 자르고 질문 하나입니다.
- `missing-rung`은 닫힌 깊이 질문 하나이며 칸을 조용히 채우지 않습니다.
- `explicit-dns-path`는 채팅 필수 산출 여섯 가지이며 호스트 도구를 요구하지 않습니다.
- `implicit-positive`는 의도한 암묵 활성화입니다.
- `near-miss-debug`와 `near-miss-eli5`는 활성화하지 않습니다. `/eli5`는 이 스킬이 아닙니다.
- `jargon-rung`은 명시한 `쉽게` 별칭이 jargon보다 우선해 그림입니다.
- `no-renderer`는 mermaid 소스와 번호 있는 홉 목록을 남기고 실패가 아닙니다.
- `no-fetched-source`는 가져온 URL이 없으면 근거 제목을 생략하고 인용을 만들지 않습니다.
- `explicit-fracture-jargon`과 `explicit-path-jargon`은 명시한 허점/길이 jargon 기본보다 우선합니다.
- `english-explicit-fracture`는 영어 fracture 선택과 영어 출력을 잠급니다.
- `jargon-without-depth`는 깊이 선택이 없을 때 기존 jargon 뼈대 기본을 유지합니다.
- `topic-number-is-not-depth`는 `Raft term 20`의 숫자를 허점 선택으로 해석하지 않습니다.
- `explicit-numeric-depth`는 `깊이 5`처럼 명시적으로 고른 숫자만 그림 별칭으로 해석합니다.
- `fracture-keeps-map`은 허점에서도 기준 Mermaid와 번호 있는 홉을 Map에
  유지하고 실패/적용 범위 표를 Body에 둡니다.
- `high-stakes-no-lookup`은 검색 금지를 지키면서 날짜·관할 의존 주장을
  미확인으로 표시하고 법령 식별자를 만들지 않습니다.
- `high-stakes-english`는 영어 배너만 선택합니다.
- `high-stakes-comparison`은 사용자가 제시한 조건 아래 tradeoff를 설명하며 개인
  행동 추천을 강제하지 않습니다.

페이로드 계약 통과는 파일 정체성, 이식 가능한 frontmatter, 금지 문자열만
증명합니다. 실제 모델이 깊이 우선순위를 준수하는지는 `not_measured`입니다.
옛 고위험 배너와 옛 DNS jargon 문구의 정확한 문자열 회귀도 거부합니다. 이 검사는
문서와 fixture의 정적 일치만 증명합니다. 설명의 진실성, 실제 해요체 준수, 영어
출력 품질, 모델의 여섯 산출 준수, Mermaid parser/renderer 결과는
`not_measured`입니다.

## 선택적 라이브 smoke

라이브 실행은 로컬, 명시적, 선택적이며 비용이 들 수 있습니다. CI가 요구하지
않습니다. 페이로드 계약 통과를 라이브 호출 증거로 설명하지 마세요.

같은 빌드에서 지원을 유지하려면 다음 네 가지가 통과해야 합니다.

1. 스킬 발견
2. 명시 호출
3. 의도한 암묵 호출과 near-miss 비호출
4. 완전한 마크다운, mermaid 소스, 번호 있는 홉 목록

기록은 호스트, 클라이언트 버전, 날짜, 케이스, 판정만 남깁니다. 전체 응답과
비공개 프롬프트는 커밋하지 않습니다.

## 명령

```bash
python3 scripts/verify.py --skill how-it-works
python3 scripts/verify.py
python3 -m unittest discover -s tests/products/how-it-works -p 'test_*.py'
git diff --check
```
