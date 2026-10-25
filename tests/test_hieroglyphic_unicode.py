import pathlib
import sys
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'src'))
from hieroglyphic_unicode import native_word,has_format_controls

class NativeWordTests(unittest.TestCase):
 def test_plain_unicode_word(self):
  self.assertTrue(native_word('𓄿𓂝'))
  self.assertFalse(native_word('nfr'))
 def test_unambiguous_format_joiners(self):
  for word in ['𓀀𓐱𓀁','𓀀𓐰𓀁','𓐷𓀀𓐰𓀁𓐸','𓀀𓐲𓀁',
               '𓐷𓀀𓐱𓐷𓀁𓐰𓀂𓐸𓐸','𓐼𓀀𓐽','𓀀𓐶𓀁','𓑀𓀁']:
   with self.subTest(word=word):self.assertTrue(native_word(word))
 def test_invalid_structure_and_damage_are_excluded(self):
  for word in ['', '𓐱𓀀','𓀀𓐱','𓀀𓐱𓐰𓀁','𓐷𓀀','𓀀𓐸',
               '𓐷𓀀𓐽','𓐷𓐸','𓑀','𓑀𓑀𓀀','𓀀𓑃',
               '𓀀𓐱𓑃','𓀀<g>A1</g>','𓀀[⯑]','𓀀𓐿']:
   with self.subTest(word=word):self.assertFalse(native_word(word))
 def test_formatted_not_fragmented(self):
  self.assertTrue(has_format_controls('𓀀𓐱𓀁'))
  self.assertFalse(has_format_controls('𓀀𓀁'))

if __name__=='__main__':unittest.main()
