# 호환성

[English](../en/compatibility.md) · [설치](installation.md)

현재 독립 제품은 [`korean-writing-editor`](../../../skills/korean-writing-editor/README.md), [`image-workbench`](../../../skills/image-workbench/README.md), [`how-it-works`](../../../skills/how-it-works/README.md), [`pre-sdd-review`](../../../skills/pre-sdd-review/README.md)입니다. How It Works는 Codex와 Claude Code에서 씁니다. 나머지 세 제품은 Codex에서만 지원합니다.

쉽게 말하면: 한국어 편집기, 이미지 작업대, SDD 전 검토는 지금 Codex만 확인했습니다. How It Works는 Codex와 Claude Code에서 이 저장소를 연결해 씁니다.

## 공유 지원 문장

korean-writing-editor: Codex supported; Agent Skills contract portable; other hosts only supported after a recorded smoke.

image-workbench: Codex-only; generate/edit requires Codex image generation and local image viewing.

how-it-works: Codex and Claude Code supported for local or repository-based use.

pre-sdd-review: Codex supported; other hosts not_measured.

## 이식과 실제 지원

폴더 모양이 같다고 그 호스트를 지원하는 것은 아닙니다. 새 호스트를 지원하려면 지금 빌드를 실제로 돌려 본 기록(smoke)과 별도 결정이 필요합니다. “예전에 지원했다”와 “지금 이 환경에서 돌렸다”는 다릅니다. 지금 실행을 확인하지 않았으면 `not_measured`(아직 확인하지 않음)로 적습니다. 그것만으로 기존 지원 범위를 바꾸지는 않습니다. 제품별 안내는 각 README를 보세요.

`how-it-works`는 로컬 또는 저장소 기준으로 Codex와 Claude Code를 지원합니다. Claude.ai, Cowork, Skills API 업로드, marketplace 게시는 지원하지 않습니다.

`image-workbench`는 Codex 전용입니다. 다른 호스트의 비슷한 도구는 호환이 아닙니다.

`pre-sdd-review`의 다른 호스트는 `not_measured`입니다.

보존된 `how-it-works` smoke는 `historical-unbound`(예전 기록, 지금 실행 증거가 아님)이며 현재 설치 파일·모델 실행 증거와 별개입니다. 현재 2.0.0의 실제 실행은 `not_measured`입니다. `current-bounded`는 버전/hash와 메타데이터만 묶여 있는지 보며, 실제 실행이나 설명 품질을 증명하지 않습니다. 새 native Windows 측정은 없습니다.

이 저장소의 카탈로그 플러그인 이름은 `beyondwin-skills`입니다. 마켓플레이스에 올라 있다는 뜻이 아닙니다.

## 설치 경로와 호스트

설치·링크·제거는 [설치](installation.md)를 보세요. 검증은 [검증](verification.md)을 보세요.

Windows에서 의미 있는 검사는 한국어 편집기 오프라인 스위트와 저장소 계약입니다. `image-workbench` 생성·편집은 Codex가 있는 환경에서만 주장하세요.

라이선스는 Apache-2.0입니다.
