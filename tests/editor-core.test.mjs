import test from 'node:test';
import assert from 'node:assert/strict';
import {wordRange,replaceRange,backspaceRange,History} from '../web/editor-core.mjs';
test('Unicode Egyptian token does not split surrogate pairs',()=>{
 const input='hello 𓄿𓈖 𓅓𓐱𓈖';
 assert.deepEqual(wordRange(input,input.length),{raw:'𓅓𓐱𓈖',start:input.lastIndexOf('𓅓'),end:input.length});
 assert.equal(wordRange(input,5).raw,'');
});
test('replace selection at caret and preserve adjacent text',()=>{
 const old='𓄿𓈖';const result=replaceRange(old,2,4,'𓅓');
 assert.equal(result.value,'𓄿𓅓');assert.equal(result.start,4);
});
test('backspace deletes complete supplementary sign',()=>{
 assert.deepEqual(backspaceRange('𓄿𓈖',4,4),{start:2,end:4});
 assert.deepEqual(backspaceRange('𓄿𓈖',0,2),{start:0,end:2});
});
test('undo/redo discards redo after new edit',()=>{
 const history=new History({value:'',start:0,end:0});
 history.push({value:'𓄿',start:2,end:2});history.push({value:'𓄿𓈖',start:4,end:4});
 assert.equal(history.undo().value,'𓄿');
 assert.equal(history.redo().value,'𓄿𓈖');
 history.undo();history.push({value:'𓄿𓂋',start:4,end:4});
 assert.equal(history.redo(),null);
});
