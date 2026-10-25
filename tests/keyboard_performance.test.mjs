
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {performance} from 'node:perf_hooks';
import {prepareKeyboardIndex,predictKeyboard} from '../src/keyboard_search.mjs';

test('full pinned release indexing and bounded prefix workload',()=>{
 const pack=JSON.parse(readFileSync(new URL('../release/lexicon.json',import.meta.url)));
 const start=performance.now();
 const index=prepareKeyboardIndex('egy',pack);
 const indexMs=performance.now()-start;
 assert.equal(index.rows.length,pack.metadata.spelling_records);
 const short='𓀀';
 const t=performance.now();
 for(let i=0;i<100;i++){
  const candidates=predictKeyboard(index,short,{limit:8});
  assert.ok(candidates.length>0&&candidates.length<=8&&candidates[0].raw);
 }
 const predictMs=performance.now()-t;
 console.log('HEADLESS_FULL_CORPUS_BENCHMARK '+JSON.stringify({
  entries:index.rows.length, indexMs:Math.round(indexMs),
  prefix100Ms:Math.round(predictMs),
  memoryMB:Math.round(process.memoryUsage().heapUsed/1048576)
 }));
 // Conservative performance guard, not a device-specific promise.
 assert.ok(indexMs<15000,'Indexing unexpectedly slow on CI');
 assert.ok(predictMs<15000,'Prefix prediction unexpectedly slow on CI');
});
