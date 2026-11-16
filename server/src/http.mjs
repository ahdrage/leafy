import http from 'node:http';
export function createHTTPServer(app){
 const server=http.createServer({maxHeaderSize:8192},async(req,res)=>{
  function send(status,body){res.writeHead(status,{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Connection':'close'});res.end(JSON.stringify(body));}
  try{
   // Browser requests are not part of the native-app API. No CORS or cookies.
   if(req.headers.origin)return send(403,{error:'browser_origin_not_allowed'});
   let body;
   if(req.method==='POST'){
    if(req.headers['content-type']?.split(';')[0].trim()!=='application/json')return send(415,{error:'json_required'});
    if(Number(req.headers['content-length'])>2048)return send(413,{error:'body_too_large'});
    let text='';for await(const chunk of req){text+=chunk.toString('utf8');if(Buffer.byteLength(text)>2048)return send(413,{error:'body_too_large'});}
    try{body=JSON.parse(text);}catch{return send(400,{error:'invalid_json'});}
   }
   const result=await app.dispatch({method:req.method,path:req.url,headers:req.headers,body});send(result.status,result.body);
  }catch{if(!res.headersSent)send(500,{error:'internal_error',message:'Unexpected server error. Do not automatically repeat a command.'});else res.destroy();}
 });
 server.requestTimeout=10000;server.headersTimeout=10000;server.maxRequestsPerSocket=1;server.maxConnections=32;server.setTimeout(10000,s=>s.destroy());
 return server;
}
