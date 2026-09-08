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
    "docs/users/ko/installation.md",
    "docs/users/en/installation.md",
)
MARKER = "<!-- how-it-works-local-links -->"


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


if __name__ == "__main__":
    unittest.main()
