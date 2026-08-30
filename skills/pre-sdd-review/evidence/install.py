"""Explicit, create-only installer for the shared pre-SDD evidence CLI."""

from __future__ import annotations

import argparse
import ast
import os
import shutil
import stat
import sys
import tempfile
import tomllib
import zipapp
from pathlib import Path


RUNTIME_PACKAGE_FILES = (
    "__init__.py",
    "__main__.py",
    "cli.py",
    "schema.py",
    "repository.py",
    "storage.py",
    "reporting.py",
)

_SKILL_NAME = "pre-sdd-review"
_SKILL_VERSION = "1.2.0"
_CLI_VERSION = "1.0.0"
_SCHEMA_VERSION = 1
_COMMAND = "pre-sdd-review-evidence"
_ARCHIVE_TIMESTAMP = 315_532_800
_ENTRYPOINT = (
    "from pre_sdd_review_evidence.cli import main\n"
    "raise SystemExit(main())\n"
)


class EvidenceError(ValueError):
    """Stable installer failure that does not import the supplied runtime."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _require_regular(path: Path, label: str) -> None:
    if path.is_symlink() or not path.is_file():
        raise EvidenceError("schema-invalid", f"{label} must be a regular non-symlink file")


def _validate_release(skill_root: Path) -> None:
    manifest = skill_root / "release.toml"
    _require_regular(manifest, "release.toml")
    try:
        with manifest.open("rb") as stream:
            value = tomllib.load(stream)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise EvidenceError("schema-invalid", "release identity is invalid") from exc
    if value.get("name") != _SKILL_NAME or value.get("version") != _SKILL_VERSION:
        raise EvidenceError(
            "schema-invalid",
            f"release identity must be {_SKILL_NAME} {_SKILL_VERSION}",
        )


def _literal_constants(path: Path) -> dict[str, object]:
    _require_regular(path, "runtime __init__.py")
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename="__init__.py")
    except (OSError, UnicodeError, SyntaxError) as exc:
        raise EvidenceError("schema-invalid", "runtime constants are invalid") from exc
    found: dict[str, object] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name) or target.id not in {
            "CLI_VERSION",
            "SCHEMA_VERSION",
        }:
            continue
        if target.id in found:
            raise EvidenceError("schema-invalid", f"duplicate {target.id} literal")
        try:
            found[target.id] = ast.literal_eval(node.value)
        except (ValueError, TypeError) as exc:
            raise EvidenceError("schema-invalid", f"{target.id} must be a literal") from exc
    return found


def _validate_source(skill_root: Path) -> Path:
    skill_root = Path(skill_root)
    if skill_root.is_symlink() or not skill_root.is_dir():
        raise EvidenceError("schema-invalid", "skill root must be a regular directory")
    _validate_release(skill_root)
    package = skill_root / "evidence" / "pre_sdd_review_evidence"
    if package.is_symlink() or not package.is_dir():
        raise EvidenceError("schema-invalid", "runtime package must be a regular directory")
    try:
        package_entries = tuple(package.iterdir())
    except OSError as exc:
        raise EvidenceError("schema-invalid", "runtime package cannot be inspected") from exc
    entries = tuple(
        sorted(
            path.name
            for path in package_entries
            if not (
                path.name == "__pycache__"
                and not path.is_symlink()
                and path.is_dir()
            )
        )
    )
    if entries != tuple(sorted(RUNTIME_PACKAGE_FILES)):
        raise EvidenceError("schema-invalid", "runtime package manifest mismatch")
    for name in RUNTIME_PACKAGE_FILES:
        _require_regular(package / name, f"runtime package member {name}")
    constants = _literal_constants(package / "__init__.py")
    if constants.get("CLI_VERSION") != _CLI_VERSION:
        raise EvidenceError("incompatible-cli", f"CLI_VERSION must be {_CLI_VERSION}")
    if constants.get("SCHEMA_VERSION") != _SCHEMA_VERSION:
        raise EvidenceError(
            "unsupported-schema-version",
            f"SCHEMA_VERSION must be {_SCHEMA_VERSION}",
        )
    return package


def _set_archive_timestamp(path: Path) -> None:
    os.utime(path, (_ARCHIVE_TIMESTAMP, _ARCHIVE_TIMESTAMP), follow_symlinks=False)


def _stage_runtime(package: Path, staging_root: Path) -> None:
    app_root = staging_root / "app"
    staged_package = app_root / "pre_sdd_review_evidence"
    staged_package.mkdir(parents=True)
    for name in RUNTIME_PACKAGE_FILES:
        destination = staged_package / name
        shutil.copyfile(package / name, destination, follow_symlinks=False)
        destination.chmod(0o644)
        _set_archive_timestamp(destination)
    entrypoint = app_root / "__main__.py"
    entrypoint.write_text(_ENTRYPOINT, encoding="utf-8", newline="\n")
    entrypoint.chmod(0o644)
    _set_archive_timestamp(entrypoint)
    _set_archive_timestamp(staged_package)
    _set_archive_timestamp(app_root)


def _validate_interpreter(python_executable: Path) -> str:
    value = str(python_executable)
    if not value or any(character in value for character in ('"', "\r", "\n")):
        raise EvidenceError("schema-invalid", "python executable path is unsafe")
    return value


def build_posix_launcher(staging_root: Path, python_executable: Path) -> Path:
    """Build the executable POSIX zipapp from a validated staged application."""

    staging_root = Path(staging_root)
    target = staging_root / _COMMAND
    zipapp.create_archive(
        staging_root / "app",
        target=target,
        interpreter=_validate_interpreter(python_executable),
        compressed=True,
    )
    target.chmod(0o755)
    return target


def build_windows_launcher(
    staging_root: Path,
    python_executable: Path,
) -> tuple[Path, Path]:
    """Build the Windows zipapp and exact-interpreter command wrapper."""

    staging_root = Path(staging_root)
    executable = _validate_interpreter(python_executable)
    archive = staging_root / f"{_COMMAND}.pyz"
    wrapper = staging_root / f"{_COMMAND}.cmd"
    zipapp.create_archive(
        staging_root / "app",
        target=archive,
        compressed=True,
    )
    wrapper.write_bytes(
        f'@"{executable}" "%~dp0{_COMMAND}.pyz" %*\r\n'.encode("utf-8")
    )
    archive.chmod(0o644)
    wrapper.chmod(0o644)
    return archive, wrapper


def _read_file(path: Path) -> bytes:
    try:
        with path.open("rb") as stream:
            return stream.read()
    except OSError as exc:
        raise EvidenceError("install-failed", "install target cannot be read") from exc


def _existing_target_is_identical(target: Path, expected: bytes) -> bool:
    if target.is_symlink() or not target.is_file():
        return False
    return _read_file(target) == expected


def _flush_directory(directory: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    try:
        descriptor = os.open(directory, flags)
    except OSError:
        return
    try:
        os.fsync(descriptor)
    except OSError:
        pass
    finally:
        os.close(descriptor)


def _publish_create_only(source: Path, target: Path, mode: int) -> None:
    expected = _read_file(source)
    if target.exists() or target.is_symlink():
        if not _existing_target_is_identical(target, expected):
            raise EvidenceError("already-finalized", "install target exists with different bytes")
        if stat.S_IMODE(target.stat().st_mode) != mode:
            target.chmod(mode)
        return

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.install-",
        dir=target.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(expected)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.chmod(mode)
        try:
            os.link(temporary, target)
        except FileExistsError:
            if not _existing_target_is_identical(target, expected):
                raise EvidenceError(
                    "already-finalized",
                    "install target exists with different bytes",
                )
            if stat.S_IMODE(target.stat().st_mode) != mode:
                target.chmod(mode)
        except OSError as exc:
            raise EvidenceError("install-failed", "install target could not be created") from exc
        _flush_directory(target.parent)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def install(
    skill_root: Path,
    bin_dir: Path,
    platform: str,
    python_executable: Path,
) -> tuple[Path, ...]:
    """Install one verified launcher set without replacing any existing file."""

    package = _validate_source(Path(skill_root))
    bin_dir = Path(bin_dir)
    if bin_dir.is_symlink() or not bin_dir.is_dir():
        raise EvidenceError(
            "install-failed",
            "bin directory must already exist and be intended for PATH",
        )
    if platform not in {"posix", "windows"}:
        raise EvidenceError("schema-invalid", "platform must be posix or windows")

    with tempfile.TemporaryDirectory(prefix="pre-sdd-review-install-") as directory:
        staging_root = Path(directory)
        _stage_runtime(package, staging_root)
        if platform == "posix":
            built = (build_posix_launcher(staging_root, python_executable),)
            modes = (0o755,)
        else:
            built = build_windows_launcher(staging_root, python_executable)
            modes = (0o644, 0o644)

        targets = tuple(bin_dir / source.name for source in built)
        expected = tuple(_read_file(source) for source in built)
        for target, data in zip(targets, expected, strict=True):
            if (target.exists() or target.is_symlink()) and not _existing_target_is_identical(
                target, data
            ):
                raise EvidenceError(
                    "already-finalized",
                    "install target exists with different bytes",
                )
        for source, target, mode in zip(built, targets, modes, strict=True):
            _publish_create_only(source, target, mode)
        return targets


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Install the shared pre-sdd-review evidence command.",
    )
    parser.add_argument("--bin-dir", type=Path, required=True)
    parser.add_argument(
        "--skill-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    arguments = parser.parse_args(argv)
    platform = "windows" if os.name == "nt" else "posix"
    try:
        install(
            arguments.skill_root,
            arguments.bin_dir,
            platform=platform,
            python_executable=Path(sys.executable),
        )
    except EvidenceError as exc:
        parser.error(f"{exc.code}: {exc.message}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
