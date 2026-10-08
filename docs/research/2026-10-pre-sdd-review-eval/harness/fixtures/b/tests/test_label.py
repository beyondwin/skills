import unittest
from src.label import label

class LabelTest(unittest.TestCase):
    def test_existing(self):
        self.assertEqual(label("Ada"), "Parcel: Ada")
