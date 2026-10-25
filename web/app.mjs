/** Standalone demonstration host. All keyboard behavior lives in the reusable library. */
import {createKeyboardFromData,createHieroglyphicKeyboard} from './keyboard_api.mjs';
import {defineHieroglyphicKeyboardElement} from './keyboard_ui.mjs';
import {History,wordRange,replaceRange,backspaceRange} from './editor-core.mjs';

defineHieroglyphicKeyboardElement();
const $=id=>document.getElementById(id);
const STORAGE='hieroglyphic-keyboard.workspace.v1';
const editor=$('editor'),count=$('character-count');
const status=$('storage-state'),lexiconLabel=$('lexicon-label'),ui=$('keyboard-ui');
let installEvent=null,toastTimer=null,saveTimer=null,renderPending=false;
let savedCaret={start:0,end:0};
ui.keyboard=createKeyboardFromData(); // Typing works even if dictionary cannot load.
try{editor.value=localStorage.getItem(STORAGE)||'';}catch{}
const history=new History({value:editor.value,start:editor.value.length,end:editor.value.length});
editor.setSelectionRange(editor.value.length,editor.value.length);
function notice(message){
 const toast=$('toast');toast.textContent=message;toast.hidden=false;
 clearTimeout(toastTimer);toastTimer=setTimeout(()=>toast.hidden=true,2800);
}
function capture(){return {value:editor.value,start:editor.selectionStart,end:editor.selectionEnd};}
function restore(snap){
 editor.value=snap.value;editor.focus({preventScroll:true});
 editor.setSelectionRange(snap.start,snap.end);rememberSelection();
 changed(false);persist();
}
function rememberSelection(){
 if(document.activeElement===editor)savedCaret={start:editor.selectionStart,end:editor.selectionEnd};
}
function persist(){
 clearTimeout(saveTimer);
 try{localStorage.setItem(STORAGE,editor.value);}
 catch{notice('Device storage is unavailable; export your text to keep it.');}
}
function changed(push=true){
 if(push)history.push(capture());
 count.textContent=[...editor.value].length+' characters';
 $('undo').disabled=!history.canUndo;$('redo').disabled=!history.canRedo;
 rememberSelection();
 clearTimeout(saveTimer);saveTimer=setTimeout(persist,500);
 schedulePredictions();
}
function splice(text,start=editor.selectionStart,end=editor.selectionEnd){
 const snapshot=replaceRange(editor.value,start,end,text);
 editor.value=snapshot.value;editor.focus({preventScroll:true});
 editor.setSelectionRange(snapshot.start,snapshot.end);
 changed();persist();
}
function schedulePredictions(){
 if(renderPending)return;
 renderPending=true;
 requestAnimationFrame(()=>{
  renderPending=false;
  const caret=savedCaret.start;
  ui.query=wordRange(editor.value,Math.min(caret,editor.value.length)).raw;
 });
}
function installButton(){
 window.addEventListener('beforeinstallprompt',e=>{e.preventDefault();installEvent=e;$('install').hidden=false;});
 $('install').addEventListener('click',async()=>{
  if(installEvent){const p=installEvent;installEvent=null;$('install').hidden=true;await p.prompt();}
  else notice('On iPhone: Share → Add to Home Screen');
 });
}
async function loadLexicon(){
 status.textContent='Verifying local dictionary…';
 try{
  const keyboard=await createHieroglyphicKeyboard({
   manifestUrl:new URL('./lexicon/manifest.json',import.meta.url),
   lexiconUrl:new URL('./lexicon/lexicon.json',import.meta.url),
   storageNamespace:'standalone-writing-v1',
   online:navigator.onLine!==false
  });
  ui.keyboard=keyboard;
  status.textContent='Dictionary ready'+(keyboard.info.complete?'':' · incomplete');
  lexiconLabel.textContent=keyboard.info.spellingRecords.toLocaleString()+
   ' spelling records · '+keyboard.info.status;
 }catch(error){
  ui.keyboard=createKeyboardFromData();
  status.textContent='Dictionary unavailable';
  lexiconLabel.textContent='Sign keyboard available · ';
  const retry=document.createElement('button');retry.type='button';
  retry.textContent='Retry lexicon';retry.className='soft';
  retry.addEventListener('click',()=>{retry.remove();void loadLexicon();});
  lexiconLabel.append(retry);
  notice('Dictionary unavailable: '+String(error.message||error));
 }
 schedulePredictions();
}
ui.addEventListener('hiero-insert',event=>splice(event.detail.text,savedCaret.start,savedCaret.end));
ui.addEventListener('hiero-delete',()=>{
 const range=backspaceRange(editor.value,savedCaret.start,savedCaret.end);
 splice('',range.start,range.end);
});
ui.addEventListener('hiero-replace',event=>{
 const range=wordRange(editor.value,Math.min(savedCaret.start,editor.value.length));
 if(!range.raw||range.raw!==event.detail.raw){
  notice('Suggestion is stale. Select the word and try again.');return;
 }
 splice(event.detail.text+' ',range.start,range.end);
});
editor.addEventListener('input',()=>changed());
for(const type of ['click','keyup','mouseup','select'])editor.addEventListener(type,()=>{rememberSelection();schedulePredictions();});
editor.addEventListener('keydown',e=>{
 const modifier=e.metaKey||e.ctrlKey;
 if(!modifier)return;
 if(e.key.toLowerCase()==='z'){
  e.preventDefault();
  if(e.shiftKey){const snap=history.redo();if(snap)restore(snap);}
  else {const snap=history.undo();if(snap)restore(snap);}
 }else if(e.key.toLowerCase()==='y'){
  e.preventDefault();const snap=history.redo();if(snap)restore(snap);
 }
});
$('undo').addEventListener('click',()=>{const s=history.undo();if(s){restore(s);persist();}});
$('redo').addEventListener('click',()=>{const s=history.redo();if(s){restore(s);persist();}});
$('select-all').addEventListener('click',()=>{editor.focus({preventScroll:true});editor.select();rememberSelection();});
$('copy').addEventListener('click',async()=>{
 const text=editor.value.slice(editor.selectionStart,editor.selectionEnd)||editor.value;
 if(!text){notice('Nothing to copy');return;}
 try{await navigator.clipboard.writeText(text);notice('Copied to clipboard');}
 catch{editor.focus();editor.select();notice('Copy selected text using your device menu');}
});
$('cut').addEventListener('click',async()=>{
 const s=editor.selectionStart,e=editor.selectionEnd,text=editor.value.slice(s,e);
 if(!text){notice('Select text to cut');return;}
 try{await navigator.clipboard.writeText(text);splice('',s,e);notice('Cut to clipboard');}
 catch{notice('Clipboard blocked — use the system Cut menu');editor.focus();}
});
$('paste').addEventListener('click',async()=>{
 try{const t=await navigator.clipboard.readText();if(t)splice(t,savedCaret.start,savedCaret.end);}
 catch{editor.focus();notice('Use the system Paste menu if clipboard permission is unavailable');}
});
$('export').addEventListener('click',()=>{
 const blob=new Blob([editor.value],{type:'text/plain;charset=utf-8'});
 const url=URL.createObjectURL(blob),link=document.createElement('a');
 link.href=url;link.download='hieroglyphic-writing.txt';link.click();setTimeout(()=>URL.revokeObjectURL(url),1500);
});
$('clear').addEventListener('click',()=>{
 if(editor.value&&!confirm('Clear your saved writing? You can undo this action.'))return;
 editor.value='';editor.focus({preventScroll:true});editor.setSelectionRange(0,0);changed();persist();
});
window.addEventListener('pagehide',persist);
document.addEventListener('visibilitychange',()=>{if(document.hidden)persist();});
if('serviceWorker' in navigator)window.addEventListener('load',()=>{
 navigator.serviceWorker.register('./sw.js').catch(()=>notice('Offline mode could not be registered'));
});
installButton();changed(false);void loadLexicon();
