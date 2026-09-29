"""Stand-in for urlopen in client tests: canned JSON per path, requests kept for asserts."""
import io
import json
from urllib.parse import urlparse

CANNED = {
    "/api/calls": {
        "calls": [
            {"id": "c2", "model": "sol", "started_at": "2026-09-28T10:00:05+00:00",
             "finished_at": "2026-09-28T10:00:09+00:00", "status": "ok", "blocked_by": "p-7"},
            {"id": "c1", "model": "nova", "started_at": "2026-09-28T09:59:00+00:00",
             "finished_at": "2026-09-28T09:59:02+00:00", "status": "failed", "blocked_by": None},
        ]
    },
    "/api/usage": {"models": [{"model": "nova", "attempts": 2, "cost_usd": "0.000580"},
                              {"model": "sol", "attempts": 3, "cost_usd": "0.012345"}]},
}


class _Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


class MockOpener:
    def __init__(self, routes=None):
        self.routes = dict(CANNED if routes is None else routes)
        self.requests = []

    def __call__(self, req):
        self.requests.append(req)
        path = urlparse(req.full_url).path
        return _Resp(json.dumps(self.routes[path]).encode())
