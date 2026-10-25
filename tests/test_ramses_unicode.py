import pathlib,sys,unittest
from unittest.mock import patch
import json,hashlib,tempfile
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'src'))
import ramses_unicode
class RamsesTests(unittest.TestCase):
 def test_plain_sign_words(self):
  self.assertEqual(ramses_unicode.ramses_native_word('A1 G39'),'𓀀𓅭')
  self.assertEqual(ramses_unicode.ramses_native_word('G17 X1'),'𓅓𓏏')
 def test_invalid_does_not_partially_convert(self):
  for x in ['A1 Ff100','A1 nTr','2','A1:A2','A1-A2','A1  G17',
            ' A1','A1 ','SHADED1 A1','A1 MISSING','A999','']:
   with self.subTest(x=x):self.assertIsNone(ramses_unicode.ramses_native_word(x))
 def test_audit_rejects_unpinned_source(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=pathlib.Path(tmp)/'model.json'
   p.write_text(json.dumps({'modelName':'Ramses','words':[
    {'encoding':'A1 G39','interpretations':[{'freq':4}]},
    {'encoding':'A1 Ff100','interpretations':[{'freq':19}]}
   ]}))
   with self.assertRaises(ValueError):ramses_unicode.audit_ramses(p)
   with patch.object(ramses_unicode,'RAMSES_MODEL_SHA256',hashlib.sha256(p.read_bytes()).hexdigest()):
    c,refs,stats=ramses_unicode.audit_ramses(p)
   self.assertEqual(c['𓀀𓅭'],4)
   self.assertEqual(len(c),1)
   self.assertEqual(stats['excluded_encoding_rows'],1)
if __name__=='__main__':unittest.main()
