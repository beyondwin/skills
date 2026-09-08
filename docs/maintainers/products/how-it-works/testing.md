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

`test_v2_release_and_repeatable_install_contract`는 제품 version, 두 README의 추출
marker, 옛 직접 `ln -s` 명령 제거, payload 밖 문서에 대한 깨진 상대 링크 제거를
검사합니다. 제품 검사는 설치 코드를 실제 HOME에서 실행하지 않습니다. 공백 포함
임시 source/target의 첫 설치, 동일 링크 반복, 실제 디렉터리, 다른 링크, 깨진 링크,
경합 반례는 통합 담당의 `tests/repository/test_installation_contract.py`가 실행해야
합니다. 첫 설치와 반복은 성공하고, 거부 시 원본과 target 바이트·링크가 그대로여야
합니다.

## 선택적 라이브 smoke

라이브 실행은 로컬, 명시적, 선택적이며 비용이 들 수 있습니다. CI가 요구하지
않습니다. 페이로드 계약 통과를 라이브 호출 증거로 설명하지 마세요.

제품 지원은 Codex/Claude Code 그대로이며 현재 2.0.0의 실제 실행 증거는
`not_measured`입니다. 지원 대상과 현재 측정 상태를 같은 조건으로 계산하지 않습니다.
과거 `live/smoke-record.json`의 schema 1 바이트와 날짜·클라이언트·판정은 유지합니다.
이 기록은 `historical-unbound`이며 당시 payload hash나 model을 추정하지 않습니다.
과거 Grok 실패와 Cursor 미측정도 현재 빌드의 측정 결과로 바꾸지 않습니다.

새 증거 계약의 순수 함수는 `tests/products/how-it-works/live/evidence_contract.py`에
있으며 설치 payload에 포함되지 않습니다. `test_evidence_contract.py`의 입력은 합성
단위 테스트용이며 실제 실행 기록이 아닙니다. 실제 새 기록 파일은 만들지 않습니다.

- `observe_text`는 닫힌 비어 있지 않은 Mermaid fence와 source/prose의 동일한
  H1/H2 hop ID 및 번호 목록의 중복 여부만 `lexical`로 관측합니다.
- `skill_loading`은 별도 `host_event`, `mermaid_syntax`는 실제 실행한 `parser` 또는
  `renderer`, `meaning`은 `semantic_review`가 있어야 측정할 수 있습니다. 로딩을
  스킬 이름 언급이나 출력 chrome에서 추정하지 않습니다.
- 모든 차원은 `status`와 `method`를 가지며, 출처가 없으면 `not_measured/not_run`입니다.
  near-miss는 invocation만 판정하고 다섯 출력 차원은 미측정으로 둡니다.
- schema 2는 실제 product version, 기존 `payload_sha256(Path)`의 hash, model,
  host, client/runner version, 실행일, 케이스별 invocation과 다섯 차원을 기록합니다.
  model을 확인할 수 없으면 `null`이고 결과는 `unbound`입니다. hash는 payload 수정이
  모두 끝난 뒤 계산하며, 실제 버전은 `load_product_release(Path).version`을 사용합니다.
- 알려진 model과 일치하는 version/hash는 `current-bounded`, 불일치는
  `different-payload`입니다. 이는 제출한 메타데이터의 결속이며 실제 실행 인증이나
  품질 통과가 아닙니다. 방법 선언 자체의 진위도 이 함수가 인증하지 않습니다.

직접 단위 검사는 깨진 Mermaid의 비승격, hop 불일치·중복·부재, 과거 기록 비변경,
null model, 버전/hash 불일치, 임시 reference 변경에 따른 실제 공통 hash 변화,
추가 키·잘못된 날짜·차원 누락·boolean schema 및 잘못된 방법 선언을 검증합니다.
형태만으로 문법·인과·깊이 전환·접근성을 입증하지 않습니다. parser/renderer는 이미
실행 가능한 경우 실제 실행 결과만 기록하며 이 작업은 설치를 요구하지 않습니다.

세 기존 synthetic prompt와 상세 schema·관측 절차는
`tests/products/how-it-works/live/README.md`를 따릅니다. 전체 응답과 비공개 프롬프트,
자격증명은 커밋하지 않습니다.

## 명령

```bash
python3 scripts/verify.py --skill how-it-works
python3 scripts/verify.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/how-it-works -p test_evidence_contract.py -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/how-it-works -p 'test_*.py' -v
git diff --check
```

공통 `how-it-works-contract` stage가 `test_contract.py`만 발견하는 동안에는 위 직접
명령으로 새 파일을 실행합니다. 통합 담당이 discovery pattern을 `test_*.py`로
수정하고 공유 version pin을 맞춘 뒤 `--skill` 및 전체 profile을 실행합니다.
제품 단위 순수 검사 통과는 이 통합 게이트나 라이브 모델 품질의 통과를 대신하지 않습니다.
