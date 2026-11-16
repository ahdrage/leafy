// Local-only test fixture: real API bridge, simulated board, no vehicle address/keys.
import http from 'node:http';
import {mkdtempSync, rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {createApp} from '../../server/src/app.mjs';
import {createHTTPServer} from '../../server/src/http.mjs';
const token = 'leafy-simulator-token-not-for-real-cars';
const dir = mkdtempSync(join(tmpdir(), 'leafy-ios-'));
let scenario = 'fresh', calls = [], requested = false;
const board = http.createServer((req, res) => {
  if (req.url === '/api/v1/status') {
    if (scenario === 'offline') { res.writeHead(503); res.end(); return; }
    res.setHeader('Content-Type', 'application/json');
    res.end(JSON.stringify({schemaVersion:1, canWriteEnabled: scenario !== 'locked', requestBusy:false,
      heatRequested:requested, lastCommandError:0, protectedSupplyMv:13700, telemetryEnabled:true,
      socTenths:scenario === 'missing' ? null : 925, socAgeMs:scenario === 'missing' ? null : scenario === 'stale' ? 240000 : 26000}));
    return;
  }
  if (req.method === 'POST' && ['/api/on','/api/off'].includes(req.url)) {
    calls.push(req.url);
    if (scenario === 'unknown') { req.socket.destroy(); return; }
    if (scenario === 'rejected') { res.writeHead(409); res.end('Low voltage'); return; }
    requested = req.url === '/api/on'; res.writeHead(202); res.end('Request submitted'); return;
  }
  res.writeHead(404); res.end();
});
await new Promise(resolve => board.listen(18788, '127.0.0.1', resolve));
const api = createHTTPServer(createApp({token,deviceKey:'simulated-board-key-only',deviceURL:'http://127.0.0.1:18788',statePath:join(dir,'commands.json')}));
await new Promise(resolve => api.listen(18787, '127.0.0.1', resolve));
const control = http.createServer((req,res) => {
  const url = new URL(req.url, 'http://127.0.0.1');
  if (req.method === 'POST' && url.pathname === '/scenario') {
    const next = url.searchParams.get('name');
    if (!['fresh','stale','missing','locked','offline','unknown','rejected'].includes(next)) {res.writeHead(400);res.end();return;}
    scenario = next;
    if (url.searchParams.has('reset')) { calls = []; requested = false; }
  }
  res.setHeader('Content-Type','application/json');res.end(JSON.stringify({scenario,calls,requested}));
});
await new Promise(resolve => control.listen(18789,'127.0.0.1',resolve));
console.log('Simulator fixture ready: http://127.0.0.1:18787 — fake car only.');
function stop(){board.close();api.close();control.close();rmSync(dir,{recursive:true,force:true});process.exit();}
process.on('SIGINT',stop);process.on('SIGTERM',stop);
