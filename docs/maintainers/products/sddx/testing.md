# sddx 테스트

이 문서는 공급자 없는 계약, `resolve_backend.py` 픽스처 경계, Git sandbox 준비·정리와
범위가 제한된 라이브 재검증을 소유합니다. 라이브 관측을 일반적인 provider 품질이나
다른 호스트의 실행 보장으로 확대하지 않습니다.

픽스처 경로는 `tests/products/sddx/`입니다.

## 공급자 없는 증거

필수 증거는 `python3 scripts/verify.py --skill sddx`입니다.
`tests/products/sddx/test_resolve_backend.py`는 PATH에 가짜 바이너리를
넣어 신원 규칙을 잠급니다. 실제 Cursor/Grok 계정을 쓰지 않습니다.
`tests/products/sddx/test_prepare_grok_sandbox.py`는 임시 저장소와 실제 linked
worktree를 만들고 Git 경로 계산, 기존 TOML 원문 복원, 재진입, 심볼릭 링크 거절,
CLI 성공·실패 출력을 검사합니다. 표준 `tomllib`를 사용하므로 Python 3.11 이상이
필요합니다.

생성되는 `sddx-worktree` 프로파일의 `read_write`는 linked worktree의 Git 디렉터리와
공용 `.git` 디렉터리를 허용합니다. 따라서 공용 `.git` 안에 있는 다른 브랜치 ref에도
쓰기 권한이 생깁니다. 이 검사는 정상적인 단일 컨트롤러 실행에서 기존 파일 변경을
보존하는지 확인하며, 악성 동시 변경에 대한 보안 경계나 Grok sandbox의 실제 실행
성공을 입증하지 않습니다.

결정적 검사:

- Grok 후보는 PATH의 `grok`뿐이다. `agent`만 있으면 `not_found`다.
- `agent`는 Cursor로 채택되지 않는다.
- Grok 신원의 `cursor-agent` 또는 `cursor`는 `identity_mismatch`다.
- Cursor는 headless print, force/yolo, trust, workspace/cwd, model, resume이
  필요하고 Grok 모델 id가 없으면 `no_grok_model`이다.
- Grok help에 `--cwd`가 없으면 `missing_flags`다.
- argv에 `--worktree`와 `--plugin-dir`가 없다. Grok 고정 플래그에
  `--disable-web-search`가 있다.

페이로드 계약 통과는 파일 정체성, 이식 가능한 frontmatter, 금지 문자열만
증명합니다. 이 공급자 없는 증거만으로 라이브 CLI, 과금, 모델 품질을
측정했다고 할 수 없습니다.

## 행동 probe

[행동 probe](../../../../tests/products/sddx/behavior-probes.md)는 이전 응답을 주지 않은
독립 문맥에서 native 모델이 제안한 행동을 컨트롤러가 수동 판정합니다. 2026-09-11
controller 시나리오 5개는 완료 판정, sandbox 실패, session 재사용·전환 기준을 모두
통과했습니다. 별도의 worker 역할 합성 표본에서는 external skill 읽기 제안이 baseline
2/5에서 candidate worker 안내 적용 후 0/5로 줄었습니다. 다섯 guided 응답은
`candidate-worker.md`를 읽었고, 최종 역할 문장과 내용은 같지만 기존 문단의 순서와
서식은 달랐습니다. 이 결과는 문자열 검사가 아니며, 작은 native simulation을 실제
Grok 호출이나 runtime 신뢰도 통계로 취급하지 않습니다.

## 2026-09-11 1.0.1 최초 Grok 검사

측정 환경은 macOS 26.5.2, Python 3.14.7, Codex controller, Grok 1.0.25,
`grok-4.6` High였습니다. 새 remote 없는 로컬 저장소의 linked worktree에서 다음
절차를 수행했습니다.

1. 수정된 제품에서 resolver와 sandbox helper를 확인하고, 각 호출 전 `prepare`,
   worker 종료 후 `cleanup`을 실행합니다.
2. 첫 task에서 Unicode 공백 정규화 구현과 테스트를 worker가 직접 커밋하게 합니다.
3. 같은 worker session에 TypeError 메시지와 동등성 테스트를 추가하라는 통제된
   요구를 보내고, 수정 커밋 뒤 native scoped review를 반복합니다.
4. 새 session으로 CLI task를 실행하고 worker의 세 번째 직접 커밋을 확인합니다.
5. fixture에서 `python3 -m unittest discover -s tests -v`, 기준과 결과 commit을
   인자로 준 `git diff --check`, `git status --short`, 변경 파일 목록과 최근 commit을
   확인합니다.

실제 provider 호출은 세 번이었고 모두 worker exit 0, cleanup exit 0, report `DONE`,
worker 직접 커밋으로 끝났습니다. 첫 task는 구현 전 `textnorm` 부재로 loader-error
test 1개를 실행한 RED exit 1 뒤 GREEN 7 tests exit 0, 통제된 same-session 수정은
RED 8 tests exit 1 뒤 GREEN 8 tests exit 0이었고, 둘째 task는 RED 14 tests
exit 1 뒤 GREEN 14 tests exit 0이었습니다. 둘째 task의
RED/GREEN은 shell wrapper exit 0 안의 실제 test exit를 별도로 확인했습니다. 원래
구현 결함은 발견되지 않았으며, same-session 변경은 미리 승인된 추가 요구의 resume
동작을 검증한 것입니다.

최종 독립 unittest는 14 tests, exit 0이었고 전체 commit 범위의
`git diff --check`도 exit 0이었습니다. worktree는 clean이었으며 세 worker commit에는
요구된 애플리케이션·테스트·README 파일 다섯 개만 포함됐습니다. 컨트롤러가 구현을
수정하거나 커밋을 보조하지 않았습니다. 생성 sandbox 설정과 복원 기록은 정리됐고,
기존 설정 byte 보존은 라이브 fixture가 아니라 공급자 없는 검사에서 입증했습니다.

실제 tool trace의 수동 검토에서는 brief-first 순서를 확인했고 external skill·전체 계획
읽기, nested agent, MCP tool 호출이나 역할 위반은 관측되지 않았습니다. 기존 host
integration의 MCP 초기화·handshake·자동 재시작 경고는 계속 나타났습니다. 이 경고는
모델의 MCP tool 호출과 다르며, 경고가 사라진다고 보장하지 않습니다.

독립 whole-fixture native review는 clean checkout, 생성 설정·journal 부재, worker가
소유한 commit 범위, same-session 수정과 새 task session, 독립 14-test 로그를 다시
확인하고 Critical/Important/Minor 0건으로 accept했습니다.

제품 구현 HEAD에서 `python3 scripts/verify.py`는 868 unittest를 포함한 전체
공급자 없는 검사를 완료해 exit 0이었습니다. 이후 변경은 문서뿐이므로 전체 suite를
반복하지 않고 내용·링크·diff를 검사합니다. Cursor worker와 Claude Code host 실행은
`not_measured`입니다.

## 명령

```bash
python3 scripts/verify.py --skill sddx
python3 scripts/verify.py
python3 -m unittest tests.products.sddx.test_resolve_backend
python3 -m unittest discover -s tests/products/sddx -p test_prepare_grok_sandbox.py -v
git diff --check
```

라이브 실행은 로컬, 명시적, 선택적이며 비용이 들 수 있습니다. CI가 요구하지
않습니다. 오프라인 통과를 호스트 품질로 설명하지 마세요.

## 1.0.1 후속 실패 재현

동일 제품 HEAD `6cc1e39`를 대상으로 두 개의 새 local linked-worktree fixture에서
각각 Grok을 세 번 호출했습니다. 첫 후속 fixture는 두 새 세션 모두 전체 계획을
읽었고, 다음 main 기반 fixture는 CLI의 새 세션에서 이를 재현했습니다. 정확한
worker rules가 전달됐고 실제 성공 read 결과가 계획 본문을 반환했으므로 규칙 전달
누락으로 설명할 수 없습니다. worker의 clean DONE 보고에서 위반도 빠졌습니다.

두 fixture의 최종 앱 테스트는 각각 15개/14개 exit 0, worker 직접 커밋은 각각
3개였습니다. 기존 CRLF·주석 포함 sandbox TOML의 원문과 0640 권한은 매 호출 후
일치했고 journal도 제거됐습니다. 앱 성공과 별개로 역할 준수는 FAIL이며 독립 최종
리뷰도 부분 통과로 판정했습니다. 이전 최초 성공 표본은 이 후속 실패를 상쇄하지
않습니다. MCP 초기화 경고와 모델의 실제 MCP 도구 호출은 구분합니다.

초기 empty fixture는 Python 3.14 unittest의 NO TESTS RAN/exit 5를 미측정으로
기록합니다. shell wrapper exit 0 안의 실제 테스트 비0도 통과로 집계하지 않습니다.
로컬 raw provider trace/receipt는 저장소에 커밋하지 않습니다.

## 1.0.2 검증 절차

[행동 probe](../../../../tests/products/sddx/behavior-probes.md)의 모델 상속·High/XHigh,
위반 보고·도구 기록 누락·계획 링크 시나리오를 독립 native 문맥에서 실행합니다.
문구 포함 검사와 실제 행동 검사, 실제 Grok 실행은 서로 다른 증거입니다.

라이브에서는 동일한 함수 → 통제된 같은 세션 수정 → 새 CLI 작업을 사용합니다.
전체 계획은 fixture에 그대로 두어 읽지 않는 행동을 측정합니다. brief에 필요한
조건을 완결하고 worker 규칙과 dispatch 경계를 모두 전달합니다. 각 호출에서
실제 read와 shell 출력, scope deviations, 실제 테스트 exit, worker 커밋, session ID,
기존 sandbox 원문·권한 복원을 확인합니다. 리뷰는 같은 오케스트레이터 모델을
상속하며 effort를 따로 지정하고 선택 이유를 기록합니다. 역할 읽기 제한은 여전히
프롬프트 지침이며 OS 파일 접근 차단을 구현한 것은 아닙니다.

### 1.0.2 작성 중 발견한 검색 노출

첫 candidate로 세 단계를 실행했을 때 함수·resume은 역할 준수를 확인했지만,
CLI 작업이 대상 경로 없는 workspace `grep`으로 계획의 두 줄을 받아왔습니다.
ReadFile로 열지 않아도 검색 결과에 계획 내용이 반환되면 역할 FAIL입니다.
이번 worker는 이를 scope deviations에 공개하고 DONE_WITH_CONCERNS를 반환해
보고 개선은 확인됐습니다. 첫 candidate의 최종 앱 14 tests·커밋·복원은 성공했으며,
해당 실행 자체의 판정은 부분 통과로 유지합니다.

이를 근거로 brief의 구체적인 Search paths와 명시 파일 직접 읽기 순서를 추가했습니다.
파일 glob만으로는 디렉터리 경계가 정해지지 않는 점을 명시했습니다. controller의
증거 추출도 검색 결과를 포함한 모든 tool result를 보존하도록 보완한 별도 로컬
검증 도구를 사용합니다. 이는 제품에 새 실행 엔진을 추가한 것이 아닙니다.
이전 candidate의 소스 해시·원문과 실패 로그를 보존하고, 최종 문구로 세 단계를
새 worktree에서 다시 검증했습니다.

### 최종 문구의 실제 검증 결과

동일 seed에서 새 linked worktree를 만들어 Grok을 세 번 호출했습니다. 최종 runtime
스킬·worker rules·dispatch·helper 등 6개 파일의 SHA-256을 호출 전 고정하고 종료 뒤
일치를 확인했습니다. 함수는 RED exit 1 → GREEN 8 tests/exit 0, 통제된 같은 세션
수정은 RED 9 tests/6 failures/exit 1 → GREEN 9/exit 0, 새 CLI는 RED 6 tests/4
failures/exit 1 → 전체 GREEN 15/exit 0이었습니다. wrapper는 사용하지 않았습니다.
최종 독립 검사도 15 tests/exit 0, 전체 diff check exit 0, clean fixture였습니다.

세 worker 직접 커밋은 task 파일 5개에 한정됐습니다. 기존 sandbox 원문·0640 권한과
journal 제거, 실제 session 재사용·전환을 확인했습니다. 모든 tool 호출과 결과를
14/14, 12/12, 16/16으로 대조했으며 최종 세 호출에는 계획 내용 읽기나 workspace
내용 검색이 없었습니다. 필요한 파일 직접 읽기를 사용했으므로 검색 도구 자체의
경로 제한 기능이나 강제 파일 접근 차단을 입증한 것은 아닙니다.

마지막 worker는 root 파일명 목록 조회와 .gitignore 읽기를 DONE_WITH_CONCERNS로
공개했습니다. 독립 리뷰와 기존 컨트롤러 ruling은 이를 커밋·저장소 확인에 부수된
비차단 관측으로 수용했습니다. 실제 목록에는 계획 파일명도 있었으나 내용은
반환되지 않았습니다. 원본 보고와 Minor 절차 해석 사항을 보존합니다. 앞선 candidate의
실제 계획 내용 검색 노출은 FAIL로 유지합니다. 이번 개선 작업의 Grok 호출은 처음
3회와 최종 문구 3회를 합쳐 6회이며, 이들을 하나의 무실패 실행으로 합치지 않습니다.

실제 오케스트레이터는 실행 기록으로 확인한 gpt-6-astra/XHigh였으며, 모든 native
리뷰는 모델 인자를 생략해 상속했습니다. 국소 Task·재리뷰는 High, 전체 정책·증거
검토는 XHigh입니다. 특정 모델 고정 정책이 아닙니다. 최종 문구 반영 후 전체 공급자
없는 검증은 868 unittest와 추가 검사 exit 0이었으며, 이후 관측 결과 문서는
내용·링크·diff로 확인합니다.


## 1.0.2 검색 추가 검증과 남은 모호함

현재 main `2e9036a`의 문구로 새 Grok 세션 두 개에서 실제 내용 검색을 요구했습니다.
Native grep은 명시한 소스와 테스트 경로에 각각 검색해 본문 5줄·4줄을 반환했고,
shell rg는 공백을 포함한 두 경로를 따옴표로 지정해 파일 4개의 9줄을 반환했습니다.
계획과 범위 밖 메모에도 같은 검색어를 두었으나 해당 내용은 반환되지 않았습니다.
독립 테스트는 각각 12개·9개 exit 0, 도구 결과는 20/20·18/18을 대조했습니다.

파일명 조회의 분류는 모호했습니다. 이전 worker는 root 목록·ignore 규칙 조회를
우려사항으로 보고했고, 추가 shell 실행은 root 목록 조회 뒤 none을 보고했습니다.
독립 리뷰는 계획 본문 노출을 확인하지 못했지만 `any search`와 `content search`가
섞인 문구로는 파일명 조회·필요한 설정 직접 읽기의 보고 기준이 명확하지 않다고
판정했습니다. 당시 판정과 원본 보고는 수정 후에도 그대로 보존합니다.

## 1.0.3 파일명·설정 조회 명료화 검증

현재 worktree의 파일명 목록과 task에 필요한 ignore·빌드·테스트 설정 직접 읽기를
허용된 확인으로 명시합니다. 이 행동만으로는 scope concern이나 ruling을 요구하지
않고, 내용 검색의 경로 제한·계획 본문 금지·기록 부족 UNVERIFIED는 유지합니다.

독립 native 문맥에서 명료화 전·후 각각 5개 표본으로 파일명 조회, 설정 직접 읽기,
실제 계획 내용 노출, 도구 기록 부재를 분류합니다. 실제 Grok에서는 파일명·설정 조회와
native grep 또는 공백 경로의 shell rg를 한 작업에 함께 요구하고, 보고의 분류와
실제 결과를 대조합니다. 이 검증은 지시된 상황의 관측이며 자연 발생 준수율이나
OS 접근 차단을 입증하지 않습니다.


### 실제 결과

명료화 전 native 표본 5개는 파일명·설정 조회를 모두 AMBIGUOUS로, 수정 후 5개는
모두 명시적 ALLOWED / none으로 분류했습니다. 계획 내용 노출 FAIL과 도구 기록
부재 UNVERIFIED는 유지했습니다. 이 표본은 이전 응답을 주지 않은 별도 문맥이며
모델 준수율 통계는 아닙니다.

새 Grok 세션 두 개에 최종 worker rules와 dispatch 경계를 전달했습니다. 두 작업 모두
root 파일명 목록, .gitignore와 일반 테스트 설정 직접 읽기, 실제 내용 검색을 수행하고
이를 보고서에 기록한 뒤 DONE / Scope deviations: none으로 마쳤습니다. Native grep은
소스·테스트 경로를 각각 지정했고, shell rg는 공백을 포함한 두 경로를 따옴표로
지정했습니다. 계획·범위 밖 메모에도 검색어를 두었으나 본문 반환은 없었습니다.

Native 작업은 RED 10 tests/4 failures/exit 1 → GREEN 10/exit 0, shell 작업은
RED 8 tests/4 failures/exit 1 → GREEN 8/exit 0이었습니다. 독립 최종 테스트도 각각
10개·8개 exit 0이며, 설정에서 확인한 python3를 사용했습니다. 각 worker는 지정
소스와 신규 테스트 두 파일만 직접 커밋했고 Git 상태는 clean이었습니다.

두 작업의 도구 호출·결과는 각각 22/22이며, 기존 sandbox 원문·0640 권한 복원과
journal 제거를 확인했습니다. Native 작업은 .git을 디렉터리로 조회해 IsAFile 오류를
받은 뒤 worktree pointer 한 줄을 읽고 정상 Git 커밋 절차를 수행했습니다. Pointer
조회는 원본 보고에 포함됐고 ListDir 오류는 원본 도구 기록에서 확인했습니다. Pointer
대상의 파일 내용을 따라 읽지 않았습니다.

Runtime 6개 파일의 해시가 호출 전·후 동일했습니다. 전체 공급자 없는 검증은
868 unittest와 추가 검사 exit 0, 제품 검사는 24개 계약·45개 SDDx 테스트와 compile
exit 0이었습니다. 마지막 관측 결과 문서는 내용·링크·diff를 확인합니다. 이전 버전의
실패와 모호함 기록은 이 새 결과로 덮어쓰지 않습니다.
