from __future__ import annotations

import dataclasses
import json
import re
import tempfile
import tomllib
from collections.abc import Sequence
from pathlib import Path

from scripts.release_archive import (
    extract_archive,
    sha256_file,
    verify_product_archive,
    _parse_checksums,
)
from scripts.lib.product_contract import (
    load_product_release,
    parse_skill_frontmatter,
    payload_sha256,
    validate_product,
)
from scripts.lib.product_registry import ProductRegistry


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


def catalog_artifact_name(release: CatalogRelease) -> str:
    return f"{release.name}-v{release.version}.zip"


def locked_artifact_name(item: LockedSkill) -> str:
    return f"{item.name}-v{item.version}.zip"


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


def validate_catalog_inputs(
    root: Path, input_dir: Path, registry: ProductRegistry
) -> list[str]:
    root = Path(root)
    input_dir = Path(input_dir)
    errors = validate_catalog(root)
    if errors:
        return errors
    if not input_dir.is_dir():
        return [f"input directory is not a directory: {input_dir}"]

    lock = load_catalog_lock(root / "catalog" / "catalog.lock.json")
    expected_zips = {locked_artifact_name(item) for item in lock.skills}
    errors.extend(_input_directory_errors(input_dir, expected_zips | {"SHA256SUMS"}))
    checksums_path = input_dir / "SHA256SUMS"
    if not checksums_path.is_file():
        errors.append("missing SHA256SUMS")
        return errors
    parse_errors: list[str] = []
    try:
        parsed = _parse_checksums(checksums_path, parse_errors)
    except (OSError, UnicodeError) as exc:
        errors.append(f"SHA256SUMS: {exc}")
        return errors
    if parse_errors:
        errors.extend(parse_errors)
        return errors
    missing_rows = [name for name in sorted(expected_zips) if name not in parsed]
    if missing_rows:
        errors.append("SHA256SUMS missing checksum row: " + ", ".join(missing_rows))
    for name in sorted(expected_zips):
        archive = input_dir / name
        if not archive.is_file():
            errors.append(f"missing archive: {name}")
            continue
        if name in parsed and sha256_file(archive) != parsed[name]:
            errors.append(f"checksum mismatch: {name}")
    if errors:
        return errors

    for item in lock.skills:
        errors.extend(_validate_locked_archive(root, input_dir / locked_artifact_name(item), item, registry))
    return errors


def locked_extract_errors(
    root: Path, skill_root: Path, item: LockedSkill, registry: ProductRegistry
) -> list[str]:
    skill_root = Path(skill_root)
    errors: list[str] = []
    if item.release_kind == "legacy-bundle":
        errors.extend(_legacy_extract_errors(skill_root, item))
    elif item.release_kind == "independent":
        errors.extend(_independent_extract_errors(root, skill_root, item, registry))
    else:
        errors.append(f"invalid release kind: {item.release_kind}")
    try:
        digest = payload_sha256(skill_root)
    except ValueError as exc:
        errors.append(f"{item.name}: {exc}")
        return errors
    if digest != item.payload_sha256:
        errors.append(f"payload hash mismatch: {item.name}")
    return errors


def _input_directory_errors(directory: Path, expected: set[str]) -> list[str]:
    errors: list[str] = []
    for path in sorted(directory.iterdir(), key=lambda item: item.name):
        if path.name in expected:
            continue
        if path.is_dir():
            errors.append(f"unexpected directory in input directory: {path.name}")
        elif path.suffix == ".zip":
            errors.append(f"unexpected zip in input directory: {path.name}")
        else:
            errors.append(f"unexpected file in input directory: {path.name}")
    return errors


def _validate_locked_archive(
    root: Path, archive: Path, item: LockedSkill, registry: ProductRegistry
) -> list[str]:
    errors = verify_product_archive(archive, item.name)
    if errors:
        return errors
    with tempfile.TemporaryDirectory() as directory:
        destination = Path(directory)
        extract_errors = extract_archive(archive, destination)
        if extract_errors:
            return extract_errors
        skill_root = destination / item.name
        if not skill_root.is_dir():
            return [f"missing extracted skill: {item.name}"]
        errors = locked_extract_errors(root, skill_root, item, registry)
        if errors:
            return errors
        if item.release_kind == "independent":
            from scripts.release import _run_product_smoke

            errors.extend(_run_product_smoke(root, item.name, skill_root))
        return errors


def _legacy_extract_errors(skill_root: Path, item: LockedSkill) -> list[str]:
    errors: list[str] = []
    if item.name not in LEGACY_BUNDLE_PRODUCTS:
        errors.append(f"legacy-bundle is not permitted for {item.name}")
    if item.version != LEGACY_BUNDLE_VERSION:
        errors.append(
            f"legacy-bundle version {item.version} != {LEGACY_BUNDLE_VERSION}"
        )
    version = _skill_version(skill_root)
    if version != item.version:
        errors.append(f"{item.name}: SKILL.md version {version} != {item.version}")
    return errors


def _independent_extract_errors(
    _root: Path, skill_root: Path, item: LockedSkill, registry: ProductRegistry
) -> list[str]:
    errors: list[str] = []
    expected_tag = f"{item.name}-v{item.version}"
    if item.tag != expected_tag:
        errors.append(
            f"independent tag {item.tag} is not product-qualified; expected {expected_tag}"
        )
    release_path = skill_root / "release.toml"
    if not release_path.is_file():
        errors.append(f"{item.name}: missing release.toml")
        return errors
    try:
        extracted = load_product_release(skill_root)
    except (OSError, ValueError, KeyError) as exc:
        return [f"{item.name}: release.toml: {exc}"]
    if extracted.tag != expected_tag:
        errors.append(
            f"independent tag {extracted.tag} is not product-qualified; expected {expected_tag}"
        )
    if extracted.version != item.version:
        errors.append(
            f"metadata version mismatch: {extracted.version} != {item.version}"
        )
    version = _skill_version(skill_root)
    if version != item.version:
        errors.append(f"{item.name}: SKILL.md version {version} != {item.version}")
    errors.extend(validate_product(skill_root, registry))
    return errors


def _skill_version(skill_root: Path) -> str | None:
    skill_md = skill_root / "SKILL.md"
    if not skill_md.is_file():
        return None
    frontmatter = parse_skill_frontmatter(skill_md.read_text(encoding="utf-8"))
    metadata = frontmatter.get("metadata")
    if not isinstance(metadata, dict):
        return None
    version = metadata.get("version")
    return str(version) if version is not None else None
