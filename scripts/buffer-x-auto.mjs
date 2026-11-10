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
 for(const c of channels) if(/twitter|^x$/i.test(c.service||'') && /papelesdelbebe|beb(e|é)peleon|beb[eé] pele[oó]n/i.test([c.name,c.displayName].join(' ')))matches.push(c);
}
if(matches.length!==1) throw new Error('Se esperaba exactamente un canal X PapelesDelBebe; encontrados: '+matches.length+'. No se publicará nada.');
console.log('Conexión Buffer correcta; canal X verificado: '+matches[0].name+'.');
if(process.env.PUBLISH!=='true') {console.log('MODO PRUEBA: no se creó ninguna publicación.');process.exit(0);}
if(process.env.AUTO_PUBLISH_ENABLED!=='true') throw new Error('Publicación desactivada: configurar variable AUTO_PUBLISH_ENABLED=true para activarla.');

const slot=process.env.SLOT;
if (!['morning','midday','evening'].includes(slot)) throw new Error('SLOT inválido');
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
const recent=history.posts.slice(-55).map(x=>x.text).join(' | ').slice(-12000);
// Mezcla editorial por cada 20 días = 60 posts: 24 conversación (40%), 21 humor (35%), 15 diario (25%).
// Se publica una pregunta diaria a mediodía; los otros formatos rotan sin convertir todo en encuestas.
const dayNumber=Math.floor(Date.parse(today+'T00:00:00Z')/86400000);
const cycleDay=dayNumber%20;
const morningDiario=[3,7,11,15,19].includes(cycleDay);
const eveningConversation=[2,7,12,17].includes(cycleDay);
const eveningHumor=[0,3,6,9,13,16].includes(cycleDay);
const category=slot==='midday'?'conversacion':
 slot==='morning'?(morningDiario?'diario':'humor'):
 (eveningConversation?'conversacion':eveningHumor?'humor':'diario');
const formats={
 conversacion:['pregunta-abierta','eleccion-divertida','dilema','pregunta-abierta'],
 humor:['chiste','observacion','anecdota','contradiccion'],
 diario:['diario-del-bebe','aprendizaje','pequeño-logro','confesion']
};
const format=formats[category][(dayNumber+(slot==='evening'?2:slot==='midday'?1:0))%formats[category].length];
const themes={
 conversacion:['cosas absurdas que hacen los niños','dinero y primeras inversiones','situaciones en el trabajo','costumbres familiares','tecnología y móviles','dormir y madrugar','fútbol y hobbies','pequeños logros personales','recuerdos de infancia','el dilema de hacerse mayor'],
 humor:['pañales y presupuestos','adultos que no entienden a los bebés','guardería','rutinas de casa','dinero y caprichos','reuniones y trabajo','siesta','tecnología','comida','fútbol'],
 diario:['misiones imposibles de un bebé','aprendiendo a hablar','mis pequeños planes para conquistar X','cosas que aprendo observando a mis padres','las primeras veces','descubrimientos cotidianos','errores inocentes de principiante','humor sobre querer ser mayor']
};
const topic=themes[category][(dayNumber+(slot==='evening'?4:slot==='midday'?2:0))%themes[category].length];
const role={
 'pregunta-abierta':'Plantea UNA pregunta directa que cualquier persona pueda responder con una anécdota; añade un giro divertido desde la perspectiva de un bebé. Termina en ?.',
 'eleccion-divertida':'Plantea UNA elección divertida entre dos opciones muy reconocibles para adultos, sin encuesta formal ni opciones numeradas. Termina en ?.',
 dilema:'Plantea UN dilema cotidiano gracioso que invite a contar experiencias; no hagas preguntas retóricas. Termina en ?.',
 chiste:'Escribe un chiste breve con remate sorprendente; evita los mismos chistes gastados de pañales.',
 observacion:'Observa una contradicción cotidiana de los adultos con voz de bebé, de manera ingeniosa.',
 anecdota:'Cuenta una escena cómica ficticia del personaje bebé; no la presentes como un hecho real.',
 contradiccion:'Abre con una frase que despierte curiosidad y remata con una paradoja divertida de la vida adulta vista por un bebé.',
 'diario-del-bebe':'Cuenta un avance pequeño o una peripecia humorística del personaje como una mini-historia en primera persona; ficticia, no un acontecimiento real confirmado.',
 aprendizaje:'Cuenta algo curioso que el personaje dice haber aprendido hoy sobre los adultos con un remate pícaro.',
 'pequeño-logro':'Cuenta un pequeño logro inventado y absurdo propio de un bebé. NO inventes cifras, seguidores, ingresos ni hitos reales de la cuenta.',
 confesion:'Haz una confesión simpática ficticia de Bebé Peleón que haga a los lectores reconocer algo de su vida.'
}[format];
const instructions=`Eres Bebé Peleón, un bebé gamberro, travieso, entrañable y muy ingenioso que escribe en primera persona en X España.
Crea UN tuit ORIGINAL, humano y con voz propia, sin apariencia de texto generado por IA. Categoría: ${category}. Formato: ${format}. Tema: ${topic}. ${role}
Objetivo: que la gente quiera responder, compartir o seguir la pequeña historia de Bebé Peleón. Usa un comienzo concreto o sorprendente, una sola idea y un remate fuerte; que no suene a anuncio ni a pregunta artificial.
No hables solo de pañales: también vida adulta, dinero, trabajo, fútbol, tecnología y actualidad atemporal desde los ojos de un niño pequeño. Nunca inventes noticias de actualidad, datos verificables, métricas, seguidores, ingresos, patrocinios ni resultados de la cuenta.
En conversación haz exactamente UNA pregunta fácil y relevante, en lenguaje natural, con signos ¿?. No pidas likes, reposts o seguidores. En humor y diario evita preguntas de relleno. Los avances del personaje son ficción humorística, NO resultados reales del perfil.
Usa español de España coloquial, humor rápido e inteligente, nada cursi, nada ofensivo. Evita frases genéricas como «la vida es», «ser padre es», «pregunta seria», «confesad» reiterados. Evita repetición de estructuras, coletillas y emojis. Entre 45 y 180 caracteres de cuerpo. Hasta un emoji si encaja.
NO hashtags ni arrobas, el programa añadirá #humorDePadres. Sin URLs ni publicidad, sin afirmaciones inventadas sobre hechos actuales y sin contenido denigrante.
Devuelve solo el texto del tuit, sin comillas ni explicaciones.
Historial reciente (no repitas temas o remates): ${recent||'vacío'}`;
async function generate(){
 const r=await fetch('https://api.openai.com/v1/responses',{method:'POST',headers:{Authorization:'Bearer '+key,'Content-Type':'application/json'},body:JSON.stringify({model:process.env.OPENAI_MODEL||'gpt-4.1-mini',instructions,input:'Escribe un post nuevo para '+slot+'; categoría '+category+'; formato '+format+'; tema '+topic+'. Cada intento debe tener una idea y un remate distintos.',max_output_tokens:190,store:false})});
 if(!r.ok)throw Error('OpenAI HTTP '+r.status+': '+(await r.text()).slice(0,350));
 const j=await r.json();
 return (j.output||[]).flatMap(x=>x.content||[]).filter(x=>x.type==='output_text').map(x=>x.text).join('').trim();
}
let message='';
const normalize=t=>t.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9 ]/g,'').replace(/\s+/g,' ').trim();
const prev=history.posts.map(p=>normalize(p.text));
const fixedHashtag='#humorDePadres';
for(let n=0;n<3;n++){
 const raw=(await generate()).replace(/^[\"“]|[\"”]$/g,'').trim();
 const joke=raw.replace(/#[A-Za-zÀ-ÿ0-9_]+/g,'').replace(/\s+/g,' ').trim();
 const candidate=joke+'\n\n'+fixedHashtag;
 if(joke && [...joke].length>=40 && [...joke].length<=180 && [...candidate].length<=220 && (category!=='conversacion'||(joke.includes('¿')&&joke.includes('?'))) && !prev.includes(normalize(candidate)) && !joke.includes('http://') && !joke.includes('https://')){message=candidate;break;}
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
