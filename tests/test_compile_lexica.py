import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1] / 'src'))
from compile_lexica import build_egyptian,build_coptic,source_rows
from unittest.mock import patch
import hashlib
import ramses_unicode

class Tests(unittest.TestCase):
 def test_tla_late_not_inventing_incomplete_spellings(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'tla.jsonl'
   rows=[
    {'hieroglyphs':'𓄿𓂝 𓎛𓏏','lemmatization':'123|a 456|b'},
    {'hieroglyphs':'𓄿𓂝 𓁷<g>Ff101</g>𓏤','lemmatization':'123|a 789|c'},
    {'hieroglyphs':'𓄿𓂝 𓎛𓏏','lemmatization':'bad data'},
   ];p.write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in rows))
   counts,_,stats=source_rows(p)
   self.assertEqual(stats['unencoded_word_tokens'],1)
   self.assertIn(('123','𓄿𓂝'),counts)
   self.assertIn(('unresolved','𓎛𓏏'),counts)
   aed=Path(tmp)/'aed.xml'
   aed.write_text('<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body><entry xml:id="tla123"><form><orth>aaa</orth></form><sense><cit type="translation" xml:lang="en"><quote>test gloss</quote></cit></sense></entry></body></text></TEI>')
   r=build_egyptian(p,aed,Path(tmp)/'result')
   self.assertGreaterEqual(r['unique_spellings'],3)
   self.assertGreaterEqual(r['aed_matched_lemmas'],1)
   db=sqlite3.connect(Path(tmp)/'result/lexicon.sqlite3')
   self.assertEqual(db.execute('pragma integrity_check').fetchone()[0],'ok')
   pack=json.loads((Path(tmp)/'result/lexicon.json').read_text())
   self.assertFalse(pack['metadata']['complete'])
   self.assertTrue(all('<g>' not in x['signs'] for x in pack['entries']))
 def test_ramses_source_is_unlinked_and_deduplicated(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)
   tla=root/'tla.jsonl'
   tla.write_text(json.dumps({'hieroglyphs':'𓀀𓅭','lemmatization':'123|a'},ensure_ascii=False))
   aed=root/'aed.xml'
   aed.write_text('<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body></body></text></TEI>')
   src=root/'ramses.json'
   src.write_text(json.dumps({'modelName':'Ramses Training data transliteration model','words':[
    {'encoding':'A1 G39','interpretations':[{'freq':9}]},
    {'encoding':'G17 X1','interpretations':[{'freq':13}]},
    {'encoding':'A1 Ff100','interpretations':[{'freq':1}]}
   ]}))
   with patch.object(ramses_unicode,'RAMSES_MODEL_SHA256',hashlib.sha256(src.read_bytes()).hexdigest()):
    report=build_egyptian(tla,aed,root/'out',ramses_path=src)
   self.assertEqual(report['ramses_new_spelling_records'],1)
   self.assertEqual(report['ramses_duplicate_existing_surfaces'],1)
   self.assertEqual(report['distinct_lemmas'],1)
   conn=sqlite3.connect(root/'out/lexicon.sqlite3')
   self.assertEqual(conn.execute('select count(*) from corpus_form').fetchone()[0],2)
   self.assertEqual(conn.execute('select count(*) from spelling').fetchone()[0],2)
   row=conn.execute("select lemma_id from spelling where native_form='𓅓𓏏'").fetchone()
   self.assertTrue(row[0].startswith('ramses-unlinked:'))
   self.assertEqual(conn.execute('pragma integrity_check').fetchone()[0],'ok')
   conn.close()
   catalog=json.loads((root/'out/lexicon.json').read_text())
   self.assertFalse(catalog['metadata']['complete'])
   self.assertEqual(catalog['metadata']['unique_native_surfaces'],2)
 def test_coptic_dialects_and_homographs(self):
  with tempfile.TemporaryDirectory() as tmp:
   t=Path(tmp);tei=t/'lex.xml';tei.write_text('''<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body>
<entry xml:id="C1"><form xml:id="F1"><usg type="geo">S</usg><orth>ⲡⲉ</orth></form><form xml:id="F2"><usg type="geo">B</usg><orth>ⲡⲉ</orth></form></entry>
<entry xml:id="C2"><form xml:id="F3"><usg type="geo">A</usg><orth>ⲟⲩ</orth></form></entry>
</body></text></TEI>''')
   original=t/'orig.json';original.write_text(json.dumps({'dialects':['Sahidic','Bohairic'],'rows':[['ⲁⲛ',1],['ⲡⲉ',1],['ϭⲱ',2]]},ensure_ascii=False))
   extra=t/'pop.json';extra.write_text(json.dumps({'rows':[['ⲡⲉ',15],['ⲫⲱ',7]]},ensure_ascii=False))
   r=build_coptic(tei,original,extra,t/'result')
   self.assertEqual(r['tei_lemmas'],2)
   p=json.loads((t/'result/lexicon.json').read_text())
   got=dict(p['rows']);self.assertEqual(got['ⲡⲉ'],3)
   self.assertEqual(got['ⲟⲩ'],0)
   self.assertEqual(got['ⲫⲱ'],0)
   self.assertEqual(p['popularity']['ⲡⲉ'],15)
   db=sqlite3.connect(t/'result/lexicon.sqlite3')
   self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0],'ok')
 def test_complete_grouped_unicode_word_is_preserved(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'tla.jsonl'
   p.write_text(json.dumps({'hieroglyphs':'𓀀𓐱𓀁 𓀀𓐱 𓑃',
                             'lemmatization':'123|one 124|bad 125|damage'},ensure_ascii=False))
   records,_,stats=source_rows(p)
   self.assertIn(('123','𓀀𓐱𓀁'),records)
   self.assertEqual(stats['formatted_word_tokens'],1)
   self.assertEqual(stats['unencoded_word_tokens'],2)
 def test_no_invented_transliteration(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'tla';p.write_text(json.dumps({'hieroglyphs':'nfr ⲁ','lemmatization':'1|nfr 2|a'}))
   counts,_,stats=source_rows(p)
   self.assertEqual(len(counts),0)
   self.assertEqual(stats['unencoded_word_tokens'],2)

if __name__=='__main__':unittest.main()
