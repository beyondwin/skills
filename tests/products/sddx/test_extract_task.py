from __future__ import annotations

import builtins
import importlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SCRIPTS = ROOT / "skills" / "sddx" / "scripts"

extract_task = None
main = None


class _ExtractTaskCase(unittest.TestCase):
    """Loads skills/sddx/scripts/extract_task.py onto sys.path for the test only.

    Mirrors the setUp/addCleanup + dynamic-reload pattern used by
    test_resolve_backend.py so the scripts directory never stays on
    sys.path beyond this test's lifetime.
    """

    def setUp(self) -> None:
        sys.path.insert(0, str(SCRIPTS))
        self.addCleanup(lambda: sys.path.remove(str(SCRIPTS)) if str(SCRIPTS) in sys.path else None)
        sys.modules.pop("extract_task", None)
        module = importlib.import_module("extract_task")
        global extract_task, main
        extract_task = module.extract_task
        main = module.main


class ExtractTaskBoundaryTests(_ExtractTaskCase):
    def test_fenced_heading_does_not_end_task(self) -> None:
        section = (
            "## Task P1: 저장\r\n"
            "요구사항\r\n```md\r\n## Task P2: 가짜\r\n```\r\n"
            "### 검증\r\n검증 내용\r\n"
        ).encode("utf-8")
        plan = b"# Plan\r\n" + section + "## Task P2: 다음\r\n다음 내용\r\n".encode("utf-8")
        self.assertEqual(extract_task(plan, "Task P1: 저장"), section)

    def test_tilde_fence_hides_heading_lookalike(self) -> None:
        section = (
            "## Task 1: 준비\n"
            "설명\n~~~\n## Task 2: 가짜\n~~~\n"
            "본문 계속\n"
        ).encode("utf-8")
        plan = section + "## Task 2: 다음\n다음\n".encode("utf-8")
        self.assertEqual(extract_task(plan, "Task 1: 준비"), section)

    def test_mismatched_fence_character_does_not_close(self) -> None:
        # A tilde fence line cannot close a backtick fence (and vice versa);
        # the original fence must stay open through to its own matching close.
        plan = (
            "## Task 1: 시작\n"
            "```\n## Task 2: 가짜\n~~~\n여전히 안 닫힘\n```\n"
            "본문 종료\n"
            "## Task 2: 다음\n다음 본문\n"
        ).encode("utf-8")
        expected = (
            "## Task 1: 시작\n```\n## Task 2: 가짜\n~~~\n여전히 안 닫힘\n```\n본문 종료\n"
        ).encode("utf-8")
        self.assertEqual(extract_task(plan, "Task 1: 시작"), expected)

    def test_level_six_heading_extracts_correctly(self) -> None:
        plan = "###### Task 1: 최소 헤딩\n본문\n".encode("utf-8")
        self.assertEqual(extract_task(plan, "Task 1: 최소 헤딩"), plan)

    def test_seven_hashes_is_not_a_heading(self) -> None:
        plan = (
            "## Task 1: 저장\n"
            "본문\n####### 일곱 개는 제목 아님\n계속\n"
        ).encode("utf-8")
        expected = plan
        self.assertEqual(extract_task(plan, "Task 1: 저장"), expected)

    def test_unclosed_fence_stays_open_to_end_of_file(self) -> None:
        # The fence never closes, so a heading-lookalike after it must stay hidden
        # and the section must run all the way to end of file.
        plan = (
            "## Task 1: 시작\n"
            "본문\n```\n## Task 2: 가짜\n더 있음\n"
        ).encode("utf-8")
        self.assertEqual(extract_task(plan, "Task 1: 시작"), plan)

    def test_fence_closer_shorter_than_opener_does_not_close(self) -> None:
        plan = (
            "## Task 1: 시작\n"
            "````\n## Task 2: 가짜\n```\n실제 닫힘\n````\n"
            "본문 종료\n"
        ).encode("utf-8")
        self.assertEqual(extract_task(plan, "Task 1: 시작"), plan)

    def test_six_heading_id_forms_each_extract_by_exact_match(self) -> None:
        cases = ["Task 1", "Task P1", "Task U1", "Task F1", "S01", "P1-T1"]
        for heading in cases:
            with self.subTest(heading=heading):
                section = f"## {heading}: 설명\n본문 내용\n".encode("utf-8")
                plan = b"# Plan\n" + section + "## 다음: 다른 절\n다른 본문\n".encode("utf-8")
                self.assertEqual(extract_task(plan, f"{heading}: 설명"), section)

    def test_p1_does_not_match_p10(self) -> None:
        plan = (
            "## Task P1: 저장\n본문1\n"
            "## Task P10: 다른 저장\n본문10\n"
        ).encode("utf-8")
        self.assertEqual(
            extract_task(plan, "Task P10: 다른 저장"),
            "## Task P10: 다른 저장\n본문10\n".encode("utf-8"),
        )
        self.assertEqual(
            extract_task(plan, "Task P1: 저장"),
            "## Task P1: 저장\n본문1\n".encode("utf-8"),
        )

    def test_closing_hash_run_is_stripped_only_for_comparison(self) -> None:
        section = "## Task 1: 저장 ##\n본문\n".encode("utf-8")
        plan = b"# Plan\n" + section + "## Task 2: 다음 ##\n다음 본문\n".encode("utf-8")
        # Requested heading has no closing hashes; match is by stripped title.
        result = extract_task(plan, "Task 1: 저장")
        self.assertEqual(result, section)
        # Bytes written are byte-for-byte identical to the source, hashes included.
        self.assertIn("## Task 1: 저장 ##\n".encode("utf-8"), result)

    def test_section_ends_at_heading_of_equal_or_lower_level(self) -> None:
        plan = (
            "## Task 1: 저장\n"
            "### 세부 1\n세부 본문\n"
            "## Task 2: 다음\n다음 본문\n"
        ).encode("utf-8")
        expected = "## Task 1: 저장\n### 세부 1\n세부 본문\n".encode("utf-8")
        self.assertEqual(extract_task(plan, "Task 1: 저장"), expected)

    def test_deeper_subheading_stays_inside_section(self) -> None:
        plan = (
            "## Task 1: 저장\n"
            "본문\n#### 아주 깊은 절\n더 깊은 본문\n"
            "## Task 2: 다음\n다음 본문\n"
        ).encode("utf-8")
        expected = (
            "## Task 1: 저장\n본문\n#### 아주 깊은 절\n더 깊은 본문\n"
        ).encode("utf-8")
        self.assertEqual(extract_task(plan, "Task 1: 저장"), expected)

    def test_higher_level_heading_ends_section_even_when_shallower(self) -> None:
        plan = (
            "## Task 1: 저장\n"
            "본문\n"
            "# 상위 제목\n상위 본문\n"
        ).encode("utf-8")
        expected = "## Task 1: 저장\n본문\n".encode("utf-8")
        self.assertEqual(extract_task(plan, "Task 1: 저장"), expected)

    def test_last_section_runs_to_end_of_file(self) -> None:
        plan = (
            "## Task 1: 저장\n본문1\n"
            "## Task 2: 마지막\n마지막 본문\n계속\n"
        ).encode("utf-8")
        expected = "## Task 2: 마지막\n마지막 본문\n계속\n".encode("utf-8")
        self.assertEqual(extract_task(plan, "Task 2: 마지막"), expected)

    def test_duplicate_heading_raises_value_error(self) -> None:
        plan = (
            "## Task 1: 저장\n본문1\n"
            "## Task 1: 저장\n본문2\n"
        ).encode("utf-8")
        with self.assertRaises(ValueError):
            extract_task(plan, "Task 1: 저장")

    def test_no_matching_heading_raises_value_error(self) -> None:
        plan = "## Task 1: 저장\n본문\n".encode("utf-8")
        with self.assertRaises(ValueError):
            extract_task(plan, "Task 9: 없음")

    def test_empty_body_raises_value_error(self) -> None:
        plan = "## Task 1: 저장\n   \n\t\n## Task 2: 다음\n본문\n".encode("utf-8")
        with self.assertRaises(ValueError):
            extract_task(plan, "Task 1: 저장")

    def test_section_with_only_a_subheading_body_is_not_empty(self) -> None:
        plan = "## Task 1: 저장\n### 하위 제목\n## Task 2: 다음\n본문\n".encode("utf-8")
        expected = "## Task 1: 저장\n### 하위 제목\n".encode("utf-8")
        self.assertEqual(extract_task(plan, "Task 1: 저장"), expected)

    def test_unicode_and_crlf_are_preserved_byte_for_byte(self) -> None:
        section = "## Task 1: 유니코드 테스트 ☃\r\n본문 ❤\r\n".encode("utf-8")
        plan = b"# Plan\r\n" + section + "## Task 2: 다음\r\n다음\r\n".encode("utf-8")
        result = extract_task(plan, "Task 1: 유니코드 테스트 ☃")
        self.assertEqual(result, section)
        self.assertIsInstance(result, bytes)

    def test_setext_heading_is_not_recognized(self) -> None:
        plan = (
            "제목\n===\n본문\n"
            "## Task 1: 실제\n실제 본문\n"
        ).encode("utf-8")
        with self.assertRaises(ValueError):
            extract_task(plan, "제목")
        self.assertEqual(extract_task(plan, "Task 1: 실제"), "## Task 1: 실제\n실제 본문\n".encode("utf-8"))

    def test_four_space_indent_hash_line_is_not_a_heading(self) -> None:
        plan = (
            "## Task 1: 저장\n"
            "본문\n    # 코드처럼 보이는 줄\n계속\n"
            "## Task 2: 다음\n다음 본문\n"
        ).encode("utf-8")
        expected = (
            "## Task 1: 저장\n본문\n    # 코드처럼 보이는 줄\n계속\n"
        ).encode("utf-8")
        self.assertEqual(extract_task(plan, "Task 1: 저장"), expected)

    def test_up_to_three_leading_spaces_still_a_heading(self) -> None:
        plan = "  ## Task 1: 저장\n본문\n".encode("utf-8")
        self.assertEqual(extract_task(plan, "Task 1: 저장"), plan)


class ExtractTaskCliTests(_ExtractTaskCase):
    def setUp(self) -> None:
        super().setUp()
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.base = Path(self.tmpdir.name)

    def _write_plan(self, content: bytes) -> Path:
        plan_path = self.base / "plan.md"
        plan_path.write_bytes(content)
        return plan_path

    def test_cli_success_writes_exact_bytes_and_exits_zero(self) -> None:
        section = "## Task 1: 저장\r\n본문\r\n".encode("utf-8")
        plan = b"# Plan\r\n" + section + "## Task 2: 다음\r\n다음\r\n".encode("utf-8")
        plan_path = self._write_plan(plan)
        output_path = self.base / "section.md"
        code = main(
            [
                str(plan_path),
                "--heading",
                "Task 1: 저장",
                "--output",
                str(output_path),
            ]
        )
        self.assertEqual(code, 0)
        self.assertEqual(output_path.read_bytes(), section)

    def test_cli_missing_plan_file_exits_2_and_writes_no_output(self) -> None:
        output_path = self.base / "section.md"
        with mock.patch("sys.stderr"):
            code = main(
                [
                    str(self.base / "does-not-exist.md"),
                    "--heading",
                    "Task 1",
                    "--output",
                    str(output_path),
                ]
            )
        self.assertEqual(code, 2)
        self.assertFalse(output_path.exists())

    def test_cli_bad_argv_exits_2(self) -> None:
        with mock.patch("sys.stderr"):
            code = main(["--heading", "Task 1"])
        self.assertEqual(code, 2)

    def test_cli_invalid_utf8_plan_exits_2_not_3(self) -> None:
        plan_path = self._write_plan(b"## Task 1: x\n\xff\xfe\n")
        output_path = self.base / "section.md"
        with mock.patch("sys.stderr"):
            code = main(
                [
                    str(plan_path),
                    "--heading",
                    "Task 1: x",
                    "--output",
                    str(output_path),
                ]
            )
        self.assertEqual(code, 2)
        self.assertFalse(output_path.exists())

    def test_cli_section_error_exits_3_and_writes_no_output(self) -> None:
        plan_path = self._write_plan("## Task 1: 저장\n본문\n".encode("utf-8"))
        output_path = self.base / "section.md"
        with mock.patch("sys.stderr"):
            code = main(
                [
                    str(plan_path),
                    "--heading",
                    "Task 9: 없음",
                    "--output",
                    str(output_path),
                ]
            )
        self.assertEqual(code, 3)
        self.assertFalse(output_path.exists())

    def test_cli_output_already_existing_exits_2_and_leaves_it_untouched(self) -> None:
        plan_path = self._write_plan("## Task 1: 저장\n본문\n".encode("utf-8"))
        output_path = self.base / "section.md"
        output_path.write_bytes(b"pre-existing content")
        with mock.patch("sys.stderr"):
            code = main(
                [
                    str(plan_path),
                    "--heading",
                    "Task 1: 저장",
                    "--output",
                    str(output_path),
                ]
            )
        self.assertEqual(code, 2)
        self.assertEqual(output_path.read_bytes(), b"pre-existing content")

    def test_cli_write_failure_removes_only_the_partial_file_it_created(self) -> None:
        plan_path = self._write_plan("## Task 1: 저장\n본문\n".encode("utf-8"))
        output_path = self.base / "section.md"
        real_open = builtins.open

        def flaky_open(path, mode="r", *args, **kwargs):
            if mode == "xb" and str(path) == str(output_path):
                handle = real_open(path, mode, *args, **kwargs)
                handle.close()

                class Boom:
                    def __enter__(self_inner):
                        return self_inner

                    def __exit__(self_inner, *exc_info):
                        return False

                    def write(self_inner, data):
                        raise OSError("simulated disk failure")

                return Boom()
            return real_open(path, mode, *args, **kwargs)

        with mock.patch("builtins.open", flaky_open), mock.patch("sys.stderr"):
            code = main(
                [
                    str(plan_path),
                    "--heading",
                    "Task 1: 저장",
                    "--output",
                    str(output_path),
                ]
            )
        self.assertEqual(code, 2)
        self.assertFalse(output_path.exists())


if __name__ == "__main__":
    unittest.main()
