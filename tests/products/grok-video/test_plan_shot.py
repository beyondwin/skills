from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "skills" / "grok-video" / "scripts" / "plan_shot.py"


def _load():
    spec = importlib.util.spec_from_file_location("plan_shot", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


plan_shot = _load().plan_shot


class PlanShotTests(unittest.TestCase):
    def test_empty_brief_asks_for_subject_and_change(self) -> None:
        result = plan_shot({})
        self.assertEqual(result["status"], "ask")
        self.assertIn("What is in the shot?", result["questions"])
        self.assertIn(
            "What one change should happen: where the subject travels, or that it stays?",
            result["questions"],
        )

    def test_style_only_action_does_not_become_a_shot(self) -> None:
        result = plan_shot({"subject": "a red boat", "action": "cinematic, beautiful movement"})
        self.assertEqual(result["status"], "ask")
        self.assertIn(
            "What one change should happen? A style word does not set the motion.",
            result["questions"],
        )

    def test_travel_plan_pins_both_ends_and_locks_the_camera(self) -> None:
        result = plan_shot({"subject": "a yellow mug", "action": "slides to the right"})
        self.assertEqual(result["status"], "plan")
        self.assertEqual(result["base"], "travel")
        self.assertEqual(result["pins"], "first_and_last")
        self.assertEqual(result["duration"], 6)
        self.assertEqual(result["resolution"], "720p")
        self.assertEqual(result["aspect_ratio"], "16:9")
        self.assertIn("Locked camera.", result["video_prompt"])
        self.assertIn("background stays fixed", result["video_prompt"])
        self.assertIn("same pose, same size", result["end_edit_prompt"])
        self.assertIn("left third", result["start_prompt"])
        self.assertIn("right third", result["end_edit_prompt"])
        self.assertIn("A yellow mug", result["start_prompt"])
        self.assertNotIn("cinematic", result["video_prompt"].lower())
        self.assertNotIn("The a ", result["video_prompt"])
        self.assertNotIn("A a ", result["start_prompt"])

    def test_start_image_hold_reuses_one_frame(self) -> None:
        result = plan_shot(
            {"subject": "a yellow mug", "has_start_image": True, "action": "stay"}
        )
        self.assertEqual(result["pins"], "same_image")
        self.assertEqual(result["end_edit_prompt"], "")
        self.assertEqual(result["start_prompt"], "")
        self.assertIn("stays where it is", result["video_prompt"])
        self.assertTrue(result["use_start_image"])

    def test_named_person_without_a_photo_asks_and_does_not_plan(self) -> None:
        result = plan_shot(
            {"subject": "Ada Lovelace", "named_person": True, "action": "walks to the right"}
        )
        self.assertEqual(result["status"], "ask")
        self.assertIn(
            "A named person needs one real photo. Share that photo, or describe a fictional subject instead.",
            result["questions"],
        )
        self.assertNotIn("video_prompt", result)

    def test_speech_without_a_line_asks(self) -> None:
        result = plan_shot({"subject": "a yellow mug", "action": "say something"})
        self.assertEqual(result["status"], "ask")
        self.assertIn("What is the spoken line?", result["questions"])

    def test_speech_on_a_still_holds_and_defaults_the_voice(self) -> None:
        result = plan_shot(
            {
                "subject": "a yellow mug",
                "has_start_image": True,
                "speech": "Hello.",
            }
        )
        self.assertEqual(result["status"], "plan")
        self.assertEqual(result["base"], "hold")
        self.assertEqual(result["voices"], ["eve"])
        self.assertIn('They say: "Hello."', result["video_prompt"])

    def test_named_voice_and_overrides_are_kept(self) -> None:
        result = plan_shot(
            {
                "subject": "a yellow mug",
                "action": "slides right",
                "speech": "Go.",
                "voice": "rex",
                "aspect": "9:16",
                "duration": 4,
                "resolution": "480p",
            }
        )
        self.assertEqual(result["voices"], ["rex"])
        self.assertEqual(result["aspect_ratio"], "9:16")
        self.assertEqual(result["duration"], 4)
        self.assertEqual(result["resolution"], "480p")
        self.assertEqual(result["base"], "travel")

    def test_exact_prompt_is_not_rewritten(self) -> None:
        result = plan_shot(
            {
                "subject": "a yellow mug",
                "action": "slides right",
                "exact_prompt": "The mug glides one inch.",
            }
        )
        self.assertEqual(result["video_prompt"], 'The mug glides one inch.')
        self.assertEqual(result["pins"], "first_and_last")

    def test_out_of_range_duration_asks(self) -> None:
        result = plan_shot({"subject": "a mug", "action": "slides right", "duration": 30})
        self.assertEqual(result["status"], "ask")
        self.assertIn(
            "Duration must be a whole number of seconds from 1 to 15.",
            result["questions"],
        )

    def test_korean_travel_and_vertical_words(self) -> None:
        result = plan_shot({"subject": "노란 머그", "action": "오른쪽으로 이동", "aspect": "쇼츠"})
        self.assertEqual(result["base"], "travel")
        self.assertEqual(result["aspect_ratio"], "9:16")


if __name__ == "__main__":
    unittest.main()
