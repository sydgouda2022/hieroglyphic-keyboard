import test from 'node:test';
import assert from 'node:assert/strict';
import {keyboardKey,prepareKeyboardIndex,predictKeyboard} from '../src/keyboard_search.mjs';
const corpus={entries:[
 {ref:'tla:1',signs:'𓄿𓂝',attestations:5,source:'TLA-LE19',lemma:'L1'},
 {ref:'tla:2',signs:'𓄿𓈖',attestations:12,source:'TLA-LE19',lemma:'L2'},
 {ref:'tla:3',signs:'𓄿𓈖',attestations:3,source:'TLA-LE19',lemma:'L3'},
 {ref:'ramses:1',signs:'𓄿𓅓',attestations:80,source:'RAMSES-WORD-MODEL-2023',lexical_identity_verified:false},
 {ref:'tla:4',signs:'𓅓𓈖',attestations:9,source:'TLA-LE19',lemma:'tla19:large'}]};
const index=prepareKeyboardIndex('egy',corpus);
test('only Egyptian Unicode and language accepted',()=>{
 assert.equal(keyboardKey('𓄿','egy'),'𓄿');
 assert.throws(()=>keyboardKey('x','cop'),RangeError);
 assert.throws(()=>prepareKeyboardIndex('cop',corpus),RangeError);
});
test('raw first and exact citation retained',()=>{
 const r=predictKeyboard(index,'𓄿𓂝');
 assert.equal(r[0].raw,true);assert.equal(r[0].attested,true);assert.equal(r[0].lexicon_ref,'tla:1');
 assert.deepEqual(predictKeyboard(index,'nfr').map(x=>x.text),['nfr']);
});
test('homographs collapse visually but preserve all references',()=>{
 const r=predictKeyboard(index,'𓄿',{limit:6});
 const homograph=r.find(x=>x.text==='𓄿𓈖');
 assert.deepEqual(homograph.lexicon_refs.sort(),['tla:2','tla:3']);
 assert.equal(r.filter(x=>x.text==='𓄿𓈖').length,1);
});
test('corpus-only word model never claims lemma verification',()=>{
 const r=predictKeyboard(index,'𓄿',{limit:6});
 const model=r.find(x=>x.text==='𓄿𓅓');
 assert.equal(model.source,'RAMSES-CORPUS');
 assert.equal(model.lexicalIdentityVerified,false);
});
test('learned raw personal strings cannot masquerade as attestations',()=>{
 const r=predictKeyboard(index,'𓄿',{limit:6,learned:{'egy:𓄿𓆓':11}});
 const p=r.find(x=>x.text==='𓄿𓆓');
 assert.ok(p.personal);assert.equal(p.attested,false);assert.equal(p.lexicon_ref,null);
});
test('prefix search and fixed limit are enforced',()=>{
 assert.equal(predictKeyboard(index,'𓄿',{limit:2}).length,2);
 assert.deepEqual(predictKeyboard(index,''),[]);
 assert.throws(()=>predictKeyboard(index,'𓄿',{limit:0}),RangeError);
 assert.ok(predictKeyboard(index,'𓅓',{limit:6}).some(x=>x.text==='𓅓𓈖'));
});
test('large native word index is searchable',()=>{
 const entries=Array.from({length:25000},(_,i)=>({ref:'r'+i,signs:'𓄿'+String.fromCodePoint(0x13000+i%1000)+'𓈖',attestations:i+1,source:'TLA-LE19'}));
 const big=prepareKeyboardIndex('egy',{entries});
 assert.ok(predictKeyboard(big,'𓄿',{limit:4}).length>1);
});

test('Ramses model-only exact input is never marked text-attested',()=>{
 const model=prepareKeyboardIndex('egy',{entries:[
  {ref:'r:1',signs:'𓄿𓈖',source:'RAMSES-WORD-MODEL-2023',
   attestations:50000,lexical_identity_verified:false}
 ]});
 const result=predictKeyboard(model,'𓄿𓈖');
 assert.equal(result[0].attested,false);
 assert.equal(result[0].lexicalIdentityVerified,false);
});
test('model-estimated frequency cannot outrank textual attestation',()=>{
 const mix=prepareKeyboardIndex('egy',{entries:[
  {ref:'model:1',signs:'𓄿𓈖',source:'RAMSES-WORD-MODEL-2023',
   attestations:100000000,lexical_identity_verified:false},
  {ref:'tla:1',signs:'𓄿𓂝',source:'TLA-LE19',lemma:'tla19:123',attestations:1}
 ]});
 const result=predictKeyboard(mix,'𓄿',{limit:3});
 assert.equal(result[1].source,'LATE');
 assert.equal(result[1].attested,true);
 assert.equal(result[2].source,'RAMSES-CORPUS');
 assert.equal(result[2].attested,false);
});
test('legacy array records cannot invent lexical verification or sources',()=>{
 assert.throws(()=>prepareKeyboardIndex('egy',{entries:[['𓄿',7,'lemma','source']]}),/legacy arrays/);
});
