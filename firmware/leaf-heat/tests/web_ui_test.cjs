const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const source = fs.readFileSync(require('node:path').join(__dirname, '../src/main.cpp'), 'utf8');
const script = source.match(/<script>([\s\S]*?)<\/script>/)[1];
function setup(saved, storageFails=false) {
 const elements = new Map();
 const calls=[]; const store=new Map(saved ? [['leafy.controlKey',saved]] : []);
 const responses=[];
 const context={AbortController,setTimeout,clearTimeout,document:{getElementById(id){if(!elements.has(id))elements.set(id,{value:'',textContent:'',disabled:false,addEventListener(){}});return elements.get(id);}},
  sessionStorage:{getItem(k){if(storageFails)throw Error('blocked');return store.get(k)||null;},setItem(k,v){if(storageFails)throw Error('blocked');store.set(k,v);},removeItem(k){store.delete(k);}},
  setInterval(){},fetch:async(url,options)=>{calls.push({url,options});if(url==='/api/status')return {ok:true,status:200,text:async()=> 'status'};const r=responses.shift();if(r instanceof Error)throw r;if(!r)throw Error('unexpected request');return {...r,text:async()=>r.body};}};
 vm.createContext(context);vm.runInContext(script,context);
 return {context,elements,calls,store,responses};
}
(async()=>{
 let t=setup();t.context.document.getElementById('key').value='example-valid-key';
 t.responses.push({ok:true,status:200,body:'Control key accepted.'});
 await t.context.saveKey();
 assert.equal(t.store.get('leafy.controlKey'),'example-valid-key');
 assert.equal(t.calls.filter(c=>c.url!='/api/status').length,1);
 assert.equal(t.calls.find(c=>c.url==='/api/auth').options.headers['X-Leaf-Key'],'example-valid-key');
 assert(!t.calls.some(c=>c.url==='/api/on'||c.url==='/api/off'));
 console.log('PASS saving validates key without a heater command');
 t=setup('old-key');t.context.document.getElementById('key').value='wrong-key';
 t.responses.push({ok:false,status:401,body:'Control key missing or incorrect.'});await t.context.saveKey();
 assert.equal(t.store.has('leafy.controlKey'),false);assert.match(t.elements.get('keyStatus').textContent,/incorrect/i);
 console.log('PASS rejected key is not saved and stale saved key is removed');
 t=setup('saved-key');assert.equal(t.elements.get('key').value,'saved-key');
 assert.equal(t.calls.filter(c=>c.url!='/api/status').length,0);
 t.context.forgetKey();assert.equal(t.elements.get('key').value,'');assert.equal(t.store.size,0);
 console.log('PASS reload restores key without commands; Forget removes it');
 t=setup();await t.context.command('on');assert(!t.calls.some(c=>c.url==='/api/on'));
 console.log('PASS empty key does not send command');
 t.context.document.getElementById('key').value='wrong-key';
 t.responses.push({ok:false,status:401,body:'Control key missing or incorrect.'});await t.context.command('on');
 assert.match(t.elements.get('result').textContent,/401/);assert.match(t.elements.get('result').textContent,/incorrect/i);
 console.log('PASS HTTP rejection remains visible with status code');
 t=setup();t.context.document.getElementById('key').value='test-key';
 t.responses.push(Error('offline'));await t.context.command('on');
 assert.equal(t.calls.filter(c=>c.url==='/api/on').length,1);assert.match(t.elements.get('result').textContent,/unknown/i);
 console.log('PASS connection failure does not retry a heat command');
 t=setup(null,true);t.context.document.getElementById('key').value='test-key';
 t.responses.push({ok:true,status:200,body:'Control key accepted.'});await t.context.saveKey();
 assert.match(t.elements.get('keyStatus').textContent,/cannot|unavailable/i);
 console.log('PASS unavailable session storage is reported without losing entered key');
})().catch(e=>{console.error(e);process.exitCode=1;});
