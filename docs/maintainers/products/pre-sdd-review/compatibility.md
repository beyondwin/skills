# pre-sdd-review 호환성

이 문서는 Pre-SDD Review의 measured-host 경계를 소유합니다.

## Supported host

Codex is supported because 측정된 계약이 local Git repository, 읽을 수 있는
design and plan files, repository inspection, isolated read-only reviewer를
요구하기 때문입니다. Every other host is `not_measured`; Markdown 패키지를
읽을 수 있어도 같은 reviewer isolation과 repository behavior를 입증하지
않았다면 지원으로 올리지 않습니다.

installer path, 비슷한 subagent 기능, provider-free fixture 통과만으로 지원을
추론하지 않습니다. 필요한 동작을 fresh-session smoke로 기록한 뒤에만
registry와 public documents에 호스트를 추가합니다.

### Host matrix

| Host | Status |
| --- | --- |
| `claude-code` | `not_measured` |
| `codex` | `supported` |

## Evidence limit

필수 provider-free command는 [testing](testing.md)에 있습니다. 이 명령은
deterministic package and instruction contracts만 증명하며 live review quality나
cross-host equivalence를 증명하지 않습니다. 선택적 live check는 explicit,
local, non-sensitive 경계를 유지합니다.
