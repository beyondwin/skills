#!/usr/bin/env python3
"""Build the synthetic project every trigger call starts from: a small Python service with a
design spec and plan, brand notes, raster assets and a CSV. Nothing here comes from a real session."""
import struct, subprocess, sys, zlib
from pathlib import Path


def png(path, w, h, rgb):
    raw = b"".join(b"\x00" + bytes(rgb) * w for _ in range(h))
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


FILES = {
    "README.md": "# relay\n\nA small job relay: HTTP requests pass a token-bucket rate limiter, then go to a worker queue\nwith retries. `python3 -m unittest` runs the tests.\n\nAssets for the landing page live in `assets/`; brand notes are in `docs/brand.md`.\n",
    "src/__init__.py": "",
    "src/ratelimit.py": '''import time


class TokenBucket:
    """Allow `rate` requests per second with bursts up to `capacity`."""

    def __init__(self, rate, capacity, clock=time.monotonic):
        self.rate, self.capacity, self.clock = rate, capacity, clock
        self.tokens, self.updated = capacity, clock()

    def allow(self):
        now = self.clock()
        self.tokens = min(self.capacity, self.tokens + (now - self.updated) * self.rate)
        self.updated = now
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False
''',
    "src/queue.py": '''import collections


class JobQueue:
    """FIFO jobs; a failed job is retried up to `max_retries` times, then parked."""

    def __init__(self, handler, max_retries=3):
        self.handler, self.max_retries = handler, max_retries
        self.pending, self.parked = collections.deque(), []

    def submit(self, job):
        self.pending.append((job, 0))

    def run_once(self):
        if not self.pending:
            return False
        job, tries = self.pending.popleft()
        try:
            self.handler(job)
        except Exception:
            if tries + 1 < self.max_retries:
                self.pending.append((job, tries + 1))
            else:
                self.parked.append(job)
        return True
''',
    "src/server.py": '''from .ratelimit import TokenBucket
from .queue import JobQueue

bucket = TokenBucket(rate=5, capacity=10)


def handle_request(queue: JobQueue, job):
    if not bucket.allow():
        return 429
    queue.submit(job)
    return 202
''',
    "tests/__init__.py": "",
    "tests/test_ratelimit.py": '''import unittest
from src.ratelimit import TokenBucket


class T(unittest.TestCase):
    def test_burst_then_block(self):
        t = [0.0]
        b = TokenBucket(1, 2, clock=lambda: t[0])
        self.assertTrue(b.allow()); self.assertTrue(b.allow()); self.assertFalse(b.allow())
        t[0] = 1.0
        self.assertTrue(b.allow())
''',
    "docs/specs/2026-10-01-retry-backoff-design.md": '''# Retry backoff for JobQueue

Status: approved 2026-10-01

## Problem
Failed jobs are retried immediately, so a flapping downstream gets hammered.

## Requirements
- A failed job waits `base_delay * 2**tries` seconds before its next attempt, capped at `max_delay`.
- `JobQueue.run_once()` must not block; a job that is not due yet stays queued.
- Parked jobs keep the last error message.
- Existing callers of `JobQueue(handler, max_retries)` keep working.
''',
    "docs/plans/2026-10-01-retry-backoff.md": '''# Retry backoff implementation plan

Spec: docs/specs/2026-10-01-retry-backoff-design.md

## Task 1: due times
- Files: src/queue.py, tests/test_queue.py
- Store `(job, tries, due_at)`; `run_once` skips jobs whose `due_at` is in the future.
- Verify: `npm test`

## Task 2: parked errors
- Files: src/queue.py
- Keep `(job, error)` in `parked`.
- Verify: `python3 -m unittest`
''',
    "docs/brand.md": "# Brand\n\n- Primary #1F6FEB, ink #0B1221, paper #F6F8FA\n- Tone: calm, technical, no mascots\n- Landing hero: 1600x900, text-safe area on the left 40%\n",
    "data/sales.csv": "month,revenue\n2026-07,120\n2026-08,135\n2026-09,160\n",
}


def build(root: Path):
    for rel, text in FILES.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    a = root / "assets"
    a.mkdir(exist_ok=True)
    png(a / "hero.png", 160, 90, (31, 111, 235))
    png(a / "hero-v2.png", 160, 90, (11, 18, 33))
    png(a / "logo.png", 64, 64, (246, 248, 250))
    png(a / "banner.png", 300, 60, (31, 111, 235))
    png(a / "screen1.png", 129, 280, (240, 240, 240))
    for c in ["git init -q -b main", "git config user.name t", "git config user.email t@example.invalid",
              "git config commit.gpgsign false", "git add -A", "git commit -q -m initial"]:
        subprocess.run(c, cwd=root, shell=True, check=True)


if __name__ == "__main__":
    build(Path(sys.argv[1]))
