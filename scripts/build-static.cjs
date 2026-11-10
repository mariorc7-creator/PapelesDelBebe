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
    html = html.replace(/<\/head>/i, '<meta name="application-name" content="Papeles del Bebé">\n</head>');
  }
  if (!/<meta[^>]+property=["']og:site_name["']/i.test(html)) {
    html = html.replace(/<\/head>/i, '<meta property="og:site_name" content="Papeles del Bebé">\n</head>');
  }
  html = html.replace(/<link\s+rel=["']icon["'][^>]*>/gi, '');
  html = html.replace(/<\/head>/i, '<link rel="icon" type="image/svg+xml" sizes="any" href="/logo-papeles-bebe.svg">\n</head>');
  if (rel === 'index.html' && !html.includes('"@type":"WebSite"')) {
    html = html.replace(/<\/head>/i, '<script type="application/ld+json">{"@context":"https://schema.org","@type":"WebSite","name":"Papeles del Bebé","alternateName":"Papeles del Bebe","url":"https://www.papelesdelbebe.es/"}</script>\n</head>');
  }

  // Enlaces internos directos hacia las versiones perennes.
  for (const [oldSlug, newSlug] of EVERGREEN_MOVES) {
    html = html.split('href="/' + oldSlug + '/"').join('href="/' + newSlug + '/"');
    html = html.split('href="https://www.papelesdelbebe.es/' + oldSlug + '/"').join('href="https://www.papelesdelbebe.es/' + newSlug + '/"');
  }

  // Plantilla editorial única: adaptar guías antiguas sin modificar su contenido ni SEO.
  // Herramientas, formularios y páginas legales conservan su estructura funcional.
  if (!/^(herramientas|aviso-legal|privacidad|cookies|terminos|gestoria|mi-panel|checklist|premium)\//.test(rel) &&
      /<main>\s*<article class="contenido-informativo">/i.test(html) &&
      !/<section class="hero(?:\s|")/i.test(html)) {
    const match = html.match(/<main>\s*<article class="contenido-informativo">([\s\S]*?)<\/article>\s*<\/main>/i);
    if (match) {
      let article = match[1];
      const h1 = article.match(/<h1[^>]*>[\s\S]*?<\/h1>/i);
      if (h1) {
        const crumb = article.match(/^\s*<p>\s*<a href="\/">Inicio<\/a>[\s\S]*?<\/p>/i);
        if (crumb) article = article.replace(crumb[0], '');
        article = article.replace(h1[0], '');
        const intro = article.match(/^\s*<p>([\s\S]*?)<\/p>/i);
        let subtitle = '';
        if (intro) {
          subtitle = intro[1];
          article = article.replace(intro[0], '');
        }
        const badge = rel.includes('rioja') ? '👨‍👩‍👧‍👦 La Rioja' :
          rel.includes('valenciana') || rel.includes('valencia') ? '👶 Comunidad Valenciana' :
          rel.includes('navarra') ? '👶 Navarra' :
          rel.includes('andalucia') ? '👶 Andalucía' : '👶 Guía para familias';
        const hero = '<main><section class="hero seo-page"><div class="badge">' + badge +
          '</div>' + h1[0] + (subtitle ? '<p class="subtitle">' + subtitle + '</p>' : '') +
          '<section class="contenido-informativo seo-article">' + article + '</section></section></main>';
        html = html.replace(match[0], hero);
      }
    }
  }

  // Fecha editorial real de las guías revisadas en esta ronda (02/11/2026).
  // No modificar fechas de páginas que no se han revisado.
  const revisedPages = new Set([
    'titulo-familia-monoparental-navarra/index.html',
    'tarjeta-sanitaria-bebe-la-rioja/index.html',
    'titulo-familia-numerosa-murcia/index.html',
    'deduccion-nacimiento-castilla-la-mancha-2026/index.html',
    'tarjeta-sanitaria-bebe-comunitat-valenciana/index.html',
    'tarjeta-sanitaria-bebe-galicia/index.html',
    'titulo-familia-numerosa-andalucia/index.html',
    'titulo-familia-numerosa-la-rioja/index.html',
    'titulo-familia-monoparental-comunitat-valenciana/index.html',
    'ayuda-partos-multiples-aragon/index.html',
    'ayuda-partos-multiples-aragon-2026/index.html',
    'comunidades/andalucia/index.html',
    'comunidades/navarra/index.html',
    'comunidades/cataluna/index.html',
    'comunidades/extremadura/index.html'
  ]);
  if (revisedPages.has(rel)) {
    // Eliminar los bloques de revisión anteriores para evitar dos fechas contradictorias.
    html = html.replace(/<p\b[^>]*class=["'][^"']*revision-sitio[^"']*["'][^>]*>[\s\S]*?<\/p>/gi, '');
    html = html.replace(/<p>\s*Revisado:\s*\d{1,2}\/\d{1,2}\/\d{4}\.?(?:\s*)<\/p>/gi, '');
    html = html.replace(/<div\b[^>]*class=["'][^"']*aviso-importante[^"']*["'][^>]*>\s*Revisado el [^<]*<\/div>/gi, '');
    const isAragonMultiple = rel === 'ayuda-partos-multiples-aragon-2026/index.html' || rel === 'ayuda-partos-multiples-aragon/index.html';
    const revisionDate = isAragonMultiple ? '2026-11-03' : '2026-11-02';
    const revisionLabel = isAragonMultiple ? '3 de noviembre de 2026' : '2 de noviembre de 2026';
    const revision = '<p class="revision revision-sitio">Última revisión: <time datetime="' + revisionDate + '">' + revisionLabel + '</time></p>';
    if (/<\/main>/i.test(html)) html = html.replace(/<\/main>/i, revision + '</main>');
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
  // Legacy sitemaps must never be published; only the generated sitemap.xml is authoritative.
  if (/^sitemap[^/]*\.xml$/i.test(rel)) return true;
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
    // Solo fechas editoriales explícitas; otros <time> pueden indicar plazos o eventos.
    // Una fecha ausente es preferible a un <lastmod> engañoso.
    const dates = [];
    const revision = /<(?:p|div|span)\b[^>]*class=["'][^"']*\b(?:revision|revision-sitio|fecha-revision|last-updated)\b[^"']*["'][^>]*>[\s\S]*?<\/\s*(?:p|div|span)>/gi;
    for (const block of html.matchAll(revision)) {
      for (const time of block[0].matchAll(/<time\b[^>]*datetime=["'](\d{4}-\d{2}-\d{2})["'][^>]*>/gi)) dates.push(time[1]);
    }
    // dateModified se acepta únicamente si existe como dato estructurado.
    for (const script of html.matchAll(/<script\b[^>]*type=["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi)) {
      try {
        const data = JSON.parse(script[1]);
        const visit = node => {
          if (!node || typeof node !== 'object') return;
          if (typeof node.dateModified === 'string') dates.push(node.dateModified.slice(0, 10));
          for (const value of Object.values(node)) if (typeof value === 'object') visit(value);
        };
        visit(data);
      } catch (_) { /* JSON-LD inválido: no inferir fecha */ }
    }
    const today = new Date().toISOString().slice(0, 10);
    const valid = dates.filter(d => /^\d{4}-\d{2}-\d{2}$/.test(d) && !Number.isNaN(Date.parse(d)) && d <= today);
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


// Control de regresión SEO para las páginas que ya han demostrado tráfico.
// Falla el build antes de publicar una canonical, redirección o sitemap incoherente.
function validatePrioritySeo() {
  const host = 'https://www.papelesdelbebe.es';
  const priority = ['ayuda-nacimiento-asturias', 'ayuda-nacimiento-cataluna'];
  const xml = fs.readFileSync(path.join(OUT, 'sitemap.xml'), 'utf8');
  const redirects = JSON.parse(fs.readFileSync(path.join(ROOT, 'vercel.json'), 'utf8')).redirects || [];
  const errors = [];
  for (const slug of priority) {
    const file = path.join(OUT, slug, 'index.html');
    if (!fs.existsSync(file)) { errors.push(slug + ': no existe HTML'); continue; }
    const html = fs.readFileSync(file, 'utf8');
    const url = host + '/' + slug + '/';
    const canonical = html.match(/<link\b(?=[^>]*\brel=["']canonical["'])[^>]*\bhref=["']([^"']+)["'][^>]*>/i);
    if (!canonical || canonical[1] !== url) errors.push(slug + ': canonical incorrecta');
    if (/<meta\b[^>]*name=["']robots["'][^>]*content=["'][^"']*noindex/i.test(html)) errors.push(slug + ': noindex');
    if (!xml.includes('<loc>' + url + '</loc>')) errors.push(slug + ': ausente del sitemap');
    if (redirects.some(r => r.source.replace(/\/$/, '') === '/' + slug)) errors.push(slug + ': redirige la URL canonica');
  }
  const oldCataluna = '/ayuda-nacimiento-cataluna-2026/';
  if (!redirects.some(r => r.source === oldCataluna && r.destination === '/ayuda-nacimiento-cataluna/' && r.permanent === true)) {
    errors.push('Cataluña: falta redireccion permanente desde URL antigua');
  }
  if (xml.includes('<loc>' + host + oldCataluna + '</loc>')) errors.push('Cataluña: URL antigua en sitemap');
  const hub = fs.readFileSync(path.join(OUT, 'ayudas-nacimiento', 'index.html'), 'utf8');
  for (const slug of priority) if (!hub.includes('href="/' + slug + '/"')) errors.push('Hub ayudas: falta enlace directo a ' + slug);
  if (hub.includes('href="' + oldCataluna + '"')) errors.push('Hub ayudas: enlace a URL antigua de Cataluña');
  if (errors.length) throw new Error('Control SEO prioritario fallido:\\n' + errors.join('\\n'));
  console.log('Control SEO prioritario OK: Asturias y Cataluña, canonicals, sitemap, redirección y enlaces.');
}


function validatePublishedSitemap() {
  const xml = fs.readFileSync(path.join(OUT, 'sitemap.xml'), 'utf8');
  const robots = fs.readFileSync(path.join(OUT, 'robots.txt'), 'utf8');
  const config = JSON.parse(fs.readFileSync(path.join(ROOT, 'vercel.json'), 'utf8'));
  const host = 'https://www.papelesdelbebe.es';
  const urls = [...xml.matchAll(/<loc>([^<]+)<\/loc>/g)].map(m => m[1]);
  const errors = [];
  const publishedSitemaps = fs.readdirSync(OUT).filter(name => /^sitemap[^/]*\.xml$/i.test(name));
  if (publishedSitemaps.length !== 1 || publishedSitemaps[0] !== 'sitemap.xml') {
    errors.push('Solo debe publicarse sitemap.xml; encontrados: ' + publishedSitemaps.join(', '));
  }
  if (!xml.startsWith('<?xml') || !xml.includes('<urlset ') || !xml.includes('</urlset>')) errors.push('XML sin estructura urlset');
  if (!urls.length) errors.push('Sitemap sin URLs');
  if (new Set(urls).size !== urls.length) errors.push('URLs duplicadas');
  const redirectPaths = new Set((config.redirects || []).filter(r => r.source && !r.source.includes(':')).map(r => r.source.replace(/\/$/, '')));
  for (const url of urls) {
    if (!url.startsWith(host + '/')) { errors.push('Host ajeno: ' + url); continue; }
    const slug = url.slice(host.length).replace(/^\//, '').replace(/\/$/, '');
    if (redirectPaths.has('/' + slug)) errors.push('URL redirigida en sitemap: ' + url);
    const file = path.join(OUT, slug, 'index.html');
    if (!fs.existsSync(file)) errors.push('HTML inexistente: ' + url);
  }
  const announced = robots.split('\n').filter(line => line.trim().toLowerCase().startsWith('sitemap:')).map(line => line.split(':').slice(1).join(':').trim());
  if (announced.length !== 1 || announced[0] !== host + '/sitemap.xml') errors.push('robots.txt debe anunciar solo sitemap.xml');
  if (errors.length) throw new Error('Validacion sitemap fallida:\\n' + errors.slice(0, 30).join('\\n'));
  console.log('Sitemap OK: ' + urls.length + ' URLs, sin duplicados ni redirecciones declaradas.');
}

copyAll();
generateEvergreenRegionalPages();
generateSitemap();
audit(OUT);
validatePrioritySeo();
validatePublishedSitemap();
