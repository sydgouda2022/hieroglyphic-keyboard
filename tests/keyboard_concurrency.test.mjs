
import test from 'node:test';
import assert from 'node:assert/strict';
import {createHieroglyphicKeyboard} from '../src/keyboard_api.mjs';

async function observeOpens(settings){
 const previous=globalThis.indexedDB, names=[];
 globalThis.indexedDB={open(name){names.push(name);throw new Error('Stopped before actual DB access');}};
 try{
  const result=await Promise.allSettled(settings.map(s=>createHieroglyphicKeyboard({
   manifestUrl:'https://example.test/lexicon/manifest.json',
   lexiconUrl:'https://example.test/lexicon/lexicon.json',
   storageNamespace:'shared', ...s
  })));
  assert.ok(result.every(x=>x.status==='rejected'));
  return names;
 }finally{
  if(previous===undefined)delete globalThis.indexedDB;
  else globalThis.indexedDB=previous;
 }
}
test('same default versioned install is coalesced',async()=>{
 const names=await observeOpens([{},{}]);
 assert.equal(names.length,1);
});
test('different injected fetchers do not share an in-flight dictionary result',async()=>{
 const names=await observeOpens([{fetcher:async()=>{}},{fetcher:async()=>{}}]);
 assert.equal(names.length,2);
});
test('different SHA-256 pins get separate local stores even for the same app',async()=>{
 const names=await observeOpens([{expectedSha256:'a'.repeat(64)},
  {expectedSha256:'b'.repeat(64)}]);
 assert.equal(names.length,2);
 assert.notEqual(names[0],names[1]);
 assert.ok(names.every(x=>x.startsWith('hieroglyphic-keyboard-v2:shared:')));
});
