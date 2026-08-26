# beyondwin-skills

[English](README.en.md)

이 저장소는 한국어 교정과 프로젝트 래스터 자산 작업을 위한 큐레이션된 Agent Skill 두 개를 Codex 우선으로 배포합니다.

[![CI](https://github.com/beyondwin/skills/actions/workflows/verify.yml/badge.svg)](https://github.com/beyondwin/skills/actions/workflows/verify.yml)
[![Release](https://img.shields.io/github/v/release/beyondwin/skills)](https://github.com/beyondwin/skills/releases)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

플러그인 번들 `beyondwin-skills`, 저장소 릴리스 식별자, 두 스킬의 메타데이터 버전은 `2.0.0`입니다. 라이선스는 Apache-2.0입니다.

## 스킬 목록과 지원

카탈로그는 아래 두 스킬뿐입니다. 세 번째 스킬은 첫 릴리스 범위가 아닙니다.

| 스킬 | 역할 | 지원 |
| --- | --- | --- |
| `korean-writing-editor` | 사용자가 이미 준 한국어 글을 보수적으로 교정하거나 윤문합니다. | korean-writing-editor: Codex supported; Agent Skills contract portable; other hosts only supported after a recorded smoke. |
| `image-workbench` | 로컬 프로젝트에 맞는 래스터 자산을 계획·생성·편집·비교·점검합니다. | image-workbench: Codex-only; generate/edit requires Codex image generation and local image viewing. |

## 1분 설치와 호출

기본 경로는 Codex `$skill-installer`와 공개 GitHub 스킬 경로입니다. 대상 디렉터리가 이미 있으면 설치기는 중단하며, 기존 설치를 자동으로 바꾸지 않습니다.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/korean-writing-editor
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/image-workbench
```

설치 후 다음 턴에서 명시 호출합니다.

```text
$korean-writing-editor 오탈자만 고쳐줘: (한국어 원문)
$image-workbench 이 프로젝트 랜딩 페이지 hero 이미지를 만들어줘.
```

선택적 제3자 설치기(한국어 편집기만):

```text
npx skills add beyondwin/skills --skill korean-writing-editor
```

이 `npx` 명령은 제3자(third-party) 설치기이며 자체 릴리스와 텔레메트리 정책을 따릅니다. Codex 기본 경로가 아니고, `image-workbench` 호환을 증명하지 않습니다.

`npx`를 쓰지 않는 대안은 검증된 Git 클론 후 호스트 기본 스킬 폴더에 복사하는 것입니다. 기존 실제 디렉터리를 확인 없이 덮어쓰지 마세요.

```bash
git clone https://github.com/beyondwin/skills.git
```

자세한 대상 확인, 갱신, 제거는 [시작하기](docs/ko/getting-started.md)를 따릅니다. 공급자 없는 검증:

```bash
python3 scripts/verify.py
```

기본은 `--profile full`입니다. Windows 이식 검증은 `python3 scripts/verify.py --profile windows-portable`입니다. 라이브 `--execute`는 포함하지 않습니다.

## 제외와 안전

이 저장소는 텔레메트리를 넣지 않습니다. 필수 CI는 자격 증명·모델·원격 이미지 호출을 하지 않습니다. 플러그인 디렉터리 등록을 주장하지 않습니다.

`korean-writing-editor`는 번역, 초안, 요약, 코드 리뷰, 일상 대화, 저작자 검출, 검출 회피에 쓰지 않습니다. `image-workbench`는 재미용 일회성 이미지, SVG·네이티브 UI, 실제 프론트엔드 구현, 외부 프롬프트 갤러리 복제에 쓰지 않습니다.

설치·갱신·제거는 정확한 대상만 다룹니다. 원격 스크립트를 셸에 파이프하거나, 대상을 확인하지 않고 덮어쓰거나, 상위 스킬 디렉터리를 지우거나, 기존 설치를 자동으로 바꾸지 마세요.

## 오프라인과 라이브 증거

Offline fixtures: deterministic contract evidence only.

Live execution: local, explicit, optional, potentially billable, and never required by CI.

오프라인 통과는 일반 윤문 품질, 의미 동등, 라이브 이미지 품질, 권리 해소, 공급자 우월, 런타임 동등성을 증명하지 않습니다.

## 문서와 커뮤니티

- [시작하기](docs/ko/getting-started.md)
- [호환성](docs/ko/compatibility.md)
- [개인정보와 권리](docs/ko/privacy-and-rights.md)
- [평가](docs/ko/evaluation.md)
- [기여](CONTRIBUTING.md)
- [보안](SECURITY.md)
- [행동 강령](CODE_OF_CONDUCT.md)
- [라이선스](LICENSE)
- [English README](README.en.md)
