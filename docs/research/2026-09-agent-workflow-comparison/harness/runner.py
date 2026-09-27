#!/usr/bin/env python3
"""Run (scenario, condition) jobs with a bounded pool. Usage: runner.py N s3:vanilla s3:dryforge ..."""
import subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOG = ROOT / "logs"
LOG.mkdir(exist_ok=True)


def job(spec):
    scen, cond = spec.split(":")
    t0 = time.time()
    with open(LOG / f"{scen}-{cond}.log", "w") as f:
        rc = subprocess.run([sys.executable, str(ROOT / "driver.py"), scen, cond], stdout=f, stderr=subprocess.STDOUT).returncode
    print(f"FINISHED {spec} rc={rc} {round(time.time()-t0)}s", flush=True)


if __name__ == "__main__":
    n = int(sys.argv[1])
    with ThreadPoolExecutor(n) as ex:
        list(ex.map(job, sys.argv[2:]))
    print("ALL DONE", flush=True)
