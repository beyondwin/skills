from __future__ import annotations

import dataclasses
import pathlib
import subprocess
import sys
from collections.abc import Iterable, Mapping, Sequence

from scripts.lib.product_registry import ProductRegistry


ROOT = pathlib.Path(__file__).resolve().parents[2]
PROFILES = ("full", "windows-portable")
WINDOWS_EXCLUDED_STAGES = frozenset({"image-contract", "image-inspector"})
CATALOG_STAGE_NAMES = (
    "catalog-contract",
    "catalog-release-contract",
    "public-docs",
    "python-compile",
)
_SHARED_PRODUCT_STAGES = frozenset({"product-contract", "python-compile"})


@dataclasses.dataclass(frozen=True)
class Stage:
    name: str
    argv: tuple[str, ...]
    cwd: pathlib.Path = ROOT


def _python(*arguments: str) -> tuple[str, ...]:
    return (sys.executable, *arguments)


def _posix(*parts: str) -> str:
    return pathlib.PurePosixPath(*parts).as_posix()


def _compile_paths(root: pathlib.Path) -> tuple[str, ...]:
    paths = ["scripts", "tests"]
    skills_root = root / "skills"
    if skills_root.is_dir():
        for skill in sorted(path for path in skills_root.iterdir() if path.is_dir()):
            scripts_dir = skill / "scripts"
            if scripts_dir.is_dir():
                paths.append(_posix("skills", skill.name, "scripts"))
    return tuple(paths)


def _stage_catalog(root: pathlib.Path) -> dict[str, Stage]:
    root = pathlib.Path(root)
    return {
        "repository-contract": Stage(
            "repository-contract",
            _python("-m", "unittest", "discover", "-s", _posix("tests", "repository"), "-p", "test_*.py"),
            cwd=root,
        ),
        "korean-offline": Stage(
            "korean-offline",
            _python(
                _posix("tests", "products", "korean-writing-editor", "offline", "run.py"),
                "--scope",
                "full",
            ),
            cwd=root,
        ),
        "image-contract": Stage(
            "image-contract",
            _python(_posix("tests", "products", "image-workbench", "run.py"), "--scope", "full"),
            cwd=root,
        ),
        "image-inspector": Stage(
            "image-inspector",
            _python(
                "-m",
                "unittest",
                "discover",
                "-s",
                _posix("tests", "products", "image-workbench"),
                "-p",
                "test_*.py",
            ),
            cwd=root,
        ),
        "korean-live-unit": Stage(
            "korean-live-unit",
            _python(
                "-m",
                "unittest",
                "discover",
                "-s",
                _posix("tests", "products", "korean-writing-editor", "live"),
                "-p",
                "test_*.py",
            ),
            cwd=root,
        ),
        "korean-live-dry-run": Stage(
            "korean-live-dry-run",
            _python(
                _posix("tests", "products", "korean-writing-editor", "live", "live_matrix.py"),
                "--dry-run",
            ),
            cwd=root,
        ),
        "python-compile": Stage(
            "python-compile",
            _python("-m", "compileall", "-q", *_compile_paths(root)),
            cwd=root,
        ),
        "product-contract": Stage(
            "product-contract",
            _python("-m", "unittest", "tests.repository.test_release_contract"),
            cwd=root,
        ),
        "korean-package": Stage(
            "korean-package",
            _python(
                "-m",
                "unittest",
                "discover",
                "-s",
                _posix("tests", "products", "korean-writing-editor"),
                "-p",
                "test_package.py",
            ),
            cwd=root,
        ),
        "graspic-contract": Stage(
            "graspic-contract",
            _python(
                "-m",
                "unittest",
                "discover",
                "-s",
                _posix("tests", "products", "graspic"),
                "-p",
                "test_contract.py",
            ),
            cwd=root,
        ),
        "catalog-contract": Stage(
            "catalog-contract",
            _python("-m", "unittest", "tests.repository.test_catalog_contract"),
            cwd=root,
        ),
        "catalog-release-contract": Stage(
            "catalog-release-contract",
            _python("-m", "unittest", "tests.repository.test_catalog_release"),
            cwd=root,
        ),
        "public-docs": Stage(
            "public-docs",
            _python("-m", "unittest", "tests.repository.test_public_docs"),
            cwd=root,
        ),
    }


REGISTERED_STAGES: Mapping[str, Stage] = _stage_catalog(ROOT)
REGISTERED_STAGE_NAMES = frozenset(_stage_catalog(ROOT))


def _full_stage_names(registry: ProductRegistry) -> tuple[str, ...]:
    names: list[str] = ["repository-contract"]
    seen = {"repository-contract", *_SHARED_PRODUCT_STAGES}
    for product in registry.products:
        for stage in product.verify_stages:
            if stage in seen:
                continue
            names.append(stage)
            seen.add(stage)
    names.append("python-compile")
    return tuple(names)


def stages(
    root: pathlib.Path,
    profile: str,
    registry: ProductRegistry,
    skill: str | None = None,
    catalog: bool = False,
) -> Sequence[Stage]:
    if profile not in PROFILES:
        raise ValueError(f"unknown profile: {profile}")
    if skill is not None and catalog:
        raise ValueError("skill and catalog selectors are mutually exclusive")
    if catalog:
        names: tuple[str, ...] = CATALOG_STAGE_NAMES
    elif skill is not None:
        try:
            names = registry.require(skill).verify_stages
        except KeyError as exc:
            raise ValueError(f"unknown skill: {skill}") from exc
    else:
        names = _full_stage_names(registry)
    if profile == "windows-portable":
        names = tuple(name for name in names if name not in WINDOWS_EXCLUDED_STAGES)
    stage_map = _stage_catalog(root)
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
