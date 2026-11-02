#!/usr/bin/env node
// PapelesDelBebe / Buffer: verificación sin publicar por defecto.
const API = 'https://api.buffer.com';
const token = process.env.BUFFER_API_KEY;
if (!token) throw new Error('Falta BUFFER_API_KEY en Actions secrets');
async function query(gql, variables) {
 const r = await fetch(API,{method:'POST',headers:{Authorization:'Bearer '+token,'Content-Type':'application/json'},body:JSON.stringify({query:gql,variables})});
 if(!r.ok) throw new Error('Buffer HTTP '+r.status);
 const j=await r.json();
 if(j.errors?.length) throw new Error(j.errors.map(x=>x.message).join('; '));
 return j.data;
}
const organizations = (await query('query { account { organizations { id name } } }')).account?.organizations || [];
const matches=[];
for(const org of organizations) {
 const channels=(await query('query { channels(input:{organizationId:'+JSON.stringify(org.id)+'}) { id name displayName service } }')).channels || [];
 for(const c of channels) if(/twitter|^x$/i.test(c.service||'') && /papelesdelbebe/i.test([c.name,c.displayName].join(' ')))matches.push(c);
}
if(matches.length!==1) throw new Error('Se esperaba exactamente un canal X PapelesDelBebe; encontrados: '+matches.length+'. No se publicará nada.');
console.log('Conexión Buffer correcta; canal X verificado: '+matches[0].name+'.');
if(process.env.PUBLISH!=='true') {console.log('MODO PRUEBA: no se creó ninguna publicación.');process.exit(0);}
if(process.env.AUTO_PUBLISH_ENABLED!=='true') throw new Error('Publicación desactivada: configurar variable AUTO_PUBLISH_ENABLED=true para activarla.');

const slot=process.env.SLOT;
if (!['morning','evening'].includes(slot)) throw new Error('SLOT inválido');
const key=process.env.OPENAI_API_KEY;
if(!key) throw new Error('Falta OPENAI_API_KEY. No publicaremos textos repetidos.');
const today=new Intl.DateTimeFormat('en-CA',{timeZone:'Europe/Madrid',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
const ghToken=process.env.GITHUB_TOKEN;
if(!ghToken)throw Error('Falta GITHUB_TOKEN para el historial antirrepetición.');
const owner='mariorc7-creator', repo='utiles-online', historyPath='data/buffer-x-history.json';
const ghUrl='https://api.github.com/repos/'+owner+'/'+repo+'/contents/'+historyPath;
async function github(method,url,body){
 const r=await fetch(url,{method,headers:{Authorization:'Bearer '+ghToken,Accept:'application/vnd.github+json','Content-Type':'application/json','X-GitHub-Api-Version':'2022-11-28'},body:body?JSON.stringify(body):undefined});
 if(!r.ok && r.status!==404)throw Error('GitHub history HTTP '+r.status+': '+(await r.text()).slice(0,300));
 return r.status===404?null:await r.json();
}
const raw=await github('GET',ghUrl);
const history=raw?JSON.parse(Buffer.from(raw.content.replace(/\\n/g,''),'base64').toString('utf8')):{version:1,posts:[]};
if(!Array.isArray(history.posts))throw Error('Historial inválido');
if(history.posts.some(x=>x.date===today&&x.slot===slot)){
 console.log('Publicación ya registrada para '+today+' '+slot+'. No se duplica.');process.exit(0);
}
// Salvaguarda excepcional: la prueba manual del 28/10 ya llenó la franja del 29/10 a las 09:15.
if(today==='2026-10-29' && slot==='morning'){
 console.log('Franja del 29/10 a las 09:15 ocupada por tweet de prueba. Se omite.');process.exit(0);
}
const recent=history.posts.slice(-45).map(x=>x.text).join(' | ').slice(-8000);
const themes={
 morning:['trabajo y reuniones absurdas','tecnología y contradicciones digitales','dinero y vida adulta','costumbres españolas','ocio, deporte y rutinas','servicio al cliente y burocracia','expectativas frente a realidad'],
 evening:['crianza con humor observacional','guarderías y conciliación','trámites e internet administrativo','primerizos y consejos no pedidos','economía familiar','momentos cotidianos con niños','ayudas y documentación sin cifras concretas']
};
const dayNumber=Math.floor(Date.parse(today+'T00:00:00Z')/86400000);
const topic=themes[slot][dayNumber%7];
const role=slot==='morning'
 ? 'Humor social cotidiano, simpático, con ingenio y buen rollo; no hace falta hablar de bebés si la idea es buena.'
 : 'Humor amable sobre crianza, familia y trámites; cercano y divertido, que conecte naturalmente con Papeles del Bebé.';
const instructions=`Eres la voz de @PapelesDelBebe en X España. Crea UN tweet con una observación ORIGINAL, aguda, simpática y divertida, con un remate inesperado que arranque una sonrisa; suena a persona con gracia, nunca a IA corporativa. Tema del día: ${topic}. ${role}
Máximo 155 caracteres contando emojis. Mejor 65 a 125. Ningún saludo, cliché de café, pregunta retórica de relleno, eslogan, listas, ni emojis obligatorios. No repitas estructuras y chistes previos.
Nunca inventes cifras, legislación, ayudas, noticias, declaraciones ni tendencias. No bromear sobre fallecidos o accidentes, ni insultar, ridiculizar o atacar a ninguna persona o colectivo. Evita el tono troll, las pullas, el desprecio y el sarcasmo agresivo. Prioriza humor observacional, ternura con picardía y complicidad. Que el lector sonría y quiera compartirlo. Sin hashtags de tendencia no verificados. No pongas URL. Una sola frase o dos frases naturales. Devuelve solo el tweet.
Historial reciente (evita ideas y remates equivalentes): ${recent||'vacío'}`;
async function generate(){
 const r=await fetch('https://api.openai.com/v1/responses',{method:'POST',headers:{Authorization:'Bearer '+key,'Content-Type':'application/json'},body:JSON.stringify({model:process.env.OPENAI_MODEL||'gpt-4.1-mini',instructions,input:'Escribe un tweet nuevo para '+slot+'; tema '+topic+'. Cada intento debe tener una idea distinta. Intento creativo.',max_output_tokens:190,store:false})});
 if(!r.ok)throw Error('OpenAI HTTP '+r.status+': '+(await r.text()).slice(0,350));
 const j=await r.json();
 return (j.output||[]).flatMap(x=>x.content||[]).filter(x=>x.type==='output_text').map(x=>x.text).join('').trim();
}
let message='';
const normalize=t=>t.toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').replace(/[^a-z0-9 ]/g,'').replace(/\\s+/g,' ').trim();
const prev=history.posts.map(p=>normalize(p.text));
for(let n=0;n<3;n++){
 const c=(await generate()).replace(/^["“]|["”]$/g,'').trim();
 if(c && [...c].length<=155 && [...c].length>=35 && !prev.includes(normalize(c)) && !/https?:\/\//i.test(c) && !/^#/m.test(c) && !/[\n]{3}/.test(c)){message=c;break;}
}
if(!message)throw Error('La IA no generó un tweet válido. Se omite publicación.');
// Solo generar texto nuevo: nunca sustituir por contenido fijo.
console.log('Tweet generado ('+[...message].length+' caracteres): '+message);
const mutation='mutation ($input: CreatePostInput!) { createPost(input:$input) { ... on PostActionSuccess { post { id text dueAt } } ... on MutationError { message } } }';
const out=await query(mutation,{input:{text:message,channelId:matches[0].id,schedulingType:'automatic',mode:'addToQueue'}});
if(!out.createPost?.post?.id)throw new Error('Buffer no aceptó la publicación: '+JSON.stringify(out.createPost));
console.log('Publicación añadida a Buffer: '+out.createPost.post.id+'; horario: '+out.createPost.post.dueAt);
history.posts.push({date:today,slot,text:message,bufferId:out.createPost.post.id,dueAt:out.createPost.post.dueAt||null});
history.posts=history.posts.slice(-180);
const encoded=Buffer.from(JSON.stringify(history,null,2)).toString('base64');
await github('PUT',ghUrl,{message:'chore: registro de tweet Buffer '+today+' '+slot,content:encoded,...(raw?{sha:raw.sha}:{})});
console.log('Historial antirrepetición actualizado: '+today+' '+slot);
