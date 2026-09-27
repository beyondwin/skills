#!/usr/bin/env python3
"""Re-run the hidden tests (including extended ones) on every finished run's final tree."""
import json, sys
from pathlib import Path
import bench

tag = sys.argv[1]
for d in sorted((bench.ROOT / "runs" / tag).iterdir()):
    mp = d / "meta.json"
    if not mp.exists():
        continue
    m = json.loads(mp.read_text())
    m["score"] = bench.score(d / "repo", d)
    mp.write_text(json.dumps(m, ensure_ascii=False, indent=1))
    s = m["score"]
    print(d.name, s["hidden_pass"], "x", s["x_pass"], [k for k, v in s["hidden"].items() if v != "ok"])
