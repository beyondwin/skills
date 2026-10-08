"""Provider-free checks of the synthetic ground truth, not a model-quality test."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

FIXTURES = Path(__file__).resolve().parent / 'fixtures'


class OracleChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def fixture(self, case):
        repo = self.root / case
        shutil.copytree(FIXTURES / case, repo)
        return repo

    def command(self, repo, args):
        return subprocess.run(args, cwd=repo, capture_output=True, text=True,
                              env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))

    def test_all_baselines_are_executable(self):
        for case in 'abcd':
            with self.subTest(case=case):
                result = self.command(self.fixture(case), [
                    'python3', '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_*.py', '-v'])
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('Ran 1 test', result.stderr)

    def test_b_counterexample_passes_proposed_cases_but_breaks_approved_empty_case(self):
        repo = self.fixture('b')
        result = self.command(repo, ['python3', '-c',
            'from src.label import label; '
            'assert all(label(x) == "Parcel: " + x for x in ["Ada", "  aDa  ", " ", "나래"]); '
            'assert label("") != "Parcel: Anonymous"'])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((repo / 'tools/check.py').exists())

    def test_d_writer_only_change_breaks_existing_consumer(self):
        repo = self.fixture('d')
        writer = repo / 'src/writer.py'
        writer.write_text(writer.read_text().replace(
            '{"sequence": sequence, "payload": payload}',
            '{"sequence": sequence, "payload": payload, "origin": "local"}'))
        result = self.command(repo, ['python3', '-m', 'unittest', 'discover', '-s', 'tests'])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('ValueError: Invalid record shape', result.stderr)
        (repo / 'src/contract.py').write_text(
            'RECORD_KEYS = frozenset({"sequence", "payload", "origin"})\n')
        repaired = self.command(repo, ['python3', '-m', 'unittest', 'discover', '-s', 'tests'])
        self.assertEqual(repaired.returncode, 0, repaired.stderr)

    def test_d_planned_command_skips_failing_nested_acceptance(self):
        repo = self.fixture('d')
        tests = repo / 'tests/contracts'
        tests.mkdir()
        (tests / 'test_origin.py').write_text(
            'import unittest\nclass OriginTest(unittest.TestCase):\n'
            '    def test_origin(self):\n        self.fail("acceptance sentinel")\n')
        args = ['python3', '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_*.py', '-v']
        skipped = self.command(repo, args)
        self.assertEqual(skipped.returncode, 0, skipped.stderr)
        self.assertIn('Ran 1 test', skipped.stderr)
        (tests / '__init__.py').write_text('')
        found = self.command(repo, args)
        self.assertNotEqual(found.returncode, 0)
        self.assertIn('acceptance sentinel', found.stderr)
        self.assertIn('Ran 2 tests', found.stderr)

    def test_exact_category_assertions_reject_normalization_mutants(self):
        # These representative inputs instantiate the plan's named categories;
        # arbitrary test method names cannot change the specified assertions.
        cases = [('', 'Parcel: Anonymous'), ('Ada', 'Parcel: Ada'),
                 ('  aDa  ', 'Parcel:   aDa  '), (' ', 'Parcel:  '),
                 ('나래', 'Parcel: 나래')]
        correct = lambda s: 'Parcel: ' + ('Anonymous' if s == '' else s)
        mutants = [lambda s: correct(s.strip()), lambda s: correct(s.lower()),
                   lambda s: correct('' if not s.strip() else s)]
        self.assertTrue(all(correct(s) == expected for s, expected in cases))
        for mutant in mutants:
            self.assertFalse(all(mutant(s) == expected for s, expected in cases))

    def test_weakened_assertions_admit_the_same_wrong_implementations(self):
        # A real verification gap remains when assertions only check the prefix.
        cases = ['', 'Ada', '  aDa  ', ' ', '나래']
        correct = lambda s: 'Parcel: ' + ('Anonymous' if s == '' else s)
        mutants = [lambda s: correct(s.strip()), lambda s: correct(s.lower()),
                   lambda s: correct('' if not s.strip() else s)]
        for mutant in mutants:
            self.assertTrue(all(mutant(s).startswith('Parcel: ') for s in cases))


if __name__ == '__main__':
    unittest.main()
