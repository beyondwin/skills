# pre-sdd-review 호환성

이 문서는 Pre-SDD Review의 측정된 호스트 경계를 소유합니다.

## Supported host

Codex is supported because 측정된 계약이 로컬 Git 저장소, 읽을 수 있는 설계와
계획 파일, 저장소 조사, 격리된 읽기 전용 검토자를 요구하기 때문입니다. Every other host is `not_measured`.
Markdown 패키지를 읽을 수 있어도 같은 검토자 격리와 저장소 동작을 입증하지
않았다면 지원으로 올리지 않습니다.

설치 경로, 비슷한 서브에이전트 기능, 공급자 없는 픽스처 통과만으로 지원을
추론하지 않습니다. 필요한 동작을 새 세션 smoke로 기록한 뒤에만 레지스트리와
공개 문서에 호스트를 추가합니다.

### Host matrix

| Host | Status |
| --- | --- |
| `claude-code` | `not_measured` |
| `codex` | `supported` |

## Evidence limit

필수 공급자 없는 명령은 [testing](testing.md)에 있습니다. 이 명령은 결정적
패키지와 지시문 계약만 증명하며, 라이브 리뷰 품질이나 호스트 간 동등을
증명하지 않습니다. 선택적 라이브 검사는 명시적, 로컬, 민감하지 않은 경계를
유지합니다.
