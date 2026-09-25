# beyondwin/skills

[English](README.en.md)

[![CI](https://github.com/beyondwin/skills/actions/workflows/verify.yml/badge.svg)](https://github.com/beyondwin/skills/actions/workflows/verify.yml)
[![Release](https://img.shields.io/github/v/release/beyondwin/skills)](https://github.com/beyondwin/skills/releases)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

Codex, Claude Code, Grok 같은 AI 코딩 도구에 넣어 쓰는 스킬 다섯 개를 모아 둔
저장소입니다. 필요한 스킬만 골라 하나씩 설치합니다. 라이선스는 Apache-2.0입니다.

지원 OS는 macOS뿐입니다. Windows와 Linux는 지원하지 않습니다. CI Ubuntu 전체 검증
통과는 Linux 지원이 아니고 macOS 지원 증거도 아닙니다.

## 스킬 고르기

현재 독립 제품은 아래 다섯 가지입니다. 호스트는 스킬을 실행하는 프로그램입니다.

| 스킬 | 하는 일 | 호스트 |
| --- | --- | --- |
| [`korean-writing-editor`](skills/korean-writing-editor/README.md) | 있는 한국어 글을 받아, 뜻은 그대로 두고 맞춤법과 문장을 고칩니다. | Codex |
| [`image-workbench`](skills/image-workbench/README.md) | 이 프로젝트에 넣을 PNG·JPG 같은 이미지를 기획하고 만들고 고칩니다. | Codex, Grok |
| [`how-it-works`](skills/how-it-works/README.md) | 한 기계가 어떻게 도는지, 고른 깊이로 그림과 글로 설명합니다. | Codex, Claude Code |
| [`pre-sdd-review`](skills/pre-sdd-review/README.md) | SDD 직전에 승인된 설계와 구현 계획을 지금 저장소와 맞춰 보고, 문서를 고친 뒤 고친 곳을 다시 확인합니다. | Codex |
| [`sddx`](skills/sddx/README.md) | Superpowers SDD는 지금 세션이 진행하고, 코드 작성만 Cursor Agent 또는 Grok Build(Grok 4.7)에 맡깁니다. | Claude Code, Codex |

쓰는 법과 첫 호출은 각 스킬 README에 있습니다.

## 설치

설치 방법은 호스트에 따라 두 가지입니다.

Korean Writing Editor, Image Workbench, Pre-SDD Review는 Codex에서
`$skill-installer`로 넣습니다. 자세한 순서는 [Codex 설치](docs/users/ko/install-codex.md)를
보세요.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/korean-writing-editor
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/image-workbench
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/pre-sdd-review
```

How It Works와 SDDx(Codex, Claude Code), 그리고 Grok의 Image Workbench는 이
저장소를 받은 뒤 바로가기(심볼릭 링크)를 겁니다. 순서는
[로컬 링크](docs/users/ko/install-local.md)를 보세요. 공개 경로는 다음과 같습니다.

- How It Works: https://github.com/beyondwin/skills/tree/main/skills/how-it-works
- SDDx: https://github.com/beyondwin/skills/tree/main/skills/sddx

스킬별 설치 방법 표, 갱신·제거, 제3자 설치기는 [설치](docs/users/ko/installation.md)에서
찾아갈 수 있습니다.

## 검증

저장소 규칙을 자격 증명과 모델 호출 없이 검사합니다.

```bash
python3 scripts/verify.py
```

어떤 검사를 하는지, 통과가 무엇을 뜻하는지는 [검증](docs/users/ko/verification.md)을
보세요.

## 안전

이 저장소는 텔레메트리를 넣지 않습니다. 자세한 내용은
[안전과 개인정보](docs/users/ko/safety-and-privacy.md)를 보세요.

## 문서와 커뮤니티

- [문서 색인](docs/README.md)
- [설치](docs/users/ko/installation.md)
- [호환성](docs/users/ko/compatibility.md)
- [안전과 개인정보](docs/users/ko/safety-and-privacy.md)
- [검증](docs/users/ko/verification.md)
- [기여](CONTRIBUTING.md)
- [보안](SECURITY.md)
- [행동 강령](CODE_OF_CONDUCT.md)
- [라이선스](LICENSE)
- [English README](README.en.md)
