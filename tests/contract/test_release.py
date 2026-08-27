from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUILD_RELEASE_PATH = ROOT / "scripts" / "build_release.py"
WRAPPER_MESSAGE = (
    "scripts/build_release.py no longer builds a shared-version bundle. "
    "Use scripts/release.py after the independent release pipeline lands.\n"
)


class BuildReleaseWrapperTests(unittest.TestCase):
    def test_build_release_module_exists(self) -> None:
        self.assertTrue(BUILD_RELEASE_PATH.is_file(), "scripts.build_release does not exist")

    def test_wrapper_prints_exact_message_exits_2_and_creates_no_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(BUILD_RELEASE_PATH),
                    "--version",
                    "2.0.0",
                    "--output",
                    str(output),
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 2)
            self.assertEqual(completed.stderr, WRAPPER_MESSAGE)
            self.assertEqual(completed.stdout, "")
            self.assertEqual(list(output.iterdir()), [])
