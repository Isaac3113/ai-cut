import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {bundle} from '@remotion/bundler';
import {openBrowser,selectComposition,renderStill,renderMedia} from '@remotion/renderer';

const root=path.dirname(fileURLToPath(import.meta.url));
const work=path.resolve(process.argv[2]??'');
const action=process.argv[3]??'stills';
if(!['stills','render'].includes(action))throw new Error('Action must be stills or render');
const props=JSON.parse(readFileSync(path.join(work,'showcase-props.json'),'utf8'));
const revision=process.argv[4]??'r1';
if(!/^r[0-9]+$/.test(revision))throw new Error('Revision must be r followed by digits');
const out=path.join(work,`visual-${revision}`);mkdirSync(out,{recursive:true});
const bundleDir=path.join(out,'bundle');
let serveUrl=bundleDir;
if(!existsSync(path.join(bundleDir,'index.html'))){
 serveUrl=await bundle({entryPoint:path.join(root,'src/template-library/talking-head-effects/index.tsx'),publicDir:path.join(work,'render-assets'),outDir:bundleDir});
}
const browser=await openBrowser('chrome',{browserExecutable:'C:/Program Files/Google/Chrome/Application/chrome.exe',logLevel:'error'});
try{
 const composition=await selectComposition({serveUrl,id:'TalkingHeadShowcase',inputProps:props,puppeteerInstance:browser,logLevel:'error'});
 if(action==='stills'){
  const samples=props.clips.map((clip)=>({kind:clip.kind,frame:clip.fromFrame+Math.floor((clip.kind===9?(21.75-clip.sourceStart)/clip.playbackRate*30:clip.durationInFrames)*.55)}));
  const dual=props.clips.find(c=>c.kind===9);samples.push({kind:10,frame:dual.fromFrame+dual.durationInFrames-14});
  for(const sample of samples){
   const output=path.join(out,`effect-${String(sample.kind).padStart(2,'0')}.png`);
   await renderStill({serveUrl,composition,inputProps:props,frame:sample.frame,output,puppeteerInstance:browser,logLevel:'error',overwrite:false});
   console.log(`Sampled effect ${sample.kind}`);
  }
  writeFileSync(path.join(out,'sample-frames.json'),JSON.stringify(samples,null,2)+'\n');
 }else{
  const outputLocation=path.join(out,'visual-master-silent.mp4');
  await renderMedia({serveUrl,composition,inputProps:props,outputLocation,codec:'h264',crf:17,gopSize:1,concurrency:3,muted:true,puppeteerInstance:browser,logLevel:'error',overwrite:false,onProgress:({renderedFrames})=>{if(renderedFrames%90===0)console.log(`Rendered ${renderedFrames}/${composition.durationInFrames}`)}});
  console.log(JSON.stringify({outputLocation,frames:composition.durationInFrames,status:'rendered-silent-visual-source'}));
 }
}finally{await browser.close({silent:true});}
