from __future__ import annotations

import dataclasses
import pathlib
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.documentation import (  # noqa: E402
    active_markdown_paths,
)
from scripts.lib.product_registry import (  # noqa: E402
    load_registry,
    normalize_repo_path,
    validate_registry,
)
from scripts.lib.verification import REGISTERED_STAGE_NAMES  # noqa: E402


def _product(
    name: str = "sample-product",
    *,
    extra: str = "",
    omit: frozenset[str] = frozenset(),
    **fields: str,
) -> str:
    values = {
        "name": f'"{name}"',
        "display_name": '"Sample Product"',
        "skill_path": f'"skills/{name}"',
        "test_path": f'"tests/{name}"',
        "maintainer_docs": f'"docs/maintainers/{name}"',
        "supported_hosts": '["codex"]',
        "owned_paths": (
            "[\n"
            f'  "skills/{name}/",\n'
            f'  "tests/{name}/",\n'
            f'  "docs/maintainers/{name}/",\n'
            "]"
        ),
        "verify_stages": '["product-contract"]',
    }
    values.update(fields)
    lines = ["[[products]]"]
    for key in (
        "name",
        "display_name",
        "skill_path",
        "test_path",
        "maintainer_docs",
        "supported_hosts",
        "owned_paths",
        "verify_stages",
    ):
        if key in omit:
            continue
        lines.append(f"{key} = {values[key]}")
    if extra:
        lines.append(extra)
    return "\n".join(lines) + "\n"


def _registry(*products: str, schema_version: int = 1) -> str:
    return f"schema_version = {schema_version}\n\n" + "\n".join(products)


class RegistryParsingTests(unittest.TestCase):
    def test_repository_registry_preserves_product_order(self) -> None:
        registry = load_registry(ROOT / "products.toml")
        self.assertEqual(
            registry.names,
            (
                "korean-writing-editor",
                "image-workbench",
                "how-it-works",
                "pre-sdd-review",
            ),
        )

    def test_explanation_product_has_measured_supported_hosts(self) -> None:
        product = load_registry(ROOT / "products.toml").require("how-it-works")
        self.assertEqual(product.display_name, "How It Works")
        self.assertEqual(product.supported_hosts, ("codex", "claude-code"))

    def test_registry_contains_no_version_or_command_fields(self) -> None:
        raw = tomllib.loads((ROOT / "products.toml").read_text(encoding="utf-8"))
        for product in raw["products"]:
            self.assertNotIn("version", product)
            self.assertNotIn("tag_prefix", product)
            self.assertNotIn("command", product)

    def test_windows_paths_are_normalized(self) -> None:
        self.assertEqual(
            normalize_repo_path(r"tests\\products\\how-it-works\\cases.json"),
            "tests/products/how-it-works/cases.json",
        )

    def test_leading_dot_github_path_is_preserved(self) -> None:
        self.assertEqual(
            normalize_repo_path(".github/workflows/verify.yml"),
            ".github/workflows/verify.yml",
        )
        self.assertEqual(normalize_repo_path("./scripts/lib/archive.py"), "scripts/lib/archive.py")

    def test_require_returns_the_named_product(self) -> None:
        product = load_registry(ROOT / "products.toml").require("how-it-works")
        self.assertEqual(product.name, "how-it-works")
        self.assertEqual(product.display_name, "How It Works")
        self.assertEqual(product.skill_path, pathlib.PurePosixPath("skills/how-it-works"))
        self.assertEqual(product.test_path, pathlib.PurePosixPath("tests/products/how-it-works"))
        self.assertEqual(
            product.maintainer_docs,
            pathlib.PurePosixPath("docs/maintainers/products/how-it-works"),
        )
        self.assertEqual(product.supported_hosts, ("codex", "claude-code"))
        self.assertEqual(
            product.owned_paths,
            (
                pathlib.PurePosixPath("skills/how-it-works"),
                pathlib.PurePosixPath("tests/products/how-it-works"),
                pathlib.PurePosixPath("docs/maintainers/products/how-it-works"),
            ),
        )
        self.assertEqual(
            product.verify_stages,
            ("product-contract", "how-it-works-contract", "python-compile"),
        )

    def test_registry_types_are_frozen(self) -> None:
        registry = load_registry(ROOT / "products.toml")
        with self.assertRaises(dataclasses.FrozenInstanceError):
            registry.schema_version = 2  # type: ignore[misc]
        with self.assertRaises(dataclasses.FrozenInstanceError):
            registry.products[0].name = "renamed"  # type: ignore[misc]


class ProductRegistryTests(unittest.TestCase):
    def test_pre_sdd_review_is_codex_only(self) -> None:
        product = load_registry(ROOT / "products.toml").require("pre-sdd-review")
        self.assertEqual(product.display_name, "Pre-SDD Review")
        self.assertEqual(product.supported_hosts, ("codex",))
        self.assertEqual(
            product.verify_stages,
            ("product-contract", "pre-sdd-review-contract", "pre-sdd-review-evidence", "python-compile"),
        )


class RegistryRejectionTests(unittest.TestCase):
    def _reject(self, contents: str, fragment: str) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "products.toml"
            path.write_text(contents, encoding="utf-8")
            with self.assertRaises(ValueError) as raised:
                load_registry(path)
            self.assertIn(fragment, str(raised.exception))

    def test_malformed_registry_is_rejected(self) -> None:
        cases = (
            (
                "duplicate product name",
                _registry(
                    _product("sample-product"),
                    _product("sample-product", display_name='"Copy"'),
                ),
                "duplicate product name",
            ),
            (
                "duplicate skill_path",
                _registry(
                    _product("sample-product"),
                    _product(
                        "other-product",
                        skill_path='"skills/sample-product"',
                    ),
                ),
                "duplicate skill_path",
            ),
            (
                "duplicate owned paths",
                _registry(
                    _product("sample-product"),
                    _product(
                        "other-product",
                        owned_paths=(
                            "[\n"
                            '  "skills/other-product/",\n'
                            '  "tests/sample-product/",\n'
                            '  "docs/maintainers/other-product/",\n'
                            "]"
                        ),
                    ),
                ),
                "duplicate owned path",
            ),
            (
                "unknown hosts",
                _registry(_product(supported_hosts='["codex", "warp"]')),
                "unknown host",
            ),
            (
                "absolute paths",
                _registry(
                    _product(skill_path='"/tmp/skills/sample-product"'),
                ),
                "path must be repository-relative",
            ),
            (
                "parent traversal",
                _registry(
                    _product(skill_path='"skills/../secrets/sample-product"'),
                ),
                "path must be repository-relative",
            ),
            (
                "wrong types",
                _registry(_product(supported_hosts='"codex"')),
                "supported_hosts",
            ),
            (
                "non-string list items",
                _registry(_product(supported_hosts='["codex", 1]')),
                "supported_hosts",
            ),
            (
                "extra keys",
                _registry(_product(extra='version = "1.0.0"')),
                "version",
            ),
            (
                "missing keys",
                _registry(_product(omit=frozenset({"display_name"}))),
                "display_name",
            ),
            (
                "non-schema-1",
                _registry(_product(), schema_version=2),
                "schema_version",
            ),
            (
                "malformed product name",
                _registry(_product("Sample_Product")),
                "name",
            ),
            (
                "owned path without trailing slash",
                _registry(
                    _product(
                        owned_paths=(
                            "[\n"
                            '  "skills/sample-product",\n'
                            '  "tests/sample-product/",\n'
                            '  "docs/maintainers/sample-product/",\n'
                            "]"
                        )
                    )
                ),
                "owned_paths",
            ),
        )
        for label, contents, fragment in cases:
            with self.subTest(label=label):
                self._reject(contents, fragment)

    def test_rejection_messages_name_the_field_and_product(self) -> None:
        self._reject(
            _registry(_product(extra='command = "true"')),
            "sample-product",
        )
        self._reject(
            _registry(_product(extra='command = "true"')),
            "command",
        )
        self._reject(
            _registry(_product(supported_hosts='["warp"]')),
            "sample-product",
        )


class RegistryValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = load_registry(ROOT / "products.toml")

    def test_registry_exactly_covers_product_directories(self) -> None:
        registry = load_registry(ROOT / "products.toml")
        self.assertEqual(
            {path.name for path in (ROOT / "skills").iterdir() if path.is_dir()},
            set(registry.names),
        )
        self.assertEqual(
            {path.name for path in (ROOT / "tests/products").iterdir() if path.is_dir()},
            set(registry.names),
        )
        self.assertEqual(
            {path.name for path in (ROOT / "docs/maintainers/products").iterdir() if path.is_dir()},
            set(registry.names),
        )

    def test_each_product_has_four_maintainer_guides(self) -> None:
        expected = {"contract.md", "testing.md", "compatibility.md", "release.md"}
        for product in self.registry.products:
            actual = {path.name for path in (ROOT / product.maintainer_docs).glob("*.md")}
            self.assertEqual(actual, expected, product.name)

    def test_current_registry_has_no_validation_errors(self) -> None:
        registry = load_registry(ROOT / "products.toml")
        self.assertEqual(
            validate_registry(ROOT, registry, REGISTERED_STAGE_NAMES),
            [],
        )

    def test_unknown_registry_stage_fails_validation(self) -> None:
        broken = dataclasses.replace(
            self.registry,
            products=(dataclasses.replace(self.registry.products[0], verify_stages=("missing-stage",)),) + self.registry.products[1:],
        )
        self.assertIn("unknown verification stage: missing-stage", validate_registry(ROOT, broken, REGISTERED_STAGE_NAMES))

    def test_validate_registry_reports_missing_directories(self) -> None:
        registry = load_registry(ROOT / "products.toml")
        with tempfile.TemporaryDirectory() as directory:
            errors = validate_registry(
                Path(directory),
                registry,
                REGISTERED_STAGE_NAMES,
            )
        joined = "\n".join(errors)
        self.assertTrue(errors)
        self.assertIn("korean-writing-editor", joined)
        self.assertIn("missing", joined)


class RegistryDocumentationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = load_registry(ROOT / "products.toml")

    def test_active_markdown_paths_include_registered_product_docs(self) -> None:
        paths = {path.relative_to(ROOT).as_posix() for path in active_markdown_paths(ROOT)}
        for product in self.registry.products:
            self.assertIn(f"{product.skill_path.as_posix()}/README.md", paths)
            self.assertIn(f"{product.skill_path.as_posix()}/README.en.md", paths)
            for filename in ("contract.md", "testing.md", "compatibility.md", "release.md"):
                self.assertIn(f"{product.maintainer_docs.as_posix()}/{filename}", paths, product.name)

    def test_active_markdown_paths_exclude_historical_records(self) -> None:
        extras = [
            path.relative_to(ROOT).as_posix()
            for path in active_markdown_paths(ROOT)
            if path.relative_to(ROOT).as_posix().startswith("docs/history/")
            and path.name != "README.md"
        ]
        self.assertEqual(extras, [])

    def test_korean_and_english_docs_share_registry_install_and_host_facts(self) -> None:
        github_root = "https://github.com/beyondwin/skills/tree/main"
        for product in self.registry.products:
            install = f"{github_root}/{product.skill_path.as_posix()}"
            maintainer = product.maintainer_docs.as_posix()
            for filename in ("README.md", "README.en.md"):
                text = (ROOT / product.skill_path / filename).read_text(encoding="utf-8")
                self.assertIn(product.name, text, filename)
                self.assertIn(install, text, filename)
                self.assertIn(maintainer, text, filename)
                for host in product.supported_hosts:
                    self.assertIn(host, text.lower(), f"{product.name}/{filename}")
            for language, readme in (("ko", "README.md"), ("en", "README.en.md")):
                for guide in (
                    "installation.md",
                    "compatibility.md",
                    "safety-and-privacy.md",
                    "verification.md",
                ):
                    text = (ROOT / "docs" / "users" / language / guide).read_text(
                        encoding="utf-8"
                    )
                    label = f"{language}/{guide}"
                    self.assertIn(product.name, text, label)
                    self.assertIn(f"{product.skill_path.as_posix()}/{readme}", text, label)
