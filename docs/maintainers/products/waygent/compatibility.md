# waygent 호환성

이 문서는 waygent를 어느 호스트와 OS에서 지원하는지, 그 근거가 무엇인지 정합니다.
지원 호스트는 제품 목록의 `claude-code`, `codex`, `cursor` 세 개이며, 로컬 또는 저장소
연결로만 지원합니다. 지원 범위와 측정 상태는 별개입니다. 측정은 아래 기록에 있고,
그 뒤 바뀐 설치 파일은 다시 재기 전까지 `not_measured`입니다.

- Claude Code: 서브에이전트(Agent 도구)로 구현·리뷰를 띄웁니다.
- Codex: `$waygent`로 부릅니다. 서브에이전트는 `spawn_agent` 도구로 띄우며,
  `~/.codex/config.toml`에 `[features]` `multi_agent = true`가 있어야 합니다.
- Cursor Agent: 이 제품에서는 호스트입니다. `sddx`에서는 여전히 워커이고 호스트가
  아닙니다. 서브에이전트는 `Task` 도구로 띄우고, 모델을 주지 않아도 메인과 같은
  모델을 씁니다.
- Grok: 지원하지 않습니다.
- Claude.ai, Cowork, Skills API 업로드, marketplace 게시는 지원하지 않습니다.

## 지원 OS

지원 OS는 macOS뿐입니다. Windows와 Linux는 지원하지 않습니다. CI Ubuntu 전체 검증
통과는 macOS 지원 증거가 아닙니다.

## 발견 경로

```text
skills/waygent/              저장소 원본
├─ ~/.claude/skills/waygent ─→ Claude Code
├─ ~/.agents/skills/waygent ─→ Codex
└─ ~/.cursor/skills/waygent ─→ Cursor Agent
```

2026-09-27에 Cursor Agent 2026.09.23이 프로젝트의 `.cursor/skills/<name>/SKILL.md`와
사용자 경로 `~/.cursor/skills/<name>/SKILL.md`를 모두 읽는 것을 확인했습니다(시험용 스킬 호출).

링크 블록은 제품 README와 [로컬 링크](../../../users/ko/install-local.md)에 있고,
다른 링크·파일·디렉터리를 자동으로 바꾸지 않습니다.

## 측정 기록

자세한 과제와 수치는 [waygent 설계와 실측](../../../research/2026-09-waygent-eval/README.md)에
있습니다. 이 기록은 그 시점의 실행 증거이고, 이후 버전을 보증하지 않습니다.

| 호스트 | 버전 | 모델 | 날짜 | waygent | 결과 |
| --- | --- | --- | --- | --- | --- |
| Claude Code | 2.1.280 | opus (Opus 5.5) | 2026-09-27 | 0.1.0 작업본 | 5회 완료(숨긴 테스트 64개 중 64/63/64, 규칙 고친 뒤 64/58). 끊고 이어 하기 1회 64/64. superpowers와 공존 1회 64/64 |
| Claude Code | 2.1.280 | fable (Fable 5.1) | 2026-09-27 | 0.1.0 작업본 | 1회 완료(64/64), $25.95 |
| Cursor Agent | 2026.09.23 | grok-4.7-high | 2026-09-27 | 0.1.0 작업본 | 2회. 두 회차 모두 10개 Task를 커밋함(63/64, 64/64). 1회차는 하네스 턴 상한으로 끝 리뷰 전에 끊김. 평균 291분으로 매우 느림 |
| Codex | 0.154.0 | gpt-5.6-sol (high) | 2026-09-27 | 0.1.0 작업본 | 2회 완료, 모두 10개 Task 커밋(63/64, 62/64). 1회차는 조율자가 자기 모델을 잘못 알아 다른 모델로 자식을 띄움. 모델을 물려받게 고친 2회차는 자식 22개 모두 세션 모델. 한 등급 위를 `xhigh`로 고정한 마지막 문구는 재지 않음. `codex exec`에서는 명시 호출 전용 스킬이 `$waygent`로 불러와지지 않아 측정 사본에서 `agents/openai.yaml`을 뺌 |
