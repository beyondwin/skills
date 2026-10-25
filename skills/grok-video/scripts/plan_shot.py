#!/usr/bin/env python3
"""Turn a shot brief into a Grok video plan, or the questions that block one.

The plan is the prompt and pin source for grok-video. Python 3.9.
"""
from __future__ import annotations

import argparse
import json
import re
import sys

ASPECTS = ("16:9", "9:16", "1:1", "4:3", "3:4", "3:2", "2:3")
VOICES = ("ara", "eve", "leo", "rex")
TRAVEL_WORDS = (
    "slide", "move", "walk", "run", "float", "fly", "drive", "travel",
    "cross", "goes", "going", "toward", "across", "into", "from",
    "left", "right",
    "이동", "움직", "걸어", "떠내", "흘러", "왼쪽", "오른쪽", "앞으로", "건너",
)
HOLD_WORDS = (
    "stay", "still", "push-in", "push in", "loop", "locked",
    "제자리", "그대로", "살짝", "고정", "밀어",
)
STYLE_ONLY = (
    "cinematic", "beautiful", "epic", "dramatic", "dreamlike", "masterpiece",
    "시네마틱", "예쁘", "멋있", "영화같",
)
VERTICAL_WORDS = ("9:16", "phone", "story", "vertical", "shorts", "쇼츠", "릴스", "세로")
SQUARE_WORDS = ("1:1", "square", "정사각")


def _text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _has_any(text: str, words: tuple[str, ...]) -> bool:
    lowered = text.lower()
    for word in words:
        if " " in word or any("\uac00" <= char <= "\ud7a3" for char in word):
            if word in lowered:
                return True
        elif re.search(r"\b" + re.escape(word) + r"\b", lowered):
            return True
    return False


def _duration(value: object, raw: str) -> tuple[int | None, str | None]:
    if value is None or value == "":
        match = re.search(r"(\d+)\s*(?:seconds|second|secs|sec|s\b|초)", raw, re.I)
        if not match:
            return 6, None
        number = int(match.group(1))
    else:
        try:
            number = int(value)
        except (TypeError, ValueError):
            return None, "Duration must be a whole number of seconds from 1 to 15."
    if number < 1 or number > 15:
        return None, "Duration must be a whole number of seconds from 1 to 15."
    return number, None


def _aspect(value: object, raw: str) -> str:
    text = _text(value)
    if text in ASPECTS:
        return text
    lowered = (text + " " + raw).lower()
    if _has_any(lowered, VERTICAL_WORDS):
        return "9:16"
    if _has_any(lowered, SQUARE_WORDS):
        return "1:1"
    return "16:9"


def _resolution(value: object, raw: str) -> str:
    text = (_text(value) + " " + raw).lower()
    if "480" in text or "draft" in text or "초안" in text:
        return "480p"
    return "720p"


def _mode(given: str, action: str, exact: str, has_start: bool) -> str:
    if given in ("travel", "hold", "speak"):
        return given
    blob = action + " " + exact
    travel = _has_any(blob, TRAVEL_WORDS)
    hold = _has_any(blob, HOLD_WORDS)
    if travel:
        return "travel"
    if hold or (has_start and not action and not exact):
        return "hold"
    return ""


def _style_only(action: str) -> bool:
    if not action:
        return False
    if _has_any(action, TRAVEL_WORDS) or _has_any(action, HOLD_WORDS):
        return False
    return _has_any(action, STYLE_ONLY)


def _cap(text: str) -> str:
    if not text:
        return text
    return text[0].upper() + text[1:]


def _subject_phrase(subject: str) -> str:
    text = subject.strip()
    if not text:
        return "the subject"
    if text.lower().startswith(("a ", "an ", "the ")):
        return text
    return "the " + text


def plan_shot(brief: dict) -> dict:
    subject = _text(brief.get("subject"))
    action = _text(brief.get("action"))
    exact = _text(brief.get("exact_prompt"))
    speech = _text(brief.get("speech"))
    voice = _text(brief.get("voice")).lower()
    named = bool(brief.get("named_person"))
    has_reference = bool(brief.get("has_reference"))
    has_start = bool(brief.get("has_start_image"))
    raw = " ".join((subject, action, exact, _text(brief.get("aspect")), speech))
    questions = []

    if named and not has_reference:
        questions.append(
            "A named person needs one real photo. Share that photo, or describe a fictional subject instead."
        )
    if not subject and not exact:
        questions.append("What is in the shot?")
    if _style_only(action) and not exact:
        questions.append("What one change should happen? A style word does not set the motion.")
        action = ""
    mode = _mode(_text(brief.get("mode")), action, exact, has_start)
    if not mode and not any("one change" in item for item in questions):
        questions.append("What one change should happen: where the subject travels, or that it stays?")
    if mode == "speak" or speech or _has_any(raw, ("say", "speak", "says", "대사", "말해", "말하")):
        if mode != "hold":
            mode = "speak" if mode == "" or _text(brief.get("mode")) == "speak" else mode
        if not speech:
            questions.append("What is the spoken line?")
        if voice and voice not in VOICES:
            questions.append("Voice must be ara, eve, leo, or rex.")
    duration, duration_error = _duration(brief.get("duration"), raw)
    if duration_error:
        questions.append(duration_error)

    if questions:
        return {"status": "ask", "questions": questions}

    aspect = _aspect(brief.get("aspect"), raw)
    resolution = _resolution(brief.get("resolution"), raw)
    phrase = _subject_phrase(subject)
    spoken = bool(speech) or mode == "speak"
    if spoken and _has_any(action + " " + exact, TRAVEL_WORDS):
        base = "travel"
    elif spoken or mode == "hold":
        base = "hold"
    else:
        base = "travel"
    if base == "hold":
        motion = action if action and not _has_any(action, ("stay", "제자리", "그대로")) else ""
        video = "Slow push-in. {0} stays where it is. {1}The background stays fixed.".format(
            _cap(phrase),
            (motion.rstrip(".") + ". ") if motion else "",
        )
        pins = "same_image"
        end_edit = ""
    else:
        toward_left = _has_any(action + " " + exact, ("left", "왼쪽")) and not _has_any(
            action + " " + exact, ("right", "오른쪽")
        )
        start_side = "right third" if toward_left else "left third"
        end_side = "left third" if toward_left else "right third"
        video = (
            "Locked camera. {0} slides from where it sits in the opening frame "
            "to where it sits in the closing frame. The background stays fixed."
        ).format(_cap(phrase))
        pins = "first_and_last"
        end_edit = (
            "Same scene, same light, same pose, same size. Move only {0} to the "
            "{1}. Do not turn it or change its size."
        ).format(phrase, end_side)
    if exact:
        video = exact
    if speech:
        chosen = voice if voice in VOICES else "eve"
        video = video.rstrip(".") + '. They say: "{0}".'.format(speech)
        voices = [chosen]
    else:
        voices = []
    start_prompt = ""
    if pins != "same_image" and not has_start and not named:
        start_prompt = (
            "{0}, large in frame, in the {1}. Uncluttered background, "
            "soft daylight, photoreal. No text."
        ).format(_cap(phrase), start_side if pins == "first_and_last" else "left third")
    return {
        "status": "plan",
        "mode": "hold" if base == "hold" and mode != "speak" else ("speak" if speech else base),
        "base": base,
        "duration": duration,
        "resolution": resolution,
        "aspect_ratio": aspect,
        "video_prompt": video,
        "start_prompt": start_prompt,
        "end_edit_prompt": end_edit,
        "pins": pins,
        "voices": voices,
        "use_start_image": has_start or named,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan one Grok video shot.")
    parser.add_argument("--request", required=True, help="UTF-8 JSON brief path")
    args = parser.parse_args(argv)
    with open(args.request, "r", encoding="utf-8") as handle:
        brief = json.load(handle)
    if not isinstance(brief, dict):
        print("brief must be a JSON object", file=sys.stderr)
        return 2
    json.dump(plan_shot(brief), sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
