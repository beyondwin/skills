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

from scripts.lib.product_registry import (  # noqa: E402
    load_registry,
    normalize_repo_path,
    validate_registry,
)


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
            ("korean-writing-editor", "image-workbench", "graspic"),
        )

    def test_registry_contains_no_version_or_command_fields(self) -> None:
        raw = tomllib.loads((ROOT / "products.toml").read_text(encoding="utf-8"))
        for product in raw["products"]:
            self.assertNotIn("version", product)
            self.assertNotIn("tag_prefix", product)
            self.assertNotIn("command", product)

    def test_windows_paths_are_normalized(self) -> None:
        self.assertEqual(
            normalize_repo_path(r"tests\\products\\graspic\\cases.json"),
            "tests/products/graspic/cases.json",
        )

    def test_require_returns_the_named_product(self) -> None:
        product = load_registry(ROOT / "products.toml").require("graspic")
        self.assertEqual(product.name, "graspic")
        self.assertEqual(product.display_name, "graspic")
        self.assertEqual(product.skill_path, pathlib.PurePosixPath("skills/graspic"))
        self.assertEqual(product.test_path, pathlib.PurePosixPath("tests/products/graspic"))
        self.assertEqual(
            product.maintainer_docs,
            pathlib.PurePosixPath("docs/maintainers/products/graspic"),
        )
        self.assertEqual(product.supported_hosts, ("codex",))
        self.assertEqual(
            product.owned_paths,
            (
                pathlib.PurePosixPath("skills/graspic"),
                pathlib.PurePosixPath("tests/products/graspic"),
                pathlib.PurePosixPath("docs/maintainers/products/graspic"),
            ),
        )
        self.assertEqual(
            product.verify_stages,
            ("product-contract", "graspic-contract", "python-compile"),
        )

    def test_registry_types_are_frozen(self) -> None:
        registry = load_registry(ROOT / "products.toml")
        with self.assertRaises(dataclasses.FrozenInstanceError):
            registry.schema_version = 2  # type: ignore[misc]
        with self.assertRaises(dataclasses.FrozenInstanceError):
            registry.products[0].name = "renamed"  # type: ignore[misc]


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

    def _declared_stages(self) -> set[str]:
        return {
            stage
            for product in self.registry.products
            for stage in product.verify_stages
        }

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
            validate_registry(ROOT, registry, self._declared_stages()),
            [],
        )

    def test_validate_registry_reports_missing_directories(self) -> None:
        registry = load_registry(ROOT / "products.toml")
        with tempfile.TemporaryDirectory() as directory:
            errors = validate_registry(
                Path(directory),
                registry,
                self._declared_stages(),
            )
        joined = "\n".join(errors)
        self.assertTrue(errors)
        self.assertIn("korean-writing-editor", joined)
        self.assertIn("missing", joined)
