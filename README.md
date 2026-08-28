# beyondwin-skills

[English](README.en.md)

이 저장소는 현재 독립 제품 세 개를 모아 둡니다. Korean Writing Editor와 Image Workbench는 Codex에서 설치합니다. How It Works는 Codex와 Claude Code에서 로컬 또는 저장소 기준으로 설치합니다.

[![CI](https://github.com/beyondwin/skills/actions/workflows/verify.yml/badge.svg)](https://github.com/beyondwin/skills/actions/workflows/verify.yml)
[![Release](https://img.shields.io/github/v/release/beyondwin/skills)](https://github.com/beyondwin/skills/releases)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

라이선스는 Apache-2.0입니다.

## 스킬 선택

현재 독립 제품은 아래 세 가지입니다. 네 번째 제품은 기본 기여 범위가 아닙니다. 불변 카탈로그 `v2.0.0` 번들에는 How It Works가 들어 있지 않습니다.

| 스킬 | 역할 | 호스트 |
| --- | --- | --- |
| [`korean-writing-editor`](skills/korean-writing-editor/README.md) | 있는 한국어 글을 받아, 뜻은 그대로 두고 맞춤법과 문장을 고칩니다. | Codex |
| [`image-workbench`](skills/image-workbench/README.md) | 이 프로젝트에 넣을 PNG·JPG 같은 이미지를 기획하고 만들고 고칩니다. | Codex |
| [`how-it-works`](skills/how-it-works/README.md) | 한 기계가 어떻게 도는지, 고른 깊이로 그림과 글로 설명합니다. | Codex, Claude Code |

사용·설치·첫 호출은 각 제품 README를 따릅니다. How It Works의 로컬 링크는 제품 README와 [설치](docs/users/ko/installation.md)에 있습니다.

## 설치

Korean Writing Editor와 Image Workbench의 Codex 기본 경로는 `$skill-installer`와 공개 GitHub 스킬 경로입니다. 대상 디렉터리가 이미 있으면 설치기는 중단하며, 기존 설치를 자동으로 바꾸지 않습니다.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/korean-writing-editor
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/image-workbench
```

How It Works는 `~/.agents/skills/how-it-works`(Codex)와 `~/.claude/skills/how-it-works`(Claude Code)에 설치합니다. 공개 GitHub 경로는 https://github.com/beyondwin/skills/tree/main/skills/how-it-works 입니다. `~/.codex` 복사본을 만들지 마세요.

설치·갱신·제거와 제3자 설치기는 [설치](docs/users/ko/installation.md)를 따릅니다.

공급자 없는 검증:

```bash
python3 scripts/verify.py
```

기본은 `--profile full`입니다. Windows 이식 검증은 `python3 scripts/verify.py --profile windows-portable`입니다. 라이브 `--execute`는 포함하지 않습니다.

## 안전

이 저장소는 텔레메트리를 넣지 않습니다. 필수 CI는 자격 증명·모델·원격 이미지 호출을 하지 않습니다. 플러그인 디렉터리 등록을 주장하지 않습니다.

`korean-writing-editor`는 번역, 초안, 요약, 코드 리뷰, 일상 대화, 저작자 검출, 검출 회피에 쓰지 않습니다. `image-workbench`는 재미용 일회성 이미지, SVG·네이티브 UI, 실제 프론트엔드 구현, 외부 프롬프트 갤러리 복제에 쓰지 않습니다. `how-it-works`는 디버깅, 구현, 리뷰, 번역, 한 줄 사실 조회, 어린이 말투 설명, `/eli5` 대행에 쓰지 않습니다.

설치·갱신·제거는 정확한 대상만 다룹니다. 원격 스크립트를 셸에 파이프하거나, 대상을 확인하지 않고 덮어쓰거나, 상위 스킬 디렉터리를 지우거나, 기존 설치를 자동으로 바꾸지 마세요.

자세한 경계는 [안전과 개인정보](docs/users/ko/safety-and-privacy.md)를 따릅니다.

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
