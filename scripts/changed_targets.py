#!/usr/bin/env python3
"""Map changed paths to a fail-closed GitHub Actions verify matrix."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGETS = ("catalog", "graspic", "image-workbench", "korean-writing-editor")
PRODUCT_PREFIXES = {
    "graspic": (
        "skills/graspic/",
        "tests/products/graspic/",
        "docs/maintainers/products/graspic/",
    ),
    "image-workbench": (
        "skills/image-workbench/",
        "tests/products/image-workbench/",
        "docs/maintainers/products/image-workbench/",
    ),
    "korean-writing-editor": (
        "skills/korean-writing-editor/",
        "tests/products/korean-writing-editor/",
        "docs/maintainers/products/korean-writing-editor/",
    ),
}
PRODUCT_EXACT_PATHS = {
    "graspic": (),
    "image-workbench": (),
    "korean-writing-editor": (),
}
OS_ROWS = (
    ("ubuntu-latest", "full"),
    ("macos-latest", "full"),
    ("windows-latest", "windows-portable"),
)
SELECTORS = {
    "catalog": "--catalog",
    "graspic": "--skill graspic",
    "image-workbench": "--skill image-workbench",
    "korean-writing-editor": "--skill korean-writing-editor",
}
FULL_REPOSITORY_EVENTS = frozenset({"push", "workflow_dispatch"})


def targets_for_paths(paths: Iterable[str]) -> Sequence[str]:
    normalized = tuple(sorted({path.replace("\\", "/") for path in paths}))
    if not normalized:
        return TARGETS
    selected: set[str] = set()
    for path in normalized:
        matched = False
        for target, prefixes in PRODUCT_PREFIXES.items():
            if path.startswith(prefixes) or path in PRODUCT_EXACT_PATHS[target]:
                selected.add(target)
                matched = True
        if path.startswith("catalog/"):
            selected.add("catalog")
            matched = True
        if not matched:
            return TARGETS
    return tuple(sorted(selected))


def matrix_for_targets(targets: Iterable[str]) -> dict[str, list[dict[str, str]]]:
    wanted = set(targets)
    selected = tuple(target for target in TARGETS if target in wanted)
    if not selected:
        selected = TARGETS
    include: list[dict[str, str]] = []
    for target in selected:
        selector = SELECTORS[target]
        for os_name, profile in OS_ROWS:
            include.append(
                {
                    "target": target,
                    "os": os_name,
                    "profile": profile,
                    "selector": selector,
                }
            )
    return {"include": include}


def full_repository_matrix() -> dict[str, list[dict[str, str]]]:
    return {
        "include": [
            {"os": os_name, "profile": profile, "selector": ""}
            for os_name, profile in OS_ROWS
        ]
    }


def serialize_matrix(matrix: dict[str, list[dict[str, str]]]) -> str:
    return json.dumps(matrix, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def changed_paths(root: Path, base: str, head: str) -> Sequence[str]:
    completed = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "diff",
            "--name-only",
            "--no-renames",
            "-z",
            f"{base}...{head}",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return ()
    paths = [
        item.replace("\\", "/")
        for item in completed.stdout.split("\0")
        if item
    ]
    return tuple(paths)


def matrix_for_event(
    event: str,
    root: Path,
    base: str = "",
    head: str = "",
) -> dict[str, list[dict[str, str]]]:
    if event in FULL_REPOSITORY_EVENTS:
        return full_repository_matrix()
    if event == "pull_request" and base and head:
        return matrix_for_targets(targets_for_paths(changed_paths(root, base, head)))
    return matrix_for_targets(TARGETS)


def write_github_output(matrix: dict[str, list[dict[str, str]]]) -> None:
    payload = serialize_matrix(matrix)
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as handle:
            handle.write(f"matrix={payload}\n")
        return
    print(payload)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event", required=True)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--base", default="")
    parser.add_argument("--head", default="")
    args = parser.parse_args(argv)
    write_github_output(matrix_for_event(args.event, args.root, args.base, args.head))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
