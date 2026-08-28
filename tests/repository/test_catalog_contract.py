from __future__ import annotations

import hashlib
import json
import os
import stat
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.catalog_contract import (  # noqa: E402
    load_catalog_lock,
    load_catalog_release,
    validate_catalog,
)
from scripts.catalog_lock import import_legacy_release  # noqa: E402
from scripts.lib.product_contract import payload_sha256  # noqa: E402
from tests.repository.test_repository import EXPECTED_PLUGIN  # noqa: E402


PINNED_SOURCE_COMMIT = "78a8b1bf37d1b943f4b8337121b556eeaea926ae"
PLUGIN_PATH = ROOT / "catalog" / "plugin" / ".codex-plugin" / "plugin.json"
HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64
COMMIT_C = "c" * 40
LEGACY_IMAGE = {
    "name": "image-workbench",
    "version": "2.0.0",
    "tag": "v2.0.0",
    "release_kind": "legacy-bundle",
    "source_commit": PINNED_SOURCE_COMMIT,
    "payload_sha256": HASH_A,
}
LEGACY_KOREAN = {
    "name": "korean-writing-editor",
    "version": "2.0.0",
    "tag": "v2.0.0",
    "release_kind": "legacy-bundle",
    "source_commit": PINNED_SOURCE_COMMIT,
    "payload_sha256": HASH_B,
}


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_release_toml(
    path: Path,
    *,
    extra: str = "",
    version: str = "2.0.0",
    schema_version: int = 1,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                f"schema_version = {schema_version}",
                'name = "beyondwin-skills"',
                f'version = "{version}"',
                'tag_prefix = "beyondwin-skills-v"',
                extra,
            ]
        ).rstrip()
        + "\n",
        encoding="utf-8",
    )


def _write_plugin(path: Path, *, version: str = "2.0.0") -> None:
    _write_json(
        path,
        {
            "name": "beyondwin-skills",
            "version": version,
            "skills": "./skills/",
        },
    )


def _write_lock(path: Path, skills: list[dict[str, object]], **extra: object) -> None:
    payload: dict[str, object] = {"schema_version": 1, "skills": skills}
    payload.update(extra)
    _write_json(path, payload)


def _catalog_tree(
    workspace: Path,
    *,
    skills: list[dict[str, object]] | None = None,
    version: str = "2.0.0",
    plugin_version: str | None = None,
    release_extra: str = "",
    lock_extra: dict[str, object] | None = None,
) -> Path:
    catalog = workspace / "catalog"
    _write_release_toml(
        catalog / "release.toml",
        extra=release_extra,
        version=version,
    )
    _write_plugin(
        catalog / "plugin" / ".codex-plugin" / "plugin.json",
        version=plugin_version if plugin_version is not None else version,
    )
    _write_lock(
        catalog / "catalog.lock.json",
        list(skills if skills is not None else [LEGACY_IMAGE, LEGACY_KOREAN]),
        **(lock_extra or {}),
    )
    return workspace


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_checksums(directory: Path, names: tuple[str, ...], extra_rows: tuple[str, ...] = ()) -> Path:
    lines = [f"{_sha256_file(directory / name)}  {name}" for name in names]
    lines.extend(extra_rows)
    path = directory / "SHA256SUMS"
    path.write_text("\n".join(lines) + "\n", encoding="ascii")
    return path


def _write_zip(
    path: Path,
    members: list[tuple[str, bytes]],
    *,
    modes: dict[str, int] | None = None,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in members:
            info = zipfile.ZipInfo(name)
            mode = (modes or {}).get(name, stat.S_IFREG | 0o644)
            info.external_attr = mode << 16
            archive.writestr(info, data)
    return path


def _product_members(name: str) -> list[tuple[str, bytes]]:
    return [
        (f"{name}/SKILL.md", f"---\nname: {name}\n---\n# {name}\n".encode("utf-8")),
        (f"{name}/LICENSE.txt", b"Apache License\nVersion 2.0, January 2004\n"),
        (f"{name}/scripts/tool.py", b"#!/usr/bin/env python3\nprint('ok')\n"),
    ]


def _legacy_release_dir(workspace: Path) -> Path:
    release_dir = workspace / "release"
    release_dir.mkdir()
    for name in ("image-workbench", "korean-writing-editor"):
        _write_zip(release_dir / f"{name}-v2.0.0.zip", _product_members(name))
    _write_checksums(
        release_dir,
        ("image-workbench-v2.0.0.zip", "korean-writing-editor-v2.0.0.zip"),
        extra_rows=(f"{'e' * 64}  beyondwin-skills-v2.0.0.zip",),
    )
    return release_dir


class CatalogContractTests(unittest.TestCase):
    def test_plugin_manifest_is_owned_below_catalog(self) -> None:
        self.assertFalse((ROOT / ".codex-plugin" / "plugin.json").exists())
        self.assertTrue(
            (ROOT / "catalog" / "plugin" / ".codex-plugin" / "plugin.json").is_file()
        )

    def test_legacy_lock_pins_exactly_the_two_v2_products(self) -> None:
        lock = load_catalog_lock(ROOT / "catalog" / "catalog.lock.json")
        self.assertEqual([item.name for item in lock.skills], [
            "image-workbench",
            "korean-writing-editor",
        ])
        self.assertTrue(all(item.release_kind == "legacy-bundle" for item in lock.skills))
        self.assertTrue(all(item.tag == "v2.0.0" for item in lock.skills))
        self.assertTrue(all(item.source_commit == PINNED_SOURCE_COMMIT for item in lock.skills))
        self.assertTrue(all(item.version == "2.0.0" for item in lock.skills))

    def test_catalog_plugin_contract_does_not_lookup_git_tag(self) -> None:
        source = Path(__file__).read_text(encoding="utf-8")
        self.assertNotIn(" ".join(("git", "show", "v2.0.0")), source)
        self.assertNotIn("v2.0.0:" + ".codex-plugin/plugin.json", source)

    def test_catalog_release_identity_and_plugin_bytes_match_v2(self) -> None:
        release = load_catalog_release(ROOT / "catalog" / "release.toml")
        self.assertEqual(release.name, "beyondwin-skills")
        self.assertEqual(release.version, "2.0.0")
        self.assertEqual(release.tag_prefix, "beyondwin-skills-v")
        plugin = json.loads(PLUGIN_PATH.read_text(encoding="utf-8"))
        self.assertEqual(plugin, EXPECTED_PLUGIN)
        self.assertNotIn("graspic", json.dumps(plugin))
        self.assertEqual(validate_catalog(ROOT), [])

    def test_catalog_readme_states_artifact_and_root_roles(self) -> None:
        text = (ROOT / "catalog" / "README.md").read_text(encoding="utf-8")
        self.assertIn("only released plugin ZIPs are supported catalog artifacts", text)
        self.assertIn("repository root is for individual skill installs", text)

    def test_current_skill_directories_are_not_described_by_catalog_plugin(self) -> None:
        plugin = json.loads(PLUGIN_PATH.read_text(encoding="utf-8"))
        self.assertNotIn("graspic", json.dumps(plugin))
        self.assertEqual(
            {path.name for path in (ROOT / "skills").iterdir() if path.is_dir()},
            {"graspic", "image-workbench", "korean-writing-editor"},
        )


class CatalogSchemaRejectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tempdir = tempfile.TemporaryDirectory()
        self.workspace = Path(self._tempdir.name)

    def tearDown(self) -> None:
        self._tempdir.cleanup()

    def _errors(self, **kwargs: object) -> str:
        return "\n".join(validate_catalog(_catalog_tree(self.workspace, **kwargs)))

    def test_rejects_unknown_release_and_lock_keys_before_construction(self) -> None:
        errors = self._errors(release_extra='license = "Apache-2.0"', lock_extra={"comment": "nope"})
        self.assertIn("unknown catalog/release.toml key: license", errors)
        self.assertIn("unknown catalog.lock.json key: comment", errors)

    def test_rejects_unknown_lock_skill_key(self) -> None:
        image = dict(LEGACY_IMAGE)
        image["note"] = "extra"
        errors = self._errors(skills=[image, LEGACY_KOREAN])
        self.assertIn("unknown lock skill key: note", errors)

    def test_rejects_unsorted_names(self) -> None:
        errors = self._errors(skills=[LEGACY_KOREAN, LEGACY_IMAGE])
        self.assertIn("catalog.lock.json skills are not sorted by name", errors)

    def test_rejects_duplicate_products(self) -> None:
        errors = self._errors(skills=[LEGACY_IMAGE, dict(LEGACY_IMAGE)])
        self.assertIn("duplicate product", errors)

    def test_rejects_invalid_release_kind(self) -> None:
        image = dict(LEGACY_IMAGE)
        image["release_kind"] = "bundle"
        errors = self._errors(skills=[image, LEGACY_KOREAN])
        self.assertIn("invalid release kind: bundle", errors)

    def test_rejects_malformed_commit_and_hash(self) -> None:
        image = dict(LEGACY_IMAGE)
        image["source_commit"] = PINNED_SOURCE_COMMIT.upper()
        image["payload_sha256"] = HASH_A.upper()
        errors = self._errors(skills=[image, LEGACY_KOREAN])
        self.assertIn("source_commit", errors)
        self.assertIn("payload_sha256", errors)

    def test_rejects_legacy_entry_for_graspic(self) -> None:
        graspic = {
            "name": "graspic",
            "version": "2.0.0",
            "tag": "v2.0.0",
            "release_kind": "legacy-bundle",
            "source_commit": PINNED_SOURCE_COMMIT,
            "payload_sha256": HASH_C,
        }
        errors = self._errors(skills=[graspic, LEGACY_IMAGE, LEGACY_KOREAN])
        self.assertIn("legacy-bundle", errors)
        self.assertIn("graspic", errors)

    def test_rejects_independent_entry_without_product_qualified_tag(self) -> None:
        graspic = {
            "name": "graspic",
            "version": "3.0.0",
            "tag": "v3.0.0",
            "release_kind": "independent",
            "source_commit": COMMIT_C,
            "payload_sha256": HASH_C,
        }
        errors = self._errors(skills=[graspic, LEGACY_IMAGE, LEGACY_KOREAN])
        self.assertIn("graspic-v3.0.0", errors)

    def test_rejects_catalog_plugin_version_mismatch_and_invalid_semver(self) -> None:
        mismatch = self._errors(plugin_version="2.1.0")
        self.assertIn("catalog/plugin version", mismatch)
        semver = self._errors(version="2.0")
        self.assertIn("invalid SemVer: 2.0", semver)


class CatalogLockImportTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tempdir = tempfile.TemporaryDirectory()
        self.workspace = Path(self._tempdir.name)

    def tearDown(self) -> None:
        self._tempdir.cleanup()

    def test_import_legacy_release_writes_sorted_canonical_lock(self) -> None:
        release_dir = _legacy_release_dir(self.workspace)
        output = self.workspace / "catalog" / "catalog.lock.json"
        result = import_legacy_release(release_dir, PINNED_SOURCE_COMMIT, output)
        self.assertEqual(result, output)
        raw = output.read_text(encoding="utf-8")
        self.assertTrue(raw.endswith("\n"))
        payload = json.loads(raw)
        self.assertEqual(payload, json.loads(json.dumps(payload, sort_keys=True)))
        self.assertEqual(
            [item["name"] for item in payload["skills"]],
            ["image-workbench", "korean-writing-editor"],
        )
        lock = load_catalog_lock(output)
        self.assertEqual(lock.schema_version, 1)
        by_name = {item.name: item for item in lock.skills}
        for name in ("image-workbench", "korean-writing-editor"):
            item = by_name[name]
            self.assertEqual(item.version, "2.0.0")
            self.assertEqual(item.tag, "v2.0.0")
            self.assertEqual(item.release_kind, "legacy-bundle")
            self.assertEqual(item.source_commit, PINNED_SOURCE_COMMIT)
            extracted = self.workspace / "expected" / name
            for relative, data in _product_members(name):
                path = extracted / relative.split("/", 1)[1]
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
            self.assertEqual(item.payload_sha256, payload_sha256(extracted))

    def test_import_tolerates_unrelated_checksum_rows_without_those_assets(self) -> None:
        release_dir = _legacy_release_dir(self.workspace)
        self.assertFalse((release_dir / "beyondwin-skills-v2.0.0.zip").exists())
        output = self.workspace / "catalog.lock.json"
        import_legacy_release(release_dir, PINNED_SOURCE_COMMIT, output)
        self.assertTrue(output.is_file())

    def test_import_rejects_a_third_local_zip_or_unexpected_file(self) -> None:
        release_dir = _legacy_release_dir(self.workspace)
        (release_dir / "graspic-v2.0.0.zip").write_bytes(b"PK\x03\x04not-a-real-zip")
        with self.assertRaises(ValueError) as extra_zip:
            import_legacy_release(
                release_dir,
                PINNED_SOURCE_COMMIT,
                self.workspace / "lock.json",
            )
        self.assertIn("unexpected", str(extra_zip.exception).lower())
        (release_dir / "graspic-v2.0.0.zip").unlink()
        (release_dir / "notes.txt").write_text("nope\n", encoding="utf-8")
        with self.assertRaises(ValueError) as extra_file:
            import_legacy_release(
                release_dir,
                PINNED_SOURCE_COMMIT,
                self.workspace / "lock.json",
            )
        self.assertIn("unexpected", str(extra_file.exception).lower())

    def test_import_rejects_unsafe_archive_members(self) -> None:
        cases = {
            "absolute path": [("/tmp/evil", b"x")],
            "backslash": [("korean-writing-editor\\SKILL.md", b"x")],
            "empty segment": [("korean-writing-editor//SKILL.md", b"x")],
            "dot segment": [("korean-writing-editor/./SKILL.md", b"x")],
            "parent segment": [("korean-writing-editor/../SKILL.md", b"x")],
            "duplicate": [
                ("korean-writing-editor/SKILL.md", b"one"),
                ("korean-writing-editor/SKILL.md", b"two"),
            ],
            "case-fold collision": [
                ("korean-writing-editor/SKILL.md", b"one"),
                ("korean-writing-editor/skill.md", b"two"),
            ],
        }
        for label, members in cases.items():
            with self.subTest(label=label):
                release_dir = self.workspace / label
                release_dir.mkdir()
                _write_zip(
                    release_dir / "image-workbench-v2.0.0.zip",
                    _product_members("image-workbench"),
                )
                _write_zip(release_dir / "korean-writing-editor-v2.0.0.zip", members)
                _write_checksums(
                    release_dir,
                    (
                        "image-workbench-v2.0.0.zip",
                        "korean-writing-editor-v2.0.0.zip",
                    ),
                )
                with self.assertRaises(ValueError):
                    import_legacy_release(
                        release_dir,
                        PINNED_SOURCE_COMMIT,
                        self.workspace / f"{label}.json",
                    )

    @unittest.skipIf(
        os.name == "nt" or not hasattr(os, "mkfifo"),
        "symlink and FIFO zip members are asserted via Unix mode bits",
    )
    def test_import_rejects_symlink_and_special_file_members(self) -> None:
        release_dir = self.workspace / "special"
        release_dir.mkdir()
        _write_zip(
            release_dir / "image-workbench-v2.0.0.zip",
            _product_members("image-workbench"),
        )
        _write_zip(
            release_dir / "korean-writing-editor-v2.0.0.zip",
            [
                ("korean-writing-editor/SKILL.md", b"# skill\n"),
                ("korean-writing-editor/link.md", b"SKILL.md"),
            ],
            modes={"korean-writing-editor/link.md": stat.S_IFLNK | 0o644},
        )
        _write_checksums(
            release_dir,
            ("image-workbench-v2.0.0.zip", "korean-writing-editor-v2.0.0.zip"),
        )
        with self.assertRaises(ValueError) as raised:
            import_legacy_release(
                release_dir,
                PINNED_SOURCE_COMMIT,
                self.workspace / "symlink.json",
            )
        self.assertIn("symlink", str(raised.exception).lower())

        fifo_dir = self.workspace / "fifo"
        fifo_dir.mkdir()
        _write_zip(
            fifo_dir / "image-workbench-v2.0.0.zip",
            _product_members("image-workbench"),
        )
        _write_zip(
            fifo_dir / "korean-writing-editor-v2.0.0.zip",
            [
                ("korean-writing-editor/SKILL.md", b"# skill\n"),
                ("korean-writing-editor/pipe", b""),
            ],
            modes={"korean-writing-editor/pipe": stat.S_IFIFO | 0o644},
        )
        _write_checksums(
            fifo_dir,
            ("image-workbench-v2.0.0.zip", "korean-writing-editor-v2.0.0.zip"),
        )
        with self.assertRaises(ValueError) as fifo_raised:
            import_legacy_release(
                fifo_dir,
                PINNED_SOURCE_COMMIT,
                self.workspace / "fifo.json",
            )
        self.assertIn("special", str(fifo_raised.exception).lower())

    def test_importer_reuses_release_archive_safety_primitives(self) -> None:
        source = (ROOT / "scripts" / "catalog_lock.py").read_text(encoding="utf-8")
        self.assertIn("from scripts.release_archive import", source)
        self.assertNotIn("def _member_safety_errors", source)
        self.assertNotIn("def _member_mode_errors", source)
        self.assertNotIn("def _is_absolute_member", source)
        self.assertNotIn("def _parse_checksums", source)
        self.assertNotIn("def _archive_member_errors", source)

    def test_import_does_not_require_historical_release_toml(self) -> None:
        release_dir = _legacy_release_dir(self.workspace)
        output = self.workspace / "lock.json"
        import_legacy_release(release_dir, PINNED_SOURCE_COMMIT, output)
        with zipfile.ZipFile(release_dir / "korean-writing-editor-v2.0.0.zip") as archive:
            self.assertNotIn("korean-writing-editor/release.toml", archive.namelist())
            self.assertNotIn("korean-writing-editor/CHANGELOG.md", archive.namelist())
        lock = load_catalog_lock(output)
        self.assertEqual(len(lock.skills), 2)


if __name__ == "__main__":
    unittest.main()
