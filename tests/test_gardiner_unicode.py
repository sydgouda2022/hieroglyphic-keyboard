import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'src'))
from gardiner_unicode import gardiner_sequence,decoded_aes_token
class GardinerTests(unittest.TestCase):
 def test_complete_plain_sequences(self):
  self.assertEqual(gardiner_sequence('A1-N35-Z1'),'𓀀𓈖𓏤')
  self.assertEqual(gardiner_sequence('D46a-X1'),'𓂨𓏏')
 def test_mdc_layout_unknown_and_damage_rejected(self):
  for text in ['Ff101','A1-FF101','A1:', 'A1*A2','A1 N35','𓀀',
                'A1-','-A1','A1[missing]','A1-A999','']:
   with self.subTest(value=text):self.assertIsNone(gardiner_sequence(text))
 def test_existing_unicode_takes_precedence(self):
  a={'hiero_unicode':'&#x13000;&#x13216;','hiero':'A1-D46'}
  self.assertEqual(decoded_aes_token(a),('𓀀𓈖','encoded_unicode'))
  self.assertEqual(decoded_aes_token({'hiero_unicode':'&#x13000;[⯑]','hiero':'A1'}),(None,None))
 def test_no_unattested_transliteration(self):
  self.assertEqual(decoded_aes_token({'hiero':'A1-N35'}),('𓀀𓈖','gardiner_sequence'))
  self.assertEqual(decoded_aes_token({'written_form':'nfr'}),(None,None))
if __name__=='__main__':unittest.main()
