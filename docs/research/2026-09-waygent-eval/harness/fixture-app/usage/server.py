"""Read-only usage API for the operator console."""
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from .config import load_config
from .store import CallStore


def call_json(c):
    return {
        "id": c.id,
        "model": c.model,
        "started_at": c.started_at.isoformat(),
        "finished_at": c.finished_at.isoformat(),
        "status": c.status,
    }


def list_calls(store):
    calls = sorted(store.all(), key=lambda c: (c.finished_at, c.id), reverse=True)
    return [call_json(c) for c in calls]


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/api/calls":
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
