# how-it-works 호환성

현재 지원 호스트는 제품 목록의 `codex`, `claude-code`입니다. 이 두
호스트만 로컬 또는 저장소 기준으로 지원합니다. 지원 범위와 현재 측정 상태는
별개이며, 2.0.0의 실제 실행 증거는 `not_measured`입니다. Grok는 과거
`--max-turns 1` 라이브 실행 확인에서 필수 산출을 내지 못해 지원하지 않습니다.
Cursor는 과거 실행 도구에 Computer Use(`node_repl` / `@oai/sky`)가 없어
미측정이었으며 지원 대상이 아닙니다. Claude.ai, Cowork, Skills API 업로드, marketplace 게시,
클라우드 동기화는 지원하지 않습니다. 호스트마다 따로 복사하지 마세요.

## 발견 경로

```text
skills/how-it-works/              저장소 원본
├─ ~/.agents/skills/how-it-works ─→ Codex
└─ ~/.claude/skills/how-it-works ─→ Claude Code
```

제품 README의 일회성 Python 블록은 source와 target을 인자로 받습니다. source의
실재와 `SKILL.md`를 먼저 검사한 뒤 링크를 만들며, 같은 링크의 반복 설치는
`already linked`로 성공합니다. 다른 링크, 깨진 링크, 파일, 디렉터리, 검사 뒤
나타난 target은 자동 교체하지 않습니다. `.codex`와 `.grok` 중복 링크를 다시 만들지
마세요. 실제 HOME 대신 공백이 있는 임시 경로에서 설치 계약을 검증합니다.

## 호출 구문

| 호스트 | 명시 호출 | 발견 경로 |
| --- | --- | --- |
| Codex | `$how-it-works` | `~/.agents/skills/how-it-works` |
| Claude Code | `/how-it-works` | `~/.claude/skills/how-it-works` |

`agents/openai.yaml`은 선택적 Codex 표시 메타데이터입니다. 런타임 필수 파일이
아닙니다.

## 필요한 호스트 능력

- 로컬 Agent Skills 디렉터리 설치와 `SKILL.md` 파일 접근
- GitHub-flavored markdown과 mermaid 소스를 채팅으로 반환하는 능력
- mermaid 렌더러는 필수가 아닙니다. 렌더러가 없어도 홉 목록이 읽혀야 합니다

## 공급자 없는 증거

필수 증거는 `python3 scripts/verify.py --skill how-it-works`입니다.
`tests/products/how-it-works/cases.json`과
`tests/products/how-it-works/test_contract.py`는 형태와 페이로드 계약만
증명합니다. 라이브 모델 품질은 증명하지 않습니다.

## 라이브 증거 경계

라이브 실행은 로컬, 명시적, 선택적이며 비용이 들 수 있습니다. CI가 요구하지
않습니다. 페이로드 계약 통과를 라이브 호출 증거로 설명하지 마세요. 사용자
주제, 공급자 트랜스크립트, 비공개 로그는 커밋하지 않습니다.

보존된 과거 smoke 메타데이터는 `tests/products/how-it-works/live/smoke-record.json`에만
있습니다. schema 1 원본 바이트를 유지하며, 결속 상태는 `historical-unbound`입니다.
기록은 호스트, 클라이언트 버전, 날짜, 케이스 판정만 남겼고 당시 model과 payload
hash를 추측해 추가하지 않습니다.
2026-08-28 실행에서 Codex `0.150.0`과 Claude Code `2.1.247`은 `supported`입니다.
Grok `1.0.5`는 `unsupported`입니다. Cursor `3.17.21`은 Computer Use 부재로
`not_measured`이며 지원이 아닙니다. 이 과거 판정은 현재 payload의 실행 증거가 아닙니다.

새 schema 2 기록은 실제 관측한 버전·payload hash·model·호스트·클라이언트·실행기·날짜와
케이스별 invocation, 다섯 관측 차원을 분리합니다. `fence`와 `hop_ids`의 `lexical`
검사로는 `skill_loading`, `mermaid_syntax`, `meaning`을 통과로 올릴 수 없습니다.
관측 출처가 없으면 `not_measured/not_run`이고 model을 모르면 `null`입니다.
`current-bounded`는 현재 버전/hash와 메타데이터가 일치한다는 뜻으로, 실제 실행이나
전체 품질을 인증하지 않습니다. `host_event`, `parser`/`renderer`, `semantic_review`도
운영자가 제출한 관측 방식 선언이며 순수 결속 함수가 그 실행 사실을 인증하지 않습니다.
새 실제 기록은 이 구현에서 만들지 않습니다.

운영 절차는 [테스트](testing.md)와 `tests/products/how-it-works/live/README.md`를
따릅니다.

## 새 호스트 지원

새 지원을 레지스트리와 공개 안내에 넣으려면 같은 빌드에서 다음 네 가지
smoke가 통과해야 합니다.

1. 스킬 발견
2. 명시 호출
3. 의도한 암묵 호출과 near-miss 비호출
4. 출력 계약(마크다운, mermaid 소스, 번호 있는 홉 목록)

새 호스트는 실제 관측 증거와 별도 지원 결정 없이 추가하지 않습니다. 기존 Codex와
Claude Code 지원은 현재 미측정 때문에 자동으로 삭제하지 않습니다. 지원 범위를
바꾸기로 결정한 경우에만 `products.toml`, 공개 안내, 테스트를 함께 고치세요. 공유 사용자 안내는
[호환성](../../../users/ko/compatibility.md)을 보세요.
