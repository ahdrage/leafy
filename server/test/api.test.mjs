import {test} from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync, existsSync, rmSync, writeFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {randomUUID} from 'node:crypto';

const implementation = new URL('../src/app.mjs', import.meta.url);
test('authenticated API is implemented', () => assert.ok(existsSync(implementation), 'Missing Leafy server implementation'));
if (existsSync(implementation)) {
 const {createApp}=await import(implementation);
 const token='test-app-token-which-is-long-enough';
 const legacy='CAN controls: enabled\nProtected supply: 12.18 V (after input diode)\nRequest sequence: idle\nLocal heat request / timer: none\nLast command error: 0\nActual heater state: unverified';
 function fixture(t, responder) {
  const dir=mkdtempSync(join(tmpdir(),'leafy-api-test-'));t.after(()=>rmSync(dir,{recursive:true,force:true}));
  const calls=[];let now=Date.parse('2026-11-16T12:00:00Z');
  const options={token,deviceKey:'test-device-secret',deviceURL:'http://192.168.1.42',statePath:join(dir,'commands.json'),now:()=>now,
   fetchImpl:async(url,options)=>{calls.push({url:String(url),options});return responder?responder(url,options):new Response('Request submitted',{status:202});}};
  const app=createApp(options);
  const request=(method,path,body,headers={})=>app.dispatch({method,path,body,headers:{authorization:'Bearer '+token,...headers}});
  const command=(action='on',id=randomUUID())=>request('POST','/v1/heater/commands',{action,issuedAt:new Date(now).toISOString()},{'idempotency-key':id});
  return {app,options,calls,request,command,advance:ms=>now+=ms};
 }
 test('unauthenticated reads and writes never contact the board',async t=>{
  const f=fixture(t);for(const [method,path] of [['GET','/v1/status'],['POST','/v1/heater/commands']])assert.equal((await f.app.dispatch({method,path,headers:{},body:{}})).status,401);
  assert.equal(f.calls.length,0);
 });
 test('legacy firmware exposes protected voltage and unavailable traction SOC',async t=>{
  const f=fixture(t,url=>new Response(String(url).endsWith('/api/v1/status')?'missing':legacy,{status:String(url).endsWith('/api/v1/status')?404:200}));
  const r=await f.request('GET','/v1/status');assert.equal(r.status,200);assert.equal(r.body.protectedSupplyVolts,12.18);assert.equal(r.body.tractionBattery.socPercent,null);assert.equal(r.body.tractionBattery.availability,'unsupported');assert.equal(r.body.heater.actualState,'unknown');
 });
 test('JSON telemetry reports freshness without claiming dashboard SOC',async t=>{
  const f=fixture(t,()=>Response.json({schemaVersion:1,uptimeMs:1234,canWriteEnabled:true,protectedSupplyMv:12180,requestBusy:false,heatRequested:false,lastCommandError:0,socTenths:534,socAgeMs:5000,telemetryEnabled:true}));
  const r=await f.request('GET','/v1/status');assert.equal(r.body.tractionBattery.socPercent,53.4);assert.equal(r.body.tractionBattery.availability,'fresh');assert.equal(r.body.tractionBattery.source,'ev_can_0x55b_bms');assert.equal(r.body.heater.actualState,'unknown');
 });
 test('stale or absent battery data is labelled, never converted to zero',async t=>{
  let socTenths=510,socAgeMs=180000;
  const f=fixture(t,()=>Response.json({schemaVersion:1,uptimeMs:200000,canWriteEnabled:true,protectedSupplyMv:12000,requestBusy:false,heatRequested:true,lastCommandError:0,socTenths,socAgeMs,telemetryEnabled:true}));
  assert.equal((await f.request('GET','/v1/status')).body.tractionBattery.availability,'stale');
  socTenths=null;socAgeMs=null;const r=await f.request('GET','/v1/status');assert.equal(r.body.tractionBattery.socPercent,null);assert.equal(r.body.tractionBattery.availability,'unavailable');
 });
 test('accepted means board accepted, not heater running; duplicate is never forwarded',async t=>{
  const f=fixture(t);const id=randomUUID();const a=await f.command('on',id);assert.equal(a.status,202);assert.equal(a.body.outcome,'accepted');assert.equal(a.body.actualHeaterState,'unknown');
  const b=await f.command('on',id);assert.deepEqual(b,a);assert.equal(f.calls.length,1);assert.equal(f.calls[0].options.headers['X-Leaf-Key'],'test-device-secret');assert.ok(f.calls[0].url.endsWith('/api/on'));
 });
 test('an idempotency key cannot change action',async t=>{const f=fixture(t);const id=randomUUID();await f.command('on',id);assert.equal((await f.command('off',id)).status,409);assert.equal(f.calls.length,1);});
 test('expired or future commands and invalid inputs never reach vehicle',async t=>{
  const f=fixture(t);for(const body of [{action:'unlock',issuedAt:'2026-11-16T12:00:00Z'},{action:'on',issuedAt:'2026-11-16T11:59:00Z'},{action:'on',issuedAt:'2026-11-16T12:01:00Z'},{action:'on'},{action:'on',issuedAt:'2026-11-16T12:00:00Z',url:'http://evil'}]){
   const r=await f.request('POST','/v1/heater/commands',body,{'idempotency-key':randomUUID()});assert.equal(r.status,400);
  }assert.equal(f.calls.length,0);
 });
 test('missing idempotency key is rejected',async t=>{const f=fixture(t);assert.equal((await f.request('POST','/v1/heater/commands',{action:'on',issuedAt:'2026-11-16T12:00:00Z'})).status,400);});
 test('uncertain network outcome is persisted and never retried, including restart',async t=>{
  const f=fixture(t,()=>{throw Error('private diagnostic secret');});const id=randomUUID();const r=await f.command('on',id);assert.equal(r.status,502);assert.equal(r.body.outcome,'unknown');assert.ok(!JSON.stringify(r).includes('private diagnostic'));
  const restarted=createApp(f.options);const again=await restarted.dispatch({method:'POST',path:'/v1/heater/commands',headers:{authorization:'Bearer '+token,'idempotency-key':id},body:{action:'on',issuedAt:'2026-11-16T12:00:00Z'}});assert.deepEqual(again,r);assert.equal(f.calls.length,1);
 });
 test('Off can proceed immediately after On; rapid new On is limited',async t=>{
  const f=fixture(t);await f.command();assert.equal((await f.command()).status,429);assert.equal((await f.command('off')).status,202);assert.equal(f.calls.length,2);
 });
 test('board rejection stays rejected, not accepted',async t=>{const f=fixture(t,()=>new Response('Low voltage',{status:409}));const r=await f.command();assert.equal(r.status,409);assert.equal(r.body.outcome,'rejected');});
 test('device errors and malformed telemetry never return fabricated status',async t=>{
  const f=fixture(t,()=>new Response('nonsense',{status:200}));assert.equal((await f.request('GET','/v1/status')).status,502);
 });
 test('offline status is explicit and does not serve stale cached success',async t=>{
  const f=fixture(t,()=>{throw Error('offline');});const r=await f.request('GET','/v1/status');assert.equal(r.status,503);assert.equal(r.body.deviceReachable,false);
 });
 test('command result can be retrieved without resending',async t=>{const f=fixture(t);const id=randomUUID();const sent=await f.command('off',id);const got=await f.request('GET','/v1/commands/'+id);assert.deepEqual(got.body,sent.body);assert.equal(f.calls.length,1);});
 test('bad configuration fails closed',()=>{
  assert.throws(()=>createApp({token:'short',deviceKey:'long-enough-secret',deviceURL:'http://127.0.0.1',statePath:'/tmp/unused'}));
 });
 test('duplicate arriving during delivery does not start another network request',async t=>{
  let finish;const f=fixture(t,()=>new Promise(resolve=>finish=resolve));const id=randomUUID();
  const first=f.command('on',id);const duplicate=await f.command('on',id);
  assert.equal(duplicate.body.outcome,'pending');assert.equal(f.calls.length,1);
  finish(new Response('accepted',{status:202}));assert.equal((await first).body.outcome,'accepted');
 });
 test('pending command from a stopped process is unknown and never replayed',async t=>{
  const f=fixture(t);const id=randomUUID();
  writeFileSync(f.options.statePath,JSON.stringify({[id]:{status:202,body:{commandId:id,action:'on',outcome:'pending'}}}));
  const restarted=createApp(f.options);
  const r=await restarted.dispatch({method:'POST',path:'/v1/heater/commands',headers:{authorization:'Bearer '+token,'idempotency-key':id},body:{action:'on'}});
  assert.equal(r.body.outcome,'unknown');assert.equal(f.calls.length,0);
 });

 test('UUID letter casing cannot bypass duplicate protection',async t=>{
  const f=fixture(t);const id=randomUUID();const a=await f.command('on',id);f.advance(4000);
  assert.deepEqual(await f.command('on',id.toUpperCase()),a);assert.equal(f.calls.length,1);
  assert.equal((await f.request('GET','/v1/commands/'+id.toUpperCase())).status,200);
 });
 test('a different command cannot overtake an in-flight delivery',async t=>{
  let finish;const f=fixture(t,()=>new Promise(resolve=>finish=resolve));
  const first=f.command('on');const other=await f.command('off');
  assert.equal(other.status,409);assert.equal(other.body.error,'delivery_busy');assert.equal(f.calls.length,1);
  finish(new Response('accepted',{status:202}));await first;
 });

}
