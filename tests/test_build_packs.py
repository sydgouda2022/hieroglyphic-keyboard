import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from build_packs import compile_records

M = {'schema': 1, 'sources': [dict(id='TEST', version='test', license='synthetic-test-only',
      attribution='TEST',url='https://example.invalid',sha256='0'*64)]}

class Tests(unittest.TestCase):
    def test_reject_missing_provenance(self):
        with self.assertRaisesRegex(ValueError, 'source'):
            compile_records([{'id':'e1','language':'egy','surface':'𓄿','stage':'Late Egyptian',
                              'sourceId':'NOT-REGISTERED','sourceRef':'r1','attested':True}],M,'egy')
    def test_no_fabricated_records(self):
        with self.assertRaisesRegex(ValueError,'attested'):
            compile_records([{'id':'e1','language':'egy','surface':'𓄿','stage':'Late Egyptian',
                              'sourceId':'TEST','sourceRef':'r1','attested':False}],M,'egy')
    def test_separate_packs(self):
        both=[{'id':'e1','language':'egy','surface':'𓄿','stage':'Late Egyptian','sourceId':'TEST','sourceRef':'r1','attested':True},
              {'id':'c1','language':'cop','surface':'ⲡⲉ','dialect':'sahidic','sourceId':'TEST','sourceRef':'r2','attested':True}]
        self.assertEqual(len(compile_records(both,M,'egy')['rows']),1)
        self.assertEqual(len(compile_records(both,M,'cop')['rows']),1)
    def test_reject_transliteration_only(self):
        with self.assertRaisesRegex(ValueError,'native-script'):
            compile_records([{'id':'e1','language':'egy','surface':'nfr','stage':'Late Egyptian',
                              'sourceId':'TEST','sourceRef':'r1','attested':True}],M,'egy')

if __name__=='__main__': unittest.main()
