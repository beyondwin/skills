"""Markdown link checks and registry-derived active documentation paths."""

from __future__ import annotations

import collections.abc
import pathlib
import re

from scripts.lib.product_registry import load_registry


_LINK_RE = re.compile(r"\[[^\]]*\]\(\s*(?:<([^>]+)>|([^)\s]+))")
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
_SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")
_PRODUCT_README_NAMES = ("README.md", "README.en.md")
_USER_LANGUAGES = ("ko", "en")


def active_markdown_paths(root: pathlib.Path) -> tuple[pathlib.Path, ...]:
    root = pathlib.Path(root)
    registry = load_registry(root / "products.toml")
    candidates: list[pathlib.Path] = [
        root / "README.md",
        root / "README.en.md",
        root / "docs" / "README.md",
        root / "docs" / "maintainers" / "README.md",
        root / "docs" / "history" / "README.md",
        root / "catalog" / "README.md",
        root / "catalog" / "CHANGELOG.md",
    ]
    for product in registry.products:
        for name in _PRODUCT_README_NAMES:
            candidates.append(root / product.skill_path / name)
        docs_root = root / product.maintainer_docs
        if docs_root.is_dir():
            candidates.extend(docs_root.glob("*.md"))
    for language in _USER_LANGUAGES:
        users = root / "docs" / "users" / language
        if users.is_dir():
            candidates.extend(users.glob("*.md"))
    repository_docs = root / "docs" / "maintainers" / "repository"
    if repository_docs.is_dir():
        candidates.extend(repository_docs.glob("*.md"))
    unique: dict[pathlib.Path, pathlib.Path] = {}
    for path in candidates:
        if path.is_file():
            unique[path.resolve()] = path
    root_resolved = root.resolve()
    return tuple(
        sorted(
            unique.values(),
            key=lambda path: path.resolve().relative_to(root_resolved).as_posix(),
        )
    )


def markdown_links(path: pathlib.Path) -> tuple[str, ...]:
    text = pathlib.Path(path).read_text(encoding="utf-8")
    links: list[str] = []
    for angle, plain in _LINK_RE.findall(text):
        href = (angle or plain).strip()
        if href:
            links.append(href)
    return tuple(links)


def broken_markdown_links(
    root: pathlib.Path,
    paths: collections.abc.Iterable[pathlib.Path],
) -> list[str]:
    root = pathlib.Path(root)
    errors: list[str] = []
    for raw in paths:
        document = pathlib.Path(raw)
        if not document.is_absolute():
            document = root / document
        relative = _repo_relative(root, document)
        if not document.is_file():
            errors.append(f"missing markdown file: {relative}")
            continue
        for href in markdown_links(document):
            error = _link_error(root, document, relative, href)
            if error:
                errors.append(error)
    return sorted(errors)


def _link_error(
    root: pathlib.Path,
    document: pathlib.Path,
    relative: str,
    href: str,
) -> str | None:
    if _SCHEME_RE.match(href):
        return None
    path_part, fragment = _split_href(href)
    if not path_part:
        return None
    resolved = (document.parent / path_part).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        return f"link escapes repository in {relative}: {href}"
    if not resolved.exists():
        return f"broken relative link in {relative}: {href}"
    if not fragment:
        return None
    ids = (
        _heading_ids(resolved.read_text(encoding="utf-8"))
        if resolved.is_file()
        else set()
    )
    if fragment not in ids:
        return f"missing anchor in {relative}: {href}"
    return None


def _split_href(href: str) -> tuple[str, str]:
    path_part, _, fragment = href.partition("#")
    return path_part.split("?", 1)[0], fragment


def _heading_ids(text: str) -> set[str]:
    seen: dict[str, int] = {}
    ids: set[str] = set()
    for match in _HEADING_RE.finditer(text):
        heading = match.group(2).replace("`", "")
        slug = heading.strip().lower()
        slug = re.sub(r"[^\w\s-]", "", slug, flags=re.UNICODE)
        slug = re.sub(r"\s+", "-", slug)
        count = seen.get(slug, 0)
        seen[slug] = count + 1
        ids.add(slug if count == 0 else f"{slug}-{count}")
    return ids


def _repo_relative(root: pathlib.Path, path: pathlib.Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return pathlib.Path(path).as_posix()
