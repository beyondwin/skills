from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "skills" / "kws-book-writer" / "scripts" / "book_check.py"
SYSTEM_PYTHON = Path("/usr/bin/python3")

CHAPTER_1 = """# 1장. 웹훅이 두 번 오는 이유

결제가 끝났는데 알림이 두 번 왔습니다. 이 장은 그 이유를 따라갑니다.

## 재시도

결제 서버는 응답이 없으면 웹훅을 3회까지 다시 보냅니다. <!-- src: RA01 -->

그래서 받는 쪽은 같은 이벤트를 여러 번 받을 수 있습니다.
"""

CHAPTER_2 = """# 2장. 한 번만 처리하기

1장에서 본 재시도 때문에 받는 쪽은 이벤트 ID를 기억해야 합니다.

## 이벤트 ID

이벤트마다 ID가 있고, 처리한 ID는 저장해 둡니다. <!-- src: RA02 -->

이제 알림이 두 번 와도 한 번만 처리합니다.
"""

PLAN = """# 계획

| 표기 | 피할 표기 | 첫 등장 설명 |
| --- | --- | --- |
| 웹훅 | 웹 훅, webhook | 웹훅(webhook) |
"""


def run(*args: str, python: str = sys.executable) -> subprocess.CompletedProcess:
    return subprocess.run(
        [python, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


class Workspace:
    def __init__(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "book"
        (self.path / "chapters").mkdir(parents=True)
        self.write("chapters/01.md", CHAPTER_1)
        self.write("chapters/02.md", CHAPTER_2)
        self.write("plan.md", PLAN)
        self.meta = {
            "title": "웹훅 안내서",
            "author": "저자",
            "chapters": ["chapters/01.md", "chapters/02.md"],
        }
        self.save_meta()

    def write(self, relative: str, text: str) -> None:
        target = self.path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    def save_meta(self) -> None:
        self.write("book.json", json.dumps(self.meta, ensure_ascii=False))

    def report(self) -> str:
        return (self.path / "checks" / "check-report.md").read_text(encoding="utf-8")

    def close(self) -> None:
        self._tmp.cleanup()


class BookCheckTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ws = Workspace()
        self.addCleanup(self.ws.close)

    def assemble_and_check(self, *extra: str) -> subprocess.CompletedProcess:
        assembled = run("assemble", str(self.ws.path))
        self.assertEqual(assembled.returncode, 0, assembled.stderr)
        return run("check", str(self.ws.path), *extra)

    def test_clean_workspace_passes_draft_check(self) -> None:
        result = self.assemble_and_check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("- none", self.ws.report())

    def test_assembly_strips_source_comments_and_builds_toc(self) -> None:
        run("assemble", str(self.ws.path))
        manuscript = (self.ws.path / "manuscript.md").read_text(encoding="utf-8")
        self.assertNotIn("src:", manuscript)
        self.assertIn("# 차례", manuscript)
        self.assertIn("- 1장. 웹훅이 두 번 오는 이유", manuscript)
        self.assertIn("    - 재시도", manuscript)

    def test_toc_keeps_inline_code_in_headings(self) -> None:
        # Observed in the 2026-11-20 smoke run: "넣기: `enqueue`와 작업의 모양" became
        # "넣기: 와 작업의 모양" in the table of contents.
        self.ws.write("chapters/02.md", CHAPTER_2.replace("## 이벤트 ID", "## 넣기: `enqueue`와 작업의 모양"))
        run("assemble", str(self.ws.path))
        manuscript = (self.ws.path / "manuscript.md").read_text(encoding="utf-8")
        self.assertIn("    - 넣기: `enqueue`와 작업의 모양", manuscript)

    def test_each_marker_is_a_hard_failure(self) -> None:
        markers = run("markers").stdout.split("\n")
        markers = [m for m in markers if m]
        self.assertGreaterEqual(len(markers), 4)
        for marker in markers:
            with self.subTest(marker=marker):
                self.ws.write("chapters/02.md", CHAPTER_2 + "\n여기는 " + marker + " 입니다.\n")
                result = self.assemble_and_check()
                self.assertEqual(result.returncode, 1)
                self.assertIn("leftover marker " + marker, result.stdout)

    def test_title_with_quotes_and_backslash_round_trips(self) -> None:
        self.ws.meta["title"] = 'AI가 "설계"한다: C:\\path'
        self.ws.save_meta()
        result = self.assemble_and_check()
        self.assertEqual(result.returncode, 0, result.stdout)
        manuscript = (self.ws.path / "manuscript.md").read_text(encoding="utf-8")
        self.assertIn('# AI가 "설계"한다: C:\\path', manuscript)

    def test_invalid_metadata_is_a_hard_failure(self) -> None:
        cases = {
            "broken json": "{",
            "missing author": json.dumps({"title": "t", "chapters": ["chapters/01.md"]}),
            "control char": json.dumps({"title": "t\u0007", "author": "a", "chapters": ["chapters/01.md"]}),
            "missing file": json.dumps({"title": "t", "author": "a", "chapters": ["chapters/09.md"]}),
            "escapes workspace": json.dumps({"title": "t", "author": "a", "chapters": ["../x.md"]}),
        }
        run("assemble", str(self.ws.path))
        for name, text in cases.items():
            with self.subTest(name=name):
                self.ws.write("book.json", text)
                result = run("check", str(self.ws.path))
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertIn("HARD book.json", result.stdout)

    def test_chapter_edited_after_assembly_is_a_hard_failure(self) -> None:
        run("assemble", str(self.ws.path))
        self.ws.write("chapters/01.md", CHAPTER_1.replace("3회", "5회"))
        result = run("check", str(self.ws.path))
        self.assertEqual(result.returncode, 1)
        self.assertIn("chapters/01.md differs from manuscript.md", result.stdout)

    def test_hash_lock_after_accept(self) -> None:
        self.assemble_and_check()
        run("accept", str(self.ws.path), "--verdict", "ACCEPT", "--note", "round 1")
        self.assertEqual(run("check", str(self.ws.path), "--final").returncode, 0)
        self.ws.write("chapters/02.md", CHAPTER_2 + "\n덧붙인 문장입니다.\n")
        result = self.assemble_and_check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("changed after the last verdict (ACCEPT)", result.stdout)

    def test_blocked_draft_may_change_but_final_needs_a_new_verdict(self) -> None:
        self.assemble_and_check()
        run("accept", str(self.ws.path), "--verdict", "BLOCK")
        self.ws.write("chapters/02.md", CHAPTER_2 + "\n고친 문장입니다.\n")
        self.assertEqual(self.assemble_and_check().returncode, 0)
        final = run("check", str(self.ws.path), "--final")
        self.assertEqual(final.returncode, 1)
        run("accept", str(self.ws.path), "--verdict", "USER_APPROVED", "--note", "사용자 승인")
        self.assertEqual(run("check", str(self.ws.path), "--final").returncode, 0)
        record = json.loads((self.ws.path / "checks" / "acceptance.json").read_text(encoding="utf-8"))
        self.assertEqual([h["verdict"] for h in record["history"]], ["BLOCK", "USER_APPROVED"])

    def test_final_without_acceptance_fails(self) -> None:
        result = self.assemble_and_check("--final")
        self.assertEqual(result.returncode, 1)
        self.assertIn("no acceptance record", result.stdout)

    def test_report_only_findings_do_not_block(self) -> None:
        self.ws.write(
            "chapters/02.md",
            CHAPTER_2
            + "\n9장에서 다시 봅니다. 다음 장에서는 웹 훅을 봅니다.\n\n"
            + "<선택적 사전조건>을 채우세요.\n\n응답 시간은 30% 줄었습니다.\n\n"
            + "오케스트레이터가 RA02를 확인했습니다.\n",
        )
        result = self.assemble_and_check()
        self.assertEqual(result.returncode, 0, result.stdout)
        report = self.ws.report()
        self.assertIn("9장 (no such chapter)", report)
        self.assertIn("'다음 장에서' teaser", report)
        self.assertIn("'웹 훅' (plan says '웹훅')", report)
        self.assertIn("<선택적 사전조건>", report)
        self.assertIn("응답 시간은 30% 줄었습니다", report)
        self.assertIn("'오케스트레이터'", report)
        self.assertIn("ledger id 'RA02' visible", report)

    def test_bold_before_korean_particle_is_reported(self) -> None:
        # Observed in the accepted smoke manuscript; markdown-it 14.1.0 renders
        # "**멱등성(idempotency)**은" with literal asterisks.
        self.ws.write(
            "chapters/02.md",
            CHAPTER_2 + "\n**멱등성(idempotency)**은 중요합니다. **멱등성**(idempotency)은 괜찮습니다.\n",
        )
        result = self.assemble_and_check()
        self.assertEqual(result.returncode, 0, result.stdout)
        report = self.ws.report()
        self.assertIn("bold will not render: **멱등성(idempotency)**", report)
        self.assertNotIn("bold will not render: **멱등성**", report)

    def test_term_variant_inside_another_word_is_not_reported(self) -> None:
        # Observed in the pilot: '리스' (avoid for 'lease') matched inside '릴리스'.
        self.ws.write("plan.md", PLAN + "| lease | 리스 | lease |\n")
        self.ws.write("chapters/02.md", CHAPTER_2 + "\n릴리스 노트를 봅니다. 리스는 피합니다.\n")
        self.assemble_and_check()
        report = self.ws.report()
        self.assertEqual(report.count("'리스' (plan says 'lease')"), 1)

    def test_placeholder_inside_code_is_not_reported(self) -> None:
        self.ws.write("chapters/02.md", CHAPTER_2 + "\n```text\n<선택적 사전조건>\n```\n\n`<이름>` 자리에 넣습니다.\n")
        self.assemble_and_check()
        self.assertNotIn("### placeholders", self.ws.report())

    @unittest.skipUnless(SYSTEM_PYTHON.is_file(), "stock macOS python3 not present")
    def test_runs_on_stock_macos_python(self) -> None:
        version = subprocess.run(
            [str(SYSTEM_PYTHON), "-c", "import sys; print(sys.version_info[:2])"],
            capture_output=True,
            text=True,
        ).stdout
        if "(3, 9)" not in version:
            self.skipTest("system python is not 3.9: " + version)
        python = str(SYSTEM_PYTHON)
        self.assertEqual(run("assemble", str(self.ws.path), python=python).returncode, 0)
        result = run("check", str(self.ws.path), python=python)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
