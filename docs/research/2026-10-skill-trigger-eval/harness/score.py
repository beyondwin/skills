#!/usr/bin/env python3
"""Summarize trigger results: hit rate on positives, false-trigger rate on near-misses, per host,
skill and split, with Wilson 95% intervals, rep-to-rep agreement, and which skill fired instead.

usage: score.py <variant> [--json OUT]
"""
import collections, json, math, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    r = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (round((c - r) / d, 3), round((c + r) / d, 3))


def load(variant):
    out = []
    for f in sorted((ROOT / "runs" / variant).glob("*/*/result.json")):
        out.append(json.loads(f.read_text()))
    return out


def main():
    variant = sys.argv[1]
    rs = load(variant)
    cells = collections.defaultdict(list)
    for r in rs:
        cells[(r["host"], r["skill"], r["kind"], r["split"])].append(r)
    summary = []
    for (host, skill, kind, split), xs in sorted(cells.items()):
        good = [x for x in xs if x["target_fired"] == (kind == "pos")]
        by_id = collections.defaultdict(list)
        for x in xs:
            by_id[x["id"]].append(x["target_fired"])
        agree = sum(len(set(v)) == 1 for v in by_id.values() if len(v) > 1)
        pairs = sum(len(v) > 1 for v in by_id.values())
        wrong = collections.Counter()
        for x in xs:
            if x["target_fired"] != (kind == "pos"):
                wrong[x["id"]] += 1
        other = collections.Counter(s for x in xs for s in x["fired"] if s not in (skill, "using-superpowers"))
        summary.append({"host": host, "skill": skill, "kind": kind, "split": split, "n": len(xs), "correct": len(good),
                        "rate": round(len(good) / len(xs), 3), "ci95": wilson(len(good), len(xs)),
                        "rep_agreement": f"{agree}/{pairs}", "misses": dict(wrong), "other_skills": dict(other.most_common(5)),
                        "timeouts": sum(x["ended"] == "timeout" for x in xs)})
    for s in summary:
        print(f"{s['host']:6} {s['skill']:22} {s['kind']} {s['split']:5} {s['correct']:2}/{s['n']:<2} ci{s['ci95']} "
              f"agree {s['rep_agreement']} miss {s['misses'] or '-'} other {s['other_skills'] or '-'}")
    if "--json" in sys.argv:
        Path(sys.argv[sys.argv.index("--json") + 1]).write_text(json.dumps(summary, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
