import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from build_master import build_master
from export_runtime import make_runtime_pack

class ExportRuntimeTests(unittest.TestCase):
 def test_both_apps_use_same_release_and_hide_corpus_payload(self):
  with tempfile.TemporaryDirectory() as t:
   db=Path(t)/'db.sqlite3'
   m={'schema':1,'sources':[{'id':'S1','version':'1','license':'CC-BY-SA-4.0','sha256':'a'*64,'lineage':'G1'}]}
   r=[dict(id='1',language='egy',stage='Late Egyptian',surface='𓄿',sourceId='S1',sourceRef='text1:p1',attested=True,lemmaId='L1')]
   build_master(r,m,db,allow_test_sources=True)
   a=make_runtime_pack(db)
   b=make_runtime_pack(db)
   self.assertEqual(a,b)
   self.assertEqual(a['rows'][0]['surface'],'𓄿')
   self.assertEqual(a['rows'][0]['evidenceCount'],1)
   self.assertNotIn('originalText',json.dumps(a))
   self.assertEqual(a['distribution'],'local')
   self.assertEqual(make_runtime_pack(db,distribution='public')['rows'],a['rows'])
 def test_public_release_restricted_but_local_index_not_blocked(self):
  with tempfile.TemporaryDirectory() as t:
   db=Path(t)/'db.sqlite3'
   m={'schema':1,'sources':[{'id':'PRIVATE','version':'1','license':'research-only','sha256':'a'*64}]}
   r=[dict(id='1',language='egy',stage='Late Egyptian',surface='𓄿',sourceId='PRIVATE',sourceRef='p1',attested=True,lemmaId='L1')]
   build_master(r,m,db,allow_test_sources=True)
   self.assertEqual(make_runtime_pack(db)['sourceEditions'],1)
   with self.assertRaises(PermissionError):make_runtime_pack(db,distribution='public')

if __name__=='__main__':unittest.main()
