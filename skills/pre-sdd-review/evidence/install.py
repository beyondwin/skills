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
import zipfile
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
    cache = package / "__pycache__"
    source_entries = tuple(path for path in package_entries if path.name != "__pycache__")
    entries = tuple(sorted(path.name for path in source_entries))
    if entries != tuple(sorted(RUNTIME_PACKAGE_FILES)):
        raise EvidenceError("schema-invalid", "runtime package manifest mismatch")
    if len(source_entries) != len(package_entries):
        if cache.is_symlink() or not cache.is_dir():
            raise EvidenceError("schema-invalid", "runtime package manifest mismatch")
        try:
            cached_entries = tuple(cache.iterdir())
        except OSError as exc:
            raise EvidenceError("schema-invalid", "runtime package manifest mismatch") from exc
        if any(
            entry.is_symlink() or not entry.is_file() or entry.suffix != ".pyc"
            for entry in cached_entries
        ):
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


def _stage_runtime(package: Path, staging_root: Path) -> None:
    app_root = staging_root / "app"
    staged_package = app_root / "pre_sdd_review_evidence"
    staged_package.mkdir(parents=True)
    for name in RUNTIME_PACKAGE_FILES:
        destination = staged_package / name
        shutil.copyfile(package / name, destination, follow_symlinks=False)
        destination.chmod(0o644)
    entrypoint = app_root / "__main__.py"
    entrypoint.write_text(_ENTRYPOINT, encoding="utf-8", newline="\n")
    entrypoint.chmod(0o644)


def _validate_interpreter(python_executable: Path) -> str:
    value = str(python_executable)
    if not value or any(character in value for character in ('"', "\r", "\n")):
        raise EvidenceError("schema-invalid", "python executable path is unsafe")
    return value


def _validate_posix_interpreter(python_executable: Path) -> str:
    path = Path(python_executable)
    value = _validate_interpreter(path)
    if (
        not path.is_absolute()
        or any(character.isspace() for character in value)
        or not path.is_file()
        or not os.access(path, os.X_OK)
    ):
        raise EvidenceError(
            "schema-invalid",
            "POSIX interpreter must be an absolute executable path without whitespace",
        )
    return value


def _create_deterministic_zipapp(
    app_root: Path,
    target: Path,
    *,
    interpreter: str | None,
) -> None:
    source_archive = target.parent / f".{target.name}.runtime.pyz"
    members = [
        ("__main__.py", app_root / "__main__.py"),
        *(
            (
                f"pre_sdd_review_evidence/{name}",
                app_root / "pre_sdd_review_evidence" / name,
            )
            for name in RUNTIME_PACKAGE_FILES
        ),
    ]
    try:
        with zipfile.ZipFile(source_archive, "w") as archive:
            for archive_name, source in members:
                info = zipfile.ZipInfo(archive_name, (1980, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = (stat.S_IFREG | 0o644) << 16
                with source.open("rb") as stream:
                    data = stream.read()
                archive.writestr(
                    info,
                    data,
                    compress_type=zipfile.ZIP_DEFLATED,
                    compresslevel=9,
                )
        zipapp.create_archive(
            source_archive,
            target=target,
            interpreter=interpreter,
        )
    finally:
        try:
            source_archive.unlink()
        except FileNotFoundError:
            pass


def build_posix_launcher(staging_root: Path, python_executable: Path) -> Path:
    """Build the executable POSIX zipapp from a validated staged application."""

    staging_root = Path(staging_root)
    target = staging_root / _COMMAND
    _create_deterministic_zipapp(
        staging_root / "app",
        target,
        interpreter=_validate_posix_interpreter(python_executable),
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
    _create_deterministic_zipapp(
        staging_root / "app",
        archive,
        interpreter=None,
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
