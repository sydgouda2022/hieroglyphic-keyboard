import copy
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1] / 'src'))
from source_registry import read_registry,validate_registry,verified_source_manifest,compatible_license

class SourceRegistryTests(unittest.TestCase):
 def setUp(self):self.registry=read_registry()
 def test_only_four_open_editions_in_priority_order(self):
  self.assertEqual([x['id'] for x in self.registry['sources']],['TLA-LE19','AED','AES','ORAEC'])
  self.assertEqual(validate_registry(self.registry)['permission_required_sources'],0)
 def test_all_sources_build_time_only_and_open(self):
  self.assertFalse(self.registry['runtime_external_sources'])
  self.assertEqual(self.registry['runtime_database'],'lexicon.sqlite3')
  for source in self.registry['sources']:
   self.assertEqual(source['usage'],'build_time_only')
   self.assertFalse(source['runtime_dependency'])
   self.assertTrue(source['publishable'])
   self.assertEqual(source['availability'],'public_data_release')
 def test_shared_source_lineage(self):
  d={s['id']:s for s in self.registry['sources']}
  self.assertEqual(d['AED']['independence_group'],d['AES']['independence_group'])
  self.assertEqual(d['AES']['independence_group'],d['ORAEC']['independence_group'])
 def test_removed_sources_are_not_registered_or_accepted(self):
  for sid in ('RAMSES','LESKO-2ED','TLA-C20'):
   with self.subTest(sid=sid),self.assertRaises(PermissionError):
    verified_source_manifest(self.registry,{sid:dict(path='/tmp/no',version='1',sha256='0'*64,license='x',attribution='a')})
 def test_cannot_reinsert_restricted_source(self):
  for sid in ('RAMSES','LESKO-2ED','TLA-C20'):
   r=copy.deepcopy(self.registry)
   r['sources'].append(dict(r['sources'][-1],id=sid,priority=90))
   with self.subTest(sid=sid),self.assertRaises(ValueError):validate_registry(r)
 def test_actual_file_pin_required(self):
  with tempfile.TemporaryDirectory() as t:
   path=Path(t)/'data';path.write_bytes(b'{"x":1}\n')
   info=dict(path=str(path),version='pin1',sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
             license='CC-BY-SA-4.0',attribution='Editors')
   manifest=verified_source_manifest(self.registry,{'AES':info})
   self.assertEqual(manifest['sources'][0]['id'],'AES')
   self.assertEqual(manifest['sources'][0]['lineage'],'BBAW-2018-EXTRACT')
   with self.assertRaisesRegex(ValueError,'SHA-256'):
    verified_source_manifest(self.registry,{'AES':{**info,'sha256':'0'*64}})
 def test_licenses_still_need_compliance_no_individual_permission(self):
  d={s['id']:s for s in self.registry['sources']}
  self.assertTrue(compatible_license(d['AED'],'CC-BY-SA-4.0'))
  self.assertFalse(compatible_license(d['AED'],'research-only'))
  self.assertTrue(compatible_license(d['ORAEC'],'CC0'))
  self.assertFalse(compatible_license(d['ORAEC'],'unknown'))
  with tempfile.TemporaryDirectory() as t:
   path=Path(t)/'data';path.write_bytes(b'x')
   info=dict(path=str(path),version='v',sha256=hashlib.sha256(b'x').hexdigest(),
             license='copyrighted',attribution='author')
   with self.assertRaisesRegex(ValueError,'license mismatch'):
    verified_source_manifest(self.registry,{'AED':info})

if __name__=='__main__':unittest.main()
