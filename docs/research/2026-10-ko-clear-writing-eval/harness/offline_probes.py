#!/usr/bin/env python3
"""Synthetic, provider-free boundary probes for an external kit (Python 3.9+).

Usage: /usr/bin/python3 offline_probes.py KIT_PATH [--output PATH]
Never changes the supplied kit or invokes a model. Every temporary repository
and input is generated here. Results contain hashes, not source-kit text.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

sys.dont_write_bytecode = True


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(kit, name):
    spec = importlib.util.spec_from_file_location(name, kit / "tools" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kit", type=Path)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "offline-results.json")
    args = parser.parse_args()
    initial_hashes = {"tools/" + name + ".py": digest(args.kit / "tools" / (name + ".py")) for name in ("writing_guard", "preflight", "git_snapshot")}
    guard, preflight, snapshot = [load(args.kit, name) for name in ("writing_guard", "preflight", "git_snapshot")]
    rows = []

    def record(identifier, classification, why, method, expected, observed, met):
        rows.append(dict(id=identifier, classification=classification, rationale=why,
                         method=method, expected=expected, observed=observed,
                         expectation_met=bool(met)))

    def guard_case(identifier, classification, source, output, contract, expected_block, why):
        result = guard.check(source, output, contract)
        blocked = result["decision"] == "blocked"
        record(identifier, classification, why,
               dict(source=source, output=output, contract=contract),
               "blocked" if expected_block else "review_required",
               result, blocked == expected_block)

    guard_case("G01", "positive_control", "최대 10 MB", "최대 10 GB",
               {"version": 1, "protected_spans": ["10 MB"]}, True,
               "Confirm literal mutation detection before interpreting negative probes.")
    guard_case("G02", "defect", "최대10회 재시도", "최대20회 재시도",
               {"version": 1, "preserve_numbers": True}, True,
               "Digits adjacent to Korean are common technical prose; numeric-token protection should detect the edit.")
    guard_case("G03", "boundary_gap", "임계값 1e3", "임계값 1e4",
               {"version": 1, "preserve_numbers": True}, True,
               "Scientific notation is numeric technical content, but no supported numeric grammar is documented.")
    guard_case("G04", "documented_limit", "값은 `alpha\nbeta`입니다.", "값은 `alpha\ngamma`입니다.",
               {"version": 1, "preserve_inline_code": True}, False,
               "The bounded recognizer explicitly excludes full Markdown parsing; multiline spans require an explicit protected span.")
    for identifier, contract, why in [
        ("G05", {"version": True}, "A Boolean is not schema version integer 1."),
        ("G06", {"version": 1, "format": []}, "Malformed format values must take the documented input-error path."),
        ("G07", {"version": 1, "json_shape": {"types": {"x": []}}}, "Malformed JSON field types must take the documented input-error path."),
    ]:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name, value in (("source", ""), ("output", ""), ("contract", json.dumps(contract))):
                (root / name).write_text(value, encoding="utf-8")
            result = subprocess.run([sys.executable, str(args.kit / "tools/writing_guard.py"),
                                     str(root / "source"), str(root / "output"), str(root / "contract"), "--json"],
                                    capture_output=True, text=True, timeout=10)
            observed = dict(exit_code=result.returncode, traceback="Traceback" in result.stderr,
                            input_error=result.stderr.startswith("Input error:"))
            record(identifier, "defect", why, dict(contract=contract),
                   dict(exit_code=2, traceback=False, input_error=True), observed,
                   observed == dict(exit_code=2, traceback=False, input_error=True))
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        (root / "source").write_text("retry=3", encoding="utf-8")
        (root / "output").write_text("retry=8", encoding="utf-8")
        ambiguous = '{"version":1,"protected_spans":["retry=3"],"protected_spans":[]}'
        (root / "contract").write_text(ambiguous, encoding="utf-8")
        result = subprocess.run([sys.executable, str(args.kit / "tools/writing_guard.py"),
                                 str(root / "source"), str(root / "output"), str(root / "contract"), "--json"],
                                capture_output=True, text=True, timeout=10)
        record("G08", "defect", "A duplicate contract key silently deletes a reviewed protection while output duplicate keys are rejected.",
               dict(source="retry=3", output="retry=8", contract_json=ambiguous),
               dict(exit_code=2), dict(exit_code=result.returncode, result=json.loads(result.stdout) if result.stdout.strip() else None), result.returncode == 2)
    guard_case("G09", "positive_control", "", '{"count":true}',
               {"version": 1, "format": "json", "json_shape": {"types": {"count": "integer"}}}, True,
               "Confirm JSON output type checks distinguish Boolean and integer.")

    def setup_preflight(root):
        (root / "AGENTS.md").write_text("<!-- BEGIN ko-clear-writing -->\nSynthetic policy.\n<!-- END ko-clear-writing -->\n", encoding="utf-8")
        (root / "CLAUDE.md").write_text("@AGENTS.md\n", encoding="utf-8")
        skill = root / ".agents/skills/ko-clear-writing/SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text("---\nname: ko-clear-writing\ndescription: Synthetic test fixture\n---\nSynthetic policy.\n", encoding="utf-8")
        return skill

    for identifier in ("P01", "P02", "P03"):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            skill = setup_preflight(root)
            if identifier == "P02":
                (root / "AGENTS.md").unlink()
                (root / "AGENTS.md").mkdir()
            if identifier == "P03":
                skill.write_text("---\nname: ko-clear-writing\ndescription: []\n---\nSynthetic policy.\n", encoding="utf-8")
            result = preflight.inspect(root)
            expected = identifier != "P01"
            record(identifier, "positive_control" if identifier == "P01" else "defect",
                   {"P01": "Confirm the synthetic canonical configuration is accepted.",
                    "P02": "A directory called AGENTS.md is not an instruction file.",
                    "P03": "An empty YAML array is not a nonempty string description; manual splitting cannot validate metadata types."}[identifier],
                   {"fixture": {"P01": "canonical files", "P02": "AGENTS.md directory", "P03": "description: []"}[identifier]},
                   {"has_error": expected}, result, bool(result["error_count"]) == expected)

    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        env = dict(os.environ)
        env["GIT_CONFIG_NOSYSTEM"] = "1"
        env["GIT_CONFIG_GLOBAL"] = os.devnull
        # Isolate synthetic Git fixtures from caller repository selectors and injected config.
        for key in list(env):
            if key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY", "GIT_COMMON_DIR", "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_CONFIG_PARAMETERS", "GIT_CONFIG_COUNT") or key.startswith(("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_")):
                env.pop(key, None)

        def git(*cmd):
            return subprocess.run(["git", "-C", str(root), *cmd], env=env,
                                  capture_output=True, check=True, timeout=10).stdout

        git("init", "-q")
        git("config", "user.name", "Synthetic Evaluator")
        git("config", "user.email", "synthetic@example.invalid")
        git("config", "commit.gpgsign", "false")
        (root / "service.txt").write_text("retry=1\n", encoding="utf-8")
        git("add", ".")
        git("commit", "-qm", "Synthetic baseline")
        first = git("rev-parse", "HEAD").decode().strip()
        git("commit", "--allow-empty", "-qm", "Synthetic second commit")
        second = git("rev-parse", "HEAD").decode().strip()
        (root / "service.txt").write_text("retry=3\n", encoding="utf-8")
        git("add", "service.txt")
        (root / "service.txt").write_text("retry=99\n", encoding="utf-8")
        old_env = dict(os.environ)
        os.environ.clear()
        os.environ.update(env)
        try:
            result = snapshot.snapshot(root)
            observed = dict(staged_retry_present="+retry=3" in result["staged_diff"],
                            unstaged_retry_absent="retry=99" not in result["staged_diff"])
            record("S01", "positive_control", "Confirm staged evidence excludes a later unstaged edit.",
                   dict(baseline=1, staged=3, unstaged=99),
                   dict(staged_retry_present=True, unstaged_retry_absent=True), observed, all(observed.values()))
            git("reset", "--hard", "-q", "HEAD")
            git("update-index", "--add", "--cacheinfo", "160000," + first + ",module")
            git("commit", "-qm", "Synthetic gitlink baseline")
            git("update-index", "--cacheinfo", "160000," + second + ",module")
            before = snapshot.snapshot(root)
            git("config", "diff.ignoreSubmodules", "all")
            after = snapshot.snapshot(root)
            observed = dict(default_empty=before["empty"], configured_empty=after["empty"],
                            configured_staged_paths=after["staged_paths"],
                            actual_staged_names=git("diff", "--cached", "--ignore-submodules=none", "--name-only").decode().splitlines())
            record("S02", "defect", "A valid local display setting can hide staged submodule updates from a purported index snapshot.",
                   dict(setting="diff.ignoreSubmodules=all", staged_change="gitlink commit changes"),
                   dict(configured_empty=False, configured_staged_paths=["module"]), observed,
                   not after["empty"] and after["staged_paths"] == ["module"])
            git("reset", "--hard", "-q", "HEAD")
            (root / "binary.dat").write_bytes(b"\x00SYNTHETIC-BINARY-PAYLOAD\xff")
            git("add", "binary.dat")
            result = snapshot.snapshot(root)
            observed = dict(path_present="binary.dat" in result["staged_paths"],
                            payload_visible="SYNTHETIC-BINARY-PAYLOAD" in result["staged_diff"],
                            binary_summary="Binary files" in result["staged_diff"])
            record("S03", "evidence_limit", "Default Git diffs identify binary changes without furnishing their contents; do not infer behavior from this snapshot alone.",
                   dict(staged_change="new synthetic binary file"),
                   dict(path_present=True, payload_visible=False, binary_summary=True), observed,
                   observed == dict(path_present=True, payload_visible=False, binary_summary=True))
        finally:
            os.environ.clear()
            os.environ.update(old_env)

    final_hashes = {relative: digest(args.kit / relative) for relative in initial_hashes}
    report = dict(schema_version=1, experiment="offline-boundaries-15",
                  executed_at_utc=datetime.now(timezone.utc).isoformat(),
                  runtime=dict(executable=sys.executable, python=platform.python_version(),
                               platform=platform.system(), release=platform.release(),
                               machine=platform.machine(), git=subprocess.run(["git", "--version"], capture_output=True, text=True, check=True).stdout.strip()),
                  policy=dict(provider_calls=0, source_tool_hashes_unchanged=initial_hashes == final_hashes, synthetic_only=True,
                              source_text_embedded=False, purpose="Boundary discovery, not pass-rate estimation or model quality evidence"),
                  source_hashes=initial_hashes,
                  harness_sha256=digest(Path(__file__)),
                  summary=dict(probes=len(rows), expectation_met=sum(row["expectation_met"] for row in rows),
                               expectation_not_met=sum(not row["expectation_met"] for row in rows)), probes=rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"]))


if __name__ == "__main__":
    main()
