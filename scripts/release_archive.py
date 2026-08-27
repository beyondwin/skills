"""Deterministic ZIP, checksum, extraction, and archive-safety primitives."""

from __future__ import annotations

import dataclasses
import hashlib
import pathlib
import re
import stat
import zipfile
from collections.abc import Iterable, Sequence
from pathlib import Path


ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
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
FORBIDDEN_NAMES = frozenset({"CHANGE_PROTOCOL.md"})


class ReleaseError(RuntimeError):
    """Raised when a release archive cannot be built."""


@dataclasses.dataclass(frozen=True)
class ArchiveMember:
    name: str
    data: bytes
    executable: bool


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


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def hashes(paths: Iterable[Path]) -> dict[str, str]:
    return {Path(path).name: sha256_file(path) for path in paths}


def write_checksums(archives: Iterable[Path], output: Path) -> Path:
    output = Path(output)
    digest_by_name = hashes(archives)
    lines = [f"{digest_by_name[name]}  {name}" for name in sorted(digest_by_name)]
    output.write_text("\n".join(lines) + "\n", encoding="ascii")
    return output


def ensure_new_empty_directory(path: Path) -> Path:
    path = Path(path)
    if path.exists():
        if not path.is_dir():
            raise ReleaseError(f"output is not a directory: {path}")
        if any(path.iterdir()):
            raise ReleaseError(f"output directory is not empty: {path}")
        return path
    path.mkdir(parents=True)
    return path


def write_zip(path: Path, members: Sequence[ArchiveMember]) -> Path:
    path = Path(path)
    ordered = sorted(members, key=lambda item: item.name)
    names = [item.name for item in ordered]
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
        for member in ordered:
            archive.writestr(zip_info(member.name, member.executable), member.data)
    return path


def verify_product_archive(path: Path, product_name: str) -> list[str]:
    path = Path(path)
    try:
        archive = zipfile.ZipFile(path)
    except zipfile.BadZipFile as exc:
        return [f"invalid zip: {exc}"]
    errors: list[str] = []
    seen: set[str] = set()
    folded: dict[str, str] = {}
    prefix = f"{product_name}/"
    with archive:
        for info in archive.infolist():
            name = info.filename
            member_errors = _member_safety_errors(name, seen, folded)
            errors.extend(member_errors)
            errors.extend(_member_mode_errors(name, info))
            if member_errors:
                continue
            if name.endswith("/"):
                if name != prefix and not name.startswith(prefix):
                    errors.append(f"unexpected member: {name}")
                continue
            if not name.startswith(prefix) or name == prefix:
                errors.append(f"unexpected member: {name}")
                continue
            relative = name[len(prefix) :]
            parts = pathlib.PurePosixPath(relative).parts
            if any(part in FORBIDDEN_PARTS for part in parts):
                errors.append(f"unexpected member: {name}")
            if pathlib.PurePosixPath(name).name in FORBIDDEN_NAMES:
                errors.append(f"unexpected member: {name}")
    for required in (f"{product_name}/SKILL.md", f"{product_name}/LICENSE.txt"):
        if required not in seen:
            errors.append(f"missing required member: {required}")
    return errors


def extract_archive(path: Path, destination: Path) -> list[str]:
    path = Path(path)
    try:
        archive = zipfile.ZipFile(path)
    except zipfile.BadZipFile as exc:
        return [f"invalid zip: {exc}"]
    errors: list[str] = []
    seen: set[str] = set()
    folded: dict[str, str] = {}
    with archive:
        infos = list(archive.infolist())
        for info in infos:
            name = info.filename
            errors.extend(_member_safety_errors(name, seen, folded))
            errors.extend(_member_mode_errors(name, info))
        if errors:
            return errors
        destination = Path(destination)
        destination.mkdir(parents=True, exist_ok=True)
        root = destination.resolve()
        for info in infos:
            name = info.filename
            if name.endswith("/"):
                continue
            target = (destination / name).resolve()
            if not target.is_relative_to(root):
                return [f"extract escapes destination: {name}"]
            target.parent.mkdir(parents=True, exist_ok=True)
            data = archive.read(info)
            target.write_bytes(data)
            unix_mode = (info.external_attr >> 16) & 0o777
            if unix_mode & 0o111 or data.startswith(b"#!"):
                target.chmod(0o755)
    return []


def _member_safety_errors(
    name: str,
    seen: set[str],
    folded: dict[str, str],
) -> list[str]:
    errors: list[str] = []
    if not name or "\\" in name or "\x00" in name:
        errors.append(f"unexpected member: {name}")
        return errors
    if _is_absolute_member(name):
        errors.append(f"absolute path: {name}")
        return errors
    raw_parts = name.split("/")
    if name.endswith("/"):
        raw_parts = raw_parts[:-1]
    if any(part in {"", ".", ".."} for part in raw_parts):
        if ".." in raw_parts:
            errors.append(f"parent path segment: {name}")
        elif "." in raw_parts:
            errors.append(f"dot path segment: {name}")
        else:
            errors.append(f"empty path segment: {name}")
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


def _reject_source_name(name: str) -> None:
    errors = _member_safety_errors(name, set(), {})
    if errors:
        raise ReleaseError(errors[0])
    parts = pathlib.PurePosixPath(name).parts
    if any(part in FORBIDDEN_PARTS for part in parts):
        raise ReleaseError(f"unexpected member: {name}")
    if pathlib.PurePosixPath(name).name in FORBIDDEN_NAMES:
        raise ReleaseError(f"unexpected member: {name}")
