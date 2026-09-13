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
정의이고, skills-dir 플러그인 로딩을 통해 전달됩니다. 로딩은 이전 버전의 제품
파일로 한 번 확인했을 뿐이며 `2.0.0`에서는 다시 확인하지 않았습니다. `2.0.0`의
정의 로딩, 서브에이전트에 실제 적용된 effort, `disallowedTools`의 실제 차단 여부는
모두 `not_measured`입니다.

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

## 2.0.0 측정 상태

이 표는 `2.0.0` 설치 파일만 다룹니다. 네 조합 가운데 실제 공급자를 호출한 것은
하나도 없습니다. 이 버전의 검증은 오프라인 검사뿐입니다.

| 오케스트레이터 호스트 | 구현 worker | `2.0.0` 실제 실행 | 근거 |
| --- | --- | --- | --- |
| Claude Code | Cursor CLI | `not_measured` | 이 버전으로 호출하지 않음 |
| Claude Code | Grok CLI | `not_measured` | 이 버전으로 호출하지 않음 |
| Codex | Cursor CLI | `not_measured` | 이 버전으로 호출하지 않음 |
| Codex | Grok CLI | `not_measured` | 이 버전으로 호출하지 않음 |

같은 기준으로 `not_measured`인 항목이 더 있습니다.

| 항목 | `2.0.0` 상태 | 근거 |
| --- | --- | --- |
| 실제 Cursor 승인 동작 | `not_measured` | `--auto-review`·`--sandbox` 선언만 확인했고 실제 승인 흐름은 호출하지 않음 |
| 실제 Cursor OS 격리 | `not_measured` | `--sandbox enabled`는 선언 확인이며 실제 격리 범위를 측정하지 않음 |
| Claude Code agent 정의 로딩 | `not_measured` | `2.0.0` 파일로 `claude -p --agent sddx-reviewer-xhigh` 확인을 수행하지 않음 |
| 모델이 실제 적용한 effort | `not_measured` | 요청·설정 effort만 기록하며 적용값을 확인할 경로가 없음 |
| Windows argv 전송 | `not_measured` | `.cmd` 왕복 테스트는 `skipUnless(os.name == "nt")`이고 개발 macOS 체크아웃에서 skip됨 |

Windows 행은 저장소의 `windows-latest`/`windows-portable` CI 행에서 실제로
실행됩니다. `sddx-contract`는 `WINDOWS_EXCLUDED_STAGES`
(`scripts/lib/verification.py:14`)에 없습니다. 다만 그 행은 push에서만 돌고 이
브랜치는 아직 push하지 않았으므로, 지금 시점의 증거는 없습니다. macOS 로컬 검사를
Windows 증거로 쓰지 않습니다.

## 알려진 플랫폼·증거 한계

Windows의 npm 방식 `.cmd` 셰임 실행은 launch failure로 기록됩니다. worker 규칙과
Cursor dispatch 텍스트는 여러 줄인데 `cmd.exe` 명령줄은 줄바꿈을 담을 수 없습니다.
의도한 선택이며, 대안은 이전 전송 방식의 조용한 인자 훼손이었습니다.

Grok의 `--rules`는 시도 디렉터리에 보존되지 않습니다. 규칙 본문이 명령줄로만
전달되고 스펙이 시도 디렉터리를 정확히 여섯 파일로 고정하므로,
`skills/sddx/references/worker-prompt.md`를 고치면 과거 Grok 시도를 저장된 증거만으로
그대로 재현할 수 없습니다. 이는 여섯 파일 계약이 강제한 결과이지 누락이 아닙니다.

## 1.0.x 관측 기록

아래 관측은 모두 `1.0.x` 설치 파일의 기록이며 `2.0.0`의 증거가 아닙니다. 당시
`Codex × Grok CLI`는 1.0.3에서 실제 2회 호출, 10/8 tests, 파일명·설정 조회의 none
보고와 경로 지정 검색을 확인했습니다. 같은 시점의 `Codex × Cursor`와
`Claude Code × Cursor 또는 Grok`은 그때도 `not_measured`였습니다.

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
Claude Code의 모델·effort 대응과 Cursor event trace는 그때도 실제 실행
미측정이었습니다. 재현 절차와 버전별 관측은 [테스트](testing.md)에 있습니다.

## 라이브 증거 경계

라이브 실행은 로컬, 명시적, 선택적이며 비용이 들 수 있습니다. CI가 요구하지
않습니다. 페이로드 계약 통과를 라이브 호출 증거로 설명하지 마세요.

## 새 호스트 지원

새 지원을 레지스트리와 공개 안내에 넣으려면 실제 관측 증거와 별도 지원
결정이 필요합니다. 지원 범위를 바꾸기로 결정한 경우에만 `products.toml`,
공개 안내, 테스트를 함께 고치세요. 공유 사용자 안내는
[호환성](../../../users/ko/compatibility.md)을 보세요.
