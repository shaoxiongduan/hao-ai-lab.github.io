// node ovshot.js <overlay.html> <hash> <out.png>: transparent 1280x720 overlay
const puppeteer = require('puppeteer-core');
(async () => {
  const [file, hash, out] = process.argv.slice(2);
  const b = await puppeteer.launch({executablePath: process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true});
  const p = await b.newPage();
  await p.setViewport({width: 1280, height: 720, deviceScaleFactor: 1});
  await p.goto('file://' + file + '#' + hash, {waitUntil: 'networkidle0'});
  await p.waitForFunction(() => document.title === 'ready');
  if (!(await p.evaluate(() => document.fonts.check('700 13px "Noto Sans"')))) throw new Error('font not loaded');
  await p.screenshot({path: out, omitBackground: true, clip: {x: 0, y: 0, width: 1280, height: 720}});
  await b.close();
})();
