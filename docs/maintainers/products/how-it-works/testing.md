# how-it-works 테스트

공급자 없는 계약과 선택적 유료 smoke를 섞지 마세요. 사용자 주제, 공급자 트랜스크립트, 비공개 로그를 Git 픽스처로 커밋하지 마세요.

## 공급자 없는 증거

필수 증거는 `python3 scripts/verify.py --skill how-it-works`입니다. `tests/products/how-it-works/cases.json`과 `tests/products/how-it-works/test_contract.py`는 형태와 페이로드 계약만 증명합니다. 라이브 모델 품질과 지원 호스트 런타임 동등은 증명하지 않습니다.

결정적 픽스처:

- `broad-slice`는 문명 명사를 세 조각으로 자르고 질문 하나입니다.
- `missing-rung`은 닫힌 깊이 질문 하나이며 칸을 조용히 채우지 않습니다.
- `explicit-dns-path`는 채팅 필수 산출 여섯 가지이며 호스트 도구를 요구하지 않습니다.
- `implicit-positive`는 의도한 암묵 활성화입니다.
- `near-miss-debug`와 `near-miss-eli5`는 활성화하지 않습니다. `/eli5`는 이 스킬이 아닙니다.
- `jargon-rung`은 뼈대 기본이며 그림 기본이 아닙니다.
- `no-renderer`는 mermaid 소스와 번호 있는 홉 목록을 남기고 실패가 아닙니다.
- `no-fetched-source`는 가져온 URL이 없으면 근거 제목을 생략하고 인용을 만들지 않습니다.

페이로드 계약 통과는 파일 정체성, 이식 가능한 frontmatter, 금지 문자열만 증명합니다.

## 선택적 라이브 smoke

라이브 실행은 로컬, 명시적, 선택적이며 비용이 들 수 있습니다. CI가 요구하지 않습니다. 페이로드 계약 통과를 라이브 호출 증거로 설명하지 마세요.

같은 빌드에서 지원을 유지하려면 다음 네 가지가 통과해야 합니다.

1. 스킬 발견
2. 명시 호출
3. 의도한 암묵 호출과 near-miss 비호출
4. 완전한 마크다운, mermaid 소스, 번호 있는 홉 목록

기록은 호스트, 클라이언트 버전, 날짜, 케이스, 판정만 남깁니다. 전체 응답과 비공개 프롬프트는 커밋하지 않습니다.

## 명령

```bash
python3 scripts/verify.py --skill how-it-works
python3 scripts/verify.py
python3 -m unittest discover -s tests/products/how-it-works -p 'test_*.py'
git diff --check
```
