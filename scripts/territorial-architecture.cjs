// HTML estático accesible para Google y para lectores sin JavaScript.
// No crea páginas ni inventa importes, plazos o ayudas vigentes.
const fs = require('fs');
const path = require('path');
const { TERRITORIES, TERRITORY_BY_SLUG, TERRITORY_BY_GUIDE, regionalUrl } = require('./territories.cjs');
const HOST = 'https://www.papelesdelbebe.es';

const esc = value => String(value).replace(/[&<>"']/g, c => ({
  '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'
}[c]));
function link(slug, label) {
  return '<li><a href="/' + esc(slug) + '/">' + esc(label) + '</a></li>';
}
function sourceExists(root, slug) {
  return fs.existsSync(path.join(root, slug, 'index.html'));
}
function renderCompactTerritorySelector() {
  const options = TERRITORIES.map(t =>
    '<option value="' + regionalUrl(t.slug) + '">' + esc(t.name) + '</option>'
  ).join('');
  return '<section class="pb-territory-compact" aria-labelledby="pb-choose-region">' +
    '<h2 id="pb-choose-region">Trámites según tu comunidad</h2>' +
    '<p>Los siete pasos son comunes a toda España. Consulta aquí los detalles autonómicos.</p>' +
    '<div class="pb-territory-compact-controls">' +
    '<label for="pb-territory-select" class="pb-territory-label">Tu comunidad</label>' +
    '<select id="pb-territory-select" name="comunidad" aria-label="Selecciona tu comunidad">' +
    '<option value="">Selecciona tu comunidad</option>' + options + '</select>' +
    '<button type="button" id="pb-territory-go">Ver trámites</button></div>' +
    '<a class="pb-territory-all" href="/comunidades/">Ver las 19 comunidades</a>' +
    '</section>';
}
function renderTerritorySelector(context) {
  const intro = context === 'guias-familias' ?
    'Elige dónde vives para consultar guías regionales. Las guías estatales siguen disponibles en esta página.' :
    context === 'ayudas-nacimiento' ?
    'Selecciona tu comunidad para localizar ayudas autonómicas y deducciones. Las prestaciones estatales se consultan también aquí.' :
    'Encuentra trámites y documentación específicos de tu territorio. Los siete pasos generales siguen siendo comunes en toda España.';
  const links = TERRITORIES.map(t => '<a href="' + regionalUrl(t.slug) + '">' + esc(t.name) + '<span aria-hidden="true">›</span></a>').join('');
  return '<section class="pb-territory-explorer" aria-labelledby="pb-territory-selector"><h2 id="pb-territory-selector">Información según tu comunidad autónoma</h2><p>' + intro + '</p><div class="pb-territory-grid">' + links + '</div></section>';
}
function foldDuplicateRegionalMenus(html, root) {
  // Los módulos antiguos «GUÍAS DESTACADAS» duplican los enlaces del HUB V4.1.
  // Conservamos los enlaces exclusivos dentro del HUB, sin borrar información legal.
  const sections = /<section\b[^>]*class="contenido-informativo"[^>]*>[\s\S]*?<\/section>/gi;
  const extras = [];
  let removed = 0;
  html = html.replace(sections, section => {
    if (!/GUÍAS DESTACADAS/i.test(section)) return section;
    removed++;
    for (const m of section.matchAll(/<a\b[^>]*href="(\/[^"]+)"[^>]*>([\s\S]*?)<\/a>/gi)) {
      const href = m[1].split('?')[0];
      const slug = href.replace(/^\/|\/$/g, '');
      if (!/^\/[a-z0-9/.-]+\/$/.test(href)) continue;
      if (['comunidades','tramites-bebe','ayudas-nacimiento','herramientas/buscador-ayudas','checklist','mi-panel'].includes(slug)) continue;
      if (!sourceExists(root, slug)) continue;
      const label = m[2].replace(/<[^>]*>/g,' ').replace(/\s+/g,' ').trim();
      if (label && !extras.some(x => x.slug === slug)) extras.push({slug,label});
    }
    return '';
  });
  if (removed > 1) throw Error('Más de un menú destacado previo en una comunidad');
  return {html, extras, removed};
}
function renderTerritoryHub(t, root, extraLinks = []) {
  const aids = t.aids.filter(slug => sourceExists(root, slug))
    .map(slug => link(slug, slug.startsWith('deduccion-') ? 'Deducción por nacimiento: requisitos y aplicación' :
      slug.startsWith('familias-') ? 'Información y ayudas familiares en ' + t.name :
      slug.startsWith('tarxeta-') ? 'Tarxeta Benvida: información y solicitud' : 'Ayuda autonómica: información y requisitos'));
  const guides = [
    t.health && ['tarjeta-sanitaria-bebe-' + t.health, 'Tarjeta sanitaria del recién nacido'],
    t.family && ['titulo-familia-numerosa-' + t.family, 'Título de familia numerosa']
  ].filter(Boolean).filter(([slug]) => sourceExists(root, slug))
    .map(([slug, label]) => link(slug, label));
  // Enlaces relevantes que el menú antiguo tenía y aún no están representados.
  const existing = new Set([
    ...t.aids, ...(t.health ? ['tarjeta-sanitaria-bebe-' + t.health] : []),
    ...(t.family ? ['titulo-familia-numerosa-' + t.family] : []),
    'registro-civil-bebe','alta-bebe-seguridad-social','permiso-nacimiento-cuidado-menor'
  ]);
  const otherLinks = extraLinks.filter(x => !existing.has(x.slug))
    .map(x => link(x.slug,x.label));
  const body = [
    '<div><h3>Ayudas y deducciones del territorio</h3>',
    aids.length ? '<ul>' + aids.join('') + '</ul>' : '<p>Consulta los recursos oficiales indicados en esta página y el buscador; no todas las ayudas existen en todas las comunidades.</p>',
    '</div><div><h3>Guías de ' + esc(t.name) + '</h3>',
    guides.length || otherLinks.length ? '<ul>' + guides.concat(otherLinks).join('') + '</ul>' : '<p>Consulta la información territorial existente y los trámites comunes para toda España.</p>',
    '</div><div><h3>Trámites comunes a toda España</h3><ul>',
    link('registro-civil-bebe','Registro Civil: inscripción del nacimiento'),
    link('alta-bebe-seguridad-social','Alta del bebé en la Seguridad Social'),
    link('permiso-nacimiento-cuidado-menor','Permiso por nacimiento y cuidado del menor'),
    '</ul></div>'
  ].join('');
  return '<section class="pb-regional-guide" aria-labelledby="pb-regional-guide-title"><h2 id="pb-regional-guide-title">Ayudas, guías y trámites del bebé en ' + esc(t.name) + '</h2><p>Accede a los contenidos específicos del territorio y separa los procedimientos autonómicos de los estatales. Comprueba en cada ficha la vigencia, los requisitos y el organismo responsable.</p><div class="pb-regional-cards">' + body + '</div></section>';
}
function addStyle(html) {
  return html.includes('href="/regional-hubs.css"') ? html :
    html.replace(/<\/head>/i, '<link rel="stylesheet" href="/regional-hubs.css">\n</head>');
}
function injectAfterIntro(html, section, territorial) {
  const start = html.indexOf('<main');
  const h1 = html.indexOf('<h1', start);
  if (start < 0 || h1 < 0) throw Error('HUB sin main/h1');
  if (territorial) {
    // El build elimina CTA antiguos del checklist; el subtítulo permanece.
    // Insertar después del H1 y del subtítulo, antes del resto del artículo.
    const subtitle = /<p\b[^>]*class="subtitle"[^>]*>[\s\S]*?<\/p>/gi;
    subtitle.lastIndex = h1;
    const match = subtitle.exec(html);
    if (!match) throw Error('HUB regional sin subtítulo reconocible');
    const at = match.index + match[0].length;
    return html.slice(0, at) + '\n' + section + html.slice(at);
  }
  // En las tres páginas de entrada: colocar después del hero completo,
  // nunca como contenido anidado dentro de su H1 o su hero.
  const tags = /<\/?section\b[^>]*>/gi;
  tags.lastIndex = h1;
  let depth = 1;
  for (const match of html.slice(h1).matchAll(/<\/?section\b[^>]*>/gi)) {
    depth += match[0].startsWith('</') ? -1 : 1;
    if (depth === 0) {
      const at = h1 + match.index + match[0].length;
      return html.slice(0, at) + '\n' + section + html.slice(at);
    }
  }
  throw Error('No se ha encontrado cierre del hero');
}
function applyTerritorialArchitecture(html, rel, root) {
  const slug = rel.replace(/\/index\.html$/, '').replace(/index\.html$/, '');
  if (slug === 'guias-familias' || slug === 'ayudas-nacimiento' || slug === 'tramites-bebe') {
    html = addStyle(html);
    if (slug === 'tramites-bebe') {
      html = html.replace(/<\/body>/i, '<script src="/regional-selector.js" defer></script></body>');
      return injectAfterIntro(html, renderCompactTerritorySelector(), false);
    }
    return injectAfterIntro(html, renderTerritorySelector(slug), false);
  }
  if (slug.startsWith('comunidades/')) {
    const territory = TERRITORY_BY_SLUG[slug.slice('comunidades/'.length)];
    if (territory) {
      const folded = foldDuplicateRegionalMenus(html, root);
      html = addStyle(folded.html);
      return injectAfterIntro(html, renderTerritoryHub(territory, root, folded.extras), true);
    }
  }
  const territorySlug = TERRITORY_BY_GUIDE[slug];
  if (!territorySlug) return html;
  const territory = TERRITORY_BY_SLUG[territorySlug];
  // Establecer breadcrumb territorial únicamente donde ya existía uno V4 explícito.
  if (html.includes('class="pb-guide-crumb"')) {
    const newCrumb = '<nav class="pb-guide-crumb" aria-label="Ruta de navegación" style="font-size:.86rem;line-height:1.6;margin:0 0 14px;color:#58647b"><a href="/">Inicio</a> › <a href="/comunidades/">Comunidades</a> › <a href="' + regionalUrl(territorySlug) + '">' + esc(territory.name) + '</a> › ' + (slug.startsWith('tarjeta-sanitaria') ? 'Tarjeta sanitaria' : 'Familia numerosa') + '</nav>';
    html = html.replace(/<nav\b[^>]*class="pb-guide-crumb"[^>]*>[\s\S]*?<\/nav>/i, newCrumb);
  }
  // Enlace contextual bidireccional antes de la fecha, nunca después.
  if (/<p\b[^>]*class="revision revision-sitio"/.test(html) && !html.includes('class="pb-regional-return"') &&
      !/rel=["']canonical["'][^>]*href=["'][^"']*-2026\//i.test(html)) {
    html = addStyle(html);
    html = html.replace(/(<p\b[^>]*class="revision revision-sitio")/i,
      '<p class="pb-regional-return"><a href="' + regionalUrl(territorySlug) + '">Ver todas las ayudas, guías y trámites de ' + esc(territory.name) + '</a></p>$1');
  }
  return html;
}
function validateTerritorialArchitecture(dist) {
  const errors = [];
  for (const t of TERRITORIES) {
    const file = path.join(dist, 'comunidades', t.slug, 'index.html');
    if (!fs.existsSync(file)) { errors.push('Falta HUB: ' + t.slug); continue; }
    const html = fs.readFileSync(file, 'utf8');
    if ((html.match(/class="pb-regional-guide"/g) || []).length !== 1)
      errors.push('HUB no es único: ' + t.slug);
    if (!html.includes('href="/regional-hubs.css"')) errors.push('CSS sin cargar: ' + t.slug);
    if (!html.includes('<h3>Trámites comunes a toda España</h3>')) errors.push('Faltan estatales: ' + t.slug);
    if (/GUÍAS DESTACADAS/i.test(html)) errors.push('Menú editorial duplicado en ' + t.slug);
    const hubPosition = html.indexOf('class="pb-regional-guide"');
    const reviewPosition = html.indexOf('class="revision revision-sitio"');
    if (hubPosition <= html.indexOf('<h1') || (reviewPosition >= 0 && hubPosition >= reviewPosition))
      errors.push('HUB fuera del artículo o después de la revisión: ' + t.slug);
    if (!html.includes('rel="canonical"') || !html.includes(regionalUrl(t.slug))) errors.push('Sin canonical: ' + t.slug);
  }
  for (const slug of ['guias-familias','ayudas-nacimiento','tramites-bebe']) {
    const html = fs.readFileSync(path.join(dist, slug, 'index.html'), 'utf8');
    const links = TERRITORIES.filter(t => !html.includes((slug === 'tramites-bebe' ? 'value="' : 'href="') + regionalUrl(t.slug) + '"'));
    if (slug === 'tramites-bebe') {
      if (!html.includes('id="pb-territory-select"') || !html.includes('src="/regional-selector.js"') ||
          links.length || (html.match(/class="pb-territory-compact"/g) || []).length !== 1)
        errors.push(slug + ': selector compacto incompleto');
    } else if (links.length || (html.match(/class="pb-territory-explorer"/g) || []).length !== 1) {
      errors.push(slug + ': selector incompleto');
    }
  }
  if (errors.length) throw Error('Arquitectura territorial inválida:\n' + errors.join('\n'));
  console.log('Arquitectura territorial OK: 19 HUB y 3 selectores HTML.');
}
module.exports = { applyTerritorialArchitecture, validateTerritorialArchitecture };
