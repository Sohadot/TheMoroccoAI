// Renders the page written by og_image.py (argv[2]) to a PNG of exactly 1200 x 630 (argv[3], default
// assets/social/themoroccoai-og.png). Usage: node tools/social/render.js OUT.html [PNG]
// Needs Node with Playwright and a Chromium browser; not run by the build or CI (the PNG is committed).
const path = require('path');
const { chromium } = require('playwright');
(async () => {
  const root = path.resolve(__dirname, '..', '..');
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1200, height: 630 }, deviceScaleFactor: 1 });
  if (!process.argv[2]) throw new Error('usage: node render.js OUT.html [PNG]');
  await page.goto('file://' + path.resolve(process.argv[2]));
  await page.evaluate(() => document.fonts.ready);
  const missing = await page.evaluate(() => ['Cormorant Garamond', 'DM Mono'].filter(f => !document.fonts.check(`16px "${f}"`)));
  if (missing.length) throw new Error('fonts not loaded: ' + missing);
  const out = process.argv[3] || path.join(root, 'assets', 'social', 'themoroccoai-og.png');
  await page.screenshot({ path: out, clip: { x: 0, y: 0, width: 1200, height: 630 } });
  await browser.close();
  console.log('wrote ' + out);
})().catch(e => { console.error(e); process.exit(1); });
