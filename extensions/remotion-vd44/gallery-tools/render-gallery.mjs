import {readFileSync, writeFileSync, mkdirSync, existsSync, statSync} from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {bundle} from '@remotion/bundler';
import {getCompositions, openBrowser, renderMedia} from '@remotion/renderer';
const ext = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const repo = path.resolve(ext, '../..');
const out = path.join(repo, 'docs/template-gallery/demos/remotion');
const work = path.join(ext, 'gallery-tools/remotion-work');
mkdirSync(out,{recursive:true}); mkdirSync(work,{recursive:true});
const catalog=JSON.parse(readFileSync(path.join(ext,'template-catalog.json'),'utf8'));
const selected = process.argv.slice(2).filter(v=>!v.startsWith('--'));
const serveUrl = await bundle({entryPoint:path.join(ext,'src/template-gallery/index.ts'), publicDir:path.join(ext,'public'), outDir:path.join(work,'bundle'), webpackOverride:(config)=>({...config,module:{...config.module,rules:[...(config.module?.rules??[]),{test:/\.(?:ts|tsx)$/,include:[path.join(ext,'src/vendor/rendercomp'),path.join(ext,'src/template-library/remotion-ui')],enforce:'pre',use:[path.join(ext,'gallery-tools/chinese-gallery-loader.cjs')]}]}})});
const browser=await openBrowser('chrome',{browserExecutable:'C:/Program Files/Google/Chrome/Application/chrome.exe',logLevel:'error'});
const reportFile=path.join(work,'render-log.json');
let report=existsSync(reportFile)?JSON.parse(readFileSync(reportFile,'utf8')):{engine:'Remotion',version:'4.0.523',font:'NotoSansSC',vendor_modified:false,renders:[]};
try {
 const comps=await getCompositions(serveUrl,{puppeteerInstance:browser,logLevel:'error'});
 if(comps.length!==55)throw new Error(`Registration count mismatch ${comps.length}`);
 console.log(`Bundle ready; ${comps.length} compositions.`);
 for(const composition of comps) {
  if(selected.length&&!selected.includes(composition.id))continue;
  const outputLocation=path.join(out,composition.id+'.mp4');
  if(existsSync(outputLocation)&&!process.argv.includes('--force')){console.log(`SKIP ${composition.id}`);continue;}
  const started=performance.now();
  const scale=composition.width>composition.height?0.5:composition.width===composition.height?2/3:0.5;
  await renderMedia({serveUrl,composition,outputLocation,codec:'h264',crf:25,x264Preset:'fast',scale,muted:true,concurrency:3,puppeteerInstance:browser,logLevel:'error',overwrite:process.argv.includes('--force')});
  const record={id:composition.id,frames:composition.durationInFrames,fps:composition.fps,width:Math.round(composition.width*scale),height:Math.round(composition.height*scale),bytes:statSync(outputLocation).size,sha256:createHash('sha256').update(readFileSync(outputLocation)).digest('hex'),render_seconds:Math.round((performance.now()-started)/10)/100,path:path.relative(repo,outputLocation).replaceAll('\\','/'),state:'rendered_pending_decode_and_visual_review'};
  if(record.bytes>=2000000)throw new Error(`Demo exceeds 2MB target: ${composition.id} ${record.bytes}`);
  report.renders=report.renders.filter(r=>r.id!==record.id);report.renders.push(record);
  writeFileSync(reportFile,JSON.stringify(report,null,2)+'\n');
  console.log(`${report.renders.length}/55 ${composition.id}: ${record.render_seconds}s, ${record.bytes} bytes`);
 }
} finally {await browser.close({silent:true});}
