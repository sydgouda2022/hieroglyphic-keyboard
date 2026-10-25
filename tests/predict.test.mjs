import {test} from 'node:test';
import assert from 'node:assert/strict';
import {assertPack,searchKey,suggest} from '../src/predict.mjs';

// Explicitly synthetic CONTRACT fixtures. These are not dictionary records
// or claims of historical attestations, and must never be published as packs.
const fixture=(lang,entries)=>({schema:1,language:lang,rows:entries.map(r=>({
 ...r,language:lang,key:searchKey(r.surface,lang),attested:true,sourceId:'TEST',sourceRef:'synthetic-test-only'
})).sort((a,b)=>a.key<b.key?-1:a.key>b.key?1:a.id<b.id?-1:a.id>b.id?1:0)});

const coptic=fixture('cop',[
 {id:'c1',surface:'ⲡⲉ',dialect:'sahidic',frequency:3},
 {id:'c2',surface:'ⲡⲉⲛ',dialect:'bohairic',frequency:1},
 {id:'c3',surface:'ⲡⲉⲣ',dialect:'sahidic',frequency:70,previous:['ⲛ']},
 {id:'c4',surface:'ⲡⲉ̀ⲣ',dialect:'sahidic',frequency:12},
]);
const egyptian=fixture('egy',[
 {id:'e1',surface:'𓄿𓂋',stage:'Late Egyptian',frequency:6},
 {id:'e2',surface:'𓄿𓂋𓏏',stage:'Late Egyptian',frequency:50},
 {id:'e3',surface:'𓄿𓊪',stage:'Earlier Egyptian',frequency:90},
]);
test('Pack validates provenance, stable IDs and ordering',()=>{
 assert.equal(assertPack(coptic).entries,4);
 assert.equal(assertPack(egyptian).entries,3);
 assert.throws(()=>assertPack({...egyptian,rows:[...egyptian.rows,egyptian.rows[0]]}),/duplicate|sorted/);
});
test('Raw input comes first and is never silently autocorrected',()=>{
 const o=suggest(egyptian,'𓄿',{limit:4});
 assert.equal(o[0].text,'𓄿');assert.equal(o[0].raw,true);
 assert.ok(o.slice(1).every(x=>x.attested && x.sourceId==='TEST'));
});
test('Egyptian stage filter prevents Earlier Egyptian leakage',()=>{
 const o=suggest(egyptian,'𓄿',{stage:'Late Egyptian'});
 assert.ok(o.slice(1).every(x=>x.stage==='Late Egyptian'));
 assert.ok(o.slice(1).every(x=>x.text!=='𓄿𓊪'));
});
test('Coptic dialect filter does not fabricate cross-dialect equivalence',()=>{
 const o=suggest(coptic,'ⲡⲉ',{dialect:'sahidic'});
 assert.ok(o.slice(1).every(x=>x.dialect==='sahidic'));
});
test('Diacritics fold only for lookup, never rewrite candidate Unicode',()=>{
 const o=suggest(coptic,'ⲡⲉ',{dialect:'sahidic'});
 assert.ok(o.some(x=>x.text==='ⲡⲉ̀ⲣ'));
});
test('Context and local learning reorder only existing attested records',()=>{
 const a=suggest(coptic,'ⲡⲉ',{dialect:'sahidic',previous:'ⲛ'});
 assert.equal(a[1].id,'c3');
 const b=suggest(coptic,'ⲡⲉ',{dialect:'sahidic',learned:{c4:100}});
 assert.equal(b[1].id,'c4');
});
test('The exact raw candidate retains attestation status and identity',()=>{
 const o=suggest(egyptian,'𓄿𓂋',{stage:'Late Egyptian'});
 assert.equal(o[0].raw,true);assert.equal(o[0].attested,true);
 assert.ok(o.slice(1).every(x=>x.text!=='𓄿𓂋'));
});
test('Invalid packs never fallback silently',()=>{
 assert.throws(()=>suggest(null,'𓄿'),/Incompatible/);
 assert.throws(()=>suggest({...egyptian,schema:3},'𓄿'),/Incompatible/);
 assert.deepEqual(suggest(egyptian,''),[]);
});
test('Unattested hand-typed string remains usable as raw only',()=>{
 const o=suggest(egyptian,'𓆓');assert.equal(o.length,1);
 assert.equal(o[0].raw,true);assert.equal(o[0].attested,false);
});
