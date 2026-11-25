// Arquitectura territorial V4.1. Las URL existentes no se mueven.
// Enlaces definidos explícitamente para evitar recomendaciones cruzadas.
const TERRITORIES = [
  {slug:'andalucia',name:'Andalucía',health:'andalucia',family:'andalucia',aids:['ayuda-partos-multiples-andalucia','deduccion-nacimiento-andalucia']},
  {slug:'aragon',name:'Aragón',health:'aragon',family:'aragon',aids:['ayuda-partos-multiples-aragon-2026']},
  {slug:'asturias',name:'Asturias',health:'asturias',family:'asturias',aids:['ayuda-nacimiento-asturias']},
  {slug:'canarias',name:'Canarias',health:'canarias',family:'canarias',aids:['deduccion-nacimiento-canarias-2026']},
  {slug:'cantabria',name:'Cantabria',health:'cantabria',family:'cantabria',aids:['deduccion-nacimiento-cantabria-2026']},
  {slug:'castilla-la-mancha',name:'Castilla-La Mancha',health:'castilla-la-mancha',family:'castilla-la-mancha',aids:['deduccion-nacimiento-castilla-la-mancha-2026']},
  {slug:'castilla-y-leon',name:'Castilla y León',health:'castilla-y-leon',family:'castilla-y-leon',aids:['bono-nacimiento-castilla-leon-2026']},
  {slug:'cataluna',name:'Cataluña',health:'cataluna',family:'cataluna',aids:['ayuda-nacimiento-cataluna','ayudas-nacimiento-cataluna']},
  {slug:'ceuta',name:'Ceuta',health:null,family:'ceuta',aids:['familias-ceuta-2026']},
  {slug:'comunidad-de-madrid',name:'Comunidad de Madrid',health:'madrid',family:'madrid',aids:['ayuda-natalidad-madrid','cheque-bebe-madrid']},
  {slug:'comunidad-valenciana',name:'Comunitat Valenciana',health:'comunitat-valenciana',family:'comunitat-valenciana',aids:['deduccion-nacimiento-comunitat-valenciana','ayuda-nacimiento-valencia']},
  {slug:'extremadura',name:'Extremadura',health:'extremadura',family:'extremadura',aids:['ayuda-natalidad-extremadura-2026']},
  {slug:'galicia',name:'Galicia',health:'galicia',family:'galicia',aids:['tarxeta-benvida']},
  {slug:'islas-baleares',name:'Illes Balears',health:'baleares',family:'baleares',aids:['deduccion-nacimiento-baleares-2026']},
  {slug:'la-rioja',name:'La Rioja',health:'la-rioja',family:'la-rioja',aids:['deduccion-nacimiento-la-rioja-2026']},
  {slug:'melilla',name:'Melilla',health:null,family:'melilla',aids:['familias-melilla-2026']},
  {slug:'navarra',name:'Navarra',health:'navarra',family:'navarra',aids:['ayuda-familias-monoparentales-navarra-2026']},
  {slug:'pais-vasco',name:'País Vasco',health:'pais-vasco',family:'pais-vasco',aids:['ayudas-hijos-pais-vasco']},
  {slug:'region-de-murcia',name:'Región de Murcia',health:'murcia',family:'murcia',aids:['ayudas-familias-murcia-2026']}
];
const regionalUrl = slug => '/comunidades/' + slug + '/';
const TERRITORY_BY_SLUG = Object.fromEntries(TERRITORIES.map(x=>[x.slug,x]));
const TERRITORY_BY_GUIDE = {};
for (const territory of TERRITORIES) {
  if (territory.health) TERRITORY_BY_GUIDE['tarjeta-sanitaria-bebe-' + territory.health] = territory.slug;
  if (territory.family) TERRITORY_BY_GUIDE['titulo-familia-numerosa-' + territory.family] = territory.slug;
  for (const slug of territory.aids) TERRITORY_BY_GUIDE[slug] = territory.slug;
}
module.exports = { TERRITORIES, TERRITORY_BY_SLUG, TERRITORY_BY_GUIDE, regionalUrl };
