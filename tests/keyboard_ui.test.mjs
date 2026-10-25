import test from 'node:test';
import assert from 'node:assert/strict';
import {createKeyboardFromData} from '../src/keyboard_api.mjs';
import {KEYBOARD_TAG,defineHieroglyphicKeyboardElement} from '../src/keyboard_ui.mjs';
test('UI module is inert in a server-side / Node runtime',()=>{
 assert.equal(KEYBOARD_TAG,'hieroglyphic-keyboard');
 assert.throws(()=>defineHieroglyphicKeyboardElement(),/browser Custom Elements/);
});
class FakeElement{
 constructor(tag='div'){this.tag=tag;this.children=[];this.dataset={};this.attributes={};this.value='';this.listeners={};this.textContent='';}
 append(...kids){this.children.push(...kids);}
 replaceChildren(...kids){this.children=[...kids];}
 setAttribute(k,v){this.attributes[k]=v;}
 getAttribute(k){return this.attributes[k]||null;}
 addEventListener(type,callback){this.listeners[type]=callback;}
 closest(){return this;}
}
class FakeRoot extends FakeElement{
 constructor(){super('shadow');this.nodes=new Map();}
 getElementById(id){if(!this.nodes.has(id))this.nodes.set(id,new FakeElement(id));return this.nodes.get(id);}
 querySelectorAll(){return [];}
 dispatch(type,target){this.listeners[type]?.({target,preventDefault(){}});}
}
class FakeHTMLElement{
 constructor(){this.events=[];this.shadowRoot=null;}
 attachShadow(){this.shadowRoot=new FakeRoot();return this.shadowRoot;}
 dispatchEvent(e){this.events.push(e);return true;}
}
class FakeCustomEvent{constructor(type,opts){this.type=type;Object.assign(this,opts);}}
test('embeddable component emits host events; does not edit a textarea',()=>{
 globalThis.HTMLElement=FakeHTMLElement;
 const elements=new Map();
 globalThis.customElements={get:key=>elements.get(key),define:(key,value)=>elements.set(key,value)};
 globalThis.document={createElement:tag=>new FakeElement(tag)};
 globalThis.CustomEvent=FakeCustomEvent;
 try{
  const Component=defineHieroglyphicKeyboardElement();
  assert.equal(defineHieroglyphicKeyboardElement(),Component);
  const c=new Component();
  c.connectedCallback();
  c.keyboard=createKeyboardFromData({
   lexicon:{entries:[{ref:'l1',signs:'𓄿𓂝',source:'TLA-LE19',attestations:3}]}
  });
  const root=c.shadowRoot;
  const signs=root.getElementById('signs').children;
  assert.equal(signs.length,27);
  root.dispatch('click',signs[0]);
  assert.equal(c.events.at(-1).type,'hiero-insert');
  assert.equal(c.events.at(-1).detail.text,signs[0].dataset.glyph);
  assert.equal(c.events.at(-1).composed,true);
  c.query='𓄿';
  const suggestions=root.getElementById('suggestions').children;
  assert.equal(suggestions.length,2);
  root.dispatch('click',suggestions[1]);
  assert.equal(c.events.at(-1).type,'hiero-replace');
  assert.equal(c.events.at(-1).detail.raw,'𓄿');
  const deleteButton=new FakeElement('button');deleteButton.dataset.delete='1';
  root.dispatch('click',deleteButton);
  assert.equal(c.events.at(-1).type,'hiero-delete');
  assert.equal(typeof c.query,'string');
  assert.throws(()=>{c.limit=0;},RangeError);
  assert.throws(()=>{c.keyboard={};},TypeError);
 }finally{
  delete globalThis.HTMLElement;delete globalThis.customElements;delete globalThis.document;delete globalThis.CustomEvent;
 }
});
