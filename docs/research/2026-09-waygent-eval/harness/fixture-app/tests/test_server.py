import json
import threading
import unittest
import urllib.request

from usage.config import Config
from usage.server import make_server
from usage.store import CallStore


class ServerTest(unittest.TestCase):
    def setUp(self):
        self.srv = make_server(Config(port=0), CallStore.load("data/calls.jsonl"), port=0)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.srv.server_address[1]}"

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()

    def test_calls_newest_first(self):
        with urllib.request.urlopen(self.base + "/api/calls") as r:
            ids = [c["id"] for c in json.loads(r.read())["calls"]]
        self.assertEqual(ids[0], "c10")
        self.assertEqual(len(ids), 10)
