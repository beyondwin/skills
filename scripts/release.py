#!/usr/bin/env python3
"""Check, build, and verify one independent skill product release at a time."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.catalog_contract import load_catalog_lock  # noqa: E402
from scripts.release_archive import (  # noqa: E402
    ArchiveMember,
    ReleaseError,
    _parse_checksums,
    _reject_source_name,
    ensure_new_empty_directory,
    extract_archive,
    sha256_file,
    verify_product_archive,
    write_checksums,
    write_zip,
)
from scripts.release_contract import (  # noqa: E402
    PRODUCT_NAMES,
    SEMVER_RE,
    ProductRelease,
    load_product_release,
    parse_skill_frontmatter,
    payload_sha256,
    require_dated_changelog as dated_changelog_errors,
    validate_product,
)


REGULAR_FILE_MODES = frozenset({"100644", "100755"})
SHARED_RELEASE_PATHS = (
    "scripts/release.py",
    "scripts/release_archive.py",
    "scripts/release_contract.py",
)


def check_product(root: Path, name: str, require_dated_changelog: bool) -> list[str]:
    root = Path(root)
    if name not in PRODUCT_NAMES:
        return [f"unlisted skill is not accepted: {name}"]
    skill_root = root / "skills" / name
    errors = validate_product(skill_root)
    if require_dated_changelog:
        errors.extend(dated_changelog_errors(skill_root))
    errors.extend(_working_tree_errors(root, name))
    try:
        release_info = load_product_release(skill_root)
    except (OSError, ValueError, KeyError) as exc:
        errors.append(f"release.toml: {exc}")
        return errors
    if _tag_exists(root, release_info.tag):
        errors.append(f"tag already exists: {release_info.tag}")
    if not SEMVER_RE.fullmatch(release_info.version):
        return errors
    try:
        baseline = _latest_baseline(root, name)
    except ReleaseError as exc:
        errors.append(str(exc))
        return errors
    if baseline is None:
        return errors
    baseline_version, baseline_hash = baseline
    if _semver_tuple(release_info.version) <= _semver_tuple(baseline_version):
        errors.append(
            f"target version {release_info.version} is not greater than baseline {baseline_version}"
        )
    try:
        current_hash = payload_sha256(skill_root)
    except ValueError as exc:
        errors.append(str(exc))
        return errors
    if current_hash != baseline_hash and release_info.version == baseline_version:
        errors.append(
            f"payload changed from baseline {baseline_version} but version did not advance"
        )
    return errors


def build_product(
    root: Path,
    name: str,
    output: Path,
    require_release_entry: bool = True,
) -> tuple[Path, Path]:
    root = Path(root)
    if name not in PRODUCT_NAMES:
        raise ReleaseError(f"unlisted skill is not accepted: {name}")
    skill_root = root / "skills" / name
    try:
        release_info = load_product_release(skill_root)
    except (OSError, ValueError, KeyError) as exc:
        raise ReleaseError(f"release.toml: {exc}") from exc
    if require_release_entry:
        dated = dated_changelog_errors(skill_root)
        if dated:
            raise ReleaseError("\n".join(dated))
    output = ensure_new_empty_directory(output)
    members = _tracked_product_files(root, name)
    with tempfile.TemporaryDirectory() as directory:
        staged_root = _stage_members(members, Path(directory))
        staged_errors = validate_product(staged_root)
        if staged_errors:
            raise ReleaseError("\n".join(staged_errors))
    archive = output / release_info.artifact_name
    write_zip(archive, members)
    archive_errors = verify_product_archive(archive, name)
    if archive_errors:
        raise ReleaseError("\n".join(archive_errors))
    with tempfile.TemporaryDirectory() as directory:
        destination = Path(directory)
        extract_errors = extract_archive(archive, destination)
        if extract_errors:
            raise ReleaseError("\n".join(extract_errors))
        extracted_errors = validate_product(destination / name)
        if extracted_errors:
            raise ReleaseError("\n".join(extracted_errors))
    checksums = write_checksums((archive,), output / "SHA256SUMS")
    return archive, checksums


def verify_product_download(root: Path, name: str, directory: Path) -> list[str]:
    root = Path(root)
    directory = Path(directory)
    if name not in PRODUCT_NAMES:
        return [f"unlisted skill is not accepted: {name}"]
    try:
        expected = load_product_release(root / "skills" / name)
    except (OSError, ValueError, KeyError) as exc:
        return [f"release.toml: {exc}"]
    if not directory.is_dir():
        return [f"download directory is not a directory: {directory}"]
    errors: list[str] = []
    errors.extend(_download_directory_errors(directory, expected.artifact_name))
    errors.extend(_verify_download_checksums(directory, expected.artifact_name))
    if errors:
        return errors
    archive = directory / expected.artifact_name
    archive_errors = verify_product_archive(archive, name)
    if archive_errors:
        return archive_errors
    with tempfile.TemporaryDirectory() as tmp:
        destination = Path(tmp)
        extract_errors = extract_archive(archive, destination)
        if extract_errors:
            return extract_errors
        skill_root = destination / name
        if not skill_root.is_dir():
            return [f"missing extracted skill: {name}"]
        extracted_errors = validate_product(skill_root)
        if extracted_errors:
            return [f"{name}: {error}" for error in extracted_errors]
        version_errors = _extracted_version_errors(skill_root, expected)
        if version_errors:
            return version_errors
        return _run_product_smoke(root, name, skill_root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    check = subparsers.add_parser("check", help="Validate one product for release")
    check.add_argument("--product", required=True, choices=PRODUCT_NAMES)
    build = subparsers.add_parser("build", help="Build one product ZIP and SHA256SUMS")
    build.add_argument("--product", required=True, choices=PRODUCT_NAMES)
    build.add_argument("--output", type=Path, required=True)
    verify_download = subparsers.add_parser(
        "verify-download",
        help="Verify one downloaded product ZIP and SHA256SUMS",
    )
    verify_download.add_argument("--product", required=True, choices=PRODUCT_NAMES)
    verify_download.add_argument("--input", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "check":
        errors = check_product(ROOT, args.product, False)
        for error in errors:
            print(error, file=sys.stderr)
        return 0 if not errors else 1
    if args.command == "build":
        try:
            artifacts = build_product(ROOT, args.product, args.output)
        except ReleaseError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        for path in artifacts:
            print(path)
        return 0
    if args.command == "verify-download":
        errors = verify_product_download(ROOT, args.product, args.input)
        for error in errors:
            print(error, file=sys.stderr)
        return 0 if not errors else 1
    parser.error(f"unknown command: {args.command}")
    return 2


def _download_directory_errors(directory: Path, expected_zip: str) -> list[str]:
    expected = {expected_zip, "SHA256SUMS"}
    errors: list[str] = []
    for path in sorted(directory.iterdir(), key=lambda item: item.name):
        if path.name in expected:
            continue
        if path.is_dir():
            errors.append(f"unexpected directory in download directory: {path.name}")
        elif path.suffix == ".zip":
            errors.append(f"unexpected zip in download directory: {path.name}")
        else:
            errors.append(f"unexpected file in download directory: {path.name}")
    return errors


def _verify_download_checksums(directory: Path, expected_zip: str) -> list[str]:
    checksums_path = directory / "SHA256SUMS"
    archive = directory / expected_zip
    if not checksums_path.is_file():
        errors = ["missing SHA256SUMS"]
        if not archive.is_file():
            errors.append(f"missing archive: {expected_zip}")
        return errors
    parse_errors: list[str] = []
    try:
        parsed = _parse_checksums(checksums_path, parse_errors)
    except (OSError, UnicodeError) as exc:
        return [f"SHA256SUMS: {exc}"]
    if parse_errors:
        return parse_errors
    errors: list[str] = []
    if set(parsed) != {expected_zip}:
        errors.append("SHA256SUMS must list exactly the expected product zip")
    if not archive.is_file():
        errors.append(f"missing archive: {expected_zip}")
        return errors
    if expected_zip in parsed and sha256_file(archive) != parsed[expected_zip]:
        errors.append(f"checksum mismatch: {expected_zip}")
    return errors


def _extracted_version_errors(skill_root: Path, expected: ProductRelease) -> list[str]:
    try:
        extracted = load_product_release(skill_root)
    except (OSError, ValueError, KeyError) as exc:
        return [f"release.toml: {exc}"]
    if extracted.version != expected.version:
        return [f"metadata version mismatch: {extracted.version} != {expected.version}"]
    frontmatter = parse_skill_frontmatter((skill_root / "SKILL.md").read_text(encoding="utf-8"))
    metadata = frontmatter.get("metadata")
    skill_version = metadata.get("version") if isinstance(metadata, dict) else None
    if skill_version != expected.version:
        return [f"metadata version mismatch: {skill_version} != {expected.version}"]
    return []


def _run_product_smoke(root: Path, name: str, skill_root: Path) -> list[str]:
    if name == "korean-writing-editor":
        return _run_korean(root, skill_root)
    if name == "image-workbench":
        inspector = skill_root / "scripts" / "inspect_asset.py"
        errors = _run_image(root, skill_root)
        errors.extend(_run_inspector(root, inspector))
        return errors
    if name == "graspic":
        return _smoke_graspic(skill_root)
    return [f"unlisted skill is not accepted: {name}"]


def _smoke_graspic(skill_root: Path) -> list[str]:
    errors: list[str] = []
    skill_md = skill_root / "SKILL.md"
    if skill_md.is_file():
        text = skill_md.read_text(encoding="utf-8")
        parts = text.split("---", 2)
        frontmatter = parts[1] if len(parts) > 2 else ""
        if "eli5" in frontmatter.lower():
            errors.append("graspic: SKILL.md description contains eli5")
        if "바로 / 하나" in frontmatter:
            errors.append("graspic: SKILL.md description contains workflow shorthand")
        if "Use when" not in frontmatter:
            errors.append("graspic: SKILL.md missing Use when")
        if "/graspic" not in frontmatter:
            errors.append("graspic: SKILL.md missing /graspic")
    for relative in (
        "SKILL.md",
        "LICENSE.txt",
        "agents/openai.yaml",
        "references/output.md",
        "references/visuals.md",
        "references/korean.md",
        "references/stakes.md",
        "references/sources.md",
    ):
        if not (skill_root / relative).is_file():
            errors.append(f"graspic: missing {relative}")
    names = {path.name for path in skill_root.rglob("*") if path.is_file()}
    if "test_contract.py" in names:
        errors.append("graspic: payload includes test_contract.py")
    if "cases.json" in names:
        errors.append("graspic: payload includes cases.json")
    markdown: list[str] = []
    for path in skill_root.rglob("*.md"):
        try:
            markdown.append(path.read_text(encoding="utf-8"))
        except OSError:
            continue
    if "<html" in "\n".join(markdown).lower():
        errors.append("graspic: payload includes html template")
    return errors


def _run_korean(root: Path, skill_root: Path) -> list[str]:
    return _run_command(
        "korean-offline",
        [
            sys.executable,
            str(root / "tests" / "korean-writing-editor" / "offline" / "run.py"),
            "--scope",
            "full",
            "--skill-root",
            str(skill_root),
        ],
        cwd=root,
    )


def _run_image(root: Path, skill_root: Path) -> list[str]:
    return _run_command(
        "image-contract",
        [
            sys.executable,
            str(root / "tests" / "image-workbench" / "run.py"),
            "--scope",
            "full",
            "--skill-root",
            str(skill_root),
        ],
        cwd=root,
    )


def _run_inspector(root: Path, inspector: Path) -> list[str]:
    if not inspector.is_file():
        return [f"missing extracted inspector: {inspector}"]
    env = os.environ.copy()
    env["IMAGE_WORKBENCH_INSPECTOR"] = str(inspector)
    return _run_command(
        "image-inspector",
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            str(root / "tests" / "image-workbench"),
            "-p",
            "test_*.py",
        ],
        cwd=root,
        env=env,
    )


def _run_command(
    stage: str,
    argv: list[str],
    cwd: Path,
    env: dict[str, str] | None = None,
) -> list[str]:
    completed = subprocess.run(
        argv,
        cwd=str(cwd),
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    if completed.returncode == 0:
        return []
    detail = (completed.stderr or completed.stdout).strip()
    return [f"{stage} failed ({completed.returncode}): {detail}"]


def _tracked_product_files(root: Path, name: str) -> list[ArchiveMember]:
    prefix = f"skills/{name}/"
    output = _git(root, "ls-files", "-s", "-z", "--", prefix)
    members: list[ArchiveMember] = []
    seen: set[str] = set()
    for record in _nul_items(output):
        mode, blob_oid, remainder = record.split(" ", 2)
        _stage, relative = remainder.split("\t", 1)
        relative = _posix(relative)
        if not relative.startswith(prefix):
            raise ReleaseError(f"unexpected tracked path: {relative}")
        member_name = relative.removeprefix("skills/")
        if member_name in seen:
            raise ReleaseError(f"duplicate tracked path: {relative}")
        seen.add(member_name)
        _reject_source_name(member_name)
        if mode not in REGULAR_FILE_MODES:
            raise ReleaseError(f"symlink or special file: {relative}")
        data = _git_bytes(root, "cat-file", "blob", blob_oid)
        members.append(
            ArchiveMember(
                name=member_name,
                data=data,
                executable=_is_executable(mode, data),
            )
        )
    if not members:
        raise ReleaseError(f"no tracked payload files for {name}")
    members.sort(key=lambda item: item.name)
    return members


def _stage_members(members: Sequence[ArchiveMember], destination: Path) -> Path:
    destination = Path(destination)
    root = destination.resolve()
    product_root: Path | None = None
    for member in members:
        target = (destination / member.name).resolve()
        if not target.is_relative_to(root):
            raise ReleaseError(f"extract escapes destination: {member.name}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(member.data)
        if member.executable:
            target.chmod(0o755)
        product_root = destination / member.name.split("/", 1)[0]
    if product_root is None or not product_root.is_dir():
        raise ReleaseError("missing extracted skill")
    return product_root


def _working_tree_errors(root: Path, name: str) -> list[str]:
    paths = (f"skills/{name}", *SHARED_RELEASE_PATHS)
    try:
        output = _git(root, "status", "--porcelain", "--untracked-files=all", "--", *paths)
    except ReleaseError as exc:
        return [str(exc)]
    if output.strip():
        return ["working tree is not clean for this product and shared release code"]
    return []


def _latest_baseline(root: Path, name: str) -> tuple[str, str] | None:
    candidates: list[tuple[tuple[int, int, int], str, str]] = []
    for tag in _git_tags(root, f"{name}-v*"):
        version = tag.removeprefix(f"{name}-v")
        if not SEMVER_RE.fullmatch(version):
            continue
        digest = _payload_sha256_from_tag(root, tag, name)
        candidates.append((_semver_tuple(version), version, digest))
    lock_path = root / "catalog" / "catalog.lock.json"
    if lock_path.is_file():
        try:
            lock = load_catalog_lock(lock_path)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise ReleaseError(f"catalog.lock.json: {exc}") from exc
        for item in lock.skills:
            if item.name == name:
                candidates.append(
                    (_semver_tuple(item.version), item.version, item.payload_sha256)
                )
    if not candidates:
        return None
    candidates.sort()
    _key, version, digest = candidates[-1]
    return version, digest


def _payload_sha256_from_tag(root: Path, tag: str, name: str) -> str:
    prefix = f"skills/{name}/"
    output = _git(root, "ls-tree", "-r", "-z", tag, "--", prefix)
    with tempfile.TemporaryDirectory() as directory:
        dest = Path(directory) / name
        for record in _nul_items(output):
            meta, path = record.split("\t", 1)
            _mode, _kind, blob_oid = meta.split()
            relative = _posix(path).removeprefix(prefix)
            target = dest / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(_git_bytes(root, "cat-file", "blob", blob_oid))
        if not dest.is_dir():
            raise ReleaseError(f"missing product {name} in tag {tag}")
        return payload_sha256(dest)


def _tag_exists(root: Path, tag: str) -> bool:
    completed = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "-q", "--verify", f"refs/tags/{tag}"],
        check=False,
        capture_output=True,
    )
    return completed.returncode == 0


def _git_tags(root: Path, pattern: str) -> list[str]:
    output = _git(root, "tag", "--list", pattern)
    return [line for line in output.splitlines() if line]


def _semver_tuple(version: str) -> tuple[int, int, int]:
    major, minor, patch = version.split(".")
    return int(major), int(minor), int(patch)


def _is_executable(mode: str, data: bytes) -> bool:
    return mode == "100755" or data.startswith(b"#!")


def _git(root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *arguments],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise ReleaseError(detail or f"git {' '.join(arguments)} failed")
    return completed.stdout.rstrip("\n")


def _git_bytes(root: Path, *arguments: str) -> bytes:
    completed = subprocess.run(
        ["git", "-C", str(root), *arguments],
        check=False,
        capture_output=True,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).decode("utf-8", "replace").strip()
        raise ReleaseError(detail or f"git {' '.join(arguments)} failed")
    return completed.stdout


def _nul_items(payload: str) -> list[str]:
    if not payload:
        return []
    return [item for item in payload.split("\0") if item]


def _posix(value: str) -> str:
    return value.replace("\\", "/")


if __name__ == "__main__":
    raise SystemExit(main())
