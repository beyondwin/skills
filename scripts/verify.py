#!/usr/bin/env python3
"""Provider-free repository verification orchestrator."""

from __future__ import annotations

import argparse
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.product_registry import load_registry, validate_registry  # noqa: E402
from scripts.lib.verification import (  # noqa: E402
    PROFILES,
    REGISTERED_STAGE_NAMES,
    run_stages,
    stages,
)


def build_parser(names: tuple[str, ...]) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profile",
        choices=PROFILES,
        default="full",
        help="verification profile (default: full)",
    )
    target = parser.add_mutually_exclusive_group()
    target.add_argument("--skill", choices=names)
    target.add_argument("--catalog", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    registry = load_registry(ROOT / "products.toml")
    errors = validate_registry(ROOT, registry, REGISTERED_STAGE_NAMES)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    parser = build_parser(registry.names)
    args = parser.parse_args(argv)
    return run_stages(stages(ROOT, args.profile, registry, skill=args.skill, catalog=args.catalog))


if __name__ == "__main__":
    raise SystemExit(main())
