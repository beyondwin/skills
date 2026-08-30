from __future__ import annotations

import ctypes
import dataclasses
import datetime as dt
import errno
import hashlib
import hmac
import os
import re
import secrets
import shutil
import stat
import sys
import uuid
from collections.abc import Callable, Mapping
from pathlib import Path

from . import CLI_VERSION, SCHEMA_VERSION
from .schema import (
    REVIEW_HARD_LIMIT,
    EvidenceError,
    canonical_json_bytes,
    read_bounded_json,
    validate_review,
)


PENDING_HARD_LIMIT = REVIEW_HARD_LIMIT
_RUN_ID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\Z")
_TIME = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T")
_REASON = re.compile(r"[a-z0-9][a-z0-9._-]{0,99}\Z")
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_Hook = Callable[[str, Path], None]


@dataclasses.dataclass(frozen=True)
class EvidencePaths:
    home: Path
    config: Path
    identity_key: Path
    runs: Path
    exports: Path

    @classmethod
    def from_home(cls, home: Path) -> "EvidencePaths":
        canonical = Path(home).resolve(strict=False)
        if not canonical.is_absolute():
            raise EvidenceError("invalid-evidence-home", "evidence home must be absolute")
        return cls(
            home=canonical,
            config=canonical / "config.json",
            identity_key=canonical / "identity.key",
            runs=canonical / "runs",
            exports=canonical / "exports",
        )

    def run_directory(self, run_id: str, started_at: str) -> Path:
        _validate_run_id(run_id)
        if not isinstance(started_at, str) or _TIME.match(started_at) is None:
            raise EvidenceError("invalid-time", "started_at is invalid")
        return self.runs / started_at[:4] / started_at[5:7] / run_id


@dataclasses.dataclass(frozen=True)
class RunHandle:
    run_id: str
    directory: Path


@dataclasses.dataclass(frozen=True)
class WriteResult:
    run_id: str
    sha256: str
    path: Path


@dataclasses.dataclass(frozen=True)
class PendingEntry:
    run_id: str
    started_at: str
    resolution_status: str
    plan_path: str | None
    design_path: str | None
    age_class: str


@dataclasses.dataclass(frozen=True)
class ScanResult:
    reviews: tuple[dict[str, object], ...]
    pending: tuple[PendingEntry, ...]
    corrupt: tuple[str, ...]


def _fail(code: str, message: str) -> None:
    raise EvidenceError(code, message)


def sha256_payload(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def evidence_home(environ: Mapping[str, str], user_home: Path) -> Path:
    override = environ.get("PRE_SDD_REVIEW_HOME")
    if override is None:
        return (Path(user_home) / ".pre-sdd-review").resolve(strict=False)
    if not override.strip():
        _fail("invalid-evidence-home", "override must be non-empty and absolute")
    candidate = Path(override).expanduser()
    if not candidate.is_absolute():
        _fail("invalid-evidence-home", "override must be absolute")
    return candidate.resolve(strict=False)


def _lstat(path: Path) -> os.stat_result | None:
    try:
        return path.lstat()
    except FileNotFoundError:
        return None


def _is_private(info: os.stat_result) -> bool:
    return os.name != "posix" or stat.S_IMODE(info.st_mode) & 0o077 == 0


def _ensure_private_directory(path: Path) -> None:
    parent = path.parent
    if path != parent and not parent.exists():
        _ensure_private_directory(parent)
    info = _lstat(path)
    if info is None:
        try:
            path.mkdir(mode=0o700)
        except FileExistsError:
            pass
        info = path.lstat()
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode) or not _is_private(info):
        _fail("unsafe-evidence-path", "evidence directories must be private real directories")


def _validate_regular(path: Path, *, private: bool = True) -> os.stat_result:
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode) or (private and not _is_private(info)):
        _fail("unsafe-evidence-path", "evidence records must be private regular files")
    return info


def _validate_run_directory(path: Path) -> os.stat_result:
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode) or not _is_private(info):
        _fail("unsafe-evidence-path", "run destination is unsafe")
    return info


def _fsync_directory(path: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    descriptor = os.open(path, flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _validate_run_id(run_id: str) -> None:
    if not isinstance(run_id, str) or _RUN_ID.fullmatch(run_id) is None:
        _fail("invalid-run-id", "run_id must be a canonical lowercase UUID")
    try:
        if str(uuid.UUID(run_id)) != run_id:
            raise ValueError
    except ValueError:
        _fail("invalid-run-id", "run_id must be a canonical lowercase UUID")


def _validate_pending(value: object) -> dict[str, object]:
    keys = {
        "schema_version", "record_type", "run_id", "started_at", "skill", "client",
        "target", "intended_mode", "start_locator_binding",
    }
    if not isinstance(value, dict) or set(value) != keys:
        _fail("schema-invalid", "pending record has invalid fields")
    if value["schema_version"] != SCHEMA_VERSION or value["record_type"] != "pending":
        _fail("schema-invalid", "pending schema identity is invalid")
    _validate_run_id(value["run_id"])
    started_at = value["started_at"]
    try:
        if not isinstance(started_at, str) or not started_at.endswith("Z"):
            raise ValueError
        dt.datetime.fromisoformat(started_at[:-1] + "+00:00")
    except ValueError:
        _fail("schema-invalid", "pending start time is invalid")
    if value["intended_mode"] not in {"default", "review-only"}:
        _fail("schema-invalid", "pending intended mode is invalid")
    binding = value["start_locator_binding"]
    if not isinstance(binding, str) or _SHA.fullmatch(binding) is None:
        _fail("schema-invalid", "pending locator binding is invalid")
    # Reuse the closed review validator to validate the copied skill/client/target projections.
    probe = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "review",
        "run_id": value["run_id"],
        "started_at": started_at,
        "completed_at": started_at,
        "skill": value["skill"],
        "client": value["client"],
        "protocol": {"mode": value["intended_mode"], "execution": "unknown", "reviewer_count": 0, "fresh_reviewer": False, "read_only_enforced": False, "conditional_trigger": None, "degraded_reasons": []},
        "target": value["target"],
        "result": {"completion": "abandoned", "verdict": None, "block_reason": None, "completion_reason": "pending-validation", "review_passes": 0, "repair_passes": 0, "findings": []},
        "freshness": {"final_head": None, "final_dirty": None, "plan_final_sha256": None, "design_final_sha256": None},
        "metrics": {"elapsed_ms": 0, "recorder_elapsed_ms": 0, "reviewer_count": 0, "review_passes": 0, "repair_passes": 0, "token_usage": None},
    }
    validate_review(probe)
    if len(canonical_json_bytes(value)) > PENDING_HARD_LIMIT:
        _fail("record-too-large", "pending record exceeds the hard size limit")
    return value.copy()


def _load_pending_path(path: Path) -> dict[str, object]:
    _validate_regular(path)
    return _validate_pending(read_bounded_json(path, PENDING_HARD_LIMIT))


def _load_exact_pending_destination(path: Path) -> dict[str, object]:
    _validate_run_directory(path)
    entries = list(path.iterdir())
    if len(entries) != 1 or entries[0].name != ".pending.json":
        _fail("conflicting-retry", "run destination has unexpected entries")
    return _load_pending_path(entries[0])


def _find_run_directory(paths: EvidencePaths, run_id: str) -> Path:
    _validate_run_id(run_id)
    info = _lstat(paths.runs)
    if info is None:
        _fail("run-not-found", "run was not found")
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        _fail("unsafe-evidence-path", "runs root is unsafe")
    matches: list[Path] = []
    for year in paths.runs.iterdir():
        if year.name.startswith("."):
            continue
        if year.is_symlink() or not year.is_dir() or not re.fullmatch(r"[0-9]{4}", year.name):
            continue
        for month in year.iterdir():
            if month.is_symlink() or not month.is_dir() or not re.fullmatch(r"(?:0[1-9]|1[0-2])", month.name):
                continue
            candidate = month / run_id
            entry = _lstat(candidate)
            if entry is not None:
                if stat.S_ISLNK(entry.st_mode) or not stat.S_ISDIR(entry.st_mode) or not _is_private(entry):
                    _fail("unsafe-evidence-path", "run directory is unsafe")
                matches.append(candidate)
    if len(matches) != 1:
        _fail("run-not-found" if not matches else "identity-state-invalid", "run was not found")
    return matches[0]


def load_pending(paths: EvidencePaths, run_id: str) -> dict[str, object]:
    directory = _find_run_directory(paths, run_id)
    path = directory / ".pending.json"
    try:
        return _load_pending_path(path)
    except FileNotFoundError as exc:
        raise EvidenceError("run-not-found", "pending run was not found") from exc


def _native_error(code: int) -> None:
    if code in {errno.EEXIST, errno.ENOTEMPTY}:
        _fail("already-exists", "destination already exists")
    _fail("atomic-create-unsupported", "native no-replace publication is unavailable")


def publish_directory_no_replace(source: Path, destination: Path) -> None:
    source = Path(source)
    destination = Path(destination)
    try:
        if sys.platform == "darwin":
            library = ctypes.CDLL(None, use_errno=True)
            function = library.renamex_np
            function.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
            function.restype = ctypes.c_int
            result = function(os.fsencode(source), os.fsencode(destination), 0x4)
            if result != 0:
                _native_error(ctypes.get_errno())
            return
        if sys.platform.startswith("linux"):
            library = ctypes.CDLL(None, use_errno=True)
            function = library.renameat2
            function.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
            function.restype = ctypes.c_int
            result = function(-100, os.fsencode(source), -100, os.fsencode(destination), 1)
            if result != 0:
                _native_error(ctypes.get_errno())
            return
        if sys.platform == "win32":
            library = ctypes.WinDLL("kernel32", use_last_error=True)
            function = library.MoveFileExW
            function.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint]
            function.restype = ctypes.c_int
            if not function(str(source), str(destination), 0):
                code = ctypes.get_last_error()
                if code in {80, 183}:
                    _fail("already-exists", "destination already exists")
                _fail("atomic-create-unsupported", "native no-replace publication is unavailable")
            return
    except AttributeError as exc:
        raise EvidenceError("atomic-create-unsupported", "native no-replace symbol is unavailable") from exc
    _fail("atomic-create-unsupported", "platform has no proved directory publication primitive")


def _write_private(path: Path, payload: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb", closefd=False) as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        os.close(descriptor)


def _ensure_roots(paths: EvidencePaths) -> None:
    _ensure_private_directory(paths.home)
    _ensure_private_directory(paths.runs)


def create_pending(
    paths: EvidencePaths,
    pending: object,
    *,
    interruption_hook: _Hook | None = None,
) -> RunHandle:
    record = _validate_pending(pending)
    _ensure_roots(paths)
    run_id = record["run_id"]
    started_at = record["started_at"]
    assert isinstance(run_id, str) and isinstance(started_at, str)
    staging = paths.runs / f".staging-{run_id}"
    if _lstat(staging) is not None:
        _fail("already-exists", "staging directory already exists")
    staging.mkdir(mode=0o700)
    pending_path = staging / ".pending.json"
    try:
        _write_private(pending_path, canonical_json_bytes(record))
        _fsync_directory(staging)
        if interruption_hook is not None:
            interruption_hook("pending-fsynced", pending_path)
        destination = paths.run_directory(run_id, started_at)
        _ensure_private_directory(destination.parent.parent)
        _ensure_private_directory(destination.parent)
        try:
            publish_directory_no_replace(staging, destination)
        except EvidenceError as exc:
            if exc.code != "already-exists":
                raise
            existing = _load_exact_pending_destination(destination)
            if canonical_json_bytes(existing) == canonical_json_bytes(record):
                shutil.rmtree(staging)
                _fsync_directory(paths.runs)
                return RunHandle(run_id, destination)
            raise EvidenceError("already-exists", "run destination already exists") from exc
        _fsync_directory(destination.parent)
        _fsync_directory(paths.runs)
        return RunHandle(run_id, destination)
    except Exception:
        # An interruption after the pending fsync deliberately preserves staging.
        if _lstat(pending_path) is None:
            try:
                staging.rmdir()
            except OSError:
                pass
        raise


def recover_staging(paths: EvidencePaths) -> tuple[str, ...]:
    _ensure_roots(paths)
    unresolved: list[str] = []
    for staging in sorted(paths.runs.iterdir(), key=lambda item: item.name):
        match = re.fullmatch(r"\.staging-([0-9a-f-]{36})", staging.name)
        if match is None:
            continue
        run_id = match.group(1)
        try:
            _validate_run_id(run_id)
            info = staging.lstat()
            if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode) or not _is_private(info):
                raise EvidenceError("unsafe-evidence-path", "staging directory is unsafe")
            entries = list(staging.iterdir())
            if [item.name for item in entries] != [".pending.json"]:
                raise EvidenceError("schema-invalid", "staging directory has unexpected entries")
            pending = _load_pending_path(entries[0])
            if pending["run_id"] != run_id:
                raise EvidenceError("schema-invalid", "staging run ID does not match")
            destination = paths.run_directory(run_id, str(pending["started_at"]))
            _ensure_private_directory(destination.parent.parent)
            _ensure_private_directory(destination.parent)
            try:
                publish_directory_no_replace(staging, destination)
            except EvidenceError as exc:
                if exc.code != "already-exists":
                    raise
                current = _load_exact_pending_destination(destination)
                if canonical_json_bytes(current) != canonical_json_bytes(pending):
                    raise EvidenceError("conflicting-retry", "staging conflicts with existing run")
                shutil.rmtree(staging)
            _fsync_directory(destination.parent)
            _fsync_directory(paths.runs)
        except (EvidenceError, OSError):
            unresolved.append(run_id)
    return tuple(unresolved)


def _acquire_lock(directory: Path) -> Path:
    lock = directory / ".write.lock"
    try:
        descriptor = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise EvidenceError("run-locked", "run is locked") from exc
    os.close(descriptor)
    _fsync_directory(directory)
    return lock


def _publish_file_no_replace(path: Path, payload: bytes, hook: _Hook | None) -> bool:
    temp = path.parent / f".{path.name}.{os.getpid()}.{secrets.token_hex(8)}.tmp"
    _write_private(temp, payload)
    if hook is not None:
        hook("review-temp-fsynced", temp)
    try:
        try:
            os.link(temp, path, follow_symlinks=False)
            created = True
        except FileExistsError:
            created = False
        except OSError as exc:
            raise EvidenceError("atomic-create-unsupported", "atomic file publication is unavailable") from exc
        _fsync_directory(path.parent)
        return created
    finally:
        try:
            temp.unlink()
        except FileNotFoundError:
            pass
        _fsync_directory(path.parent)


def _existing_review_result(paths: EvidencePaths, run_id: str, payload: bytes | None = None, *, reason: str | None = None) -> WriteResult | None:
    directory = _find_run_directory(paths, run_id)
    final = directory / "review.json"
    if _lstat(final) is None:
        return None
    _validate_regular(final)
    existing = validate_review(read_bounded_json(final, REVIEW_HARD_LIMIT))
    existing_bytes = canonical_json_bytes(existing)
    matches = payload is not None and hmac.compare_digest(existing_bytes, payload)
    if reason is not None:
        result = existing["result"]
        matches = result["completion"] == "abandoned" and result["completion_reason"] == reason
    if not matches:
        _fail("already-finalized", "conflicting retry")
    pending = directory / ".pending.json"
    try:
        pending.unlink()
    except FileNotFoundError:
        pass
    for artifact in directory.iterdir():
        if artifact.name == ".write.lock" or (artifact.name.startswith(".review.json.") and artifact.name.endswith(".tmp")):
            try:
                artifact.unlink()
            except FileNotFoundError:
                pass
    _fsync_directory(directory)
    return WriteResult(run_id, sha256_payload(existing_bytes), final)


def _write_terminal(paths: EvidencePaths, run_id: str, review: object, hook: _Hook | None) -> WriteResult:
    normalized = validate_review(review)
    if normalized["run_id"] != run_id:
        _fail("schema-invalid", "review run ID does not match")
    payload = canonical_json_bytes(normalized)
    existing = _existing_review_result(paths, run_id, payload)
    if existing is not None:
        return existing
    directory = _find_run_directory(paths, run_id)
    pending = _load_pending_path(directory / ".pending.json")
    if pending["run_id"] != run_id:
        _fail("schema-invalid", "pending run ID does not match")
    if (
        normalized["started_at"] != pending["started_at"]
        or normalized["skill"] != pending["skill"]
        or normalized["client"] != pending["client"]
        or normalized["target"] != pending["target"]
        or normalized["protocol"]["mode"] != pending["intended_mode"]
    ):
        _fail("schema-invalid", "review does not preserve pending identity and target facts")
    lock = _acquire_lock(directory)
    try:
        created = _publish_file_no_replace(directory / "review.json", payload, hook)
        if not created:
            retry = _existing_review_result(paths, run_id, payload)
            if retry is None:
                _fail("already-finalized", "conflicting retry")
            return retry
        if hook is not None:
            hook("review-published", directory / "review.json")
        try:
            (directory / ".pending.json").unlink()
        except FileNotFoundError:
            pass
        _fsync_directory(directory)
        return WriteResult(run_id, sha256_payload(payload), directory / "review.json")
    finally:
        try:
            lock.unlink()
        except FileNotFoundError:
            pass
        _fsync_directory(directory)


def finish_review(paths: EvidencePaths, run_id: str, review: object, *, interruption_hook: _Hook | None = None) -> WriteResult:
    return _write_terminal(paths, run_id, review, interruption_hook)


def _milliseconds(started_at: str, completed_at: str) -> int:
    try:
        start = dt.datetime.fromisoformat(started_at[:-1] + "+00:00")
        end = dt.datetime.fromisoformat(completed_at[:-1] + "+00:00")
    except (TypeError, ValueError) as exc:
        raise EvidenceError("invalid-time", "completion time is invalid") from exc
    return max(0, int((end - start).total_seconds() * 1000))


def abandon_run(
    paths: EvidencePaths,
    run_id: str,
    reason: str,
    *,
    completed_at: str,
    recorder_elapsed_ms: int,
    interruption_hook: _Hook | None = None,
) -> WriteResult:
    if not isinstance(reason, str) or _REASON.fullmatch(reason) is None:
        _fail("invalid-reason", "completion reason is invalid")
    try:
        existing = _existing_review_result(paths, run_id, reason=reason)
    except EvidenceError as exc:
        if exc.code != "run-not-found":
            raise
        existing = None
    if existing is not None:
        return existing
    pending = load_pending(paths, run_id)
    review = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "review",
        "run_id": run_id,
        "started_at": pending["started_at"],
        "completed_at": completed_at,
        "skill": pending["skill"],
        "client": pending["client"],
        "protocol": {"mode": pending["intended_mode"], "execution": "unknown", "reviewer_count": 0, "fresh_reviewer": False, "read_only_enforced": False, "conditional_trigger": None, "degraded_reasons": []},
        "target": pending["target"],
        "result": {"completion": "abandoned", "verdict": None, "block_reason": None, "completion_reason": reason, "review_passes": 0, "repair_passes": 0, "findings": []},
        "freshness": {"final_head": None, "final_dirty": None, "plan_final_sha256": None, "design_final_sha256": None},
        "metrics": {"elapsed_ms": _milliseconds(str(pending["started_at"]), completed_at), "recorder_elapsed_ms": recorder_elapsed_ms, "reviewer_count": 0, "review_passes": 0, "repair_passes": 0, "token_usage": None},
    }
    return _write_terminal(paths, run_id, review, interruption_hook)


def load_review(paths: EvidencePaths, run_id: str) -> dict[str, object]:
    directory = _find_run_directory(paths, run_id)
    final = directory / "review.json"
    try:
        _validate_regular(final)
        return validate_review(read_bounded_json(final, REVIEW_HARD_LIMIT))
    except FileNotFoundError as exc:
        raise EvidenceError("run-not-found", "review was not found") from exc


def _parse_time(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(value[:-1] + "+00:00")


def _now(value: str | None) -> dt.datetime:
    if value is not None:
        return _parse_time(value)
    return dt.datetime.now(dt.timezone.utc)


def _run_directories(paths: EvidencePaths) -> list[Path]:
    runs_info = _lstat(paths.runs)
    if runs_info is None:
        return []
    if (
        stat.S_ISLNK(runs_info.st_mode)
        or not stat.S_ISDIR(runs_info.st_mode)
        or not _is_private(runs_info)
    ):
        return []
    result: list[Path] = []
    for year in paths.runs.iterdir():
        year_info = _lstat(year)
        if (
            year.name.startswith(".")
            or year_info is None
            or stat.S_ISLNK(year_info.st_mode)
            or not stat.S_ISDIR(year_info.st_mode)
            or not _is_private(year_info)
        ):
            continue
        for month in year.iterdir():
            month_info = _lstat(month)
            if (
                month_info is None
                or stat.S_ISLNK(month_info.st_mode)
                or not stat.S_ISDIR(month_info.st_mode)
                or not _is_private(month_info)
            ):
                continue
            for run in month.iterdir():
                run_info = _lstat(run)
                if (
                    run_info is not None
                    and not stat.S_ISLNK(run_info.st_mode)
                    and stat.S_ISDIR(run_info.st_mode)
                    and _is_private(run_info)
                    and _RUN_ID.fullmatch(run.name)
                ):
                    result.append(run)
    return sorted(result)


def scan_runs(paths: EvidencePaths, *, now: str | None = None) -> ScanResult:
    reviews: list[dict[str, object]] = []
    pending_entries: list[PendingEntry] = []
    corrupt: list[str] = []
    instant = _now(now)
    for directory in _run_directories(paths):
        final = directory / "review.json"
        pending_path = directory / ".pending.json"
        try:
            if _lstat(final) is not None:
                reviews.append(load_review(paths, directory.name))
                continue
            if _lstat(pending_path) is not None:
                pending = _load_pending_path(pending_path)
                age = instant - _parse_time(str(pending["started_at"]))
                age_class = "stale" if age > dt.timedelta(days=7) else "interrupted" if age > dt.timedelta(hours=24) else "active"
                target = pending["target"]
                assert isinstance(target, dict)
                pending_entries.append(PendingEntry(directory.name, str(pending["started_at"]), str(target["resolution_status"]), target["plan_path"], target["design_path"], age_class))
        except (EvidenceError, OSError, ValueError):
            corrupt.append(directory.name)
    return ScanResult(tuple(reviews), tuple(pending_entries), tuple(corrupt))


def doctor(paths: EvidencePaths) -> tuple[dict[str, str], ...]:
    issues: list[dict[str, str]] = []

    home_info = _lstat(paths.home)
    if home_info is None:
        return ()
    if (
        stat.S_ISLNK(home_info.st_mode)
        or not stat.S_ISDIR(home_info.st_mode)
        or not _is_private(home_info)
    ):
        return ({"code": "unsafe-evidence-home", "run_id": "evidence-home"},)
    runs_info = _lstat(paths.runs)
    if runs_info is None:
        return ()
    if (
        stat.S_ISLNK(runs_info.st_mode)
        or not stat.S_ISDIR(runs_info.st_mode)
        or not _is_private(runs_info)
    ):
        return ({"code": "unsafe-runs-root", "run_id": "runs"},)

    safe_runs: list[Path] = []
    for year in sorted(paths.runs.iterdir(), key=lambda item: item.name):
        if year.name.startswith(".staging-"):
            staging_info = _lstat(year)
            if staging_info is None or stat.S_ISLNK(staging_info.st_mode) or not stat.S_ISDIR(staging_info.st_mode) or not _is_private(staging_info):
                issues.append({"code": "unsafe-run-entry", "run_id": year.name[9:]})
            else:
                issues.append({"code": "stranded-staging", "run_id": year.name[9:]})
            continue
        year_info = _lstat(year)
        if year_info is None or stat.S_ISLNK(year_info.st_mode) or not stat.S_ISDIR(year_info.st_mode) or not _is_private(year_info) or re.fullmatch(r"[0-9]{4}", year.name) is None:
            issues.append({"code": "unsafe-run-entry", "run_id": year.name})
            continue
        for month in sorted(year.iterdir(), key=lambda item: item.name):
            month_info = _lstat(month)
            if month_info is None or stat.S_ISLNK(month_info.st_mode) or not stat.S_ISDIR(month_info.st_mode) or not _is_private(month_info) or re.fullmatch(r"(?:0[1-9]|1[0-2])", month.name) is None:
                issues.append({"code": "unsafe-run-entry", "run_id": month.name})
                continue
            for run in sorted(month.iterdir(), key=lambda item: item.name):
                run_info = _lstat(run)
                if run_info is None or stat.S_ISLNK(run_info.st_mode) or not stat.S_ISDIR(run_info.st_mode) or not _is_private(run_info) or _RUN_ID.fullmatch(run.name) is None:
                    issues.append({"code": "unsafe-run-entry", "run_id": run.name})
                    continue
                safe_runs.append(run)

    instant = dt.datetime.now(dt.timezone.utc)
    for directory in safe_runs:
        run_id = directory.name
        final = directory / "review.json"
        pending_path = directory / ".pending.json"
        try:
            if _lstat(final) is not None:
                _validate_regular(final)
                raw = read_bounded_json(final, REVIEW_HARD_LIMIT)
                if not isinstance(raw, dict):
                    raise EvidenceError("invalid-json", "review is not an object")
                if raw.get("schema_version") != SCHEMA_VERSION:
                    issues.append({"code": "unsupported-schema-version", "run_id": run_id})
                    continue
                skill = raw.get("skill")
                if not isinstance(skill, dict) or skill.get("cli_version") != CLI_VERSION:
                    issues.append({"code": "incompatible-cli", "run_id": run_id})
                    continue
                validate_review(raw)
            elif _lstat(pending_path) is not None:
                _validate_regular(pending_path)
                raw_pending = read_bounded_json(pending_path, PENDING_HARD_LIMIT)
                if not isinstance(raw_pending, dict):
                    raise EvidenceError("invalid-json", "pending record is not an object")
                if raw_pending.get("schema_version") != SCHEMA_VERSION:
                    issues.append({"code": "unsupported-schema-version", "run_id": run_id})
                    continue
                pending_skill = raw_pending.get("skill")
                if not isinstance(pending_skill, dict) or pending_skill.get("cli_version") != CLI_VERSION:
                    issues.append({"code": "incompatible-cli", "run_id": run_id})
                    continue
                pending = _validate_pending(raw_pending)
                if instant - _parse_time(str(pending["started_at"])) > dt.timedelta(days=7):
                    issues.append({"code": "stale-pending", "run_id": run_id})
        except EvidenceError as exc:
            code = "unsafe-receipt-entry" if exc.code == "unsafe-evidence-path" else "corrupt-record"
            issues.append({"code": code, "run_id": run_id})
        except (OSError, ValueError):
            issues.append({"code": "corrupt-record", "run_id": run_id})
        for item in directory.iterdir():
            if item.name == ".write.lock" or item.name.endswith(".tmp"):
                issues.append({"code": "abandoned-artifact", "run_id": run_id})
    return tuple(issues)
