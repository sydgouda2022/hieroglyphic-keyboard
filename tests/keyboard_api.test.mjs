import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {webcrypto} from 'node:crypto';
import {API_VERSION,KEYBOARD_GROUPS,createKeyboardFromData,createHieroglyphicKeyboard} from '../src/keyboard_api.mjs';
import {createKeyboardFromData as viaPackage} from '@sydgouda/hieroglyphic-keyboard';
if(!globalThis.crypto)globalThis.crypto=webcrypto;

const catalog={format:'mdwnfr-predict-v1',metadata:{stage:'Late Egyptian',complete:false,spelling_records:3},
 entries:[
 {ref:'tla:1',signs:'𓄿𓂝',source:'TLA-LE19',lemma:'l1',attestations:4},
 {ref:'tla:2',signs:'𓄿𓈖',source:'TLA-LE19',lemma:'l2',attestations:3},
 {ref:'r:1',signs:'𓄿𓅓',source:'RAMSES-WORD-MODEL-2023',lexical_identity_verified:false,attestations:40}
]};
test('self-referenced npm package import resolves public headless API',()=>{
 assert.equal(viaPackage,createKeyboardFromData);
 assert.equal(API_VERSION,'1.0.0');
 assert.deepEqual(KEYBOARD_GROUPS,['uni','bi','tri']);
});
test('sign catalog is deterministic, independently usable, immutable',()=>{
 const a=createKeyboardFromData();const b=createKeyboardFromData();
 assert.equal(a.info.status,'signs-only');
 assert.equal(a.getSigns('uni').length,27);
 assert.equal(a.getSigns('uniliteral').length,27);
 assert.equal(a.getSigns('bi').length,151);
 assert.equal(a.getSigns('tri').length,89);
 assert.equal(a.getSigns('all').length,267);
 assert.equal(a.searchSigns('m17a')[0].glyph,'𓇌');
 assert.ok(a.searchSigns('owl').some(x=>x.code==='G17'));
 assert.ok(a.searchSigns('m17a',{group:'tri'}).length===0);
 assert.throws(()=>a.getSigns('cop'),RangeError);
 assert.throws(()=>a.searchSigns('',{limit:-1}),RangeError);
 assert.throws(()=>{a.getSigns()[0].code='OTHER';},TypeError);
 assert.equal(b.getSigns('uni')[0].code,a.getSigns('uni')[0].code);
 assert.equal(a.predict('𓄿')[0].raw,true);
 assert.deepEqual(a.predict(''),[]);
});
test('pure core is independent of DOM, browser storage and network',()=>{
 const api=createKeyboardFromData({lexicon:catalog});
 assert.equal(api.info.spellingRecords,3);
 assert.equal(api.info.complete,false);
 assert.equal(api.validate('𓄿𓈖'),true);
 assert.equal(api.validate('English'),false);
 assert.equal(api.predict('𓄿',{limit:4}).length,4);
 const model=api.predict('𓄿',{limit:4}).find(x=>x.text==='𓄿𓅓');
 assert.equal(model.source,'RAMSES-CORPUS');
 assert.equal(model.lexicalIdentityVerified,false);
 assert.throws(()=>api.predict(12),TypeError);
});
const manifest=JSON.parse(readFileSync(new URL('../release/manifest.json',import.meta.url)));
const binary=readFileSync(new URL('../release/lexicon.json',import.meta.url));
const bytes=binary.buffer.slice(binary.byteOffset,binary.byteOffset+binary.byteLength);
function store(){
 return {slot:null,
  async read(){return {active:this.slot,previous:null};},
  async activate(next){this.slot=next;},
  async restore(valid){this.slot=valid;}
 };
}
test('two consuming applications have isolated store and configurable URL requests',async()=>{
 const visited=[];
 const mock=async url=>{
  visited.push(String(url));
  if(String(url).includes('manifest.json'))return {ok:true,json:async()=>manifest};
  if(String(url).includes('lexicon.json'))return {ok:true,arrayBuffer:async()=>bytes};
  throw Error('Unexpected URL');
 };
 const a=await createHieroglyphicKeyboard({
  manifestUrl:'https://app-a.example/keyboard/manifest.json',
  lexiconUrl:'https://app-a.example/keyboard/lexicon.json',
  storageNamespace:'renpet',store:store(),fetcher:mock
 });
 const b=await createHieroglyphicKeyboard({
  manifestUrl:'https://app-b.example/keyboard/manifest.json',
  lexiconUrl:'https://app-b.example/keyboard/lexicon.json',
  storageNamespace:'mdwnfr',store:store(),fetcher:mock
 });
 assert.equal(a.info.spellingRecords,41330);
 assert.equal(b.info.spellingRecords,41330);
 assert.equal(a.info.sha256,manifest.sha256);
 assert.deepEqual(visited.slice(0,2),[
  'https://app-a.example/keyboard/manifest.json',
  'https://app-a.example/keyboard/lexicon.json'
 ]);
 assert.deepEqual(visited.slice(2,4),[
  'https://app-b.example/keyboard/manifest.json',
  'https://app-b.example/keyboard/lexicon.json'
 ]);
});
test('URL and namespace requirements prevent accidental ambient installs',async()=>{
 await assert.rejects(createHieroglyphicKeyboard(),/Explicit manifestUrl/);
 await assert.rejects(createHieroglyphicKeyboard({manifestUrl:'a',lexiconUrl:'b',storageNamespace:''}),/namespace/);
});
test('offline verified storage works without network',async()=>{
 const storage=store();storage.slot={manifest,bytes};
 const a=await createHieroglyphicKeyboard({
  manifestUrl:'https://example.com/manifest.json',lexiconUrl:'https://example.com/lexicon.json',
  store:storage,online:false,fetcher:()=>{throw Error('Offline');}
 });
 assert.equal(a.info.spellingRecords,41330);
});
