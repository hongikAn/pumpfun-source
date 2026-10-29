const { chromium, expect } = require(process.env.PLAYWRIGHT_MODULE);
const fs = require('node:fs');
const path = require('node:path');
const cp = require('node:child_process');
const mode = process.argv[2];
const out = path.resolve(process.argv[3]);
const worktree = process.env.WORKTREE;
const origin = 'http://127.0.0.1:3011';
const events = [];
const record = (name, data={}) => { events.push({ at: new Date().toISOString(), name, ...data }); console.log(JSON.stringify(events.at(-1))); };
(async()=>{
 const sha=cp.execFileSync('git',['rev-parse','HEAD'],{cwd:worktree,encoding:'utf8'}).trim();
 const expected = mode==='1219' ? 'b5190a6e88b07e18ffe6bd8b8a92fcf00b12790d' : 'ec972afcfd9623633096aa2775d49d2c9f021264';
 if(sha!==expected)throw new Error('Unexpected source head: '+sha);
 record('start',{mode,sourceHead:sha,scope:'fresh review-response capture, not the earlier qualification run'});
 const browser = await chromium.launch({headless:true});
 const context = await browser.newContext({viewport:{width:1280,height:720},recordVideo:{dir:out,size:{width:1280,height:720}}});
 await context.addCookies([{name:'clickwrap_accepted',value:'true',domain:'127.0.0.1',path:'/',httpOnly:false,secure:false,sameSite:'Lax'}]);
 const violations=[]; const consoleErrors=[]; const requests=[];
 await context.route('**/*', async route=>{
   const req=route.request(); const url=new URL(req.url());
   if(mode==='1181' && url.origin==='https://x.com' && url.pathname==='/alice_pump' && req.method()==='GET'){
    record('external target intercepted',{url:url.href,networkResponse:'local synthetic HTML'});
    return route.fulfill({status:200,contentType:'text/html',body:'<!doctype html><title>Intercepted X target</title><h1>Local test interceptor</h1><p>No request reached X.</p>'});
   }
   if(url.origin!==origin || !['GET','HEAD'].includes(req.method())){violations.push(req.method()+' '+url.href);return route.abort();}
   requests.push(req.method()+' '+url.pathname+url.search);return route.continue();
 });
 const page=await context.newPage();
 page.on('console',m=>{if(m.type()==='error')consoleErrors.push(m.text());});
 page.on('pageerror',e=>consoleErrors.push(String(e)));
 if(mode==='1219'){
  let r=await fetch('http://127.0.0.1:3001/__control',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({mode:'normal'})});if(!r.ok)throw Error('control failed');
  for(const [label,token] of [['backend-rejected','YWJj.ZGVm'],['malformed','not-a-cursor']]){
   await page.goto(origin+'/?tab=local-callouts&nativeView=newest&nativeCursor='+token);
   await expect(page.getByTestId('native-feed-error')).toContainText('Local page cursor rejected');
   const recovery=page.getByRole('link',{name:'Return to first local page'});
   await expect(recovery).toHaveAttribute('href','/?tab=local-callouts&nativeView=newest');
   await expect(page.getByRole('link',{name:'Local newest',exact:true})).toHaveAttribute('aria-current','page');
   await recovery.focus();await page.waitForTimeout(1000);
   await page.screenshot({path:path.join(out,'after-'+label+'.png')});
   record('cursor rejected; selected view retained',{label,url:page.url(),recoveryHref:await recovery.getAttribute('href')});
   await page.keyboard.press('Enter');
   await expect(page).toHaveURL(origin+'/?tab=local-callouts&nativeView=newest');
   await expect(page.getByTestId('native-callout-card')).toHaveCount(3);
   await expect(page.getByTestId('native-feed-count')).toBeVisible();
   await page.waitForTimeout(1100);await page.screenshot({path:path.join(out,'after-'+label+'-recovered.png')});
   record('recovered to first newest page',{label,url:page.url(),cards:await page.getByTestId('native-callout-card').count()});
  }
  const data=await(await fetch('http://127.0.0.1:3001/__requests')).json();
  fs.writeFileSync(path.join(out,'backend-requests.json'),JSON.stringify(data,null,2)+'\n');
  record('backend requests saved',{requests:data.requests});
 }else{
  await page.goto(origin+'/profile/user-001');
  const link=page.getByRole('link',{name:'View on X'});
  await expect(link).toHaveAttribute('href','https://x.com/alice_pump');
  await expect(link).toHaveAttribute('target','_blank');
  await link.focus();await page.waitForTimeout(1100);
  await page.screenshot({path:path.join(out,'after-profile.png')});
  record('recorded X link visible',{href:await link.getAttribute('href'),label:await link.getAttribute('aria-label')});
  const popupPromise=context.waitForEvent('page');await page.keyboard.press('Enter');const popup=await popupPromise;await popup.waitForLoadState('domcontentloaded');
  await expect(popup).toHaveURL('https://x.com/alice_pump');await expect(popup.getByRole('heading',{name:'Local test interceptor'})).toBeVisible();
  await page.waitForTimeout(1000);await popup.screenshot({path:path.join(out,'after-keyboard-popup.png')});
  record('keyboard activation opened intercepted target',{url:popup.url()});await popup.close();
  await page.goto(origin+'/profile/user-003');await expect(page.getByRole('link',{name:'View on X'})).toHaveCount(0);
  await page.waitForTimeout(1000);await page.screenshot({path:path.join(out,'after-missing-handle.png')});record('missing handle omitted');
 }
 expect(violations).toEqual([]);expect(consoleErrors).toEqual([]);
 record('pass',{violations,consoleErrors});
 const video=page.video();await context.close();await video.saveAs(path.join(out,'walkthrough.webm'));await browser.close();
 fs.writeFileSync(path.join(out,'browser-requests.json'),JSON.stringify(requests,null,2)+'\n');
 fs.writeFileSync(path.join(out,'capture.json'),JSON.stringify({sourceHead:sha,recordedAt:new Date().toISOString(),events,violations,consoleErrors},null,2)+'\n');
})().catch(e=>{console.error(e);process.exit(1)});
