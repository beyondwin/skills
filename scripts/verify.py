#!/usr/bin/env python3
"""Provider-free repository verification orchestrator."""

from __future__ import annotations

import argparse
import dataclasses
import pathlib
import subprocess
import sys
from collections.abc import Iterable, Sequence


ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.product_registry import load_registry  # noqa: E402

REGISTRY = load_registry(ROOT / "products.toml")

PROFILES = ("full", "windows-portable")
FULL_STAGE_NAMES = (
    "contract",
    "korean-offline",
    "image-contract",
    "image-inspector",
    "korean-live-unit",
    "korean-live-dry-run",
    "python-compile",
)
WINDOWS_EXCLUDED_STAGES = frozenset({"image-contract", "image-inspector"})
PRODUCT_STAGE_NAMES = {
    "korean-writing-editor": (
        "product-contract",
        "korean-package",
        "korean-offline",
        "korean-live-unit",
        "korean-live-dry-run",
        "python-compile",
    ),
    "image-workbench": (
        "product-contract",
        "image-contract",
        "image-inspector",
        "python-compile",
    ),
    "graspic": (
        "product-contract",
        "graspic-contract",
        "python-compile",
    ),
}
CATALOG_STAGE_NAMES = (
    "catalog-contract",
    "catalog-release-contract",
    "public-docs",
    "python-compile",
)


@dataclasses.dataclass(frozen=True)
class Stage:
    name: str
    argv: tuple[str, ...]
    cwd: pathlib.Path = ROOT


def _python(*arguments: str) -> tuple[str, ...]:
    return (sys.executable, *arguments)


def _posix(*parts: str) -> str:
    return pathlib.PurePosixPath(*parts).as_posix()


def _compile_paths() -> tuple[str, ...]:
    paths = ["scripts", "tests"]
    skills_root = ROOT / "skills"
    if skills_root.is_dir():
        for skill in sorted(path for path in skills_root.iterdir() if path.is_dir()):
            scripts_dir = skill / "scripts"
            if scripts_dir.is_dir():
                paths.append(_posix("skills", skill.name, "scripts"))
    return tuple(paths)


def _catalog() -> dict[str, Stage]:
    return {
        "contract": Stage(
            "contract",
            _python("-m", "unittest", "discover", "-s", _posix("tests", "contract"), "-p", "test_*.py"),
        ),
        "korean-offline": Stage(
            "korean-offline",
            _python(
                _posix("tests", "korean-writing-editor", "offline", "run.py"),
                "--scope",
                "full",
            ),
        ),
        "image-contract": Stage(
            "image-contract",
            _python(_posix("tests", "image-workbench", "run.py"), "--scope", "full"),
        ),
        "image-inspector": Stage(
            "image-inspector",
            _python(
                "-m",
                "unittest",
                "discover",
                "-s",
                _posix("tests", "image-workbench"),
                "-p",
                "test_*.py",
            ),
        ),
        "korean-live-unit": Stage(
            "korean-live-unit",
            _python(
                "-m",
                "unittest",
                "discover",
                "-s",
                _posix("tests", "korean-writing-editor", "live"),
                "-p",
                "test_*.py",
            ),
        ),
        "korean-live-dry-run": Stage(
            "korean-live-dry-run",
            _python(
                _posix("tests", "korean-writing-editor", "live", "live_matrix.py"),
                "--dry-run",
            ),
        ),
        "python-compile": Stage(
            "python-compile",
            _python("-m", "compileall", "-q", *_compile_paths()),
        ),
        "product-contract": Stage(
            "product-contract",
            _python("-m", "unittest", "tests.contract.test_release_contract"),
        ),
        "korean-package": Stage(
            "korean-package",
            _python("-m", "unittest", "tests.contract.test_korean_package"),
        ),
        "graspic-contract": Stage(
            "graspic-contract",
            _python("-m", "unittest", "tests.contract.test_graspic"),
        ),
        "catalog-contract": Stage(
            "catalog-contract",
            _python("-m", "unittest", "tests.contract.test_catalog_contract"),
        ),
        "catalog-release-contract": Stage(
            "catalog-release-contract",
            _python("-m", "unittest", "tests.contract.test_catalog_release"),
        ),
        "public-docs": Stage(
            "public-docs",
            _python("-m", "unittest", "tests.contract.test_public_docs"),
        ),
    }


def stages(
    profile: str, *, skill: str | None = None, catalog: bool = False
) -> Sequence[Stage]:
    if profile not in PROFILES:
        raise ValueError(f"unknown profile: {profile}")
    if skill is not None and catalog:
        raise ValueError("skill and catalog selectors are mutually exclusive")
    if skill is not None and skill not in PRODUCT_STAGE_NAMES:
        raise ValueError(f"unknown skill: {skill}")
    stage_map = _catalog()
    if catalog:
        names: tuple[str, ...] = CATALOG_STAGE_NAMES
    elif skill is not None:
        names = PRODUCT_STAGE_NAMES[skill]
    else:
        names = FULL_STAGE_NAMES
    if profile == "windows-portable":
        names = tuple(name for name in names if name not in WINDOWS_EXCLUDED_STAGES)
    return tuple(stage_map[name] for name in names)


def run_stage(stage: Stage) -> int:
    print(f"==> {stage.name}: {' '.join(stage.argv)}", flush=True)
    return subprocess.run(stage.argv, cwd=stage.cwd, check=False).returncode


def run_stages(stage_list: Iterable[Stage]) -> int:
    for stage in stage_list:
        code = run_stage(stage)
        if code != 0:
            print(f"FAILED stage: {stage.name}", file=sys.stderr, flush=True)
            return code
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profile",
        choices=PROFILES,
        default="full",
        help="verification profile (default: full)",
    )
    target = parser.add_mutually_exclusive_group()
    target.add_argument("--skill", choices=REGISTRY.names)
    target.add_argument("--catalog", action="store_true")
    args = parser.parse_args(argv)
    return run_stages(stages(args.profile, skill=args.skill, catalog=args.catalog))


if __name__ == "__main__":
    raise SystemExit(main())
