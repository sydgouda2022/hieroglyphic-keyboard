import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {webcrypto} from 'node:crypto';
import {ensureLexiconImpl, validateManifest,validateCatalog,validateSlot} from '../src/lexicon_install.mjs';
if (!globalThis.crypto)globalThis.crypto=webcrypto;
const base=new URL('../releases/dev-late-egyptian/', import.meta.url);
const content=readFileSync(new URL('lexicon.json',base));
const manifest=JSON.parse(readFileSync(new URL('manifest.json',base)));
const raw=content.buffer.slice(content.byteOffset,content.byteOffset+content.byteLength);
const example={manifest,bytes:raw};
function store(active=null,previous=null){return {
  state:{active,previous},
  async read(){return {...this.state}},
  async activate(next,prior){this.state={active:structuredClone(next),previous:prior&&structuredClone(prior)}},
  async restore(prior){this.state={active:structuredClone(prior),previous:null}}
};}
function fetcher({manifestValue=manifest,body=raw,failManifest=false,failPayload=false}={}){
 return async url=>{
  if(url.includes('manifest')){if(failManifest)throw Error('offline');return {ok:true,json:async()=>manifestValue}};
  if(failPayload)throw Error('offline download');return {ok:true,arrayBuffer:async()=>body};
 };
}
test('valid catalog and manifest; real development subset never claims completeness',async()=>{
 assert.equal(validateManifest(manifest).spelling_records,728);
 assert.equal(validateCatalog(JSON.parse(content.toString())).metadata.complete,false);
 assert.equal((await validateSlot(example)).payload.entries.length,728);
});
test('no existing database installs once and verifies',async()=>{
 const s=store();const a=await ensureLexiconImpl({store:s,fetcher:fetcher()});
 assert.equal(a.payload.entries.length,728);assert.equal(a.complete,false);
 assert.equal(s.state.active.manifest.sha256,manifest.sha256);
});
test('existing good database starts completely offline',async()=>{
 const s=store(example);const a=await ensureLexiconImpl({store:s,online:false,fetcher:()=>{throw Error('network forbidden')}});
 assert.equal(a.manifest.sha256,manifest.sha256);
});
test('corrupt active is repaired from remote and persisted',async()=>{
 const bytes=raw.slice(0);new Uint8Array(bytes)[2]^=3;
 const s=store({...example,bytes});const a=await ensureLexiconImpl({store:s,fetcher:fetcher()});
 assert.equal(a.manifest.sha256,manifest.sha256);
 assert.ok(await validateSlot(s.state.active));
});
test('corrupt active restores previously verified snapshot offline',async()=>{
 const bytes=raw.slice(0);new Uint8Array(bytes)[3]^=8;
 const s=store({...example,bytes},example);
 const a=await ensureLexiconImpl({store:s,online:false});assert.equal(a.status,'recovered');
 assert.equal(s.state.previous,null);assert.ok(await validateSlot(s.state.active));
});
test('failed update preserves last verified release',async()=>{
 const s=store(example);const changed={...manifest,sha256:'f'.repeat(64),release:'new-release'};
 const a=await ensureLexiconImpl({store:s,fetcher:fetcher({manifestValue:changed,failPayload:true})});
 assert.equal(a.manifest.sha256,manifest.sha256);
 assert.equal(s.state.active.manifest.sha256,manifest.sha256);
});
test('missing offline database repairs from offline PWA precache',async()=>{
 const s=store();const a=await ensureLexiconImpl({store:s,online:false,fetcher:fetcher()});
 assert.equal(a.manifest.sha256,manifest.sha256);assert.ok(await validateSlot(s.state.active));
});
test('missing database without cached assets reports install required',async()=>{
 await assert.rejects(ensureLexiconImpl({store:store(),online:false,fetcher:fetcher({failManifest:true})}),/no verified local copy/);
});
test('fake poisoned manifest cannot damage working installation',async()=>{
 const s=store(example);const a=await ensureLexiconImpl({store:s,fetcher:fetcher({manifestValue:{...manifest,complete:'yes'}})});
 assert.equal(a.manifest.sha256,manifest.sha256);
});
test('never accept partial or tampered downloads',async()=>{
 const truncated=raw.slice(0,raw.byteLength-3);
 await assert.rejects(ensureLexiconImpl({store:store(),fetcher:fetcher({body:truncated})}),/checksum mismatch/);
});