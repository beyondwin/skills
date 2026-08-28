from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.product_contract import parse_skill_frontmatter  # noqa: E402
from scripts.lib.product_registry import load_registry  # noqa: E402

SKILL = ROOT / "skills" / "how-it-works"
CASES = ROOT / "tests" / "products" / "how-it-works" / "cases.json"
PORTABLE_FIELDS = {"name", "description", "license", "compatibility", "metadata"}
CASE_IDS = [
    "broad-slice",
    "missing-rung",
    "explicit-dns-path",
    "implicit-positive",
    "near-miss-debug",
    "near-miss-eli5",
    "jargon-rung",
    "no-renderer",
    "no-fetched-source",
]
REQUIRED_DELIVERABLE_PHRASES = (
    "one-sentence claim",
    "Mermaid",
    "numbered hop list",
    "rung-specific body",
    "adjacent slices",
    "one next move",
)
OUTPUT_CHROME = (
    "# {slice} · {그림|길|뼈대|허점}",
    "{high-stakes banner or omit}",
    "## 한 줄 / One sentence",
    "## 지도 / Map",
    "```mermaid",
    "{diagram source}",
    "1. **H1** — {what moves or changes}",
    "2. **H2** — {what moves or changes}",
    "## 본문 / Body",
    "## 지금 다루지 않은 것 / Adjacent slices",
    "다음 / Next: {exactly one move}",
)
RUNTIME_FLOW = (
    "fill slice, type, rung, language",
    "emit one intent line",
    "read focused references",
    "emit complete Markdown + Mermaid source + numbered hop list",
    "offer one next move",
)
PAGE_CONTRACT_MARKERS = (
    "artifact" + "-design",
    "published" + " page",
    "<pre class=" + '"mermaid">',
    "same file" + " path",
)
HOST_TOOL_MARKERS = (
    "artifact" + "-design",
    "Artifact" + " tool",
    "published" + " page",
    "<pre class=" + '"mermaid">',
)


def section(text: str, start_heading: str, end_heading: str) -> str:
    start = text.find(start_heading)
    end = text.find(end_heading)
    if start < 0:
        raise AssertionError(f"missing heading: {start_heading}")
    if end < 0:
        raise AssertionError(f"missing heading: {end_heading}")
    if end <= start:
        raise AssertionError(f"{end_heading!r} must appear after {start_heading!r}")
    return text[start + len(start_heading) : end]


def _skill_markdown() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in SKILL.rglob("*.md"))


def _reference(name: str) -> str:
    return (SKILL / "references" / name).read_text(encoding="utf-8")


LIVE = ROOT / "tests" / "products" / "how-it-works" / "live"
LIVE_CASES = LIVE / "cases.json"
LIVE_README = LIVE / "README.md"
LIVE_RECORD = LIVE / "smoke-record.json"
LIVE_CASE_IDS = ("explicit-dns-path", "implicit-dns-path", "near-miss-debug")
LIVE_HOSTS = ("codex", "claude-code", "grok", "cursor")
LIVE_CASE_FIELDS = {
    "explicit-dns-path": {"id", "prompt_codex", "prompt_slash", "expect"},
    "implicit-dns-path": {"id", "prompt", "expect"},
    "near-miss-debug": {"id", "prompt", "expect"},
}
HOST_RECORD_FIELDS = {"host", "client_version", "cases", "verdict"}
CASE_VERDICTS = {"pass", "fail", "not_measured"}
HOST_VERDICTS = {"supported", "unsupported", "not_measured"}
FORBIDDEN_LIVE_KEYS = {
    "stdout",
    "stderr",
    "response",
    "transcript",
    "screenshot",
    "receipt",
    "credential",
    "body",
}
LIVE_CASES_PAYLOAD = {
    "schema_version": 1,
    "cases": [
        {
            "id": "explicit-dns-path",
            "prompt_codex": "$how-it-works DNS가 브라우저 요청에서 IP 주소가 되는 길을 보여줘",
            "prompt_slash": "/how-it-works DNS가 브라우저 요청에서 IP 주소가 되는 길을 보여줘",
            "expect": [
                "discovered",
                "explicit",
                "claim",
                "mermaid",
                "numbered_hops",
                "body",
                "adjacent_slices",
                "next_move",
            ],
        },
        {
            "id": "implicit-dns-path",
            "prompt": "DNS 요청이 브라우저에서 어디를 거쳐 IP 주소가 되는지 길로 보여줘",
            "expect": ["implicit", "claim", "mermaid", "numbered_hops"],
        },
        {
            "id": "near-miss-debug",
            "prompt": "DNS resolver 테스트 실패를 고쳐줘. 동작 설명은 하지 마.",
            "expect": ["not_activated"],
        },
    ],
}
LIVE_README_MARKERS = (
    "pass/fail from observable output",
    "Do not use private or user prompts",
    "Do not commit full responses",
    "fresh session",
    "subscription/API quota",
    "unsupported",
    "outside the repository",
    "delete them after scoring",
)


class SectionHelperTests(unittest.TestCase):
    def test_section_requires_headings_in_order(self) -> None:
        text = "## Start\nbody\n## End\n"
        self.assertEqual(section(text, "## Start", "## End").strip(), "body")
        with self.assertRaises(AssertionError):
            section("## End\n", "## Start", "## End")
        with self.assertRaises(AssertionError):
            section("## Start\n## End\n", "## End", "## Start")


class HowItWorksPayloadTests(unittest.TestCase):
    def test_frontmatter_uses_portable_intersection(self) -> None:
        frontmatter = parse_skill_frontmatter((SKILL / "SKILL.md").read_text(encoding="utf-8"))
        self.assertEqual(set(frontmatter), PORTABLE_FIELDS)
        self.assertEqual(frontmatter["name"], "how-it-works")
        self.assertEqual(frontmatter["license"], "Apache-2.0")
        self.assertEqual(frontmatter["metadata"]["version"], "1.0.0")

    def test_frontmatter_has_no_host_tool_requirement(self) -> None:
        frontmatter = parse_skill_frontmatter((SKILL / "SKILL.md").read_text(encoding="utf-8"))
        compatibility = str(frontmatter["compatibility"]).lower()
        for forbidden in ("artifact", "canvas", "browser", "imagegen", "artifact" + "-design"):
            self.assertNotIn(forbidden, compatibility)

    def test_documentation_includes_supported_host_invocations(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        body = text.split("---", 2)[-1]
        self.assertIn("$how-it-works", body)
        self.assertIn("/how-it-works", body)
        self.assertIn("Codex", body)
        self.assertIn("Claude Code", body)
        self.assertNotIn("Grok", body)
        self.assertNotIn("Cursor", body)
        self.assertNotIn("@how-it-works", body)

    def test_runtime_emits_complete_output_without_reference_reads(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn(
            "Emit the complete required deliverable in the current reply even if you cannot read focused references this turn.",
            text,
        )

    def test_release_smoke_accepts_portable_frontmatter(self) -> None:
        from scripts.release import _smoke_how_it_works

        self.assertEqual(_smoke_how_it_works(SKILL), [])

    def test_runtime_does_not_require_openai_yaml(self) -> None:
        runtime_paths = [SKILL / "SKILL.md", *sorted((SKILL / "references").glob("*.md"))]
        runtime = "\n".join(path.read_text(encoding="utf-8") for path in runtime_paths)
        self.assertNotRegex(
            runtime,
            r"(?is)agents/openai\.yaml.{0,80}required|required.{0,80}agents/openai\.yaml",
        )

    def test_name_matches_directory(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("name: how-it-works\n", text.split("---")[1])
        self.assertEqual(SKILL.name, "how-it-works")

    def test_description_excludes_eli5_and_workflow(self) -> None:
        frontmatter = parse_skill_frontmatter((SKILL / "SKILL.md").read_text(encoding="utf-8"))
        description = str(frontmatter["description"])
        self.assertNotIn("/eli5", description.lower())
        self.assertNotIn("바로 / 하나", description)
        self.assertIn("Use when", description)
        self.assertIn("Do not use", description)
        self.assertIn("ELI5", description)

    def test_payload_files_exist(self) -> None:
        for rel in (
            "SKILL.md",
            "LICENSE.txt",
            "agents/openai.yaml",
            "references/output.md",
            "references/visuals.md",
            "references/korean.md",
            "references/stakes.md",
            "references/sources.md",
        ):
            self.assertTrue((SKILL / rel).is_file(), rel)

    def test_payload_excludes_eval_and_html_templates(self) -> None:
        names = {p.name for p in SKILL.rglob("*") if p.is_file()}
        self.assertNotIn("test_contract.py", names)
        self.assertNotIn("cases.json", names)
        joined = "\n".join(
            p.read_text(encoding="utf-8") for p in SKILL.rglob("*.md")
        )
        self.assertNotIn("<html", joined.lower())

    def test_cases_file_parses(self) -> None:
        data = json.loads(CASES.read_text(encoding="utf-8"))
        ids = [c["id"] for c in data["cases"]]
        self.assertEqual(ids, CASE_IDS)

    def test_cases_lock_synthetic_dns_and_rebase_behavior(self) -> None:
        data = json.loads(CASES.read_text(encoding="utf-8"))
        by_id = {case["id"]: case for case in data["cases"]}
        self.assertEqual(
            by_id["broad-slice"],
            {
                "id": "broad-slice",
                "prompt": "/how-it-works 인터넷",
                "must": ["three_slices", "one_question"],
                "forbidden": ["explanation"],
            },
        )
        self.assertEqual(
            by_id["missing-rung"],
            {
                "id": "missing-rung",
                "prompt": "/how-it-works DNS 흐름",
                "must": ["one_closed_question"],
                "forbidden": ["silent_rung"],
            },
        )
        self.assertEqual(
            by_id["explicit-dns-path"]["must"],
            ["claim", "mermaid", "numbered_hops", "body", "adjacent_slices", "next_move"],
        )
        self.assertEqual(by_id["explicit-dns-path"]["forbidden"], ["host_tool_required"])
        self.assertEqual(by_id["implicit-positive"]["must"], ["activate"])
        self.assertEqual(by_id["implicit-positive"]["forbidden"], ["debug"])
        self.assertEqual(by_id["near-miss-debug"]["must"], ["do_not_activate"])
        self.assertEqual(by_id["near-miss-eli5"]["prompt"], "/eli5 DNS")
        self.assertEqual(by_id["jargon-rung"]["must"], ["skeleton_default"])
        self.assertEqual(by_id["jargon-rung"]["forbidden"], ["picture_default"])
        self.assertEqual(by_id["no-renderer"]["must"], ["mermaid_source", "numbered_hops"])
        self.assertEqual(by_id["no-renderer"]["forbidden"], ["failure"])
        self.assertEqual(by_id["no-fetched-source"]["must"], ["omit_citations"])
        self.assertEqual(by_id["no-fetched-source"]["forbidden"], ["invented_citation"])

    def test_required_deliverable_is_complete_in_chat(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        required = section(text, "## Required deliverable", "## Optional preview")
        for phrase in REQUIRED_DELIVERABLE_PHRASES:
            self.assertIn(phrase, required)
        for forbidden in ("Artifact", "Canvas", "browser", "URL", "file"):
            self.assertNotIn(forbidden, required)

    def test_payload_has_no_mandatory_page_contract(self) -> None:
        corpus = _skill_markdown()
        for forbidden in PAGE_CONTRACT_MARKERS:
            self.assertNotIn(forbidden, corpus)

    def test_runtime_flow_emits_complete_markdown_in_chat(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for phrase in RUNTIME_FLOW:
            self.assertIn(phrase, text)
        self.assertNotIn("## Deliverable", text)

    def test_optional_preview_is_non_fatal_enhancement(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        preview = section(text, "## Optional preview", "## EXPLAIN")
        self.assertIn("host page", preview)
        self.assertIn("Canvas", preview)
        self.assertIn("only after the complete output", preview)
        self.assertIn("never replaces", preview)
        self.assertIn("non-fatal", preview)

    def test_output_chrome_is_common_markdown(self) -> None:
        text = _reference("output.md")
        positions = [text.index(marker) for marker in OUTPUT_CHROME]
        self.assertEqual(positions, sorted(positions))

    def test_hop_ids_agree_and_survive_rung_changes(self) -> None:
        text = _reference("output.md")
        self.assertIn(
            "Hop identifiers in Mermaid labels and the numbered list must agree and survive rung changes",
            text,
        )

    def test_mermaid_rendering_is_enhancement_only(self) -> None:
        output = _reference("output.md")
        visuals = _reference("visuals.md")
        self.assertIn(
            "Mermaid rendering is enhancement only; source plus hop list is the fallback",
            output,
        )
        self.assertIn("HTML boxes are not substitutes for Mermaid", visuals)
        for forbidden in HOST_TOOL_MARKERS:
            self.assertNotIn(forbidden, output)
            self.assertNotIn(forbidden, visuals)

    def test_sources_omit_citations_when_none_fetched(self) -> None:
        text = _reference("sources.md")
        self.assertIn("only URLs fetched in the current turn may appear as verified sources", text)
        self.assertIn("omit the citation heading", text)
        self.assertNotIn("The page is the artifact", text)
        for forbidden in HOST_TOOL_MARKERS:
            self.assertNotIn(forbidden, text)

    def test_references_do_not_require_a_host_tool(self) -> None:
        corpus = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted((SKILL / "references").glob("*.md"))
        )
        for forbidden in HOST_TOOL_MARKERS:
            self.assertNotIn(forbidden, corpus)
        self.assertNotIn("same file" + " path", corpus)
        self.assertNotIn("Artifact" + " tool", corpus)

    def test_type_word_does_not_silently_fill_rung(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("`흐름` → 흐름", text)
        self.assertIn("Type inference does not fill `rung`", text)
        self.assertIn("Do not silently pick a depth", text)
        aliases = section(text, "Silent aliases", "If the prompt already uses domain words")
        self.assertNotIn("흐름", aliases)

    def test_debug_and_eli5_do_not_enter_the_gate(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        frontmatter = parse_skill_frontmatter(text)
        description = str(frontmatter["description"])
        self.assertIn("debugging", description.lower())
        self.assertIn("Do not activate on eli5", text)
        self.assertIn("Do not use the rung picker", text)

    def test_jargon_defaults_to_skeleton_not_picture(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("default **뼈대**", text)
        self.assertIn("Aliases (쉽게, 한눈에, `5`) do not count as naming 그림", text)

    def test_high_stakes_banner_bytes_unchanged(self) -> None:
        text = _reference("stakes.md")
        self.assertIn(
            "이건 시술/계약/투자 조언이 아니다. 단순화는 예외와 관할을 지운다.",
            text,
        )
        self.assertIn("결정 전에 자격이 있는 사람에게 물어라.", text)
        self.assertIn("Explain mechanism only.", text)

    def test_korean_keeps_one_language_and_register(self) -> None:
        text = _reference("korean.md")
        self.assertIn("One language per reply", text)
        self.assertIn("해요체", text)
        self.assertIn("complete chat output", text)
        for forbidden in HOST_TOOL_MARKERS:
            self.assertNotIn(forbidden, text)


class HowItWorksLiveContractTests(unittest.TestCase):
    def test_live_cases_lock_synthetic_dns_prompts_and_allowed_fields(self) -> None:
        self.assertTrue(LIVE_CASES.is_file(), "live/cases.json is absent")
        data = json.loads(LIVE_CASES.read_text(encoding="utf-8"))
        self.assertEqual(data, LIVE_CASES_PAYLOAD)
        self.assertEqual(set(data), {"schema_version", "cases"})
        ids = [case["id"] for case in data["cases"]]
        self.assertEqual(tuple(ids), LIVE_CASE_IDS)
        for case in data["cases"]:
            self.assertEqual(set(case), LIVE_CASE_FIELDS[case["id"]], case["id"])
            self.assertTrue(FORBIDDEN_LIVE_KEYS.isdisjoint(case), case["id"])

    def test_live_readme_defines_observable_fresh_private_quota_rules(self) -> None:
        self.assertTrue(LIVE_README.is_file(), "live/README.md is absent")
        text = LIVE_README.read_text(encoding="utf-8")
        for marker in LIVE_README_MARKERS:
            self.assertIn(marker, text, marker)
        for case_id in LIVE_CASE_IDS:
            self.assertIn(case_id, text)
        self.assertNotIn("sk-", text)

    @unittest.skipUnless(
        LIVE_RECORD.is_file(),
        "live/smoke-record.json is created after approved execution",
    )
    def test_live_smoke_record_contains_only_metadata_fields(self) -> None:
        self.assertTrue(LIVE_RECORD.is_file(), "live/smoke-record.json is absent")
        data = json.loads(LIVE_RECORD.read_text(encoding="utf-8"))
        self.assertEqual(set(data), {"schema_version", "executed_on", "hosts"})
        self.assertEqual(data["schema_version"], 1)
        self.assertRegex(str(data["executed_on"]), r"^\d{4}-\d{2}-\d{2}$")
        hosts = data["hosts"]
        self.assertEqual([row["host"] for row in hosts], list(LIVE_HOSTS))
        self.assertTrue(FORBIDDEN_LIVE_KEYS.isdisjoint(data))
        for row in hosts:
            self.assertEqual(set(row), HOST_RECORD_FIELDS, row["host"])
            self.assertIsInstance(row["client_version"], str)
            self.assertTrue(row["client_version"])
            self.assertEqual(set(row["cases"]), set(LIVE_CASE_IDS))
            for case_id, verdict in row["cases"].items():
                self.assertIn(verdict, CASE_VERDICTS, f"{row['host']}:{case_id}")
            self.assertIn(row["verdict"], HOST_VERDICTS, row["host"])
            if row["verdict"] == "supported":
                self.assertEqual(set(row["cases"].values()), {"pass"}, row["host"])
            self.assertTrue(FORBIDDEN_LIVE_KEYS.isdisjoint(row), row["host"])
            self.assertNotIn("prompt", row)
            self.assertNotIn("transcript", row)
        supported = {
            row["host"] for row in hosts if row["verdict"] == "supported"
        }
        self.assertEqual(
            supported,
            set(load_registry(ROOT / "products.toml").require("how-it-works").supported_hosts),
        )


if __name__ == "__main__":
    unittest.main()
