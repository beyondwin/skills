# beyondwin/skills

[English](README.md)

[![CI](https://github.com/beyondwin/skills/actions/workflows/verify.yml/badge.svg)](https://github.com/beyondwin/skills/actions/workflows/verify.yml)
[![Release](https://img.shields.io/github/v/release/beyondwin/skills)](https://github.com/beyondwin/skills/releases)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

Codex, Claude Code, Cursor, Grok 같은 AI 코딩 도구에 넣어 쓰는 스킬 여섯 개입니다.
필요한 것만 골라 설치하면 되고, 하나하나 따로 동작합니다.

지원 OS는 macOS뿐입니다. Windows와 Linux는 지원하지 않습니다. CI Ubuntu 전체 검증
통과는 Linux 지원이 아니고 macOS 지원 증거도 아닙니다.

## 스킬

현재 독립 제품은 아래와 같습니다. 호스트는 스킬을 실행하는 도구입니다.

| 스킬 | 하는 일 | 호스트 |
| --- | --- | --- |
| [`korean-writing-editor`](skills/korean-writing-editor/README.ko.md) | 가진 한국어 글의 맞춤법과 문장을 뜻은 그대로 두고 고칩니다. | Codex |
| [`image-workbench`](skills/image-workbench/README.ko.md) | 프로젝트에 맞아야 하는 이미지(PNG, JPG)를 기획하고 만들고 고칩니다. | Codex, Grok |
| [`how-it-works`](skills/how-it-works/README.ko.md) | 무언가가 어떻게 도는지 고른 깊이로 그림과 함께 설명합니다. | Codex, Claude Code |
| [`pre-sdd-review`](skills/pre-sdd-review/README.ko.md) | SDD 직전에 승인된 설계와 계획을 저장소와 맞춰 보고, 고친 뒤 다시 확인합니다. | Codex |
| [`sddx`](skills/sddx/README.ko.md) | Superpowers SDD는 지금 세션이 진행하고, 코드 작성만 Cursor Agent나 Grok Build에 맡깁니다. | Claude Code, Codex |
| [`waygent`](skills/waygent/README.ko.md) | 계획을 과제마다 새 서브에이전트로 돌립니다. 테스트 먼저, 과제별 리뷰 한 번, 최종 리뷰 한 번. | Claude Code, Codex, Cursor |

설치 방법과 첫 호출은 각 스킬 README에 있습니다.

## 설치

Codex에서는 Korean Writing Editor, Image Workbench, Pre-SDD Review를
`$skill-installer`로 넣습니다([Codex 설치](docs/users/ko/install-codex.md)).

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/korean-writing-editor
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/image-workbench
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/pre-sdd-review
```

나머지 스킬과 Grok의 Image Workbench는 이 저장소를 받은 뒤 링크를 겁니다
([로컬 링크](docs/users/ko/install-local.md)).

- https://github.com/beyondwin/skills/tree/main/skills/how-it-works
- https://github.com/beyondwin/skills/tree/main/skills/sddx
- https://github.com/beyondwin/skills/tree/main/skills/waygent

갱신, 제거, 모든 선택지는 [설치](docs/users/ko/installation.md)에 있습니다.

## 검증

자격 증명과 모델 호출 없이 저장소 규칙을 검사합니다
([통과의 의미](docs/users/ko/verification.md)).

```bash
python3 scripts/verify.py
```

## 문서

- [문서 색인](docs/README.ko.md): 사용자 안내, 관리자 문서, 기록, 조사
- [호환성](docs/users/ko/compatibility.md), [안전과 개인정보](docs/users/ko/safety-and-privacy.md)(텔레메트리 없음)
- [기여](CONTRIBUTING.md), [보안](SECURITY.md), [행동 강령](CODE_OF_CONDUCT.md)

## 라이선스

Apache-2.0입니다. [LICENSE](LICENSE)를 보세요.
