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
    "# {slice} · {그림|길|뼈대|허점 / picture|path|skeleton|fracture}",
    "{high-stakes banner or omit}",
    "## 한 줄 / One sentence",
    "## 지도 / Map",
    "1. **H1** — {what moves or changes}",
    "2. **H2** — {what moves or changes}",
    "```mermaid",
    "{diagram source}",
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
LIVE_CASE_IDS = ("explicit-dns-path", "implicit-dns-path", "near-miss-debug")
LIVE_CASE_FIELDS = {
    "explicit-dns-path": {"id", "prompt_codex", "prompt_slash", "expect"},
    "implicit-dns-path": {"id", "prompt", "expect"},
    "near-miss-debug": {"id", "prompt", "expect"},
}
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
    "current-bounded",
    "host_event",
    "not_measured/not_run",
    "does not authenticate execution",
    "Do not use private or user prompts",
    "Do not commit full responses",
    "fresh session",
    "subscription/API quota",
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
    def test_release_and_repeatable_install_contract(self) -> None:
        from scripts.lib.product_contract import load_product_release

        self.assertEqual(load_product_release(SKILL).version, "3.0.1")
        self.assertEqual(
            {path.name for path in SKILL.glob("README*.md")}, {"README.md", "README.ko.md"}
        )
        for filename in ("README.md", "README.ko.md"):
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
        self.assertEqual(frontmatter["metadata"]["version"], "3.0.1")

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

    def test_runtime_reads_references_unless_the_host_cannot_read_files(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        runtime = section(text, "## Runtime", "## After EXPLAIN")
        self.assertIn(
            "When the host can read files, read `references/output.md` (and `references/korean.md` for a Korean reply) before replying.",
            runtime,
        )
        self.assertIn(
            "Only when the host cannot read files this turn, emit the complete required deliverable from the skeleton in Required deliverable.",
            runtime,
        )
        self.assertNotIn("even if you cannot read focused references", text)
        self.assertNotIn("I'll read the references first", text)

    def test_skill_skeleton_mirrors_output_chrome(self) -> None:
        def skeleton(markdown: str) -> str:
            start = markdown.index("````markdown\n")
            return markdown[start : markdown.index("\n````\n", start)]

        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        required = section(text, "## Required deliverable", "## Optional preview")
        self.assertEqual(skeleton(required), skeleton(_reference("output.md")))
        self.assertIn("mirrored from `references/output.md`", required)
        self.assertIn("Korean replies use 해요체.", required)
        self.assertLess(required.index("2. numbered hop list"), required.index("3. Mermaid source"))
        self.assertIn("a branch reuses its parent id, `H3a`", required)

    def test_red_flags_catch_hop_ids_missing_from_the_list(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        flags = text.split("## Red flags", 1)[1]
        self.assertIn(
            "A Mermaid hop id with no matching `**Hk**` list item (a branch `H3a` matches `**H3**`), or hop list items without `**Hk**`",
            flags,
        )

    def test_classify_states_slice_rules_and_high_stakes_still_explain(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        classify = section(text, "## Classify", "## Slots")
        self.assertIn("the slice is the one mechanism that answer rests on", classify)
        self.assertIn("answer it after the next move as a short separate list", classify)
        self.assertIn("More than one mechanism in the request: Ask one, or Cut.", classify)
        self.assertIn("so the user can redirect on the next turn", classify)
        self.assertNotIn("so the user can override", text)
        self.assertNotIn("surprising", text)
        self.assertNotIn("Pause when", text)
        self.assertIn(
            "Medical, legal, or financial topic: read `references/stakes.md`, add its banner, and still explain in the same turn.",
            text,
        )

    def test_intent_line_and_next_moves_have_clear_labels(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("> {slice}을/를 **{rung}** 깊이로 설명할게요. {moving_thing}이/가 이동하는 순서를 따라가요.", text)
        self.assertNotIn("{particle}", _skill_markdown())
        self.assertNotIn("Intent line:", _reference("korean.md"))
        after = section(text, "## After EXPLAIN", "## Required deliverable")
        for label in (
            "- 다음 칸 / Next rung (그림→길→뼈대→허점 / picture→path→skeleton→fracture)",
            "- 흐린 홉 하나 / One blurry hop",
            "- 다른 각도 / Another angle",
            "- 한 줄로 되말하기 / Say it back in one line",
        ):
            self.assertIn(label, after)
        self.assertIn("다른 각도 recuts the type (개념, 흐름, 비교, or 절차)", after)
        self.assertNotIn("실패)", after)
        for leftover in ("Age does not go down", "Rung picker", "rung picker"):
            self.assertNotIn(leftover, text)

    def test_changelog_records_one_turn_emit_instruction(self) -> None:
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
        self.assertIn("Never replace a filled rung", text)
        self.assertIn("default 그림", text)
        self.assertNotIn("Do not silently pick a depth", text)
        aliases = section(text, "Silent aliases", "If the prompt already uses domain words")
        self.assertNotIn("흐름", aliases)
        self.assertIn("감이 안 와", aliases)

    def test_missing_depth_explains_at_default_picture(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Do not explain until `slice` is a cut mechanism", text)
        self.assertIn("Explain in the same turn", text)
        self.assertIn("Announce the rung in the intent line", text)
        self.assertIn("Missing rung takes default 그림", text)
        self.assertIn("| Direct | slice is a cut mechanism |", text)
        self.assertIn("- **그림** — 한 장 (default)", text)
        self.assertNotIn(
            "Do not explain until `slice`, `type`, `rung`, and `language` are filled",
            text,
        )
        self.assertNotIn("- **길** — 누가 무엇을 넘기는지 (default)", text)

    def test_explicit_depth_precedence_contract(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn(
            "explicit rung > explicit depth alias > existing jargon default > default 그림",
            text,
        )
        self.assertIn("Interpret numeric aliases only when explicitly selecting depth", text)
        self.assertNotIn("jargon wins", text)
        self.assertNotIn("Aliases (쉽게, 한눈에, `5`) do not count as naming 그림", text)

    def test_fracture_and_stakes_contract(self) -> None:
        output = _reference("output.md")
        stakes = _reference("stakes.md")
        sources = _reference("sources.md")
        korean = _reference("korean.md")
        visuals = _reference("visuals.md")
        self.assertIn("Keep the baseline Mermaid and numbered hops in Map at every rung", output)
        self.assertIn("Put the failure/regime table in Body at 허점", output)
        self.assertIn(
            "허점: keep the baseline Mermaid in Map; put the failure/regime table in Body",
            visuals,
        )
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
        self.assertIn("Do not use this explanation flow on debugging", text)

    def test_explicit_easy_alias_precedes_jargon(self) -> None:
        # Design section 5.3 intentionally changes the former jargon-first contract.
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("default **뼈대**", text)
        self.assertIn("Explicit 쉽게/한눈에/한 장 selects 그림 even with jargon", text)

    def test_picture_body_does_not_restate_hops(self) -> None:
        output = _reference("output.md")
        self.assertIn("그림 hops are the map; Body does not walk the hops again", output)
        self.assertIn("Analogy, if used, comes after the hops", output)
        self.assertIn(
            "그림: Map hops only; Body is identity and use. 길 walks the hops on a sequence diagram",
            output,
        )
        self.assertNotIn(
            "Walk the hops. 길 gets the sequence diagram. 그림 gets boxes only",
            output,
        )
        visuals = _reference("visuals.md")
        box_rule = "4–6 boxes, one per hop; more than 6 means recut the slice"
        self.assertIn(box_rule, output)
        self.assertIn(box_rule, visuals)
        for stale in ("5–7 boxes", "≤7 boxes", "hard cap 12"):
            self.assertNotIn(stale, output)
            self.assertNotIn(stale, visuals)

    def test_hop_ids_are_labels_and_branches_reuse_the_parent(self) -> None:
        output = _reference("output.md")
        visuals = _reference("visuals.md")
        for text in (output, visuals):
            self.assertNotIn("message numbers = hop IDs", text)
            self.assertIn("each message label starts with its hop id (`H1: …`)", text)
            self.assertIn("`H3a`", text)
        self.assertIn(
            "The baseline is the 그림 hop list: deeper rungs may redraw the diagram type but keep the same H ids.",
            output,
        )

    def test_comparison_columns_are_fixed(self) -> None:
        output = _reference("output.md")
        self.assertIn("these four columns at every rung", output)
        self.assertNotIn("그림 uses 3 axes", output)

    def test_korean_picture_target_keeps_cache_in_the_same_movie(self) -> None:
        korean = _reference("korean.md")
        self.assertIn("묻다, 맡기다, 적어 두다, 만료되다", korean)
        self.assertIn("가까운 기억", korean)
        self.assertIn("만료되면", korean)
        self.assertNotIn("컴퓨터는 숫자 주소를 본다", korean)
        self.assertIn("여러분이", korean)
        self.assertIn("답니다", korean)

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
        self.assertIn("해요체, even when earlier turns used 합니다체", text)
        self.assertIn("No 우리 / 여러분 / 당신 / 너 / 네가.", text)
        self.assertIn("In Body, after the one-line claim, open with a lived snag", text)
        self.assertIn("complete chat output", text)
        for forbidden in HOST_TOOL_MARKERS:
            self.assertNotIn(forbidden, text)

    def test_product_readmes_state_current_measurement(self) -> None:
        korean = " ".join((SKILL / "README.ko.md").read_text(encoding="utf-8").split())
        english = " ".join((SKILL / "README.md").read_text(encoding="utf-8").split())
        self.assertIn("지금 설치 파일의 실제 실행은 아직 확인하지 않았습니다(`not_measured`)", korean)
        self.assertIn("Grok와 Cursor는 지원하지 않습니다", korean)
        self.assertIn("Live runs of the current install files are `not_measured`", english)
        self.assertIn("Grok and Cursor are not supported", english)
        self.assertIn("If the topic is already technical jargon and you name no depth, it starts at skeleton.", english)
        self.assertIn("주제가 이미 기술 용어이고 깊이를 고르지 않으면 뼈대로 시작합니다.", korean)


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

    def test_live_readme_covers_only_supported_hosts_with_event_output(self) -> None:
        text = LIVE_README.read_text(encoding="utf-8")
        for retired in ("Grok", "grok", "Cursor", "@how-it-works", "/Users/kws", "print -u2", "2.0.0"):
            self.assertNotIn(retired, text, retired)
        self.assertIn("`codex` or `claude-code`", text)
        self.assertIn('--cd "$PWD"', text)
        self.assertIn("codex exec --json", text)
        self.assertIn("claude --print --output-format stream-json --verbose", text)
        self.assertIn('.name=="Skill"', text)
        self.assertIn("how-it-works/SKILL.md", text)

    def test_registry_preserves_supported_hosts_independently_of_current_measurement(self) -> None:
        # Locks the existing support scope; it does not depend on a live record.
        self.assertEqual(
            {"codex", "claude-code"},
            set(load_registry(ROOT / "products.toml").require("how-it-works").supported_hosts),
        )


if __name__ == "__main__":
    unittest.main()
