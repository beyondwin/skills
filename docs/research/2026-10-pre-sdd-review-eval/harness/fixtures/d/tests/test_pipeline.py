import unittest
from src.pipeline import roundtrip

class PipelineTest(unittest.TestCase):
    def test_roundtrip(self):
        self.assertEqual(roundtrip(4, "one"), (4, "one"))
