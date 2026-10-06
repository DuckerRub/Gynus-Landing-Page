// Exercise the preserved handoffs with deterministic browser APIs; never launch real apps.
const {readFileSync}=require('node:fs');
const {runInNewContext}=require('node:vm');
const {join}=require('node:path');
const assert=require('node:assert/strict');
function run(pathname,userAgent='Desktop',search='',file='404.html',platform='',maxTouchPoints=0) {
 const text=readFileSync(join(__dirname,'..',file),'utf8');
 const source=text.match(/<script>([\s\S]*?)<\/script>/)[1];
 const nodes={};const events={};const timers=new Map();let timerId=0;
 function element(id){return nodes[id]??={style:{},hidden:false,addEventListener:(name,cb)=>events[id+':'+name]=cb};}
 const location={pathname,search,href:'',replace(url){this.href=url;}};
 const document={title:'',documentElement:{lang:''},visibilityState:'visible',getElementById:element,querySelector:element,querySelectorAll:()=>[],addEventListener:(name,cb)=>events[name]=cb};
 const window={location,addEventListener:(name,cb)=>events[name]=cb,dispatchEvent(){}};
 runInNewContext(source,{window,location,navigator:{userAgent,language:'en',platform,maxTouchPoints},document,URLSearchParams,CustomEvent:class{},localStorage:{getItem(){return null;},setItem(){}},setTimeout:(cb,ms)=>{assert.equal(ms,1200);timers.set(++timerId,cb);return timerId;},clearTimeout:id=>timers.delete(id)});
 return {nodes,location,document,timers,click(){events['open-app:click']({preventDefault(){}});},hide(){document.visibilityState='hidden';events.visibilitychange();},pagehide(){events.pagehide();},tick(){for(const cb of [...timers.values()])cb();timers.clear();}};
}
let cases=0;
const devices=[['iPhone','ios'],['iPad','ios'],['Android','android'],['Desktop Safari','ios','MacIntel',5]];
for(const token of ['AbCd123456','A'.repeat(32)])for(const suffix of ['', '/', '///']){
 for(const [ua,os,platform,touch] of devices){
  const path='/join-group/'+token+suffix;const expected='gynus://join-group/'+token;
  const r=run(path,ua,'?source=test','404.html',platform,touch);
  assert.equal(r.location.href,expected);assert.equal(r.nodes['open-app'].href,expected);
  r.tick();assert.equal(r.location.href,os==='ios'?'https://apps.apple.com/app/id6764876378':'https://play.google.com/store/apps/details?id=fit.gynus.app');
  for(const cancel of ['hide','pagehide']){const installed=run(path,ua,'','404.html',platform,touch);installed[cancel]();installed.tick();assert.equal(installed.location.href,expected);cases++;}
  r.click();r.click();assert.equal(r.timers.size,1);cases++;
 }
 const desktop=run('/join-group/'+token+suffix);assert.equal(desktop.location.href,'');assert.equal(desktop.timers.size,0);assert.equal(desktop.nodes['open-app'].href,'gynus://join-group/'+token);desktop.click();assert.equal(desktop.location.href,'gynus://join-group/'+token);cases++;
}
for(const path of ['/missing','/join-group/short','/join-group/'+'A'.repeat(33),'/join-group/ABC_DEF1234','/join-group/ABCDEFGHIJ/extra']){
 const r=run(path,'Android');assert.equal(r.nodes['handoff-title'].textContent,'Page not found');for(const id of ['open-app','store-buttons','status-row'])assert.equal(r.nodes[id].hidden,true);assert.equal(r.timers.size,0);assert.equal(r.location.href,'');cases++;
}
for(const query of ['','?source=chatgpt-plugin','?source=untrusted'])for(const [ua,os,platform,touch] of devices){
 const expected='gynus://import-plan?source='+(query==='?source=chatgpt-plugin'?'chatgpt-plugin':'website');
 const r=run('/import-plan/',ua,query,'import-plan/index.html',platform,touch);assert.equal(r.location.href,expected);r.hide();r.tick();assert.equal(r.location.href,expected);cases++;
}
console.log(`PASS: ${cases} handoff cases including groups, import plans, iPadOS, timer cancellation and desktop retry`);
