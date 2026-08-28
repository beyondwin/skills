from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.archive_manifest import (  # noqa: E402
    DEFAULT_IDENTIFIERS,
    DEFAULT_PREFIXES,
    CaptureError,
    build_manifest,
    canonical_bytes,
    source_problems,
    verify_manifest,
)

CAPTURE_SCRIPT = Path(__file__).resolve()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Capture or verify a read-only Archive skill migration manifest."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    capture = subparsers.add_parser("capture")
    capture.add_argument("--repository", type=Path, required=True)
    capture.add_argument("--output", type=Path, required=True)
    capture.add_argument("--prefix", action="append", dest="prefixes")
    capture.add_argument("--identifier", action="append", dest="identifiers")

    verify = subparsers.add_parser("verify")
    verify.add_argument("--repository", type=Path, required=True)
    verify.add_argument("--manifest", type=Path, required=True)

    args = parser.parse_args(argv)
    repository = args.repository.expanduser().resolve()
    if args.command == "capture":
        prefixes = tuple(args.prefixes) if args.prefixes else DEFAULT_PREFIXES
        identifiers = tuple(args.identifiers) if args.identifiers else DEFAULT_IDENTIFIERS
        return _run_capture(repository, args.output, prefixes, identifiers)
    return _run_verify(repository, args.manifest)


def _run_capture(
    repository: Path,
    output: Path,
    prefixes: tuple[str, ...],
    identifiers: tuple[str, ...],
) -> int:
    problems = source_problems(repository)
    if problems:
        _print_problems(problems)
        return 1
    try:
        payload = build_manifest(repository, prefixes, identifiers)
    except CaptureError as exc:
        _print_problems([str(exc)])
        return 1
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical_bytes(payload))
    return 0


def _run_verify(repository: Path, manifest_file: Path) -> int:
    problems = source_problems(repository)
    try:
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        problems.append(str(exc))
        _print_problems(problems)
        return 1
    if not isinstance(manifest, dict):
        problems.append("manifest digest mismatch")
        _print_problems(problems)
        return 1
    problems.extend(verify_manifest(repository, manifest))
    if problems:
        _print_problems(problems)
        return 1
    return 0


def _print_problems(problems: list[str]) -> None:
    sys.stderr.write("\n".join(problems) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
