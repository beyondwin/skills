#!/usr/bin/env python3
"""Score one grok-video held-out clip. Python 3.9. See protocol.md."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys

MASKS = {
    "apple": lambda r, g, b: r > 150 and g < 110 and b < 110 and r > g + 50 and r > b + 50,
    "pitcher": lambda r, g, b: b > 130 and b > r + 30 and b > g + 15 and r < 160 and g < 190,
    "balloon": lambda r, g, b: (
        r > 70 and b > 70 and g < 140 and r > g + 20 and b > g + 20 and abs(r - b) < 90
    ),
}


def _run(command: list[str]) -> bytes:
    return subprocess.check_output(command, stderr=subprocess.DEVNULL)


def _size(path: str) -> tuple[int, int]:
    text = subprocess.check_output(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height", "-of", "csv=p=0:s=x", path,
        ],
        text=True,
    ).strip()
    width, height = text.split("x")
    return int(width), int(height)


def _frame(path: str, width: int, height: int, ss: str | None, sseof: str | None) -> bytes:
    command = ["ffmpeg", "-v", "error", "-y"]
    if sseof:
        command.extend(["-sseof", sseof])
    if ss is not None:
        command.extend(["-ss", ss])
    command.extend([
        "-i", path, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1",
    ])
    data = _run(command)
    expected = width * height * 3
    if len(data) < expected:
        raise RuntimeError("short frame from {0}: {1}".format(path, len(data)))
    return data[:expected]


def _still(path: str, width: int, height: int) -> bytes:
    data = _run([
        "ffmpeg", "-v", "error", "-y", "-i", path,
        "-vf", "scale={0}:{1}:flags=bilinear".format(width, height),
        "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1",
    ])
    expected = width * height * 3
    if len(data) < expected:
        raise RuntimeError("short still from {0}".format(path))
    return data[:expected]


def _mean(frame: bytes) -> float:
    return sum(frame) / float(len(frame))


def _component(frame: bytes, width: int, height: int, kind: str) -> dict:
    pred = MASKS[kind]
    total = width * height
    seen = bytearray(total)
    best: list[int] = []
    for start in range(total):
        if seen[start]:
            continue
        offset = start * 3
        if not pred(frame[offset], frame[offset + 1], frame[offset + 2]):
            seen[start] = 1
            continue
        stack = [start]
        seen[start] = 1
        cells: list[int] = []
        while stack:
            current = stack.pop()
            cells.append(current)
            x = current % width
            y = current // width
            if x > 0:
                nxt = current - 1
                if not seen[nxt]:
                    seen[nxt] = 1
                    off = nxt * 3
                    if pred(frame[off], frame[off + 1], frame[off + 2]):
                        stack.append(nxt)
            if x + 1 < width:
                nxt = current + 1
                if not seen[nxt]:
                    seen[nxt] = 1
                    off = nxt * 3
                    if pred(frame[off], frame[off + 1], frame[off + 2]):
                        stack.append(nxt)
            if y > 0:
                nxt = current - width
                if not seen[nxt]:
                    seen[nxt] = 1
                    off = nxt * 3
                    if pred(frame[off], frame[off + 1], frame[off + 2]):
                        stack.append(nxt)
            if y + 1 < height:
                nxt = current + width
                if not seen[nxt]:
                    seen[nxt] = 1
                    off = nxt * 3
                    if pred(frame[off], frame[off + 1], frame[off + 2]):
                        stack.append(nxt)
        if len(cells) > len(best):
            best = cells
    area = len(best)
    fraction = area / float(total)
    if area == 0 or fraction < 0.005 or fraction > 0.40:
        return {"ok": False, "area_fraction": round(fraction, 4), "pixels": area}
    sx = sy = 0
    min_x = width
    max_x = 0
    for cell in best:
        x = cell % width
        y = cell // width
        sx += x
        sy += y
        if x < min_x:
            min_x = x
        if x > max_x:
            max_x = x
    return {
        "ok": True,
        "area_fraction": round(fraction, 4),
        "pixels": area,
        "cx": round((sx / float(area)) / width, 4),
        "cy": round((sy / float(area)) / height, 4),
        "width_fraction": round((max_x - min_x + 1) / float(width), 4),
        "cells": best,
    }


def _mae(left: bytes, right: bytes, skip: set[int] | None = None) -> float | None:
    count = 0
    total = 0
    pixels = len(left) // 3
    for index in range(pixels):
        if skip and index in skip:
            continue
        a = index * 3
        total += abs(left[a] - right[a]) + abs(left[a + 1] - right[a + 1]) + abs(left[a + 2] - right[a + 2])
        count += 1
    if count == 0:
        return None
    return round(total / float(count * 3), 3)


def _sample(path: str, width: int, height: int) -> tuple[bytes, str]:
    frame = _frame(path, width, height, "0", None)
    note = "0"
    if _mean(frame) < 8:
        frame = _frame(path, width, height, "0.1", None)
        note = "0.1"
    return frame, note


def _duration(path: str) -> float:
    text = subprocess.check_output(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "csv=p=0", path,
        ],
        text=True,
    ).strip()
    return float(text)


def _last(path: str, width: int, height: int) -> tuple[bytes, str]:
    # -sseof is empty on this ffmpeg, and a seek 0.04s before the container
    # duration can also fall past the last packet. Step back until a frame
    # arrives. See the protocol erratum.
    duration = _duration(path)
    frame = b""
    note = "missing"
    for back in (0.05, 0.10, 0.15, 0.20):
        seconds = max(0.0, duration - back)
        stamp = "{:.3f}".format(int(seconds * 1000) / 1000.0)
        try:
            frame = _frame(path, width, height, stamp, None)
        except RuntimeError:
            continue
        note = "duration-{0}".format(stamp)
        if _mean(frame) >= 8:
            return frame, note
    if not frame:
        raise RuntimeError("no last frame from {0}".format(path))
    return frame, note


def score(video: str, kind: str, end: str | None) -> dict:
    width, height = _size(video)
    first, first_at = _sample(video, width, height)
    middle = _frame(video, width, height, "3", None)
    last, last_at = _last(video, width, height)
    first_mask = _component(first, width, height, kind)
    last_mask = _component(last, width, height, kind)
    result = {
        "video": video,
        "kind": kind,
        "width": width,
        "height": height,
        "first_at": first_at,
        "middle_mean": round(_mean(middle), 3),
        "last_at": last_at,
        "first": {key: value for key, value in first_mask.items() if key != "cells"},
        "last": {key: value for key, value in last_mask.items() if key != "cells"},
    }
    if first_mask["ok"] and last_mask["ok"]:
        result["dx"] = round(last_mask["cx"] - first_mask["cx"], 4)
        result["dy"] = round(last_mask["cy"] - first_mask["cy"], 4)
        result["width_ratio"] = round(
            last_mask["width_fraction"] / first_mask["width_fraction"], 4
        ) if first_mask["width_fraction"] else None
        skip = set(first_mask["cells"]) | set(last_mask["cells"])
        result["background_mae"] = _mae(first, last, skip)
    if end and last_mask["ok"]:
        result["end_mae"] = _mae(last, _still(end, width, height))
    return result


def score_still(path: str, kind: str) -> dict:
    width, height = _size(path)
    frame = _still(path, width, height)
    mask = _component(frame, width, height, kind)
    return {
        "image": path,
        "kind": kind,
        "width": width,
        "height": height,
        "mask": {key: value for key, value in mask.items() if key != "cells"},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Score one held-out grok-video clip.")
    parser.add_argument("--video")
    parser.add_argument("--image")
    parser.add_argument("--kind", required=True, choices=sorted(MASKS))
    parser.add_argument("--end")
    args = parser.parse_args(argv)
    if bool(args.video) == bool(args.image):
        print("pass exactly one of --video or --image", file=sys.stderr)
        return 2
    if args.image:
        payload = score_still(args.image, args.kind)
    else:
        payload = score(args.video, args.kind, args.end)
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
