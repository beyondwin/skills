from __future__ import annotations

import json
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.catalog import (  # noqa: E402
    PINNED_SOURCE_COMMIT,
    load_catalog_lock,
    validate_catalog_inputs,
)
from scripts.release import build_catalog, verify_catalog_download  # noqa: E402
from scripts.lib.archive import (  # noqa: E402
    ArchiveMember,
    ReleaseError,
    extract_archive,
    sha256_file,
    write_checksums,
    write_zip,
    zip_names,
)
from scripts.lib.product_contract import payload_sha256  # noqa: E402
from scripts.lib.product_registry import load_registry  # noqa: E402
from scripts import release  # noqa: E402

REGISTRY = load_registry(ROOT / "products.toml")


HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64
COMMIT_C = "c" * 40
SCRIPT = ROOT / "scripts" / "release.py"
LEGACY_FIXTURE_ROOT = ROOT / "tests" / "repository" / "fixtures" / "legacy-bundle-v2.0.0"
PUBLISHED_V2_NOTICE = (
    b"beyondwin-skills\n"
    b"Copyright 2026 beyondwin\n"
    b"\n"
    b"This product includes skills migrated from the Archive repository\n"
    b"https://github.com/beyondwin/Archive.git\n"
    b"pinned source commit 76e6bf4ebbc9430aee9a04a5b780ae38330f3021\n"
    b"manifest digest 6917f68e6e0d81226e50195d58a884373d23ffbbbe48363ef2428c8cbcb83f78\n"
)


def _standalone_members_from_fixture(name: str) -> list[ArchiveMember]:
    fixture = LEGACY_FIXTURE_ROOT / name
    members: list[ArchiveMember] = []
    for path in fixture.rglob("*"):
        if not path.is_file():
            continue
        if "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
            continue
        relative = path.relative_to(fixture).as_posix()
        data = path.read_bytes()
        members.append(
            ArchiveMember(
                name=f"{name}/{relative}",
                data=data,
                executable=data.startswith(b"#!"),
            )
        )
    if not members:
        raise RuntimeError(f"missing legacy fixture for {name}")
    members.sort(key=lambda item: item.name)
    return members


def _populate_legacy_inputs(root: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    lock = load_catalog_lock(root / "catalog" / "catalog.lock.json")
    archives: list[Path] = []
    for item in lock.skills:
        archive = dest / f"{item.name}-v{item.version}.zip"
        members = _standalone_members_from_fixture(item.name)
        write_zip(archive, members)
        with tempfile.TemporaryDirectory() as directory:
            extracted = Path(directory)
            errors = extract_archive(archive, extracted)
            if errors:
                raise RuntimeError("\n".join(errors))
            digest = payload_sha256(extracted / item.name)
            if digest != item.payload_sha256:
                raise RuntimeError(
                    f"reconstructed {item.name} payload {digest} != lock {item.payload_sha256}"
                )
        archives.append(archive)
    checksums = write_checksums(tuple(archives), dest / "SHA256SUMS")
    checksums.write_text(
        checksums.read_text(encoding="ascii")
        + f"{'0' * 64}  beyondwin-skills-v2.0.0.zip\n",
        encoding="ascii",
    )


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_checksums(directory: Path, names: tuple[str, ...]) -> Path:
    return write_checksums(tuple(directory / name for name in names), directory / "SHA256SUMS")


def _rewrite_zip(archive: Path, rewriter) -> None:
    with zipfile.ZipFile(archive) as source:
        items = [(info, source.read(info)) for info in source.infolist()]
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as dest:
        for info, data in rewriter(items):
            dest.writestr(info, data)


class CatalogLegacyNewlineTests(unittest.TestCase):
    def test_legacy_fixture_bytes_use_lf_newlines(self) -> None:
        files = [
            path
            for path in LEGACY_FIXTURE_ROOT.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
        ]
        self.assertGreater(len(files), 0)
        for path in files:
            self.assertNotIn(b"\r", path.read_bytes(), path.as_posix())


class CatalogLegacyFixtureTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tempdir = tempfile.TemporaryDirectory()
        root = Path(self._tempdir.name)
        self.legacy_inputs = root / "inputs"
        self.output_one = root / "one"
        self.output_two = root / "two"
        self.legacy_inputs.mkdir()
        self.output_one.mkdir()
        self.output_two.mkdir()
        _populate_legacy_inputs(ROOT, self.legacy_inputs)

    def tearDown(self) -> None:
        self._tempdir.cleanup()

    def test_catalog_build_uses_locked_archives_not_current_skill_source(self) -> None:
        before = build_catalog(ROOT, self.legacy_inputs, self.output_one)
        with mock.patch.object(Path, "read_bytes", autospec=True, wraps=Path.read_bytes) as read_bytes:
            after = build_catalog(ROOT, self.legacy_inputs, self.output_two)
        self.assertEqual(sha256_file(before[0]), sha256_file(after[0]))
        current_skill_paths = [
            str(call.args[0])
            for call in read_bytes.call_args_list
            if call.args and "/skills/" in str(call.args[0])
        ]
        self.assertEqual(current_skill_paths, [])

    def test_catalog_build_emits_only_plugin_zip_and_checksums(self) -> None:
        artifacts = build_catalog(ROOT, self.legacy_inputs, self.output_one)
        self.assertEqual(
            {path.name for path in artifacts},
            {"beyondwin-skills-v2.0.0.zip", "SHA256SUMS"},
        )
        self.assertEqual(
            {path.name for path in self.output_one.iterdir()},
            {"beyondwin-skills-v2.0.0.zip", "SHA256SUMS"},
        )

    def test_catalog_build_plugin_members_match_lock(self) -> None:
        archive, _checksums = build_catalog(ROOT, self.legacy_inputs, self.output_one)
        names = zip_names(archive)
        skill_dirs = sorted(
            {
                parts[1]
                for name in names
                if (parts := name.replace("\\", "/").split("/"))[:1] == ["skills"]
                and len(parts) > 1
            }
        )
        lock = load_catalog_lock(ROOT / "catalog" / "catalog.lock.json")
        self.assertEqual(skill_dirs, [item.name for item in lock.skills])
        self.assertIn(".codex-plugin/plugin.json", names)
        self.assertIn("LICENSE", names)
        self.assertIn("NOTICE", names)
        self.assertTrue(any(name.startswith("skills/korean-writing-editor/") for name in names))
        self.assertTrue(any(name.startswith("skills/image-workbench/") for name in names))
        self.assertTrue(
            all(
                not name.startswith("korean-writing-editor/")
                and not name.startswith("image-workbench/")
                for name in names
                if name not in {".codex-plugin/plugin.json", "LICENSE", "NOTICE"}
            )
        )

    def test_catalog_build_payload_matches_standalone_bytes(self) -> None:
        archive, _checksums = build_catalog(ROOT, self.legacy_inputs, self.output_one)
        lock = load_catalog_lock(ROOT / "catalog" / "catalog.lock.json")
        with zipfile.ZipFile(archive) as plugin:
            for item in lock.skills:
                standalone = self.legacy_inputs / f"{item.name}-v{item.version}.zip"
                with zipfile.ZipFile(standalone) as source:
                    expected = {
                        name: source.read(name)
                        for name in source.namelist()
                        if not name.endswith("/")
                    }
                actual = {
                    name.removeprefix("skills/"): plugin.read(name)
                    for name in plugin.namelist()
                    if name.startswith(f"skills/{item.name}/") and not name.endswith("/")
                }
                self.assertEqual(actual, expected, item.name)

    def test_catalog_notice_member_matches_published_v2_0_0(self) -> None:
        archive, _checksums = build_catalog(ROOT, self.legacy_inputs, self.output_one)
        with zipfile.ZipFile(archive) as plugin:
            self.assertEqual(plugin.read("NOTICE"), PUBLISHED_V2_NOTICE)
        self.assertEqual((ROOT / "NOTICE").read_bytes(), PUBLISHED_V2_NOTICE)

    def test_catalog_inputs_reject_missing_locked_zip(self) -> None:
        (self.legacy_inputs / "korean-writing-editor-v2.0.0.zip").unlink()
        errors = "\n".join(validate_catalog_inputs(ROOT, self.legacy_inputs, REGISTRY))
        self.assertIn("missing archive: korean-writing-editor-v2.0.0.zip", errors)

    def test_catalog_inputs_reject_extra_product(self) -> None:
        (self.legacy_inputs / "extra-product-v9.9.9.zip").write_bytes(b"PK\x03\x04not-a-zip")
        errors = "\n".join(validate_catalog_inputs(ROOT, self.legacy_inputs, REGISTRY))
        self.assertIn("unexpected zip in input directory: extra-product-v9.9.9.zip", errors)

    def test_catalog_inputs_reject_wrong_source_version(self) -> None:
        archive = self.legacy_inputs / "korean-writing-editor-v2.0.0.zip"

        def bump_version(items):
            for info, data in items:
                if info.filename == "korean-writing-editor/SKILL.md":
                    text = data.decode("utf-8").replace('version: "2.0.0"', 'version: "9.9.9"')
                    data = text.encode("utf-8")
                yield info, data

        _rewrite_zip(archive, bump_version)
        _write_checksums(
            self.legacy_inputs,
            ("image-workbench-v2.0.0.zip", "korean-writing-editor-v2.0.0.zip"),
        )
        errors = "\n".join(validate_catalog_inputs(ROOT, self.legacy_inputs, REGISTRY))
        self.assertTrue(
            any("version" in error.lower() for error in errors.splitlines()),
            errors,
        )

    def test_catalog_inputs_reject_wrong_payload_hash(self) -> None:
        archive = self.legacy_inputs / "image-workbench-v2.0.0.zip"

        def append_byte(items):
            for info, data in items:
                if info.filename == "image-workbench/SKILL.md":
                    data = data + b"\n"
                yield info, data

        _rewrite_zip(archive, append_byte)
        _write_checksums(
            self.legacy_inputs,
            ("image-workbench-v2.0.0.zip", "korean-writing-editor-v2.0.0.zip"),
        )
        errors = "\n".join(validate_catalog_inputs(ROOT, self.legacy_inputs, REGISTRY))
        self.assertTrue(any("payload" in error.lower() for error in errors.splitlines()), errors)

    def test_catalog_inputs_reject_current_source_fallback(self) -> None:
        current = ROOT / "skills" / "korean-writing-editor"
        members: list[ArchiveMember] = []
        for path in current.rglob("*"):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            relative = path.relative_to(current).as_posix()
            data = path.read_bytes()
            members.append(
                ArchiveMember(
                    name=f"korean-writing-editor/{relative}",
                    data=data,
                    executable=data.startswith(b"#!"),
                )
            )
        write_zip(self.legacy_inputs / "korean-writing-editor-v2.0.0.zip", members)
        _write_checksums(
            self.legacy_inputs,
            ("image-workbench-v2.0.0.zip", "korean-writing-editor-v2.0.0.zip"),
        )
        errors = "\n".join(validate_catalog_inputs(ROOT, self.legacy_inputs, REGISTRY))
        self.assertTrue(
            any("payload" in error.lower() or "version" in error.lower() for error in errors.splitlines()),
            errors,
        )
        with self.assertRaises(ReleaseError):
            build_catalog(ROOT, self.legacy_inputs, self.output_one)
        self.assertEqual(list(self.output_one.iterdir()), [])

    def test_catalog_build_rejects_missing_zip_without_reading_current_skills(self) -> None:
        (self.legacy_inputs / "image-workbench-v2.0.0.zip").unlink()
        with self.assertRaises(ReleaseError) as raised:
            build_catalog(ROOT, self.legacy_inputs, self.output_one)
        self.assertIn("missing archive: image-workbench-v2.0.0.zip", str(raised.exception))
        self.assertEqual(list(self.output_one.iterdir()), [])

    def test_verify_catalog_download_accepts_built_legacy_catalog(self) -> None:
        build_catalog(ROOT, self.legacy_inputs, self.output_one)
        self.assertEqual(verify_catalog_download(ROOT, self.output_one), [])

    def test_verify_catalog_download_rejects_plugin_members_not_equal_to_lock(self) -> None:
        archive, _checksums = build_catalog(ROOT, self.legacy_inputs, self.output_one)

        def add_extra_product(items):
            yield from items
            info = zipfile.ZipInfo("skills/extra-product/SKILL.md")
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            yield info, b"---\nname: extra-product\n---\n"

        _rewrite_zip(archive, add_extra_product)
        write_checksums((archive,), self.output_one / "SHA256SUMS")
        errors = "\n".join(verify_catalog_download(ROOT, self.output_one))
        self.assertTrue(
            any(
                "lock" in error.lower() or "extra-product" in error.lower()
                for error in errors.splitlines()
            ),
            errors,
        )

    def test_verify_catalog_download_rejects_non_byte_equivalent_standalone_payload(self) -> None:
        archive, _checksums = build_catalog(ROOT, self.legacy_inputs, self.output_one)

        def tamper(items):
            for info, data in items:
                if info.filename == "skills/korean-writing-editor/SKILL.md":
                    data = data + b"\n"
                yield info, data

        _rewrite_zip(archive, tamper)
        write_checksums((archive,), self.output_one / "SHA256SUMS")
        errors = "\n".join(verify_catalog_download(ROOT, self.output_one))
        self.assertTrue(
            any(
                "byte-equivalent" in error.lower() or "payload" in error.lower()
                for error in errors.splitlines()
            ),
            errors,
        )


class CatalogSchemaInputTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tempdir = tempfile.TemporaryDirectory()
        self.workspace = Path(self._tempdir.name)

    def tearDown(self) -> None:
        self._tempdir.cleanup()

    def _catalog_root(
        self,
        *,
        skills: list[dict[str, object]],
        version: str = "2.0.0",
    ) -> Path:
        root = self.workspace / "root"
        catalog = root / "catalog"
        (catalog / "plugin" / ".codex-plugin").mkdir(parents=True)
        (root / "LICENSE").write_text("Apache License\nVersion 2.0\n", encoding="utf-8")
        (root / "NOTICE").write_text("Copyright\n", encoding="utf-8")
        (catalog / "release.toml").write_text(
            "\n".join(
                [
                    "schema_version = 1",
                    'name = "beyondwin-skills"',
                    f'version = "{version}"',
                    'tag_prefix = "beyondwin-skills-v"',
                    "",
                ]
            ),
            encoding="utf-8",
        )
        _write_json(
            catalog / "plugin" / ".codex-plugin" / "plugin.json",
            {"name": "beyondwin-skills", "version": version, "skills": "./skills/"},
        )
        _write_json(catalog / "catalog.lock.json", {"schema_version": 1, "skills": skills})
        return root

    def test_catalog_inputs_reject_legacy_bundle_extra_product(self) -> None:
        extra = {
            "name": "extra-product",
            "version": "2.0.0",
            "tag": "v2.0.0",
            "release_kind": "legacy-bundle",
            "source_commit": PINNED_SOURCE_COMMIT,
            "payload_sha256": HASH_C,
        }
        image = {
            "name": "image-workbench",
            "version": "2.0.0",
            "tag": "v2.0.0",
            "release_kind": "legacy-bundle",
            "source_commit": PINNED_SOURCE_COMMIT,
            "payload_sha256": HASH_A,
        }
        korean = {
            "name": "korean-writing-editor",
            "version": "2.0.0",
            "tag": "v2.0.0",
            "release_kind": "legacy-bundle",
            "source_commit": PINNED_SOURCE_COMMIT,
            "payload_sha256": HASH_B,
        }
        root = self._catalog_root(skills=[extra, image, korean])
        input_dir = self.workspace / "inputs"
        input_dir.mkdir()
        (input_dir / "SHA256SUMS").write_text("", encoding="ascii")
        errors = "\n".join(validate_catalog_inputs(root, input_dir, REGISTRY))
        self.assertIn("legacy-bundle", errors)
        self.assertIn("extra-product", errors)


class CatalogIndependentFixtureTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tempdir = tempfile.TemporaryDirectory()
        self.workspace = Path(self._tempdir.name)

    def tearDown(self) -> None:
        self._tempdir.cleanup()

    def _independent_root(self, archive: Path, *, tag: str = "how-it-works-v1.0.0") -> Path:
        with tempfile.TemporaryDirectory() as directory:
            extracted = Path(directory)
            errors = extract_archive(archive, extracted)
            if errors:
                raise RuntimeError("\n".join(errors))
            digest = payload_sha256(extracted / "how-it-works")
        root = self.workspace / "root"
        catalog = root / "catalog"
        (catalog / "plugin" / ".codex-plugin").mkdir(parents=True)
        shutil.copy2(ROOT / "LICENSE", root / "LICENSE")
        shutil.copy2(ROOT / "NOTICE", root / "NOTICE")
        (catalog / "release.toml").write_text(
            "\n".join(
                [
                    "schema_version = 1",
                    'name = "beyondwin-skills"',
                    'version = "2.1.0"',
                    'tag_prefix = "beyondwin-skills-v"',
                    "",
                ]
            ),
            encoding="utf-8",
        )
        _write_json(
            catalog / "plugin" / ".codex-plugin" / "plugin.json",
            {"name": "beyondwin-skills", "version": "2.1.0", "skills": "./skills/"},
        )
        _write_json(
            catalog / "catalog.lock.json",
            {
                "schema_version": 1,
                "skills": [
                    {
                        "name": "how-it-works",
                        "version": "1.0.0",
                        "tag": tag,
                        "release_kind": "independent",
                        "source_commit": COMMIT_C,
                        "payload_sha256": digest,
                    }
                ],
            },
        )
        return root

    def _independent_inputs(self, archive: Path) -> Path:
        inputs = self.workspace / "inputs"
        inputs.mkdir()
        shutil.copy2(archive, inputs / archive.name)
        write_checksums((inputs / archive.name,), inputs / "SHA256SUMS")
        return inputs

    def test_independent_catalog_build_and_download_verify(self) -> None:
        product_dir = self.workspace / "product"
        product_dir.mkdir()
        archive, _checksums = release.build_product(
            ROOT, "how-it-works", product_dir, require_release_entry=False
        )
        root = self._independent_root(archive)
        inputs = self._independent_inputs(archive)
        self.assertEqual(validate_catalog_inputs(root, inputs, REGISTRY), [])
        output = self.workspace / "output"
        output.mkdir()
        artifacts = build_catalog(root, inputs, output)
        self.assertEqual(
            {path.name for path in artifacts},
            {"beyondwin-skills-v2.1.0.zip", "SHA256SUMS"},
        )
        names = zip_names(output / "beyondwin-skills-v2.1.0.zip")
        self.assertIn("skills/how-it-works/release.toml", names)
        self.assertIn(".codex-plugin/plugin.json", names)
        self.assertEqual(verify_catalog_download(root, output), [])

    def test_independent_inputs_reject_missing_release_toml(self) -> None:
        product_dir = self.workspace / "product"
        product_dir.mkdir()
        archive, _checksums = release.build_product(
            ROOT, "how-it-works", product_dir, require_release_entry=False
        )

        def drop_release(items):
            for info, data in items:
                if info.filename == "how-it-works/release.toml":
                    continue
                yield info, data

        _rewrite_zip(archive, drop_release)
        root = self._independent_root(archive)
        inputs = self._independent_inputs(archive)
        errors = "\n".join(validate_catalog_inputs(root, inputs, REGISTRY))
        self.assertIn("release.toml", errors)

    def test_independent_inputs_reject_non_product_qualified_tag(self) -> None:
        product_dir = self.workspace / "product"
        product_dir.mkdir()
        archive, _checksums = release.build_product(
            ROOT, "how-it-works", product_dir, require_release_entry=False
        )
        root = self._independent_root(archive, tag="v1.0.0")
        inputs = self._independent_inputs(archive)
        errors = "\n".join(validate_catalog_inputs(root, inputs, REGISTRY))
        self.assertIn("how-it-works-v1.0.0", errors)


class CatalogCLITests(unittest.TestCase):
    def setUp(self) -> None:
        self._tempdir = tempfile.TemporaryDirectory()
        root = Path(self._tempdir.name)
        self.legacy_inputs = root / "inputs"
        self.output = root / "output"
        self.legacy_inputs.mkdir()
        self.output.mkdir()
        _populate_legacy_inputs(ROOT, self.legacy_inputs)

    def tearDown(self) -> None:
        self._tempdir.cleanup()

    def test_product_and_catalog_selectors_are_mutually_exclusive(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "check",
                "--product",
                "how-it-works",
                "--catalog",
                "--input",
                str(self.legacy_inputs),
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(completed.returncode, 0)

    def test_check_catalog_requires_input(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "check", "--catalog"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(completed.returncode, 0)

    def test_build_catalog_requires_input_and_output(self) -> None:
        missing_input = subprocess.run(
            [sys.executable, str(SCRIPT), "build", "--catalog", "--output", str(self.output)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(missing_input.returncode, 0)
        missing_output = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "build",
                "--catalog",
                "--input",
                str(self.legacy_inputs),
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(missing_output.returncode, 0)


if __name__ == "__main__":
    unittest.main()
