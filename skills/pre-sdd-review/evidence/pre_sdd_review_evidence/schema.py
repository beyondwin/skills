from __future__ import annotations

import copy
import datetime as dt
import json
import re
import uuid
from pathlib import Path
from typing import Any

from . import CLI_VERSION, SCHEMA_VERSION


REVIEW_HARD_LIMIT = 32 * 1024
OUTCOME_HARD_LIMIT = 8 * 1024
VERDICTS = frozenset({"READY", "REVISE", "BLOCKED"})
FINDING_SEVERITIES = frozenset({"BLOCKER", "IMPORTANT"})
FINDING_CLASSES = frozenset(
    {"authority-drift", "repo-reality", "coverage", "ordering", "verification-gap"}
)
CLIENT_IDS = frozenset({"codex", "claude-code", "cursor", "grok", "other", "unknown"})
MODES = frozenset({"default", "review-only"})
EXECUTIONS = frozenset({"full", "degraded", "blocked", "unknown"})
CONDITIONAL_TRIGGERS = frozenset(
    {"runtime-removal", "schema-migration", "auth-boundary", "data-boundary", "external-side-effect"}
)
DEGRADED_REASONS = frozenset(
    {"fresh-reviewer-unavailable", "read-only-unavailable", "conditional-reviewer-unavailable", "host-capability-unknown", "other"}
)
RESOLUTION_STATUSES = frozenset(
    {"resolved", "plan-missing", "spec-field-missing", "spec-path-invalid", "design-missing", "outside-repository", "not-git-repository"}
)
FINDING_STATUSES = frozenset({"repaired", "unresolved", "blocked-by-authority", "accepted-as-is"})
CONSEQUENCE_CATEGORIES = frozenset(
    {"escaped-material-defect", "avoidable-rework", "false-block", "protocol-degradation", "input-resolution-failure", "other"}
)
DOWNSTREAM_STATUSES = frozenset({"sdd-completed", "implementation-completed", "implementation-abandoned", "cancelled"})
ASSESSMENT_LABELS = frozenset({"good", "false-ready", "noisy", "prevented-rework", "inconclusive", "abandoned"})
EVIDENCE_BASES = frozenset({"verified-repository-evidence", "user-reported", "agent-observed", "agent-inferred", "unknown"})
CONFIDENCES = frozenset({"low", "medium", "high"})

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_GIT = re.compile(r"(?:unborn|[0-9a-f]{40}|[0-9a-f]{64})\Z")
_REASON = re.compile(r"[a-z0-9][a-z0-9._-]{0,99}\Z")
_PATTERN = re.compile(r"[a-z0-9][a-z0-9._-]*\Z")
_FINDING_ID = re.compile(r"PSDR-[0-9]{3,}\Z")
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")
_RFC3339_UTC = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?Z\Z"
)


class EvidenceError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def read_bounded_bytes(path: Path, limit: int) -> bytes:
    if not isinstance(limit, int) or isinstance(limit, bool) or limit < 0:
        raise EvidenceError("invalid-limit", "limit must be a non-negative integer")
    with Path(path).open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise EvidenceError("record-too-large", f"file exceeds {limit} bytes")
    return data


def read_bounded_json(path: Path, limit: int) -> object:
    data = read_bounded_bytes(path, limit)
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise EvidenceError("invalid-json", "file is not valid UTF-8 JSON") from exc
    return parse_json_text(text, name="file")


def parse_json_text(
    value: str, *, byte_limit: int | None = None, name: str = "value"
) -> object:
    if not isinstance(value, str):
        raise EvidenceError("invalid-json", f"{name} is not valid UTF-8 JSON")
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise EvidenceError(
            "invalid-json", f"{name} is not valid UTF-8 JSON"
        ) from exc
    if byte_limit is not None and len(encoded) > byte_limit:
        raise EvidenceError(
            "record-too-large", f"{name} exceeds the hard size limit"
        )
    try:
        return json.loads(value)
    except (UnicodeError, ValueError) as exc:
        raise EvidenceError(
            "invalid-json", f"{name} is not valid UTF-8 JSON"
        ) from exc


def _fail(code: str, message: str) -> None:
    raise EvidenceError(code, message)


def _object(value: object, name: str, keys: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        _fail("invalid-type", f"{name} must be an object")
    actual = set(value)
    if actual != keys:
        detail = (
            "unknown keys"
            if actual - keys
            else f"missing keys: {', '.join(sorted(keys - actual))}"
        )
        _fail("invalid-keys", f"{name} has {detail}")
    return value


def _string(value: object, name: str, maximum: int, *, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str):
        _fail("invalid-type", f"{name} must be a string")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise EvidenceError(
            "invalid-string", f"{name} must be valid UTF-8"
        ) from exc
    if not value or len(value) > maximum or _CONTROL.search(value):
        _fail("invalid-string", f"{name} must be a non-empty single-line string within {maximum} characters")
    return value


def _enum(value: object, name: str, values: frozenset[str], *, nullable: bool = False) -> str | None:
    result = _string(value, name, 500, nullable=nullable)
    if result is not None and result not in values:
        _fail("invalid-enum", f"{name} is not an allowed value")
    return result


def _integer(value: object, name: str, minimum: int = 0, maximum: int | None = None) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum or (maximum is not None and value > maximum):
        _fail("invalid-integer", f"{name} is outside its allowed range")
    return value


def _boolean(value: object, name: str, *, nullable: bool = False) -> bool | None:
    if value is None and nullable:
        return None
    if not isinstance(value, bool):
        _fail("invalid-type", f"{name} must be a boolean")
    return value


def _sha(value: object, name: str, *, nullable: bool = False) -> str | None:
    result = _string(value, name, 64, nullable=nullable)
    if result is not None and not _SHA.fullmatch(result):
        _fail("invalid-sha256", f"{name} must be a lowercase SHA-256")
    return result


def _timestamp(value: object, name: str) -> str:
    result = _string(value, name, 30)
    assert result is not None
    if not _RFC3339_UTC.fullmatch(result):
        _fail("invalid-time", f"{name} must be an extended UTC RFC 3339 timestamp")
    try:
        dt.datetime.fromisoformat(result[:-1] + "+00:00")
    except ValueError as exc:
        raise EvidenceError("invalid-time", f"{name} must be RFC 3339") from exc
    return result


def _run_id(value: object) -> str:
    result = _string(value, "run_id", 36)
    assert result is not None
    try:
        parsed = uuid.UUID(result)
    except ValueError as exc:
        raise EvidenceError("invalid-run-id", "run_id must be a canonical lowercase UUID") from exc
    if str(parsed) != result:
        _fail("invalid-run-id", "run_id must be a canonical lowercase UUID")
    return result


def _safe_reference(value: object, name: str, maximum: int = 500, *, nullable: bool = False) -> str | None:
    result = _string(value, name, maximum, nullable=nullable)
    if result is None:
        return None
    components = result.split("/")
    if (
        "\\" in result
        or result.startswith("/")
        or re.match(r"^[A-Za-z]:/", result)
        or any(component in {"", ".", ".."} for component in components)
    ):
        _fail("unsafe-path", f"{name} must be a safe relative reference")
    return result


def _deduplicate(values: list[Any]) -> list[Any]:
    result: list[Any] = []
    seen: set[bytes] = set()
    for value in values:
        encoded = canonical_json_bytes(value)
        if encoded not in seen:
            seen.add(encoded)
            result.append(value)
    return result


def _client(value: object, name: str, *, key: str = "id") -> dict[str, Any]:
    data = _object(value, name, {key, "version", "model"})
    _enum(data[key], f"{name}.{key}", CLIENT_IDS)
    _string(data["version"], f"{name}.version", 100, nullable=True)
    _string(data["model"], f"{name}.model", 100, nullable=True)
    return copy.deepcopy(data)


def _validate_target(value: object) -> dict[str, Any]:
    data = _object(value, "target", {"repo_id", "initial_head", "initial_dirty", "plan_path", "plan_initial_sha256", "design_path", "design_initial_sha256", "resolution_status"})
    _string(data["repo_id"], "target.repo_id", 200, nullable=True)
    head = _string(data["initial_head"], "target.initial_head", 64, nullable=True)
    if head is not None and not _GIT.fullmatch(head): _fail("invalid-git", "target.initial_head is invalid")
    _boolean(data["initial_dirty"], "target.initial_dirty", nullable=True)
    _safe_reference(data["plan_path"], "target.plan_path", nullable=True)
    _sha(data["plan_initial_sha256"], "target.plan_initial_sha256", nullable=True)
    _safe_reference(data["design_path"], "target.design_path", nullable=True)
    _sha(data["design_initial_sha256"], "target.design_initial_sha256", nullable=True)
    _enum(data["resolution_status"], "target.resolution_status", RESOLUTION_STATUSES)
    return copy.deepcopy(data)


def _validate_freshness(value: object) -> dict[str, Any]:
    data = _object(value, "freshness", {"final_head", "final_dirty", "plan_final_sha256", "design_final_sha256"})
    head = _string(data["final_head"], "freshness.final_head", 64, nullable=True)
    if head is not None and not _GIT.fullmatch(head): _fail("invalid-git", "freshness.final_head is invalid")
    _boolean(data["final_dirty"], "freshness.final_dirty", nullable=True)
    _sha(data["plan_final_sha256"], "freshness.plan_final_sha256", nullable=True)
    _sha(data["design_final_sha256"], "freshness.design_final_sha256", nullable=True)
    return copy.deepcopy(data)


def _validate_finding(value: object) -> dict[str, Any]:
    data = _object(value, "finding", {"id", "severity", "class", "pattern_key", "consequence_category", "status", "location", "evidence_refs", "consequence", "minimal_fix", "repair_pass"})
    identifier = _string(data["id"], "finding.id", 100)
    if identifier is None or not _FINDING_ID.fullmatch(identifier): _fail("invalid-finding-id", "finding.id is invalid")
    _enum(data["severity"], "finding.severity", FINDING_SEVERITIES)
    _enum(data["class"], "finding.class", FINDING_CLASSES)
    pattern = _string(data["pattern_key"], "finding.pattern_key", 80)
    if pattern is None or not _PATTERN.fullmatch(pattern): _fail("invalid-pattern-key", "finding.pattern_key is invalid")
    _enum(data["consequence_category"], "finding.consequence_category", CONSEQUENCE_CATEGORIES)
    _enum(data["status"], "finding.status", FINDING_STATUSES)
    location = _object(data["location"], "finding.location", {"path", "locator"})
    _safe_reference(location["path"], "finding.location.path")
    _string(location["locator"], "finding.location.locator", 200)
    if not isinstance(data["evidence_refs"], list): _fail("invalid-type", "finding.evidence_refs must be a list")
    references = [_safe_reference(item, "finding.evidence_refs[]") for item in data["evidence_refs"]]
    _string(data["consequence"], "finding.consequence", 300)
    _string(data["minimal_fix"], "finding.minimal_fix", 300)
    repair_pass = data["repair_pass"]
    if repair_pass is not None: _integer(repair_pass, "finding.repair_pass", 1, 2)
    normalized = copy.deepcopy(data)
    normalized["evidence_refs"] = _deduplicate(references)
    return normalized


def _resolution_invariants(target: dict[str, Any], freshness: dict[str, Any], *, abandoned: bool) -> None:
    status = target["resolution_status"]
    keys = ("repo_id", "initial_head", "initial_dirty")
    if status == "not-git-repository":
        if any(target[key] is not None for key in (*keys, "plan_path", "plan_initial_sha256", "design_path", "design_initial_sha256")):
            _fail("resolution-nullability", "not-git-repository requires all target facts to be null")
    elif any(target[key] is None for key in keys):
        _fail("resolution-nullability", "repository facts must be available for this resolution status")
    if status == "resolved":
        required = ("plan_path", "plan_initial_sha256", "design_path", "design_initial_sha256")
        if any(target[key] is None for key in required): _fail("resolution-nullability", "resolved requires both document paths and hashes")
    elif status == "plan-missing":
        if target["plan_path"] is None or any(target[key] is not None for key in ("plan_initial_sha256", "design_path", "design_initial_sha256")):
            _fail("resolution-nullability", "plan-missing has an invalid target projection")
    elif status in {"spec-field-missing", "spec-path-invalid"}:
        if target["plan_path"] is None or target["plan_initial_sha256"] is None or target["design_path"] is not None or target["design_initial_sha256"] is not None:
            _fail("resolution-nullability", "spec resolution failure has an invalid target projection")
    elif status == "design-missing":
        if target["plan_path"] is None or target["plan_initial_sha256"] is None or target["design_path"] is None or target["design_initial_sha256"] is not None:
            _fail("resolution-nullability", "design-missing has an invalid target projection")
    elif status == "outside-repository":
        if target["design_path"] is not None or target["design_initial_sha256"] is not None:
            _fail("resolution-nullability", "outside-repository cannot retain a design reference")
        if (target["plan_path"] is None) != (target["plan_initial_sha256"] is None):
            _fail("resolution-nullability", "outside-repository plan values must be retained together")
    if abandoned:
        if any(value is not None for value in freshness.values()): _fail("freshness-nullability", "abandoned reviews require all-null freshness")
        return
    if status == "not-git-repository":
        if any(value is not None for value in freshness.values()): _fail("freshness-nullability", "not-git-repository requires all-null freshness")
        return
    if freshness["final_head"] is None or freshness["final_dirty"] is None:
        _fail("freshness-nullability", "repository freshness facts must be available")
    if (target["plan_initial_sha256"] is None) != (freshness["plan_final_sha256"] is None):
        _fail("freshness-nullability", "plan freshness must mirror initial availability")
    if (target["design_initial_sha256"] is None) != (freshness["design_final_sha256"] is None):
        _fail("freshness-nullability", "design freshness must mirror initial availability")


def validate_review(value: object) -> dict[str, object]:
    data = _object(value, "review", {"schema_version", "record_type", "run_id", "started_at", "completed_at", "skill", "client", "protocol", "target", "result", "freshness", "metrics"})
    if data["schema_version"] != SCHEMA_VERSION or data["record_type"] != "review": _fail("schema-version", "review schema identity is invalid")
    _run_id(data["run_id"])
    _timestamp(data["started_at"], "started_at")
    _timestamp(data["completed_at"], "completed_at")
    skill = _object(data["skill"], "skill", {"name", "declared_version", "release_version", "skill_sha256", "reviewer_protocol_sha256", "release_manifest_sha256", "cli_version", "schema_version"})
    if skill["name"] != "pre-sdd-review" or skill["declared_version"] != skill["release_version"] or skill["cli_version"] != CLI_VERSION or skill["schema_version"] != SCHEMA_VERSION:
        _fail("skill-identity", "skill identity does not match the running recorder")
    _string(skill["declared_version"], "skill.declared_version", 100)
    for key in ("skill_sha256", "reviewer_protocol_sha256", "release_manifest_sha256"): _sha(skill[key], f"skill.{key}")
    client = _client(data["client"], "client")
    protocol = _object(data["protocol"], "protocol", {"mode", "execution", "reviewer_count", "fresh_reviewer", "read_only_enforced", "conditional_trigger", "degraded_reasons"})
    _enum(protocol["mode"], "protocol.mode", MODES)
    execution = _enum(protocol["execution"], "protocol.execution", EXECUTIONS)
    reviewer_count = _integer(protocol["reviewer_count"], "protocol.reviewer_count", 0, 2)
    fresh = _boolean(protocol["fresh_reviewer"], "protocol.fresh_reviewer")
    readonly = _boolean(protocol["read_only_enforced"], "protocol.read_only_enforced")
    trigger = _enum(protocol["conditional_trigger"], "protocol.conditional_trigger", CONDITIONAL_TRIGGERS, nullable=True)
    if not isinstance(protocol["degraded_reasons"], list): _fail("invalid-type", "protocol.degraded_reasons must be a list")
    reasons = [_enum(item, "protocol.degraded_reasons[]", DEGRADED_REASONS) for item in protocol["degraded_reasons"]]
    reasons = _deduplicate(reasons)
    if execution == "full" and (not fresh or not readonly or reasons or reviewer_count != (2 if trigger is not None else 1)):
        _fail("protocol-invariant", "full protocol requires fresh read-only reviewers and no degraded reasons")
    if execution == "degraded" and not reasons: _fail("protocol-invariant", "degraded protocol requires a reason")
    target = _validate_target(data["target"])
    freshness = _validate_freshness(data["freshness"])
    result = _object(data["result"], "result", {"completion", "verdict", "block_reason", "completion_reason", "review_passes", "repair_passes", "findings"})
    completion = _enum(result["completion"], "result.completion", frozenset({"completed", "abandoned"}))
    verdict = _enum(result["verdict"], "result.verdict", VERDICTS, nullable=True)
    block = _string(result["block_reason"], "result.block_reason", 100, nullable=True)
    reason = _string(result["completion_reason"], "result.completion_reason", 100, nullable=True)
    for name, item in (("result.block_reason", block), ("result.completion_reason", reason)):
        if item is not None and not _REASON.fullmatch(item): _fail("invalid-reason", f"{name} is invalid")
    review_passes = _integer(result["review_passes"], "result.review_passes", 0, 3)
    repair_passes = _integer(result["repair_passes"], "result.repair_passes", 0, 2)
    if not isinstance(result["findings"], list): _fail("invalid-type", "result.findings must be a list")
    findings = [_validate_finding(item) for item in result["findings"]]
    if len({item["id"] for item in findings}) != len(findings): _fail("duplicate-finding", "finding IDs must be unique")
    if completion == "abandoned":
        if verdict is not None or block is not None or reason is None or review_passes != 0 or repair_passes != 0 or findings: _fail("completion-invariant", "abandoned review has invalid result fields")
    else:
        if verdict is None or reason is not None or review_passes < 1: _fail("completion-invariant", "completed review has invalid result fields")
        if verdict == "READY" and any(item["status"] != "repaired" for item in findings): _fail("verdict-invariant", "READY permits only repaired findings")
        if verdict == "REVISE" and not any(item["status"] == "unresolved" for item in findings): _fail("verdict-invariant", "REVISE requires an unresolved finding")
        if verdict == "BLOCKED" and block is None: _fail("verdict-invariant", "BLOCKED requires a block reason")
    for finding in findings:
        repair = finding["repair_pass"]
        if repair is not None and repair > repair_passes: _fail("repair-pass", "finding repair pass exceeds recorded repair passes")
    metrics = _object(data["metrics"], "metrics", {"elapsed_ms", "recorder_elapsed_ms", "reviewer_count", "review_passes", "repair_passes", "token_usage"})
    _integer(metrics["elapsed_ms"], "metrics.elapsed_ms")
    _integer(metrics["recorder_elapsed_ms"], "metrics.recorder_elapsed_ms")
    if metrics["reviewer_count"] != reviewer_count or metrics["review_passes"] != review_passes or metrics["repair_passes"] != repair_passes:
        _fail("mirrored-count", "review and metric counts must match")
    _integer(metrics["reviewer_count"], "metrics.reviewer_count", 0, 2)
    _integer(metrics["review_passes"], "metrics.review_passes", 0, 3)
    _integer(metrics["repair_passes"], "metrics.repair_passes", 0, 2)
    token_usage = metrics["token_usage"]
    if token_usage is not None:
        token = _object(token_usage, "metrics.token_usage", {"input", "output", "total", "provenance"})
        if _integer(token["total"], "metrics.token_usage.total") != _integer(token["input"], "metrics.token_usage.input") + _integer(token["output"], "metrics.token_usage.output"): _fail("token-total", "token total must equal input plus output")
        _string(token["provenance"], "metrics.token_usage.provenance", 100)
    _resolution_invariants(target, freshness, abandoned=completion == "abandoned")
    normalized = copy.deepcopy(data)
    normalized["client"] = client
    normalized["target"] = target
    normalized["freshness"] = freshness
    normalized["protocol"] = copy.deepcopy(protocol)
    normalized["protocol"]["degraded_reasons"] = reasons
    normalized["result"] = copy.deepcopy(result)
    normalized["result"]["findings"] = findings
    if len(canonical_json_bytes(normalized)) > REVIEW_HARD_LIMIT: _fail("record-too-large", "review exceeds the hard size limit")
    return normalized


def derive_assessment(review: dict[str, object], downstream: dict[str, object]) -> str:
    status = downstream.get("status")
    if status in ("implementation-abandoned", "cancelled"): return "abandoned"
    escaped = downstream.get("escaped_findings", [])
    disputed = downstream.get("disputed_findings", [])
    prevented = downstream.get("prevented_rework", [])
    if review.get("result", {}).get("verdict") == "READY" and escaped: return "false-ready"
    if disputed: return "noisy"
    if prevented: return "prevented-rework"
    if status in ("sdd-completed", "implementation-completed") and not escaped and not disputed: return "good"
    return "inconclusive"


def _strongest_basis(records: list[dict[str, Any]]) -> str:
    order = {"verified-repository-evidence": 0, "user-reported": 1, "agent-observed": 2, "agent-inferred": 3, "unknown": 4}
    return min((item["basis"] for item in records), key=order.__getitem__)


def validate_outcome(value: object, review: object) -> dict[str, object]:
    normalized_review = validate_review(review)
    data = _object(value, "outcome", {"schema_version", "record_type", "run_id", "recorded_at", "recorder", "downstream", "assessment"})
    if data["schema_version"] != SCHEMA_VERSION or data["record_type"] != "outcome": _fail("schema-version", "outcome schema identity is invalid")
    outcome_run_id = _run_id(data["run_id"])
    if outcome_run_id != normalized_review["run_id"]:
        _fail("schema-invalid", "outcome run ID must match the review")
    _timestamp(data["recorded_at"], "recorded_at")
    if (
        isinstance(data["assessment"], dict)
        and data["assessment"].get("label") == "false-ready"
        and normalized_review["result"]["verdict"] != "READY"
    ):
        _fail("assessment-label", "false-ready requires READY")
    recorder = _client(data["recorder"], "recorder", key="client")
    downstream = _object(data["downstream"], "downstream", {"status", "plan_hash_matched", "replan_count", "evaluated_finding_ids", "escaped_findings", "disputed_findings", "prevented_rework"})
    _enum(downstream["status"], "downstream.status", DOWNSTREAM_STATUSES)
    if downstream["plan_hash_matched"] is not True: _fail("plan-hash", "plan_hash_matched must be true")
    _integer(downstream["replan_count"], "downstream.replan_count")
    findings = {item["id"]: item for item in normalized_review["result"]["findings"]}
    if not isinstance(downstream["evaluated_finding_ids"], list): _fail("invalid-type", "evaluated_finding_ids must be a list")
    evaluated = [_string(item, "downstream.evaluated_finding_ids[]", 100) for item in downstream["evaluated_finding_ids"]]
    if len(set(evaluated)) != len(evaluated) or any(item not in findings for item in evaluated): _fail("finding-link", "evaluated finding IDs must be unique review findings")
    escaped: list[dict[str, Any]] = []
    if not isinstance(downstream["escaped_findings"], list): _fail("invalid-type", "escaped_findings must be a list")
    for item in downstream["escaped_findings"]:
        record = _object(item, "escaped_finding", {"severity", "class", "pattern_key", "consequence_category", "basis"})
        _enum(record["severity"], "escaped_finding.severity", FINDING_SEVERITIES)
        _enum(record["class"], "escaped_finding.class", FINDING_CLASSES)
        pattern = _string(record["pattern_key"], "escaped_finding.pattern_key", 80)
        if pattern is None or not _PATTERN.fullmatch(pattern): _fail("invalid-pattern-key", "escaped_finding.pattern_key is invalid")
        _enum(record["consequence_category"], "escaped_finding.consequence_category", CONSEQUENCE_CATEGORIES)
        _enum(record["basis"], "escaped_finding.basis", EVIDENCE_BASES)
        escaped.append(copy.deepcopy(record))
    disputed: list[dict[str, Any]] = []
    prevented: list[dict[str, Any]] = []
    for field, destination in (("disputed_findings", disputed), ("prevented_rework", prevented)):
        if not isinstance(downstream[field], list): _fail("invalid-type", f"{field} must be a list")
        keys = {"finding_id", "class", "pattern_key", "consequence_category", "basis"} if field == "disputed_findings" else {"finding_id", "pattern_key", "consequence_category", "basis"}
        for item in downstream[field]:
            record = _object(item, field, keys)
            identifier = _string(record["finding_id"], f"{field}.finding_id", 100)
            if identifier not in findings or identifier not in evaluated: _fail("finding-link", f"{field} must reference an evaluated review finding")
            source = findings[identifier]
            if field == "disputed_findings" and record["class"] != source["class"]: _fail("finding-copy", "disputed finding class must match review finding")
            if record["pattern_key"] != source["pattern_key"] or record["consequence_category"] != source["consequence_category"]: _fail("finding-copy", f"{field} must copy review finding fields")
            if field == "prevented_rework" and source["status"] != "repaired": _fail("prevention-status", "prevented rework requires a repaired finding")
            _enum(record["basis"], f"{field}.basis", EVIDENCE_BASES)
            destination.append(copy.deepcopy(record))
    if len(_deduplicate(escaped)) != len(escaped) or len(_deduplicate(disputed)) != len(disputed) or len(_deduplicate(prevented)) != len(prevented): _fail("duplicate-record", "downstream records must be unique")
    normalized_downstream = copy.deepcopy(downstream)
    normalized_downstream["evaluated_finding_ids"] = _deduplicate(evaluated)
    normalized_downstream["escaped_findings"] = _deduplicate(escaped)
    normalized_downstream["disputed_findings"] = _deduplicate(disputed)
    normalized_downstream["prevented_rework"] = _deduplicate(prevented)
    label = derive_assessment(normalized_review, normalized_downstream)
    assessment = _object(data["assessment"], "assessment", {"label", "basis", "confidence"})
    if assessment["label"] != label: _fail("assessment-label", f"{assessment['label']} assessment is not derived as {label}")
    _enum(assessment["label"], "assessment.label", ASSESSMENT_LABELS)
    basis = _enum(assessment["basis"], "assessment.basis", EVIDENCE_BASES)
    _enum(assessment["confidence"], "assessment.confidence", CONFIDENCES)
    sufficient = escaped if label == "false-ready" else disputed if label == "noisy" else prevented if label == "prevented-rework" else []
    if sufficient and basis != _strongest_basis(sufficient): _fail("assessment-basis", "assessment basis must use the strongest triggering evidence")
    normalized = copy.deepcopy(data)
    normalized["recorder"] = recorder
    normalized["downstream"] = normalized_downstream
    if len(canonical_json_bytes(normalized)) > OUTCOME_HARD_LIMIT: _fail("record-too-large", "outcome exceeds the hard size limit")
    return normalized
