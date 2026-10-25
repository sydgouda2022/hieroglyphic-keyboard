/** Pure Unicode editing primitives. All offsets are UTF-16 textarea offsets. */
const WORD=/[\u{13000}-\u{13440}\u{13460}-\u{143FF}]+$/u;
export function wordRange(value,caret){
 if(typeof value!=='string'||!Number.isInteger(caret)||caret<0||caret>value.length)throw new RangeError('Invalid text offset');
 const part=value.slice(0,caret), match=part.match(WORD);
 return {raw:match?.[0]||'',start:caret-(match?.[0].length||0),end:caret};
}
export function replaceRange(value,start,end,insert){
 if(typeof value!=='string'||typeof insert!=='string'||!Number.isInteger(start)||!Number.isInteger(end)||start<0||end<start||end>value.length)throw new RangeError('Invalid replacement');
 const next=value.slice(0,start)+insert+value.slice(end), pos=start+insert.length;
 return {value:next,start:pos,end:pos};
}
export function backspaceRange(value,start,end){
 if(start!==end)return {start,end};
 if(start<=0)return {start:0,end:0};
 const left=value.slice(0,start);
 if(typeof Intl!=='undefined'&&Intl.Segmenter){
  let last=0;for(const segment of new Intl.Segmenter('und',{granularity:'grapheme'}).segment(left))last=segment.index;
  return {start:last,end:start};
 }
 const last=[...left].at(-1);
 return {start:start-last.length,end:start};
}
export class History{
 constructor(first){this.steps=[{...first}];this.pos=0;}
 push(snapshot){
  const old=this.steps[this.pos];
  if(snapshot.value===old.value)return;
  this.steps.length=this.pos+1;
  this.steps.push({...snapshot});
  if(this.steps.length>100)this.steps.shift();
  this.pos=this.steps.length-1;
 }
 undo(){if(this.pos===0)return null;return {...this.steps[--this.pos]};}
 redo(){if(this.pos>=this.steps.length-1)return null;return {...this.steps[++this.pos]};}
 get canUndo(){return this.pos>0;}
 get canRedo(){return this.pos<this.steps.length-1;}
}
