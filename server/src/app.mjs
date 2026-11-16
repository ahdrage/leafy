import {timingSafeEqual} from 'node:crypto';
import {existsSync, readFileSync, mkdirSync, openSync, writeFileSync, fsyncSync, closeSync, renameSync} from 'node:fs';
import {dirname} from 'node:path';

const uuid=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const reply=(status,body)=>({status,body});
const error=(status,code,message)=>reply(status,{error:code,message});
function equal(a,b){const x=Buffer.from(a),y=Buffer.from(b);return x.length===y.length&&timingSafeEqual(x,y);}
function save(path,data){
 mkdirSync(dirname(path),{recursive:true,mode:0o700});
 const temp=path+'.tmp';const fd=openSync(temp,'w',0o600);
 try{writeFileSync(fd,JSON.stringify(data));fsyncSync(fd);}finally{closeSync(fd);}
 renameSync(temp,path);
 const directory=openSync(dirname(path),'r');try{fsyncSync(directory);}finally{closeSync(directory);}
}
function normalizeStatus(data,at){
 if(data.schemaVersion!==1||typeof data.canWriteEnabled!=='boolean'||typeof data.requestBusy!=='boolean'||typeof data.heatRequested!=='boolean'||!Number.isInteger(data.lastCommandError)||!Number.isFinite(data.protectedSupplyMv)||data.protectedSupplyMv<0||data.protectedSupplyMv>100000)throw Error('Invalid board status');
 const value=data.socTenths,age=data.socAgeMs;
 const available=Number.isInteger(value)&&value>=0&&value<=1000&&Number.isFinite(age)&&age>=0;
 if(value!==null&&value!==undefined&&!available)throw Error('Invalid battery status');
 return {apiVersion:1,deviceReachable:true,observedAt:at,protectedSupplyVolts:data.protectedSupplyMv>0?data.protectedSupplyMv/1000:null,
  canWriteEnabled:data.canWriteEnabled,requestBusy:data.requestBusy,lastCommandError:data.lastCommandError,
  heater:{requested:data.heatRequested,actualState:'unknown'},
  tractionBattery:{socPercent:available?value/10:null,ageSeconds:available?Math.floor(age/1000):null,
   availability:available?(age<=120000?'fresh':'stale'):(data.telemetryEnabled?'unavailable':'unsupported'),
   source:available?'ev_can_0x55b_bms':null}};
}
function legacyStatus(text,at){
 const mv=/^Protected supply: ([0-9]+\.[0-9]+) V \(after input diode\)$/m.exec(text);
 const errorCode=/^Last command error: (-?\d+)$/m.exec(text);
 if(!mv||!errorCode||!/^CAN controls: (enabled|locked for commissioning)$/m.test(text)||!/^Request sequence: (idle|running)$/m.test(text)||!/^Local heat request \/ timer: (none|active or outcome uncertain)$/m.test(text))throw Error('Invalid legacy status');
 return normalizeStatus({schemaVersion:1,canWriteEnabled:text.includes('CAN controls: enabled'),protectedSupplyMv:Number(mv[1])*1000,
  requestBusy:text.includes('Request sequence: running'),heatRequested:text.includes('Local heat request / timer: active'),lastCommandError:Number(errorCode[1]),socTenths:null,socAgeMs:null,telemetryEnabled:false},at);
}
export function createApp({token,deviceKey,deviceURL,statePath,fetchImpl=fetch,now=Date.now}){
 if(typeof token!=='string'||token.length<32||typeof deviceKey!=='string'||deviceKey.length<12||token===deviceKey||!statePath)throw Error('Set distinct app token (32+ characters), device key (12+) and state path');
 const url=new URL(deviceURL);
 if(!['http:','https:'].includes(url.protocol)||url.username||url.password||url.search||url.hash||url.pathname!=='/')throw Error('Device URL must be a fixed HTTP(S) origin');
 let records=existsSync(statePath)?JSON.parse(readFileSync(statePath,'utf8')):{};
 if(!records||Array.isArray(records)||typeof records!=='object')throw Error('Invalid command ledger');
 // A process crash can occur after delivery but before the reply was saved.
 // Preserve every reserved ID and never replay it after restart.
 for(const [id,r] of Object.entries(records)){
  if(!uuid.test(id)||!r?.body||!Number.isInteger(r.status))throw Error('Invalid command ledger');
  if(r.body.outcome==='pending'){r.status=502;r.body.outcome='unknown';r.body.message='Server restarted during delivery. Check the car; this command will not be resent.';}
 }
 if(Object.keys(records).length)save(statePath,records);
 let lastOn=-Infinity, deliveryBusy=false;
 async function board(path,method='GET'){
  const signal=AbortSignal.timeout(3500);
  const response=await fetchImpl(url.origin+path,{method,headers:{'X-Leaf-Key':deviceKey},redirect:'error',signal});
  let text='';const reader=response.body?.getReader();
  if(reader){try{while(true){const {done,value}=await reader.read();if(done)break;text+=Buffer.from(value).toString('utf8');if(text.length>8192)throw Error('Oversized response');}}finally{await reader.cancel().catch(()=>{});}}
  return {status:response.status,text};
 }
 async function status(){
  let response;try{response=await board('/api/v1/status');if(response.status===404)response={...await board('/api/status'),legacy:true};}
  catch{return reply(503,{error:'device_unreachable',deviceReachable:false,message:'Cannot read Leafy. No command was sent.'});}
  if(response.status!==200)return error(502,'device_status_failed','Board rejected status access. Check the server device key and firmware.');
  try{return reply(200,response.legacy?legacyStatus(response.text,new Date(now()).toISOString()):normalizeStatus(JSON.parse(response.text),new Date(now()).toISOString()));}
  catch{return error(502,'invalid_device_status','Board returned an unrecognized status response.');}
 }
 async function command(headers,body){
  const rawID=headers['idempotency-key'];
  const id=typeof rawID==='string'?rawID.toLowerCase():null;
  if(!uuid.test(id??'')||!body||Array.isArray(body)||!['on','off'].includes(body.action)||Object.keys(body).some(k=>!['action','issuedAt'].includes(k)))return error(400,'invalid_command','Use a UUID Idempotency-Key and JSON action (on/off), issuedAt.');
  if(records[id])return records[id].body.action===body.action?records[id]:error(409,'idempotency_conflict','That ID belongs to a different action.');
  if(deliveryBusy)return error(409,'delivery_busy','Another request is still being delivered. No command sent. Wait for its result, then explicitly request Off if needed.');
  const issued=typeof body.issuedAt==='string'?Date.parse(body.issuedAt):NaN;
  if(!Number.isFinite(issued)||now()-issued>10000||issued-now()>5000)return error(400,'expired_command','Command must be issued now. Check your phone clock; offline commands are not queued.');
  if(body.action==='on'&&now()-lastOn<3000)return error(429,'on_rate_limited','Wait before sending another new On request. Off remains available.');
  if(Object.keys(records).length>=10000)return error(503,'ledger_full','Command history is full; maintenance is required. No command sent.');
  records[id]=reply(202,{commandId:id,action:body.action,outcome:'pending',actualHeaterState:'unknown',createdAt:new Date(now()).toISOString(),message:'Delivery in progress; do not create a new command to retry.'});
  // Persist before touching the vehicle; failure to persist means fail closed.
  try{save(statePath,records);}catch{delete records[id];return error(503,'storage_failed','Cannot record command safely. No command sent.');}
  if(body.action==='on')lastOn=now();
  deliveryBusy=true;
  let response;
  try{response=await board('/api/'+body.action,'POST');}
  catch{response=null;}
  let outcome='unknown',code=502,message='Delivery outcome unknown. Check the car. This command will not be resent.';
  if(response?.status===202){outcome='accepted';code=202;message='Leafy accepted the request. This does not confirm the heater state.';}
  else if(response&&[400,401,403,409,429].includes(response.status)){
   outcome='rejected';code=response.status===401?502:response.status;
   message=response.status===409?'Leafy rejected the request: low/unknown protected voltage or a command is busy.':'Leafy rejected the command. Check device configuration.';
  }
  records[id]=reply(code,{...records[id].body,outcome,message});
  try{save(statePath,records);}catch{
   records[id]=reply(502,{...records[id].body,outcome:'unknown',message:'Could not persist the result. Check the car; do not resend with a new ID.'});
  }
  deliveryBusy=false;
  return records[id];
 }
 return {async dispatch({method,path,headers={},body}){
  if(typeof headers.authorization!=='string'||!equal(headers.authorization,'Bearer '+token))return error(401,'unauthorized','A valid app token is required.');
  if(method==='GET'&&path==='/v1/status')return status();
  if(method==='POST'&&path==='/v1/heater/commands')return command(headers,body);
  const match=/^\/v1\/commands\/([^/]+)$/.exec(path);
  if(method==='GET'&&match&&uuid.test(match[1]))return records[match[1].toLowerCase()]?reply(200,records[match[1].toLowerCase()].body):error(404,'command_not_found','No command with that ID is recorded.');
  return error(404,'not_found','Unknown API route.');
 }};
}
