// Usage:
//   node render.mjs <page.html> <timing.json> <out.mp4> [fps]
//   node render.mjs <page.html> <timing.json> --stills <t1,t2,...> <outdir>
import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

const [html, timingPath, a3, a4, a5] = process.argv.slice(2);
const timing = JSON.parse(fs.readFileSync(timingPath, 'utf8'));
const stills = a3 === '--stills';

const browser = await chromium.launch({ args: ['--disable-web-security', '--allow-file-access-from-files', '--force-color-profile=srgb'] });
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
page.on('console', m => console.log('[page]', m.text()));
page.on('pageerror', e => { console.error('[pageerror]', e.message); process.exitCode = 2; });
await page.addInitScript(t => { window.TIMING = t; }, timing);
await page.goto('file://' + path.resolve(html), { waitUntil: 'networkidle' });
await page.evaluate(() => window.ready());

if (stills) {
  const times = a4.split(',').map(Number);
  fs.mkdirSync(a5, { recursive: true });
  for (const t of times) {
    await page.evaluate(t => window.seek(t), t);
    await page.screenshot({ path: path.join(a5, `t${t.toFixed(2)}.jpg`), type: 'jpeg', quality: 85 });
  }
  await browser.close();
  process.exit();
}

const fps = Number(a4 || 30);
const total = timing.total;
const n = Math.round(total * fps);
const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
  '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', String(fps), a3], { stdio: ['pipe', 'inherit', 'inherit'] });
const t0 = Date.now();
for (let f = 0; f < n; f++) {
  const t = f / fps;
  await page.evaluate(t => window.seek(t), t);
  const buf = await page.screenshot({ type: 'jpeg', quality: 93 });
  if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
  if (f % 150 === 0) console.log(`frame ${f}/${n} ${((Date.now() - t0) / 1000).toFixed(1)}s`);
}
ff.stdin.end();
await new Promise(r => ff.on('close', r));
await browser.close();
console.log('done', n, 'frames in', ((Date.now() - t0) / 1000).toFixed(1), 's');
