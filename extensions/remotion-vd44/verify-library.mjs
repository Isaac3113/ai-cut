// Integration check: real browser renders, without user footage or online accounts.
import {createHash} from 'node:crypto';
import {existsSync, mkdirSync, readFileSync, writeFileSync} from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {bundle} from '@remotion/bundler';
import {getCompositions, openBrowser, renderMedia, renderStill} from '@remotion/renderer';

const root = path.dirname(fileURLToPath(import.meta.url));
const output = path.resolve(process.argv[2] ?? path.join(root, 'out/template-library', new Date().toISOString().replace(/[:.]/g, '-')));
const browserExecutable = process.argv[3] ?? 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const catalog = JSON.parse(readFileSync(path.join(root, 'template-catalog.json'), 'utf8'));
if (existsSync(output)) throw new Error('Output directory exists; choose a new directory.');
if (!existsSync(path.join(root, 'public/NotoSansSC.ttf'))) throw new Error('Local licensed font is missing.');
mkdirSync(path.join(output, 'stills'), {recursive: true});
const hash = (file) => createHash('sha256').update(readFileSync(file)).digest('hex');
const report = {checkedAt: new Date().toISOString(), runtime: 'Remotion 4.0.523', compositions: [], videos: [], limitations: ['Sample frames do not prove full animation quality.', 'Synthetic examples do not test person matting, source-video input, final ChatCut export or listening.']};
let browser;
try {
  const serveUrl = await bundle({entryPoint: path.join(root, 'src/template-library/index.ts'), publicDir: path.join(root, 'public'), outDir: path.join(output, 'bundle')});
  browser = await openBrowser('chrome', {browserExecutable, logLevel: 'error'});
  const compositions = await getCompositions(serveUrl, {puppeteerInstance: browser, logLevel: 'error'});
  const expectedIds = new Set(catalog.compositions.map((item) => item.composition_id));
  if (compositions.length !== catalog.counts.registered_compositions || compositions.length !== expectedIds.size || compositions.some((item) => !expectedIds.has(item.id))) {
    throw new Error('Actual compositions and template-catalog.json disagree. Update both when adding templates.');
  }
  for (const composition of compositions) {
    const frame = Math.floor(composition.durationInFrames / 2);
    const file = path.join(output, 'stills', `${composition.id}.png`);
    await renderStill({serveUrl, composition, output: file, frame, puppeteerInstance: browser, imageFormat: 'png', logLevel: 'error', overwrite: false});
    report.compositions.push({id: composition.id, width: composition.width, height: composition.height, fps: composition.fps, durationInFrames: composition.durationInFrames, sampledFrame: frame, sha256: hash(file)});
    if (report.compositions.length % 10 === 0) console.log(`Still renders: ${report.compositions.length}/${compositions.length}`);
  }
  for (const id of ['library-bar-zh', 'library-glass-zh', 'library-player-zh', 'library-orbit', 'library-text-mask']) {
    const composition = compositions.find((item) => item.id === id);
    const file = path.join(output, `${id}.mp4`);
    await renderMedia({serveUrl, composition, outputLocation: file, codec: 'h264', crf: 18, concurrency: 4, puppeteerInstance: browser, muted: true, logLevel: 'error', overwrite: false});
    report.videos.push({id, path: file, frames: composition.durationInFrames, sha256: hash(file)});
    console.log(`Video rendered: ${id}`);
  }
  report.status = 'passed';
} catch (error) {
  report.status = 'failed';
  report.error = String(error?.stack ?? error);
  process.exitCode = 1;
} finally {
  if (browser) await browser.close({silent: true});
  writeFileSync(path.join(output, 'verification.json'), JSON.stringify(report, null, 2) + '\n');
}
console.log(JSON.stringify({output, status: report.status, stills: report.compositions.length, videos: report.videos.length}));
