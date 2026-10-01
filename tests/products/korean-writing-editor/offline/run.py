#!/usr/bin/env python3
"""Property evaluator and skill-tree validator for korean-writing-editor."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import tempfile
import unittest

REQUIRED_CASE_FIELDS = (
    "id",
    "category",
    "request",
    "source",
    "candidate",
    "candidate_trigger",
    "candidate_mode",
    "expected_trigger",
    "expected_mode",
    "expected_noop",
    "must_preserve",
    "required_substrings",
    "forbidden_substrings",
    "rationale",
)
ALLOWED_CATEGORIES = {"normative", "preservation", "noop", "voice", "trigger"}
ALLOWED_MODES = {"diagnose", "correct", "polish", "none"}
EXPECTED_CATEGORY_COUNTS = {
    "normative": 10,
    "preservation": 8,
    "noop": 6,
    "voice": 4,
    "trigger": 7,
}
CASE_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
STRING_LIST_FIELDS = ("must_preserve", "required_substrings", "forbidden_substrings")
BOOLEAN_FIELDS = ("candidate_trigger", "expected_trigger", "expected_noop")
SKILL_NAME = "korean-writing-editor"
DESCRIPTION_REQUIRED_TERMS = (
    "proofread",
    "correct",
    "polish",
    "Korean",
    "text they provide",
    "translation",
    "drafting",
    "summarization",
    "code review",
    "casual",
)
MODE_TERMS = ("diagnose", "correct", "polish")
ROUTING_TERM = "routing unavailable"
OUTPUT_RECIPE_TERMS = ("work product", "first non-whitespace", "excluded task", "고칠 부분 없음")
REQUIRED_HEADINGS = {
    "SKILL.md": (
        "# Korean Writing Editor",
        "## Activation Gate",
        "## Modes",
        "## Default Interaction",
        "## Editing Pass",
        "## Preservation Gate",
        "## Model",
        "## Output Contract",
        "## Refuse Or Hold",
        "## References",
    ),
    "references/editorial-guide.md": (
        "# Korean Editorial Guide",
        "## Decision Classes",
        "## Normative Pass",
        "## Grammar And Local Flow",
        "## Voice Preservation",
        "## Genre Boundaries",
        "## Material Holds",
        "## Compact Examples",
    ),
}
MARKDOWN_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def load_cases(path: pathlib.Path) -> list[dict[str, object]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("cases root must be a JSON object")
    if raw.get("version") != "1":
        raise ValueError('cases version must be "1"')
    cases = raw.get("cases")
    if not isinstance(cases, list):
        raise ValueError("cases must be an array")
    return cases


def validate_case(case: dict[str, object]) -> list[str]:
    errors: list[str] = []
    case_id = case.get("id")
    prefix = case_id if isinstance(case_id, str) and case_id else "<unknown>"

    for field in REQUIRED_CASE_FIELDS:
        if field not in case:
            errors.append(f"{prefix}: missing {field}")

    if "id" in case:
        if not isinstance(case_id, str) or not CASE_ID_RE.fullmatch(case_id):
            errors.append(f"{prefix}: invalid id")

    category = case.get("category")
    if "category" in case and category not in ALLOWED_CATEGORIES:
        errors.append(f"{prefix}: invalid category")

    for mode_field in ("candidate_mode", "expected_mode"):
        if mode_field in case and case.get(mode_field) not in ALLOWED_MODES:
            errors.append(f"{prefix}: invalid {mode_field}")

    for field in BOOLEAN_FIELDS:
        if field in case and not isinstance(case.get(field), bool):
            errors.append(f"{prefix}: {field} must be boolean")

    for field in ("request", "source", "candidate", "rationale"):
        if field in case and not isinstance(case.get(field), str):
            errors.append(f"{prefix}: {field} must be string")

    request = case.get("request")
    source = case.get("source")
    if (
        case.get("expected_trigger") is True
        and isinstance(request, str)
        and isinstance(source, str)
        and source not in request
    ):
        errors.append(f"{prefix}: request does not contain source")

    for field in STRING_LIST_FIELDS:
        if field not in case:
            continue
        value = case.get(field)
        if not isinstance(value, list):
            errors.append(f"{prefix}: {field} must be a string list")
            continue
        if any(not isinstance(item, str) for item in value):
            errors.append(f"{prefix}: {field} must be a string list")

    return errors


def evaluate_candidate(case: dict[str, object]) -> list[str]:
    case_id = str(case.get("id", "<unknown>"))
    errors: list[str] = []
    source = str(case.get("source", ""))
    candidate = str(case.get("candidate", ""))

    if case.get("candidate_trigger") != case.get("expected_trigger"):
        errors.append(
            f"{case_id}: trigger mismatch: "
            f"{case.get('candidate_trigger')!r} != {case.get('expected_trigger')!r}"
        )
    if case.get("candidate_mode") != case.get("expected_mode"):
        errors.append(
            f"{case_id}: mode mismatch: "
            f"{case.get('candidate_mode')!r} != {case.get('expected_mode')!r}"
        )

    if case.get("expected_noop") is True and candidate != source:
        errors.append(f"{case_id}: expected no-op but candidate differs from source")
    if case.get("expected_noop") is False and candidate == source:
        errors.append(f"{case_id}: expected an edit but candidate equals source")
    if case.get("expected_trigger") is False and candidate == source:
        errors.append(
            f"{case_id}: near-miss candidate echoes the source instead of a handoff"
        )

    must_preserve = case.get("must_preserve") or []
    if isinstance(must_preserve, list):
        for literal in must_preserve:
            if not isinstance(literal, str):
                continue
            source_count = source.count(literal)
            candidate_count = candidate.count(literal)
            if source_count != candidate_count:
                errors.append(
                    f"{case_id}: occurrence count changed for '{literal}': "
                    f"{source_count} -> {candidate_count}"
                )

    required = case.get("required_substrings") or []
    if isinstance(required, list):
        for substring in required:
            if isinstance(substring, str) and substring not in candidate:
                errors.append(f"{case_id}: missing required substring '{substring}'")

    forbidden = case.get("forbidden_substrings") or []
    if isinstance(forbidden, list):
        for substring in forbidden:
            if isinstance(substring, str) and substring in candidate:
                errors.append(f"{case_id}: forbidden substring present '{substring}'")

    return errors


def _parse_frontmatter(text: str) -> dict[str, object]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    block = match.group(1)
    data: dict[str, object] = {}
    metadata: dict[str, str] = {}
    in_metadata = False
    for raw_line in block.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue
        if line == "metadata:":
            in_metadata = True
            continue
        if in_metadata and line.startswith("  ") and ":" in line:
            key, value = line.strip().split(":", 1)
            metadata[key.strip()] = value.strip().strip("\"'")
            continue
        in_metadata = False
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip("\"'")
    if metadata:
        data["metadata"] = metadata
    return data


def _heading_lines(text: str) -> set[str]:
    return {line.rstrip() for line in text.splitlines() if line.startswith("#")}


def _contains_term(text: str, term: str) -> bool:
    return (
        re.search(
            rf"(?<![A-Za-z0-9_]){re.escape(term)}(?![A-Za-z0-9_])",
            text,
        )
        is not None
    )


def _check_relative_links(
    skill_root: pathlib.Path, relative_path: str, text: str
) -> list[str]:
    errors: list[str] = []
    base = (skill_root / relative_path).parent
    for _label, target in MARKDOWN_LINK_RE.findall(text):
        href = target.strip()
        if not href or href.startswith("#"):
            continue
        if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", href):
            continue
        path_part = href.split("#", 1)[0]
        if not path_part:
            continue
        resolved = (base / path_part).resolve()
        try:
            resolved.relative_to(skill_root.resolve())
        except ValueError:
            errors.append(
                f"skill tree: link escapes skill root in {relative_path}: {href}"
            )
            continue
        if not resolved.exists():
            errors.append(
                f"skill tree: broken relative link in {relative_path}: {href}"
            )
    return errors


def validate_skill_tree(skill_root: pathlib.Path, scope: str) -> list[str]:
    if scope not in {"core", "full", "fixtures"}:
        return [f"skill tree: invalid scope {scope!r}"]

    errors: list[str] = []
    if skill_root.name != SKILL_NAME:
        errors.append(
            f"skill tree: directory name must be {SKILL_NAME}, "
            f"got {skill_root.name!r}"
        )

    required_files = [
        "SKILL.md",
        "references/editorial-guide.md",
        "references/sources.md",
    ]
    if scope == "full":
        required_files.extend(["README.md", "README.ko.md"])

    if scope == "fixtures":
        return errors

    present: dict[str, str] = {}
    for relative in required_files:
        path = skill_root / relative
        if not path.is_file():
            errors.append(f"skill tree: missing {relative}")
            continue
        present[relative] = path.read_text(encoding="utf-8")

    skill_text = present.get("SKILL.md")
    if skill_text is not None:
        frontmatter = _parse_frontmatter(skill_text)
        name = frontmatter.get("name")
        description = frontmatter.get("description")
        metadata = frontmatter.get("metadata")
        if name != SKILL_NAME:
            errors.append("skill tree: SKILL.md name must match directory")
        if frontmatter.get("license") != "Apache-2.0":
            errors.append("skill tree: SKILL.md license must be Apache-2.0")
        compatibility = frontmatter.get("compatibility")
        if not isinstance(compatibility, str) or not compatibility.strip():
            errors.append("skill tree: SKILL.md compatibility missing")
        if not isinstance(description, str) or not description.strip():
            errors.append("skill tree: SKILL.md description missing")
        else:
            for term in DESCRIPTION_REQUIRED_TERMS:
                if term not in description:
                    errors.append(
                        f"skill tree: SKILL.md description missing term {term!r}"
                    )
        version = None
        if isinstance(metadata, dict):
            version = metadata.get("version")
        if not isinstance(version, str) or not version:
            errors.append("skill tree: SKILL.md metadata.version must be a string")
        for term in OUTPUT_RECIPE_TERMS:
            if not _contains_term(skill_text, term):
                errors.append(
                    f"skill tree: SKILL.md missing output-recipe term {term!r}"
                )
        if ROUTING_TERM not in skill_text:
            errors.append(f"skill tree: SKILL.md missing {ROUTING_TERM!r}")

    for relative in ("SKILL.md", "references/editorial-guide.md"):
        text = present.get(relative)
        if text is None:
            continue
        for term in MODE_TERMS:
            if not _contains_term(text, term):
                errors.append(f"skill tree: {relative} missing mode term {term!r}")

    heading_targets = ["SKILL.md", "references/editorial-guide.md"]
    for relative in heading_targets:
        text = present.get(relative)
        if text is None:
            continue
        headings = _heading_lines(text)
        for heading in REQUIRED_HEADINGS[relative]:
            if heading not in headings:
                errors.append(f"skill tree: {relative} missing heading {heading!r}")

    for relative, text in present.items():
        errors.extend(_check_relative_links(skill_root, relative, text))

    return errors


def _cases_by_id(cases: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    indexed: dict[str, dict[str, object]] = {}
    for case in cases:
        if isinstance(case, dict) and isinstance(case.get("id"), str):
            indexed[str(case["id"])] = case
    return indexed


def run_mutation_checks(cases: list[dict[str, object]]) -> list[str]:
    """Prove deliberate corruptions are rejected by evaluate_candidate."""
    by_id = _cases_by_id(cases)
    errors: list[str] = []

    quantity = by_id.get("meaning-quantity-03")
    if quantity is None:
        errors.append("mutation: missing meaning-quantity-03")
    else:
        mutated = dict(quantity)
        mutated["candidate"] = str(quantity["candidate"]).replace("12.5%", "12%", 1)
        if not evaluate_candidate(mutated):
            errors.append("mutation: removing repeated number produced no error")

    negation = by_id.get("meaning-negation-01")
    if negation is None:
        errors.append("mutation: missing meaning-negation-01")
    else:
        mutated = dict(negation)
        mutated["candidate"] = (
            str(negation["candidate"])
            .replace("출시하지 않을 수 있다", "출시할 수 있다")
        )
        if not evaluate_candidate(mutated):
            errors.append("mutation: flipping negation produced no error")

        hedge = dict(negation)
        hedge["candidate"] = (
            str(negation["candidate"]).replace(
                "출시하지 않을 수 있다", "출시하지 않을 수도 있다"
            )
        )
        if not evaluate_candidate(hedge):
            errors.append(
                "mutation: replacing 수 있다 with 수도 있다 produced no error"
            )

    modality = by_id.get("meaning-modality-02")
    if modality is None:
        errors.append("mutation: missing meaning-modality-02")
    else:
        mutated = dict(modality)
        mutated["candidate"] = str(modality["candidate"]) + " 확실하다"
        if not evaluate_candidate(mutated):
            errors.append("mutation: adding forbidden certainty produced no error")

    quote = by_id.get("meaning-quote-07")
    if quote is None:
        errors.append("mutation: missing meaning-quote-07")
    else:
        mutated = dict(quote)
        mutated["candidate"] = str(quote["candidate"]).replace("이서연", "김민수")
        if not evaluate_candidate(mutated):
            errors.append("mutation: changing quote speaker produced no error")
        verb = dict(quote)
        verb["candidate"] = str(quote["candidate"]).replace("말했다", "밝혔다")
        if not evaluate_candidate(verb):
            errors.append("mutation: changing the reporting verb produced no error")

    spacing = by_id.get("norm-spacing-can-01")
    if spacing is None:
        errors.append("mutation: missing norm-spacing-can-01")
    else:
        paraphrased = dict(spacing)
        paraphrased["candidate"] = str(spacing["candidate"]).replace(
            "켤 필요는", "켜야 할 필요는"
        )
        if not evaluate_candidate(paraphrased):
            errors.append(
                "mutation: paraphrasing already-correct obligation produced no error"
            )

        preamble = dict(spacing)
        preamble["candidate"] = (
            "요청은 오탈자만 고치는 교정입니다." + str(spacing["candidate"])
        )
        if not evaluate_candidate(preamble):
            errors.append(
                "mutation: adding process preamble produced no error"
            )

        english_preamble = dict(spacing)
        english_preamble["candidate"] = (
            "Using the Korean writing editor skill to correct typos."
            + str(spacing["candidate"])
        )
        if not evaluate_candidate(english_preamble):
            errors.append(
                "mutation: adding English skill-usage preamble produced no error"
            )

        korean_preamble = dict(spacing)
        korean_preamble["candidate"] = (
            "한국어 교정 스킬을 확인한 뒤 오탈자만 고치겠습니다."
            + str(spacing["candidate"])
        )
        if not evaluate_candidate(korean_preamble):
            errors.append(
                "mutation: adding Korean skill-usage preamble produced no error"
            )

    for mode, suffix in (("correct", "09"), ("polish", "10")):
        case_id = f"norm-grammar-particle-{mode}-{suffix}"
        case = by_id.get(case_id)
        if case is None:
            errors.append(f"mutation: missing {case_id}")
            continue
        for candidate in (
            case["source"],
            str(case["candidate"]).replace(
                "다시 읽을지는 모르겠다", "반드시 다시 읽겠다"
            ),
        ):
            mutated = dict(case, candidate=candidate)
            if not evaluate_candidate(mutated):
                errors.append(
                    f"mutation: grammar or voice corruption escaped {case_id}"
                )

    for case_id in ("trigger-diagnose-05", "trigger-diagnose-clean-07"):
        case = by_id.get(case_id)
        if case is None:
            errors.append(f"mutation: missing {case_id}")
            continue
        if not evaluate_candidate(dict(case, candidate=case["source"])):
            errors.append(
                f"mutation: returning the unchanged source escaped {case_id}"
            )

    no_text = by_id.get("trigger-explicit-no-text-06")
    if no_text is None:
        errors.append("mutation: missing trigger-explicit-no-text-06")
    elif not evaluate_candidate(
        dict(no_text, candidate="이 편집기는 적용되지 않습니다.")
    ):
        errors.append("mutation: a no-op handoff without asking for text produced no error")

    translation = by_id.get("trigger-translation-03")
    if translation is None:
        errors.append("mutation: missing trigger-translation-03")
    else:
        mutated = dict(translation)
        mutated["candidate"] = (
            str(translation["candidate"])
            + " There is a meeting tomorrow morning."
        )
        if not evaluate_candidate(mutated):
            errors.append(
                "mutation: fulfilling a translation near-miss produced no error"
            )

    return errors


def _validate_fixtures(
    cases_path: pathlib.Path,
) -> tuple[list[str], list[dict[str, object]], dict[str, int]]:
    errors: list[str] = []
    try:
        cases = load_cases(cases_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [f"fixtures: failed to load cases: {exc}"], [], {}

    seen_ids: set[str] = set()
    category_counts = {name: 0 for name in EXPECTED_CATEGORY_COUNTS}

    for case in cases:
        if not isinstance(case, dict):
            errors.append("fixtures: case entry must be an object")
            continue
        case_errors = validate_case(case)
        errors.extend(case_errors)
        case_id = case.get("id")
        if isinstance(case_id, str):
            if case_id in seen_ids:
                errors.append(f"{case_id}: duplicate id")
            seen_ids.add(case_id)
        category = case.get("category")
        if isinstance(category, str) and category in category_counts:
            category_counts[category] += 1
        if not case_errors:
            errors.extend(evaluate_candidate(case))

    for name, expected in EXPECTED_CATEGORY_COUNTS.items():
        actual = category_counts[name]
        if actual != expected:
            errors.append(
                f"fixtures: expected {expected} {name} cases, found {actual}"
            )

    mutation_errors = run_mutation_checks(cases)
    errors.extend(mutation_errors)
    return errors, cases, category_counts


class EvaluatorTests(unittest.TestCase):
    def valid_case(self, **overrides):
        case = {
            "id": "case-01",
            "category": "preservation",
            "request": "다듬어줘: 출시하지 않을 수 있다.",
            "source": "출시하지 않을 수 있다.",
            "candidate": "출시하지 않을 수 있다.",
            "candidate_trigger": True,
            "candidate_mode": "polish",
            "expected_trigger": True,
            "expected_mode": "polish",
            "expected_noop": True,
            "must_preserve": ["출시하지 않을 수 있다"],
            "required_substrings": ["출시하지 않을 수 있다"],
            "forbidden_substrings": ["반드시 출시한다"],
            "rationale": "Negation and modality are material.",
        }
        case.update(overrides)
        return case

    def test_rejects_missing_required_field(self):
        errors = validate_case({"id": "broken"})
        self.assertIn("broken: missing category", errors)

    def test_preserved_literal_uses_occurrence_count(self):
        case = {
            "id": "duplicate-number",
            "category": "preservation",
            "request": "다듬어줘",
            "source": "7명 중 7명이 동의했다.",
            "candidate": "7명이 동의했다.",
            "candidate_trigger": True,
            "candidate_mode": "polish",
            "expected_trigger": True,
            "expected_mode": "polish",
            "expected_noop": False,
            "must_preserve": ["7"],
            "required_substrings": [],
            "forbidden_substrings": [],
            "rationale": "Duplicate counts must survive.",
        }
        self.assertIn(
            "duplicate-number: occurrence count changed for '7': 2 -> 1",
            evaluate_candidate(case),
        )

    def test_mutated_negation_is_rejected(self):
        case = self.valid_case(candidate="출시할 수 있다.")
        case["required_substrings"] = ["출시하지 않을 수 있다"]
        self.assertIn(
            "case-01: missing required substring '출시하지 않을 수 있다'",
            evaluate_candidate(case),
        )

    def test_full_scope_requires_skill_md(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            errors = validate_skill_tree(root, "full")
        self.assertIn("skill tree: missing SKILL.md", errors)

    def obligation_case(self):
        return {
            "id": "norm-spacing-can-01",
            "category": "normative",
            "request": (
                "오탈자만 고쳐줘: 이 기능은 사용할수 있지만 "
                "반드시 켤 필요는 없습니다."
            ),
            "source": "이 기능은 사용할수 있지만 반드시 켤 필요는 없습니다.",
            "candidate": "이 기능은 사용할 수 있지만 반드시 켤 필요는 없습니다.",
            "candidate_trigger": True,
            "candidate_mode": "correct",
            "expected_trigger": True,
            "expected_mode": "correct",
            "expected_noop": False,
            "must_preserve": ["반드시 켤 필요는 없습니다"],
            "required_substrings": ["사용할 수"],
            "forbidden_substrings": [
                "사용할수",
                "켜야 할 필요는",
                "요청은 오탈자",
                "Using the",
                "한국어 교정 스킬",
            ],
            "rationale": (
                "Dependent-noun spacing plus already-correct obligation "
                "wording; no process preamble."
            ),
        }

    def test_rejects_obligation_paraphrase_candidate(self):
        case = self.obligation_case()
        case["candidate"] = case["candidate"].replace(
            "켤 필요는", "켜야 할 필요는"
        )
        self.assertIn(
            "norm-spacing-can-01: forbidden substring present '켜야 할 필요는'",
            evaluate_candidate(case),
        )

    def test_rejects_process_preamble_candidate(self):
        case = self.obligation_case()
        case["candidate"] = (
            "요청은 오탈자만 고치는 교정입니다." + case["candidate"]
        )
        self.assertIn(
            "norm-spacing-can-01: forbidden substring present '요청은 오탈자'",
            evaluate_candidate(case),
        )

    def test_obligation_case_matches_live_forbidden_substrings(self):
        live = json.loads(
            pathlib.Path(__file__).with_name("cases.json").read_text(encoding="utf-8")
        )
        live_case = next(
            case for case in live["cases"] if case["id"] == "norm-spacing-can-01"
        )
        self.assertEqual(
            self.obligation_case()["forbidden_substrings"],
            live_case["forbidden_substrings"],
        )

    def test_rejects_english_skill_usage_preamble_candidate(self):
        case = self.obligation_case()
        case["candidate"] = (
            "Using the Korean writing editor skill to correct typos."
            + case["candidate"]
        )
        self.assertIn(
            "norm-spacing-can-01: forbidden substring present 'Using the'",
            evaluate_candidate(case),
        )

    def test_rejects_korean_skill_usage_preamble_candidate(self):
        case = self.obligation_case()
        case["candidate"] = (
            "한국어 교정 스킬을 확인한 뒤 오탈자만 고치겠습니다."
            + case["candidate"]
        )
        self.assertIn(
            "norm-spacing-can-01: forbidden substring present '한국어 교정 스킬'",
            evaluate_candidate(case),
        )

    def test_mutation_checks_ignore_non_object_entries(self):
        errors = run_mutation_checks(["not-an-object"])
        self.assertIn("mutation: missing meaning-quantity-03", errors)
        self.assertIn("mutation: missing norm-spacing-can-01", errors)

    def test_triggered_request_must_contain_source(self):
        case = self.valid_case(request="다듬어줘: 출시하지 않는다.")
        self.assertIn("case-01: request does not contain source", validate_case(case))
        near_miss = self.valid_case(
            request="번역해줘",
            expected_trigger=False,
            candidate_trigger=False,
        )
        self.assertNotIn(
            "case-01: request does not contain source", validate_case(near_miss)
        )

    def test_edit_expected_candidate_must_differ_from_source(self):
        case = self.valid_case(expected_noop=False)
        self.assertIn(
            "case-01: expected an edit but candidate equals source",
            evaluate_candidate(case),
        )

    def test_near_miss_candidate_must_not_echo_source(self):
        case = self.valid_case(
            expected_trigger=False,
            candidate_trigger=False,
            expected_mode="none",
            candidate_mode="none",
            must_preserve=[],
            required_substrings=[],
        )
        self.assertIn(
            "case-01: near-miss candidate echoes the source instead of a handoff",
            evaluate_candidate(case),
        )

    def test_full_scope_requires_routing_unavailable_reply(self):
        source = pathlib.Path(__file__).resolve().parents[4] / "skills" / SKILL_NAME
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory) / SKILL_NAME
            root.mkdir()
            for relative in ("SKILL.md", "references/editorial-guide.md", "references/sources.md"):
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text((source / relative).read_text(encoding="utf-8"), encoding="utf-8")
            self.assertEqual(validate_skill_tree(root, "core"), [])
            skill = root / "SKILL.md"
            skill.write_text(
                skill.read_text(encoding="utf-8").replace("routing unavailable", "no routing"),
                encoding="utf-8",
            )
            self.assertIn(
                "skill tree: SKILL.md missing 'routing unavailable'",
                validate_skill_tree(root, "core"),
            )

    def test_mode_term_does_not_match_correction(self):
        self.assertFalse(_contains_term("local corrections only", "correct"))
        self.assertTrue(_contains_term("mode `correct` and polish", "correct"))


def run_self_tests() -> unittest.result.TestResult:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(EvaluatorTests)
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate Korean writing editor fixtures and skill tree."
    )
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument(
        "--scope",
        choices=("fixtures", "core", "full"),
        default=None,
    )
    parser.add_argument("--skill-root", type=pathlib.Path)
    args = parser.parse_args(argv)

    if args.self_test:
        result = run_self_tests()
        return 0 if result.wasSuccessful() else 1

    if args.scope is None:
        parser.error("one of --self-test or --scope is required")

    skill_root = args.skill_root or (
        pathlib.Path(__file__).resolve().parents[4] / "skills" / "korean-writing-editor"
    )
    cases_path = pathlib.Path(__file__).with_name("cases.json")

    fixture_errors, _cases, category_counts = _validate_fixtures(cases_path)
    errors = list(fixture_errors)

    if args.scope in {"core", "full"}:
        errors.extend(validate_skill_tree(skill_root, args.scope))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print(
        f"{len(_cases)} cases: "
        f"normative={category_counts['normative']} "
        f"preservation={category_counts['preservation']} "
        f"noop={category_counts['noop']} "
        f"voice={category_counts['voice']} "
        f"trigger={category_counts['trigger']}"
    )
    print("mutation checks: PASS")
    if args.scope in {"core", "full"}:
        print(f"skill tree ({args.scope}): PASS")
    print(
        "offline contract only: reference candidates do not prove live model quality"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
