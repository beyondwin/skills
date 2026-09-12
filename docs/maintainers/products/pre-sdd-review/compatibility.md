# pre-sdd-review 호환성

이 문서는 Pre-SDD Review의 측정된 호스트 경계를 소유합니다.

## 지원 호스트

지금은 Codex만 지원합니다. 측정된 계약이 로컬 Git 저장소, 읽을 수 있는 설계와
계획 파일, 저장소 조사, 격리된 읽기 전용 검토자를 요구하기 때문입니다.
다른 호스트는 모두 `not_measured`입니다.
폴더 모양이 같다고 같은 검토자 격리와 저장소 동작이 있는 것은 아닙니다.
입증하기 전에는 지원으로 올리지 않습니다.

설치 경로, 비슷한 서브에이전트 기능, 공급자 없는 픽스처 통과만으로 지원을
추론하지 않습니다. 필요한 동작을 새 세션 smoke로 기록한 뒤에만 레지스트리와
공개 문서에 호스트를 추가합니다.

### Host matrix

| Host | Status |
| --- | --- |
| `claude-code` | `not_measured` |
| `codex` | `supported` |
| `grok` | `not_measured` |

## 기록기 호환성

기록기 이식은 의미 호스트 표와 별개입니다. Codex, Claude Code, Cursor, Grok는
로드된 스킬 루트의 같은 `evidence/evidence.py`를 쓰고, 데이터 루트
`~/.pre-sdd-review/` 하나를 공유합니다. 기록기 통과가 그 호스트의 독립 읽기
전용 검토나 의미 품질을 증명하지는 않습니다.

### CLI matrix

| Runtime | Status | Evidence boundary |
| --- | --- | --- |
| macOS / Python 3.11+ | `verified` | provider-free evidence suite |
| Linux / Python 3.11+ | `not_measured` | no native run evidence |
| Windows / Python 3.11+ | `not_measured` | schema 3 mutations require POSIX `fcntl.flock`; read-only commands are not a native support claim |

다른 OS의 `windows-portable` 실행은 단계 선택만 확인합니다. native 지원으로
올리지 않습니다.

schema 3 변경 명령은 `.identity.lock`과 `locks/<run-id>.lock`에 OS 파일
locking을 씁니다. `show`, `summary`, `--version`은 읽기 전용이며 그 lock을
잡지 않습니다. 이 구분으로 native Windows 변경 지원을 주장하거나 Windows를
`not_measured` 위로 올리지 않습니다.

## 증거 한계

필수 공급자 없는 명령은 [테스트](testing.md)에 있습니다. 이 명령은 결정적
패키지와 지시문 계약만 증명합니다. 라이브 검토 품질이나 호스트 간 동등은
증명하지 않습니다. 선택적 라이브 검사는 명시적, 로컬, 민감하지 않은 경계를
유지합니다.
