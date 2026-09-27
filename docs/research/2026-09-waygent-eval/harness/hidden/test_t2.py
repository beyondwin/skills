"""Hidden acceptance tests. Never copied into the agent's repo.

Each test name starts with the task (t1..t6) and ends with the principle or kind it probes.
"basic" tests follow the plan's explicit sentences; "edge" tests probe behavior the plan
states only as a principle (the class a per-task or final review is supposed to catch).
"""
import asyncio
import unittest

from promptops.fake_model import FakeModel
from promptops.store import PromptMissing, PromptStore, VersionConflict


def run(coro):
    return asyncio.run(coro)


def store_with(**bodies):
    s = PromptStore()
    for k, v in bodies.items():
        s.create(k, v)
    return s


from promptops.session import EditSession



class T2(unittest.TestCase):
    def test_t2_basic_edit_save(self):
        s = store_with(a="x")
        e = EditSession(s, "a")
        e.edit("y")
        self.assertTrue(e.dirty)
        e.save()
        self.assertFalse(e.dirty)
        self.assertEqual(e.base_version, 2)
        e.edit("z")
        e.save()
        self.assertEqual(s.get("a").body, "z")

    def test_t2_edge_clean_reload_takes_new_values_and_saves(self):
        # v26 high: after reload the form kept old values, and saving raised a 409.
        s = store_with(a="x")
        e = EditSession(s, "a")
        s.save("a", "remote", 1)
        e.reload()
        self.assertEqual(e.body, "remote")
        self.assertFalse(e.conflict)
        e.edit("mine")
        e.save()
        self.assertEqual(s.get("a").body, "mine")

    def test_t2_edge_dirty_reload_keeps_edit_and_flags_conflict(self):
        s = store_with(a="x")
        e = EditSession(s, "a")
        e.edit("mine")
        s.save("a", "remote", 1)
        e.reload()
        self.assertEqual(e.body, "mine")
        self.assertTrue(e.conflict)

    def test_t2_edge_no_lost_update_after_reload(self):
        # Principle 1: reload must not let the next save silently overwrite the remote change.
        s = store_with(a="x")
        e = EditSession(s, "a")
        e.edit("mine")
        s.save("a", "remote", 1)
        e.reload()
        try:
            e.save()
        except VersionConflict:
            pass
        self.assertEqual(s.get("a").body, "remote")

    def test_t2_edge_dirty_reload_no_remote_change(self):
        s = store_with(a="x")
        e = EditSession(s, "a")
        e.edit("mine")
        e.reload()
        self.assertEqual(e.body, "mine")
        self.assertFalse(e.conflict)
        e.save()
        self.assertEqual(s.get("a").body, "mine")

    def test_t2_edge_discard_after_conflict(self):
        s = store_with(a="x")
        e = EditSession(s, "a")
        e.edit("mine")
        s.save("a", "remote", 1)
        e.reload()
        e.discard()
        self.assertEqual(e.body, "remote")
        self.assertFalse(e.dirty)
        self.assertFalse(e.conflict)
        e.edit("again")
        e.save()
        self.assertEqual(s.get("a").body, "again")

    def test_t2_edge_missing_on_reload(self):
        s = store_with(a="x")
        e = EditSession(s, "a")
        s.delete("a")
        e.reload()
        self.assertTrue(e.missing)
        with self.assertRaises(PromptMissing):
            e.save()
