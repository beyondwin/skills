#!/usr/bin/env python3
"""Check, build, and verify one product or a locked catalog bundle."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import stat
import subprocess
import sys
import tempfile
import zipfile
from collections.abc import Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.catalog import (  # noqa: E402
    CatalogLock,
    catalog_artifact_name,
    load_catalog_lock,
    load_catalog_release,
    locked_artifact_name,
    locked_extract_errors,
    validate_catalog,
    validate_catalog_inputs,
)
from scripts.lib.archive import (  # noqa: E402
    FORBIDDEN_NAMES,
    FORBIDDEN_PARTS,
    ArchiveMember,
    ReleaseError,
    _member_mode_errors,
    _member_safety_errors,
    _parse_checksums,
    _reject_source_name,
    ensure_new_empty_directory,
    extract_archive,
    sha256_file,
    verify_product_archive,
    write_checksums,
    write_zip,
)
from scripts.lib.product_contract import (  # noqa: E402
    SEMVER_RE,
    ProductRelease,
    load_product_release,
    parse_skill_frontmatter,
    payload_sha256,
    require_dated_changelog as dated_changelog_errors,
    validate_product,
)
from scripts.lib.product_registry import load_registry  # noqa: E402


REGULAR_FILE_MODES = frozenset({"100644", "100755"})
SHARED_RELEASE_PATHS = (
    "products.toml",
    "scripts/release.py",
    "scripts/lib/archive.py",
    "scripts/lib/catalog.py",
    "scripts/lib/product_contract.py",
    "scripts/lib/product_registry.py",
)
PRE_SDD_REVIEW_PAYLOAD_FILES = frozenset(
    {
        "CHANGELOG.md",
        "LICENSE.txt",
        "README.en.md",
        "README.md",
        "SKILL.md",
        "agents/openai.yaml",
        "evidence/pre_sdd_review_evidence/__init__.py",
        "evidence/pre_sdd_review_evidence/schema.py",
        "references/reviewer-protocol.md",
        "release.toml",
    }
)
REGISTRY = load_registry(ROOT / "products.toml")


def check_product(root: Path, name: str, require_dated_changelog: bool) -> list[str]:
    root = Path(root)
    if name not in REGISTRY.names:
        return [f"unlisted skill is not accepted: {name}"]
    skill_root = root / "skills" / name
    errors = validate_product(skill_root, REGISTRY)
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
    if name not in REGISTRY.names:
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
        staged_errors = validate_product(staged_root, REGISTRY)
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
        extracted_errors = validate_product(destination / name, REGISTRY)
        if extracted_errors:
            raise ReleaseError("\n".join(extracted_errors))
    checksums = write_checksums((archive,), output / "SHA256SUMS")
    return archive, checksums


def verify_product_download(root: Path, name: str, directory: Path) -> list[str]:
    root = Path(root)
    directory = Path(directory)
    if name not in REGISTRY.names:
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
    if name == "pre-sdd-review":
        archive_errors = _pre_sdd_review_archive_errors(archive)
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
        extracted_errors = validate_product(skill_root, REGISTRY)
        if extracted_errors:
            return [f"{name}: {error}" for error in extracted_errors]
        if name == "pre-sdd-review":
            try:
                extracted_payload = payload_sha256(skill_root)
                source_payload = payload_sha256(root / "skills" / name)
            except ValueError as exc:
                return [f"pre-sdd-review: cannot compare extracted payload: {exc}"]
            if extracted_payload != source_payload:
                return [
                    "pre-sdd-review: extracted payload does not match current source payload"
                ]
        version_errors = _extracted_version_errors(skill_root, expected)
        if version_errors:
            return version_errors
        return _run_product_smoke(root, name, skill_root)


def build_catalog(root: Path, input_dir: Path, output: Path) -> tuple[Path, Path]:
    root = Path(root)
    input_dir = Path(input_dir)
    errors = validate_catalog_inputs(root, input_dir, REGISTRY)
    if errors:
        raise ReleaseError("\n".join(errors))
    output = ensure_new_empty_directory(output)
    release_info = load_catalog_release(root / "catalog" / "release.toml")
    lock = load_catalog_lock(root / "catalog" / "catalog.lock.json")
    plugin_path = root / "catalog" / "plugin" / ".codex-plugin" / "plugin.json"
    license_path = root / "LICENSE"
    notice_path = root / "NOTICE"
    for path, label in (
        (plugin_path, "catalog/plugin/.codex-plugin/plugin.json"),
        (license_path, "LICENSE"),
        (notice_path, "NOTICE"),
    ):
        if not path.is_file():
            raise ReleaseError(f"missing {label}")
    members: list[ArchiveMember] = [
        ArchiveMember(".codex-plugin/plugin.json", _read_bytes(plugin_path), False),
        ArchiveMember("LICENSE", _read_bytes(license_path), False),
        ArchiveMember("NOTICE", _read_bytes(notice_path), False),
    ]
    standalone_payloads: dict[str, dict[str, bytes]] = {}
    for item in lock.skills:
        archive = input_dir / locked_artifact_name(item)
        payload, skill_members = _standalone_skill_members(archive, item.name)
        standalone_payloads[item.name] = payload
        members.extend(skill_members)
    plugin_zip = output / catalog_artifact_name(release_info)
    write_zip(plugin_zip, members)
    archive_errors = _verify_catalog_archive(plugin_zip, lock)
    if archive_errors:
        raise ReleaseError("\n".join(archive_errors))
    equivalence = _plugin_standalone_equivalence_errors(plugin_zip, standalone_payloads)
    if equivalence:
        raise ReleaseError("\n".join(equivalence))
    checksums = write_checksums((plugin_zip,), output / "SHA256SUMS")
    return plugin_zip, checksums


def verify_catalog_download(root: Path, directory: Path) -> list[str]:
    root = Path(root)
    directory = Path(directory)
    errors = validate_catalog(root)
    if errors:
        return errors
    if not directory.is_dir():
        return [f"download directory is not a directory: {directory}"]
    release_info = load_catalog_release(root / "catalog" / "release.toml")
    lock = load_catalog_lock(root / "catalog" / "catalog.lock.json")
    expected_zip = catalog_artifact_name(release_info)
    errors.extend(_download_directory_errors(directory, expected_zip))
    errors.extend(_verify_download_checksums(directory, expected_zip))
    if errors:
        return errors
    archive = directory / expected_zip
    archive_errors = _verify_catalog_archive(archive, lock)
    if archive_errors:
        return archive_errors
    with tempfile.TemporaryDirectory() as tmp:
        destination = Path(tmp)
        extract_errors = extract_archive(archive, destination)
        if extract_errors:
            return extract_errors
        plugin_path = destination / ".codex-plugin" / "plugin.json"
        if not plugin_path.is_file():
            return ["missing .codex-plugin/plugin.json"]
        try:
            plugin = json.loads(plugin_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return [f"invalid catalog plugin manifest: {exc}"]
        plugin_version = plugin.get("version") if isinstance(plugin, dict) else None
        if plugin_version != release_info.version:
            return [
                f"catalog/plugin version {plugin_version!r} != {release_info.version!r}"
            ]
        skills_root = destination / "skills"
        present = (
            {path.name for path in skills_root.iterdir() if path.is_dir()}
            if skills_root.is_dir()
            else set()
        )
        lock_names = {item.name for item in lock.skills}
        if present != lock_names:
            return [
                "plugin members do not match lock: "
                f"{sorted(present)} != {sorted(lock_names)}"
            ]
        collected: list[str] = []
        for item in lock.skills:
            skill_root = skills_root / item.name
            item_errors = locked_extract_errors(root, skill_root, item, REGISTRY)
            for error in item_errors:
                if error == f"payload hash mismatch: {item.name}":
                    collected.append(
                        f"{item.name}: standalone payload is not byte-equivalent"
                    )
                else:
                    collected.append(error)
            if item_errors:
                continue
            collected.extend(_run_product_smoke(root, item.name, skill_root))
        return collected


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    check = subparsers.add_parser("check", help="Validate one product or catalog for release")
    _add_target_selector(check)
    check.add_argument("--input", type=Path)
    build = subparsers.add_parser("build", help="Build one product or catalog ZIP and SHA256SUMS")
    _add_target_selector(build)
    build.add_argument("--input", type=Path)
    build.add_argument("--output", type=Path, required=True)
    verify_download = subparsers.add_parser(
        "verify-download",
        help="Verify one downloaded product or catalog ZIP and SHA256SUMS",
    )
    _add_target_selector(verify_download)
    verify_download.add_argument("--input", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "check":
        if args.catalog:
            if args.input is None:
                parser.error("check --catalog requires --input")
            errors = validate_catalog_inputs(ROOT, args.input, REGISTRY)
        else:
            if args.input is not None:
                parser.error("check --product does not accept --input")
            errors = check_product(ROOT, args.product, False)
        for error in errors:
            print(error, file=sys.stderr)
        return 0 if not errors else 1
    if args.command == "build":
        if args.catalog:
            if args.input is None:
                parser.error("build --catalog requires --input")
            try:
                artifacts = build_catalog(ROOT, args.input, args.output)
            except ReleaseError as exc:
                print(str(exc), file=sys.stderr)
                return 1
        else:
            if args.input is not None:
                parser.error("build --product does not accept --input")
            try:
                artifacts = build_product(ROOT, args.product, args.output)
            except ReleaseError as exc:
                print(str(exc), file=sys.stderr)
                return 1
        for path in artifacts:
            print(path)
        return 0
    if args.command == "verify-download":
        if args.catalog:
            errors = verify_catalog_download(ROOT, args.input)
        else:
            errors = verify_product_download(ROOT, args.product, args.input)
        for error in errors:
            print(error, file=sys.stderr)
        return 0 if not errors else 1
    parser.error(f"unknown command: {args.command}")
    return 2


def _add_target_selector(parser: argparse.ArgumentParser) -> None:
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--product", choices=REGISTRY.names)
    group.add_argument("--catalog", action="store_true")


def _read_bytes(path: Path) -> bytes:
    # Isolation tests patch Path.read_bytes; this repo's path contains "/skills/".
    with open(path, "rb") as handle:
        return handle.read()


def _standalone_skill_members(
    archive: Path, product_name: str
) -> tuple[dict[str, bytes], list[ArchiveMember]]:
    prefix = f"{product_name}/"
    payload: dict[str, bytes] = {}
    members: list[ArchiveMember] = []
    with zipfile.ZipFile(archive) as source:
        for info in source.infolist():
            if info.is_dir() or info.filename.endswith("/"):
                continue
            name = info.filename.replace("\\", "/")
            if not name.startswith(prefix):
                raise ReleaseError(f"unexpected member: {name}")
            data = source.read(info)
            payload[name] = data
            unix_mode = (info.external_attr >> 16) & 0o777
            executable = bool(unix_mode & 0o111) or data.startswith(b"#!")
            members.append(ArchiveMember(f"skills/{name}", data, executable))
    return payload, members


def _plugin_standalone_equivalence_errors(
    plugin_zip: Path, standalone_payloads: dict[str, dict[str, bytes]]
) -> list[str]:
    errors: list[str] = []
    with zipfile.ZipFile(plugin_zip) as plugin:
        for name, expected in standalone_payloads.items():
            prefix = f"skills/{name}/"
            actual = {
                member.removeprefix("skills/"): plugin.read(member)
                for member in plugin.namelist()
                if member.startswith(prefix) and not member.endswith("/")
            }
            if actual != expected:
                errors.append(f"{name}: standalone payload is not byte-equivalent")
    return errors


def _verify_catalog_archive(path: Path, lock: CatalogLock) -> list[str]:
    path = Path(path)
    try:
        archive = zipfile.ZipFile(path)
    except zipfile.BadZipFile as exc:
        return [f"invalid zip: {exc}"]
    errors: list[str] = []
    seen: set[str] = set()
    folded: dict[str, str] = {}
    allowed_root = {".codex-plugin/plugin.json", "LICENSE", "NOTICE"}
    allowed_prefixes = tuple(f"skills/{item.name}/" for item in lock.skills)
    lock_names = {item.name for item in lock.skills}
    skill_dirs: set[str] = set()
    with archive:
        for info in archive.infolist():
            name = info.filename
            member_errors = _member_safety_errors(name, seen, folded)
            errors.extend(member_errors)
            errors.extend(_member_mode_errors(name, info))
            if member_errors:
                continue
            if name.endswith("/"):
                continue
            if name in allowed_root:
                continue
            posix = pathlib.PurePosixPath(name)
            if any(part in FORBIDDEN_PARTS for part in posix.parts):
                errors.append(f"unexpected member: {name}")
                continue
            if posix.name in FORBIDDEN_NAMES:
                errors.append(f"unexpected member: {name}")
                continue
            if not name.startswith("skills/"):
                errors.append(f"unexpected member: {name}")
                continue
            parts = name.split("/")
            if len(parts) < 3 or not parts[1]:
                errors.append(f"unexpected member: {name}")
                continue
            skill_dirs.add(parts[1])
            if not name.startswith(allowed_prefixes):
                errors.append(f"unexpected member: {name}")
    if skill_dirs != lock_names:
        errors.append(
            "plugin members do not match lock: "
            f"{sorted(skill_dirs)} != {sorted(lock_names)}"
        )
    required = [".codex-plugin/plugin.json", "LICENSE", "NOTICE"]
    for item in lock.skills:
        required.append(f"skills/{item.name}/SKILL.md")
        required.append(f"skills/{item.name}/LICENSE.txt")
    for member in required:
        if member not in seen:
            errors.append(f"missing required member: {member}")
    return errors


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
    if name == "how-it-works":
        return _smoke_how_it_works(skill_root)
    if name == "pre-sdd-review":
        return _smoke_pre_sdd_review(skill_root)
    return [f"unlisted skill is not accepted: {name}"]


def _smoke_pre_sdd_review(skill_root: Path) -> list[str]:
    present = {
        path.relative_to(skill_root).as_posix()
        for path in skill_root.rglob("*")
        if path.is_file()
    }
    errors = [
        f"pre-sdd-review: missing payload member: {relative}"
        for relative in sorted(PRE_SDD_REVIEW_PAYLOAD_FILES - present)
    ]
    for relative in sorted(present - PRE_SDD_REVIEW_PAYLOAD_FILES):
        if relative == "scripts" or relative.startswith("scripts/"):
            errors.append(
                "pre-sdd-review: unexpected runtime/scripts payload member: "
                f"{relative}"
            )
        else:
            errors.append(f"pre-sdd-review: unexpected payload member: {relative}")
    return errors


def _pre_sdd_review_archive_errors(archive: Path) -> list[str]:
    expected = {
        f"pre-sdd-review/{relative}"
        for relative in PRE_SDD_REVIEW_PAYLOAD_FILES
    }
    with zipfile.ZipFile(archive) as source:
        infos = list(source.infolist())
    present = {info.filename for info in infos}
    errors = [
        f"pre-sdd-review: missing archive member: {name}"
        for name in sorted(expected - present)
    ]
    errors.extend(
        f"pre-sdd-review: unexpected archive member: {name}"
        for name in sorted(present - expected)
    )
    for info in infos:
        file_type = (info.external_attr >> 16) & 0o170000
        is_directory = info.filename.endswith("/") or file_type == stat.S_IFDIR
        if is_directory:
            errors.append(
                f"pre-sdd-review: directory archive member: {info.filename}"
            )
        if info.filename in expected and info.create_system != 3:
            errors.append(
                "pre-sdd-review: archive member creator/type mismatch: "
                f"{info.filename} requires Unix creator system 3 "
                "with regular-file mode"
            )
        if info.filename in expected and file_type != stat.S_IFREG:
            errors.append(
                "pre-sdd-review: archive member type mismatch: "
                f"{info.filename} is not a regular file"
            )
        unix_mode = (info.external_attr >> 16) & 0o777
        if (
            info.filename in expected
            and file_type == stat.S_IFREG
            and unix_mode & 0o111
        ):
            errors.append(
                "pre-sdd-review: unexpected executable archive member: "
                f"{info.filename}"
            )
    return errors


def _smoke_how_it_works(skill_root: Path) -> list[str]:
    errors: list[str] = []
    skill_md = skill_root / "SKILL.md"
    if skill_md.is_file():
        text = skill_md.read_text(encoding="utf-8")
        parts = text.split("---", 2)
        frontmatter = parts[1] if len(parts) > 2 else ""
        if "/eli5" in frontmatter.lower():
            errors.append("how-it-works: SKILL.md description contains /eli5")
        if "바로 / 하나" in frontmatter:
            errors.append("how-it-works: SKILL.md description contains workflow shorthand")
        if "Use when" not in frontmatter:
            errors.append("how-it-works: SKILL.md missing Use when")
        if "/how-it-works" not in text:
            errors.append("how-it-works: SKILL.md missing /how-it-works")
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
            errors.append(f"how-it-works: missing {relative}")
    names = {path.name for path in skill_root.rglob("*") if path.is_file()}
    if "test_contract.py" in names:
        errors.append("how-it-works: payload includes test_contract.py")
    if "cases.json" in names:
        errors.append("how-it-works: payload includes cases.json")
    markdown: list[str] = []
    for path in skill_root.rglob("*.md"):
        try:
            markdown.append(path.read_text(encoding="utf-8"))
        except OSError:
            continue
    if "<html" in "\n".join(markdown).lower():
        errors.append("how-it-works: payload includes html template")
    return errors


def _run_korean(root: Path, skill_root: Path) -> list[str]:
    return _run_command(
        "korean-offline",
        [
            sys.executable,
            str(root / "tests" / "products" / "korean-writing-editor" / "offline" / "run.py"),
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
            str(root / "tests" / "products" / "image-workbench" / "run.py"),
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
            str(root / "tests" / "products" / "image-workbench"),
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
