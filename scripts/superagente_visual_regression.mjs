// Check critical responsive layout invariants between source and isolated editorial preview.
// This does not replace human screenshot review or approve publication.
import { chromium } from '../superagente/node_modules/playwright/index.mjs';
import fs from 'node:fs';

const BASELINE = 'http://127.0.0.1:8765';
const PROPOSED = 'http://127.0.0.1:8766';
const routes = ['/ayuda-nacimiento-cataluna/', '/ayuda-natalidad-madrid/'];
const widths = [320, 375, 430, 768, 1440];
const selectors = ['header', 'nav', 'main', 'footer', 'h1'];
const report = { routes, widths, comparisons: [], failures: [], warning: 'Geometric checks and screenshots do not replace visual/editorial approval.' };
const browser = await chromium.launch({ headless: true });
async function inspect(page, url) {
  const response = await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
  if (!response || response.status() >= 400) throw new Error('HTTP ' + response?.status());
  await page.evaluate(() => document.fonts?.ready);
  return page.evaluate((selectors) => {
    const rect = (el) => {
      const r = el.getBoundingClientRect();
      return { x: r.x, y: r.y, width: r.width, height: r.height };
    };
    const nodes = {};
    for (const s of selectors) {
      const el = document.querySelector(s);
      nodes[s] = el ? { rect: rect(el), display: getComputedStyle(el).display } : null;
    }
    return {
      viewport: document.documentElement.clientWidth,
      scrollWidth: document.documentElement.scrollWidth,
      nodes,
      images: [...document.images].filter(i => i.complete && i.naturalWidth === 0).length,
      links: document.querySelectorAll('a[href]').length,
      buttons: document.querySelectorAll('button').length,
      title: document.title,
      canonical: document.querySelector('link[rel="canonical"]')?.href || null,
      headings: [...document.querySelectorAll('h1,h2,h3')].map(el => el.tagName).join(','),
      stylesheets: [...document.querySelectorAll('link[rel="stylesheet"]')].map(el => el.getAttribute('href')).sort(),
    };
  }, selectors);
}
try {
  for (const route of routes) {
    for (const width of widths) {
      const context = await browser.newContext({ viewport: { width, height: 900 }, deviceScaleFactor: 1, reducedMotion: 'reduce' });
      const page = await context.newPage();
      const failure = (reason, detail) => report.failures.push({ route, width, reason, detail });
      try {
        const before = await inspect(page, BASELINE + route);
        const after = await inspect(page, PROPOSED + route);
        if (before.scrollWidth > before.viewport + 2 || after.scrollWidth > after.viewport + 2) {
          failure('horizontal_overflow', { before: before.scrollWidth, after: after.scrollWidth, viewport: before.viewport });
        }
        if (before.images !== after.images) failure('broken_images_changed', { before: before.images, after: after.images });
        for (const key of ['title', 'canonical', 'headings', 'links', 'buttons', 'stylesheets']) {
          const a = typeof before[key] === 'object' ? JSON.stringify(before[key]) : before[key];
          const b = typeof after[key] === 'object' ? JSON.stringify(after[key]) : after[key];
          if (a !== b) failure('structure_changed_' + key, { before: a, after: b });
        }
        for (const sel of selectors) {
          const a = before.nodes[sel], b = after.nodes[sel];
          if (Boolean(a) !== Boolean(b)) { failure('node_presence_changed', sel); continue; }
          if (!a) continue;
          if (a.display !== b.display) failure('display_changed', sel);
          // Text changes can increase height; only protect widths and horizontal placement.
          if (Math.abs(a.rect.x - b.rect.x) > 2 || Math.abs(a.rect.width - b.rect.width) > 2) {
            failure('horizontal_geometry_changed', { selector: sel, before: a.rect, after: b.rect });
          }
        }
        report.comparisons.push({ route, width, before, after, outcome: 'checked' });
      } catch (err) {
        failure('browser_error', String(err));
      } finally {
        await context.close();
      }
    }
  }
} finally {
  await browser.close();
}
fs.mkdirSync('superagente', { recursive: true });
fs.writeFileSync('superagente/visual-regression-results.json', JSON.stringify(report, null, 2));
console.log('Editorial visual regression: ' + report.comparisons.length + ' pairs; failures: ' + report.failures.length);
if (report.failures.length) {
  console.error(JSON.stringify(report.failures, null, 2));
  process.exitCode = 1;
}
