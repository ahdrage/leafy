import {test} from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import {randomUUID} from 'node:crypto';
import {mkdtempSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {createApp} from '../src/app.mjs';
import {createHTTPServer} from '../src/http.mjs';
const token='integration-test-app-token-long-enough';
async function listen(t,server){
 await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve);});
 t.after(()=>new Promise(resolve=>{server.close(resolve);server.closeAllConnections();}));
 return 'http://127.0.0.1:'+server.address().port;
}
test('real HTTP chain: authenticated status, commands, deduplication and no redirects',async t=>{
 const dir=mkdtempSync(join(tmpdir(),'leafy-integration-'));t.after(()=>rmSync(dir,{recursive:true,force:true}));
 let commands=0,redirect=false,stolen=0;
 const other=await listen(t,http.createServer((req,res)=>{stolen++;res.end('unexpected');}));
 const device=await listen(t,http.createServer((req,res)=>{
  assert.equal(req.headers['x-leaf-key'],'integration-device-key');
  if(redirect){res.writeHead(302,{Location:other});res.end();return;}
  if(req.url==='/api/v1/status'){
   res.setHeader('Content-Type','application/json');res.end(JSON.stringify({schemaVersion:1,canWriteEnabled:true,requestBusy:false,heatRequested:false,lastCommandError:0,protectedSupplyMv:12500,socTenths:750,socAgeMs:200,telemetryEnabled:true}));
  }else if(req.method==='POST'&&req.url==='/api/off'){commands++;res.writeHead(202);res.end('submitted');}
  else{res.writeHead(404);res.end();}
 }));
 const app=createApp({token,deviceKey:'integration-device-key',deviceURL:device,statePath:join(dir,'commands.json')});
 const url=await listen(t,createHTTPServer(app));const headers={Authorization:'Bearer '+token};
 assert.equal((await fetch(url+'/v1/status')).status,401);
 const status=await (await fetch(url+'/v1/status',{headers})).json();assert.equal(status.tractionBattery.socPercent,75);assert.equal(status.heater.actualState,'unknown');
 const id=randomUUID();const options={method:'POST',headers:{...headers,'Content-Type':'application/json','Idempotency-Key':id},body:JSON.stringify({action:'off',issuedAt:new Date().toISOString()})};
 assert.equal((await fetch(url+'/v1/heater/commands',options)).status,202);
 assert.equal((await fetch(url+'/v1/heater/commands',options)).status,202);assert.equal(commands,1);
 const record=await (await fetch(url+'/v1/commands/'+id,{headers})).json();assert.equal(record.outcome,'accepted');
 redirect=true;assert.equal((await fetch(url+'/v1/status',{headers})).status,503);assert.equal(stolen,0);
});
