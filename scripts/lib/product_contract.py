from __future__ import annotations

import dataclasses
import hashlib
import json
import re
import shutil
import stat
import tomllib
from pathlib import Path

from scripts.lib.product_registry import ProductRegistry


SEMVER_RE = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
ALLOWED_TOP_LEVEL = frozenset({
    "SKILL.md",
    "README.md",
    "README.en.md",
    "CHANGELOG.md",
    "release.toml",
    "LICENSE.txt",
    "agents",
    "references",
    "scripts",
})
FORBIDDEN_PAYLOAD_NAMES = frozenset({"CHANGE_PROTOCOL.md", "evals", "tests"})
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---(?:\n|\Z)", re.DOTALL)
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
UNRELEASED_RE = re.compile(r"^## Unreleased\s*$", re.MULTILINE)
HOME_PREFIX = "/Users/"
ARCHIVE_MARKERS = ("SKILLS_ARCHIVE_CHECKOUT", "source/private")
CREDENTIAL_MARKERS = ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "CURSOR_API_KEY")
LEGACY_IDENTIFIERS = (
    "kws-korean-writing-editor",
    "kws-image-workbench",
)
IGNORE_NAMES = frozenset({"__pycache__"})
BYTECODE_SUFFIXES = {".pyc", ".pyo"}


@dataclasses.dataclass(frozen=True)
class ProductRelease:
    root: Path
    name: str
    version: str
    tag_prefix: str
    license: str

    @property
    def tag(self) -> str:
        return f"{self.tag_prefix}{self.version}"

    @property
    def artifact_name(self) -> str:
        return f"{self.name}-v{self.version}.zip"


def load_product_release(skill_root: Path) -> ProductRelease:
    skill_root = Path(skill_root)
    data = tomllib.loads((skill_root / "release.toml").read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("release.toml schema_version must be 1")
    return ProductRelease(
        root=skill_root,
        name=str(data["name"]),
        version=str(data["version"]),
        tag_prefix=str(data["tag_prefix"]),
        license=str(data["license"]),
    )


def payload_sha256(skill_root: Path) -> str:
    encoded = (
        json.dumps(
            payload_entries(skill_root),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def payload_entries(skill_root: Path) -> list[dict[str, object]]:
    skill_root = Path(skill_root)
    entries: list[dict[str, object]] = []
    for path in _iter_payload_paths(skill_root):
        relative = path.relative_to(skill_root).as_posix()
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode):
            raise ValueError(f"symlink is not allowed: {relative}")
        if stat.S_ISDIR(info.st_mode):
            continue
        if not stat.S_ISREG(info.st_mode):
            raise ValueError(f"special file is not allowed: {relative}")
        data = path.read_bytes()
        entries.append(
            {
                "path": relative,
                "mode": _normalized_mode(info.st_mode, data),
                "size": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    entries.sort(key=lambda item: str(item["path"]))
    return entries


def parse_skill_frontmatter(text: str) -> dict[str, object]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    data: dict[str, object] = {}
    metadata: dict[str, str] = {}
    in_metadata = False
    for raw_line in match.group(1).splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue
        if line == "metadata:":
            in_metadata = True
            continue
        if in_metadata and line.startswith("  ") and ":" in line:
            key, value = line.strip().split(":", 1)
            metadata[key.strip()] = value.strip().strip("\"'")
            continue
        in_metadata = False
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip("\"'")
    if metadata:
        data["metadata"] = metadata
    return data


def require_dated_changelog(skill_root: Path) -> list[str]:
    skill_root = Path(skill_root)
    try:
        release = load_product_release(skill_root)
    except (OSError, ValueError, tomllib.TOMLDecodeError, KeyError) as exc:
        return [f"release.toml: {exc}"]
    path = skill_root / "CHANGELOG.md"
    if not path.is_file():
        return ["missing CHANGELOG.md"]
    text = path.read_text(encoding="utf-8")
    pattern = rf"^## {re.escape(release.version)} - \d{{4}}-\d{{2}}-\d{{2}}$"
    if re.search(pattern, text, re.MULTILINE) is None:
        return [f"CHANGELOG.md missing dated release heading for {release.version}"]
    return []


def validate_product(skill_root: Path, registry: ProductRegistry) -> list[str]:
    errors: list[str] = []
    skill_root = Path(skill_root)
    if skill_root.name not in registry.names:
        errors.append(f"unlisted skill is not accepted: {skill_root.name}")
        return errors

    skill_md = skill_root / "SKILL.md"
    if not skill_md.is_file():
        errors.append("missing SKILL.md")
        return errors

    skill_text = skill_md.read_text(encoding="utf-8")
    frontmatter = parse_skill_frontmatter(skill_text)
    if frontmatter.get("name") != skill_root.name:
        errors.append("directory/frontmatter name mismatch")
    if frontmatter.get("license") != "Apache-2.0":
        errors.append("missing Apache declaration")
    metadata = frontmatter.get("metadata")
    skill_version = metadata.get("version") if isinstance(metadata, dict) else None

    release: ProductRelease | None = None
    release_path = skill_root / "release.toml"
    if not release_path.is_file():
        errors.append("missing release.toml")
    else:
        try:
            release = load_product_release(skill_root)
        except ValueError as exc:
            errors.append(str(exc))
        except (tomllib.TOMLDecodeError, KeyError, OSError) as exc:
            errors.append(f"invalid release.toml: {exc}")
        else:
            if release.name != skill_root.name:
                errors.append("directory/release.toml name mismatch")
            if not SEMVER_RE.fullmatch(release.version):
                errors.append(f"invalid SemVer: {release.version}")
            if release.tag_prefix != f"{skill_root.name}-v":
                errors.append(
                    f"tag_prefix {release.tag_prefix!r} != '{skill_root.name}-v'"
                )
            if release.license != "Apache-2.0":
                errors.append("release.toml license must be Apache-2.0")
            if skill_version != release.version:
                errors.append(
                    f"release.toml version {release.version} != SKILL.md version {skill_version}"
                )

    changelog = skill_root / "CHANGELOG.md"
    if not changelog.is_file():
        errors.append("missing CHANGELOG.md")
    else:
        changelog_text = changelog.read_text(encoding="utf-8")
        if not changelog_text.startswith("# Changelog"):
            errors.append("CHANGELOG.md must start with # Changelog")
        if UNRELEASED_RE.search(changelog_text) is None:
            errors.append("CHANGELOG.md missing ## Unreleased section")

    if not (skill_root / "README.md").is_file():
        errors.append("missing README.md")
    if not (skill_root / "README.en.md").is_file():
        errors.append("missing README.en.md")

    license_path = skill_root / "LICENSE.txt"
    if not license_path.is_file():
        errors.append("missing Apache license")
    else:
        license_text = license_path.read_text(encoding="utf-8")
        if "Apache License" not in license_text or "Version 2.0" not in license_text:
            errors.append("missing Apache license")

    openai_path = skill_root / "agents" / "openai.yaml"
    if not openai_path.is_file():
        errors.append("missing agents/openai.yaml")
    else:
        errors.extend(_validate_openai_yaml(openai_path, skill_root.name))

    for child in skill_root.iterdir():
        if _is_ignored_residue(child.name):
            continue
        if child.name not in ALLOWED_TOP_LEVEL:
            errors.append(f"unexpected top-level file: {child.name}")

    for path in _iter_payload_paths(skill_root):
        relative = path.relative_to(skill_root).as_posix()
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode):
            errors.append(f"symlink is not allowed: {relative}")
            continue
        if any(part in FORBIDDEN_PAYLOAD_NAMES for part in path.relative_to(skill_root).parts):
            errors.append(f"payload test/eval/maintainer file: {relative}")
        if stat.S_ISDIR(info.st_mode):
            continue
        if not stat.S_ISREG(info.st_mode):
            errors.append(f"special file is not allowed: {relative}")
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if HOME_PREFIX in content:
            errors.append(f"personal macOS home-prefix path in {relative}")
        if any(marker in content for marker in ARCHIVE_MARKERS):
            errors.append(f"Archive checkout assumption in {relative}")
        if any(marker in content for marker in CREDENTIAL_MARKERS):
            errors.append(f"credential-like token in {relative}")
        if any(identifier in content for identifier in LEGACY_IDENTIFIERS):
            errors.append(f"legacy prefixed identifier in {relative}")
        if path.suffix.lower() in {".md", ".markdown"}:
            errors.extend(_check_relative_links(skill_root, relative, content))
    return errors


def stage_product(skill_root: Path, destination: Path, registry: ProductRegistry) -> Path:
    skill_root = Path(skill_root)
    errors = validate_product(skill_root, registry)
    if errors:
        raise ValueError("\n".join(errors))
    target = Path(destination) / skill_root.name
    shutil.copytree(
        skill_root,
        target,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
        symlinks=False,
    )
    staged_errors = validate_product(target, registry)
    if staged_errors:
        raise ValueError("\n".join(staged_errors))
    return target


def _normalized_mode(mode: int, data: bytes) -> str:
    executable = bool(mode & 0o111) or data.startswith(b"#!")
    return "0755" if executable else "0644"


def _is_ignored_residue(name: str) -> bool:
    return name in IGNORE_NAMES or Path(name).suffix in BYTECODE_SUFFIXES


def _validate_openai_yaml(path: Path, skill_name: str) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    for field in ("display_name:", "short_description:", "default_prompt:"):
        if field not in text:
            errors.append(f"missing {field[:-1]} in agents/openai.yaml")
    if f"${skill_name}" not in text:
        errors.append("default_prompt must mention the skill")
    if "allow_implicit_invocation: true" not in text:
        errors.append("invocation policy must match the skill activation gate")
    if "allow_implicit_invocation: false" in text:
        errors.append("invocation policy bypasses excluded near misses")
    return errors


def _check_relative_links(skill_root: Path, relative_path: str, text: str) -> list[str]:
    errors: list[str] = []
    base = (skill_root / relative_path).parent
    for href in MARKDOWN_LINK_RE.findall(text):
        target = href.strip()
        if not target or target.startswith("#"):
            continue
        if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target):
            continue
        path_part = target.split("#", 1)[0]
        if not path_part:
            continue
        resolved = (base / path_part).resolve()
        try:
            resolved.relative_to(skill_root.resolve())
        except ValueError:
            if Path(relative_path).name in {"README.md", "README.en.md"}:
                continue
            errors.append(f"broken relative link in {relative_path}: {target}")
            continue
        if not resolved.exists():
            errors.append(f"broken relative link in {relative_path}: {target}")
    return errors


def _iter_payload_paths(skill_root: Path):
    for path in skill_root.rglob("*"):
        parts = path.relative_to(skill_root).parts
        if any(_is_ignored_residue(part) for part in parts):
            continue
        yield path
