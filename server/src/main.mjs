import {resolve} from 'node:path';
import {openSync,closeSync,unlinkSync,mkdirSync} from 'node:fs';
import {dirname} from 'node:path';
import {createApp} from './app.mjs';
import {createHTTPServer} from './http.mjs';
const statePath=resolve(process.env.LEAFY_STATE_PATH??'server/data/commands.json');
const host=process.env.LEAFY_BIND??'127.0.0.1';
const port=Number(process.env.LEAFY_PORT??8787);
let lock;
try{
 if(!Number.isInteger(port)||port<1||port>65535)throw Error('invalid port');
 if(!['127.0.0.1','::1'].includes(host)&&process.env.LEAFY_ALLOW_LAN_HTTP!=='true')throw Error('Set LEAFY_ALLOW_LAN_HTTP=true only for a trusted home network or private VPN');
 mkdirSync(dirname(statePath),{recursive:true,mode:0o700});
 // One process per ledger. Never silently take over a crashed process's lock.
 lock=openSync(statePath+'.lock','wx',0o600);
 const app=createApp({token:process.env.LEAFY_API_TOKEN,deviceKey:process.env.LEAFY_DEVICE_KEY,deviceURL:process.env.LEAFY_DEVICE_URL,statePath});
 const server=createHTTPServer(app);
 const cleanup=()=>{if(lock!==undefined){closeSync(lock);unlinkSync(statePath+'.lock');lock=undefined;}};
 process.on('exit',cleanup);
 for(const signal of ['SIGTERM','SIGINT'])process.on(signal,()=>server.close(()=>process.exit(0)));
 server.on('error',()=>{console.error('Server could not listen. Check the bind address and port.');process.exit(1);});
 server.listen(port,host,()=>console.log(`Leafy API listening on ${host}:${port}. Local/private network only; no commands queued on startup.`));
}catch{
 if(lock!==undefined){closeSync(lock);unlinkSync(statePath+'.lock');}
 console.error('Leafy API startup refused. Check configuration, state permissions, or an existing/stale .lock file. Do not delete a lock while another instance is running.');process.exit(1);
}
