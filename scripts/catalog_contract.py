from __future__ import annotations

import dataclasses
import json
import re
import tomllib
from collections.abc import Sequence
from pathlib import Path


SEMVER_RE = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
HASH_RE = re.compile(r"^[0-9a-f]{64}$")
CATALOG_NAME = "beyondwin-skills"
CATALOG_TAG_PREFIX = "beyondwin-skills-v"
LEGACY_BUNDLE_PRODUCTS = frozenset({"image-workbench", "korean-writing-editor"})
LEGACY_BUNDLE_VERSION = "2.0.0"
LEGACY_BUNDLE_TAG = "v2.0.0"
PINNED_SOURCE_COMMIT = "78a8b1bf37d1b943f4b8337121b556eeaea926ae"
RELEASE_KEYS = frozenset({"schema_version", "name", "version", "tag_prefix"})
LOCK_KEYS = frozenset({"schema_version", "skills"})
LOCKED_SKILL_KEYS = frozenset(
    {
        "name",
        "version",
        "tag",
        "release_kind",
        "source_commit",
        "payload_sha256",
    }
)


@dataclasses.dataclass(frozen=True)
class CatalogRelease:
    root: Path
    name: str
    version: str
    tag_prefix: str


@dataclasses.dataclass(frozen=True)
class LockedSkill:
    name: str
    version: str
    tag: str
    release_kind: str
    source_commit: str
    payload_sha256: str


@dataclasses.dataclass(frozen=True)
class CatalogLock:
    schema_version: int
    skills: Sequence[LockedSkill]


def load_catalog_release(path: Path) -> CatalogRelease:
    data = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    return CatalogRelease(
        root=Path(path).parent,
        name=str(data["name"]),
        version=str(data["version"]),
        tag_prefix=str(data["tag_prefix"]),
    )


def load_catalog_lock(path: Path) -> CatalogLock:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    skills = tuple(LockedSkill(**item) for item in data["skills"])
    return CatalogLock(schema_version=int(data["schema_version"]), skills=skills)


def validate_catalog(root: Path) -> list[str]:
    root = Path(root)
    errors: list[str] = []
    release_path = root / "catalog" / "release.toml"
    lock_path = root / "catalog" / "catalog.lock.json"
    plugin_path = root / "catalog" / "plugin" / ".codex-plugin" / "plugin.json"

    if not release_path.is_file():
        errors.append("missing catalog/release.toml")
    if not lock_path.is_file():
        errors.append("missing catalog/catalog.lock.json")
    if not plugin_path.is_file():
        errors.append("missing catalog/plugin/.codex-plugin/plugin.json")
    if errors:
        return errors

    try:
        release_data = tomllib.loads(release_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return [f"invalid catalog/release.toml: {exc}"]
    if not isinstance(release_data, dict):
        return ["catalog/release.toml must be a table"]

    try:
        lock_data = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"invalid catalog.lock.json: {exc}"]
    if not isinstance(lock_data, dict):
        return ["catalog.lock.json must be an object"]

    errors.extend(_unknown_keys(release_data, RELEASE_KEYS, "unknown catalog/release.toml key"))
    errors.extend(_unknown_keys(lock_data, LOCK_KEYS, "unknown catalog.lock.json key"))
    skill_items = lock_data.get("skills")
    if not isinstance(skill_items, list):
        errors.append("catalog.lock.json skills must be a list")
        return errors
    for item in skill_items:
        if not isinstance(item, dict):
            errors.append("catalog.lock.json skill must be an object")
            continue
        errors.extend(_unknown_keys(item, LOCKED_SKILL_KEYS, "unknown lock skill key"))
    if errors:
        return errors

    release = load_catalog_release(release_path)
    lock = load_catalog_lock(lock_path)
    try:
        plugin = json.loads(plugin_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"invalid catalog plugin manifest: {exc}"]
    if not isinstance(plugin, dict):
        return ["catalog plugin manifest must be an object"]

    if release_data.get("schema_version") != 1:
        errors.append("catalog/release.toml schema_version must be 1")
    if lock.schema_version != 1:
        errors.append("catalog.lock.json schema_version must be 1")
    if release.name != CATALOG_NAME:
        errors.append(f"catalog name {release.name!r} != {CATALOG_NAME!r}")
    if release.tag_prefix != CATALOG_TAG_PREFIX:
        errors.append(
            f"catalog tag_prefix {release.tag_prefix!r} != {CATALOG_TAG_PREFIX!r}"
        )
    if not SEMVER_RE.fullmatch(release.version):
        errors.append(f"invalid SemVer: {release.version}")
    plugin_version = plugin.get("version")
    if plugin_version != release.version:
        errors.append(
            f"catalog/plugin version {plugin_version!r} != {release.version!r}"
        )
    plugin_name = plugin.get("name")
    if plugin_name != release.name:
        errors.append(f"catalog/plugin name {plugin_name!r} != {release.name!r}")

    names = [item.name for item in lock.skills]
    if names != sorted(names):
        errors.append("catalog.lock.json skills are not sorted by name")
    if len(names) != len(set(names)):
        errors.append("duplicate product names in catalog.lock.json")
    for item in lock.skills:
        errors.extend(_validate_locked_skill(item))
    return errors


def _unknown_keys(
    data: dict[str, object],
    allowed: frozenset[str],
    prefix: str,
) -> list[str]:
    return [f"{prefix}: {key}" for key in sorted(set(data) - allowed)]


def _validate_locked_skill(item: LockedSkill) -> list[str]:
    errors: list[str] = []
    if not SEMVER_RE.fullmatch(item.version):
        errors.append(f"invalid SemVer: {item.version}")
    if not COMMIT_RE.fullmatch(item.source_commit):
        errors.append(f"invalid source_commit: {item.source_commit}")
    if not HASH_RE.fullmatch(item.payload_sha256):
        errors.append(f"invalid payload_sha256: {item.payload_sha256}")
    if item.release_kind == "legacy-bundle":
        if item.name not in LEGACY_BUNDLE_PRODUCTS:
            errors.append(
                f"legacy-bundle is not permitted for {item.name}"
            )
        if item.version != LEGACY_BUNDLE_VERSION:
            errors.append(
                f"legacy-bundle version {item.version} != {LEGACY_BUNDLE_VERSION}"
            )
        if item.tag != LEGACY_BUNDLE_TAG:
            errors.append(f"legacy-bundle tag {item.tag} != {LEGACY_BUNDLE_TAG}")
        if item.source_commit != PINNED_SOURCE_COMMIT:
            errors.append(
                f"legacy-bundle source_commit {item.source_commit} != {PINNED_SOURCE_COMMIT}"
            )
    elif item.release_kind == "independent":
        expected = f"{item.name}-v{item.version}"
        if item.tag != expected:
            errors.append(
                f"independent tag {item.tag} is not product-qualified; expected {expected}"
            )
    else:
        errors.append(f"invalid release kind: {item.release_kind}")
    return errors
