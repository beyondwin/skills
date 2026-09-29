"""Read-only usage API for the operator console."""
import argparse
import json
from decimal import ROUND_HALF_UP, Decimal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from .config import load_config
from .pricing import cost
from .store import CallStore


def call_json(c):
    return {
        "id": c.id,
        "model": c.model,
        "started_at": c.started_at.isoformat(),
        "finished_at": c.finished_at.isoformat(),
        "status": c.status,
        "blocked_by": c.blocked_by or None,
    }


def list_calls(store):
    calls = sorted(store.all(), key=lambda c: (c.finished_at, c.id), reverse=True)
    return [call_json(c) for c in calls]


SIX = Decimal("0.000001")


def usage_summary(store):
    by_model = {}
    for c in store.all():
        attempts, total = by_model.get(c.model, (0, Decimal(0)))
        billed = Decimal(0) if c.estimated else cost(c.model, c.input_tokens, c.output_tokens)
        by_model[c.model] = (attempts + 1, total + billed)
    return [
        {"model": m, "attempts": a, "cost_usd": str(t.quantize(SIX, rounding=ROUND_HALF_UP))}
        for m, (a, t) in sorted(by_model.items())
    ]


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urlparse(self.path)
        if self.headers.get("X-Caller") not in self.server.config.allowed_callers:
            self._send(403, {"error": "caller_not_allowed"})
        elif url.path == "/api/usage":
            self._send(200, {"models": usage_summary(self.server.store)})
        elif url.path == "/api/calls":
            self._send(200, {"calls": list_calls(self.server.store)})
        else:
            self._send(404, {"error": "not_found"})

    def _send(self, status, body):
        data = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


def make_server(config, store, port=None):
    """Bound but not serving; call serve_forever() (tests use port=0)."""
    srv = ThreadingHTTPServer(("127.0.0.1", config.port if port is None else port), Handler)
    srv.store = store
    srv.config = config
    return srv


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python3 -m usage.server")
    ap.add_argument("--config", required=True)
    ap.add_argument("--seed", required=True)
    ap.add_argument("--port", type=int)
    args = ap.parse_args(argv)
    srv = make_server(load_config(args.config), CallStore.load(args.seed), args.port)
    print(f"serving on http://127.0.0.1:{srv.server_address[1]}", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
