# sddx 호환성

이 문서는 SDDx의 오케스트레이터 호스트와 구현 worker 경계를 소유합니다.
호스트는 스킬을 실행하는 프로그램이고, worker는 구현만 맡는 외부 CLI입니다.

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

`agents/openai.yaml`은 Codex 표시 메타데이터이며 선택적입니다. 런타임 필수
파일이 아닙니다.
`agents/claude-code/sddx-reviewer-xhigh.md`는 성격이 다릅니다. Claude Code 런타임
정의이고, skills-dir 플러그인 로딩을 통해 전달됩니다. 로딩은 배포되는 제품 파일로
한 번 확인했으며, 서브에이전트에 실제 적용된 effort와 `disallowedTools`의 실제
차단 여부는 모두 `not_measured`입니다.

사용자 프로젝트의 `.claude/agents/`에 같은 이름의 정의가 있으면 그쪽이 우선합니다.
제품 접두사를 붙인 이름 외에 방어 수단이 없습니다.

## 공급자 없는 증거

필수 증거는 `python3 scripts/verify.py --skill sddx`입니다. 이 명령은
패키지 정체, resolver 픽스처, sandbox 준비·복원을 검사합니다. 라이브 모델 품질과
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
| Codex | Grok CLI | measured | 1.0.3: 실제 2회, 10/8 tests, 파일명·설정 조회의 none 보고와 경로 지정 검색 확인; 이전 버전 실패 별도 보존 |
| Codex | Cursor CLI | `not_measured` | 현재 설치 파일로 실행하지 않음 |
| Claude Code | Cursor 또는 Grok CLI | `not_measured` | 현재 설치 파일로 실행하지 않음 |

1.0.1 최초 fixture에서는 세 호출, 최종 14 tests, 역할 위반 미관측을 확인했습니다.
이후 독립된 두 fixture에서 각각 세 호출을 다시 측정했으며 최종 15/14 tests와
커밋·복원은 성공했지만, 새 세션의 전체 계획 읽기가 재현됐습니다. 기존 sandbox
설정의 바이트와 0640 권한도 후속 실제 호출마다 복원됐습니다. 이전 성공 표본을
현재의 전면 통과나 역할 준수 보장으로 해석하지 않습니다.

1.0.2는 brief 경계·보고·도구 기록 판정과 리뷰 모델 상속을 보완합니다.
리뷰어는 호스트 네이티브로 현재 오케스트레이터 모델을 따르고, High/XHigh를 따로
지정합니다. 호스트에서 해당 제어를 지원하지 않으면 한계를 보고합니다.
최종 문구의 새 세 호출은 15 tests와 직접 커밋·재개·복원을 통과했고 계획 내용
노출은 관측되지 않았습니다. 파일명·ignore 규칙 확인에 대한 마지막 worker의
DONE_WITH_CONCERNS는 실제 기록과 독립 리뷰에 근거한 기존 ruling으로 수용했습니다.
검색 노출이 있었던 초기 candidate는 별도 실패 기록으로 남습니다.
1.0.3은 파일명 목록·작업에 필요한 설정 직접 읽기의 허용과 none 보고 기준을
명시합니다. 새 두 세션에서 실제 해당 조회와 native/shell 내용 검색을 함께 수행하고,
각각 10개·8개 테스트 및 설정 복원을 확인했습니다. 두 원본 보고는 허용된 조회를
공개하고도 불필요한 scope concern 없이 DONE/none이었습니다. 이는 해당 fixture의
관측이며 일반적인 준수율이나 강제 파일 접근 차단을 증명하지 않습니다.
Claude Code의 모델·effort 대응과 Cursor event trace는 실제 실행 미측정입니다.
재현 절차와 버전별 관측은 [테스트](testing.md)에 있습니다.

## 라이브 증거 경계

라이브 실행은 로컬, 명시적, 선택적이며 비용이 들 수 있습니다. CI가 요구하지
않습니다. 페이로드 계약 통과를 라이브 호출 증거로 설명하지 마세요.

## 새 호스트 지원

새 지원을 레지스트리와 공개 안내에 넣으려면 실제 관측 증거와 별도 지원
결정이 필요합니다. 지원 범위를 바꾸기로 결정한 경우에만 `products.toml`,
공개 안내, 테스트를 함께 고치세요. 공유 사용자 안내는
[호환성](../../../users/ko/compatibility.md)을 보세요.
