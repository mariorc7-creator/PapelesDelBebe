const fs = require('fs');
const path = require('path');

const ROOT = process.cwd();
const OUT = path.join(ROOT, 'dist');
const GLOBAL_UI = '<script src="/global-ui.js?v=20261020-13" defer></script>';
const FOOTER = `<footer class="pb-global-footer" data-pb-global-footer="1"><div class="footer-contenido"><div class="logo">Papeles del <span>Bebé</span></div><p>Menos papeleo. Más tiempo para tu bebé.</p><p class="metodologia-footer"><a href="/metodologia/">Metodología</a> · <a href="/privacidad/">Privacidad</a></p><p class="footer-copy">© 2026 Papeles del Bebé</p></div></footer>`;

function applyPageFixes(html, relPath) {
  const rel = relPath.replace(/\\/g, '/');
  // Preserve enlaces internos directos tras la migración gradual a URLs perennes.
  const permalinkMoves = {
    '/tarxeta-benvida-2026/': '/tarxeta-benvida/',
    '/ayuda-nacimiento-valencia-2026/': '/ayuda-nacimiento-valencia/',
    '/permiso-nacimiento-cuidado-menor-2026/': '/permiso-nacimiento-cuidado-menor/',
    '/ayuda-nacimiento-cataluna-2026/': '/ayuda-nacimiento-cataluna/',
    '/ayudas-nacimiento-cataluna-2026/': '/ayudas-nacimiento-cataluna/',
    '/ca/ajut-naixement-catalunya-2026/': '/ca/ajut-naixement-catalunya/'
  };
  for (const [oldPath,newPath] of Object.entries(permalinkMoves)) {
    html=html.split('href="'+oldPath+'"').join('href="'+newPath+'"');
  }

  // Identidad de marca consistente en los resultados de Google.
  // Google puede elegir otro nombre; WebSite y og:site_name son señales, no garantías.
  if (!/<meta[^>]+name=["']application-name["']/i.test(html)) {
    html = html.replace(/<\/head>/i, '<meta name="application-name" content="Papeles del Bebé">\\n</head>');
  }
  if (!/<meta[^>]+property=["']og:site_name["']/i.test(html)) {
    html = html.replace(/<\/head>/i, '<meta property="og:site_name" content="Papeles del Bebé">\\n</head>');
  }
  html = html.replace(/<link\\s+rel=["']icon["'][^>]*>/gi, '');
  html = html.replace(/<\/head>/i, '<link rel="icon" type="image/svg+xml" sizes="any" href="/logo-papeles-bebe.svg">\\n</head>');
  if (rel === 'index.html' && !html.includes('"@type":"WebSite"')) {
    html = html.replace(/<\/head>/i, '<script type="application/ld+json">{"@context":"https://schema.org","@type":"WebSite","name":"Papeles del Bebé","alternateName":"Papeles del Bebe","url":"https://www.papelesdelbebe.es/"}</script>\\n</head>');
  }

  // Enlaces internos directos hacia las versiones perennes.
  for (const [oldSlug, newSlug] of EVERGREEN_MOVES) {
    html = html.split('href="/' + oldSlug + '/"').join('href="/' + newSlug + '/"');
    html = html.split('href="https://www.papelesdelbebe.es/' + oldSlug + '/"').join('href="https://www.papelesdelbebe.es/' + newSlug + '/"');
  }

  // Retirar la promoción del checklist antiguo de todas las páginas generadas.
  // El panel de trámites es el destino vigente; las herramientas imprimibles se conservan.
  if (/^comunidades\/[^/]+\/index\.html$/.test(rel)) {
    html = html.replace(/<a\b[^>]*href=["']\/checklist\/\?comunidad=[^"']*["'][^>]*>[\s\S]*?<\/a>/gi, '');
    html = html.replace(/<a\b[^>]*href=["']\/checklist\/["'][^>]*>\s*Mi checklist\s*<\/a>/gi, '');
  }
  // No dirigir al usuario a una experiencia de checklist que ya no promocionamos.
  html = html.replace(/href=(["'])\/checklist\/(?:\?comunidad=[^"']*)?\1/gi, 'href="/mi-panel/"');
  html = html.replace(/(<a\b[^>]*href=["']\/mi-panel\/["'][^>]*>)\s*Crear mi checklist personalizada[^<]*(<\/a>)/gi, '$1Abrir mis trámites$2');
  html = html.replace(/(<a\b[^>]*href=["']\/mi-panel\/["'][^>]*>)\s*Mi checklist\s*(<\/a>)/gi, '$1Mis trámites$2');
  html = html.replace(/(<a\b[^>]*href=["']\/mi-panel\/["'][^>]*>)\s*lista de ayudas y trámites\s*(<\/a>)/gi, '$1panel de trámites$2');

  if (rel === 'pack-empadronamiento/index.html') {
    html = html.replace(/<script src="\/pack-empadronamiento\/(?:fix|review-v6|municipal-universal|capitales-only)\.js[^>]*><\/script>\s*/gi, '');
    html = html.replace(/<\/body>/i, '<script src="/pack-empadronamiento/review-v6.js?v=20261015-11" defer></script>\n<script src="/pack-empadronamiento/municipal-universal.js?v=20261016-2" defer></script>\n<script src="/pack-empadronamiento/capitales-only.js?v=20261016-1" defer></script>\n<script src="/pack-empadronamiento/capitales-ux.js?v=20261020-1" defer></script>\n</body>');
  }
  return html;
}

function ensureDir(dir) { fs.mkdirSync(dir, { recursive: true }); }
function rmDir(dir) { if (fs.existsSync(dir)) fs.rmSync(dir, { recursive: true, force: true }); }
function walk(dir, cb) {
  for (const name of fs.readdirSync(dir)) {
    const full = path.join(dir, name);
    const st = fs.statSync(full);
    if (st.isDirectory()) walk(full, cb); else cb(full);
  }
}
function shouldSkip(rel) {
  return rel.startsWith('.git/') || rel.startsWith('node_modules/') || rel.startsWith('dist/') || rel.startsWith('.vercel/');
}
function copyAll() {
  rmDir(OUT); ensureDir(OUT);
  walk(ROOT, full => {
    const rel = path.relative(ROOT, full).replace(/\\/g, '/');
    if (shouldSkip(rel)) return;
    const dest = path.join(OUT, rel); ensureDir(path.dirname(dest));
    if (/\.html$/i.test(rel)) {
      let html = fs.readFileSync(full, 'utf8');
      if (!html.includes('/global-ui.js')) html = html.replace(/<\/body>/i, `${GLOBAL_UI}\n</body>`);
      html = applyPageFixes(html, rel);
      fs.writeFileSync(dest, html);
    } else fs.copyFileSync(full, dest);
  });
}
function audit(dir) {
  const failures = []; const warnings = [];
  walk(dir, full => {
    const rel = path.relative(dir, full).replace(/\\/g, '/');
    if (/\.html$/i.test(rel)) {
      const html = fs.readFileSync(full, 'utf8');
      if (!/<title>[^<]+<\/title>/i.test(html)) failures.push(`${rel}: sin <title>`);
      if (!/<meta[^>]+name=["']description["'][^>]+content=["'][^"']+/i.test(html)) warnings.push(`${rel}: sin meta description`);
      if (!/rel=["']canonical["']/i.test(html)) warnings.push(`${rel}: sin canonical`);
      if (!html.includes('/global-ui.js')) warnings.push(`${rel}: sin global-ui.js`);
      const suspicious=(html.match(/href=["']#['"]/gi)||[]).length;
      if (suspicious) warnings.push(`${rel}: ${suspicious} enlace(s) placeholder`);
      if (rel === 'pack-empadronamiento/index.html') {
        if (!html.includes('https://sede.madrid.es/UnidadesDescentralizadas/UDCEstadistica/TramitesMunicipales/Ficheros/Hoja_padronal.pdf')) failures.push(`${rel}: falta enlace al PDF oficial`);
        if (!html.includes('/pack-empadronamiento/review-v6.js?v=20261015-11')) failures.push(`${rel}: sin verificador PDF v11`);
        if (!html.includes('/pack-empadronamiento/municipal-universal.js?v=20261016-2')) failures.push(`${rel}: sin motor municipal universal v20261016-2`);
        if (!html.includes('/pack-empadronamiento/capitales-only.js?v=20261016-1')) failures.push(`${rel}: sin limitador a capitales`);
        if (html.includes('/pack-empadronamiento/fix.js')) failures.push(`${rel}: sigue cargando verificador antiguo`);
      }
    }
  });
  if (warnings.length) console.warn('WARNINGS:\n' + warnings.join('\n'));
  if (failures.length) { console.error('FAILURES:\n' + failures.join('\n')); process.exit(1); }
  console.log(`Build OK: ${dir}`);
}


// Publicar URLs permanentes conservando el contenido de las guías existentes.
const EVERGREEN_MOVES = [
  ['autonomos-permiso-nacimiento-2026', 'autonomos-permiso-nacimiento'],
  ['ayuda-familias-monoparentales-navarra-2026', 'ayuda-familias-monoparentales-navarra'],
  ['ayuda-natalidad-extremadura-2026', 'ayuda-natalidad-extremadura'],
  ['ayuda-pago-unico-nacimiento-1000-euros-2026', 'ayuda-pago-unico-nacimiento-1000-euros'],
  ['ayuda-partos-multiples-andalucia-2026', 'ayuda-partos-multiples-andalucia'],
  ['ayuda-partos-multiples-aragon-2026', 'ayuda-partos-multiples-aragon'],
  ['ayudas-adopcion-acogimiento-2026', 'ayudas-adopcion-acogimiento'],
  ['ayudas-familias-murcia-2026', 'ayudas-familias-murcia'],
  ['bono-nacimiento-castilla-leon-2026', 'bono-nacimiento-castilla-leon'],
  ['cheque-bebe-madrid-2026', 'cheque-bebe-madrid'],
  ['deduccion-guarderia-1000-euros-2026', 'deduccion-guarderia-1000-euros'],
  ['deduccion-nacimiento-baleares-2026', 'deduccion-nacimiento-baleares'],
  ['deduccion-nacimiento-canarias-2026', 'deduccion-nacimiento-canarias'],
  ['deduccion-nacimiento-cantabria-2026', 'deduccion-nacimiento-cantabria'],
  ['deduccion-nacimiento-castilla-la-mancha-2026', 'deduccion-nacimiento-castilla-la-mancha'],
  ['deduccion-nacimiento-comunitat-valenciana-2026', 'deduccion-nacimiento-comunitat-valenciana'],
  ['deduccion-nacimiento-la-rioja-2026', 'deduccion-nacimiento-la-rioja'],
  ['familias-ceuta-2026', 'familias-ceuta'],
  ['familias-melilla-2026', 'familias-melilla'],
  ['familias-monoparentales-ayudas-2026', 'familias-monoparentales-ayudas'],
  ['familias-numerosas-ayudas-2026', 'familias-numerosas-ayudas'],
  ['permiso-lactancia-2026', 'permiso-lactancia'],
  ['ayudas-nacimiento-cataluna-2026', 'ayudas-nacimiento-cataluna'],
  ['ca/ajut-naixement-catalunya-2026', 'ca/ajut-naixement-catalunya']
];
function generateEvergreenRegionalPages() {
  for (const [oldSlug, newSlug] of EVERGREEN_MOVES) {
    const oldFile = path.join(OUT, oldSlug, 'index.html');
    if (!fs.existsSync(oldFile)) throw new Error('Falta página origen: ' + oldSlug);
    const newFile = path.join(OUT, newSlug, 'index.html');
    if (fs.existsSync(newFile)) throw new Error('Ya existe destino: ' + newSlug);
    let html = fs.readFileSync(oldFile, 'utf8');
    html = html.split('https://www.papelesdelbebe.es/' + oldSlug + '/').join('https://www.papelesdelbebe.es/' + newSlug + '/');
    html = html.split('/' + oldSlug + '/').join('/' + newSlug + '/');
    html = applyPageFixes(html, newSlug + '/index.html');
    ensureDir(path.dirname(newFile));
    fs.writeFileSync(newFile, html);
  }
  // Eliminar del sitemap las páginas históricas que ya redirigen.
}

function generateSitemap() {
  const host = 'https://www.papelesdelbebe.es';
  const excluded = new Set([
    'ayuda-nacimiento-cataluna-2026','ayuda-nacimiento-valencia-2026',
    'permiso-nacimiento-cuidado-menor-2026','tarxeta-benvida-2026',
    'ayudas-nacimiento-cataluna-2026','ca/ajut-naixement-catalunya-2026',
    'mi-plan','herramientas/que-me-falta'
  ]);
  for (const [oldSlug] of EVERGREEN_MOVES) excluded.add(oldSlug);
  const urls = [];
  function contentLastmod(html) {
    const matches = [...html.matchAll(/<time\b[^>]*datetime=["'](\d{4}-\d{2}-\d{2})["'][^>]*>/gi), ...html.matchAll(/"dateModified"\s*:\s*"(\d{4}-\d{2}-\d{2})"/gi)].map(m => m[1]);
    const today = new Date().toISOString().slice(0, 10);
    const valid = matches.filter(d => !Number.isNaN(Date.parse(d)) && d <= today);
    return valid.length ? valid.sort().at(-1) : null;
  }
  walk(OUT, full => {
    const rel = path.relative(OUT, full).replace(/\\/g, '/');
    if (rel !== 'index.html' && !rel.endsWith('/index.html')) return;
    const slug = rel === 'index.html' ? '' : rel.slice(0, -'/index.html'.length);
    if (excluded.has(slug) || /^(premium|gestoria|checklist\/completada)(\/|$)/.test(slug)) return;
    const html = fs.readFileSync(full, 'utf8');
    if (/<meta[^>]+name=["']robots["'][^>]+content=["'][^"']*noindex/i.test(html) ||
        /<meta[^>]+content=["'][^"']*noindex[^"']*["'][^>]+name=["']robots/i.test(html)) return;
    const canonical = html.match(/<link[^>]+rel=["']canonical["'][^>]+href=["']([^"']+)/i) ||
                      html.match(/<link[^>]+href=["']([^"']+)["'][^>]+rel=["']canonical/i);
    const url = host + (slug ? '/' + slug + '/' : '/');
    if (canonical && canonical[1].replace(/\/$/, '') !== url.replace(/\/$/, '')) return;
    urls.push({url, lastmod: contentLastmod(html)});
  });
  urls.sort((a,b) => a.url.localeCompare(b.url));
  const escapeXml = value => value.replace(/&/g, '&amp;').replace(/</g, '&lt;');
  const xml = '<?xml version="1.0" encoding="UTF-8"?>\n' +
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
    urls.map(({url,lastmod}) => '  <url><loc>' + escapeXml(url) + '</loc>' + (lastmod ? '<lastmod>' + lastmod + '</lastmod>' : '') + '</url>').join('\n') +
    '\n</urlset>\n';
  fs.writeFileSync(path.join(OUT, 'sitemap.xml'), xml);
  console.log('Sitemap generado: ' + urls.length + ' URLs canonicas.');
}

copyAll();
generateEvergreenRegionalPages();
generateSitemap();
audit(OUT);
