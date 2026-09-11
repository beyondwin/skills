# sddx 호환성

이 문서는 SDDx의 오케스트레이터 호스트와 구현 worker 경계를 소유합니다.

현재 지원 호스트는 제품 목록의 `claude-code`, `codex`입니다. Cursor CLI와
Grok CLI는 구현 worker이지 호스트가 아닙니다. 지원 범위와 현재 측정 상태는
별개입니다. Claude.ai, Cowork,
Skills API 업로드, marketplace 게시, 클라우드 동기화는 지원하지 않습니다.

## 발견 경로

```text
skills/sddx/              저장소 원본
├─ ~/.agents/skills/sddx ─→ Codex
└─ ~/.claude/skills/sddx ─→ Claude Code
```

`~/.codex`와 `~/.grok`에 복사본을 만들지 마세요. Cursor와 Grok을
`supported_hosts`에 넣지 않습니다.

## 호출 구문

| 호스트 | 명시 호출 | 발견 경로 |
| --- | --- | --- |
| Codex | `$sddx` | `~/.agents/skills/sddx` |
| Claude Code | `/sddx` | `~/.claude/skills/sddx` |

`agents/openai.yaml`은 선택적 Codex 표시 메타데이터입니다. 런타임 필수 파일이
아닙니다.

## 공급자 없는 증거

필수 증거는 `python3 scripts/verify.py --skill sddx`입니다. 이 명령은
패키지 정체와 `resolve_backend.py` 픽스처만 증명합니다. 라이브 모델 품질과
지원 호스트 런타임 동등은 증명하지 않습니다.

## Grok linked worktree 경계

Grok linked worktree 실행은 Python 3.11+가 필요합니다. 임시 작업 프로파일은
`workspace`를 상속하고 현재 worktree의 실제 Git 디렉터리와 공용 Git
디렉터리에 쓰기 권한을 추가합니다. 이 권한은 worker가 커밋하는 데 필요하며,
worker가 저장소의 공유 Git 메타데이터를 쓸 수 있음을 뜻합니다. 준비 도구가
만든 설정과 복원 상태는 커밋하지 않고 worker 종료 뒤 정리합니다.

외부 스킬, MCP, 전체 계획을 읽지 말라는 제한은 worker prompt 지침입니다.
공급자 CLI의 초기화 경고가 없거나 역할 이탈이 불가능하다는 보장은 아닙니다.

## 측정 상태

| 오케스트레이터 호스트 | 구현 worker | 상태 | 관측 범위 |
| --- | --- | --- | --- |
| Codex | Grok CLI | measured | macOS 26.5.2, Python 3.14.7, Grok 1.0.25와 `grok-4.6` High에서 새 linked-worktree fixture의 실제 호출 3회 성공 |
| Codex | Cursor CLI | `not_measured` | 현재 설치 파일로 실행하지 않음 |
| Claude Code | Cursor 또는 Grok CLI | `not_measured` | 현재 설치 파일로 실행하지 않음 |

측정된 세 호출은 서로 다른 두 task와 첫 task의 통제된 same-session 수정으로 구성됐고,
각 호출에서 worker 직접 커밋, cleanup, native review를 확인했습니다. 최종 fixture 검사는
14 tests와 전체 diff 검사를 exit 0으로 마쳤습니다. tool trace에서 external skill·전체
계획 읽기, nested agent, MCP tool 호출이나 역할 위반은 관측되지 않았습니다. 다만 기존
host integration의 MCP startup 경고는 계속 나타났습니다. 이 결과는 해당 fixture와
버전의 범위 제한된 성공이며 모든 저장소나 실행의 보장이 아닙니다. 독립 최종 native
review도 Critical/Important/Minor 0건으로 accept했습니다. 재현 절차와 세부 exit code는
[테스트](testing.md)에 있습니다.

## 라이브 증거 경계

라이브 실행은 로컬, 명시적, 선택적이며 비용이 들 수 있습니다. CI가 요구하지
않습니다. 페이로드 계약 통과를 라이브 호출 증거로 설명하지 마세요.

## 새 호스트 지원

새 지원을 레지스트리와 공개 안내에 넣으려면 실제 관측 증거와 별도 지원
결정이 필요합니다. 지원 범위를 바꾸기로 결정한 경우에만 `products.toml`,
공개 안내, 테스트를 함께 고치세요. 공유 사용자 안내는
[호환성](../../../users/ko/compatibility.md)을 보세요.
