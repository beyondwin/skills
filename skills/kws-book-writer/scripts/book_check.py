#!/usr/bin/env python3
"""Assemble and check a kws-book-writer workspace.

Standard library only; runs on Python 3.9.

Commands:
  markers                      print the leftover-marker list (the only definition)
  assemble <workspace>         build manuscript.md from book.json and print its SHA-256
  check <workspace> [--final]  write checks/check-report.md; exit 1 on a hard failure
  accept <workspace> --verdict ACCEPT|BLOCK|USER_APPROVED [--note TEXT]
                               record a verdict against the current manuscript hash
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# The one list of markers a writer may leave for unfinished work. Every other file
# in the skill points here instead of repeating it.
MARKERS = (
    "[리서치 공백]",
    "[사실 확인 필요]",
    "[미완성]",
    "[그림 예정]",
)

VERDICTS = ("ACCEPT", "BLOCK", "USER_APPROVED")
PASSING_VERDICTS = ("ACCEPT", "USER_APPROVED")
REQUIRED_META = ("title", "author", "chapters")
OPTIONAL_TEXT_META = ("subtitle", "date", "language")
OPTIONAL_LIST_META = ("front", "back")

SRC_COMMENT = re.compile(r"<!--\s*src:\s*([^>]*?)\s*-->")
HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)
KOREAN_PLACEHOLDER = re.compile(r"<[^<>\n]*[가-힣][^<>\n]*>")
INLINE_CODE = re.compile(r"`[^`\n]*`")
CHAPTER_REF = re.compile(r"(\d{1,2})\s*장(?:에서|으로|의|을|과|와|에|부터|까지|은|이|\b)")
NEXT_CHAPTER_PHRASE = re.compile(r"다음 장에서(?:는)?")
NUMBER_CLAIM = re.compile(
    r"\d[\d,.]*\s*(?:%|퍼센트|배|명|개|건|회|원|달러|초|분|시간|일|주|개월|년|ms|MB|GB|TB|만|억)"
)
CONTRAST = re.compile(r"[가-힣]+(?:이|가)\s*아니라")
# CommonMark does not close "**" that follows punctuation and precedes a letter, so
# "**멱등성(idempotency)**은" renders with literal asterisks.
UNCLOSED_BOLD = re.compile(r"\*\*[^*\n]*?[^\w\s*]\*\*(?=[0-9A-Za-z\uac00-\ud7a3])")
LEDGER_ID = re.compile(r"(?<![A-Za-z0-9])R[A-Z]?\d{2,3}(?![0-9])")
INTERNAL_TERMS = (
    "오케스트레이터",
    "하위 에이전트",
    "서브에이전트",
    "subagent",
    "리서치 장부",
    "ledger",
    "수락 게이트",
    "brief.md",
    "plan.md",
    "voice.md",
)


class Report:
    def __init__(self) -> None:
        self.hard: List[str] = []
        self.notes: Dict[str, List[str]] = {}

    def fail(self, message: str) -> None:
        self.hard.append(message)

    def note(self, section: str, message: str) -> None:
        self.notes.setdefault(section, []).append(message)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_meta(workspace: Path, report: Optional[Report] = None) -> Optional[dict]:
    """Load book.json; every problem is a hard failure."""
    path = workspace / "book.json"
    errors: List[str] = []
    meta = None
    if not path.is_file():
        errors.append("book.json is missing")
    else:
        try:
            meta = json.loads(read(path))
        except (ValueError, UnicodeDecodeError) as exc:
            errors.append("book.json is not valid UTF-8 JSON: {}".format(exc))
    if meta is not None and not isinstance(meta, dict):
        errors.append("book.json must be a JSON object")
        meta = None
    if meta is not None:
        for key in REQUIRED_META:
            if key not in meta:
                errors.append("book.json is missing '{}'".format(key))
        for key in ("title", "author") + OPTIONAL_TEXT_META:
            if key in meta:
                value = meta[key]
                if not isinstance(value, str) or not value.strip():
                    errors.append("book.json '{}' must be a non-empty string".format(key))
                elif any(ord(ch) < 32 for ch in value):
                    errors.append("book.json '{}' contains a control character".format(key))
        for key in ("chapters",) + OPTIONAL_LIST_META:
            if key not in meta:
                continue
            value = meta[key]
            if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
                errors.append("book.json '{}' must be a list of paths".format(key))
                continue
            if key == "chapters" and not value:
                errors.append("book.json 'chapters' is empty")
            for rel in value:
                if Path(rel).is_absolute() or ".." in Path(rel).parts:
                    errors.append("book.json path must stay inside the workspace: {}".format(rel))
                elif not (workspace / rel).is_file():
                    errors.append("book.json lists a missing file: {}".format(rel))
    if errors:
        if report is not None:
            for error in errors:
                report.fail(error)
            return None
        raise SystemExit("\n".join(errors))
    return meta


def prose_lines(text: str) -> List[Tuple[int, str]]:
    """Return (line number, line) pairs outside fenced code blocks."""
    lines: List[Tuple[int, str]] = []
    in_fence = False
    for number, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("```") or line.lstrip().startswith("~~~"):
            in_fence = not in_fence
            continue
        if not in_fence:
            lines.append((number, line))
    return lines


def strip_code(text: str) -> List[Tuple[int, str]]:
    """Return prose lines with inline code removed, for checks that must ignore code."""
    return [(number, INLINE_CODE.sub("", line)) for number, line in prose_lines(text)]


def headings(text: str) -> List[Tuple[int, int, str]]:
    found = []
    # Headings keep their inline code: the table of contents must show it.
    for number, line in prose_lines(text):
        match = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", line)
        if match:
            found.append((number, len(match.group(1)), match.group(2)))
    return found


def clean_for_reader(text: str) -> str:
    """Drop writer-only comments (source tags) from chapter text."""
    text = HTML_COMMENT.sub("", text)
    return re.sub(r"[ \t]+\n", "\n", text).strip() + "\n"


def assemble(workspace: Path) -> Tuple[Path, str]:
    meta = load_meta(workspace)
    assert meta is not None
    parts: List[str] = []
    title_block = ["# " + meta["title"]]
    if meta.get("subtitle"):
        title_block.append("")
        title_block.append(meta["subtitle"])
    title_block.append("")
    byline = meta["author"]
    if meta.get("date"):
        byline += " · " + meta["date"]
    title_block.append(byline)
    parts.append("\n".join(title_block) + "\n")

    chapter_texts = [clean_for_reader(read(workspace / rel)) for rel in meta["chapters"]]
    toc = ["# 차례", ""]
    for text in chapter_texts:
        for _, level, name in headings(text):
            if level == 1:
                toc.append("- " + name)
            elif level == 2:
                toc.append("    - " + name)
    parts.append("\n".join(toc) + "\n")
    for rel in meta.get("front", []):
        parts.append(clean_for_reader(read(workspace / rel)))
    parts.extend(chapter_texts)
    for rel in meta.get("back", []):
        parts.append(clean_for_reader(read(workspace / rel)))
    manuscript = "\n".join(parts)
    out = workspace / "manuscript.md"
    out.write_text(manuscript, encoding="utf-8")
    return out, sha256_text(manuscript)


def paragraphs(text: str) -> List[str]:
    body = []
    in_fence = False
    current: List[str] = []
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            if current:
                body.append(" ".join(current))
                current = []
            continue
        if in_fence or line.startswith("#") or line.startswith("|"):
            if current:
                body.append(" ".join(current))
                current = []
            continue
        if line.strip():
            current.append(line.strip())
        elif current:
            body.append(" ".join(current))
            current = []
    if current:
        body.append(" ".join(current))
    return [p for p in body if HTML_COMMENT.sub("", p).strip()]


def first_sentence(paragraph: str) -> str:
    paragraph = HTML_COMMENT.sub("", paragraph).strip()
    match = re.match(r"(.+?[.!?。])(\s|$)", paragraph)
    return (match.group(1) if match else paragraph)[:80]


def last_sentence(paragraph: str) -> str:
    paragraph = HTML_COMMENT.sub("", paragraph).strip()
    pieces = re.split(r"(?<=[.!?。])\s+", paragraph)
    return pieces[-1][:80] if pieces else paragraph[:80]


def term_rules(workspace: Path) -> List[Tuple[str, List[str]]]:
    """Read '| 표기 | 피할 표기 |' rows from the term table in plan.md."""
    plan = workspace / "plan.md"
    if not plan.is_file():
        return []
    rules = []
    in_table = False
    for line in read(plan).splitlines():
        if re.match(r"^\|\s*표기\s*\|\s*피할 표기", line):
            in_table = True
            continue
        if in_table:
            if not line.startswith("|"):
                in_table = False
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 2 or set(cells[0]) <= set("-: "):
                continue
            avoid = [a.strip() for a in re.split(r"[,、]", cells[1]) if a.strip() and a.strip() != "-"]
            if cells[0] and avoid:
                rules.append((cells[0], avoid))
    return rules


def check(workspace: Path, final: bool) -> Report:
    report = Report()
    meta = load_meta(workspace, report)
    manuscript_path = workspace / "manuscript.md"
    if not manuscript_path.is_file():
        report.fail("manuscript.md is missing; run assemble first")
        return report
    manuscript = read(manuscript_path)
    digest = sha256_text(manuscript)

    # Hard: leftover markers anywhere in the manuscript.
    for number, line in enumerate(manuscript.splitlines(), 1):
        for marker in MARKERS:
            if marker in line:
                report.fail("manuscript.md:{} leftover marker {}".format(number, marker))

    # Hard: acceptance record must match the manuscript it judged.
    record_path = workspace / "checks" / "acceptance.json"
    if record_path.is_file():
        try:
            record = json.loads(read(record_path))
            latest = record["history"][-1]
            if latest["manuscript_sha256"] != digest:
                message = (
                    "manuscript.md changed after the last verdict ({}); "
                    "re-run the check and the gate".format(latest["verdict"])
                )
                # Fixing a blocked draft is the expected path; editing an accepted
                # manuscript, or shipping any unjudged change, is not.
                if final or latest["verdict"] in PASSING_VERDICTS:
                    report.fail(message)
                else:
                    report.note("summary", message)
            elif final and latest["verdict"] not in PASSING_VERDICTS:
                report.fail("last verdict is {}; the book is not accepted".format(latest["verdict"]))
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            report.fail("checks/acceptance.json is malformed: {}".format(exc))
    elif final:
        report.fail("no acceptance record; run the gate and accept first")

    # Hard: assembled manuscript must match the chapter files.
    if meta is not None:
        chapter_texts = [read(workspace / rel) for rel in meta["chapters"]]
        for rel, text in zip(meta["chapters"], chapter_texts):
            if clean_for_reader(text) not in manuscript:
                report.fail("{} differs from manuscript.md; re-run assemble".format(rel))
    else:
        chapter_texts = []

    if meta is not None:
        report_chapters(workspace, meta, chapter_texts, report)
    report_manuscript(manuscript, report)
    report.note("summary", "manuscript sha256 {}".format(digest))
    report.note("summary", "manuscript characters {}".format(len(manuscript)))
    return report


def report_chapters(workspace: Path, meta: dict, texts: List[str], report: Report) -> None:
    count = len(texts)
    lengths = []
    openings = []
    closings = []
    for index, (rel, text) in enumerate(zip(meta["chapters"], texts), 1):
        reader_text = HTML_COMMENT.sub("", text)
        lengths.append(len(reader_text))
        heads = headings(text)
        tops = [h for h in heads if h[1] == 1]
        if len(tops) != 1:
            report.note("headings", "{}: expected one '# ' chapter heading, found {}".format(rel, len(tops)))
        previous = 1
        for number, level, name in heads:
            if level > previous + 1:
                report.note("headings", "{}:{} heading jumps from level {} to {}: {}".format(rel, number, previous, level, name))
            if not name.strip():
                report.note("headings", "{}:{} empty heading".format(rel, number))
            previous = level
        paras = paragraphs(text)
        if paras:
            openings.append("{} opening: {}".format(rel, first_sentence(paras[0])))
            closings.append("{} closing: {}".format(rel, last_sentence(paras[-1])))
        for number, line in strip_code(text):
            if line.startswith("#"):
                continue
            for match in CHAPTER_REF.finditer(line):
                target = int(match.group(1))
                flag = " (no such chapter)" if target < 1 or target > count else ""
                report.note("cross-references", "{}:{} -> {}장{}: {}".format(rel, number, target, flag, line.strip()[:100]))
            if NEXT_CHAPTER_PHRASE.search(line):
                report.note("cross-references", "{}:{} '다음 장에서' teaser: {}".format(rel, number, line.strip()[:100]))
        for para in paras:
            if NUMBER_CLAIM.search(HTML_COMMENT.sub("", para)) and not SRC_COMMENT.search(para):
                report.note("unsourced numbers", "{}: {}".format(rel, HTML_COMMENT.sub("", para)[:120]))
        contrast = len(CONTRAST.findall(reader_text))
        if contrast > 3:
            report.note("repetition", "{}: 'A가 아니라 B' pattern {} times".format(rel, contrast))
        cited = SRC_COMMENT.findall(text)
        ledger_ids = set()
        for group in cited:
            ledger_ids.update(LEDGER_ID.findall(group))
        report.note("sources", "{}: {} source tags, {} distinct ledger ids".format(rel, len(cited), len(ledger_ids)))
    if lengths:
        report.note(
            "length",
            "chapters {}; characters min {} max {} ratio {:.2f}".format(
                count, min(lengths), max(lengths), max(lengths) / max(1, min(lengths))
            ),
        )
        for rel, length in zip(meta["chapters"], lengths):
            report.note("length", "{}: {}".format(rel, length))
    for item in openings + closings:
        report.note("openings and closings", item)
    starts: Dict[str, int] = {}
    for text in texts:
        for para in paragraphs(text):
            words = HTML_COMMENT.sub("", para).split()
            if len(words) >= 2:
                key = " ".join(words[:2])
                starts[key] = starts.get(key, 0) + 1
    for key, value in sorted(starts.items(), key=lambda kv: -kv[1])[:10]:
        if value >= 3:
            report.note("repetition", "paragraphs starting '{}': {}".format(key, value))
    for preferred, avoid in term_rules(workspace):
        for rel, text in zip(meta["chapters"], texts):
            for number, line in strip_code(text):
                for variant in avoid:
                    # A variant must start a word: '리스' inside '릴리스' is not a hit.
                    if re.search(r"(?<![0-9A-Za-z\uac00-\ud7a3])" + re.escape(variant), line):
                        report.note("terms", "{}:{} '{}' (plan says '{}')".format(rel, number, variant, preferred))


def report_manuscript(manuscript: str, report: Report) -> None:
    for number, line in strip_code(manuscript):
        visible = HTML_COMMENT.sub("", line)
        for match in UNCLOSED_BOLD.finditer(visible):
            report.note(
                "markdown",
                "manuscript.md:{} bold will not render: {} (close before the parenthesis or particle)".format(
                    number, match.group(0)
                ),
            )
        for match in KOREAN_PLACEHOLDER.finditer(visible):
            report.note("placeholders", "manuscript.md:{} {}".format(number, match.group(0)))
        for term in INTERNAL_TERMS:
            if term.lower() in visible.lower():
                report.note("internal terms", "manuscript.md:{} '{}': {}".format(number, term, visible.strip()[:100]))
        for match in LEDGER_ID.finditer(visible):
            report.note("internal terms", "manuscript.md:{} ledger id '{}' visible".format(number, match.group(0)))


def render(report: Report, final: bool) -> str:
    lines = ["# Check report", ""]
    lines.append("Mode: {}".format("final" if final else "draft"))
    lines.append("")
    lines.append("## Hard failures")
    lines.append("")
    if report.hard:
        lines.extend("- " + item for item in report.hard)
    else:
        lines.append("- none")
    lines.append("")
    lines.append("## Report only (read each item; none of these blocks)")
    for section, items in report.notes.items():
        lines.append("")
        lines.append("### " + section)
        lines.append("")
        lines.extend("- " + item for item in items)
    return "\n".join(lines) + "\n"


def accept(workspace: Path, verdict: str, note: str) -> str:
    manuscript_path = workspace / "manuscript.md"
    if not manuscript_path.is_file():
        raise SystemExit("manuscript.md is missing; run assemble first")
    digest = sha256_text(read(manuscript_path))
    checks = workspace / "checks"
    checks.mkdir(exist_ok=True)
    record_path = checks / "acceptance.json"
    record = {"history": []}
    if record_path.is_file():
        record = json.loads(read(record_path))
    record["history"].append(
        {
            "verdict": verdict,
            "manuscript_sha256": digest,
            "recorded_at": datetime.datetime.now().isoformat(timespec="seconds"),
            "note": note,
        }
    )
    record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return digest


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("markers")
    p_assemble = sub.add_parser("assemble")
    p_assemble.add_argument("workspace", type=Path)
    p_check = sub.add_parser("check")
    p_check.add_argument("workspace", type=Path)
    p_check.add_argument("--final", action="store_true")
    p_accept = sub.add_parser("accept")
    p_accept.add_argument("workspace", type=Path)
    p_accept.add_argument("--verdict", required=True, choices=VERDICTS)
    p_accept.add_argument("--note", default="")
    args = parser.parse_args(argv)

    if args.command == "markers":
        for marker in MARKERS:
            print(marker)
        return 0
    if args.command == "assemble":
        out, digest = assemble(args.workspace)
        print("{} sha256 {}".format(out, digest))
        return 0
    if args.command == "check":
        report = check(args.workspace, args.final)
        checks = args.workspace / "checks"
        checks.mkdir(exist_ok=True)
        (checks / "check-report.md").write_text(render(report, args.final), encoding="utf-8")
        for item in report.hard:
            print("HARD " + item)
        counts = ", ".join("{} {}".format(k, len(v)) for k, v in report.notes.items())
        print("report-only: " + counts)
        print("wrote {}".format(checks / "check-report.md"))
        return 1 if report.hard else 0
    if args.command == "accept":
        digest = accept(args.workspace, args.verdict, args.note)
        print("recorded {} for sha256 {}".format(args.verdict, digest))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
