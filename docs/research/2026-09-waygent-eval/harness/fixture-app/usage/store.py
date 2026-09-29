"""LLM call records collected by the orchestrator, read from a JSONL file."""
import json
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Call:
    id: str
    model: str
    started_at: datetime
    finished_at: datetime
    status: str  # "ok" or "failed"
    input_tokens: int
    output_tokens: int
    estimated: bool  # True when the provider sent no usage and the collector wrote its reserve
    blocked_by: str  # stored form: policy id, or "" when nothing blocked the call


def _call(d):
    return Call(
        id=d["id"],
        model=d["model"],
        started_at=datetime.fromisoformat(d["started_at"]),
        finished_at=datetime.fromisoformat(d["finished_at"]),
        status=d["status"],
        input_tokens=int(d["input_tokens"]),
        output_tokens=int(d["output_tokens"]),
        estimated=bool(d.get("estimated", False)),
        blocked_by=d.get("blocked_by", ""),
    )


class CallStore:
    def __init__(self, calls=()):
        self._calls = list(calls)

    @classmethod
    def load(cls, path):
        with open(path, encoding="utf-8") as f:
            return cls(_call(json.loads(line)) for line in f if line.strip())

    @classmethod
    def from_dicts(cls, rows):
        return cls(_call(d) for d in rows)

    def all(self):
        return list(self._calls)
