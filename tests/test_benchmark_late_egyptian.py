import json,pathlib,sys,tempfile,unittest
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'src'))
import benchmark_late_egyptian
class BenchmarkTest(unittest.TestCase):
 def test_leave_one_document_out_excludes_its_own_training_data(self):
  data={
   's1':{'text':'a','date':'NK','token':[{'lemmaID':'1','hiero_unicode':'&#x13000;'},
         {'lemmaID':'1','hiero_unicode':'&#x13000;'},
         {'lemmaID':'2','hiero_unicode':'&#x13001;'}]},
   's2':{'text':'b','date':'NK','token':[{'lemmaID':'1','hiero_unicode':'&#x13000;'},
         {'lemmaID':'3','hiero_unicode':'&#x13002;'}]}}
  manifest={'schema':1,'edition':'AES 35276d2527cca1a055e31ed5f6683e777717170f',
   'documents':[{'id':x,'title':x,'allowed_dates':['NK']} for x in ('a','b')]}
  with tempfile.TemporaryDirectory() as temp:
   root=pathlib.Path(temp);aes=root/'aes.json';aes.write_text(json.dumps(data))
   tla=root/'tla.jsonl';tla.write_text(json.dumps({'hieroglyphs':'𓀀','lemmatization':'1|one'}))
   whitelist=root/'whitelist.json';whitelist.write_text(json.dumps(manifest))
   import hashlib
   with patch.object(benchmark_late_egyptian,'AES_SAWLIT_SHA',hashlib.sha256(aes.read_bytes()).hexdigest()):
    report=benchmark_late_egyptian.benchmark(aes,whitelist,tla)
  self.assertEqual(report['total_eligible_tokens'],5)
  doc_a=next(x for x in report['documents'] if x['document_id']=='a')
  self.assertEqual(doc_a['tla_token_coverage'],0.6667)
  self.assertEqual(doc_a['leave_document_out_token_coverage'],0.6667)
  doc_b=next(x for x in report['documents'] if x['document_id']=='b')
  self.assertEqual(doc_b['leave_document_out_token_coverage'],0.5)
  self.assertTrue(report['not_a_complete_historical_coverage_claim'])
if __name__=='__main__':unittest.main()
