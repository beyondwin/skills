"""Tracked-file identifier scan with an explicit history and changelog allowlist."""

from __future__ import annotations

import dataclasses
import pathlib
import subprocess


@dataclasses.dataclass(frozen=True)
class IdentifierHit:
    path: str
    location: str  # "path" or "content"


def tracked_identifier_hits(
    root: pathlib.Path,
    identifier: str,
    *,
    allowed_prefixes: tuple[str, ...] = ("docs/history/",),
    allowed_files: frozenset[str] = frozenset({"skills/how-it-works/CHANGELOG.md"}),
) -> tuple[IdentifierHit, ...]:
    root = pathlib.Path(root)
    tracked = tuple(_normalize(path) for path in _git_ls_files(root))
    tracked_set = set(tracked)
    prefixes = tuple(_normalize_prefix(prefix) for prefix in allowed_prefixes)
    allow_files = frozenset(_normalize(path) for path in allowed_files)
    missing = sorted(path for path in allow_files if path not in tracked_set)
    if missing:
        raise ValueError(f"allowlisted path is not tracked: {missing[0]}")
    hits: dict[tuple[str, str], IdentifierHit] = {}
    for relative in tracked:
        if _is_allowed(relative, prefixes, allow_files):
            continue
        if identifier in relative:
            hits[relative, "path"] = IdentifierHit(relative, "path")
        if _content_mentions(root / relative, identifier):
            hits[relative, "content"] = IdentifierHit(relative, "content")
    return tuple(hits[key] for key in sorted(hits))


def _git_ls_files(root: pathlib.Path) -> tuple[str, ...]:
    completed = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise ValueError(detail or f"git ls-files failed in {root}")
    return tuple(item for item in completed.stdout.split("\0") if item)


def _content_mentions(path: pathlib.Path, identifier: str) -> bool:
    if path.is_symlink() or not path.is_file():
        return False
    try:
        data = path.read_bytes()
    except OSError:
        return False
    if b"\0" in data:
        return False
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return identifier in text


def _is_allowed(
    relative: str,
    prefixes: tuple[str, ...],
    allowed_files: frozenset[str],
) -> bool:
    if relative in allowed_files:
        return True
    return any(
        relative == prefix.rstrip("/") or relative.startswith(prefix)
        for prefix in prefixes
    )


def _normalize(relative: str) -> str:
    normalized = str(relative).replace("\\", "/").lstrip("./")
    while "//" in normalized:
        normalized = normalized.replace("//", "/")
    if normalized in {"", "."}:
        return ""
    return pathlib.PurePosixPath(normalized).as_posix()


def _normalize_prefix(prefix: str) -> str:
    normalized = _normalize(prefix)
    if not normalized:
        return ""
    return normalized if normalized.endswith("/") else f"{normalized}/"
