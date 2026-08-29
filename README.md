# beyondwin-skills

[English](README.en.md)

스킬 네 개를 모아 둔 저장소입니다. Korean Writing Editor, Image Workbench, Pre-SDD Review는 Codex에서 설치합니다. How It Works는 Codex와 Claude Code에서 로컬 또는 저장소 기준으로 설치합니다.

[![CI](https://github.com/beyondwin/skills/actions/workflows/verify.yml/badge.svg)](https://github.com/beyondwin/skills/actions/workflows/verify.yml)
[![Release](https://img.shields.io/github/v/release/beyondwin/skills)](https://github.com/beyondwin/skills/releases)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

라이선스는 Apache-2.0입니다.

## 스킬 선택

현재 독립 제품은 아래 네 가지입니다. 불변 카탈로그 `v2.0.0` 번들에는 How It Works와 Pre-SDD Review가 들어 있지 않습니다.

| 스킬 | 역할 | 호스트 |
| --- | --- | --- |
| [`korean-writing-editor`](skills/korean-writing-editor/README.md) | 있는 한국어 글을 받아, 뜻은 그대로 두고 맞춤법과 문장을 고칩니다. | Codex |
| [`image-workbench`](skills/image-workbench/README.md) | 이 프로젝트에 넣을 PNG·JPG 같은 이미지를 기획하고 만들고 고칩니다. | Codex |
| [`how-it-works`](skills/how-it-works/README.md) | 한 기계가 어떻게 도는지, 고른 깊이로 그림과 글로 설명합니다. | Codex, Claude Code |
| [`pre-sdd-review`](skills/pre-sdd-review/README.md) | 승인된 설계와 구현 계획을 SDD 직전에 저장소 현실과 대조하고 문서를 고쳐 다시 검토합니다. | Codex |

쓰는 법과 첫 호출은 각 제품 README에 있습니다. How It Works 로컬 링크는 제품 README와 [설치](docs/users/ko/installation.md)에 있습니다.

## 설치

Korean Writing Editor, Image Workbench, Pre-SDD Review는 Codex에서 `$skill-installer`로 넣습니다. 같은 폴더가 이미 있으면 설치기는 멈춥니다. 있는 설치를 자동으로 바꾸지 않습니다.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/korean-writing-editor
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/image-workbench
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/pre-sdd-review
```

How It Works는 `~/.agents/skills/how-it-works`(Codex)와 `~/.claude/skills/how-it-works`(Claude Code)에 둡니다. 공개 GitHub 경로는 https://github.com/beyondwin/skills/tree/main/skills/how-it-works 입니다. `~/.codex` 복사본을 만들지 마세요.

설치·갱신·제거와 제3자 설치기는 [설치](docs/users/ko/installation.md)를 보세요.

모델 없이 저장소를 검사하려면:

```bash
python3 scripts/verify.py
```

기본은 `--profile full`입니다. Windows는 `python3 scripts/verify.py --profile windows-portable`입니다. 라이브 `--execute`는 들어 있지 않습니다.

## 안전

이 저장소는 텔레메트리를 넣지 않습니다. 필수 CI는 자격 증명·모델·원격 이미지 호출을 하지 않습니다. 플러그인 디렉터리 등록을 주장하지 않습니다.

아래에는 쓰지 않습니다.

- `korean-writing-editor`: 번역, 초안, 요약, 코드 리뷰, 일상 대화, 저작자 검출, 검출 회피
- `image-workbench`: 재미용 일회성 이미지, SVG·네이티브 UI, 실제 프론트엔드 구현, 외부 프롬프트 갤러리 복제
- `how-it-works`: 디버깅, 구현, 리뷰, 번역, 한 줄 사실 조회, 어린이 말투 설명, `/eli5` 대행
- `pre-sdd-review`: 최초 설계·계획 작성, 코드 리뷰, 릴리스 검토. 명시적인 외부 요청 없이 구현을 시작하지 않습니다.

설치·갱신·제거는 확인한 대상만 다룹니다. 원격 스크립트를 셸에 파이프하거나, 대상을 확인하지 않고 덮어쓰거나, 상위 스킬 디렉터리를 지우거나, 기존 설치를 자동으로 바꾸지 마세요.

자세한 내용은 [안전과 개인정보](docs/users/ko/safety-and-privacy.md)를 보세요.

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
