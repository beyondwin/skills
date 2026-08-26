# 호환성

[English](../en/compatibility.md) · [시작하기](getting-started.md)

Codex가 두 스킬의 1급 런타임입니다. 카탈로그는 `korean-writing-editor`와 `image-workbench` 두 개이며 버전은 `2.0.0`입니다.

## 공유 지원 문장

korean-writing-editor: Codex supported; Agent Skills contract portable; other hosts only supported after a recorded smoke.

image-workbench: Codex-only; generate/edit requires Codex image generation and local image viewing.

Offline fixtures: deterministic contract evidence only.

Live execution: local, explicit, optional, potentially billable, and never required by CI.

## 계약 이식과 측정된 지원

`korean-writing-editor`는 열린 Agent Skills 디렉터리 형식(`SKILL.md`, `scripts/`, `references/`, `assets/`)을 따릅니다. 그 계약 이식은 Claude Code, Cursor, 그 밖의 호스트가 지금 지원된다는 뜻이 아닙니다. 호스트는 현재 smoke가 기록된 뒤에만 `supported`이고, 그렇지 않으면 `partially verified` 또는 `not_measured`입니다.

`image-workbench`는 Codex 전용입니다. 다른 호스트의 비슷한 이미지 도구는 호환을 성립시키지 않습니다. `brief`와 `audit`은 읽기 전용일 수 있지만, 생성·편집은 Codex 내장 이미지 생성과 로컬 이미지 보기가 필요합니다.

플러그인 이름 `beyondwin-skills`는 저장소가 플러그인으로 패키징되어 있다는 뜻입니다. 플러그인 디렉터리에 올라 있다고 주장하지 않습니다.

## 설치 경로와 호스트

- 기본: `$skill-installer`와 공개 GitHub 스킬 경로. [시작하기](getting-started.md)를 보세요.
- 선택: 제3자 `npx skills add beyondwin/skills --skill korean-writing-editor`. 이 설치기의 정책은 이 저장소와 다릅니다.
- 대안: `git clone` 후 호스트 기본 폴더 설치. 정확한 대상을 확인하기 전에 복사하지 마세요.

Windows에서 의미 있는 검사는 한국어 편집기 오프라인 스위트와 저장소 계약입니다. `image-workbench` 생성·편집은 Codex 전제 조건을 충족하는 환경에서만 주장합니다.

라이선스는 Apache-2.0입니다. 공급자 없는 검증은 `python3 scripts/verify.py`입니다.
