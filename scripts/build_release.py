#!/usr/bin/env python3
"""Compatibility wrapper; the shared-version bundle builder is retired."""

from __future__ import annotations

import sys

MESSAGE = (
    "scripts/build_release.py no longer builds a shared-version bundle. "
    "Use scripts/release.py after the independent release pipeline lands."
)


def main(argv: list[str] | None = None) -> int:
    print(MESSAGE, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
