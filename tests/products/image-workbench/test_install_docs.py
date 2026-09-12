from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.repository.test_installation_contract import installation_block


MARKER = "<!-- image-workbench-local-links -->"
AGENTS = (
    'python3 - "$PWD/skills/image-workbench" '
    '"$HOME/.agents/skills/image-workbench" <<\'PY\''
)
UNLINK = "unlink ~/.agents/skills/image-workbench"
INSTALLER = (
    "$skill-installer https://github.com/beyondwin/skills/tree/main/"
    "skills/image-workbench"
)
DOCUMENTS = (
    "skills/image-workbench/README.md",
    "skills/image-workbench/README.en.md",
    "docs/users/ko/install-local.md",
    "docs/users/en/install-local.md",
)


class ImageWorkbenchInstallTests(unittest.TestCase):
    def test_local_link_marker_and_agents_invocation(self) -> None:
        how_it_works_fence = installation_block("skills/how-it-works/README.md")
        for relative in DOCUMENTS:
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertEqual(text.count(MARKER), 1, relative)
            self.assertIn(AGENTS, text)
            self.assertIn(UNLINK, text)
            self.assertNotIn("ln -s", text)
            self.assertNotIn("~/.grok/skills/image-workbench", text)
            self.assertNotIn("$HOME/.grok/skills/image-workbench", text)
            self.assertNotIn("$HOME/.claude/skills/image-workbench", text)
            self.assertEqual(text.count("$HOME/.agents/skills/image-workbench"), 1, relative)
            tail = text.split(MARKER, 1)[1]
            match = re.match(r"\s*```python\n(.*?)\n```", tail, re.S)
            self.assertIsNotNone(match, relative)
            self.assertEqual(match.group(1), how_it_works_fence, relative)

    def test_install_local_omits_codex_installer_command(self) -> None:
        for relative in (
            "docs/users/ko/install-local.md",
            "docs/users/en/install-local.md",
        ):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertNotIn(INSTALLER, text)

    def test_product_readme_keeps_codex_installer_command(self) -> None:
        for name in ("README.md", "README.en.md"):
            text = (ROOT / "skills" / "image-workbench" / name).read_text(
                encoding="utf-8"
            )
            self.assertIn(INSTALLER, text)
            self.assertIn("$image-workbench", text)
            self.assertIn("/image-workbench", text)
