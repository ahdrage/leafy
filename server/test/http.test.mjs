import {test} from 'node:test';
import assert from 'node:assert/strict';
import {existsSync} from 'node:fs';
const moduleURL=new URL('../src/http.mjs',import.meta.url);
test('HTTP transport exists',()=>assert.ok(existsSync(moduleURL),'Missing HTTP transport'));
if(existsSync(moduleURL)){
 const {createHTTPServer}=await import(moduleURL);
 test('real HTTP adapter limits JSON bodies and supplies no-store responses',async t=>{
  const seen=[];const server=createHTTPServer({dispatch:async r=>{seen.push(r);return {status:200,body:{ok:true}};}});
  await new Promise(r=>server.listen(0,'127.0.0.1',r));t.after(()=>new Promise(r=>server.close(r)));
  const url='http://127.0.0.1:'+server.address().port;
  const good=await fetch(url+'/v1/status');assert.equal(good.status,200);assert.equal(good.headers.get('cache-control'),'no-store');assert.equal(good.headers.get('access-control-allow-origin'),null);
  assert.equal((await fetch(url+'/v1/heater/commands',{method:'POST',body:'{}'})).status,415);
  assert.equal((await fetch(url+'/v1/heater/commands',{method:'POST',headers:{'Content-Type':'application/json'},body:'x'.repeat(3000)})).status,413);
  assert.equal((await fetch(url+'/v1/heater/commands',{method:'POST',headers:{'Content-Type':'application/json'},body:'{'})).status,400);
  assert.equal(seen.length,1);
 });
}
