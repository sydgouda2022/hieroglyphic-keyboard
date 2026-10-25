import test from 'node:test';
import assert from 'node:assert/strict';
import {keyboardKey,prepareKeyboardIndex,predictKeyboard} from '../src/keyboard_search.mjs';
test('Egyptian language isolation and typed spelling records',()=>{
 assert.throws(()=>keyboardKey('ⲡ','cop'),RangeError);
 assert.throws(()=>prepareKeyboardIndex('cop',{entries:[]}),RangeError);
 assert.throws(()=>prepareKeyboardIndex('egy',{rows:[['𓄿',2]]}),TypeError);
 const index=prepareKeyboardIndex('egy',{entries:[
  {ref:'tla:1',signs:'𓄿𓂝',source:'TLA-LE19',lemma:'tla19:1',attestations:4}
 ]});
 const r=predictKeyboard(index,'𓄿');
 assert.equal(r[0].raw,true);
 assert.equal(r[1].attested,true);
});
