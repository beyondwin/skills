# 호환성

[English](../en/compatibility.md) · [설치](installation.md)

현재 독립 제품은 [`korean-writing-editor`](../../../skills/korean-writing-editor/README.md), [`image-workbench`](../../../skills/image-workbench/README.md), [`how-it-works`](../../../skills/how-it-works/README.md)입니다. 네 호스트 주장은 How It Works뿐입니다. Korean Writing Editor와 Image Workbench는 등록된 Codex 경계를 유지합니다.

## 공유 지원 문장

korean-writing-editor: Codex supported; Agent Skills contract portable; other hosts only supported after a recorded smoke.

image-workbench: Codex-only; generate/edit requires Codex image generation and local image viewing.

how-it-works: Codex, Claude Code, Grok, and Cursor supported for local or repository-based use.

## 계약 이식과 측정된 지원

`korean-writing-editor`는 열린 Agent Skills 디렉터리 형식(`SKILL.md`, `scripts/`, `references/`, `assets/`)을 따릅니다. 그 계약 이식은 Claude Code, Cursor, 그 밖의 호스트가 지금 지원된다는 뜻이 아닙니다. 호스트는 현재 smoke가 기록된 뒤에만 `supported`이고, 그렇지 않으면 `partially verified` 또는 `not_measured`입니다.

`image-workbench`는 Codex 전용입니다. 다른 호스트의 비슷한 이미지 도구가 있어도 호환이 되지는 않습니다. `brief`와 `audit`은 읽기 전용일 수 있지만, 생성·편집은 Codex 내장 이미지 생성과 로컬 이미지 보기가 필요합니다.

`how-it-works`는 로컬 또는 저장소 기준으로 `codex`, `claude-code`, `grok`, `cursor`를 지원합니다. 출력은 채팅의 GitHub-flavored markdown과 mermaid 소스, 번호 있는 홉 목록입니다. 호스트 페이지나 mermaid 렌더러는 필수가 아닙니다. Claude.ai, Cowork, Skills API 업로드, marketplace 게시는 지원하지 않습니다.

불변 카탈로그 `v2.0.0` 플러그인 번들에는 How It Works가 들어 있지 않습니다. 플러그인 이름 `beyondwin-skills`는 저장소가 플러그인으로 패키징되어 있다는 뜻입니다. 플러그인 디렉터리에 올라 있다고 주장하지 않습니다.

## 설치 경로와 호스트

- Codex 기본: `$skill-installer`와 공개 GitHub 스킬 경로. [설치](installation.md)를 보세요.
- How It Works: `~/.agents/skills/how-it-works`(Codex, Grok, Cursor)와 `~/.claude/skills/how-it-works`(Claude Code). `ln -s`는 이미 있는 대상을 덮어쓰지 않고 실패합니다.
- 선택: 제3자 `npx skills add beyondwin/skills --skill korean-writing-editor`. 이 설치기의 정책은 이 저장소와 다릅니다.
- 대안: `git clone` 후 호스트 기본 폴더 설치. 정확한 대상을 확인하기 전에 복사하지 마세요.

Windows에서 의미 있는 검사는 한국어 편집기 오프라인 스위트와 저장소 계약입니다. `image-workbench` 생성·편집은 Codex 전제 조건을 충족하는 환경에서만 주장합니다.

라이선스는 Apache-2.0입니다. 공급자 없는 검증은 `python3 scripts/verify.py`입니다.
