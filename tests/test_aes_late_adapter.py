import importlib.util
import pathlib
import tempfile
import unittest
from unittest.mock import patch
import json
import hashlib
import sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from aes_late_adapter import curated_aes_rows
import aes_late_adapter

class Tests(unittest.TestCase):
    def test_filters_by_whitelisted_document_date_and_exact_unicode(self):
        corpus={
          'a':{'text':'late1','date':'NK','token':[{'_id':'t1','lemmaID':'200','hiero_unicode':'&#x13000;&#x131d3;'},
            {'_id':'t2','lemmaID':'200','hiero_unicode':'&#x13000;&#x131d3;'},
            {'_id':'t3','lemmaID':'200','hiero_unicode':'&#x13000;?'}]},
          'b':{'text':'early','date':'MK & SIP','token':[{'_id':'t4','lemmaID':'200','hiero_unicode':'&#x13000;'}]},
          'c':{'text':'late1','date':'MK & SIP','token':[{'_id':'t5','lemmaID':'200','hiero_unicode':'&#x13000;'}]},
        }
        whitelist={'schema':1,'edition':'AES 35276d2527cca1a055e31ed5f6683e777717170f',
            'documents':[{'id':'late1','title':'Test manuscript','stage_basis':'Evidence','allowed_dates':['NK']}]}
        with tempfile.TemporaryDirectory() as tmp:
            aes=pathlib.Path(tmp)/'aes.json'
            wl=pathlib.Path(tmp)/'manifest.json'
            raw=json.dumps(corpus).encode()
            aes.write_bytes(raw)
            wl.write_text(json.dumps(whitelist))
            with patch.object(aes_late_adapter,'AES_SAWLIT_SHA',hashlib.sha256(raw).hexdigest()):
                counts,refs,stats,_=curated_aes_rows(aes,wl)
        self.assertEqual(counts[('200','𓀀𓇓')],2)
        self.assertEqual(len(refs[('200','𓀀𓇓')]),2)
        self.assertEqual(stats['rejected_wrong_date'],1)
        self.assertEqual(stats['rejected_missing_or_incomplete_signs'],1)
        self.assertEqual(stats['qualified_tokens'],2)
    def test_rejects_unpinned_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            aes=pathlib.Path(tmp)/'aes.json';aes.write_text('{}')
            wl=pathlib.Path(tmp)/'manifest.json';wl.write_text('{}')
            with self.assertRaisesRegex(ValueError,'differs'):curated_aes_rows(aes,wl)
if __name__=='__main__':unittest.main()
