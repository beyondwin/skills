# usage

운영 콘솔의 LLM 사용량 화면입니다. 서버(`usage/server.py`)가 수집된 호출 기록을 API로 내주고,
콘솔(`usage/client.py`)이 그 API를 불러 글자 화면을 그립니다.

- Python 3.11+, 표준 라이브러리만 씁니다(외부 패키지 추가 금지).
- 시험: `python3 -m unittest discover -s tests -t .` (1초 안쪽)
- 콘솔 시험은 `usage.mock.MockOpener`로 서버를 대신합니다.
- 실행:
  - 서버: `python3 -m usage.server --config config/dev.toml --seed data/calls.jsonl --port 8765`
  - 콘솔: `python3 -m usage.client --base http://127.0.0.1:8765 calls`
- `data/calls.jsonl`은 운영에서 뽑은 실제 기록 모양 그대로입니다.
- 설계서는 `docs/design.md`입니다. 동작을 정할 때는 설계서가 기준입니다.
