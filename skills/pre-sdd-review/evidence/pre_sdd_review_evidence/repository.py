from __future__ import annotations

import datetime as dt
import hashlib
import hmac
import os
import re
import secrets
import stat
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from . import CLI_VERSION, SCHEMA_VERSION
from .schema import (
    EvidenceError,
    canonical_json_bytes,
    read_bounded_bytes,
    read_bounded_json,
)


IDENTITY_KEY_LIMIT = 32
IDENTITY_CONFIG_LIMIT = 1024
DOCUMENT_LIMIT = 8 * 1024 * 1024
SKILL_DOCUMENT_LIMIT = 256 * 1024

_SPEC_MARKER = "**Spec:**"
_PLAIN_SPEC = re.compile(r"^\*\*Spec:\*\*[ \t]*(\S+)[ \t]*$")
_INLINE_SPEC = re.compile(r"^\*\*Spec:\*\*[ \t]*`([^`\r\n]+)`[ \t]*$")
_WINDOWS_ABSOLUTE = re.compile(r"^[A-Za-z]:[/\\]")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


@dataclass(frozen=True)
class GitSnapshot:
    head: str
    dirty: bool


@dataclass(frozen=True)
class SkillSnapshot:
    name: str
    declared_version: str
    release_version: str
    skill_sha256: str
    reviewer_protocol_sha256: str
    release_manifest_sha256: str
    cli_version: str
    schema_version: int


@dataclass(frozen=True)
class TargetSnapshot:
    repo_id: str | None
    initial_head: str | None
    initial_dirty: bool | None
    plan_path: str | None
    plan_initial_sha256: str | None
    design_path: str | None
    design_initial_sha256: str | None
    resolution_status: str


def _fail(code: str, message: str) -> None:
    raise EvidenceError(code, message)


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
        text=True,
    )


def _git_root(locator: Path) -> Path:
    result = _git(Path(locator), "rev-parse", "--show-toplevel")
    if result.returncode != 0:
        _fail("not-git-repository", "repository locator is not inside a Git repository")
    output = result.stdout.strip()
    if not output or "\n" in output or "\r" in output:
        _fail("not-git-repository", "Git returned an invalid repository root")
    return Path(output).resolve()


def git_snapshot(repo_root: Path) -> GitSnapshot:
    root = _git_root(Path(repo_root))
    head_result = _git(root, "rev-parse", "--verify", "HEAD")
    if head_result.returncode == 0:
        head = head_result.stdout.strip().lower()
        if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", head):
            _fail("git-state-invalid", "Git returned an invalid HEAD")
    else:
        unborn = _git(root, "symbolic-ref", "-q", "HEAD")
        if unborn.returncode != 0:
            _fail("git-state-invalid", "Git HEAD is unavailable")
        head = "unborn"
    status_result = _git(
        root,
        "status",
        "--porcelain=v1",
        "--untracked-files=normal",
    )
    if status_result.returncode != 0:
        _fail("git-state-invalid", "Git status is unavailable")
    return GitSnapshot(head=head, dirty=bool(status_result.stdout))


def repository_id(repo_root: Path, identity_key: bytes) -> str:
    if not isinstance(identity_key, bytes) or len(identity_key) != IDENTITY_KEY_LIMIT:
        _fail("identity-state-invalid", "identity key must contain exactly 32 bytes")
    canonical = str(Path(repo_root).resolve()).encode("utf-8")
    return hmac.new(identity_key, canonical, hashlib.sha256).hexdigest()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _document_bytes(path: Path) -> bytes:
    return read_bounded_bytes(path, DOCUMENT_LIMIT)


def _target(
    *,
    repo_id_value: str | None,
    git: GitSnapshot | None,
    plan_path: str | None = None,
    plan_sha256: str | None = None,
    design_path: str | None = None,
    design_sha256: str | None = None,
    status: str,
) -> TargetSnapshot:
    return TargetSnapshot(
        repo_id=repo_id_value,
        initial_head=None if git is None else git.head,
        initial_dirty=None if git is None else git.dirty,
        plan_path=plan_path,
        plan_initial_sha256=plan_sha256,
        design_path=design_path,
        design_initial_sha256=design_sha256,
        resolution_status=status,
    )


def _lexically_safe_relative(value: str, *, allow_dot_prefix: bool) -> str | None:
    if (
        not value
        or "\\" in value
        or value.startswith("/")
        or value.startswith("~")
        or _WINDOWS_ABSOLUTE.match(value)
    ):
        return None
    candidate = value[2:] if allow_dot_prefix and value.startswith("./") else value
    if not candidate:
        return None
    parts = candidate.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        return None
    return PurePosixPath(*parts).as_posix()


def _inside(root: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(root)
    except ValueError:
        return False
    return True


def _plan_candidate(root: Path, plan_argument: Path) -> tuple[Path | None, str | None]:
    raw = os.fspath(plan_argument)
    if Path(plan_argument).is_absolute():
        resolved = Path(plan_argument).resolve()
        if not _inside(root, resolved):
            return None, None
        try:
            relative = Path(plan_argument).relative_to(root).as_posix()
        except ValueError:
            relative = resolved.relative_to(root).as_posix()
        safe = _lexically_safe_relative(relative, allow_dot_prefix=False)
        if safe is None:
            return None, None
        return root / safe, safe
    safe = _lexically_safe_relative(raw, allow_dot_prefix=True)
    if safe is None:
        return None, None
    lexical = root / safe
    resolved = lexical.resolve()
    if not _inside(root, resolved):
        return None, None
    return lexical, safe


def _parse_spec(plan_bytes: bytes) -> tuple[str | None, bool]:
    try:
        text = plan_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return None, True
    lines = [line for line in text.splitlines() if line.startswith(_SPEC_MARKER)]
    if not lines:
        return None, False
    if len(lines) != 1:
        return None, True
    line = lines[0]
    inline = _INLINE_SPEC.fullmatch(line)
    if inline is not None:
        value = inline.group(1)
        if not value.strip():
            return None, True
        return value, False
    plain = _PLAIN_SPEC.fullmatch(line)
    if plain is None:
        return None, True
    value = plain.group(1)
    if "`" in value:
        return None, True
    return value, False


def resolve_target(
    repo_root: Path, plan_argument: Path, identity_key: bytes
) -> TargetSnapshot:
    try:
        root = _git_root(Path(repo_root))
    except EvidenceError as exc:
        if exc.code == "not-git-repository":
            return _target(repo_id_value=None, git=None, status="not-git-repository")
        raise
    git = git_snapshot(root)
    repo_id_value = repository_id(root, identity_key)
    plan_file, plan_relative = _plan_candidate(root, Path(plan_argument))
    if plan_file is None or plan_relative is None:
        return _target(
            repo_id_value=repo_id_value,
            git=git,
            status="outside-repository",
        )
    if not plan_file.exists():
        return _target(
            repo_id_value=repo_id_value,
            git=git,
            plan_path=plan_relative,
            status="plan-missing",
        )
    resolved_plan = plan_file.resolve()
    if not _inside(root, resolved_plan) or not resolved_plan.is_file():
        return _target(
            repo_id_value=repo_id_value,
            git=git,
            status="outside-repository",
        )
    try:
        plan_bytes = _document_bytes(resolved_plan)
    except (OSError, EvidenceError):
        return _target(
            repo_id_value=repo_id_value,
            git=git,
            plan_path=plan_relative,
            status="spec-path-invalid",
        )
    plan_sha256 = _sha256(plan_bytes)
    spec_value, invalid = _parse_spec(plan_bytes)
    if invalid:
        return _target(
            repo_id_value=repo_id_value,
            git=git,
            plan_path=plan_relative,
            plan_sha256=plan_sha256,
            status="spec-path-invalid",
        )
    if spec_value is None:
        return _target(
            repo_id_value=repo_id_value,
            git=git,
            plan_path=plan_relative,
            plan_sha256=plan_sha256,
            status="spec-field-missing",
        )
    design_relative = _lexically_safe_relative(spec_value, allow_dot_prefix=True)
    if design_relative is None:
        return _target(
            repo_id_value=repo_id_value,
            git=git,
            plan_path=plan_relative,
            plan_sha256=plan_sha256,
            status="spec-path-invalid",
        )
    if spec_value.startswith("./"):
        design_file = plan_file.parent / design_relative
        try:
            persisted_design = design_file.relative_to(root).as_posix()
        except ValueError:
            persisted_design = ""
    else:
        design_file = root / design_relative
        persisted_design = design_relative
    resolved_design = design_file.resolve()
    if (
        not persisted_design
        or _lexically_safe_relative(persisted_design, allow_dot_prefix=False) is None
        or not _inside(root, resolved_design)
    ):
        return _target(
            repo_id_value=repo_id_value,
            git=git,
            plan_path=plan_relative,
            plan_sha256=plan_sha256,
            status="outside-repository",
        )
    if not design_file.exists():
        return _target(
            repo_id_value=repo_id_value,
            git=git,
            plan_path=plan_relative,
            plan_sha256=plan_sha256,
            design_path=persisted_design,
            status="design-missing",
        )
    if not resolved_design.is_file():
        return _target(
            repo_id_value=repo_id_value,
            git=git,
            plan_path=plan_relative,
            plan_sha256=plan_sha256,
            status="outside-repository",
        )
    try:
        design_bytes = _document_bytes(resolved_design)
    except (OSError, EvidenceError):
        return _target(
            repo_id_value=repo_id_value,
            git=git,
            plan_path=plan_relative,
            plan_sha256=plan_sha256,
            status="spec-path-invalid",
        )
    return _target(
        repo_id_value=repo_id_value,
        git=git,
        plan_path=plan_relative,
        plan_sha256=plan_sha256,
        design_path=persisted_design,
        design_sha256=_sha256(design_bytes),
        status="resolved",
    )


def _skill_frontmatter_identity(skill_bytes: bytes) -> tuple[str, str]:
    try:
        text = skill_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise EvidenceError("skill-state-invalid", "SKILL.md is not valid UTF-8") from exc
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        _fail("skill-state-invalid", "SKILL.md frontmatter is unavailable")
    frontmatter = text[4 : text.index("\n---\n", 4)]
    name_match = re.search(r"^name:[ \t]*([^\s]+)[ \t]*$", frontmatter, re.MULTILINE)
    version_match = re.search(
        r'^  version:[ \t]*["\']?([^\s"\']+)["\']?[ \t]*$',
        frontmatter,
        re.MULTILINE,
    )
    if name_match is None or version_match is None:
        _fail("skill-state-invalid", "skill name or declared version is unavailable")
    return name_match.group(1), version_match.group(1)


def load_skill_snapshot(skill_root: Path) -> SkillSnapshot:
    root = Path(skill_root).resolve()
    paths = {
        "skill": root / "SKILL.md",
        "protocol": root / "references/reviewer-protocol.md",
        "release": root / "release.toml",
    }
    try:
        payloads = {
            name: read_bounded_bytes(path, SKILL_DOCUMENT_LIMIT)
            for name, path in paths.items()
        }
    except (OSError, EvidenceError) as exc:
        raise EvidenceError("skill-state-invalid", "loaded skill files are unavailable") from exc
    name, declared_version = _skill_frontmatter_identity(payloads["skill"])
    try:
        release = tomllib.loads(payloads["release"].decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise EvidenceError("skill-state-invalid", "release.toml is invalid") from exc
    release_name = release.get("name")
    release_version = release.get("version")
    release_schema = release.get("schema_version")
    if (
        name != "pre-sdd-review"
        or release_name != name
        or not isinstance(release_version, str)
        or declared_version != release_version
        or release_schema != SCHEMA_VERSION
    ):
        _fail("skill-state-invalid", "declared and release versions or identities do not match")
    return SkillSnapshot(
        name=name,
        declared_version=declared_version,
        release_version=release_version,
        skill_sha256=_sha256(payloads["skill"]),
        reviewer_protocol_sha256=_sha256(payloads["protocol"]),
        release_manifest_sha256=_sha256(payloads["release"]),
        cli_version=CLI_VERSION,
        schema_version=SCHEMA_VERSION,
    )


def _lstat(path: Path) -> os.stat_result | None:
    try:
        return path.lstat()
    except FileNotFoundError:
        return None


def _private_mode(info: os.stat_result) -> bool:
    return os.name != "posix" or stat.S_IMODE(info.st_mode) & 0o077 == 0


def _validate_home(evidence_home: Path) -> None:
    info = _lstat(evidence_home)
    if info is None:
        try:
            evidence_home.mkdir(mode=0o700, parents=True, exist_ok=False)
        except FileExistsError:
            pass
        else:
            _fsync_directory(evidence_home.parent)
        info = evidence_home.lstat()
    if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode) or not _private_mode(info):
        _fail("identity-state-invalid", "evidence home must be a private real directory")


def _validate_identity_entry(path: Path) -> os.stat_result | None:
    info = _lstat(path)
    if info is None:
        return None
    if not stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode) or not _private_mode(info):
        _fail("identity-state-invalid", f"{path.name} must be a private regular file")
    return info


def _fsync_directory(directory: Path) -> None:
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    descriptor = os.open(directory, flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _write_candidate(path: Path, payload: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb", closefd=False) as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        os.close(descriptor)


def _publish_create_only(path: Path, payload: bytes) -> bool:
    candidate = path.parent / f".{path.name}.{os.getpid()}.{secrets.token_hex(8)}.candidate"
    _write_candidate(candidate, payload)
    try:
        try:
            os.link(candidate, path, follow_symlinks=False)
            won = True
        except FileExistsError:
            won = False
        _fsync_directory(path.parent)
        return won
    finally:
        try:
            candidate.unlink()
        except FileNotFoundError:
            pass
        _fsync_directory(path.parent)


def _created_at(key_info: os.stat_result) -> str:
    timestamp = dt.datetime(1970, 1, 1, tzinfo=dt.timezone.utc) + dt.timedelta(
        microseconds=key_info.st_mtime_ns // 1_000
    )
    return timestamp.isoformat(timespec="microseconds").replace("+00:00", "Z")


def _expected_config(key: bytes, key_info: os.stat_result) -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at": _created_at(key_info),
        "identity_key_sha256": _sha256(key),
    }


def _load_key(path: Path) -> bytes:
    try:
        payload = read_bounded_bytes(path, IDENTITY_KEY_LIMIT)
    except (OSError, EvidenceError) as exc:
        raise EvidenceError("identity-state-invalid", "identity key is unreadable or oversized") from exc
    if len(payload) != IDENTITY_KEY_LIMIT:
        _fail("identity-state-invalid", "identity key must contain exactly 32 bytes")
    return payload


def _load_and_validate_config(path: Path, expected: dict[str, object]) -> None:
    try:
        config = read_bounded_json(path, IDENTITY_CONFIG_LIMIT)
    except (OSError, EvidenceError) as exc:
        raise EvidenceError("identity-state-invalid", "identity config is unreadable or malformed") from exc
    if not isinstance(config, dict) or config != expected:
        _fail("identity-state-invalid", "identity config does not match the active key")
    fingerprint = config.get("identity_key_sha256")
    if not isinstance(fingerprint, str) or _SHA256.fullmatch(fingerprint) is None:
        _fail("identity-state-invalid", "identity config fingerprint is invalid")


def _publish_config(path: Path, expected: dict[str, object]) -> None:
    _publish_create_only(path, canonical_json_bytes(expected))


def load_or_create_identity(evidence_home: Path) -> bytes:
    home = Path(evidence_home)
    if not home.is_absolute():
        _fail("invalid-evidence-home", "evidence home must be absolute")
    home = home.resolve(strict=False)
    _validate_home(home)
    key_path = home / "identity.key"
    config_path = home / "config.json"
    key_info = _validate_identity_entry(key_path)
    config_info = _validate_identity_entry(config_path)
    if key_info is None and config_info is not None:
        _fail("identity-key-missing", "identity config exists without an identity key")
    if key_info is None:
        _publish_create_only(key_path, secrets.token_bytes(IDENTITY_KEY_LIMIT))
        key_info = _validate_identity_entry(key_path)
        if key_info is None:
            _fail("identity-state-invalid", "identity key publication failed")
    key = _load_key(key_path)
    expected = _expected_config(key, key_info)
    if config_info is None:
        _publish_config(config_path, expected)
        config_info = _validate_identity_entry(config_path)
        if config_info is None:
            _fail("identity-state-invalid", "identity config publication failed")
    _load_and_validate_config(config_path, expected)
    return key
