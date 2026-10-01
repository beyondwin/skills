from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime
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


RUN_AT_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:\d{2})$"
)


def skill_binding_sha256(skill_bytes: bytes) -> str:
    """SHA-256 of SKILL.md without the frontmatter `metadata:` block.

    The block is the `metadata:` line and the two-space-indented lines under
    it, so a version-only bump keeps a valid smoke bound to the same text.
    """
    lines = skill_bytes.decode("utf-8").splitlines(keepends=True)
    if not lines or lines[0].rstrip("\r\n") != "---":
        raise ValueError("SKILL.md has no frontmatter")
    kept: list[str] = []
    in_frontmatter = True
    in_metadata = False
    for index, line in enumerate(lines):
        bare = line.rstrip("\r\n")
        if index > 0 and in_frontmatter and bare == "---":
            in_frontmatter = False
            in_metadata = False
        elif in_frontmatter and bare == "metadata:":
            in_metadata = True
            continue
        elif in_metadata and line.startswith("  "):
            continue
        else:
            in_metadata = False
        kept.append(line)
    return hashlib.sha256("".join(kept).encode("utf-8")).hexdigest()


def _is_iso_run_at(value: object) -> bool:
    if not isinstance(value, str) or not RUN_AT_RE.fullmatch(value):
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


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
    if data.get("skill_md_sha256") != skill_binding_sha256(skill_bytes):
        errors.append("smoke-record skill_md_sha256 does not match SKILL.md")
    session_id = data.get("session_id")
    if not isinstance(session_id, str) or not session_id.strip():
        errors.append("smoke-record session_id is missing")
    if not _is_iso_run_at(data.get("run_at")):
        errors.append("smoke-record run_at is not an ISO timestamp with a time zone")
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

    def test_binding_hash_ignores_only_the_metadata_block(self) -> None:
        skill = SKILL.read_bytes()
        text = skill.decode("utf-8")
        bumped = text.replace('  version: "', '  version: "9', 1).replace(
            '  updated_at: "', '  updated_at: "1', 1
        )
        self.assertNotEqual(bumped, text)
        self.assertEqual(
            skill_binding_sha256(bumped.encode("utf-8")), skill_binding_sha256(skill)
        )
        body_changed = text + "\nOne more rule.\n"
        self.assertNotEqual(
            skill_binding_sha256(body_changed.encode("utf-8")), skill_binding_sha256(skill)
        )
        description_changed = text.replace("description: ", "description: x", 1)
        self.assertNotEqual(
            skill_binding_sha256(description_changed.encode("utf-8")),
            skill_binding_sha256(skill),
        )
        self.assertNotEqual(skill_binding_sha256(skill), hashlib.sha256(skill).hexdigest())

    def test_record_requires_session_id_and_iso_run_at(self) -> None:
        hosts = ("codex", "grok")
        skill = SKILL.read_bytes()
        record = {item: "pass" for item in SMOKE_ITEMS}
        record.update(
            skill_md_sha256=skill_binding_sha256(skill),
            session_id="01a0ffff-0000-7000-8000-000000000000",
            run_at="2026-10-01T09:30:00+09:00",
            inspector={"format": "jpeg", "width": 1280, "height": 720},
        )
        self.assertEqual(
            grok_claim_errors(hosts=hosts, record_text=json.dumps(record), skill_bytes=skill),
            (),
        )
        for field, value, error in (
            ("session_id", None, "smoke-record session_id is missing"),
            ("session_id", "", "smoke-record session_id is missing"),
            ("run_at", None, "smoke-record run_at is not an ISO timestamp with a time zone"),
            ("run_at", "2026-10-01", "smoke-record run_at is not an ISO timestamp with a time zone"),
            ("run_at", "2026-10-01T09:30:00", "smoke-record run_at is not an ISO timestamp with a time zone"),
            ("run_at", "yesterday", "smoke-record run_at is not an ISO timestamp with a time zone"),
        ):
            with self.subTest(field=field, value=value):
                broken = dict(record)
                if value is None:
                    del broken[field]
                else:
                    broken[field] = value
                self.assertIn(
                    error,
                    grok_claim_errors(hosts=hosts, record_text=json.dumps(broken), skill_bytes=skill),
                )
        utc = dict(record, run_at="2026-10-01T00:30:00Z")
        self.assertEqual(
            grok_claim_errors(hosts=hosts, record_text=json.dumps(utc), skill_bytes=skill),
            (),
        )
