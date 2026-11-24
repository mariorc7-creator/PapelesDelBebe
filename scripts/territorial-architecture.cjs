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
  // Some evergreen URLs are generated from historical -2026 source pages.
  return fs.existsSync(path.join(root, slug, 'index.html')) ||
    fs.existsSync(path.join(root, slug + '-2026', 'index.html'));
}
// Un único selector compacto para Trámites, Guías y Ayudas.
function renderCompactTerritorySelector(context) {
  const variants = {
    'tramites-bebe': {
      title: 'Trámites según tu comunidad',
      intro: 'Los siete pasos son comunes a toda España. Consulta aquí los detalles autonómicos.',
      button: 'Ver trámites'
    },
    'guias-familias': {
      title: 'Guías según tu comunidad',
      intro: 'Elige tu comunidad para consultar las guías específicas de tu territorio.',
      button: 'Ver guías'
    },
    'ayudas-nacimiento': {
      title: 'Ayudas según tu comunidad',
      intro: 'Consulta las ayudas y deducciones del territorio donde resides.',
      button: 'Ver ayudas'
    }
  };
  const current = variants[context];
  if (!current) throw new Error('Selector territorial sin contexto: ' + context);
  const options = TERRITORIES.map(t =>
    '<option value="' + regionalUrl(t.slug) + '">' + esc(t.name) + '</option>'
  ).join('');
  return '<section class="pb-territory-compact" aria-labelledby="pb-choose-region">' +
    '<h2 id="pb-choose-region">' + current.title + '</h2>' +
    '<p>' + current.intro + '</p>' +
    '<div class="pb-territory-compact-controls">' +
    '<label for="pb-territory-select" class="pb-territory-label">Tu comunidad</label>' +
    '<select id="pb-territory-select" name="comunidad" aria-label="Selecciona tu comunidad">' +
    '<option value="">Selecciona tu comunidad</option>' + options + '</select>' +
    '<button type="button" id="pb-territory-go">' + current.button + '</button></div>' +
    '<a class="pb-territory-all" href="/comunidades/">Ver las 19 comunidades</a>' +
    '</section>';
}

// Eliminar de la versión pública los listados redundantes que ya sustituye
// el selector, sin afectar los demás módulos, fuentes ni contenido nacional.
function stripOldTerritorialMenus(html, slug) {
  if (slug === 'guias-familias') {
    const pattern = /<section class="tool-panel" aria-labelledby="guias-comunidades-titulo">[\s\S]*?<\/section>/gi;
    const count = (html.match(pattern) || []).length;
    if (count !== 1) throw new Error('Guías: se esperaba exactamente un listado de comunidades previo');
    return html.replace(pattern, '');
  }
  if (slug === 'ayudas-nacimiento') {
    const oldSelector = /<section class="pb-hub-panel"><span class="tool-kicker" id="elegir-comunidad">[\s\S]*?<select id="selectorComunidadHub"[\s\S]*?<\/select><\/div><\/section>/gi;
    const oldFeatured = /<details class="pb-hub-more pb-aid-featured-more">[\s\S]*?<\/section><\/div><\/details>/gi;
    if ((html.match(oldSelector) || []).length !== 1 || (html.match(oldFeatured) || []).length !== 1) {
      throw new Error('Ayudas: selectores/listas antiguos no identificados de forma unívoca');
    }
    const cleaned = html.replace(oldSelector, '').replace(oldFeatured, '');
    const territoryAnchor = '<a href="/comunidades/">Consultar las 19 comunidades y ciudades autónomas</a>';
    if (!cleaned.includes(territoryAnchor)) throw new Error('Ayudas: falta ancla editorial de comunidades');
    // Tres enlaces directos prioritarios exigidos por SEO, junto a la explicación
    // autonómica existente; no se crea un segundo listado de comunidades.
    return cleaned.replace(territoryAnchor, territoryAnchor +
      '. Ejemplos: <a href="/ayuda-nacimiento-cataluna/">ayuda por nacimiento en Cataluña</a>, ' +
      '<a href="/ayuda-nacimiento-asturias/">ayuda por nacimiento en Asturias</a> y ' +
      '<a href="/deduccion-nacimiento-la-rioja/">deducción por nacimiento en La Rioja</a>');
  }
  return html;
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
    html = stripOldTerritorialMenus(html, slug);
    html = addStyle(html);
    html = html.replace(/<\/body>/i, '<script src="/regional-selector.js" defer></script></body>');
    return injectAfterIntro(html, renderCompactTerritorySelector(slug), false);
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
    const missing = TERRITORIES.filter(t => !html.includes('value="' + regionalUrl(t.slug) + '"'));
    const count = (html.match(/class="pb-territory-compact"/g) || []).length;
    if (missing.length || count !== 1 || !html.includes('id="pb-territory-select"') ||
        !html.includes('src="/regional-selector.js"'))
      errors.push(slug + ': selector compacto incompleto');
    if (html.includes('class="pb-territory-explorer"') ||
        (slug === 'guias-familias' && html.includes('id="guias-comunidades-titulo"')) ||
        (slug === 'ayudas-nacimiento' && (
          /<select\b[^>]*id="selectorComunidadHub"/.test(html) || /<details\b[^>]*class="[^"]*pb-aid-featured-more/.test(html)
        )))
      errors.push(slug + ': quedan módulos regionales duplicados');
  }
  if (errors.length) throw Error('Arquitectura territorial inválida:\n' + errors.join('\n'));
  console.log('Arquitectura territorial OK: 19 HUB y 3 selectores HTML.');
}
module.exports = { applyTerritorialArchitecture, validateTerritorialArchitecture };
