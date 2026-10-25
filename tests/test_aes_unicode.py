import importlib.util
import pathlib
import unittest

SRC=pathlib.Path(__file__).resolve().parents[1]/'src'/'aes_unicode.py'
spec=importlib.util.spec_from_file_location('aes_unicode',SRC)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class TestAESUnicode(unittest.TestCase):
    def test_html_entities_exact(self):
        self.assertEqual(module.decode_aes_hiero('&#x131d3;&#x132b5;'),'𓇓𓊵')
    def test_preserve_literal_hieroglyphs(self):
        self.assertEqual(module.decode_aes_hiero('𓇓&#x132b5;'),'𓇓𓊵')
    def test_disallow_markup_damage_and_partial(self):
        for x in ['&#x131d3','&#x131d3; ...','[𓇓]','&#xZZZZ;','&#x131d3;<i>','𓇓?','𓇓 ','','&#x41;','hiero']:
            with self.subTest(x=x):
                self.assertIsNone(module.decode_aes_hiero(x))
    def test_exact_html_encoded_format_controls(self):
        self.assertEqual(module.decode_aes_hiero('&#x13000;&#x13431;&#x13001;'),'𓀀𓐱𓀁')
        self.assertEqual(module.decode_aes_hiero('&#x13437;&#x13000;&#x13438;'),'𓐷𓀀𓐸')
        self.assertIsNone(module.decode_aes_hiero('&#x13000;&#x13431;'))
        self.assertIsNone(module.decode_aes_hiero('&#x13000;&#x13443;'))
    def test_length_limit(self):
        self.assertIsNone(module.decode_aes_hiero('𓇓'*257))
    def test_decimal_entities(self):
        self.assertEqual(module.decode_aes_hiero('&#77824;'),chr(77824))

if __name__=='__main__':unittest.main()
