// Visual smoke tests: static site, no production writes. Run with a local HTTP server.
import { chromium } from '../superagente/node_modules/playwright/index.mjs';
import fs from 'node:fs';
import path from 'node:path';

const base = process.env.TEST_BASE_URL || 'http://127.0.0.1:8765';
const routes = ['/', '/tramites-bebe/', '/ayudas-nacimiento/', '/mi-panel/', '/herramientas/', '/ayuda-nacimiento-cataluna/', '/ayuda-natalidad-madrid/'];
const widths = [320, 375, 430, 768, 1440];
const out = 'superagente/mobile-artifacts';
fs.mkdirSync(out, { recursive: true });
const browser = await chromium.launch({ headless: true });
const failures = [];
try {
  for (const route of routes) {
    for (const width of widths) {
      const page = await browser.newPage({ viewport: { width, height: 900 }, deviceScaleFactor: 1 });
      try {
        const response = await page.goto(base + route, { waitUntil: 'domcontentloaded', timeout: 30000 });
        if (!response || response.status() >= 400) throw new Error('HTTP ' + response?.status());
        await page.evaluate(() => document.fonts?.ready);
        const result = await page.evaluate(() => ({
          documentWidth: document.documentElement.scrollWidth,
          viewportWidth: document.documentElement.clientWidth,
          title: document.title,
          hasMain: !!document.querySelector('main, [role="main"]'),
          brokenImages: [...document.images].filter(i => i.complete && i.naturalWidth === 0).map(i => i.src).slice(0, 10)
        }));
        if (result.documentWidth > result.viewportWidth + 2) failures.push({ route, width, problem: 'horizontal_overflow', ...result });
        if (!result.title.trim()) failures.push({ route, width, problem: 'missing_title' });
        if (result.brokenImages.length) failures.push({ route, width, problem: 'broken_images', images: result.brokenImages });
        const slug = route.replaceAll('/', '_') || 'home';
        await page.screenshot({ path: path.join(out, slug + '-' + width + '.png'), fullPage: true, animations: 'disabled' });
      } catch (e) {
        failures.push({ route, width, problem: String(e) });
      } finally {
        await page.close();
      }
    }
  }
} finally {
  await browser.close();
}
fs.writeFileSync('superagente/mobile-results.json', JSON.stringify({ failures, routes, widths }, null, 2));
console.log('Mobile tests: ' + (routes.length * widths.length) + '; failures: ' + failures.length);
if (failures.length) { console.error(JSON.stringify(failures, null, 2)); process.exitCode = 1; }
