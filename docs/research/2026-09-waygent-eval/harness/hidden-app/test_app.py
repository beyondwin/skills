"""Hidden acceptance tests for the app fixture. Never copied into the agent's repo.

"basic" tests follow the plan's explicit sentences. "trap" tests probe a rule the design
states but the plan does not name, each modeled on a defect a real run shipped: money on
failure paths, contract drift between server, client and mock, and startup config.
They run the real server and the real client together, as the app check would.
"""
import json
import os
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from decimal import Decimal

from usage import client as client_mod
from usage import server as server_mod
from usage.config import ConfigError, load_config
from usage.store import CallStore

SEED = "data/calls.jsonl"


def toml(text):
    fd, path = tempfile.mkstemp(suffix=".toml")
    with os.fdopen(fd, "w") as f:
        f.write(text)
    return path


class Live:
    """Real server on a free port with the given config file."""

    def __init__(self, config_path, store=None):
        self.srv = server_mod.make_server(load_config(config_path), store or CallStore.load(SEED), port=0)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.srv.server_address[1]}"

    def get(self, path, caller="console"):
        headers = {"X-Caller": caller} if caller else {}
        try:
            with urllib.request.urlopen(urllib.request.Request(self.base + path, headers=headers)) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            with e:
                return e.code, json.loads(e.read() or b"{}")

    def close(self):
        self.srv.shutdown()
        self.srv.server_close()


CONSOLE = toml('port = 0\nallowed_callers = ["console"]\n')


class AppTest(unittest.TestCase):
    def live(self, path=CONSOLE, store=None):
        lv = Live(path, store)
        self.addCleanup(lv.close)
        return lv

    # basic: the plan's sentences

    def test_t1_basic_usage_shape(self):
        status, body = self.live().get("/api/usage")
        self.assertEqual(status, 200)
        self.assertEqual([m["model"] for m in body["models"]], ["nova", "sol"])
        self.assertEqual(set(body["models"][0]), {"model", "attempts", "cost_usd"})

    def test_t1_basic_client_usage_mock(self):
        rows = client_mod.Client("http://x", opener=__import__("usage.mock", fromlist=["x"]).MockOpener()).usage()
        self.assertTrue(rows and isinstance(rows[0].cost_usd, Decimal))

    def test_t2_basic_blocked_field(self):
        status, body = self.live().get("/api/calls")
        by_id = {c["id"]: c for c in body["calls"]}
        self.assertEqual(by_id["c04"]["blocked_by"], "p-7")

    def test_t3_basic_config_required(self):
        with self.assertRaises(ConfigError):
            load_config(toml("port = 0\n"))

    def test_t3_basic_stranger_forbidden(self):
        status, body = self.live().get("/api/calls", caller="stranger")
        self.assertEqual((status, body.get("error")), (403, "caller_not_allowed"))

    # trap: money on failure paths (design 2, 4)

    def test_t1_trap_estimated_not_billed(self):
        _, body = self.live().get("/api/usage")
        got = {m["model"]: (m["attempts"], m["cost_usd"]) for m in body["models"]}
        self.assertEqual(got["sol"], (6, "0.016120"))  # estimated failures excluded, billed failure kept
        self.assertEqual(got["nova"], (4, "0.001715"))

    def test_t1_trap_round_once(self):
        rows = [dict(id=f"n{i}", model="nova", started_at="2026-09-28T10:00:00+00:00",
                     finished_at="2026-09-28T10:00:01+00:00", status="ok",
                     input_tokens=1, output_tokens=0) for i in range(3)]
        _, body = self.live(store=CallStore.from_dicts(rows)).get("/api/usage")
        self.assertEqual(body["models"][0]["cost_usd"], "0.000002")

    # trap: contract drift, real server with real client (design 3, 5, 6)

    def test_t2_trap_null_not_empty_string(self):
        _, body = self.live().get("/api/calls")
        by_id = {c["id"]: c for c in body["calls"]}
        self.assertIsNone(by_id["c01"]["blocked_by"])

    def test_t2_trap_real_screen_marks_only_blocked(self):
        lv = self.live()
        screen = client_mod.render_calls(client_mod.Client(lv.base).calls())
        marked = [line.split()[3] for line in screen.splitlines() if "차단" in line]
        self.assertEqual(sorted(marked), ["c04", "c08"])

    def test_t3_trap_console_sends_caller(self):
        lv = self.live()
        self.assertEqual(len(client_mod.Client(lv.base).calls()), 10)

    def test_t3_trap_repo_dev_config_serves_console(self):
        lv = self.live(path="config/dev.toml")
        self.assertEqual(len(client_mod.Client(lv.base).usage()), 2)

    # trap: startup config and deploy (design 6, 7)

    def test_t3_trap_prod_config_starts_and_serves_console(self):
        cfg = load_config("config/prod.toml")
        self.assertIn("console", cfg.allowed_callers)
