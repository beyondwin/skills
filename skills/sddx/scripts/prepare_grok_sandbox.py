#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    raise SystemExit("BLOCKED: Grok sandbox preparation requires Python 3.11+")


PROFILE = "sddx-worktree"


def git_path(worktree: Path, flag: str) -> Path:
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("GIT_")
    }
    result = subprocess.run(
        ["git", "-C", str(worktree), "rev-parse", flag],
        check=True,
        capture_output=True,
        text=True,
        timeout=5,
        env=env,
    )
    return (worktree / result.stdout.removesuffix("\n")).resolve()


def profile_values(worktree: Path) -> dict:
    if git_path(worktree, "--show-toplevel") != worktree:
        raise ValueError("worktree must be a Git checkout root")
    paths = {
        git_path(worktree, "--git-dir"),
        git_path(worktree, "--git-common-dir"),
    }
    extra = sorted(str(path) for path in paths if not path.is_relative_to(worktree))
    return {"extends": "workspace", "read_write": extra}


def profile_text(before: str | None, expected: dict) -> str:
    text = "" if before is None else before
    profiles = tomllib.loads(text).get("profiles", {})
    if not isinstance(profiles, dict):
        raise ValueError("profiles must be a TOML table")
    if PROFILE in profiles:
        if profiles[PROFILE] != expected:
            raise ValueError("sddx-worktree profile conflicts with required settings")
        return text
    block = (
        f"\n[profiles.{PROFILE}]\n"
        'extends = "workspace"\n'
        f'read_write = {json.dumps(expected["read_write"], ensure_ascii=False)}\n'
    )
    result = text + "\n" + block
    if tomllib.loads(result)["profiles"][PROFILE] != expected:
        raise ValueError("generated profile differs from required settings")
    return result


def _check_regular_file(path: Path, label: str) -> None:
    if path.is_symlink():
        raise ValueError(f"{label} must not be a symbolic link")
    if path.exists() and not path.is_file():
        raise ValueError(f"{label} must be a regular file")


def _validated_paths(worktree: Path, state: Path) -> tuple[Path, Path, Path, dict]:
    worktree = worktree.resolve()
    expected = profile_values(worktree)
    state = Path(os.path.abspath(state))
    superpowers = worktree / ".superpowers"
    try:
        relative_state = state.relative_to(superpowers)
    except ValueError as error:
        raise ValueError("state must be inside the worktree .superpowers directory") from error
    if len(relative_state.parts) < 2 or not state.parent.is_dir():
        raise ValueError("state parent must be an existing evidence directory")

    current = state
    while current != worktree:
        if current.is_symlink():
            raise ValueError("state path must not contain symbolic links")
        current = current.parent
    _check_regular_file(state, "state")

    config_dir = worktree / ".grok"
    if config_dir.is_symlink():
        raise ValueError(".grok must not be a symbolic link")
    if config_dir.exists() and not config_dir.is_dir():
        raise ValueError(".grok must be a directory")
    config = config_dir / "sandbox.toml"
    _check_regular_file(config, "sandbox config")
    return worktree, state, config, expected


def _read_optional(path: Path) -> str | None:
    if not path.exists():
        return None
    return path.read_bytes().decode("utf-8")


def _read_journal(state: Path, worktree: Path) -> dict:
    journal = json.loads(state.read_bytes().decode("utf-8"))
    if not isinstance(journal, dict) or set(journal) != {
        "worktree",
        "before",
        "after",
        "created_dir",
    }:
        raise ValueError("sandbox restoration record has invalid fields")
    if type(journal["worktree"]) is not str or journal["worktree"] != str(worktree):
        raise ValueError("sandbox restoration record belongs to another worktree")
    if journal["before"] is not None and type(journal["before"]) is not str:
        raise ValueError("sandbox restoration record has invalid before text")
    if type(journal["after"]) is not str:
        raise ValueError("sandbox restoration record has invalid after text")
    if type(journal["created_dir"]) is not bool:
        raise ValueError("sandbox restoration record has invalid directory flag")
    return journal


def _write_config(config: Path, before: str | None, after: str) -> None:
    if before is None:
        if not config.parent.exists():
            config.parent.mkdir()

    descriptor, temp_name = tempfile.mkstemp(
        prefix=f".{config.name}.", suffix=".tmp", dir=config.parent
    )
    temp_path = Path(temp_name)
    try:
        if before is not None:
            fchmod = getattr(os, "fchmod", None)
            if fchmod is not None:
                fchmod(descriptor, config.stat().st_mode & 0o7777)
        remaining = memoryview(after.encode("utf-8"))
        while remaining:
            written = os.write(descriptor, remaining)
            if written <= 0:
                raise OSError("failed to write complete sandbox config")
            remaining = remaining[written:]
        os.close(descriptor)
        descriptor = -1

        if _read_optional(config) != before:
            raise ValueError("sandbox config changed during preparation")
        if before is None:
            os.link(temp_path, config)
            temp_path.unlink()
        else:
            os.replace(temp_path, config)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if temp_path.exists():
            temp_path.unlink()


def prepare(worktree: Path, state: Path) -> str:
    worktree, state, config, expected = _validated_paths(worktree, state)
    if state.exists():
        journal = _read_journal(state, worktree)
        current = _read_optional(config)
        if current == journal["after"]:
            return PROFILE
        if current != journal["before"]:
            raise ValueError("sandbox config differs from restoration record")
        _write_config(config, journal["before"], journal["after"])
        return PROFILE

    before = _read_optional(config)
    after = profile_text(before, expected)
    journal = {
        "worktree": str(worktree),
        "before": before,
        "after": after,
        "created_dir": not config.parent.exists(),
    }
    with state.open("x", encoding="utf-8", newline="") as output:
        json.dump(journal, output, ensure_ascii=False)
        output.write("\n")
    _write_config(config, before, after)
    return PROFILE


def cleanup(worktree: Path, state: Path) -> None:
    worktree, state, config, _ = _validated_paths(worktree, state)
    if not state.exists():
        return
    journal = _read_journal(state, worktree)
    current = _read_optional(config)
    if current != journal["after"] and current != journal["before"]:
        raise ValueError("sandbox config differs from restoration record")

    before = journal["before"]
    if current == journal["after"] and before != journal["after"]:
        if before is None:
            config.unlink()
        else:
            _write_config(config, journal["after"], before)
    state.unlink()
    if journal["created_dir"] and config.parent.exists():
        if not any(config.parent.iterdir()):
            config.parent.rmdir()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("prepare", "cleanup"))
    parser.add_argument("--worktree", required=True, type=Path)
    parser.add_argument("--state", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.action == "prepare":
            result = {"profile": prepare(args.worktree, args.state)}
        else:
            cleanup(args.worktree, args.state)
            result = {"cleaned": True}
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"BLOCKED: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
