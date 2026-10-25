import json
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from build_keyboard_signs import project
class SignsTests(unittest.TestCase):
    def test_generated_signs_are_exact_projection(self):
        source=(ROOT/"src/keyboard_catalog.js").read_text()
        projected=project(source)
        shipped=json.loads((ROOT/"release/signs.json").read_text())
        self.assertEqual(projected,shipped)
        self.assertEqual(len(shipped["pages"]["uni"]),27)
        self.assertIn(["𓇌","M17A"],shipped["pages"]["uni"])
        self.assertEqual(len(shipped["pages"]["bi"]),151)
        self.assertEqual(len(shipped["pages"]["tri"]),89)
if __name__=="__main__":unittest.main()
