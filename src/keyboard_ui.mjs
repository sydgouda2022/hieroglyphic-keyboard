/**
 * Optional, framework-independent UI.
 *
 * This module is safe to import in Node and never modifies the page on import.
 * Call defineHieroglyphicKeyboardElement() in a browser, then set element.keyboard
 * to the headless engine. All editing is performed by the host application.
 */
export const KEYBOARD_TAG='hieroglyphic-keyboard';

const CSS=`
:host{display:block;color:var(--hiero-ink,#152f44);font-family:var(--hiero-ui-font,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif)}
*{box-sizing:border-box}button,input{font:inherit}button{cursor:pointer;touch-action:manipulation}
button:focus-visible,input:focus-visible{outline:3px solid #bd914e;outline-offset:2px}
.header{display:flex;justify-content:space-between;align-items:start;flex-wrap:wrap;gap:10px;margin-bottom:12px}
h3{font-size:16px;font-weight:700;margin:0}.subtitle{font-size:12px;color:#72818b;margin-top:4px}
.search{width:min(100%,245px);border:1px solid #d9ccb4;border-radius:10px;padding:11px;min-height:44px;background:white;color:inherit}
.tabs{display:flex;gap:7px;margin-bottom:12px;border-bottom:1px solid #e2d9c8;padding-bottom:12px}
.tabs button{flex:1;background:#efe9de;color:#43566b;border:0;border-radius:10px;padding:12px 6px;min-height:44px;font-weight:600;font-size:12px}
.tabs button[aria-selected="true"]{background:var(--hiero-primary,#102b44);color:white}
.signs{display:grid;grid-template-columns:repeat(auto-fill,minmax(64px,1fr));gap:7px;max-height:355px;overflow-y:auto;overscroll-behavior:contain;padding:2px}
.signs button{border:1px solid #e4d9c6;border-radius:10px;background:white;min-height:70px;padding:6px 3px;display:grid;place-items:center;gap:1px}
.signs button:hover{background:#f6efdf;border-color:#b18a43}
.glyph{font-family:var(--hiero-font,"Noto Sans Egyptian Hieroglyphs",serif);font-size:31px;line-height:1.4}
.code{font-size:10px;color:#687888}
.message{font-size:13px;color:#72818b;padding:12px 3px}
.tools{display:flex;flex-wrap:wrap;gap:8px;border-top:1px solid #e2d9c8;margin-top:12px;padding-top:12px}
.tools button{flex:1;min-width:75px;border:1px solid #dfd5c1;border-radius:10px;background:white;color:inherit;padding:11px 6px;min-height:44px}
.suggestions{display:flex;gap:8px;overflow:auto;min-height:55px;margin-bottom:12px;padding-bottom:4px}
.suggestions button{flex:none;display:flex;align-items:center;gap:11px;border:1px solid #d9ccb5;border-radius:10px;background:white;padding:6px 12px;min-height:54px}
.suggestions button.raw{background:#eaf0f3;border-color:#9daeb9}
.suggestions .glyph{font-size:25px}
.suggestions .badge{font-size:10px;color:#71654c}
.label{font-size:12px;font-weight:600;color:#566875;margin:0 0 7px}
.sr-only{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap}
@media(max-width:600px){.search{width:100%}.signs{grid-template-columns:repeat(auto-fill,minmax(56px,1fr));gap:5px}.signs button{min-height:65px}.glyph{font-size:28px}}
`;
export function defineHieroglyphicKeyboardElement(tag=KEYBOARD_TAG){
 if(typeof customElements==='undefined'||typeof HTMLElement==='undefined')
  throw new Error('Keyboard UI requires a browser Custom Elements implementation');
 const existing=customElements.get(tag);
 if(existing)return existing;
 class HieroglyphicKeyboardElement extends HTMLElement{
  constructor(){
   super();
   this._keyboard=null;this._query='';this._group='uni';this._limit=6;
   const root=this.attachShadow({mode:'open'});
   root.innerHTML=`<style>${CSS}</style>
   <div class="label" id="suggest-title">Word suggestions</div>
   <div class="suggestions" id="suggestions" role="listbox" aria-labelledby="suggest-title"></div>
   <div class="header"><div><h3>Signs</h3><div class="subtitle">Select a sign to insert into your document</div></div>
     <input id="search" class="search" type="search" placeholder="G17, M17A, owl…" aria-label="Search Gardiner codes or sign names"></div>
   <div class="tabs" role="tablist" aria-label="Sign classes">
     <button type="button" data-group="uni" role="tab" aria-controls="signs" aria-selected="true">Uniliteral</button>
     <button type="button" data-group="bi" role="tab" aria-controls="signs" aria-selected="false">Biliteral</button>
     <button type="button" data-group="tri" role="tab" aria-controls="signs" aria-selected="false">Triliteral</button></div>
   <div id="signs" class="signs" role="tabpanel" aria-label="Available signs"></div>
   <div class="tools" aria-label="Unicode editing commands">
     <button type="button" data-insert=" " aria-label="Insert space">Space</button>
     <button type="button" data-insert="𓐰" aria-label="Insert vertical joiner">↧ Stack</button>
     <button type="button" data-insert="𓐱" aria-label="Insert horizontal joiner">⇥ Join</button>
     <button type="button" data-delete="1" aria-label="Delete previous grapheme">⌫ Delete</button>
   </div>`;
   root.addEventListener('pointerdown',event=>{
    if(event.target.closest('button'))event.preventDefault();
   });
   root.addEventListener('click',event=>{
    const button=event.target.closest('button');if(!button)return;
    if(button.dataset.group){this._group=button.dataset.group;
     root.querySelectorAll('[data-group]').forEach(b=>b.setAttribute('aria-selected',String(b===button)));
     root.getElementById('search').value='';this._renderSigns();return;}
    if(button.dataset.code){this._emit('hiero-insert',{text:button.dataset.glyph,code:button.dataset.code,kind:'sign'});return;}
    if(Object.hasOwn(button.dataset,'insert')){this._emit('hiero-insert',{text:button.dataset.insert,kind:'control'});return;}
    if(button.dataset.delete){this._emit('hiero-delete',{});return;}
    if(Object.hasOwn(button.dataset,'candidate')){
     const candidates=this._options||[];
     const candidate=candidates[Number(button.dataset.candidate)];
     if(candidate)this._emit('hiero-replace',{text:candidate.text,raw:this._query,candidate:{...candidate}});
    }
   });
   root.getElementById('search').addEventListener('input',()=>this._renderSigns());
  }
  connectedCallback(){this._renderSigns();this._renderSuggestions();}
  get keyboard(){return this._keyboard;}
  set keyboard(value){
   if(value!==null && (!value||typeof value.getSigns!=='function'||typeof value.predict!=='function'))
    throw new TypeError('A Hieroglyphic Keyboard API object is required');
   this._keyboard=value;this._renderSigns();this._renderSuggestions();
  }
  get query(){return this._query;}
  set query(value){
   if(typeof value!=='string')throw new TypeError('Query must be a string');
   this._query=value;this._renderSuggestions();
  }
  get limit(){return this._limit;}
  set limit(value){if(!Number.isInteger(value)||value<1||value>20)throw new RangeError('Invalid suggestion limit');
   this._limit=value;this._renderSuggestions();}
  _emit(name,detail){this.dispatchEvent(new CustomEvent(name,{
   bubbles:true,composed:true,detail:Object.freeze(detail)}));}
  _renderSigns(){
   const root=this.shadowRoot;if(!root)return;
   const grid=root.getElementById('signs');grid.replaceChildren();
   if(!this._keyboard){const note=document.createElement('span');note.className='message';note.textContent='Sign catalog not loaded';grid.append(note);return;}
   const search=root.getElementById('search').value.trim();
   const signs=search?this._keyboard.searchSigns(search,{group:'all',limit:1000}):this._keyboard.getSigns(this._group);
   for(const sign of signs){
    const button=document.createElement('button');button.type='button';
    button.dataset.code=sign.code;button.dataset.glyph=sign.glyph;
    button.setAttribute('aria-label',`Insert ${sign.code}: ${sign.name}`);
    const glyph=document.createElement('span');glyph.className='glyph';glyph.textContent=sign.glyph;
    const label=document.createElement('span');label.className='code';label.textContent=sign.code;
    button.append(glyph,label);grid.append(button);
   }
   if(!signs.length){const note=document.createElement('span');note.className='message';note.textContent='No matching signs';grid.append(note);}
  }
  _renderSuggestions(){
   const box=this.shadowRoot?.getElementById('suggestions');if(!box)return;
   box.replaceChildren();this._options=[];
   if(!this._query||!this._keyboard){const span=document.createElement('span');span.className='message';
    span.textContent='Start typing hieroglyphs for suggestions';box.append(span);return;}
   const options=this._keyboard.predict(this._query,{limit:this._limit});
   this._options=options;
   options.forEach((candidate,i)=>{
    const button=document.createElement('button');button.type='button';button.dataset.candidate=String(i);
    button.setAttribute('role','option');button.setAttribute('aria-selected',String(candidate.raw));
    if(candidate.raw)button.className='raw';
    const glyph=document.createElement('span');glyph.className='glyph';glyph.textContent=candidate.text;
    const tag=document.createElement('span');tag.className='badge';
    tag.textContent=candidate.raw?(candidate.attested?'Typed ✓':'Typed'):
      candidate.source==='RAMSES-CORPUS'?'RTC':candidate.personal?'Personal':'LE';
    button.append(glyph,tag);box.append(button);
   });
  }
 }
 customElements.define(tag,HieroglyphicKeyboardElement);
 return HieroglyphicKeyboardElement;
}
