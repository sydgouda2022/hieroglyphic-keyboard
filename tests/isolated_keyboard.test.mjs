import test from 'node:test';
import assert from 'node:assert/strict';
import {keyboardKey,prepareKeyboardIndex,predictKeyboard} from '../src/keyboard_search.mjs';
const lang='egy';
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
