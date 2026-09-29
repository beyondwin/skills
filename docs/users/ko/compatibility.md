# 호환성

[English](../en/compatibility.md) · [설치](installation.md)

각 스킬이 어느 호스트에서 돌아가는지 정리합니다. 호스트는 스킬을 실행하는 에이전트 앱입니다. 제품 안내: [`korean-writing-editor`](../../../skills/korean-writing-editor/README.ko.md), [`image-workbench`](../../../skills/image-workbench/README.ko.md), [`how-it-works`](../../../skills/how-it-works/README.ko.md), [`pre-sdd-review`](../../../skills/pre-sdd-review/README.ko.md), [`sddx`](../../../skills/sddx/README.ko.md), [`waygent`](../../../skills/waygent/README.ko.md).

| 스킬 | 지원 호스트 | 설치 방법 |
| --- | --- | --- |
| Korean Writing Editor | Codex | `$skill-installer` |
| Pre-SDD Review | Codex | `$skill-installer` |
| Image Workbench | Codex, Grok | Codex: `$skill-installer`. Grok: 로컬 링크 |
| How It Works | Codex, Claude Code | 로컬 링크 |
| SDDx | Claude Code, Codex | 로컬 링크 |
| Waygent | Claude Code, Codex, Cursor Agent, Grok Build | 로컬 링크 |

말 뜻:

- smoke: 실제로 한 번 돌려 본 기록
- `not_measured`: 아직 확인하지 않음
- `current-bounded`: 버전과 hash만 기록에 묶였음. 실제 실행이 아님

## 공유 지원 문장

korean-writing-editor: Codex supported; Agent Skills contract portable; other hosts only supported after a recorded smoke.

image-workbench: Codex and Grok supported; generate/edit requires the current host's built-in image generation and local image viewing.

how-it-works: Codex and Claude Code supported for local or repository-based use.

pre-sdd-review: Codex supported; other hosts not_measured.

sddx: Claude Code and Codex supported for local or repository-based use.

waygent: Claude Code, Codex, Cursor Agent, and Grok Build supported for local or repository-based use.

## 무엇을 지원으로 보나

다른 호스트가 스킬 폴더를 읽을 수 있다고 지원하는 것은 아닙니다. 새 호스트를 지원하려면 지금 빌드로 돌린 smoke 기록과 별도 결정이 필요합니다. 지원 범위와 측정 상태는 따로 봅니다. 지금 파일을 돌려 보지 않았으면 상태는 `not_measured`이고, 지원 범위는 그대로입니다.

이 스킬들은 Claude.ai, Cowork, Skills API 업로드로 쓰지 않으며, 마켓플레이스에 올라 있지 않습니다.

## 스킬별 메모

- `image-workbench`는 지금 호스트에 자체 그림 도구가 있고 결과를 열어 볼 수 있을 때만 그림을 만들거나 고칩니다. 다른 호스트의 비슷한 도구는 치지 않습니다. Grok에서는 `~/.agents/skills/image-workbench` 링크를 씁니다.
- `pre-sdd-review`는 다른 호스트에서 확인하지 않았습니다(`not_measured`).
- `how-it-works`: 현재 설치 파일의 라이브 실행은 `not_measured`입니다.
- `sddx`: Cursor Agent와 Grok Build는 과제를 넘겨받는 워커이고 호스트가 아닙니다. 같은 호스트에 `waygent`도 옆에 링크되어 있어야 합니다.
- `waygent`: 모든 호스트가 서브에이전트를 띄울 수 있어야 합니다. Codex는 `~/.codex/config.toml`의 `[features]`에 `multi_agent = true`가 있어야 합니다. 측정 기록은 [waygent 호환성 기록](../../maintainers/products/waygent/compatibility.md)에 있습니다.

## 운영체제

지원 OS는 macOS뿐입니다. Windows와 Linux는 지원하지 않습니다. CI는 Ubuntu에서 전체 검증을 돌릴 수 있습니다. 그 통과는 Linux 지원이 아니고 macOS 지원 증거도 아닙니다.

## 더 보기

설치·링크·제거는 [설치](installation.md), 검사는 [검증](verification.md)을 보세요. 라이선스는 Apache-2.0입니다.
