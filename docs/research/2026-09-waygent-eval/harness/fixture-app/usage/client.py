"""Operator console side: fetches the usage API and renders text screens."""
import argparse
import json
import urllib.request
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CallRow:
    id: str
    model: str
    started_at: datetime
    finished_at: datetime
    status: str


class Client:
    def __init__(self, base_url, opener=None):
        self.base_url = base_url.rstrip("/")
        self._open = opener or urllib.request.urlopen

    def _get(self, path):
        req = urllib.request.Request(self.base_url + path)
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
            )
            for d in self._get("/api/calls")["calls"]
        ]


def render_calls(rows):
    """Calls screen: one line per call, newest first as the API sends them."""
    return "\n".join(f"{r.finished_at:%H:%M:%S}  {r.model:<5} {r.status:<6} {r.id}" for r in rows)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python3 -m usage.client")
    ap.add_argument("--base", required=True)
    ap.add_argument("screen", choices=["calls"])
    args = ap.parse_args(argv)
    client = Client(args.base)
    print(render_calls(client.calls()))


if __name__ == "__main__":
    main()
