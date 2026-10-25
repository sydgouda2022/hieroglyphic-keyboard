import {test} from 'node:test';
import assert from 'node:assert/strict';
import {keyboardKey,prepareKeyboardIndex,predictKeyboard} from '../src/keyboard_search.mjs';

const cop=prepareKeyboardIndex('cop',{rows:[
 ['ⲡⲉ',1],['ⲡⲓ',2],['ⲡⲱ',3],['ⲡⲕ',0],['ⲡⲉ̄',1]],popularity:{'ⲡⲉ':10,'ⲡⲓ':15}});
const egy=prepareKeyboardIndex('egy',{entries:[
 {ref:'TLA:1',signs:'𓄿𓂝',attestations:9,lemma:'1'},
 {ref:'TLA:2',signs:'𓄿𓈖',attestations:5,lemma:'2'},
 {ref:'TLA:3',signs:'𓅓𓈖',attestations:7,lemma:'3'}]});
test('Coptic search keys normalize marks but preserve actual writing',()=>{
 assert.equal(keyboardKey('ⲡⲉ̄','cop'),keyboardKey('ⲡⲉ','cop'));
 const r=predictKeyboard(cop,'ⲡ',{limit:10});
 assert.equal(r[0].text,'ⲡ');
 assert.ok(r.some(x=>x.text==='ⲡⲉ̄'),'Attested combining marks survive insertion');
 assert.ok(r.some(x=>x.text==='ⲡⲕ'&&x.dialects===0),'Undetermined forms appear in All only');
});
test('Sahidic/Bohairic filtering blocks cross-dialect and unknown attributions',()=>{
 const s=predictKeyboard(cop,'ⲡ',{dialect:'sahidic',limit:10});
 assert.ok(s.some(x=>x.text==='ⲡⲉ')&&s.some(x=>x.text==='ⲡⲱ'));
 assert.ok(!s.some(x=>x.text==='ⲡⲓ'||x.text==='ⲡⲕ'));
 const b=predictKeyboard(cop,'ⲡ',{dialect:'bohairic',limit:10});
 assert.ok(b.some(x=>x.text==='ⲡⲓ')&&b.some(x=>x.text==='ⲡⲱ'));
 assert.ok(!b.some(x=>x.text==='ⲡⲉ'||x.text==='ⲡⲕ'));
});
test('raw input is always first and attestation is only true for known input',()=>{
 const r=predictKeyboard(egy,'𓄿𓂝',{limit:5});
 assert.equal(r[0].text,'𓄿𓂝');assert.equal(r[0].attested,true);
 assert.ok(r.every((x,i)=>i===0||x.text!=='𓄿𓂝'));
 const x=predictKeyboard(egy,'𓄿𓅃',{limit:5});
 assert.equal(x[0].attested,false);
});
test('Egyptian suggestions use actual Late Egyptian ref IDs and no transliteration',()=>{
 const r=predictKeyboard(egy,'𓄿',{limit:5});
 assert.equal(r.length,3);
 assert.ok(r.slice(1).every(x=>x.source==='LATE'&&x.lexicon_ref.startsWith('TLA:')));
 assert.equal(predictKeyboard(egy,'nfr').length,1);
});
test('personal learning and document context reorder but never label inventions as attested',()=>{
 const learned={'egy:𓄿𓈖':10,'ctx:egy:𓅓𓈖:𓄿𓈖':4,'egy:𓄿𓅃':20};
 const r=predictKeyboard(egy,'𓄿',{learned,previous:'𓅓𓈖',limit:6});
 assert.equal(r[0].text,'𓄿');
 assert.equal(r[1].text,'𓄿𓈖');
 const user=r.find(x=>x.text==='𓄿𓅃');
 assert.ok(user&&user.personal&&!user.attested&&user.lexicon_ref===null);
});
test('Ramses corpus-derived spellings are visibly distinguished from lemmatized records',()=>{
 const idx=prepareKeyboardIndex('egy',{entries:[
   {ref:'tla19:1',signs:'𓄿𓂝',attestations:4,lemma:'tla19:12',source:'TLA-LE19'},
   {ref:'ramses:2',signs:'𓄿𓈖',attestations:20,lemma:'ramses-unlinked:2',
    source:'RAMSES-WORD-MODEL-2023',lexical_identity_verified:false}
 ]});
 const matches=predictKeyboard(idx,'𓄿',{limit:4});
 const tl=matches.find(x=>x.text==='𓄿𓂝');
 const rm=matches.find(x=>x.text==='𓄿𓈖');
 assert.ok(tl&&tl.source==='LATE'&&tl.lexicalIdentityVerified);
 assert.ok(rm&&rm.source==='RAMSES-CORPUS'&&!rm.lexicalIdentityVerified);
 assert.equal(matches[0].text,'𓄿');
});
test('indexed prefix span works with thousands of attested forms',()=>{
 const rows=Array.from({length:25000},(_,i)=>['ⲡ'+(i+'').padStart(5,'0'),1]);
 rows.push(['ⲁⲛ',1],['ⲁⲩⲱ',2]);
 const idx=prepareKeyboardIndex('cop',{rows});
 const r=predictKeyboard(idx,'ⲁ',{limit:4});
 assert.deepEqual(r.map(x=>x.text),['ⲁ','ⲁⲛ','ⲁⲩⲱ']);
});
