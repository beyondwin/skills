import tempfile
import unittest
from pathlib import Path

from scripts.lib.product_contract import _check_relative_links


class StandaloneLinkTests(unittest.TestCase):
    def test_readme_cannot_escape_standalone_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = root / "sample"
            payload.mkdir()
            (root / "outside.md").write_text("repository-only", encoding="utf-8")
            for filename in ("README.md", "README.en.md"):
                with self.subTest(filename=filename):
                    self.assertEqual(
                        _check_relative_links(payload, filename, "[guide](../outside.md)"),
                        [f"broken relative link in {filename}: ../outside.md"],
                    )
                    self.assertEqual(_check_relative_links(
                        payload, filename,
                        "[guide](https://github.com/beyondwin/skills/blob/main/docs/README.md)",
                    ), [])

    def test_readme_internal_links_still_require_existing_payload_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            payload = Path(tmp)
            (payload / "guide.md").write_text("standalone guide", encoding="utf-8")
            for filename in ("README.md", "README.en.md"):
                with self.subTest(filename=filename):
                    self.assertEqual(_check_relative_links(
                        payload, filename, "[guide](guide.md#section)",
                    ), [])
                    self.assertEqual(_check_relative_links(
                        payload, filename, "[guide](missing.md)",
                    ), [f"broken relative link in {filename}: missing.md"])


if __name__ == "__main__":
    unittest.main()
