from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from support import EVIDENCE_DIR, error_code, run


VERSION_LINE = b'{"cli_version":"2.0.0","schema":2,"skill_name":"pre-sdd-review"}\n'


class VersionTests(unittest.TestCase):
    def test_version_is_canonical_and_touches_no_home(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "home"
            code, out, err = run(["--version"], home=home, cwd=Path(directory))
            self.assertEqual((code, out.encode("utf-8"), err), (0, VERSION_LINE, ""))
            self.assertFalse(home.exists())

    def test_version_rejects_extra_arguments(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            code, out, err = run(["--version", "summary"], home=Path(directory), cwd=Path(directory))
            self.assertEqual((code, out), (2, ""))
            self.assertEqual(error_code(err), "invalid-arguments")

    def test_unknown_command_uses_error_envelope(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            code, out, err = run(["prune"], home=Path(directory), cwd=Path(directory))
            self.assertEqual((code, out), (2, ""))
            envelope = json.loads(err)
            self.assertEqual(set(envelope), {"error"})
            self.assertEqual(set(envelope["error"]), {"code", "message"})
            self.assertEqual(envelope["error"]["code"], "invalid-arguments")

    def test_script_runs_as_a_file_without_installation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "home"
            completed = subprocess.run(
                [sys.executable, str(EVIDENCE_DIR / "evidence.py"), "--version"],
                check=False,
                capture_output=True,
                env={"PRE_SDD_REVIEW_HOME": str(home), "PYTHONDONTWRITEBYTECODE": "1", "PATH": ""},
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(completed.stdout, VERSION_LINE)
            self.assertFalse(home.exists())


if __name__ == "__main__":
    unittest.main()
