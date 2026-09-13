# SDDx 오케스트레이션 개선 조사

상태: 설계 근거. 2026-09-13에 조사했으며 제품 구현과 라이브 모델 실험은 하지 않았다.

연결 문서: [설계 스펙](2026-09-13-sddx-execution-design.md), [구현 계획](2026-09-13-sddx-implementation-plan.md).

## 결론

**기존 SDD 위에 작은 태스크 발췌 도구와 worker 실행·조회 도구를 두는 안을 권한다.** 현재 상태는 기존 원장의 상단 한 곳에서 갱신하고, 원시 로그는 별도 파일로 보존한다. 실행·재개에는 명시적인 식별자를 쓰고, 같은 조건에서 해결되지 않는 오류를 다시 실행하지 않는다.

조사한 프로젝트의 전체 프레임워크를 도입할 이유는 없다. 그래프 스케줄러, 상태 DB, 자동 재실행, LLM을 이용한 로그 요약은 이번 문제보다 큰 유지보수 범위를 만든다. Superpowers 원본과 기존 리뷰 절차도 그대로 둔다.

## 세션에서 확인한 문제

사용자가 지정한 여섯 작업의 루트 기록, 관련 원장, 브리프, 실행 스크립트를 대조했다. 모든 자식 작업의 전체 로그를 전수 감사한 것은 아니다. 비공개 원문과 공급자 로그는 이 저장소에 넣지 않는다. 다음은 원문을 옮기지 않은 조사 결과다.

| 항목 | 확인한 사실 | 설계에 반영할 판단 |
| --- | --- | --- |
| 태스크 발췌 | 설치된 숫자 전용 추출기로 `Task 1`은 성공했고 `Task P1`, `Task U1`, `Task F1`, `S01`, `P1-T1` 합성 입력은 exit 3이었다. 새 작업 다섯 곳에서 수동 발췌나 제목 변환이 있었다. | 제목을 바꾼 계획 사본 대신 정확한 제목 발췌를 제공한다. |
| 현재 상태 | 한 원장은 약 22.3만 자였고 별도 현재 상태·복구 문서도 각각 약 7.2만/7.9만 자였다. 상단 backend와 후속 실행의 backend가 달랐다. | 현재 상태를 추가하지 말고 교체한다. 이력과 현재 사실의 역할을 나눈다. |
| 로그 조회 | 세 명령의 출력이 각각 154,571자, 280,038자, 343,738자였다. 여섯 작업에서 실행·조회용 보조 Python을 따로 작성했다. | 공통 실행 도구와 크기가 제한된 조회를 제공한다. 원시 증거는 삭제하지 않는다. |
| Cursor 실행 | 현재 resolver는 `--print --force --trust`를 반환한다. 한 작업에서 `--auto-review --sandbox enabled`로 보완한 판단이 제품에 반영되지 않았다. | 지원 기능을 확인해 실행 조합을 제품에서 정한다. 실제 격리 성공은 별도로 측정한다. |
| backend 질문 | 명시적 Grok 요청 네 건은 picker를 건너뛰었다. 지정 또는 재개 기록이 없었던 두 건은 한 번 물었다. | 반복 질문 결함으로 과장하지 않는다. 자연어 지정과 현재 실행의 선택을 공식 입력으로 인정한다. |
| 여러 문서 | spec+plan은 계획 두 개가 아니다. 여러 단계의 실행 순서가 명시된 사례와, 병행 작업의 실제 소유권 충돌을 확인한 질문도 있었다. | 참고 문서와 실행 계획을 구분한다. 순서와 소유권이 불명확할 때만 질문한다. |
| 402 | 소진을 인지한 다섯 루트 작업에서 사용자 전환 지시 전 새 Grok 실행을 찾지 못했다. | 반복 재시도를 확인된 결함으로 쓰지 않는다. 같은 조건의 재시도 금지는 예방 규칙으로 명확히 한다. |
| 리뷰 | 여섯 루트의 확인 가능한 세션 effort는 이미 XHigh였다. 정의 부재 문구가 반복됐다. 리뷰가 실제 코드 결함을 찾아낸 사례도 있었다. | 상속 상태를 먼저 확인하고 제약은 한 번 기록한다. 리뷰를 일괄 생략하지 않는다. |

원시 세션 파일 크기는 약 41–129 MB였으나 중복 이벤트와 압축 기록을 포함한다. 이를 모델 입력 토큰, 청구 비용, 낭비율로 환산하지 않는다. 추출 실패가 모든 `NEEDS_CONTEXT` 라운드의 원인이라는 인과도 확인되지 않았다.

현재 제품 기준은 `db853c0`의 [SDDx](../../skills/sddx/SKILL.md), [resolver](../../skills/sddx/scripts/resolve_backend.py), [dispatch](../../skills/sddx/references/dispatch.md)다. 파일명 조회와 필요한 설정 읽기의 허용은 이미 현행 규칙에 있으므로 새 기능으로 중복 구현하지 않는다.

## 오픈소스 11개 비교

공식 저장소의 조사 시점 커밋을 고정하고 관련 구현을 읽었다. 아래 링크는 브랜치 최신값이 아니라 그 커밋의 코드다. 프로젝트 수는 관련성이 있는 구현을 비교한 수이며, 이들을 실행하거나 성능 순위를 매겼다는 뜻이 아니다. '적용' 열은 SDDx에 대한 설계 판단이다.

| 프로젝트 / 확인 지점 | 실제 방식 | SDDx 적용과 제외 |
| --- | --- | --- |
| **OpenHands SDK** — [EventLog.append](https://github.com/OpenHands/software-agent-sdk/blob/c37007429be8b4465a83487dc1fd0914df0ea734/openhands-sdk/openhands/sdk/conversation/event_store.py#L188-L238) | 이벤트에 ID를 부여하고 저장 시 중복 ID와 없는 부모를 거절한다. 저장 기록을 인덱스로 조회한다. | 시도마다 새 디렉터리를 만들고 이전 증거를 덮어쓰지 않는다. 이벤트 저장소·부모 트리·분산 잠금은 도입하지 않는다. |
| **pi** — [buildContextEntries](https://github.com/badlogic/pi-mono/blob/71dca871bc80b6bc97be37f0ca3189399d651fff/packages/coding-agent/src/core/session-manager.ts#L411-L455), [session format](https://github.com/badlogic/pi-mono/blob/71dca871bc80b6bc97be37f0ca3189399d651fff/packages/coding-agent/docs/session-format.md) | 저장된 세션 이력에서 현재 경로와 마지막 compaction 이후의 문맥을 따로 구성한다. | 원본 증거와 재개 시 읽을 현재 상태를 분리한다. 세션 트리나 LLM compaction은 가져오지 않는다. |
| **Aider** — [get_repo_map](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/repomap.py#L103-L146), [공식 설명](https://aider.chat/docs/repomap.html) | 전체 저장소 대신 관련 파일의 정의·참조를 정해진 문맥 예산에 맞춰 제공한다. | worker에 현재 태스크와 필요한 제약·참조만 준다. 심볼 그래프·랭킹·토큰 예측기는 필요 없다. |
| **Goose** — [ToolPairCompactionOperation](https://github.com/block/goose/blob/50666ae0b9a51e260b52b7efbab2e4e020346e94/crates/goose/src/agents/state_machine/ops_tool_pair_compaction.rs#L67-L160) | 도구 요청·응답을 ID로 묶는다. 짝이나 함께 담긴 호출들의 대응이 불완전하면 요약을 건너뛴다. | 잘린 미리보기를 완전한 실행 증거로 판정하지 않는다. 호출·결과 원문을 함께 확인한다. 자동 의미 요약은 제외한다. |
| **LangGraph** — [put_writes](https://github.com/langchain-ai/langgraph/blob/e539ac122f4126f6dd850581c1494948cf620e31/libs/checkpoint/langgraph/checkpoint/memory/__init__.py#L467-L504) | thread/checkpoint/task 식별자로 쓰기를 연결하고 같은 쓰기의 중복 저장을 건너뛴다. | 태스크 ID, 시도 ID, 공급자 세션 ID를 구분한다. 명시적 재개와 증거 연결만 채택한다. 체크포인트 DB와 실행 재생은 제외한다. |
| **AutoGen** — [BufferedChatCompletionContext](https://github.com/microsoft/autogen/blob/027ecf0a379bcc1d09956d46d12d44a3ad9cee14/python/packages/autogen-core/src/autogen_core/model_context/_buffered_chat_completion_context.py#L16-L40), [team state](https://github.com/microsoft/autogen/blob/027ecf0a379bcc1d09956d46d12d44a3ad9cee14/python/packages/autogen-agentchat/src/autogen_agentchat/teams/_group_chat/_base_group_chat.py#L748-L834) | 제한된 최근 메시지 뷰를 제공하며, 저장·복원 상태를 별도 인터페이스로 다룬다. 실행 중 상태 복원은 거절한다. | 상태 조회와 실행을 분리하고 조회가 worker를 재시작하지 않게 한다. 팀 런타임이나 메시지 버퍼는 추가하지 않는다. |
| **smolagents** — [ActionStep](https://github.com/huggingface/smolagents/blob/30bb1161095dbae2271e6bc3cc4c219cc3897a57/src/smolagents/memory.py#L50-L164) | 도구 호출, 관측, 오류, 모델 출력을 구분해 저장하고 모델에 보낼 메시지를 따로 만든다. | 프로세스 exit, worker 보고, 실제 테스트 결과, 리뷰 판정을 구분한다. 실패마다 재시도를 유도하는 문구는 가져오지 않는다. |
| **OpenAI Agents SDK** — [streaming](https://github.com/openai/openai-agents-python/blob/fbd2dbcaaf74a2c447c6d3fa9d5645d83fd7e292/docs/streaming.md#L1-L94) | 원시 스트림과 완료된 항목 이벤트가 별도다. 마지막 표시 토큰 이후에도 저장 등의 후처리가 남을 수 있다. | 마지막 문장이나 보고서 생성만으로 프로세스 종료를 판정하지 않는다. CLI의 실제 종료를 기다린다. SDK는 의존성으로 넣지 않는다. |
| **Temporal** — [RetryPolicy](https://github.com/temporalio/sdk-python/blob/ab25ed693f7ec77589346e66c98db299a8c9c9fe/temporalio/common.py#L37-L60), [공식 재시도 정책](https://docs.temporal.io/encyclopedia/retry-policies) | 재시도 대상과 비재시도 오류를 구분한다. SDK의 기본 최대 시도 수 0은 무제한을 뜻한다. | 잔액·인증·권한처럼 조건 변경이 필요한 오류를 구분하는 원칙만 적용한다. 무제한 재시도나 workflow 실행기는 채택하지 않는다. |
| **Prefect** — [handle_retry](https://github.com/PrefectHQ/prefect/blob/9795fc271ce582dbe94165cdc43a9119bc3828f6/src/prefect/task_engine.py#L660-L702) | 남은 재시도 횟수와 재시도 조건을 함께 확인하고, 재시도 상태를 명시한다. | 기존 SDD 수정 횟수를 이어받는다. backend 전환이나 기록 정정으로 횟수·미해결 지적을 초기화하지 않는다. 별도 retry 엔진은 만들지 않는다. |
| **PydanticAI** — [deferred tools](https://github.com/pydantic/pydantic-ai/blob/5cbacfc8f86d653baa0ca2e31970cbf4f0fcec95/docs/deferred-tools.md#L315-L336) | 외부에서 수행한 도구 결과를 원래 호출 ID에 연결해 후속 실행에 전달한다. | host 전용 검증을 브리프에 미리 지정하고 결과를 해당 태스크에 돌려준다. 별도 승인 서비스나 새로운 worker 상태는 만들지 않는다. |

## 채택할 최소 변환

1. **전체 문맥 대신 필요한 입력:** 정확한 태스크 본문을 발췌하고 컨트롤러가 전역 제약·선행 인터페이스·검증 담당을 보충한다. 추출기가 의미 판단까지 맡지 않는다.
2. **이력과 현재 상태 분리:** `progress.md` 상단의 현재 상태만 교체한다. 실행 원문은 시도별 파일에 남긴다. 현재 상태용 DB나 두 번째 복구 원장을 만들지 않는다.
3. **실행과 조회 분리:** 공통 도구는 CLI 실행, 파일 저장, 실제 프로세스 exit, 제한된 로그 구간 조회까지만 담당한다. 조회만으로 테스트·역할·코드 PASS를 만들지 않는다.
4. **명시적 연결:** 시도 디렉터리는 재사용하지 않는다. 공급자 세션 ID가 확인될 때만 `--resume`에 전달하고, 없으면 기존 SDD의 새 worker + 이전 보고서 방식으로 이어간다.
5. **조건이 필요한 오류는 멈춤:** helper의 자동 재시도는 0회다. 컨트롤러가 실제 오류와 다음 조건을 기록한다. backend 전환은 사용자 지정이 있을 때만 한다.

의도적으로 첫 구현에서 제외하는 것은 공급자 이벤트 전체를 공통 스키마로 바꾸는 파서다. Cursor/Grok의 전체 출력 형식을 따라가며 tool/test 판정을 자동화하면 도우미가 또 하나의 오케스트레이터가 된다. 먼저 원문 저장과 byte 위치 기반 조회를 공통화한다. 자동 call-ID 인덱스가 필요한지는 적용 후에도 수동 조회가 반복되는지 보고 판단한다.

## Cursor 기능 확인의 한계

설치된 Cursor `2026.09.10-fd3934a`의 읽기 전용 `--help`에서 `--auto-review`, `--sandbox enabled|disabled`, `--output-format stream-json`을 확인했다. Auto-review는 분류기에 따라 일부 도구를 실행하고 나머지는 승인을 요청할 수 있다. 이 조사에서 실제 worker를 실행하지 않았다.

[공식 출력 문서](https://cursor.com/docs/cli/reference/output-format)는 `stream-json`이 NDJSON이며 오류 시 terminal result 없이 비0 exit로 끝날 수 있다고 설명한다. [공식 파라미터 문서](https://cursor.com/docs/cli/reference/parameters)의 조사 시점 내용에는 로컬 help의 `--auto-review` 설명이 없었다. 따라서 웹 문서만으로 지원 기능을 고정하지 않고 로컬 CLI identity와 help를 확인한다. 이 차이는 실제 headless 승인 동작과 OS 격리 검증을 생략할 근거가 아니다.

## 검증과 미측정

- 세션 조사 때 현재 제품의 공급자 없는 검사는 통과했다. 이는 개선안의 성공 증거가 아니라 기존 검사에 제목 호환성 문제가 드러나지 않는다는 근거다.
- 오픈소스는 공식 저장소의 고정 커밋에서 관련 코드를 읽었다. 외부 코드나 패키지를 제품에 복사·설치하지 않았다.
- 시간·비용·토큰 감소율, 두 호스트의 실제 모델 동작, 새 Cursor 조합의 실제 격리는 `not_measured`다.
- 개선 성공 기준은 임의의 감소율 대신 발췌 우회 제거, 실행 스크립트 재작성 제거, 현재 상태의 일치, 조회 크기 상한, 자동 재시도 0회로 정한다.
