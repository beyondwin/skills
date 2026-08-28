from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Iterable


DEFAULT_PREFIXES = (
    "skills/korean-writing-editor/",
    "skills/image-workbench/",
)
DEFAULT_IDENTIFIERS = (
    "korean-writing-editor",
    "image-workbench",
    "kws-korean-writing-editor",
    "kws-image-workbench",
)
HIT_CLASSES = (
    "source",
    "active-routing",
    "verification-registration",
    "skill-history-document",
    "mixed-document",
    "generated-residue",
)
ACTIVE_ROUTING_PATHS = frozenset({
    "skills/AGENTS.md",
    "skills/README.md",
})
REGULAR_FILE_MODES = frozenset({"100644", "100755"})
WORKTREE_ROOT = ".superpowers/worktrees/"


class CaptureError(RuntimeError):
    """Raised when Archive capture or verification cannot proceed."""


def git(repository: Path, *arguments: str, ok_returncodes: tuple[int, ...] = (0,)) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode not in ok_returncodes:
        detail = (completed.stderr or completed.stdout).strip()
        joined = " ".join(arguments)
        raise CaptureError(detail or f"git {joined} failed ({completed.returncode})")
    return completed.stdout.rstrip("\n")


def remote_url(repository: Path) -> str:
    value = git(repository, "config", "--get", "remote.origin.url")
    if not value:
        raise CaptureError("missing remote.origin.url")
    return value


def canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode()


def source_entries(repository: Path, prefixes: tuple[str, ...]) -> list[dict[str, object]]:
    output = git(repository, "ls-files", "-s", "-z", "--", *prefixes)
    entries: list[dict[str, object]] = []
    seen: set[str] = set()
    for record in _nul_items(output):
        mode, blob_oid, remainder = record.split(" ", 2)
        _stage, relative = remainder.split("\t", 1)
        relative = _posix(relative)
        if relative in seen:
            raise CaptureError("duplicate paths")
        seen.add(relative)
        if mode not in REGULAR_FILE_MODES:
            raise CaptureError("symlink or special file in selected prefixes")
        file_location = repository / relative
        if file_location.is_symlink() or not file_location.is_file():
            raise CaptureError("symlink or special file in selected prefixes")
        data = file_location.read_bytes()
        entries.append({
            "path": relative,
            "mode": mode,
            "blob_oid": blob_oid,
            "size": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        })
    entries.sort(key=lambda item: str(item["path"]))
    return entries


def identifier_hits(
    repository: Path,
    identifiers: tuple[str, ...],
    prefixes: tuple[str, ...] = (),
) -> list[dict[str, str]]:
    tracked = set(_nul_items(git(repository, "ls-files", "-z")))
    found: set[str] = set()
    if identifiers:
        found.update(_content_hit_paths(repository, identifiers))
        for relative in _listed_names(repository):
            if _mentions_identifier(relative, identifiers):
                found.add(_collapse_worktree(_posix(relative)))
    hits: list[dict[str, str]] = []
    for relative in sorted(found):
        if relative == ".git" or relative.startswith(".git/"):
            continue
        collapsed = _collapse_worktree(relative)
        classification = classify_hit(collapsed, prefixes, tracked)
        if classification not in HIT_CLASSES:
            raise CaptureError(f"unclassified identifier hit: {collapsed}")
        hits.append({"path": collapsed, "class": classification})
    return _unique_hits(hits)


def classify_hit(relative: str, prefixes: tuple[str, ...], tracked: set[str]) -> str:
    posix = _posix(relative).rstrip("/")
    if posix not in tracked:
        return "generated-residue"
    if _under_prefixes(posix, prefixes):
        return "source"
    if posix in ACTIVE_ROUTING_PATHS:
        return "active-routing"
    if posix.startswith("scripts/agent/"):
        return "verification-registration"
    if posix.startswith("docs/history/") or posix.startswith("docs/operations/"):
        return "skill-history-document"
    return "mixed-document"


def build_manifest(
    repository: Path,
    prefixes: tuple[str, ...],
    identifiers: tuple[str, ...],
) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": 1,
        "source_repository": remote_url(repository),
        "source_commit": git(repository, "rev-parse", "HEAD"),
        "prefixes": list(prefixes),
        "identifiers": list(identifiers),
        "entries": source_entries(repository, prefixes),
        "identifier_hits": identifier_hits(repository, identifiers, prefixes),
    }
    payload["manifest_sha256"] = hashlib.sha256(canonical_bytes(payload)).hexdigest()
    return payload


def verify_manifest(repository: Path, manifest: dict[str, object]) -> list[str]:
    problems: list[str] = []
    recorded_digest = manifest.get("manifest_sha256")
    payload = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    actual_digest = hashlib.sha256(canonical_bytes(payload)).hexdigest()
    if recorded_digest != actual_digest:
        problems.append("manifest digest mismatch")
    prefixes = tuple(str(item) for item in manifest.get("prefixes", []))
    try:
        current_entries = source_entries(repository, prefixes)
    except CaptureError as exc:
        problems.append(str(exc))
        return problems
    current_commit = git(repository, "rev-parse", "HEAD")
    current_remote = remote_url(repository)
    if (
        current_entries != manifest.get("entries")
        or current_commit != manifest.get("source_commit")
        or current_remote != manifest.get("source_repository")
    ):
        problems.append("source tree differs from manifest")
    return problems


def source_problems(repository: Path) -> list[str]:
    problems: list[str] = []
    porcelain = git(repository, "status", "--porcelain", "--untracked-files=all")
    if porcelain:
        problems.append("dirty source")
    detached = git(repository, "symbolic-ref", "-q", "HEAD", ok_returncodes=(0, 1))
    if not detached:
        problems.append("detached source")
    head = git(repository, "rev-parse", "HEAD")
    try:
        origin_main = git(repository, "rev-parse", "origin/main")
    except CaptureError:
        problems.append("HEAD differs from origin/main")
    else:
        if head != origin_main:
            problems.append("HEAD differs from origin/main")
    return problems


def _content_hit_paths(repository: Path, identifiers: tuple[str, ...]) -> set[str]:
    grep_arguments = [
        "grep",
        "-I",
        "-l",
        "-F",
        "-z",
        "--untracked",
        "--no-exclude-standard",
    ]
    for identifier in identifiers:
        grep_arguments.extend(["-e", identifier])
    grep_arguments.extend([
        "--",
        ".",
        ":(exclude).git",
        ":(exclude).git/**",
        f":(exclude){WORKTREE_ROOT}",
        f":(exclude){WORKTREE_ROOT}**",
    ])
    return {
        _collapse_worktree(_posix(item))
        for item in _nul_items(git(repository, *grep_arguments, ok_returncodes=(0, 1)))
    }


def _listed_names(repository: Path) -> Iterable[str]:
    tracked = _nul_items(git(repository, "ls-files", "-z"))
    untracked = _nul_items(git(repository, "ls-files", "-o", "--exclude-standard", "-z"))
    ignored = _nul_items(
        git(repository, "ls-files", "-o", "-i", "--exclude-standard", "-z")
    )
    yield from tracked
    yield from untracked
    yield from ignored


def _under_prefixes(relative: str, prefixes: tuple[str, ...]) -> bool:
    for prefix in prefixes:
        normalized = prefix if prefix.endswith("/") else f"{prefix}/"
        if relative == prefix.rstrip("/") or relative.startswith(normalized):
            return True
    return False


def _mentions_identifier(relative: str, identifiers: tuple[str, ...]) -> bool:
    return any(identifier in relative for identifier in identifiers)


def _collapse_worktree(relative: str) -> str:
    posix = _posix(relative).rstrip("/")
    if posix.startswith(WORKTREE_ROOT):
        name = posix[len(WORKTREE_ROOT):].split("/", 1)[0]
        if name:
            return WORKTREE_ROOT + name
    return posix


def _unique_hits(hits: list[dict[str, str]]) -> list[dict[str, str]]:
    unique: list[dict[str, str]] = []
    seen: set[str] = set()
    for hit in hits:
        key = hit["path"]
        if key in seen:
            continue
        seen.add(key)
        unique.append(hit)
    return unique


def _nul_items(payload: str) -> list[str]:
    return [item for item in payload.split("\0") if item]


def _posix(relative: str) -> str:
    return relative.replace("\\", "/")
