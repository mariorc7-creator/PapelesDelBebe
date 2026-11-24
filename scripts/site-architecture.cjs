// Fuente de verdad de la navegación y de los hubs del sitio.
// Las URL públicas permanecen estables: la jerarquía editorial NO fuerza una migración.
const NAV_ITEMS = [
  ['/tramites-bebe/', 'Trámites'],
  ['/guias-familias/', 'Guías'],
  ['/ayudas-nacimiento/', 'Ayudas'],
  ['/comunidades/', 'Comunidades'],
  ['/herramientas/', 'Herramientas'],
  ['/preparativos-bebe/', 'Preparativos'],
  ['/mi-panel/', 'Mi panel']
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
const GUIDE_BREADCRUMBS = {
  'tarjeta-sanitaria-bebe-baleares': ['guias-familias', 'guias-documentacion-bebe'],
  'tarjeta-sanitaria-bebe-cantabria': ['guias-familias', 'guias-documentacion-bebe'],
  'tarjeta-sanitaria-bebe-castilla-la-mancha': ['guias-familias', 'guias-documentacion-bebe'],
  'tarjeta-sanitaria-bebe-extremadura': ['guias-familias', 'guias-documentacion-bebe'],
  'tarjeta-sanitaria-bebe-navarra': ['guias-familias', 'guias-documentacion-bebe'],
  'tarjeta-sanitaria-bebe-pais-vasco': ['guias-familias', 'guias-documentacion-bebe'],
  'titulo-familia-numerosa-cantabria': ['guias-familias', 'guias-familias-territorios'],
  'titulo-familia-numerosa-ceuta': ['guias-familias', 'guias-familias-territorios'],
  'titulo-familia-numerosa-melilla': ['guias-familias', 'guias-familias-territorios'],
  'titulo-familia-numerosa-pais-vasco': ['guias-familias', 'guias-familias-territorios']
};
const BREADCRUMB_LABELS = {
  'guias-familias': 'Guías',
  'guias-documentacion-bebe': 'Documentación del bebé',
  'guias-familias-territorios': 'Guías por territorio'
};
module.exports = { NAV_ITEMS, HUBS, GUIDE_BREADCRUMBS, BREADCRUMB_LABELS };
