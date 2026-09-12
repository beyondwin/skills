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
    "default-dns-picture",
    "explicit-dns-path",
    "implicit-positive",
    "near-miss-debug",
    "near-miss-eli5",
    "jargon-rung",
    "no-renderer",
    "no-fetched-source",
    "explicit-fracture-jargon",
    "explicit-path-jargon",
    "english-explicit-fracture",
    "jargon-without-depth",
    "topic-number-is-not-depth",
    "explicit-numeric-depth",
    "fracture-keeps-map",
    "high-stakes-no-lookup",
    "high-stakes-english",
    "high-stakes-comparison",
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
            "expect": {
                "invocation": "explicit",
                "dimensions": {
                    "fence": "lexical", "hop_ids": "lexical",
                    "skill_loading": "host_event",
                    "mermaid_syntax": "not_measured", "meaning": "not_measured",
                },
            },
        },
        {
            "id": "implicit-dns-path",
            "prompt": "DNS 요청이 브라우저에서 어디를 거쳐 IP 주소가 되는지 길로 보여줘",
            "expect": {
                "invocation": "implicit",
                "dimensions": {
                    "fence": "lexical", "hop_ids": "lexical",
                    "skill_loading": "host_event",
                    "mermaid_syntax": "not_measured", "meaning": "not_measured",
                },
            },
        },
        {
            "id": "near-miss-debug",
            "prompt": "DNS resolver 테스트 실패를 고쳐줘. 동작 설명은 하지 마.",
            "expect": {
                "invocation": "not_activated",
                "dimensions": {
                    "fence": "not_measured", "hop_ids": "not_measured",
                    "skill_loading": "not_measured",
                    "mermaid_syntax": "not_measured", "meaning": "not_measured",
                },
            },
        },
    ],
}
LIVE_README_MARKERS = (
    "historical-unbound",
    "current-bounded",
    "host_event",
    "not_measured/not_run",
    "does not authenticate execution",
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
    def test_v2_release_and_repeatable_install_contract(self) -> None:
        from scripts.lib.product_contract import load_product_release

        self.assertEqual(load_product_release(SKILL).version, "2.0.1")
        for filename in ("README.md", "README.en.md"):
            text = (SKILL / filename).read_text(encoding="utf-8")
            self.assertIn("<!-- how-it-works-local-links -->\n```python\n", text)
            self.assertNotIn(
                'ln -s "$PWD/skills/how-it-works" ~/.agents/skills/how-it-works',
                text,
            )
            self.assertNotIn("](../../docs/", text)

    def test_frontmatter_uses_portable_intersection(self) -> None:
        frontmatter = parse_skill_frontmatter((SKILL / "SKILL.md").read_text(encoding="utf-8"))
        self.assertEqual(set(frontmatter), PORTABLE_FIELDS)
        self.assertEqual(frontmatter["name"], "how-it-works")
        self.assertEqual(frontmatter["license"], "Apache-2.0")
        self.assertEqual(frontmatter["metadata"]["version"], "2.0.1")

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

    def test_v2_changelog_records_one_turn_emit_instruction(self) -> None:
        text = (SKILL / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn("## 2.0.0 - 2026-09-08", text)
        release = text.split("## 2.0.0 - 2026-09-08", 1)[1].split("\n## ", 1)[0]
        self.assertIn("current reply", release)
        self.assertIn("focused references", release)

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
        self.assertNotIn("test_evidence_contract.py", names)
        self.assertNotIn("evidence_contract.py", names)
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
                "must": [
                    "picture_default",
                    "claim",
                    "mermaid",
                    "numbered_hops",
                    "body",
                    "adjacent_slices",
                    "next_move",
                ],
                "forbidden": ["one_closed_question", "skeleton_default"],
            },
        )
        self.assertEqual(
            by_id["default-dns-picture"],
            {
                "id": "default-dns-picture",
                "prompt": "/how-it-works DNS",
                "must": [
                    "picture_default",
                    "claim",
                    "mermaid",
                    "numbered_hops",
                    "body",
                    "adjacent_slices",
                    "next_move",
                ],
                "forbidden": ["one_closed_question", "skeleton_default"],
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
        self.assertEqual(by_id["jargon-rung"]["must"], ["picture_default"])
        self.assertEqual(by_id["jargon-rung"]["forbidden"], ["skeleton_default"])
        self.assertEqual(by_id["no-renderer"]["must"], ["mermaid_source", "numbered_hops"])
        self.assertEqual(by_id["no-renderer"]["forbidden"], ["failure"])
        self.assertEqual(by_id["no-fetched-source"]["must"], ["omit_citations"])
        self.assertEqual(by_id["no-fetched-source"]["forbidden"], ["invented_citation"])
        self.assertEqual(
            by_id["explicit-fracture-jargon"],
            {
                "id": "explicit-fracture-jargon",
                "prompt": "Raft 허점으로 설명해줘",
                "must": ["fracture"],
                "forbidden": ["skeleton_default"],
            },
        )
        self.assertEqual(
            by_id["explicit-path-jargon"],
            {
                "id": "explicit-path-jargon",
                "prompt": "rebase 길로 보여줘",
                "must": ["path"],
                "forbidden": ["skeleton_default"],
            },
        )
        self.assertEqual(
            by_id["english-explicit-fracture"],
            {
                "id": "english-explicit-fracture",
                "prompt": "Explain Raft at the fracture depth.",
                "must": ["fracture", "english"],
                "forbidden": ["korean_banner", "skeleton_default"],
            },
        )
        self.assertEqual(
            by_id["jargon-without-depth"],
            {
                "id": "jargon-without-depth",
                "prompt": "Raft 원리부터 설명해줘",
                "must": ["skeleton_default"],
                "forbidden": ["numeric_depth"],
            },
        )
        self.assertEqual(
            by_id["topic-number-is-not-depth"],
            {
                "id": "topic-number-is-not-depth",
                "prompt": "Raft term 20의 원리부터 설명해줘",
                "must": ["skeleton_default"],
                "forbidden": ["fracture"],
            },
        )
        self.assertEqual(
            by_id["explicit-numeric-depth"],
            {
                "id": "explicit-numeric-depth",
                "prompt": "Raft를 깊이 5로 설명해줘",
                "must": ["picture_default"],
                "forbidden": ["skeleton_default"],
            },
        )
        self.assertEqual(
            by_id["fracture-keeps-map"],
            {
                "id": "fracture-keeps-map",
                "prompt": "Raft 허점",
                "must": ["baseline_mermaid", "numbered_hops", "body_regime_table"],
                "forbidden": ["table_only_map"],
            },
        )
        self.assertEqual(
            by_id["high-stakes-no-lookup"],
            {
                "id": "high-stakes-no-lookup",
                "prompt": "계약 해지의 일반 원리를 길로 설명해줘. 검색하지 마",
                "must": ["unverified_dependent_claim", "no_invented_statute"],
                "forbidden": ["verified_without_fetch"],
            },
        )
        self.assertEqual(
            by_id["high-stakes-english"],
            {
                "id": "high-stakes-english",
                "prompt": "Explain compound interest as a path in English",
                "must": ["english_banner"],
                "forbidden": ["korean_banner"],
            },
        )
        self.assertEqual(
            by_id["high-stakes-comparison"],
            {
                "id": "high-stakes-comparison",
                "prompt": "고정금리와 변동금리의 작동 차이를 그림으로 비교해줘",
                "must": ["conditional_tradeoff"],
                "forbidden": ["forced_personal_recommendation"],
            },
        )

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

    def test_v2_explicit_depth_precedence_contract(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn(
            "explicit rung > explicit depth alias > existing jargon default > one necessary question",
            text,
        )
        self.assertIn("Interpret numeric aliases only when explicitly selecting depth", text)
        self.assertNotIn("jargon wins", text)
        self.assertNotIn("Aliases (쉽게, 한눈에, `5`) do not count as naming 그림", text)

    def test_v2_fracture_and_stakes_contract(self) -> None:
        output = _reference("output.md")
        stakes = _reference("stakes.md")
        sources = _reference("sources.md")
        korean = _reference("korean.md")
        visuals = _reference("visuals.md")
        self.assertIn("Keep the baseline Mermaid and numbered hops in Map at every rung", output)
        self.assertIn("Put the failure/regime table in Body at 허점", output)
        self.assertIn("Map의 기준 Mermaid 유지; Body의 실패/적용 범위 표", visuals)
        self.assertNotIn("The 한 줄 is a **recommendation**, not a tie", output)
        self.assertNotIn("Do not fetch sources unless", stakes)
        self.assertIn("verified or explicitly unverified", stakes)
        self.assertIn("verified or explicitly unverified", sources)
        self.assertIn("## 한국어", stakes)
        self.assertIn("## English", stakes)
        self.assertNotIn("물어라", stakes)
        self.assertNotIn(
            "이건 시술/계약/투자 조언이 아니다. 단순화는 예외와 관할을 지운다.",
            stakes,
        )
        self.assertNotIn("컴퓨터는 숫자 주소를 본다", korean)

    def test_debug_and_eli5_do_not_enter_the_gate(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        frontmatter = parse_skill_frontmatter(text)
        description = str(frontmatter["description"])
        self.assertIn("debugging", description.lower())
        self.assertIn("Do not activate on eli5", text)
        self.assertIn("Do not use the rung picker", text)

    def test_explicit_easy_alias_precedes_jargon(self) -> None:
        # Design section 5.3 intentionally changes the former jargon-first contract.
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("default **뼈대**", text)
        self.assertIn("Explicit 쉽게/한눈에/한 장 selects 그림 even with jargon", text)

    def test_high_stakes_banners_are_language_specific(self) -> None:
        text = _reference("stakes.md")
        self.assertIn(
            "일반적인 작동 원리를 설명해요. 개인의 의료·법률·금융 결정을 위한 조언은 아니에요.",
            text,
        )
        self.assertIn(
            "This explains the general mechanism. It is not personalized medical, legal, or financial advice.",
            text,
        )
        self.assertNotIn(
            "이건 시술/계약/투자 조언이 아니다. 단순화는 예외와 관할을 지운다.",
            text,
        )
        self.assertNotIn("결정 전에 자격이 있는 사람에게 물어라.", text)

    def test_korean_keeps_one_language_and_register(self) -> None:
        text = _reference("korean.md")
        self.assertIn("One language per reply", text)
        self.assertIn("해요체", text)
        self.assertIn("complete chat output", text)
        for forbidden in HOST_TOOL_MARKERS:
            self.assertNotIn(forbidden, text)

    def test_product_readmes_separate_historical_and_current_measurement(self) -> None:
        for filename in ("README.md", "README.en.md"):
            text = (SKILL / filename).read_text(encoding="utf-8")
            self.assertNotRegex(
                text,
                r"(?is)cursor.{0,120}(did not pass|통과하지 않)",
                filename,
            )
            self.assertNotRegex(
                text,
                r"(?is)(did not pass|통과하지 않).{0,120}cursor",
                filename,
            )
            self.assertNotIn(
                "Grok and Cursor are not supported on this build because live smoke did not pass",
                text,
            )
            self.assertNotIn(
                "Grok와 Cursor는 이 빌드의 라이브 smoke가 통과하지 않아 지원하지 않습니다",
                text,
            )
        korean = (SKILL / "README.md").read_text(encoding="utf-8")
        english = (SKILL / "README.en.md").read_text(encoding="utf-8")
        self.assertIn("지금 설치 파일의 실제 실행은\n아직 확인하지 않았습니다(`not_measured`)", korean)
        self.assertIn("보존된 2026-08-28 측정에서는 Grok가 실패했고 Cursor는", korean)
        self.assertIn("Live evidence for the\ncurrent install files is `not_measured`", english)
        self.assertIn("In the preserved 2026-08-28 measurement,\nGrok failed and Cursor was not run", english)


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
            self.assertEqual(set(case["expect"]), {"invocation", "dimensions"})
            self.assertEqual(set(case["expect"]["dimensions"]), {
                "fence", "hop_ids", "skill_loading", "mermaid_syntax", "meaning",
            })

    def test_live_readme_defines_observable_fresh_private_quota_rules(self) -> None:
        self.assertTrue(LIVE_README.is_file(), "live/README.md is absent")
        text = LIVE_README.read_text(encoding="utf-8")
        for marker in LIVE_README_MARKERS:
            self.assertIn(marker, text, marker)
        for case_id in LIVE_CASE_IDS:
            self.assertIn(case_id, text)
        self.assertNotIn("sk-", text)

    def test_live_readme_keeps_desktop_cursor_smoke_as_required_path(self) -> None:
        text = LIVE_README.read_text(encoding="utf-8")
        self.assertIn("installed desktop", text)
        self.assertIn("@how-it-works", text)
        self.assertIn("separate new chats", text)
        self.assertIn("not_measured", text)
        self.assertIn("this-run", text)
        self.assertNotIn(
            "If Computer Use is unavailable, record Cursor as not executed",
            text,
        )

    def test_live_smoke_record_test_is_not_gated_by_skipunless(self) -> None:
        source = Path(__file__).read_text(encoding="utf-8")
        marker = "def test_live_smoke_record_contains_only_metadata_fields"
        start = source.index(marker)
        prefix = source[max(0, start - 180) : start]
        self.assertNotIn("skipUnless", prefix)

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

    def test_registry_preserves_supported_hosts_independently_of_current_measurement(self) -> None:
        # Historical verdicts remain historical; this locks the existing support scope.
        self.assertEqual(
            {"codex", "claude-code"},
            set(load_registry(ROOT / "products.toml").require("how-it-works").supported_hosts),
        )


if __name__ == "__main__":
    unittest.main()
