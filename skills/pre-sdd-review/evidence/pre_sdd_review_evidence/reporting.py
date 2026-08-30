from __future__ import annotations

import dataclasses
import datetime as dt
import hashlib
import hmac
import os
import re
import shutil
import stat
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path

from . import SCHEMA_VERSION, repository, storage
from .schema import (
    CLIENT_IDS,
    CONSEQUENCE_CATEGORIES,
    DEGRADED_REASONS,
    FINDING_CLASSES,
    OUTCOME_HARD_LIMIT,
    REVIEW_HARD_LIMIT,
    RESOLUTION_STATUSES,
    EvidenceError,
    canonical_json_bytes,
    read_bounded_bytes,
)


_CANDIDATE_FILES = ("design.md", "plan.md", "repository.json", "expected.json")
_CANDIDATE_ID = re.compile(r"[0-9a-f]{64}\Z")
_INPUT_FAILURES = {
    "plan-missing",
    "spec-field-missing",
    "spec-path-invalid",
    "design-missing",
    "outside-repository",
    "not-git-repository",
}


@dataclasses.dataclass(frozen=True)
class MatchResult:
    status: str
    run_id: str | None
    candidate_run_ids: tuple[str, ...]


@dataclasses.dataclass(frozen=True)
class Record:
    review: dict[str, object]
    outcome: dict[str, object] | None = None
    directory: Path | None = None
    review_sha256: str | None = None
    outcome_sha256: str | None = None
    review_bytes: int | None = None
    outcome_bytes: int | None = None


@dataclasses.dataclass(frozen=True)
class Candidate:
    schema_version: int
    candidate_id: str
    kind: str
    source_run_count: int
    group: dict[str, str]
    required_synthetic_files: tuple[str, ...] = _CANDIDATE_FILES

    def payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "candidate_id": self.candidate_id,
            "kind": self.kind,
            "source_run_count": self.source_run_count,
            "group": self.group.copy(),
            "required_synthetic_files": list(self.required_synthetic_files),
        }


@dataclasses.dataclass(frozen=True)
class PruneSelection:
    cutoff: str
    include_without_outcome: bool
    runs: tuple[dict[str, object], ...]
    counts: dict[str, int]

    def payload(self) -> dict[str, object]:
        return {
            "schema_version": SCHEMA_VERSION,
            "cutoff": self.cutoff,
            "include_without_outcome": self.include_without_outcome,
            "runs": [item.copy() for item in self.runs],
            "counts": self.counts.copy(),
        }

    @property
    def digest(self) -> str:
        return hashlib.sha256(canonical_json_bytes(self.payload())).hexdigest()


def _fail(code: str, message: str) -> None:
    raise EvidenceError(code, message)


def _not_found() -> MatchResult:
    return MatchResult("not-found", None, ())


def load_existing_identity(paths: storage.EvidencePaths) -> bytes:
    key_info = repository._validate_identity_entry(paths.identity_key)
    config_info = repository._validate_identity_entry(paths.config)
    if key_info is None:
        if config_info is not None:
            _fail("identity-key-missing", "identity config exists without an identity key")
        _fail("identity-key-missing", "identity key is unavailable")
    if config_info is None:
        # The approved identity contract makes key-only state recoverable.
        return repository.load_or_create_identity(paths.home)
    key = repository._load_key(paths.identity_key)
    repository._load_and_validate_config(
        paths.config, repository._expected_config(key, key_info)
    )
    return key


def resolve_review(
    paths: storage.EvidencePaths, repo_root: Path, plan_path: Path
) -> MatchResult:
    key = load_existing_identity(paths)
    try:
        root = repository._git_root(Path(repo_root))
        plan_file, relative = repository._plan_candidate(root, Path(plan_path))
    except EvidenceError:
        return _not_found()
    if plan_file is None or relative is None:
        return _not_found()
    resolved = plan_file.resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        return _not_found()
    if not resolved.is_file():
        return _not_found()
    try:
        current_hash = hashlib.sha256(
            read_bounded_bytes(resolved, repository.DOCUMENT_LIMIT)
        ).hexdigest()
    except (EvidenceError, OSError):
        return _not_found()

    repo_id = repository.repository_id(root, key)
    same_target: list[str] = []
    exact: list[str] = []
    for review in storage.scan_runs(paths).reviews:
        target = review["target"]
        freshness = review["freshness"]
        if not isinstance(target, dict) or not isinstance(freshness, dict):
            continue
        if target["repo_id"] != repo_id or target["plan_path"] != relative:
            continue
        run_id = str(review["run_id"])
        same_target.append(run_id)
        if freshness["plan_final_sha256"] == current_hash:
            exact.append(run_id)
    exact = sorted(exact)
    if len(exact) == 1:
        return MatchResult("matched", exact[0], tuple(exact))
    if len(exact) > 1:
        return MatchResult("ambiguous", None, tuple(exact))
    if same_target:
        return MatchResult("stale", None, ())
    return _not_found()


def _fingerprint(path: Path, limit: int) -> tuple[str, int]:
    payload = read_bounded_bytes(path, limit)
    return hashlib.sha256(payload).hexdigest(), len(payload)


def load_records(paths: storage.EvidencePaths) -> tuple[Record, ...]:
    """Load validated completed receipt pairs without consulting identity state."""
    records: list[Record] = []
    for directory in storage._run_directories(paths):
        try:
            review = storage.load_review(paths, directory.name)
            review_sha, review_bytes = _fingerprint(directory / "review.json", REVIEW_HARD_LIMIT)
        except (EvidenceError, OSError):
            continue
        outcome: dict[str, object] | None = None
        outcome_sha: str | None = None
        outcome_bytes: int | None = None
        outcome_path = directory / "outcome.json"
        if storage._lstat(outcome_path) is not None:
            try:
                outcome = storage.load_outcome(paths, directory.name)
                outcome_sha, outcome_bytes = _fingerprint(outcome_path, OUTCOME_HARD_LIMIT)
            except (EvidenceError, OSError):
                continue
        records.append(
            Record(
                review, outcome, directory, review_sha, outcome_sha,
                review_bytes, outcome_bytes,
            )
        )
    return tuple(sorted(records, key=lambda item: str(item.review["run_id"])))


def _rate(numerator: int, denominator: int) -> dict[str, object]:
    interpretation = (
        "not_measured"
        if denominator == 0
        else "insufficient-sample"
        if denominator < 10
        else "observed-rate"
    )
    return {"numerator": numerator, "denominator": denominator, "interpretation": interpretation}


def _integer_stats(values: Sequence[int]) -> dict[str, int]:
    return {
        "count": len(values),
        "total": sum(values),
        "minimum": min(values, default=0),
        "maximum": max(values, default=0),
    }


def summarize(
    records: Sequence[Record],
    pending: Sequence[storage.PendingEntry] = (),
) -> dict[str, object]:
    completed = [
        record
        for record in records
        if isinstance(record.review.get("result"), dict)
        and record.review["result"]["completion"] == "completed"  # type: ignore[index]
    ]
    with_outcomes = [record for record in completed if record.outcome is not None]
    verified_ready = [
        record
        for record in with_outcomes
        if record.review["result"]["verdict"] == "READY"  # type: ignore[index]
        and record.review["protocol"]["execution"] == "full"  # type: ignore[index]
        and record.outcome["assessment"]["basis"] == "verified-repository-evidence"  # type: ignore[index,union-attr]
    ]
    verified_false_ready = sum(
        record.outcome["assessment"]["label"] == "false-ready"  # type: ignore[index,union-attr]
        for record in verified_ready
    )
    evaluated = 0
    disputed = 0
    prevented_records = 0
    prevented_runs = 0
    protocol_counts = Counter({key: 0 for key in ("full", "degraded", "blocked", "unknown")})
    protocol_by_client: dict[str, Counter[str]] = defaultdict(
        lambda: Counter({key: 0 for key in ("full", "degraded", "blocked", "unknown")})
    )
    client_slices: dict[str, dict[str, Counter[str]]] = defaultdict(lambda: defaultdict(Counter))
    repository_slices: Counter[str] = Counter()
    trigger_counts: Counter[str] = Counter()
    degraded_reason_counts: Counter[str] = Counter()
    degraded_reasons_by_client: dict[str, Counter[str]] = defaultdict(Counter)
    basis_counts: Counter[str] = Counter()
    finding_counts: Counter[tuple[str, str, str]] = Counter()
    elapsed_values: list[int] = []
    recorder_elapsed_values: list[int] = []
    reviewer_values: list[int] = []
    review_pass_values: list[int] = []
    repair_pass_values: list[int] = []
    receipt_sizes: list[int] = []
    for record in completed:
        protocol = record.review["protocol"]
        client = record.review["client"]
        target = record.review["target"]
        assert isinstance(protocol, dict) and isinstance(client, dict) and isinstance(target, dict)
        execution = str(protocol["execution"])
        client_id = str(client["id"])
        protocol_counts[execution] += 1
        protocol_by_client[client_id][execution] += 1
        for reason in protocol["degraded_reasons"]:
            degraded_reason = str(reason)
            degraded_reason_counts[degraded_reason] += 1
            degraded_reasons_by_client[client_id][degraded_reason] += 1
        repo_id = target.get("repo_id")
        repository_slices["unavailable" if repo_id is None else str(repo_id)] += 1
        trigger = protocol["conditional_trigger"]
        if trigger is not None:
            trigger_counts[str(trigger)] += 1
        review_result = record.review["result"]
        metrics = record.review["metrics"]
        assert isinstance(review_result, dict) and isinstance(metrics, dict)
        for finding in review_result["findings"]:
            finding_counts[(
                str(finding["class"]),
                str(finding["pattern_key"]),
                str(finding["consequence_category"]),
            )] += 1
        elapsed_values.append(int(metrics["elapsed_ms"]))
        recorder_elapsed_values.append(int(metrics["recorder_elapsed_ms"]))
        reviewer_values.append(int(metrics["reviewer_count"]))
        review_pass_values.append(int(metrics["review_passes"]))
        repair_pass_values.append(int(metrics["repair_passes"]))
        review_size = record.review_bytes
        if review_size is None:
            review_size = len(canonical_json_bytes(record.review))
        outcome_size = record.outcome_bytes
        if outcome_size is None and record.outcome is not None:
            outcome_size = len(canonical_json_bytes(record.outcome))
        receipt_sizes.append(review_size + (outcome_size or 0))
        if record.outcome is None:
            client_slices[client_id][execution]["not_measured"] += 1
            continue
        downstream = record.outcome["downstream"]
        assessment = record.outcome["assessment"]
        assert isinstance(downstream, dict) and isinstance(assessment, dict)
        evaluated += len(downstream["evaluated_finding_ids"])
        disputed += len(downstream["disputed_findings"])
        prevention_count = len(downstream["prevented_rework"])
        prevented_records += prevention_count
        prevented_runs += prevention_count > 0
        client_slices[client_id][execution][str(assessment["label"])] += 1
        client_slices[client_id][execution][f"basis:{assessment['basis']}"] += 1
        basis_counts[str(assessment["basis"])] += 1
    pending_counts = Counter({key: 0 for key in ("active", "interrupted", "stale")})
    pending_counts.update(item.age_class for item in pending)
    return {
        "schema_version": SCHEMA_VERSION,
        "assessment_boundary": "observer-supplied-self-improvement-evidence-not-audit-grade",
        "completed_reviews": len(completed),
        "outcome_coverage": _rate(len(with_outcomes), len(completed)),
        "missing_outcomes": {"count": len(completed) - len(with_outcomes), "interpretation": "not_measured"},
        "verified_false_ready": _rate(verified_false_ready, len(verified_ready)),
        "noisy_findings": _rate(disputed, evaluated),
        "prevented_rework": {"records": prevented_records, "runs": prevented_runs},
        "protocol_counts": dict(sorted(protocol_counts.items())),
        "protocol_by_client": {client: dict(sorted(counts.items())) for client, counts in sorted(protocol_by_client.items())},
        "client_protocol_outcomes": {
            client: {execution: dict(sorted(counts.items())) for execution, counts in sorted(executions.items())}
            for client, executions in sorted(client_slices.items())
        },
        "anonymous_repository_counts": dict(sorted(repository_slices.items())),
        "conditional_trigger_counts": dict(sorted(trigger_counts.items())),
        "degraded_reason_counts": dict(sorted(degraded_reason_counts.items())),
        "degraded_reasons_by_client": {
            client: dict(sorted(counts.items()))
            for client, counts in sorted(degraded_reasons_by_client.items())
        },
        "assessment_basis_counts": dict(sorted(basis_counts.items())),
        "finding_groups": [
            {
                "finding_class": group[0],
                "pattern_key": group[1],
                "consequence_category": group[2],
                "count": count,
            }
            for group, count in sorted(finding_counts.items())
        ],
        "operational_overhead": {
            "elapsed_ms": _integer_stats(elapsed_values),
            "recorder_elapsed_ms": _integer_stats(recorder_elapsed_values),
            "reviewer_count": _integer_stats(reviewer_values),
            "review_passes": _integer_stats(review_pass_values),
            "repair_passes": _integer_stats(repair_pass_values),
            "receipt_bytes": _integer_stats(receipt_sizes),
        },
        "pending_age_classes": dict(sorted(pending_counts.items())),
    }


def _candidate_identity(kind: str, group: Mapping[str, str]) -> str:
    return hashlib.sha256(canonical_json_bytes({"schema_version": SCHEMA_VERSION, "kind": kind, "group": dict(group)})).hexdigest()


def _candidate(kind: str, group: dict[str, str], run_ids: set[str]) -> Candidate:
    return Candidate(SCHEMA_VERSION, _candidate_identity(kind, group), kind, len(run_ids), group)


def select_candidates(records: Sequence[Record]) -> tuple[Candidate, ...]:
    escaped: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    disputed: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    immediate: set[tuple[str, str, str]] = set()
    degraded: dict[tuple[str, str], set[str]] = defaultdict(set)
    resolution: dict[str, set[str]] = defaultdict(set)
    for record in records:
        review = record.review
        run_id = str(review["run_id"])
        target = review["target"]
        protocol = review["protocol"]
        client = review["client"]
        result = review["result"]
        assert isinstance(target, dict) and isinstance(protocol, dict)
        assert isinstance(client, dict) and isinstance(result, dict)
        resolution_status = str(target["resolution_status"])
        if resolution_status in _INPUT_FAILURES:
            resolution[resolution_status].add(run_id)
        if protocol["execution"] == "degraded":
            for reason in protocol["degraded_reasons"]:
                degraded[(str(client["id"]), str(reason))].add(run_id)
        if record.outcome is None:
            continue
        downstream = record.outcome["downstream"]
        assessment = record.outcome["assessment"]
        assert isinstance(downstream, dict) and isinstance(assessment, dict)
        for item in downstream["escaped_findings"]:
            group = (str(item["class"]), str(item["pattern_key"]), str(item["consequence_category"]))
            escaped[group].add(run_id)
            if assessment["label"] == "false-ready" or item["class"] == "authority-drift":
                immediate.add(group)
        findings_by_id = {item["id"]: item for item in result["findings"] if isinstance(item, dict)}
        for item in downstream["disputed_findings"]:
            group = (str(item["class"]), str(item["pattern_key"]), str(item["consequence_category"]))
            disputed[group].add(run_id)
            source = findings_by_id.get(item["finding_id"])
            if item["basis"] in {"verified-repository-evidence", "user-reported"} and source is not None and source["severity"] in {"BLOCKER", "IMPORTANT"}:
                immediate.add(group)
    candidates: list[Candidate] = []
    for group_tuple in set(escaped) | set(disputed) | immediate:
        sources = escaped[group_tuple] | disputed[group_tuple]
        if group_tuple not in immediate and len(escaped[group_tuple]) < 2 and len(disputed[group_tuple]) < 3:
            continue
        candidates.append(_candidate("finding-pattern", {
            "finding_class": group_tuple[0],
            "pattern_key": group_tuple[1],
            "consequence_category": group_tuple[2],
        }, sources))
    for (client_id, reason), run_ids in degraded.items():
        if len(run_ids) >= 3:
            candidates.append(_candidate("degraded-reason", {"client": client_id, "degraded_reason": reason}, run_ids))
    for status, run_ids in resolution.items():
        if len(run_ids) >= 5:
            candidates.append(_candidate("resolution-failure", {"resolution_status": status}, run_ids))
    return tuple(sorted(candidates, key=lambda item: item.candidate_id))


def _validate_real_directory(path: Path) -> None:
    try:
        info = path.lstat()
    except FileNotFoundError as exc:
        raise EvidenceError("unsafe-evidence-path", "export root is unavailable") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        _fail("unsafe-evidence-path", "export root must be a real directory")
    if os.name == "posix" and stat.S_IMODE(info.st_mode) & 0o077:
        _fail("unsafe-evidence-path", "export root must be private")


def _validate_candidate(candidate: Candidate) -> None:
    groups = {
        "finding-pattern": {
            "finding_class", "pattern_key", "consequence_category"
        },
        "degraded-reason": {"client", "degraded_reason"},
        "resolution-failure": {"resolution_status"},
    }
    expected = groups.get(candidate.kind)
    if (
        candidate.schema_version != SCHEMA_VERSION
        or expected is None
        or set(candidate.group) != expected
        or not isinstance(candidate.source_run_count, int)
        or isinstance(candidate.source_run_count, bool)
        or candidate.source_run_count < 1
        or candidate.required_synthetic_files != _CANDIDATE_FILES
        or _CANDIDATE_ID.fullmatch(candidate.candidate_id) is None
        or not hmac.compare_digest(
            candidate.candidate_id,
            _candidate_identity(candidate.kind, candidate.group),
        )
    ):
        _fail("schema-invalid", "candidate metadata is invalid")
    if candidate.kind == "finding-pattern":
        if (
            candidate.group["finding_class"] not in FINDING_CLASSES
            or candidate.group["consequence_category"] not in CONSEQUENCE_CATEGORIES
            or re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,79}", candidate.group["pattern_key"]) is None
        ):
            _fail("schema-invalid", "candidate finding group is invalid")
    elif candidate.kind == "degraded-reason":
        if candidate.group["client"] not in CLIENT_IDS or candidate.group["degraded_reason"] not in DEGRADED_REASONS:
            _fail("schema-invalid", "candidate degraded group is invalid")
    elif candidate.group["resolution_status"] not in RESOLUTION_STATUSES - {"resolved"}:
        _fail("schema-invalid", "candidate resolution group is invalid")


def export_candidate(candidate: Candidate, exports_root: Path) -> Path:
    _validate_candidate(candidate)
    root = Path(exports_root)
    _validate_real_directory(root)
    canonical_root = root.resolve(strict=True)
    if root.absolute() != canonical_root:
        _fail("unsafe-evidence-path", "export root must be canonical")
    if _CANDIDATE_ID.fullmatch(candidate.candidate_id) is None:
        _fail("schema-invalid", "candidate ID is invalid")
    destination = root / candidate.candidate_id
    try:
        destination.resolve(strict=False).relative_to(canonical_root)
    except ValueError as exc:
        raise EvidenceError("unsafe-evidence-path", "candidate export escaped the export root") from exc
    if storage._lstat(destination) is not None:
        _fail("already-exists", "candidate export already exists")
    staging = root / f".staging-export-{candidate.candidate_id}-{os.getpid()}"
    if storage._lstat(staging) is not None:
        _fail("already-exists", "candidate export staging already exists")
    staging.mkdir(mode=0o700)
    payloads = {
        "candidate.json": canonical_json_bytes(candidate.payload()),
        "design.md": b"# Design\n\n",
        "plan.md": b"# Plan\n\n**Spec:** ./design.md\n\n## Tasks\n",
        "repository.json": b"{}\n",
        "expected.json": b"{}\n",
    }
    try:
        for name, payload in payloads.items():
            storage._write_private(staging / name, payload)
        storage._fsync_directory(staging)
        try:
            storage.publish_directory_no_replace(staging, destination)
        except EvidenceError as exc:
            if exc.code == "already-exists":
                raise EvidenceError("already-exists", "candidate export already exists") from exc
            raise
        storage._fsync_directory(root)
        return destination
    except Exception:
        if staging.exists() and not staging.is_symlink():
            shutil.rmtree(staging)
            storage._fsync_directory(root)
        raise


def _parse_cutoff(value: str) -> dt.datetime:
    try:
        if (
            not isinstance(value, str)
            or re.fullmatch(
                r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?Z",
                value,
            )
            is None
        ):
            raise ValueError
        instant = dt.datetime.fromisoformat(value[:-1] + "+00:00")
    except (TypeError, ValueError) as exc:
        raise EvidenceError("invalid-time", "prune cutoff is invalid") from exc
    if instant.tzinfo != dt.timezone.utc:
        _fail("invalid-time", "prune cutoff must be UTC")
    return instant


def _completed_at(record: Record) -> dt.datetime:
    return _parse_cutoff(str(record.review["completed_at"]))


def preview_prune(records: Sequence[Record], cutoff: str, include_without_outcome: bool) -> PruneSelection:
    cutoff_time = _parse_cutoff(cutoff)
    selected: list[dict[str, object]] = []
    excluded_without_outcome = 0
    for record in records:
        result = record.review["result"]
        assert isinstance(result, dict)
        if result["completion"] != "completed" or _completed_at(record) > cutoff_time:
            continue
        if record.outcome is None and not include_without_outcome:
            excluded_without_outcome += 1
            continue
        if record.directory is None or record.review_sha256 is None:
            _fail("schema-invalid", "prune records must come from validated storage")
        selected.append({
            "run_id": str(record.review["run_id"]),
            "review_sha256": record.review_sha256,
            "outcome_sha256": record.outcome_sha256,
        })
    return PruneSelection(cutoff, bool(include_without_outcome), tuple(sorted(selected, key=lambda item: str(item["run_id"]))), {
        "selected": len(selected),
        "excluded_without_outcome": excluded_without_outcome,
    })


def _selection(value: object) -> PruneSelection:
    keys = {"schema_version", "cutoff", "include_without_outcome", "runs", "counts"}
    if not isinstance(value, dict) or set(value) != keys or value["schema_version"] != SCHEMA_VERSION:
        _fail("schema-invalid", "prune selection has invalid fields")
    if not isinstance(value["include_without_outcome"], bool):
        _fail("schema-invalid", "prune selection option is invalid")
    runs = value["runs"]
    counts = value["counts"]
    if not isinstance(runs, list) or not isinstance(counts, dict) or set(counts) != {"selected", "excluded_without_outcome"}:
        _fail("schema-invalid", "prune selection shape is invalid")
    normalized_runs: list[dict[str, object]] = []
    for item in runs:
        if not isinstance(item, dict) or set(item) != {"run_id", "review_sha256", "outcome_sha256"}:
            _fail("schema-invalid", "prune run selection is invalid")
        storage._validate_run_id(item["run_id"])
        if not isinstance(item["review_sha256"], str) or re.fullmatch(r"[0-9a-f]{64}", item["review_sha256"]) is None:
            _fail("schema-invalid", "prune review fingerprint is invalid")
        outcome_sha = item["outcome_sha256"]
        if outcome_sha is not None and (not isinstance(outcome_sha, str) or re.fullmatch(r"[0-9a-f]{64}", outcome_sha) is None):
            _fail("schema-invalid", "prune outcome fingerprint is invalid")
        normalized_runs.append(item.copy())
    if normalized_runs != sorted(normalized_runs, key=lambda item: str(item["run_id"])):
        _fail("schema-invalid", "prune run selection must be sorted")
    if len({item["run_id"] for item in normalized_runs}) != len(normalized_runs):
        _fail("schema-invalid", "prune run selection contains duplicates")
    if any(not isinstance(counts[key], int) or isinstance(counts[key], bool) or counts[key] < 0 for key in counts):
        _fail("schema-invalid", "prune counts are invalid")
    if counts["selected"] != len(normalized_runs):
        _fail("schema-invalid", "prune selected count is invalid")
    cutoff = value["cutoff"]
    _parse_cutoff(cutoff)
    assert isinstance(cutoff, str)
    return PruneSelection(cutoff, value["include_without_outcome"], tuple(normalized_runs), counts.copy())


def _current_selected_record(paths: storage.EvidencePaths, expected: dict[str, object], cutoff: dt.datetime, include_without_outcome: bool) -> Record:
    run_id = str(expected["run_id"])
    try:
        directory = storage._find_run_directory(paths, run_id)
        review = storage.load_review(paths, run_id)
        review_sha, review_bytes = _fingerprint(directory / "review.json", REVIEW_HARD_LIMIT)
    except (EvidenceError, OSError) as exc:
        raise EvidenceError("selection-changed", "prune selection changed") from exc
    outcome: dict[str, object] | None = None
    outcome_sha: str | None = None
    outcome_bytes: int | None = None
    outcome_path = directory / "outcome.json"
    if storage._lstat(outcome_path) is not None:
        try:
            outcome = storage.load_outcome(paths, run_id)
            outcome_sha, outcome_bytes = _fingerprint(outcome_path, OUTCOME_HARD_LIMIT)
        except (EvidenceError, OSError) as exc:
            raise EvidenceError("selection-changed", "prune selection changed") from exc
    record = Record(
        review, outcome, directory, review_sha, outcome_sha,
        review_bytes, outcome_bytes,
    )
    result = review["result"]
    assert isinstance(result, dict)
    current = {"run_id": run_id, "review_sha256": review_sha, "outcome_sha256": outcome_sha}
    if result["completion"] != "completed" or _completed_at(record) > cutoff or (outcome is None and not include_without_outcome) or expected != current:
        _fail("selection-changed", "prune selection changed")
    return record


def confirm_prune(paths: storage.EvidencePaths, selection: object, digest: str) -> tuple[str, ...]:
    normalized = _selection(selection)
    if not isinstance(digest, str) or not hmac.compare_digest(normalized.digest, digest):
        _fail("selection-changed", "prune selection digest does not match")
    load_existing_identity(paths)
    unresolved = storage.recover_staging(paths)
    selected_ids = {str(item["run_id"]) for item in normalized.runs}
    if selected_ids.intersection(unresolved):
        _fail("selection-changed", "prune selection changed due to unresolved staging")
    cutoff = _parse_cutoff(normalized.cutoff)
    locks: list[tuple[Path, Path]] = []
    try:
        for item in normalized.runs:
            try:
                directory = storage._find_run_directory(paths, str(item["run_id"]))
            except EvidenceError as exc:
                if exc.code == "run-not-found":
                    raise EvidenceError("selection-changed", "prune selection changed") from exc
                raise
            try:
                directory.resolve(strict=True).relative_to(paths.runs.resolve(strict=True))
            except ValueError as exc:
                raise EvidenceError("unsafe-evidence-path", "prune path escaped evidence root") from exc
            locks.append((directory, storage._acquire_lock(directory)))
        records = [_current_selected_record(paths, item, cutoff, normalized.include_without_outcome) for item in normalized.runs]
        for record in records:
            assert record.directory is not None
            parent = record.directory.parent
            shutil.rmtree(record.directory)
            storage._fsync_directory(parent)
        return tuple(str(item["run_id"]) for item in normalized.runs)
    finally:
        for directory, lock in locks:
            try:
                lock.unlink()
                storage._fsync_directory(directory)
            except FileNotFoundError:
                pass
