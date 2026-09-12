from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.product_registry import load_registry

SKILL = ROOT / "skills" / "image-workbench" / "SKILL.md"
LIVE_RECORD = ROOT / "tests" / "products" / "image-workbench" / "live" / "smoke-record.json"
SMOKE_ITEMS = (
    "discovery",
    "explicit_brief",
    "implicit_and_near_miss",
    "output_contract",
)


def grok_claim_errors(
    *,
    hosts: tuple[str, ...],
    record_text: str | None,
    skill_bytes: bytes,
) -> tuple[str, ...]:
    if "grok" not in hosts:
        return ()
    if record_text is None:
        return ("grok claim missing live/smoke-record.json",)
    errors: list[str] = []
    if "/Users/" in record_text:
        errors.append("smoke-record contains an absolute home path")
    try:
        data = json.loads(record_text)
    except json.JSONDecodeError:
        return ("smoke-record is not JSON",)
    if not isinstance(data, dict):
        return ("smoke-record is not an object",)
    if "prompt" in data:
        errors.append("smoke-record contains a prompt field")
    for item in SMOKE_ITEMS:
        if data.get(item) != "pass":
            errors.append(f"smoke-record {item} is not pass")
    expected = hashlib.sha256(skill_bytes).hexdigest()
    if data.get("skill_md_sha256") != expected:
        errors.append("smoke-record skill_md_sha256 does not match SKILL.md")
    inspector = data.get("inspector")
    if not isinstance(inspector, dict):
        errors.append("smoke-record missing inspector object")
    else:
        if inspector.get("format") not in {"png", "jpeg", "webp"}:
            errors.append("smoke-record inspector format is not png, jpeg, or webp")
        if not isinstance(inspector.get("width"), int) or inspector.get("width") <= 0:
            errors.append("smoke-record inspector width is missing")
        if not isinstance(inspector.get("height"), int) or inspector.get("height") <= 0:
            errors.append("smoke-record inspector height is missing")
    return tuple(errors)


class ImageWorkbenchLiveRecordTests(unittest.TestCase):
    def test_grok_registry_claim_requires_four_pass_smoke_bound_to_skill_md(self) -> None:
        hosts = load_registry(ROOT / "products.toml").require("image-workbench").supported_hosts
        text = LIVE_RECORD.read_text(encoding="utf-8") if LIVE_RECORD.is_file() else None
        self.assertEqual(
            grok_claim_errors(
                hosts=hosts,
                record_text=text,
                skill_bytes=SKILL.read_bytes(),
            ),
            (),
        )

    def test_missing_record_or_failed_item_or_stale_hash_is_rejected(self) -> None:
        hosts = ("codex", "grok")
        skill = SKILL.read_bytes()
        current = LIVE_RECORD.read_text(encoding="utf-8")
        self.assertIn(
            "grok claim missing live/smoke-record.json",
            grok_claim_errors(hosts=hosts, record_text=None, skill_bytes=skill),
        )
        broken = json.loads(current)
        broken["output_contract"] = "fail"
        self.assertIn(
            "smoke-record output_contract is not pass",
            grok_claim_errors(
                hosts=hosts,
                record_text=json.dumps(broken),
                skill_bytes=skill,
            ),
        )
        stale = json.loads(current)
        stale["skill_md_sha256"] = "0" * 64
        self.assertIn(
            "smoke-record skill_md_sha256 does not match SKILL.md",
            grok_claim_errors(
                hosts=hosts,
                record_text=json.dumps(stale),
                skill_bytes=skill,
            ),
        )
        self.assertEqual(
            grok_claim_errors(hosts=("codex",), record_text=None, skill_bytes=skill),
            (),
        )
