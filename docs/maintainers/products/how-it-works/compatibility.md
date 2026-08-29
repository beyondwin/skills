# how-it-works 호환성

현재 지원 호스트는 제품 레지스트리의 `codex`, `claude-code`입니다. 이 두 호스트만 로컬 또는 저장소 기준으로 지원합니다. Grok는 `--max-turns 1` 라이브 smoke에서 필수 산출을 내지 못해 지원하지 않습니다. Cursor는 이 하네스에 Computer Use(`node_repl` / `@oai/sky`)가 없어 실행하지 못했고 지원하지 않습니다. Claude.ai, Cowork, Skills API 업로드, marketplace 게시, 클라우드 동기화는 지원하지 않습니다. 호스트마다 따로 복사하지 마세요.

## 발견 경로

```text
skills/how-it-works/              저장소 원본
├─ ~/.agents/skills/how-it-works ─→ Codex
└─ ~/.claude/skills/how-it-works ─→ Claude Code
```

`ln -s`는 이미 있는 대상을 덮어쓰지 않고 실패합니다. `.codex`와 `.grok` 중복 링크를 다시 만들지 마세요.

## 호출 구문

| 호스트 | 명시 호출 | 발견 경로 |
| --- | --- | --- |
| Codex | `$how-it-works` | `~/.agents/skills/how-it-works` |
| Claude Code | `/how-it-works` | `~/.claude/skills/how-it-works` |

`agents/openai.yaml`은 선택적 Codex 표시 메타데이터이며 런타임 필수 파일이 아닙니다.

## 필요한 호스트 능력

- 로컬 Agent Skills 디렉터리 설치와 `SKILL.md` 파일 접근
- GitHub-flavored markdown과 mermaid 소스를 채팅으로 반환하는 능력
- mermaid 렌더러는 필수가 아닙니다. 렌더러가 없어도 홉 목록이 읽혀야 합니다

## 공급자 없는 증거

필수 증거는 `python3 scripts/verify.py --skill how-it-works`입니다. `tests/products/how-it-works/cases.json`과 `tests/products/how-it-works/test_contract.py`는 형태와 페이로드 계약만 증명합니다. 라이브 모델 품질은 증명하지 않습니다.

## 라이브 증거 경계

라이브 실행은 로컬, 명시적, 선택적이며 비용이 들 수 있습니다. CI가 요구하지 않습니다. 페이로드 계약 통과를 라이브 호출 증거로 설명하지 마세요. 사용자 주제, 공급자 트랜스크립트, 비공개 로그는 커밋하지 않습니다.

현재 smoke 메타데이터는 `tests/products/how-it-works/live/smoke-record.json`에만 있습니다. 기록은 호스트, 클라이언트 버전, 날짜, 케이스 판정만 남깁니다. 2026-08-28 실행에서 Codex `0.150.0`과 Claude Code `2.1.247`은 `supported`입니다. Grok `1.0.5`는 `unsupported`입니다. Cursor `3.17.21`은 Computer Use 부재로 `not_measured`이며 지원이 아닙니다.

운영 절차는 [테스트](testing.md)와 `tests/products/how-it-works/live/README.md`를 따릅니다.

## 새 호스트 지원

새 지원을 레지스트리와 공개 안내에 넣으려면 같은 빌드에서 다음 네 가지 smoke가 통과해야 합니다.

1. 스킬 발견
2. 명시 호출
3. 의도한 암묵 호출과 near-miss 비호출
4. 출력 계약(마크다운, mermaid 소스, 번호 있는 홉 목록)

기록이 없으면 그 호스트는 지원이 아닙니다. `products.toml`, 공개 안내, 테스트를 함께 고치세요. 공유 사용자 안내는 [호환성](../../../users/ko/compatibility.md)을 보세요.
