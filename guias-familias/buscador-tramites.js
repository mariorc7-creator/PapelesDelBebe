(()=>{
'use strict';
const field=document.getElementById('pbFindInput'),results=document.getElementById('pbFindResults');if(!field||!results)return;
const entries=[
 ['Empadronar al bebé','/pack-empadronamiento/','Padrón municipal · Comprobar el alta y preparar documentos','empadronamiento empadronar padron padrón domicilio ayuntamiento empadronado volante certificado'],
 ['Si el bebé no aparece empadronado','/empadronamiento-bebe-no-aparece-oficio/','Qué revisar cuando el empadronamiento no consta de oficio','empadronamiento padron padrón oficio ayuntamiento automatico'],
 ['Inscripción en el Registro Civil','/registro-civil-bebe/','Registro del nacimiento y documentación','registro civil nacimiento inscribir bebé certificado'],
 ['Alta del bebé en Seguridad Social','/alta-bebe-seguridad-social/','Gestión del alta y datos necesarios','seguridad social alta recien nacido beneficiario inss'],
 ['Tarjeta sanitaria del bebé','/tarjeta-sanitaria-bebe/','Cómo tramitar la tarjeta en tu comunidad','tarjeta sanitaria salud sip catsalut tis medico pediatra'],
 ['Incluir al bebé como beneficiario sanitario','/incluir-bebe-beneficiario-seguridad-social/','Reconocimiento del derecho a asistencia sanitaria','beneficiario seguridad social asistencia sanitaria'],
 ['Permiso por nacimiento','/permiso-nacimiento-cuidado-menor/','Permiso parental y prestación','permiso paternidad maternidad baja nacimiento'],
 ['Certificado de nacimiento online','/certificado-nacimiento-online/','Solicitud del certificado','certificado nacimiento literal online'],
 ['DNI del bebé','/dni-bebe-cuando-hace-falta/','Cuándo es necesario y qué llevar','dni documento identidad policia'],
 ['Pasaporte del bebé','/pasaporte-bebe-requisitos/','Documentos y condiciones para viajar','pasaporte viaje viajar extranjero'],
 ['Deducción por maternidad','/deduccion-maternidad/','Condiciones y solicitud de la deducción','deduccion maternidad modelo 140 hacienda aeat'],
 ['Buscar ayudas por nacimiento','/herramientas/buscador-ayudas/','Simulador según comunidad y situación familiar','ayudas subsidios prestaciones cheque bebe dinero'],
 ['Documentos para los trámites','/documentos-tramites-bebe/','Checklist de documentos más habituales','documentacion papeles carpeta tramites']
];
const normalize=s=>(s||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9 ]/g,' ').replace(/\s+/g,' ').trim();
const enriched=entries.map(([name,url,description,keywords])=>({name,url,description,search:normalize(name+' '+description+' '+keywords)}));
field.addEventListener('input',()=>{
 const q=normalize(field.value);
 results.replaceChildren();
 if(!q){results.hidden=true;return;}
 const words=q.split(' ').filter(Boolean);
 const matching=enriched.filter(e=>words.every(w=>e.search.includes(w))).slice(0,7);
 results.hidden=false;
 if(!matching.length){const p=document.createElement('p');p.textContent='No encontramos ese término. Prueba con «padrón», «sanitaria» o «registro», o consulta las categorías de abajo.';results.append(p);return;}
 matching.forEach(e=>{const a=document.createElement('a');a.href=e.url;const strong=document.createElement('strong');strong.textContent=e.name;const small=document.createElement('small');small.textContent=e.description;a.append(strong,small);results.append(a);});
});
})();