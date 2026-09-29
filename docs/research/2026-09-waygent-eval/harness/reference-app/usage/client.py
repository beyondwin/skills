"""Operator console side: fetches the usage API and renders text screens."""
import argparse
import json
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class CallRow:
    id: str
    model: str
    started_at: datetime
    finished_at: datetime
    status: str
    blocked_by: str | None = None


@dataclass(frozen=True)
class UsageRow:
    model: str
    attempts: int
    cost_usd: Decimal


class Client:
    def __init__(self, base_url, opener=None, caller="console"):
        self.base_url = base_url.rstrip("/")
        self._open = opener or urllib.request.urlopen
        self.caller = caller

    def _get(self, path):
        req = urllib.request.Request(self.base_url + path, headers={"X-Caller": self.caller})
        with self._open(req) as resp:
            return json.loads(resp.read())

    def calls(self):
        return [
            CallRow(
                id=d["id"],
                model=d["model"],
                started_at=datetime.fromisoformat(d["started_at"]),
                finished_at=datetime.fromisoformat(d["finished_at"]),
                status=d["status"],
                blocked_by=d["blocked_by"],
            )
            for d in self._get("/api/calls")["calls"]
        ]

    def usage(self):
        return [
            UsageRow(model=d["model"], attempts=int(d["attempts"]), cost_usd=Decimal(d["cost_usd"]))
            for d in self._get("/api/usage")["models"]
        ]


def render_calls(rows):
    """Calls screen: one line per call, newest first as the API sends them."""
    return "\n".join(
        f"{r.finished_at:%H:%M:%S}  {r.model:<5} {r.status:<6} {r.id}"
        + (f"  차단 {r.blocked_by}" if r.blocked_by is not None else "")
        for r in rows
    )


def render_usage(rows):
    return "\n".join(f"{r.model:<5} {r.attempts:>4}  ${r.cost_usd}" for r in rows)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python3 -m usage.client")
    ap.add_argument("--base", required=True)
    ap.add_argument("screen", choices=["calls", "usage"])
    args = ap.parse_args(argv)
    client = Client(args.base)
    print(render_calls(client.calls()) if args.screen == "calls" else render_usage(client.usage()))


if __name__ == "__main__":
    main()
