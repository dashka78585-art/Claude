const {chromium}=require('playwright');const fs=require('fs');
const C=JSON.parse(fs.readFileSync('chunks.json'));
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920}});
await p.goto('file://'+process.cwd()+'/overlay.html');await p.evaluate(()=>document.fonts.ready);
await p.evaluate(()=>{document.getElementById('head').style.display='block';document.getElementById('sub').innerHTML=''});
await p.waitForTimeout(300);await p.screenshot({path:'render/head.png',omitBackground:true});
await p.evaluate(()=>document.getElementById('head').style.display='none');
await p.screenshot({path:'render/blank.png',omitBackground:true});
for(let i=0;i<C.length;i++){await p.evaluate(t=>{document.getElementById('sub').innerHTML=t.replace(/\*([^*]+)\*/g,'<b>$1</b>')},C[i][2]);
await p.screenshot({path:`render/s${String(i).padStart(3,'0')}.png`,omitBackground:true});}
await b.close()})();
