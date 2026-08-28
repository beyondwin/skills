#!/usr/bin/env python3
"""Map changed paths to a fail-closed GitHub Actions verify matrix."""

from __future__ import annotations

import argparse
import os
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.change_routing import matrix_for_event, serialize_matrix  # noqa: E402
from scripts.lib.product_registry import load_registry, validate_registry  # noqa: E402
from scripts.lib.verification import REGISTERED_STAGE_NAMES  # noqa: E402


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
    parser.add_argument("--root", type=pathlib.Path, default=ROOT)
    parser.add_argument("--base", default="")
    parser.add_argument("--head", default="")
    args = parser.parse_args(argv)
    registry = load_registry(ROOT / "products.toml")
    errors = validate_registry(ROOT, registry, REGISTERED_STAGE_NAMES)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    write_github_output(
        matrix_for_event(args.event, args.root, registry, args.base, args.head)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
