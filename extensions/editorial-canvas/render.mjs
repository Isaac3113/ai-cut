import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {bundle} from '@remotion/bundler';
import {openBrowser,renderMedia,renderStill,selectComposition} from '@remotion/renderer';

const root=path.dirname(fileURLToPath(import.meta.url));
const args=process.argv.slice(2), options={};
for(let i=0;i<args.length;i+=2){if(!args[i]?.startsWith('--')||args[i+1]===undefined)throw Error('Use --input, --assets, --out, --chrome and optional --mode still|render / --time seconds');options[args[i].slice(2)]=args[i+1];}
for(const k of Object.keys(options))if(!['input','assets','out','chrome','mode','time','crf','concurrency'].includes(k))throw Error('Unknown option '+k);
if(!options.input||!options.out)throw Error('Provide --input inputs.json --out a-new-instance-directory');
const p=JSON.parse(fs.readFileSync(options.input,'utf8').replace(/^\uFEFF/,''));
const fail=(s)=>{throw Error('INPUT_INVALID: '+s);};
const str=(v,n,k)=>{if(typeof v!=='string'||!v.trim()||Array.from(v).length>n)fail(k+' must be 1–'+n+' characters');};
const keys=(value,allowed,where)=>{if(!value||typeof value!=='object'||Array.isArray(value)||Object.keys(value).some(k=>!allowed.includes(k)))fail('unknown field in '+where);};
keys(p,['duration','aspect','variant','accent','secondary','paper','ink','label','presenter','presenterType','presenterLabel','presenterStart','font','seed','scenes','captions'],'inputs');
if(!['9:16','16:9'].includes(p.aspect)||!['paper-editorial','dark-workbench','material-wall'].includes(p.variant))fail('aspect or variant');
for(const k of ['accent','secondary','paper','ink'])if(!/^#[0-9a-f]{6}$/i.test(p[k]))fail(k+' must be #RRGGBB');
str(p.label,32,'label');
if(!Number.isInteger(p.seed)||p.seed<0||p.seed>9999)fail('seed 0–9999');
if(!Array.isArray(p.scenes)||p.scenes.length<1||p.scenes.length>12)fail('1–12 scenes');
const allowed=new Set(['hook','prompt','shift','flow','gallery','folder','closing']);
let duration=0;
for(const [i,s] of p.scenes.entries()){
 keys(s,['kind','title','emphasis','detail','duration','items'],'scene');
 if(!allowed.has(s.kind))fail('scene kind');str(s.title,26,'title');str(s.emphasis,20,'emphasis');str(s.detail,70,'detail');
 if(!Number.isFinite(s.duration)||s.duration<3||s.duration>12)fail('each scene duration 3–12 seconds');
 if(!Array.isArray(s.items)||s.items.length<1||s.items.length>(s.kind==='flow'?5:3))fail('scene items 1–3; flow supports 2–5');
 if(s.kind==='flow'&&s.items.length<2)fail('flow needs 2–5 meaningful steps');
 if(s.kind==='flow'&&s.items.length>3&&s.duration<s.items.length)fail('4 or 5 flow steps require at least 4 or 5 seconds so every step can enter');
 for(const a of s.items){keys(a,['title','detail','media','mediaType','sourceStart'],'item');str(a.title,s.kind==='hook'?6:12,'item.title');if(typeof a.detail!=='string'||Array.from(a.detail).length>(s.kind==='flow'?20:32))fail('item.detail exceeds this scene capacity');if(a.media&& !['image','video'].includes(a.mediaType))fail('media needs image/video type');if(a.sourceStart!==undefined&&(!Number.isFinite(a.sourceStart)||a.sourceStart<0))fail('sourceStart must be nonnegative');}
 duration+=s.duration;
}
if(duration>120)fail('whole visual at most 120 seconds');
if(!Number.isFinite(p.duration)||p.duration<3||p.duration>120||Math.abs(p.duration-duration)>1/30)fail('duration must equal the sum of scene durations (3–120 seconds)');
if(!Array.isArray(p.captions))fail('captions array is required (empty for graphic-only output)');
let previous=-1;
for(const c of p.captions){keys(c,['start','end','text'],'caption');str(c.text,p.aspect==='9:16'?24:45,'caption');if(!Number.isFinite(c.start)||!Number.isFinite(c.end)||c.start<previous||c.end<=c.start||c.end>duration)fail('caption clock/order');previous=c.end;}
if(p.presenter&&!['image','video'].includes(p.presenterType))fail('presenterType');
if(p.presenterStart!==undefined&&(!Number.isFinite(p.presenterStart)||p.presenterStart<0))fail('presenterStart must be a finite nonnegative source time');
const out=path.resolve(options.out);if(fs.existsSync(out))throw Error('OUTPUT_EXISTS: use a new instance directory; original output preserved');fs.mkdirSync(out,{recursive:true});
const assetRoot=options.assets?fs.realpathSync(options.assets):root;
const publicDir=path.join(out,'assets');fs.mkdirSync(publicDir);
const media=new Set([p.presenter,p.font,...p.scenes.flatMap(s=>s.items.map(a=>a.media))].filter(Boolean));
for(const relative of media){
 if(typeof relative!=='string'||relative.includes('\\')||path.isAbsolute(relative)||relative.split('/').some(x=>!x||x==='.'||x==='..')||/^[a-z]+:/i.test(relative))fail('media paths must be safe relative paths within --assets');
 const from=fs.realpathSync(path.join(assetRoot,relative));const rel=path.relative(assetRoot,from);
 if(rel==='..'||rel.startsWith('..'+path.sep)||path.isAbsolute(rel)||!fs.statSync(from).isFile())fail('asset escapes root');
 const to=path.join(publicDir,relative);fs.mkdirSync(path.dirname(to),{recursive:true});fs.copyFileSync(from,to);
}
fs.writeFileSync(path.join(out,'inputs.json'),JSON.stringify(p,null,2));
const serveUrl=await bundle({entryPoint:path.join(root,'src','index.tsx'),publicDir,outDir:path.join(out,'bundle'),webpackOverride:(config)=>({...config,resolve:{...config.resolve,modules:[path.join(root,'node_modules'),...(config.resolve?.modules??[])]}})});
const browser=await openBrowser('chrome',{browserExecutable:options.chrome||process.env.CHROME_PATH||undefined,logLevel:'error'});
try{
 const composition=await selectComposition({serveUrl,id:'EditorialCanvas',inputProps:p,puppeteerInstance:browser,logLevel:'error'});
 fs.writeFileSync(path.join(out,'composition.json'),JSON.stringify(composition,null,2));
 if(options.mode==='still'){
  const t=Number(options.time??Math.min(duration/2,4));if(!Number.isFinite(t)||t<0||t>=duration)fail('still time outside range');
  await renderStill({serveUrl,composition,inputProps:p,frame:Math.round(t*30),output:path.join(out,'preview.png'),puppeteerInstance:browser,logLevel:'error'});
 }else{
  const crf=Number(options.crf??19),concurrency=Number(options.concurrency??2);if(!Number.isInteger(crf)||crf<12||crf>30||!Number.isInteger(concurrency)||concurrency<1||concurrency>8)fail('crf/concurrency bounds');
  let step=-1;await renderMedia({serveUrl,composition,inputProps:p,outputLocation:path.join(out,'video-silent.mp4'),codec:'h264',crf,concurrency,muted:true,puppeteerInstance:browser,logLevel:'error',onProgress:({renderedFrames})=>{const q=Math.floor(renderedFrames/90);if(q!==step){console.log('Rendered '+renderedFrames+'/'+composition.durationInFrames);step=q;}}});
 }
 console.log(JSON.stringify({status:'rendered',out,width:composition.width,height:composition.height,fps:composition.fps,frames:composition.durationInFrames,audio:'none; sync source voice/music/SFX in the parent timeline'}));
}finally{await browser.close({silent:true});}
