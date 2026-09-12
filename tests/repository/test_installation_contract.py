import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOCUMENTS = (
    "skills/how-it-works/README.md",
    "skills/how-it-works/README.en.md",
    "docs/users/ko/install-local.md",
    "docs/users/en/install-local.md",
)
MARKER = "<!-- how-it-works-local-links -->"

# Arrange a real competing entry at the last possible point, then call the
# original syscall wrapper. No sleeps or synthetic FileExistsError are involved.
RACE_INSTALLER = r"""
import json
import os
import sys
from pathlib import Path

race_source = Path(sys.argv[1])
race_target = Path(sys.argv[2])
race_state = sys.argv.pop(3)
race_record = Path(sys.argv.pop(3))
race_original_symlink_to = Path.symlink_to

def create_competing_entry_then_link(self, *args, **kwargs):
    Path.symlink_to = race_original_symlink_to
    assert self == race_target
    assert not os.path.lexists(self)
    if race_state == "file":
        self.write_bytes(b"file keep")
    elif race_state == "directory":
        self.mkdir()
        (self / "keep.txt").write_bytes(b"directory keep")
    else:
        destination = {
            "same": race_source,
            "other": race_source.parent.parent / "other source",
            "dangling": race_source.parent.parent / "missing",
        }[race_state]
        os.symlink(destination, self, target_is_directory=True)
    before = self.lstat()
    race_record.write_text(json.dumps({
        "identity": [before.st_dev, before.st_ino, before.st_mode,
                     before.st_mtime_ns, before.st_ctime_ns],
        "link": os.readlink(self) if self.is_symlink() else None,
    }), encoding="utf-8")
    return race_original_symlink_to(self, *args, **kwargs)

Path.symlink_to = create_competing_entry_then_link
exec(compile(sys.stdin.read(), "<documented installer>", "exec"))
"""


def installation_block(relative: str) -> str:
    text = (ROOT / relative).read_text(encoding="utf-8")
    if text.count(MARKER) != 1:
        raise AssertionError(f"one installation block required: {relative}")
    tail = text.split(MARKER, 1)[1]
    match = re.match(r"\s*```python\n(.*?)\n```", tail, re.S)
    if match is None:
        raise AssertionError(f"Python block must follow marker: {relative}")
    return match.group(1)


class InstallationContractTests(unittest.TestCase):
    def test_documented_installation_preserves_targets_appearing_before_creation(self):
        # Removing the collision handler leaks a traceback; retrying after an
        # unlink destroys the competing entry. Both break this contract.
        for document in DOCUMENTS:
            for state in ("file", "directory", "same", "other", "dangling"):
                with self.subTest(document=document, state=state), tempfile.TemporaryDirectory() as tmp:
                    base = Path(tmp)
                    source = base / "source with spaces" / "how-it-works"
                    source.mkdir(parents=True)
                    (source / "SKILL.md").write_bytes(b"name: how-it-works\n")
                    other = base / "other source"
                    other.mkdir()
                    (other / "keep.txt").write_bytes(b"other keep")
                    target = base / "target with spaces" / "how-it-works"
                    record = base / "race-record.json"
                    result = subprocess.run(
                        [sys.executable, "-c", RACE_INSTALLER,
                         str(source), str(target), state, str(record)],
                        input=installation_block(document),
                        capture_output=True, text=True, check=False,
                    )
                    if os.name == "nt" and "WinError 1314" in result.stderr:
                        self.skipTest("symlink privilege unavailable on this Windows runner")
                    self.assertTrue(record.is_file(), result.stderr)
                    self.assertNotEqual(result.returncode, 0, result.stdout)
                    self.assertNotIn("Traceback", result.stderr)
                    self.assertTrue(result.stderr.strip(), "collision needs a user-visible reason")
                    before = json.loads(record.read_text(encoding="utf-8"))
                    after = target.lstat()
                    self.assertEqual(
                        [after.st_dev, after.st_ino, after.st_mode,
                         after.st_mtime_ns, after.st_ctime_ns],
                        before["identity"],
                    )
                    if state in ("same", "other", "dangling"):
                        self.assertTrue(target.is_symlink())
                        self.assertEqual(os.readlink(target), before["link"])
                    elif state == "file":
                        self.assertFalse(target.is_symlink())
                        self.assertEqual(target.read_bytes(), b"file keep")
                    else:
                        self.assertFalse(target.is_symlink())
                        self.assertEqual((target / "keep.txt").read_bytes(), b"directory keep")
                    self.assertEqual(sorted(p.name for p in source.iterdir()), ["SKILL.md"])
                    self.assertEqual((source / "SKILL.md").read_bytes(), b"name: how-it-works\n")
                    self.assertEqual((other / "keep.txt").read_bytes(), b"other keep")
                    self.assertFalse((base / "missing").exists())

    def test_documented_link_installation_preserves_existing_targets(self):
        for document in DOCUMENTS:
            with self.subTest(document=document):
                block = installation_block(document)
                for state in ("absent", "same", "directory", "file", "other", "dangling"):
                    with self.subTest(state=state), tempfile.TemporaryDirectory() as tmp:
                        base = Path(tmp)
                        source = base / "source with spaces" / "how-it-works"
                        source.mkdir(parents=True)
                        (source / "SKILL.md").write_bytes(b"name: how-it-works\n")
                        other = base / "other source"
                        other.mkdir()
                        (other / "keep.txt").write_bytes(b"other keep")
                        target = base / "target with spaces" / "how-it-works"
                        target.parent.mkdir()
                        try:
                            if state == "same":
                                target.symlink_to(source, target_is_directory=True)
                            elif state == "directory":
                                target.mkdir()
                                (target / "keep.txt").write_bytes(b"keep")
                            elif state == "file":
                                target.write_bytes(b"file keep")
                            elif state == "other":
                                target.symlink_to(other, target_is_directory=True)
                            elif state == "dangling":
                                target.symlink_to(base / "missing", target_is_directory=True)
                        except OSError as exc:
                            if os.name == "nt" and getattr(exc, "winerror", None) == 1314:
                                self.skipTest("symlink privilege unavailable on this Windows runner")
                            raise
                        link_before = os.readlink(target) if target.is_symlink() else None
                        result = subprocess.run(
                            [sys.executable, "-c", block, str(source), str(target)],
                            capture_output=True, text=True, check=False,
                        )
                        if state in ("absent", "same"):
                            if os.name == "nt" and "WinError 1314" in result.stderr:
                                self.skipTest("symlink privilege unavailable on this Windows runner")
                            self.assertEqual(result.returncode, 0, result.stderr)
                            self.assertTrue(target.is_symlink())
                            self.assertEqual(target.resolve(), source.resolve())
                            installed_link = os.readlink(target)
                            again = subprocess.run(
                                [sys.executable, "-c", block, str(source), str(target)],
                                capture_output=True, text=True, check=False,
                            )
                            self.assertEqual(again.returncode, 0, again.stderr)
                            self.assertEqual(os.readlink(target), installed_link)
                        else:
                            self.assertNotEqual(result.returncode, 0)
                            if link_before is not None:
                                self.assertTrue(target.is_symlink())
                                self.assertEqual(os.readlink(target), link_before)
                            elif state == "file":
                                self.assertFalse(target.is_symlink())
                                self.assertEqual(target.read_bytes(), b"file keep")
                            else:
                                self.assertFalse(target.is_symlink())
                                self.assertEqual((target / "keep.txt").read_bytes(), b"keep")
                        self.assertEqual(sorted(p.name for p in source.iterdir()), ["SKILL.md"])
                        self.assertEqual((source / "SKILL.md").read_bytes(), b"name: how-it-works\n")
                        self.assertEqual((other / "keep.txt").read_bytes(), b"other keep")
                        self.assertFalse((base / "missing").exists())


LINKER_FIXTURE = ROOT / "tests" / "repository" / "fixtures" / "link-skill.py"
LINKER_SURFACES = (
    ("skills/how-it-works/README.md", "<!-- how-it-works-local-links -->"),
    ("skills/how-it-works/README.en.md", "<!-- how-it-works-local-links -->"),
    ("docs/users/ko/install-local.md", "<!-- how-it-works-local-links -->"),
    ("docs/users/en/install-local.md", "<!-- how-it-works-local-links -->"),
    ("skills/sddx/README.md", "<!-- sddx-local-links -->"),
    ("skills/sddx/README.en.md", "<!-- sddx-local-links -->"),
    ("docs/users/ko/install-local.md", "<!-- sddx-local-links -->"),
    ("docs/users/en/install-local.md", "<!-- sddx-local-links -->"),
    ("skills/image-workbench/README.md", "<!-- image-workbench-local-links -->"),
    ("skills/image-workbench/README.en.md", "<!-- image-workbench-local-links -->"),
    ("docs/users/ko/install-local.md", "<!-- image-workbench-local-links -->"),
    ("docs/users/en/install-local.md", "<!-- image-workbench-local-links -->"),
)


def documented_linker(relative: str, marker: str) -> str:
    text = (ROOT / relative).read_text(encoding="utf-8")
    if text.count(marker) != 1:
        raise AssertionError(f"one installation block required: {relative} {marker}")
    tail = text.split(marker, 1)[1]
    match = re.match(r"\s*```python\n(.*?)\n```", tail, re.S)
    if match is None:
        raise AssertionError(f"Python block must follow marker: {relative} {marker}")
    return match.group(1)


class CanonicalLinkerFixtureTests(unittest.TestCase):
    def test_every_documented_linker_matches_the_fixture(self) -> None:
        expected = LINKER_FIXTURE.read_text(encoding="utf-8")
        if expected.endswith("\n"):
            expected = expected[:-1]
        for relative, marker in LINKER_SURFACES:
            with self.subTest(relative=relative, marker=marker):
                self.assertEqual(documented_linker(relative, marker), expected)


if __name__ == "__main__":
    unittest.main()
