# beyondwin/skills

[English](README.md)

[![CI](https://github.com/beyondwin/skills/actions/workflows/verify.yml/badge.svg)](https://github.com/beyondwin/skills/actions/workflows/verify.yml)
[![Release](https://img.shields.io/github/v/release/beyondwin/skills)](https://github.com/beyondwin/skills/releases)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

한국어 글 교정, 프로젝트용 이미지 제작, 그림을 곁들인 원리 설명을 돕는
스킬 세 개를 제공합니다. 각 스킬은 독립적으로 동작하므로, 사용하는 AI 코딩
도구에서 지원하는 스킬 중 필요한 것만 골라 설치하세요.

지원 OS는 macOS뿐입니다. Windows와 Linux는 지원하지 않습니다. CI Ubuntu 전체 검증
통과는 Linux 지원이 아니고 macOS 지원 증거도 아닙니다.

## 스킬

현재 독립 제품 세 개와 각각 지원하는 도구(호스트)는 다음과 같습니다.

| 스킬 | 하는 일 | 호스트 |
| --- | --- | --- |
| [`korean-writing-editor`](skills/korean-writing-editor/README.ko.md) | 작성된 한국어 글의 뜻을 유지하면서 맞춤법과 문장을 고칩니다. | Codex |
| [`image-workbench`](skills/image-workbench/README.ko.md) | 프로젝트의 요구에 맞춰 이미지(PNG, JPG)를 기획·생성·편집합니다. | Codex, Grok |
| [`how-it-works`](skills/how-it-works/README.ko.md) | 작동 원리를 원하는 깊이로 그림과 함께 설명합니다. | Codex, Claude Code |

스킬 이름을 누르면 자세한 사용법과 첫 요청 예시를 볼 수 있습니다.

## 설치

Codex에서 Korean Writing Editor나 Image Workbench를 쓰려면, 아래에서 필요한
스킬의 요청을 입력하세요. 설치 위치와 기존 설치가 있을 때의 처리 방법은
[Codex 설치](docs/users/ko/install-codex.md)에 있습니다.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/korean-writing-editor
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/image-workbench
```

How It Works를 쓰거나 Grok에서 Image Workbench를 쓰려면 저장소를 클론한 뒤,
도구가 그 안의 스킬 폴더를 읽도록 연결합니다. [로컬 링크](docs/users/ko/install-local.md)
안내를 따르세요. How It Works의 공개 경로는 다음과 같습니다.

- https://github.com/beyondwin/skills/tree/main/skills/how-it-works

설치 방법을 비교하거나 갱신·제거 안내를 찾으려면 [설치](docs/users/ko/installation.md)를 보세요.

## 검증

저장소를 클론했다면 저장소 루트에서 다음 명령으로 규칙 준수 여부를 검사할 수 있습니다.
자격 증명이나 모델 호출은 필요하지 않습니다.

```bash
python3 scripts/verify.py
```

검사 통과가 모델의 글쓰기나 이미지 품질을 보장하지는 않습니다.
확인 범위는 [검증 안내](docs/users/ko/verification.md)를 보세요.

## 문서

- [문서 색인](docs/README.ko.md): 사용자 안내, 관리자 문서, 기록, 조사
- [호환성](docs/users/ko/compatibility.md), [안전과 개인정보](docs/users/ko/safety-and-privacy.md)(텔레메트리 없음)
- [기여](CONTRIBUTING.md), [보안](SECURITY.md), [행동 강령](CODE_OF_CONDUCT.md)

## 라이선스

Apache-2.0입니다. [LICENSE](LICENSE)를 보세요.
