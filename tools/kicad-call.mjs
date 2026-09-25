import { Client } from './KiCAD-MCP-Server/node_modules/@modelcontextprotocol/sdk/dist/esm/client/index.js';
import { StdioClientTransport } from './KiCAD-MCP-Server/node_modules/@modelcontextprotocol/sdk/dist/esm/client/stdio.js';
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
const base = resolve(dirname(fileURLToPath(import.meta.url)), 'KiCAD-MCP-Server');
const env = {...process.env, KICAD_PYTHON: `${base}/venv/bin/python3`, PYTHONNOUSERSITE:'1',
  KICAD_AUTO_LAUNCH:'false', LOG_LEVEL:'error',
  PATH:`/Applications/KiCad/KiCad.app/Contents/MacOS:${process.env.PATH}`};
const transport = new StdioClientTransport({command:process.execPath,args:[`${base}/dist/index.js`],cwd:base,env,stderr:'pipe'});
const client = new Client({name:'leaf-board-design',version:'1.0.0'});
transport.stderr?.on('data',data=>process.stderr.write(data));
await client.connect(transport);
try {
  if(process.argv[2]==='list') {
    const result=await client.listTools();
    writeFileSync(resolve(dirname(base),'kicad-tool-schemas.json'),JSON.stringify(result,null,2));
    console.log(JSON.stringify(result.tools.map(t=>({name:t.name,description:t.description.slice(0,120)}))));
  } else {
    const calls=JSON.parse(readFileSync(process.argv[2],'utf8'));
    for(const call of calls){
      let result;
      for(let attempt=0; attempt<20; attempt++) {
        result=await client.callTool(call,undefined,{timeout:120000});
        if(!JSON.stringify(result).includes('Python process for KiCAD scripting is not running')) break;
        await new Promise(resolve=>setTimeout(resolve,500));
      }
      console.log(JSON.stringify({name:call.name,result}));
      if(result.isError) throw new Error(`Tool failed: ${call.name}`);
    }
  }
} finally { await client.close(); }
