from __future__ import annotations

import contextlib
import dataclasses
import io
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.change_routing import (  # noqa: E402
    changed_paths,
    full_repository_matrix,
    matrix_for_event,
    matrix_for_targets,
    serialize_matrix,
    targets_for_paths,
)
from scripts.lib.product_registry import load_registry  # noqa: E402


def run_git(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def init_repository(root: Path) -> None:
    run_git(root, "init", "-b", "main")
    run_git(root, "config", "user.email", "changed-targets@example.com")
    run_git(root, "config", "user.name", "Changed Targets")
    run_git(root, "config", "commit.gpgsign", "false")


class RegistryRoutingTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = load_registry(ROOT / "products.toml")
        cls.all_targets = ("catalog", *cls.registry.names)


class TargetMappingTests(RegistryRoutingTestCase):
    def test_each_owned_path_routes_to_its_product(self) -> None:
        for product in self.registry.products:
            for prefix in product.owned_paths:
                changed = f"{prefix.as_posix().rstrip('/')}/probe.txt"
                self.assertEqual(targets_for_paths([changed], self.registry), (product.name,))

    def test_windows_separator_routes_to_product(self) -> None:
        self.assertEqual(
            targets_for_paths([r"tests\\products\\how-it-works\\cases.json"], self.registry),
            ("how-it-works",),
        )

    def test_unmatched_path_selects_full_matrix(self) -> None:
        self.assertEqual(targets_for_paths(["products.toml"], self.registry), ("catalog", *self.registry.names))

    def test_product_path_selects_only_that_product(self) -> None:
        self.assertEqual(targets_for_paths(["skills/how-it-works/SKILL.md"], self.registry), ("how-it-works",))

    def test_shared_release_code_selects_every_target(self) -> None:
        self.assertEqual(
            targets_for_paths(["scripts/release_archive.py"], self.registry),
            self.all_targets,
        )

    def test_unknown_path_fails_safe_to_every_target(self) -> None:
        self.assertEqual(
            targets_for_paths(["unexpected/new-surface.txt"], self.registry),
            self.all_targets,
        )

    def test_product_docs_and_tests_select_that_product(self) -> None:
        self.assertEqual(
            targets_for_paths(["docs/maintainers/products/how-it-works/contract.md"], self.registry),
            ("how-it-works",),
        )
        self.assertEqual(
            targets_for_paths(["tests/products/how-it-works/cases.json"], self.registry),
            ("how-it-works",),
        )
        self.assertEqual(
            targets_for_paths(["tests/products/how-it-works/test_contract.py"], self.registry),
            ("how-it-works",),
        )
        self.assertEqual(
            targets_for_paths(
                ["docs/maintainers/products/image-workbench/testing.md"],
                self.registry,
            ),
            ("image-workbench",),
        )
        self.assertEqual(
            targets_for_paths(["tests/products/image-workbench/run.py"], self.registry),
            ("image-workbench",),
        )
        self.assertEqual(
            targets_for_paths(
                ["docs/maintainers/products/korean-writing-editor/release.md"],
                self.registry,
            ),
            ("korean-writing-editor",),
        )
        self.assertEqual(
            targets_for_paths(
                ["tests/products/korean-writing-editor/offline/cases.json"],
                self.registry,
            ),
            ("korean-writing-editor",),
        )
        self.assertEqual(
            targets_for_paths(
                ["tests/products/korean-writing-editor/test_package.py"],
                self.registry,
            ),
            ("korean-writing-editor",),
        )

    def test_catalog_path_selects_catalog(self) -> None:
        self.assertEqual(targets_for_paths(["catalog/release.toml"], self.registry), ("catalog",))
        self.assertEqual(
            targets_for_paths(["catalog/plugin/.codex-plugin/plugin.json"], self.registry),
            ("catalog",),
        )

    def test_shared_public_docs_select_every_target(self) -> None:
        for path in (
            "README.md",
            "README.en.md",
            "docs/users/en/installation.md",
            "docs/users/ko/verification.md",
            "docs/maintainers/README.md",
            "docs/maintainers/repository/architecture.md",
        ):
            self.assertEqual(targets_for_paths([path], self.registry), self.all_targets, path)

    def test_license_notice_and_workflow_files_select_every_target(self) -> None:
        for path in (
            "LICENSE",
            "NOTICE",
            ".github/workflows/verify.yml",
            "tests/repository/test_community_and_ci.py",
            "scripts/changed_targets.py",
        ):
            self.assertEqual(targets_for_paths([path], self.registry), self.all_targets, path)

    def test_empty_diff_selects_every_target(self) -> None:
        self.assertEqual(targets_for_paths([], self.registry), self.all_targets)
        self.assertEqual(targets_for_paths((), self.registry), self.all_targets)

    def test_windows_paths_are_normalized(self) -> None:
        self.assertEqual(
            targets_for_paths(["skills\\how-it-works\\SKILL.md"], self.registry),
            ("how-it-works",),
        )

    def test_multiple_product_paths_union_in_deterministic_order(self) -> None:
        self.assertEqual(
            targets_for_paths(
                [
                    "skills/korean-writing-editor/SKILL.md",
                    "catalog/README.md",
                    "skills/how-it-works/SKILL.md",
                ],
                self.registry,
            ),
            ("catalog", "korean-writing-editor", "how-it-works"),
        )

    def test_product_plus_unknown_fails_safe_to_every_target(self) -> None:
        self.assertEqual(
            targets_for_paths(["skills/how-it-works/SKILL.md", "unexpected.txt"], self.registry),
            self.all_targets,
        )

    def test_all_targets_follow_catalog_then_registry_order(self) -> None:
        self.assertEqual(self.all_targets, ("catalog", *self.registry.names))
        self.assertEqual(
            self.registry.names,
            (
                "korean-writing-editor",
                "image-workbench",
                "how-it-works",
                "pre-sdd-review",
            ),
        )

    def test_routing_follows_replaced_owned_paths(self) -> None:
        original = self.registry.require("how-it-works")
        replaced = dataclasses.replace(
            original,
            owned_paths=(pathlib.PurePosixPath("alternate/how-it-works"),),
        )
        registry = dataclasses.replace(
            self.registry,
            products=tuple(
                replaced if product.name == "how-it-works" else product
                for product in self.registry.products
            ),
        )
        self.assertEqual(
            targets_for_paths(["alternate/how-it-works/SKILL.md"], registry),
            ("how-it-works",),
        )
        self.assertEqual(
            targets_for_paths(["skills/how-it-works/SKILL.md"], registry),
            ("catalog", *registry.names),
        )


class MatrixSerializationTests(RegistryRoutingTestCase):
    def test_each_target_runs_ubuntu_macos_full_and_windows_portable(self) -> None:
        matrix = matrix_for_targets(["how-it-works"], self.registry)
        rows = matrix["include"]
        self.assertEqual(
            [(row["os"], row["profile"], row["selector"], row["target"]) for row in rows],
            [
                ("ubuntu-latest", "full", "--skill how-it-works", "how-it-works"),
                ("macos-latest", "full", "--skill how-it-works", "how-it-works"),
                ("windows-latest", "windows-portable", "--skill how-it-works", "how-it-works"),
            ],
        )

    def test_windows_rows_cover_every_selected_target(self) -> None:
        matrix = matrix_for_targets(self.all_targets, self.registry)
        windows = [row for row in matrix["include"] if row["os"] == "windows-latest"]
        self.assertEqual(
            [(row["target"], row["profile"], row["selector"]) for row in windows],
            [
                ("catalog", "windows-portable", "--catalog"),
                ("korean-writing-editor", "windows-portable", "--skill korean-writing-editor"),
                ("image-workbench", "windows-portable", "--skill image-workbench"),
                ("how-it-works", "windows-portable", "--skill how-it-works"),
                ("pre-sdd-review", "windows-portable", "--skill pre-sdd-review"),
            ],
        )

    def test_matrix_rows_follow_targets_order_not_input_order(self) -> None:
        matrix = matrix_for_targets(("korean-writing-editor", "catalog"), self.registry)
        self.assertEqual(
            [row["target"] for row in matrix["include"]],
            ["catalog"] * 3 + ["korean-writing-editor"] * 3,
        )

    def test_selectors_are_fixed_strings(self) -> None:
        by_target = {
            row["target"]: row["selector"]
            for row in matrix_for_targets(self.all_targets, self.registry)["include"]
        }
        expected = {"catalog": "--catalog"}
        expected.update({name: f"--skill {name}" for name in self.registry.names})
        self.assertEqual(by_target, expected)

    def test_json_serialization_is_canonical_and_compact(self) -> None:
        matrix = matrix_for_targets(["catalog", "how-it-works"], self.registry)
        encoded = serialize_matrix(matrix)
        self.assertEqual(
            encoded,
            json.dumps(matrix, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        )
        self.assertNotIn(": ", encoded)
        self.assertNotIn(", ", encoded)
        self.assertNotIn("\n", encoded)
        self.assertEqual(json.loads(encoded), matrix)
        self.assertTrue(encoded.startswith('{"include":['))

    def test_full_repository_matrix_is_three_unselected_os_rows(self) -> None:
        matrix = full_repository_matrix()
        self.assertEqual(
            [(row["os"], row["profile"], row.get("selector", ""), row.get("target")) for row in matrix["include"]],
            [
                ("ubuntu-latest", "full", "", None),
                ("macos-latest", "full", "", None),
                ("windows-latest", "windows-portable", "", None),
            ],
        )
        for row in matrix["include"]:
            self.assertNotIn("target", row)
            self.assertEqual(row["selector"], "")

    def test_push_and_dispatch_events_use_full_repository_matrix(self) -> None:
        expected = full_repository_matrix()
        for event in ("push", "workflow_dispatch"):
            self.assertEqual(matrix_for_event(event, ROOT, self.registry), expected, event)

    def test_unknown_event_selects_every_target_row(self) -> None:
        self.assertEqual(
            matrix_for_event("schedule", ROOT, self.registry),
            matrix_for_targets(self.all_targets, self.registry),
        )


class ChangedPathAndCliTests(RegistryRoutingTestCase):
    def test_changed_paths_lists_posix_paths_between_revisions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            init_repository(repository)
            first = repository / "skills" / "how-it-works" / "SKILL.md"
            first.parent.mkdir(parents=True)
            first.write_text("one\n", encoding="utf-8")
            (repository / "LICENSE").write_text("license\n", encoding="utf-8")
            run_git(repository, "add", "-A")
            run_git(repository, "commit", "-m", "base")
            base = run_git(repository, "rev-parse", "HEAD")
            first.write_text("two\n", encoding="utf-8")
            extra = repository / "catalog" / "release.toml"
            extra.parent.mkdir(parents=True)
            extra.write_text("name = 'catalog'\n", encoding="utf-8")
            run_git(repository, "add", "-A")
            run_git(repository, "commit", "-m", "head")
            head = run_git(repository, "rev-parse", "HEAD")
            self.assertEqual(
                tuple(sorted(changed_paths(repository, base, head))),
                ("catalog/release.toml", "skills/how-it-works/SKILL.md"),
            )

    def test_empty_git_diff_is_empty_path_list(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            init_repository(repository)
            (repository / "README.md").write_text("seed\n", encoding="utf-8")
            run_git(repository, "add", "-A")
            run_git(repository, "commit", "-m", "seed")
            sha = run_git(repository, "rev-parse", "HEAD")
            self.assertEqual(changed_paths(repository, sha, sha), ())

    def test_cli_writes_compact_full_matrix_for_main_and_dispatch(self) -> None:
        script = ROOT / "scripts" / "changed_targets.py"
        for event in ("push", "workflow_dispatch"):
            with tempfile.TemporaryDirectory() as directory:
                output = Path(directory) / "github-output"
                env = os.environ.copy()
                env["GITHUB_OUTPUT"] = str(output)
                completed = subprocess.run(
                    [sys.executable, str(script), "--event", event],
                    check=True,
                    capture_output=True,
                    text=True,
                    env=env,
                    cwd=ROOT,
                )
                self.assertEqual(completed.returncode, 0)
                line = output.read_text(encoding="utf-8").splitlines()[0]
                self.assertTrue(line.startswith("matrix="))
                payload = line.split("=", 1)[1]
                self.assertEqual(payload, serialize_matrix(full_repository_matrix()))
                matrix = json.loads(payload)
                self.assertEqual(len(matrix["include"]), 3)
                self.assertTrue(all(row["selector"] == "" for row in matrix["include"]))

    def test_cli_writes_pr_matrix_from_changed_paths(self) -> None:
        script = ROOT / "scripts" / "changed_targets.py"
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory) / "repo"
            repository.mkdir()
            init_repository(repository)
            skill = repository / "skills" / "image-workbench" / "SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text("one\n", encoding="utf-8")
            run_git(repository, "add", "-A")
            run_git(repository, "commit", "-m", "base")
            base = run_git(repository, "rev-parse", "HEAD")
            skill.write_text("two\n", encoding="utf-8")
            run_git(repository, "add", "-A")
            run_git(repository, "commit", "-m", "head")
            head = run_git(repository, "rev-parse", "HEAD")
            output = Path(directory) / "github-output"
            env = os.environ.copy()
            env["GITHUB_OUTPUT"] = str(output)
            subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--event",
                    "pull_request",
                    "--root",
                    str(repository),
                    "--base",
                    base,
                    "--head",
                    head,
                ],
                check=True,
                capture_output=True,
                text=True,
                env=env,
                cwd=ROOT,
            )
            payload = output.read_text(encoding="utf-8").splitlines()[0].split("=", 1)[1]
            self.assertEqual(
                payload,
                serialize_matrix(matrix_for_targets(("image-workbench",), self.registry)),
            )
            matrix = json.loads(payload)
            self.assertEqual({row["target"] for row in matrix["include"]}, {"image-workbench"})
            self.assertEqual(len(matrix["include"]), 3)

    def test_cli_returns_nonzero_on_registry_errors(self) -> None:
        import scripts.changed_targets as module

        original = getattr(module, "validate_registry", None)

        def fake_validate(*args: object, **kwargs: object) -> list[str]:
            return ["broken registry"]

        module.validate_registry = fake_validate  # type: ignore[method-assign]
        stderr = io.StringIO()
        try:
            with contextlib.redirect_stderr(stderr):
                code = module.main(["--event", "push"])
        finally:
            if original is None:
                delattr(module, "validate_registry")
            else:
                module.validate_registry = original
        self.assertEqual(code, 1)
        self.assertIn("broken registry", stderr.getvalue())

    def test_cli_has_no_hard_coded_product_path_tables(self) -> None:
        source = (ROOT / "scripts" / "changed_targets.py").read_text(encoding="utf-8")
        self.assertNotIn("PRODUCT_PREFIXES", source)
        self.assertNotIn("PRODUCT_EXACT_PATHS", source)
        routing = (ROOT / "scripts" / "lib" / "change_routing.py").read_text(encoding="utf-8")
        self.assertNotIn("PRODUCT_PREFIXES", routing)
        self.assertNotIn("PRODUCT_EXACT_PATHS", routing)
        self.assertNotIn("skills/how-it-works/", routing)


if __name__ == "__main__":
    unittest.main()
