#!/usr/bin/env python3
"""Reproduce bounded, provider-free counterexamples against pinned upstreams.

Pass a directory containing the three repositories listed in README.md.
Dependencies must already be installed in the temporary anti-slop checkout.
This script never installs skills or invokes a model.
"""

import argparse
import json
import pathlib
import subprocess
import tempfile


REVISIONS = {
    "no-ai-slop": "000650b156983f5159695b441477f4e63b25dc85",
    "im-not-ai": "2f3d943d08056b612a92e12bfb72ea94dd2acd18",
    "anti-slop": "c44ef22ca116d0ba62a3ff663a0bd13a3f3fa40b",
}
GATE_CASES = [
    (
        "unchanged-control",
        "참가자는 40명이다. 장소는 강당이다. 행사는 오후에 열린다.",
        "참가자는 40명이다. 장소는 강당이다. 행사는 오후에 열린다.",
    ),
    (
        "number-loss",
        "참가자는 40명이다. 장소는 강당이다. 행사는 오후에 열린다.",
        "참가자가 모였다. 장소는 강당이다. 행사는 오후에 열린다.",
    ),
    (
        "negation-reversal",
        "캐시는 원본이 아니다. 캐시는 임시 저장소다. 서버는 캐시를 주기적으로 갱신한다.",
        "캐시는 원본이다. 캐시는 임시 저장소다. 서버는 캐시를 주기적으로 갱신한다.",
    ),
]
LINT_PROBE = r'''
import { RuleTester } from "oxlint/plugins-dev";
import { noArrayFilterMapRule } from "./src/rules/no-array-filter-map.ts";
import { noUnknownParametersRule } from "./src/rules/no-unknown-parameters.ts";
const t = new RuleTester({languageOptions:{parserOptions:{lang:"ts"}}});
t.run("array-boundary", noArrayFilterMapRule, {
  valid: [
    "function f(values) { return values.filter(Boolean).map(String); }",
    "type Values = number[]; function f(values: Values) { return values.filter(Boolean).map(String); }",
  ],
  invalid: [{
    code: "const values: number[] = [1,2]; values.filter(Boolean).map(String);",
    errors: [{messageId:"arrayFilterMap"}],
  }],
});
t.run("input-boundary", noUnknownParametersRule, {
  valid: ["function isNumber(value: unknown): value is number { return typeof value === 'number'; }"],
  invalid: [{
    code: "function parseNumber(value: unknown): number { if (typeof value === 'number') return value; throw new Error('number required'); }",
    errors: [{messageId:"unknownParameter"}],
  }],
});
const eagerLog = []; const lazyLog = [];
[1,2].filter(x => {eagerLog.push('f'+x); return true;})
  .map(x => {eagerLog.push('m'+x); return x;});
[1,2].values().filter(x => {lazyLog.push('f'+x); return true;})
  .map(x => {lazyLog.push('m'+x); return x;}).toArray();
const sparse = [,1];
console.log(JSON.stringify({
  lint_cases: 5, eagerLog, lazyLog,
  eagerSparse: sparse.filter(() => true).map(x => String(x)),
  lazySparse: sparse.values().filter(() => true).map(x => String(x)).toArray(),
}));
'''


def run(argv, cwd=None):
    return subprocess.run(
        [str(arg) for arg in argv], cwd=cwd, capture_output=True,
        text=True, timeout=60,
    )


def require_success(result):
    if result.returncode:
        raise RuntimeError(result.stderr or result.stdout)
    return result.stdout.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkouts", type=pathlib.Path)
    parser.add_argument("--python", default="/usr/bin/python3")
    args = parser.parse_args()
    root = args.checkouts.resolve()
    for name, expected in REVISIONS.items():
        actual = require_success(run(["git", "rev-parse", "HEAD"], root / name))
        if actual != expected:
            raise RuntimeError("revision mismatch: " + name)
        require_success(run(["git", "diff", "--exit-code", "HEAD"], root / name))

    report = {
        "revisions": REVISIONS,
        "python": require_success(run([args.python, "--version"])),
        "node": require_success(run(["node", "--version"])),
        "model_calls": 0,
        "humanize_gate": [],
    }
    with tempfile.TemporaryDirectory(prefix="slop-gate-") as directory:
        before_path = pathlib.Path(directory) / "before.txt"
        after_path = pathlib.Path(directory) / "after.txt"
        for name, before, after in GATE_CASES:
            before_path.write_text(before, encoding="utf-8")
            after_path.write_text(after, encoding="utf-8")
            result = run([
                args.python, root / "im-not-ai/scripts/verify_gates.py",
                "--before", before_path, "--after", after_path,
                "--genre", "report", "--json",
            ])
            require_success(result)
            payload = json.loads(result.stdout[result.stdout.index("{\n"):])
            report["humanize_gate"].append({
                "case": name, "exit_code": result.returncode,
                "change_rate": payload["change_rate"]["rate"],
                "numbers_dropped": payload["numbers_dropped"],
                "golden_findings": len(payload["golden"]),
                "modality_lost_pairs": len(payload["modality"]["lost_pairs"]),
            })

    anti = root / "anti-slop"
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", prefix="audit-", suffix=".ts",
        dir=anti, delete=False,
    ) as handle:
        handle.write(LINT_PROBE)
        script = pathlib.Path(handle.name)
    try:
        output = require_success(run([anti / "node_modules/.bin/tsx", script], anti))
        report["anti_slop"] = json.loads(output)
    finally:
        script.unlink()
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
