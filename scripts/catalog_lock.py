#!/usr/bin/env python3
"""Import the published v2.0.0 standalone ZIPs into catalog.lock.json."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.catalog import (  # noqa: E402
    PINNED_SOURCE_COMMIT,
    CatalogLock,
    LockedSkill,
)
from scripts.lib.archive import (  # noqa: E402
    extract_archive,
    sha256_file,
    verify_product_archive,
    _parse_checksums,
)
from scripts.lib.product_contract import payload_sha256  # noqa: E402


REQUIRED_ZIPS = (
    "image-workbench-v2.0.0.zip",
    "korean-writing-editor-v2.0.0.zip",
)
ALLOWED_IMPORT_NAMES = frozenset((*REQUIRED_ZIPS, "SHA256SUMS"))
ZIP_NAME_RE = re.compile(r"^([a-z0-9-]+)-v2\.0\.0\.zip$")


def import_legacy_release(release_dir: Path, source_commit: str, output: Path) -> Path:
    release_dir = Path(release_dir)
    output = Path(output)
    if source_commit != PINNED_SOURCE_COMMIT:
        raise ValueError(
            f"source_commit {source_commit!r} != {PINNED_SOURCE_COMMIT!r}"
        )
    if not release_dir.is_dir():
        raise ValueError(f"release directory is not a directory: {release_dir}")

    names = sorted(path.name for path in release_dir.iterdir())
    unexpected = [name for name in names if name not in ALLOWED_IMPORT_NAMES]
    if unexpected:
        details = []
        for name in unexpected:
            path = release_dir / name
            if path.is_dir():
                kind = "directory"
            elif name.endswith(".zip"):
                kind = "zip"
            else:
                kind = "file"
            details.append(f"unexpected {kind} in import directory: {name}")
        raise ValueError("\n".join(details))

    checksums_path = release_dir / "SHA256SUMS"
    if not checksums_path.is_file():
        raise ValueError("missing SHA256SUMS")
    checksum_errors: list[str] = []
    parsed = _parse_checksums(checksums_path, checksum_errors)
    if checksum_errors:
        raise ValueError("\n".join(checksum_errors))
    missing_rows = [name for name in REQUIRED_ZIPS if name not in parsed]
    if missing_rows:
        raise ValueError(
            "SHA256SUMS missing checksum row: " + ", ".join(missing_rows)
        )

    skills: list[LockedSkill] = []
    with tempfile.TemporaryDirectory() as directory:
        extracted_root = Path(directory)
        for archive_name in REQUIRED_ZIPS:
            archive = release_dir / archive_name
            if not archive.is_file():
                raise ValueError(f"missing archive: {archive_name}")
            digest = sha256_file(archive)
            if digest != parsed[archive_name]:
                raise ValueError(f"checksum mismatch: {archive_name}")
            product_name = _product_name(archive_name)
            product_root = _extract_standalone(archive, product_name, extracted_root)
            skills.append(
                LockedSkill(
                    name=product_name,
                    version="2.0.0",
                    tag="v2.0.0",
                    release_kind="legacy-bundle",
                    source_commit=source_commit,
                    payload_sha256=payload_sha256(product_root),
                )
            )
    skills.sort(key=lambda item: item.name)
    return _write_lock(output, CatalogLock(schema_version=1, skills=tuple(skills)))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    import_legacy = subparsers.add_parser(
        "import-legacy",
        help="Write catalog.lock.json from published v2.0.0 standalone ZIPs",
    )
    import_legacy.add_argument("--release-dir", type=Path, required=True)
    import_legacy.add_argument("--source-commit", required=True)
    import_legacy.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "import-legacy":
        try:
            path = import_legacy_release(
                args.release_dir,
                args.source_commit,
                args.output,
            )
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        print(path)
        return 0
    parser.error(f"unknown command: {args.command}")
    return 2


def _product_name(archive_name: str) -> str:
    match = ZIP_NAME_RE.fullmatch(archive_name)
    if match is None:
        raise ValueError(f"unexpected archive: {archive_name}")
    return match.group(1)


def _extract_standalone(archive_path: Path, product_name: str, destination: Path) -> Path:
    errors = verify_product_archive(archive_path, product_name)
    if errors:
        raise ValueError("\n".join(errors))
    extract_errors = extract_archive(archive_path, destination)
    if extract_errors:
        raise ValueError("\n".join(extract_errors))
    product_root = Path(destination) / product_name
    if not product_root.is_dir():
        raise ValueError(f"missing extracted skill: {product_name}")
    return product_root


def _write_lock(output: Path, lock: CatalogLock) -> Path:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": lock.schema_version,
        "skills": [
            {
                "name": item.name,
                "payload_sha256": item.payload_sha256,
                "release_kind": item.release_kind,
                "source_commit": item.source_commit,
                "tag": item.tag,
                "version": item.version,
            }
            for item in lock.skills
        ],
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    fd, tmp_name = tempfile.mkstemp(prefix=f".{output.name}.", dir=output.parent)
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(encoded)
        tmp.replace(output)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise
    return output


if __name__ == "__main__":
    raise SystemExit(main())
