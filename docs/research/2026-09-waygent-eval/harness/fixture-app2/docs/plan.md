# 사용량 화면 구현 계획

설계서: `docs/design.md`. 동작은 설계서를 따릅니다. 이 계획은 순서와 이름만 정합니다.

## 공통

- 작업 브랜치 `work`에서 합니다. `main`에는 커밋하지 않습니다. Task마다 커밋합니다.
- 시험: `python3 -m unittest discover -s tests -t .` 가 끝날 때 모두 통과해야 합니다.
- 표준 라이브러리만 씁니다.
- 이름과 시그니처는 아래 그대로 둡니다.

## Task 1. 모델별 비용

파일: `usage/server.py`, `usage/client.py`, `usage/mock.py` · 설계 2, 3장

- 서버 `usage_summary(store) -> list[dict]`, 모델 이름순. 항목 `{"model", "attempts", "cost_usd"}`.
- `GET /api/usage` → `{"models": usage_summary(store)}`.
- 콘솔 `UsageRow(model: str, attempts: int, cost_usd: Decimal)`, `Client.usage() -> list[UsageRow]`,
  `render_usage(rows) -> str`.
- 목에 `/api/usage` 응답을 더합니다.

## Task 2. 차단 표시

파일: `usage/server.py`, `usage/client.py`, `usage/mock.py` · 설계 2, 4장

- 호출 응답에 `blocked_by`를 더합니다.
- `CallRow.blocked_by: str | None`. `render_calls`가 차단을 표시합니다.

## Task 3. 호출자 허용 목록

파일: `usage/config.py`, `usage/server.py`, `config/dev.toml` · 설계 5장

- `Config.allowed_callers: tuple[str, ...]`. `load_config`가 읽습니다.
- 서버가 `X-Caller`를 검사합니다.
- `config/dev.toml`에 `allowed_callers = ["console"]`을 더합니다.
