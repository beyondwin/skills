from __future__ import annotations

import re
import shutil
import tempfile
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
PAYLOAD = REPOSITORY_ROOT / "skills" / "image-workbench"
DOCS_ROOT = (REPOSITORY_ROOT / "docs").resolve()
DOC_PREFIX = "/beyondwin/skills/blob/main/docs/"


class PayloadDocumentationTests(unittest.TestCase):
    def assert_link_target_resolves(
        self, target: str, document: Path, payload_root: Path
    ) -> None:
        parsed = urlsplit(target)
        if parsed.scheme:
            self.assertEqual(parsed.scheme, "https")
            self.assertEqual(parsed.netloc, "github.com")
            self.assertTrue(parsed.path.startswith(DOC_PREFIX))
            resolved = (
                DOCS_ROOT / unquote(parsed.path[len(DOC_PREFIX) :])
            ).resolve()
            self.assertTrue(resolved.is_relative_to(DOCS_ROOT), target)
            self.assertTrue(resolved.is_file(), target)
            return
        resolved = (document.parent / unquote(parsed.path)).resolve()
        self.assertTrue(resolved.is_relative_to(payload_root.resolve()), target)
        self.assertTrue(resolved.is_file(), target)

    def test_public_doc_url_rejects_encoded_parent_traversal(self):
        valid = (
            "https://github.com/beyondwin/skills/blob/main/"
            "docs/users/en/installation.md"
        )
        escaped = (
            "https://github.com/beyondwin/skills/blob/main/"
            "docs/%2e%2e/skills/image-workbench/SKILL.md"
        )

        self.assert_link_target_resolves(valid, PAYLOAD / "README.md", PAYLOAD)
        with self.assertRaises(AssertionError):
            self.assert_link_target_resolves(
                escaped, PAYLOAD / "README.md", PAYLOAD
            )

    def test_readme_links_work_from_standalone_payload(self):
        with tempfile.TemporaryDirectory(prefix="image payload ") as directory:
            root = Path(directory) / "image-workbench"
            shutil.copytree(PAYLOAD, root)
            for name in ("README.md", "README.en.md"):
                document = root / name
                targets = re.findall(
                    r"\[[^\]]+\]\(([^)]+)\)",
                    document.read_text(encoding="utf-8"),
                )
                self.assertTrue(targets, name)
                for target in targets:
                    with self.subTest(document=name, target=target):
                        self.assert_link_target_resolves(target, document, root)


if __name__ == "__main__":
    unittest.main()
