// Screenshot figures without captions (drawing box + legend). Usage: node figcrop.js <base> <outDir> idx:name,...
const puppeteer = require('puppeteer-core');
(async () => {
  const [base, out, list] = process.argv.slice(2);
  const browser = await puppeteer.launch({ executablePath: process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true, args: ['--hide-scrollbars'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 900, deviceScaleFactor: 2 });
  await page.goto(base + '/blogs/realtime-rua/', { waitUntil: 'networkidle0', timeout: 60000 });
  if (await page.evaluate(() => document.body.classList.contains('dark'))) { await page.click('#theme-toggle'); await new Promise(r => setTimeout(r, 300)); }
  for (const item of list.split(',')) {
    const [i, name] = item.split(':');
    const clip = await page.evaluate(i => {
      const f = document.querySelectorAll('.post-content figure')[+i]; f.scrollIntoView(); 
      const parts = [...f.querySelectorAll('.rua-fig, .rua-legend')].map(e => e.getBoundingClientRect());
      const x = Math.min(...parts.map(r => r.left)) - 12, y = Math.min(...parts.map(r => r.top)) - 12;
      const r = Math.max(...parts.map(r => r.right)) + 12, b = Math.max(...parts.map(r => r.bottom)) + 12;
      return { x: x + scrollX, y: y + scrollY, width: r - x, height: b - y };
    }, i);
    await page.screenshot({ path: `${out}/${name}.png`, clip, captureBeyondViewport: true });
  }
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
