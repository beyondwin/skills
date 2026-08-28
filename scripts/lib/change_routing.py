from __future__ import annotations

import json
import pathlib
import subprocess
from collections.abc import Iterable, Sequence

from scripts.lib.product_registry import ProductRegistry, normalize_repo_path


CATALOG_PREFIX = "catalog/"
OS_ROWS = (
    ("ubuntu-latest", "full"),
    ("macos-latest", "full"),
    ("windows-latest", "windows-portable"),
)
FULL_REPOSITORY_EVENTS = frozenset({"push", "workflow_dispatch"})


def _all_targets(registry: ProductRegistry) -> tuple[str, ...]:
    return ("catalog", *registry.names)


def _matches_owned(path: str, owned_paths: Iterable[pathlib.PurePosixPath]) -> bool:
    for owned in owned_paths:
        prefix = normalize_repo_path(owned).rstrip("/")
        if prefix and (path == prefix or path.startswith(f"{prefix}/")):
            return True
    return False


def _selector(target: str) -> str:
    if target == "catalog":
        return "--catalog"
    return f"--skill {target}"


def targets_for_paths(paths: Iterable[str], registry: ProductRegistry) -> Sequence[str]:
    normalized = {normalize_repo_path(path) for path in paths}
    if not normalized:
        return _all_targets(registry)
    selected: set[str] = set()
    for path in normalized:
        matched = False
        if path.startswith(CATALOG_PREFIX):
            selected.add("catalog")
            matched = True
        for product in registry.products:
            if _matches_owned(path, product.owned_paths):
                selected.add(product.name)
                matched = True
        if not matched:
            return _all_targets(registry)
    return tuple(target for target in _all_targets(registry) if target in selected)


def matrix_for_targets(
    targets: Iterable[str],
    registry: ProductRegistry,
) -> dict[str, list[dict[str, str]]]:
    wanted = set(targets)
    order = _all_targets(registry)
    selected = tuple(target for target in order if target in wanted)
    if not selected:
        selected = order
    include: list[dict[str, str]] = []
    for target in selected:
        selector = _selector(target)
        for os_name, profile in OS_ROWS:
            include.append(
                {
                    "target": target,
                    "os": os_name,
                    "profile": profile,
                    "selector": selector,
                }
            )
    return {"include": include}


def full_repository_matrix() -> dict[str, list[dict[str, str]]]:
    return {
        "include": [
            {"os": os_name, "profile": profile, "selector": ""}
            for os_name, profile in OS_ROWS
        ]
    }


def serialize_matrix(matrix: dict[str, list[dict[str, str]]]) -> str:
    return json.dumps(matrix, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def changed_paths(root: pathlib.Path, base: str, head: str) -> Sequence[str]:
    completed = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "diff",
            "--name-only",
            "--no-renames",
            "-z",
            f"{base}...{head}",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return ()
    return tuple(
        normalize_repo_path(item) for item in completed.stdout.split("\0") if item
    )


def matrix_for_event(
    event: str,
    root: pathlib.Path,
    registry: ProductRegistry,
    base: str = "",
    head: str = "",
) -> dict[str, list[dict[str, str]]]:
    if event in FULL_REPOSITORY_EVENTS:
        return full_repository_matrix()
    if event == "pull_request" and base and head:
        return matrix_for_targets(
            targets_for_paths(changed_paths(root, base, head), registry),
            registry,
        )
    return matrix_for_targets(_all_targets(registry), registry)
