"""Extract a single task section from a Markdown implementation plan.

Given the exact heading text of a task (excluding the leading ``#`` marks),
this scans the plan for ATX headings outside of fenced code blocks, selects
the one section whose title matches exactly, and returns (or writes) that
section's original source bytes untouched.

Pass ``--global-constraints`` to prepend the plan's Global Constraints section.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_HEADING_RE = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*))?$")
_FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
GLOBAL_CONSTRAINT_TITLES = frozenset({"Global Constraints", "Global constraints"})


def _strip_closing_hashes(text: str) -> str:
    """Strip an optional closing run of '#' from an ATX heading's content."""
    text = text.strip()
    if not text:
        return text
    end = len(text)
    while end > 0 and text[end - 1] == "#":
        end -= 1
    if end == len(text):
        return text
    if end == 0:
        return ""
    if text[end - 1] in (" ", "\t"):
        return text[:end].rstrip()
    return text


def _scan_headings(decoded_lines: list[str]) -> list[tuple[int, int, str]]:
    """Return (line_index, level, title) for each ATX heading outside fences."""
    headings: list[tuple[int, int, str]] = []
    fence_char: str | None = None
    fence_len = 0
    for index, raw_line in enumerate(decoded_lines):
        line = raw_line.rstrip("\r\n")

        if fence_char is not None:
            match = _FENCE_RE.match(line)
            if match is not None:
                run = match.group(1)
                remainder = line[match.end():]
                if run[0] == fence_char and len(run) >= fence_len and remainder.strip() == "":
                    fence_char = None
                    fence_len = 0
            continue

        fence_match = _FENCE_RE.match(line)
        if fence_match is not None:
            run = fence_match.group(1)
            fence_char = run[0]
            fence_len = len(run)
            continue

        heading_match = _HEADING_RE.match(line)
        if heading_match is None:
            continue
        level = len(heading_match.group(1))
        title = _strip_closing_hashes(heading_match.group(2) or "")
        headings.append((index, level, title))
    return headings


def _select_section(
    headings: list[tuple[int, int, str]], requested: str, line_count: int
) -> tuple[int, int]:
    matches = [item for item in headings if item[2] == requested]
    if not matches:
        raise ValueError(f"no heading matches {requested!r}")
    if len(matches) > 1:
        raise ValueError(f"heading {requested!r} matches more than one section")
    start, level, _ = matches[0]
    end = line_count
    for other_start, other_level, _ in headings:
        if other_start > start and other_level <= level:
            end = other_start
            break
    return start, end


def _section_bytes(
    lines: list[bytes],
    decoded_lines: list[str],
    start: int,
    end: int,
    heading: str,
) -> bytes:
    body = decoded_lines[start + 1 : end]
    if all(text.strip() == "" for text in body):
        raise ValueError(f"section {heading!r} has an empty body")
    return b"".join(lines[start:end])


def extract_task(
    plan: bytes,
    heading: str,
    *,
    global_constraints: bool = False,
) -> bytes:
    """Extract the section for ``heading`` from ``plan``, byte-for-byte.

    When ``global_constraints`` is true, prepend the plan's Global Constraints
    section (no extra separator newline). Raises ValueError when the heading
    has no match, more than one match, or an empty (blank-only) body — and,
    with the flag, when constraints are missing, duplicated, or empty.
    """
    lines = plan.splitlines(keepends=True)
    decoded_lines = [line.decode("utf-8") for line in lines]
    headings = _scan_headings(decoded_lines)
    start, end = _select_section(headings, heading, len(lines))
    section = _section_bytes(lines, decoded_lines, start, end, heading)
    if not global_constraints:
        return section
    matches = [item for item in headings if item[2] in GLOBAL_CONSTRAINT_TITLES]
    if not matches:
        raise ValueError("no heading matches 'Global Constraints'")
    if len(matches) > 1:
        raise ValueError("heading 'Global Constraints' matches more than one section")
    c_start, c_level, c_title = matches[0]
    c_end = len(lines)
    for other_start, other_level, _ in headings:
        if other_start > c_start and other_level <= c_level:
            c_end = other_start
            break
    constraints = _section_bytes(lines, decoded_lines, c_start, c_end, c_title)
    return constraints + section


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="extract_task.py")
    parser.add_argument("plan", type=Path)
    parser.add_argument("--heading", required=True)
    parser.add_argument("--global-constraints", action="store_true")
    parser.add_argument("--output", required=True, type=Path)
    try:
        args = parser.parse_args(argv)
    except SystemExit as error:
        code = error.code
        return code if isinstance(code, int) else 2

    try:
        plan_bytes = args.plan.read_bytes()
    except OSError as error:
        print(f"error: cannot read plan file: {error}", file=sys.stderr)
        return 2

    try:
        section = extract_task(
            plan_bytes,
            args.heading,
            global_constraints=args.global_constraints,
        )
    except UnicodeDecodeError as error:
        print(f"error: plan file is not valid UTF-8: {error}", file=sys.stderr)
        return 2
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 3

    output_path: Path = args.output
    try:
        with open(output_path, "xb") as handle:
            handle.write(section)
    except FileExistsError:
        print(f"error: output already exists: {output_path}", file=sys.stderr)
        return 2
    except OSError as error:
        if output_path.exists():
            try:
                output_path.unlink()
            except OSError:
                pass
        print(f"error: failed to write output: {error}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
