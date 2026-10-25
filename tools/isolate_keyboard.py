#!/usr/bin/env python3
"""One-time language isolation within a migrated GitHub keyboard repository.

Preserves the attested release bytes; only reorganizes compiler, public API
and tests. Generic ranking code is locally vendored, not a fifth dependency.
"""
from __future__ import annotations
import ast
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MODE=sys.argv[1] if len(sys.argv)==2 else ''
if MODE not in ('cop','egy'):
    raise SystemExit('Usage: isolate_keyboard.py cop|egy')
SOURCE=ROOT/'src/compile_lexica.py'
old=SOURCE.read_text(encoding='utf8')
tree=ast.parse(old)
functions={
 'cop':{'digest','coptic','db_connect','persist_json','geo_mask','xml_entries',
        'coptic_tei_forms','build_coptic'},
 'egy':{'digest','hieroglyphic','xml_entries','aed_metadata','source_rows',
        'db_connect','persist_json','build_egyptian'}
}[MODE]
parts=[]
for node in tree.body:
    if isinstance(node,(ast.Import,ast.ImportFrom)):
        fragment=ast.get_source_segment(old,node)
        if MODE=='cop' and 'hieroglyphic_unicode' in fragment:
            continue
        parts.append(fragment)
    elif isinstance(node,ast.Assign):
        names={x.id for x in node.targets if isinstance(x,ast.Name)}
        if names & {'TEI','XML'}:
            parts.append(ast.get_source_segment(old,node))
    elif isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name in functions:
        parts.append(ast.get_source_segment(old,node))
found={n.name for n in tree.body if isinstance(n,ast.FunctionDef)}
if not functions<=found:
    raise ValueError('Publisher compiler no longer matches documented source layout')
if MODE=='cop':
    driver="""if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument('--tei',type=Path,required=True)
    p.add_argument('--forms',type=Path,required=True)
    p.add_argument('--popular',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(build_coptic(a.tei,a.forms,a.popular,a.out),sort_keys=True))
"""
else:
    driver="""if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument('--tla',type=Path,required=True)
    p.add_argument('--aed',type=Path,required=True)
    p.add_argument('--aes',type=Path)
    p.add_argument('--aes-whitelist',type=Path)
    p.add_argument('--ramses',type=Path)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(build_egyptian(a.tla,a.aed,a.out,a.aes,a.aes_whitelist,a.ramses),sort_keys=True))
"""
rewritten='"""Independent '+('Coptic' if MODE=='cop' else 'Late Egyptian')+' lexicon compiler. No other language is compiled.\n"""\n'+'\n\n'.join(parts)+'\n\n'+driver
ast.parse(rewritten)
SOURCE.write_text(rewritten,encoding='utf8')

kernel=ROOT/'src/keyboard_search.mjs'
private=ROOT/'src/_generic_search.mjs'
if not private.exists():
    kernel.replace(private)
kernel.write_text("""/** Independent script-scoped public predictive keyboard.
 * Generic Unicode comparison is vendored locally as a private implementation.
 */
import {keyboardKey as key,prepareKeyboardIndex as prepare,predictKeyboard as predict}
  from './_generic_search.mjs';
const LANGUAGE='"""+MODE+"""';
export function keyboardKey(value,language=LANGUAGE){
  if(language!==LANGUAGE)throw new RangeError('Wrong keyboard language package');
  return key(value,LANGUAGE);
}
export function prepareKeyboardIndex(language,pack){
  if(language!==LANGUAGE)throw new RangeError('Wrong keyboard language package');
  return prepare(language,pack);
}
export function predictKeyboard(index,raw,options={}){
  if(index?.language!==LANGUAGE)throw new RangeError('Wrong keyboard language package');
  return predict(index,raw,options);
}
""",encoding='utf8')
for p in [ROOT/'tests/keyboard_search.test.mjs']:
    if p.exists():
        p.write_text(p.read_text().replace("../src/keyboard_search.mjs","../src/_generic_search.mjs"))

(ROOT/'tests/isolated_keyboard.test.mjs').write_text(
"""import test from 'node:test';
import assert from 'node:assert/strict';
import {keyboardKey,prepareKeyboardIndex,predictKeyboard} from '../src/keyboard_search.mjs';
const lang='"""+MODE+"""';
const other=lang==='cop'?'egy':'cop';
test('language boundary is enforced by the public keyboard API',()=>{
 assert.throws(()=>keyboardKey('x',other),RangeError);
 assert.throws(()=>prepareKeyboardIndex(other,{rows:[]}),RangeError);
 const pack=lang==='cop'?{rows:[['ⲡⲉ',3]],popularity:{'ⲡⲉ':10}}:{entries:[{ref:'tla:1',signs:'𓄿𓂝',attestations:4}]};
 const index=prepareKeyboardIndex(lang,pack);
 const results=predictKeyboard(index,lang==='cop'?'ⲡ':'𓄿');
 assert.equal(results[0].raw,true);
 assert.ok(results.some(x=>!x.raw));
});
""",encoding='utf8')
if MODE=='cop':
    combined=ROOT/'tests/test_compile_lexica.py'
    mixed=combined.read_text()
    parsed=ast.parse(mixed)
    klass=next(x for x in parsed.body if isinstance(x,ast.ClassDef) and x.name=='Tests')
    test=next(x for x in klass.body if isinstance(x,ast.FunctionDef) and
              x.name=='test_coptic_dialects_and_homographs')
    fragment=ast.get_source_segment(mixed,test)
    standalone=('import json,sqlite3,tempfile,unittest\nfrom pathlib import Path\n'
                'import sys\nsys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))\n'
                'from compile_lexica import build_coptic\n\nclass Tests(unittest.TestCase):\n'+
                '\n'.join('    '+line for line in fragment.splitlines())+
                '\n\nif __name__=="__main__":unittest.main()\n')
    ast.parse(standalone)
    (ROOT/'tests/test_coptic_compile.py').write_text(standalone)
    for f in (ROOT/'src').iterdir():
        if f.suffix in ('.py','.mjs') and f.name not in (
            'compile_lexica.py','coptic_install.mjs','keyboard_search.mjs',
            '_generic_search.mjs','predict.mjs','publish_compiled_coptic.py',
            'publish_coptic_release.py'
        ):
            f.unlink()
    for f in (ROOT/'tests').iterdir():
        if f.is_file() and f.name not in (
            'coptic_install.test.mjs','keyboard_search.test.mjs','predict.test.mjs',
            'isolated_keyboard.test.mjs','test_coptic_compile.py'
        ):
            f.unlink()
else:
    combined=ROOT/'tests/test_compile_lexica.py'
    if combined.exists():
        mixed=combined.read_text()
        parsed=ast.parse(mixed)
        klass=next(x for x in parsed.body if isinstance(x,ast.ClassDef) and x.name=='Tests')
        test=next(x for x in klass.body if isinstance(x,ast.FunctionDef) and
                  x.name=='test_coptic_dialects_and_homographs')
        lines=mixed.splitlines(keepends=True)
        del lines[test.lineno-1:test.end_lineno]
        combined.write_text(''.join(lines).replace(
            'from compile_lexica import build_egyptian,build_coptic,source_rows',
            'from compile_lexica import build_egyptian,source_rows'
        ))
print('Language-isolated',MODE,'compiler, public keyboard API and tests.')
