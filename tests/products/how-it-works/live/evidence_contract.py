"""Pure lexical observations and declared metadata binding, not execution proof."""

import re
from datetime import date

DIMENSIONS = ("fence", "hop_ids", "skill_loading", "mermaid_syntax", "meaning")
METHODS = {
    "fence": {"lexical"}, "hop_ids": {"lexical"},
    "skill_loading": {"host_event"},
    "mermaid_syntax": {"parser", "renderer"},
    "meaning": {"semantic_review"},
}
FIELDS = {"schema_version", "product", "product_version", "payload_sha256", "model",
          "host", "client_version", "runner_version", "executed_on", "cases"}


def observe_text(text: str) -> dict[str, dict[str, str]]:
    # Lexical markers only: this deliberately does not parse Mermaid or infer loading.
    result = {name: {"status": "not_measured", "method": "not_run"} for name in DIMENSIONS}
    blocks = re.findall(r"(?ms)^```mermaid[ \t]*\n(.*?)^```[ \t]*$", text)
    result["fence"] = {"status": "pass" if blocks and all(b.strip() for b in blocks) else "fail",
                       "method": "lexical"}
    if result["fence"]["status"] == "pass":
        source_ids = set(re.findall(r"\bH[1-9][0-9]*\b", "\n".join(blocks)))
        prose = re.sub(r"(?ms)^```.*?^```[ \t]*$", "", text)
        list_ids = re.findall(r"(?m)^\s*[0-9]+\.\s+\*\*(H[1-9][0-9]*)\*\*", prose)
        match = bool(source_ids) and source_ids == set(list_ids) and len(list_ids) == len(set(list_ids))
        result["hop_ids"] = {"status": "pass" if match else "fail", "method": "lexical"}
    return result


def record_binding(record: dict, *, current_version: str, current_hash: str) -> str:
    if not isinstance(record, dict):
        raise ValueError("record must be a dictionary")
    if type(record.get("schema_version")) is not int:
        raise ValueError("schema_version must be an integer")
    if record["schema_version"] == 1:
        if set(record) != {"schema_version", "executed_on", "hosts"}:
            raise ValueError("invalid historical record fields")
        if not isinstance(record["executed_on"], str):
            raise ValueError("invalid executed_on")
        date.fromisoformat(record["executed_on"])
        if not isinstance(record["hosts"], list):
            raise ValueError("invalid historical hosts")
        return "historical-unbound"
    if record["schema_version"] != 2 or set(record) != FIELDS:
        raise ValueError("invalid current record fields")
    if record["product"] != "how-it-works":
        raise ValueError("invalid product")
    for key in ("product_version", "host", "client_version", "runner_version", "executed_on"):
        if not isinstance(record[key], str) or not record[key].strip():
            raise ValueError(f"invalid {key}")
    date.fromisoformat(record["executed_on"])
    if record["host"] not in {"codex", "claude-code", "grok", "cursor"}:
        raise ValueError("invalid host")
    if not isinstance(record["payload_sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", record["payload_sha256"]):
        raise ValueError("invalid payload hash")
    if record["model"] is not None and (not isinstance(record["model"], str) or not record["model"].strip()):
        raise ValueError("invalid model")
    if not isinstance(record["cases"], dict) or not record["cases"]:
        raise ValueError("invalid cases")
    for case_id, case in record["cases"].items():
        if not isinstance(case_id, str) or not case_id or not isinstance(case, dict):
            raise ValueError("invalid case")
        if set(case) != {"invocation", "dimensions"} or not isinstance(case["invocation"], str) or case["invocation"] not in {"pass", "fail", "not_measured"}:
            raise ValueError("invalid invocation")
        if not isinstance(case["dimensions"], dict) or set(case["dimensions"]) != set(DIMENSIONS):
            raise ValueError("invalid dimensions")
        for name, item in case["dimensions"].items():
            if not isinstance(item, dict) or set(item) != {"status", "method"}:
                raise ValueError("invalid dimension")
            if not isinstance(item["status"], str) or item["status"] not in {"pass", "fail", "not_measured"}:
                raise ValueError("invalid status")
            allowed = {"not_run"} if item["status"] == "not_measured" else METHODS[name]
            if not isinstance(item["method"], str) or item["method"] not in allowed:
                raise ValueError("invalid evidence method")
    # A valid declaration binds metadata only, even when every dimension is unmeasured.
    if record["model"] is None:
        return "unbound"
    if record["product_version"] != current_version or record["payload_sha256"] != current_hash:
        return "different-payload"
    return "current-bounded"
