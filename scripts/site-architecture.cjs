// Fuente de verdad de la navegación y de los hubs del sitio.
// Las URL públicas permanecen estables: la jerarquía editorial NO fuerza una migración.
const NAV_ITEMS = [
  ['/mi-panel/', 'Mi panel'],
  ['/tramites-bebe/', 'Trámites'],
  ['/guias-familias/', 'Guías'],
  ['/ayudas-nacimiento/', 'Ayudas'],
  ['/herramientas/', 'Herramientas'],
  ['/preparativos-bebe/', 'Preparativos']
];
const HUBS = {
  tramites: '/tramites-bebe/',
  guias: '/guias-familias/',
  ayudas: '/ayudas-nacimiento/',
  comunidades: '/comunidades/',
  herramientas: '/herramientas/',
  preparativos: '/preparativos-bebe/'
};
// BreadcrumbList is only added where there is a matching visible breadcrumb.
// Do not infer topic from a substring or invent folder URLs.
const { TERRITORY_BY_GUIDE, TERRITORY_BY_SLUG } = require('./territories.cjs');
const PREVIOUSLY_BREADCRUMBED_GUIDES = [
  'tarjeta-sanitaria-bebe-baleares',
  'tarjeta-sanitaria-bebe-cantabria',
  'tarjeta-sanitaria-bebe-castilla-la-mancha',
  'tarjeta-sanitaria-bebe-extremadura',
  'tarjeta-sanitaria-bebe-navarra',
  'tarjeta-sanitaria-bebe-pais-vasco',
  'titulo-familia-numerosa-cantabria',
  'titulo-familia-numerosa-ceuta',
  'titulo-familia-numerosa-melilla',
  'titulo-familia-numerosa-pais-vasco'
];
const GUIDE_BREADCRUMBS = Object.fromEntries(PREVIOUSLY_BREADCRUMBED_GUIDES.map(slug =>
  [slug, ['comunidades', 'comunidades/' + TERRITORY_BY_GUIDE[slug]]]
));
const BREADCRUMB_LABELS = { comunidades: 'Comunidades' };
for (const [slug, territory] of Object.entries(TERRITORY_BY_SLUG)) {
  BREADCRUMB_LABELS['comunidades/' + slug] = territory.name;
}
module.exports = { NAV_ITEMS, HUBS, GUIDE_BREADCRUMBS, BREADCRUMB_LABELS };
