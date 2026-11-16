// Real-browser regression: all network traffic is mocked; never contacts a car.
const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');
const {chromium}=require('playwright');
const source=fs.readFileSync(path.join(__dirname,'../src/main.cpp'),'utf8');
const html=source.match(/static const char PAGE\[\]=R"HTML\(([\s\S]*?)\)HTML";/)[1];
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});
 try{
  const context=await browser.newContext();
  const page=await context.newPage();const errors=[],commands=[];
  let hangStatus=false,statusText='Main battery (dashboard): 97% - updated 2 seconds ago\nMain battery (BMS): 50.0% - updated 4 seconds ago\nAutomatic Off request: in 14:59 (local timer)\nActual heater state: unverified';
  page.on('pageerror',e=>errors.push(e.message));
  await context.route('**/*',async route=>{
   const req=route.request();const url=new URL(req.url());
   if(url.origin!=='http://leafy.test'){await route.abort();return;}
   if(url.pathname==='/'){await route.fulfill({status:200,contentType:'text/html',body:html});return;}
   if(url.pathname==='/api/auth'){await route.fulfill({status:200,body:'Control key accepted. No heater command sent.'});return;}
   if(url.pathname==='/api/status'){if(hangStatus)return;await route.fulfill({status:200,body:statusText});return;}
   if(url.pathname==='/api/on'||url.pathname==='/api/off'){
    commands.push({path:url.pathname,method:req.method(),key:req.headers()['x-leaf-key']});
    await route.fulfill({status:202,body:'Request submitted. Verify the heater in the car.'});return;
   }
   await route.fulfill({status:404,body:'not found'});
  });
  await page.goto('http://leafy.test/');
  await page.waitForFunction(()=>document.getElementById('status').textContent.includes('50.0%'));
  assert.match(await page.locator('#status').innerText(),/dashboard\): 97%/);
  assert.match(await page.locator('#status').innerText(),/14:59/);
  statusText='Main battery (dashboard): 97% - updated 2 seconds ago\nMain battery (BMS): Last known 50.0% - 180 seconds ago (stale)\nAutomatic Off request: timer elapsed; verify heater in car';
  await page.evaluate(()=>refresh());
  assert.match(await page.locator('#status').innerText(),/Last known/);
  assert.match(await page.locator('#status').innerText(),/timer elapsed/);
  assert.equal(commands.length,0);
  // Exercise the HTML buttons, not just the JavaScript functions directly.
  console.log('Browser:',await browser.version());
  console.log('Native button.command type:',await page.locator('#on').evaluate(b=>typeof b.command));
  await page.getByLabel('Control key',{exact:true}).fill('browser-test-key-only');
  await page.getByRole('button',{name:'Save key for this tab',exact:true}).click();
  await page.waitForFunction(()=>document.getElementById('keyStatus').textContent.includes('verified and saved'));
  assert.equal(commands.length,0,'Save must never send a heater request');
  await page.getByRole('button',{name:'Heat on',exact:true}).click();
  await page.waitForTimeout(150);
  assert.deepEqual(errors,[],'Button click must not raise a JavaScript exception');
  assert.equal(commands.length,1,'Heat On must send exactly one mocked request');
  assert.deepEqual(commands[0],{path:'/api/on',method:'POST',key:'browser-test-key-only'});
  assert.match(await page.locator('#result').innerText(),/accepted.*202/);
  await page.getByRole('button',{name:'Heat off',exact:true}).click();
  await page.waitForFunction(()=>document.getElementById('result').textContent.includes('Heat off request accepted'));
  assert.equal(commands.length,2);assert.equal(commands[1].path,'/api/off');
  await page.reload();assert.equal(await page.locator('#key').inputValue(),'browser-test-key-only');
  assert.equal(commands.length,2,'Reload must never replay a command');
  await page.getByRole('button',{name:'Forget key',exact:true}).click();
  assert.equal(await page.locator('#key').inputValue(),'');
  assert.deepEqual(errors,[]);
  hangStatus=true;
  const refreshed=await page.evaluate(()=>Promise.race([refresh().then(()=> 'done'),new Promise(r=>setTimeout(()=>r('hung'),4500))]));
  assert.equal(refreshed,'done','A stalled status request must time out instead of leaving a fresh-looking reading');
  assert.match(await page.locator('#status').innerText(),/unreachable/i);
  assert.equal(commands.length,2,'Status failure must not send or retry heater commands');
  console.log('PASS battery age/countdown display and bounded offline status; all requests intercepted.');
  console.log('PASS real button clicks: Save, Heat On, Heat Off, reload, Forget; all requests intercepted.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
