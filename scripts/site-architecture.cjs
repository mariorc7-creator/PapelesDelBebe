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
module.exports = { NAV_ITEMS, HUBS };
