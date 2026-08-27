#!/usr/bin/env python3
"""Deterministic v2 release archives and extraction smokes."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import pathlib
import re
import stat
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from types import ModuleType
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]

ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)
PLUGIN_NAME = "beyondwin-skills"
SKILLS = ("korean-writing-editor", "image-workbench", "graspic")
PLUGIN_TRACKED = (
    ".codex-plugin/plugin.json",
    "LICENSE",
    "NOTICE",
    "skills/korean-writing-editor/",
    "skills/image-workbench/",
    "skills/graspic/",
)
REGULAR_FILE_MODES = frozenset({"100644", "100755"})
FORBIDDEN_PARTS = frozenset(
    {
        "tests",
        "evals",
        "__pycache__",
        ".evidence",
        "receipts",
        "generated-media",
        ".git",
        ".github",
    }
)
FORBIDDEN_NAMES = frozenset({"README.md", "CHANGE_PROTOCOL.md"})
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")


class ReleaseError(RuntimeError):
    """Raised when a release archive cannot be built."""


def zip_info(name: str, executable: bool) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, ZIP_EPOCH)
    mode = 0o755 if executable else 0o644
    info.external_attr = (stat.S_IFREG | mode) << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    return info


def zip_names(path: Path) -> tuple[str, ...]:
    with zipfile.ZipFile(path) as archive:
        return tuple(archive.namelist())


def hashes(paths: Iterable[Path]) -> dict[str, str]:
    return {
        Path(path).name: hashlib.sha256(Path(path).read_bytes()).hexdigest()
        for path in paths
    }


def write_checksums(archives: Iterable[Path], output: Path) -> Path:
    output = Path(output)
    digest_by_name = hashes(archives)
    lines = [f"{digest_by_name[name]}  {name}" for name in sorted(digest_by_name)]
    output.write_text("\n".join(lines) + "\n", encoding="ascii")
    return output


def archive_filenames(version: str) -> tuple[str, ...]:
    return (
        f"{PLUGIN_NAME}-v{version}.zip",
        f"korean-writing-editor-v{version}.zip",
        f"image-workbench-v{version}.zip",
        f"graspic-v{version}.zip",
    )


def build_archives(root: Path, output: Path, version: str) -> tuple[Path, ...]:
    root = Path(root)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    plugin_members = _tracked_files(root, PLUGIN_TRACKED)
    _assert_plugin_version(plugin_members, version)
    plugin_zip = output / f"{PLUGIN_NAME}-v{version}.zip"
    _write_zip(
        plugin_zip,
        [
            (relative, data, _is_executable(mode, data))
            for relative, mode, data in plugin_members
        ],
    )
    archives = [plugin_zip]
    for skill in SKILLS:
        tracked = _tracked_files(root, (f"skills/{skill}/",))
        members = [
            (relative.removeprefix("skills/"), data, _is_executable(mode, data))
            for relative, mode, data in tracked
        ]
        skill_zip = output / f"{skill}-v{version}.zip"
        _write_zip(skill_zip, members)
        archives.append(skill_zip)
    return tuple(archives)


def verify_archive(path: Path) -> list[str]:
    path = Path(path)
    errors: list[str] = []
    kind = _archive_kind(path.name)
    if kind is None:
        return [f"unexpected archive: {path.name}"]
    try:
        archive = zipfile.ZipFile(path)
    except zipfile.BadZipFile as exc:
        return [f"invalid zip: {exc}"]
    with archive:
        names = archive.namelist()
        infos = archive.infolist()
    seen: set[str] = set()
    folded: dict[str, str] = {}
    for info, name in zip(infos, names):
        member_errors = _member_safety_errors(name, seen, folded)
        errors.extend(member_errors)
        errors.extend(_member_mode_errors(name, info))
        if member_errors:
            continue
        if not _member_allowed(kind, name):
            errors.append(f"unexpected member: {name}")
    for required in _required_members(kind):
        if required not in seen:
            errors.append(f"missing required member: {required}")
    return errors


def verify_download(directory: Path, version: str) -> list[str]:
    directory = Path(directory)
    checksums_path = directory / "SHA256SUMS"
    if not checksums_path.is_file():
        return ["missing SHA256SUMS"]
    expected = set(archive_filenames(version))
    errors: list[str] = []
    parsed = _parse_checksums(checksums_path, errors)
    if errors:
        return errors
    if set(parsed) != expected:
        errors.append("SHA256SUMS must list exactly the release zips")
        return errors
    if list(parsed) != sorted(parsed):
        errors.append("SHA256SUMS is not sorted")
    extra_zips = sorted(
        path.name
        for path in directory.iterdir()
        if path.is_file() and path.suffix == ".zip" and path.name not in expected
    )
    if extra_zips:
        errors.append("unexpected zip in download directory: " + ", ".join(extra_zips))
    archives: list[Path] = []
    for name in archive_filenames(version):
        archive = directory / name
        if not archive.is_file():
            errors.append(f"missing archive: {name}")
            continue
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        if digest != parsed[name]:
            errors.append(f"checksum mismatch: {name}")
        archives.append(archive)
    if errors:
        return errors
    return smoke_archives(archives)


def smoke_archives(archives: Iterable[Path]) -> list[str]:
    errors: list[str] = []
    for archive in archives:
        archive = Path(archive)
        member_errors = verify_archive(archive)
        if member_errors:
            errors.extend(member_errors)
            continue
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp)
            extract_errors = extract_archive(archive, destination)
            if extract_errors:
                errors.extend(extract_errors)
                continue
            errors.extend(_smoke_extracted(archive.name, destination))
    return errors


def extract_archive(path: Path, destination: Path) -> list[str]:
    errors = verify_archive(path)
    if errors:
        return errors
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    root = destination.resolve()
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            target = (destination / name).resolve()
            if not target.is_relative_to(root):
                return [f"extract escapes destination: {name}"]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(name))
    return []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--verify-download", type=Path)
    args = parser.parse_args(argv)
    if args.verify_download is not None and args.output is not None:
        parser.error("--output and --verify-download are mutually exclusive")
    if args.verify_download is not None:
        errors = verify_download(args.verify_download, args.version)
        for error in errors:
            print(error, file=sys.stderr)
        return 0 if not errors else 1
    if args.output is None:
        parser.error("one of --output or --verify-download is required")
    try:
        archives = build_archives(ROOT, args.output, args.version)
    except ReleaseError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    errors = smoke_archives(archives)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    checksums = write_checksums(archives, Path(args.output) / "SHA256SUMS")
    for archive in archives:
        print(archive)
    print(checksums)
    return 0


def _tracked_files(root: Path, prefixes: tuple[str, ...]) -> list[tuple[str, str, bytes]]:
    output = _git(root, "ls-files", "-s", "-z", "--", *prefixes)
    entries: list[tuple[str, str, bytes]] = []
    seen: set[str] = set()
    for record in _nul_items(output):
        mode, blob_oid, remainder = record.split(" ", 2)
        _stage, relative = remainder.split("\t", 1)
        relative = _posix(relative)
        if relative in seen:
            raise ReleaseError(f"duplicate tracked path: {relative}")
        seen.add(relative)
        _reject_source_name(relative)
        if mode not in REGULAR_FILE_MODES:
            raise ReleaseError(f"symlink or special file: {relative}")
        data = _git_bytes(root, "cat-file", "blob", blob_oid)
        entries.append((relative, mode, data))
    if not entries:
        raise ReleaseError("no tracked payload files")
    entries.sort(key=lambda item: item[0])
    return entries


def _assert_plugin_version(members: list[tuple[str, str, bytes]], version: str) -> None:
    for relative, _mode, data in members:
        if relative == ".codex-plugin/plugin.json":
            payload = json.loads(data.decode("utf-8"))
            if payload.get("version") != version:
                raise ReleaseError(
                    f"plugin version {payload.get('version')!r} != {version!r}"
                )
            return
    raise ReleaseError("missing .codex-plugin/plugin.json")


def _is_executable(mode: str, data: bytes) -> bool:
    return mode == "100755" or data.startswith(b"#!")


def _write_zip(path: Path, members: list[tuple[str, bytes, bool]]) -> None:
    ordered = sorted(members, key=lambda item: item[0])
    names = [name for name, _data, _executable in ordered]
    if len(names) != len(set(names)):
        raise ReleaseError("duplicate zip member")
    folded: dict[str, str] = {}
    for name in names:
        _reject_source_name(name)
        key = name.casefold()
        if key in folded:
            raise ReleaseError(f"case-fold collision: {name}")
        folded[key] = name
    with zipfile.ZipFile(
        path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        allowZip64=False,
    ) as archive:
        for name, data, executable in ordered:
            archive.writestr(zip_info(name, executable), data)


def _archive_kind(name: str) -> str | None:
    if re.fullmatch(r"beyondwin-skills-v.+\.zip", name):
        return "plugin"
    if re.fullmatch(r"korean-writing-editor-v.+\.zip", name):
        return "korean-writing-editor"
    if re.fullmatch(r"image-workbench-v.+\.zip", name):
        return "image-workbench"
    if re.fullmatch(r"graspic-v.+\.zip", name):
        return "graspic"
    return None


def _required_members(kind: str) -> tuple[str, ...]:
    if kind == "plugin":
        return (
            ".codex-plugin/plugin.json",
            "LICENSE",
            "NOTICE",
            "skills/korean-writing-editor/SKILL.md",
            "skills/korean-writing-editor/LICENSE.txt",
            "skills/image-workbench/SKILL.md",
            "skills/image-workbench/LICENSE.txt",
            "skills/image-workbench/scripts/inspect_asset.py",
            "skills/graspic/SKILL.md",
            "skills/graspic/LICENSE.txt",
        )
    return (f"{kind}/SKILL.md", f"{kind}/LICENSE.txt")


def _member_allowed(kind: str, name: str) -> bool:
    parts = pathlib.PurePosixPath(name).parts
    if any(part in FORBIDDEN_PARTS for part in parts):
        return False
    if pathlib.PurePosixPath(name).name in FORBIDDEN_NAMES:
        return False
    if kind == "plugin":
        return name in {".codex-plugin/plugin.json", "LICENSE", "NOTICE"} or name.startswith(
            ("skills/korean-writing-editor/", "skills/image-workbench/", "skills/graspic/")
        )
    return name.startswith(f"{kind}/")


def _member_safety_errors(
    name: str,
    seen: set[str],
    folded: dict[str, str],
) -> list[str]:
    errors: list[str] = []
    if not name or name.endswith("/") or "\\" in name or "\x00" in name:
        errors.append(f"unexpected member: {name}")
        return errors
    if _is_absolute_member(name):
        errors.append(f"absolute path: {name}")
        return errors
    parts = name.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        if ".." in parts:
            errors.append(f"parent path segment: {name}")
        else:
            errors.append(f"unexpected member: {name}")
        return errors
    if name in seen:
        errors.append(f"duplicate member: {name}")
        return errors
    seen.add(name)
    key = name.casefold()
    if key in folded:
        errors.append(f"case-fold collision: {name}")
        return errors
    folded[key] = name
    return errors


def _member_mode_errors(name: str, info: zipfile.ZipInfo) -> list[str]:
    mode = (info.external_attr >> 16) & 0o170000
    if mode == stat.S_IFLNK:
        return [f"symlink member: {name}"]
    if mode and mode not in {stat.S_IFREG, stat.S_IFDIR}:
        return [f"special file member: {name}"]
    return []


def _is_absolute_member(name: str) -> bool:
    if name.startswith("/") or name.startswith("\\"):
        return True
    if pathlib.PurePosixPath(name).is_absolute():
        return True
    if pathlib.PureWindowsPath(name).is_absolute():
        return True
    return False


def _reject_source_name(name: str) -> None:
    errors = _member_safety_errors(name, set(), {})
    if errors:
        raise ReleaseError(errors[0])
    parts = pathlib.PurePosixPath(name).parts
    if any(part in FORBIDDEN_PARTS for part in parts):
        raise ReleaseError(f"unexpected member: {name}")
    if pathlib.PurePosixPath(name).name in FORBIDDEN_NAMES:
        raise ReleaseError(f"unexpected member: {name}")


def _parse_checksums(path: Path, errors: list[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    text = path.read_text(encoding="ascii")
    for raw in text.splitlines():
        if not raw.strip():
            continue
        if "  " not in raw:
            errors.append(f"malformed SHA256SUMS line: {raw}")
            continue
        digest, name = raw.split("  ", 1)
        if "/" in name or "\\" in name or name != Path(name).name:
            errors.append(f"SHA256SUMS name must be a basename: {name}")
            continue
        if not DIGEST_RE.fullmatch(digest):
            errors.append(f"malformed digest: {digest}")
            continue
        if name in parsed:
            errors.append(f"duplicate SHA256SUMS name: {name}")
            continue
        parsed[name] = digest
    return parsed


def _smoke_extracted(archive_name: str, extracted: Path) -> list[str]:
    kind = _archive_kind(archive_name)
    if kind == "plugin":
        skills_root = extracted / "skills"
        errors: list[str] = []
        for skill in SKILLS:
            errors.extend(_validate_extracted_skill(skills_root / skill))
        errors.extend(_run_korean(skills_root / "korean-writing-editor"))
        errors.extend(_run_image(skills_root / "image-workbench"))
        errors.extend(
            _run_inspector(
                skills_root / "image-workbench" / "scripts" / "inspect_asset.py"
            )
        )
        return errors
    if kind == "korean-writing-editor":
        skill = extracted / "korean-writing-editor"
        return [*_validate_extracted_skill(skill), *_run_korean(skill)]
    if kind == "image-workbench":
        skill = extracted / "image-workbench"
        return [
            *_validate_extracted_skill(skill),
            *_run_image(skill),
            *_run_inspector(skill / "scripts" / "inspect_asset.py"),
        ]
    if kind == "graspic":
        skill = extracted / "graspic"
        return _validate_extracted_skill(skill)
    return [f"unexpected archive: {archive_name}"]


def _validate_extracted_skill(skill_root: Path) -> list[str]:
    if not skill_root.is_dir():
        return [f"missing extracted skill: {skill_root.name}"]
    validator = _load_skill_validator()
    return [f"{skill_root.name}: {error}" for error in validator.validate_skill(skill_root)]


def _load_skill_validator() -> ModuleType:
    name = "beyondwin_release_skill_validator"
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    path = ROOT / "tests" / "contract" / "test_repository.py"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ReleaseError(f"unable to load skill validator: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _run_korean(skill_root: Path) -> list[str]:
    return _run_command(
        "korean-offline",
        [
            sys.executable,
            str(ROOT / "tests" / "korean-writing-editor" / "offline" / "run.py"),
            "--scope",
            "full",
            "--skill-root",
            str(skill_root),
        ],
    )


def _run_image(skill_root: Path) -> list[str]:
    return _run_command(
        "image-contract",
        [
            sys.executable,
            str(ROOT / "tests" / "image-workbench" / "run.py"),
            "--scope",
            "full",
            "--skill-root",
            str(skill_root),
        ],
    )


def _run_inspector(inspector: Path) -> list[str]:
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
            str(ROOT / "tests" / "image-workbench"),
            "-p",
            "test_*.py",
        ],
        env=env,
    )


def _run_command(
    stage: str,
    argv: list[str],
    env: dict[str, str] | None = None,
) -> list[str]:
    completed = subprocess.run(
        argv,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    if completed.returncode == 0:
        return []
    detail = (completed.stderr or completed.stdout).strip()
    return [f"{stage} failed ({completed.returncode}): {detail}"]


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
