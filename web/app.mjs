import {prepareKeyboardIndex,predictKeyboard} from './keyboard_search.mjs';
import {ensureLexicon} from './lexicon_install.mjs';
import {History,wordRange,replaceRange,backspaceRange} from './editor-core.mjs';

const $=id=>document.getElementById(id);
const STORAGE='hieroglyphic-keyboard.workspace.v1';
const CURRENT='hieroglyphic-keyboard.v1';
const editor=$('editor'),count=$('character-count'),suggestions=$('suggestions'),status=$('storage-state'),lexiconLabel=$('lexicon-label');
const grid=$('sign-grid'),search=$('sign-search');
let pages=null,tab='uni',index=null,ready=false,installEvent=null,toastTimer=null;
let lastSave=0,saveTimer=null,renderPending=false;
let savedCaret={start:0,end:0};
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
 editor.dispatchEvent(new Event('input',{bubbles:true,detail:0}));
}
function rememberSelection(){
 if(document.activeElement===editor)savedCaret={start:editor.selectionStart,end:editor.selectionEnd};
}
function persist(){
 clearTimeout(saveTimer);lastSave=Date.now();
 try{localStorage.setItem(STORAGE,editor.value);}
 catch{notice('Device storage is unavailable; export your text to keep it.');}
}
function changed(push=true){
 if(push)history.push(capture());
 count.textContent=[...editor.value].length+' characters';
 $('undo').disabled=!history.canUndo;$('redo').disabled=!history.canRedo;
 rememberSelection();
 if(Date.now()-lastSave>700)saveTimer=setTimeout(persist,500);
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
 renderPending=true;requestAnimationFrame(()=>{renderPending=false;drawSuggestions();});
}
function selectedWord(){return wordRange(editor.value,editor.selectionStart);}
function drawSuggestions(){
 suggestions.replaceChildren();
 const {raw}=selectedWord();
 if(!raw){const label=document.createElement('span');label.className='hint';label.textContent='Start typing a word to see suggestions.';suggestions.append(label);return;}
 const options=index?predictKeyboard(index,raw,{limit:6}):[{text:raw,raw:true,attested:false}];
 for(const candidate of options){
  const button=document.createElement('button');button.type='button';
  if(candidate.raw)button.className='is-raw';
  button.setAttribute('role','option');button.setAttribute('aria-selected',candidate.raw?'true':'false');
  const glyph=document.createElement('span');glyph.className='glyph';glyph.textContent=candidate.text;
  const label=document.createElement('small');
  label.textContent=candidate.raw?(candidate.attested?'Typed ✓':'Typed'):candidate.source==='RAMSES-CORPUS'?'RTC':'LE';
  button.append(glyph,label);
  button.addEventListener('pointerdown',e=>e.preventDefault());
  button.addEventListener('click',()=>{
    const r=selectedWord();
    if(!r.raw)return;
    splice(candidate.text+' ',r.start,r.end);
  });
  suggestions.append(button);
 }
}
function makeSign(glyph,code){
 const button=document.createElement('button');button.type='button';
 button.title=code;button.setAttribute('aria-label','Insert '+code);
 const symbol=document.createElement('span');symbol.className='glyph';symbol.textContent=glyph;
 const label=document.createElement('small');label.textContent=code;
 button.append(symbol,label);
 button.addEventListener('pointerdown',e=>e.preventDefault());
 button.addEventListener('click',()=>splice(glyph,savedCaret.start,savedCaret.end));
 return button;
}
function drawGrid(){
 grid.replaceChildren();
 if(!pages){
  const retry=document.createElement('button');retry.textContent='Sign list unavailable — retry';retry.addEventListener('click',loadSigns);grid.append(retry);return;
 }
 const term=search.value.trim().toUpperCase();
 const all=term?Object.values(pages).flat():pages[tab];
 const matches=all.filter(([,code])=>code.toUpperCase().includes(term));
 // Search across all phonogram groups; deduplicate by glyph/code.
 const seen=new Set();
 for(const [glyph,code] of matches){
  const key=glyph+'|'+code;if(seen.has(key))continue;seen.add(key);grid.append(makeSign(glyph,code));
 }
 if(!matches.length){const label=document.createElement('span');label.className='hint';label.textContent='No matching Gardiner codes';grid.append(label);}
}
async function loadSigns(){
 try{
  const response=await fetch('./signs.json');
  if(!response.ok)throw Error('HTTP '+response.status);
  const obj=await response.json();
  if(obj?.schema!==1||!obj.pages||!['uni','bi','tri'].every(p=>Array.isArray(obj.pages[p])))throw Error('Malformed signs catalog');
  for(const group of Object.values(obj.pages))for(const row of group)
   if(!Array.isArray(row)||row.length!==2||typeof row[0]!=='string'||typeof row[1]!=='string')throw Error('Malformed sign');
  pages=obj.pages;
 }catch(e){pages=null;notice('Sign catalog unavailable: '+e.message);}
 drawGrid();
}
function installButton(){
 window.addEventListener('beforeinstallprompt',e=>{e.preventDefault();installEvent=e;$('install').hidden=false;});
 $('install').addEventListener('click',async()=>{
  if(installEvent){const p=installEvent;installEvent=null;$('install').hidden=true;await p.prompt();}
  else notice('On iPhone: Share → Add to Home Screen');
 });
}
async function loadLexicon(){
 status.textContent='Verifying dictionary…';
 try{
  const installed=await ensureLexicon();
  index=prepareKeyboardIndex('egy',installed.payload);
  ready=true;
  status.textContent='Dictionary ready'+(installed.complete?'':' · incomplete');
  lexiconLabel.textContent=index.rows.length.toLocaleString()+' spelling records · '+installed.status;
 }catch(error){
  ready=false;index=null;status.textContent='Dictionary unavailable';
  lexiconLabel.textContent='Raw writing still works · retry below';
  notice('Dictionary unavailable: '+String(error.message||error));
  const retry=document.createElement('button');retry.type='button';retry.textContent='Retry lexicon';retry.className='soft';
  retry.addEventListener('click',()=>{retry.remove();void loadLexicon();});
  lexiconLabel.append(' ',retry);
 }
 schedulePredictions();
}
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
$('backspace').addEventListener('pointerdown',e=>e.preventDefault());
$('backspace').addEventListener('click',()=>{const r=backspaceRange(editor.value,savedCaret.start,savedCaret.end);splice('',r.start,r.end);});
document.querySelectorAll('[data-insert]').forEach(button=>{
 button.addEventListener('pointerdown',e=>e.preventDefault());
 button.addEventListener('click',()=>splice(button.dataset.insert,savedCaret.start,savedCaret.end));
});
document.querySelectorAll('[data-tab]').forEach(button=>button.addEventListener('click',()=>{
 tab=button.dataset.tab;search.value='';
 document.querySelectorAll('[data-tab]').forEach(b=>b.setAttribute('aria-selected',String(b===button)));
 grid.setAttribute('aria-labelledby',button.id);drawGrid();
}));
search.addEventListener('input',drawGrid);
window.addEventListener('pagehide',persist);
window.addEventListener('visibilitychange',()=>{if(document.hidden)persist();});
if('serviceWorker' in navigator)window.addEventListener('load',()=>{
 navigator.serviceWorker.register('./sw.js').catch(()=>notice('Offline mode could not be registered'));
});
installButton();changed(false);void loadSigns();void loadLexicon();
