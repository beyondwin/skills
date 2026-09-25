# pre-sdd-review 호환성

이 문서는 Pre-SDD Review를 어느 호스트에서 실제로 확인했는지 정합니다.

## 지원 호스트

지금은 Codex만 지원합니다. 계약이 로컬 Git 저장소, 읽을 수 있는 설계와 계획
파일, 저장소 조사, 격리된 읽기 전용 검토자를 요구하고, 이를 Codex에서만
측정했기 때문입니다. 다른 호스트는 모두 `not_measured`입니다.

폴더 모양이 같다고 검토자 격리와 저장소 동작이 같은 것은 아닙니다. 설치 경로,
비슷한 서브에이전트 기능, 공급자 없는 픽스처 통과만으로 지원을 추론하지
않습니다. 필요한 동작을 새 세션 스모크 검사로 기록한 뒤에만 레지스트리와 공개
문서에 호스트를 추가합니다.

### Host matrix

| Host | Status |
| --- | --- |
| `claude-code` | `not_measured` |
| `codex` | `supported` |
| `grok` | `not_measured` |

## 지원 OS

지원 OS는 macOS뿐입니다. Windows와 Linux는 지원하지 않습니다. CI는 Ubuntu에서
`full` 프로필을 돌릴 수 있습니다. 그 통과는 Linux 지원이 아니고 macOS 지원
증거도 아닙니다.

## 기록기 호환성

기록기 호환성은 위 호스트 표(검토 동작 기준)와 별개입니다. Codex, Claude Code,
Cursor, Grok는 로드된 스킬 루트의 같은 `evidence/evidence.py`를 쓰고, 데이터
루트 `~/.pre-sdd-review/` 하나를 공유합니다. 기록기가 동작해도 그 호스트의 독립
읽기 전용 검토나 검토 품질을 증명하지는 않습니다.

### CLI matrix

| Runtime | Status | Evidence boundary |
| --- | --- | --- |
| macOS / Python 3.11+ | `verified` | provider-free evidence suite |
| Linux / Python 3.11+ | `unsupported` | 제품 미지원. CI POSIX 검사 ≠ Linux 제품 지원 |
| Windows / Python 3.11+ | `unsupported` | Windows는 지원하지 않습니다 |

변경 명령은 `.identity.lock`과 `locks/<run-id>.lock`에 OS 파일 잠금을 씁니다.
`show`, `summary`, `--version`은 읽기 전용이며 그 lock을 잡지 않습니다.

## 증거 한계

필수 공급자 없는 명령은 [테스트](testing.md)에 있습니다. 이 명령은 결정적
패키지와 지시문 계약만 증명합니다. 라이브 검토 품질이나 호스트 간 동등은
증명하지 않습니다. 선택적 라이브 검사는 명시적으로, 로컬에서, 민감하지 않은
입력으로만 합니다.
