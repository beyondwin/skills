import unittest

from promptops.store import PromptStore


class EventsTest(unittest.TestCase):
    def test_create_emits(self):
        s = PromptStore()
        s.create("a", "x")
        self.assertEqual(s.events.of("prompt.created"), [{"id": "a"}])
