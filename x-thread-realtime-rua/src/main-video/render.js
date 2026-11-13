// Render the built main-video page frame by frame. Usage: node render.js <html> stills <out-prefix> t1,t2,...  |  node render.js <html> video <out.mp4>
const puppeteer = require('puppeteer-core');
const { spawn } = require('child_process');
(async () => {
  const [file, mode, out, times] = process.argv.slice(2);
  const browser = await puppeteer.launch({ executablePath: process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true, args: ['--allow-file-access-from-files', '--hide-scrollbars'] });
  const page = await browser.newPage();
  const errs = []; page.on('pageerror', e => errs.push(e.message)); page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 1 });
  await page.goto('file://' + file, { waitUntil: 'networkidle0', timeout: 60000 });
  await page.evaluate(() => document.fonts.ready);
  const fontOk = await page.evaluate(() => document.fonts.check('800 40px Archivo'));
  console.log('font Archivo loaded:', fontOk);
  if (mode === 'stills') {
    for (const t of times.split(',').map(Number)) {
      await page.evaluate(t => window.render(t), t);
      await page.screenshot({ path: `${out}-${t}.jpg`, type: 'jpeg', quality: 85 });
    }
  } else {
    const fps = 30, dur = await page.evaluate(() => window.DUR), n = Math.round(dur * fps);
    const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(fps), '-i', '-', '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
    const t0 = Date.now();
    for (let i = 0; i < n; i++) {
      await page.evaluate(t => window.render(t), i / fps);
      const buf = await page.screenshot({ type: 'jpeg', quality: 95 });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if (i % 150 === 0) console.log(`frame ${i}/${n} ${((Date.now() - t0) / 1000).toFixed(0)} s`);
    }
    ff.stdin.end();
    await new Promise(r => ff.on('close', r));
    console.log('done', n, 'frames in', ((Date.now() - t0) / 1000).toFixed(0), 's');
  }
  console.log('errors', JSON.stringify(errs));
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
