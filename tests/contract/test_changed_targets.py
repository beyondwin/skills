from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.changed_targets import (  # noqa: E402
    TARGETS,
    changed_paths,
    full_repository_matrix,
    matrix_for_targets,
    serialize_matrix,
    targets_for_paths,
)


ALL_TARGETS = ("catalog", "graspic", "image-workbench", "korean-writing-editor")
OS_ROWS = (
    ("ubuntu-latest", "full"),
    ("macos-latest", "full"),
    ("windows-latest", "windows-portable"),
)
SELECTORS = {
    "catalog": "--catalog",
    "graspic": "--skill graspic",
    "image-workbench": "--skill image-workbench",
    "korean-writing-editor": "--skill korean-writing-editor",
}


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


class TargetMappingTests(unittest.TestCase):
    def test_product_path_selects_only_that_product(self) -> None:
        self.assertEqual(targets_for_paths(["skills/graspic/SKILL.md"]), ("graspic",))

    def test_shared_release_code_selects_every_target(self) -> None:
        self.assertEqual(
            targets_for_paths(["scripts/release_archive.py"]),
            ("catalog", "graspic", "image-workbench", "korean-writing-editor"),
        )

    def test_unknown_path_fails_safe_to_every_target(self) -> None:
        self.assertEqual(
            targets_for_paths(["unexpected/new-surface.txt"]),
            ("catalog", "graspic", "image-workbench", "korean-writing-editor"),
        )

    def test_product_docs_and_tests_select_that_product(self) -> None:
        self.assertEqual(
            targets_for_paths(["docs/maintainers/graspic/contract.md"]),
            ("graspic",),
        )
        self.assertEqual(targets_for_paths(["tests/graspic/cases.json"]), ("graspic",))
        self.assertEqual(
            targets_for_paths(["tests/contract/test_graspic.py"]),
            ("graspic",),
        )
        self.assertEqual(
            targets_for_paths(["docs/maintainers/image-workbench/testing.md"]),
            ("image-workbench",),
        )
        self.assertEqual(
            targets_for_paths(["tests/image-workbench/run.py"]),
            ("image-workbench",),
        )
        self.assertEqual(
            targets_for_paths(["docs/maintainers/korean-writing-editor/release.md"]),
            ("korean-writing-editor",),
        )
        self.assertEqual(
            targets_for_paths(["tests/korean-writing-editor/offline/cases.json"]),
            ("korean-writing-editor",),
        )
        self.assertEqual(
            targets_for_paths(["tests/contract/test_korean_package.py"]),
            ("korean-writing-editor",),
        )

    def test_catalog_path_selects_catalog(self) -> None:
        self.assertEqual(targets_for_paths(["catalog/release.toml"]), ("catalog",))
        self.assertEqual(
            targets_for_paths(["catalog/plugin/.codex-plugin/plugin.json"]),
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
            self.assertEqual(targets_for_paths([path]), ALL_TARGETS, path)

    def test_license_notice_and_workflow_files_select_every_target(self) -> None:
        for path in (
            "LICENSE",
            "NOTICE",
            ".github/workflows/verify.yml",
            "tests/contract/test_community_and_ci.py",
            "scripts/changed_targets.py",
        ):
            self.assertEqual(targets_for_paths([path]), ALL_TARGETS, path)

    def test_empty_diff_selects_every_target(self) -> None:
        self.assertEqual(targets_for_paths([]), ALL_TARGETS)
        self.assertEqual(targets_for_paths(()), ALL_TARGETS)

    def test_windows_paths_are_normalized(self) -> None:
        self.assertEqual(
            targets_for_paths(["skills\\graspic\\SKILL.md"]),
            ("graspic",),
        )

    def test_multiple_product_paths_union_in_deterministic_order(self) -> None:
        self.assertEqual(
            targets_for_paths(
                [
                    "skills/korean-writing-editor/SKILL.md",
                    "catalog/README.md",
                    "skills/graspic/SKILL.md",
                ]
            ),
            ("catalog", "graspic", "korean-writing-editor"),
        )

    def test_product_plus_unknown_fails_safe_to_every_target(self) -> None:
        self.assertEqual(
            targets_for_paths(["skills/graspic/SKILL.md", "unexpected.txt"]),
            ALL_TARGETS,
        )

    def test_targets_constant_order(self) -> None:
        self.assertEqual(TARGETS, ALL_TARGETS)


class MatrixSerializationTests(unittest.TestCase):
    def test_each_target_runs_ubuntu_macos_full_and_windows_portable(self) -> None:
        matrix = matrix_for_targets(["graspic"])
        rows = matrix["include"]
        self.assertEqual(
            [(row["os"], row["profile"], row["selector"], row["target"]) for row in rows],
            [
                ("ubuntu-latest", "full", "--skill graspic", "graspic"),
                ("macos-latest", "full", "--skill graspic", "graspic"),
                ("windows-latest", "windows-portable", "--skill graspic", "graspic"),
            ],
        )

    def test_windows_rows_cover_every_selected_target(self) -> None:
        matrix = matrix_for_targets(ALL_TARGETS)
        windows = [row for row in matrix["include"] if row["os"] == "windows-latest"]
        self.assertEqual(
            [(row["target"], row["profile"], row["selector"]) for row in windows],
            [
                ("catalog", "windows-portable", "--catalog"),
                ("graspic", "windows-portable", "--skill graspic"),
                ("image-workbench", "windows-portable", "--skill image-workbench"),
                ("korean-writing-editor", "windows-portable", "--skill korean-writing-editor"),
            ],
        )

    def test_matrix_rows_follow_targets_order_not_input_order(self) -> None:
        matrix = matrix_for_targets(("korean-writing-editor", "catalog"))
        self.assertEqual(
            [row["target"] for row in matrix["include"]],
            ["catalog"] * 3 + ["korean-writing-editor"] * 3,
        )

    def test_selectors_are_fixed_strings(self) -> None:
        by_target = {
            row["target"]: row["selector"]
            for row in matrix_for_targets(ALL_TARGETS)["include"]
        }
        self.assertEqual(by_target, SELECTORS)

    def test_json_serialization_is_canonical_and_compact(self) -> None:
        matrix = matrix_for_targets(["catalog", "graspic"])
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


class ChangedPathAndCliTests(unittest.TestCase):
    def test_changed_paths_lists_posix_paths_between_revisions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            init_repository(repository)
            first = repository / "skills" / "graspic" / "SKILL.md"
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
                ("catalog/release.toml", "skills/graspic/SKILL.md"),
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
            self.assertEqual(payload, serialize_matrix(matrix_for_targets(("image-workbench",))))
            matrix = json.loads(payload)
            self.assertEqual({row["target"] for row in matrix["include"]}, {"image-workbench"})
            self.assertEqual(len(matrix["include"]), 3)


if __name__ == "__main__":
    unittest.main()
