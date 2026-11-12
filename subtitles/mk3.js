const {chromium}=require('playwright');const fs=require('fs');
const C=JSON.parse(fs.readFileSync('chunks2.json'));
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920}});
await p.goto('file://'+process.cwd()+'/overlay3.html');await p.evaluate(()=>document.fonts.ready);
fs.mkdirSync('r3',{recursive:true});
await p.evaluate(()=>document.getElementById('head').style.display='block');await p.waitForTimeout(300);
await p.screenshot({path:'r3/head.png',omitBackground:true});
await p.evaluate(()=>document.getElementById('head').style.display='none');
let maxw=0;
for(let i=0;i<C.length;i++){const w=await p.evaluate(t=>{const s=document.getElementById('sub');s.innerHTML='<span>'+t+'</span>';const sp=s.firstChild;let fs=66;sp.style.fontSize='';while(sp.getBoundingClientRect().width>1000&&fs>40){fs-=2;sp.style.fontSize=fs+'px'}return sp.getBoundingClientRect().width},C[i][2]);maxw=Math.max(maxw,w);
await p.screenshot({path:`r3/s${String(i).padStart(3,'0')}.png`,omitBackground:true});}
console.log('max width',maxw);await b.close()})();
