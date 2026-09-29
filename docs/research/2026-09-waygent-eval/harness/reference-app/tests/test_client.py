import unittest

from usage.client import Client, render_calls
from usage.mock import MockOpener


class ClientTest(unittest.TestCase):
    def test_calls_render(self):
        rows = Client("http://x", opener=MockOpener()).calls()
        self.assertEqual([r.id for r in rows], ["c2", "c1"])
        self.assertIn("10:00:09", render_calls(rows))
