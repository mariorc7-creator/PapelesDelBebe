# Arquitectura editorial V4 — Papeles del Bebé
Fecha de definición: 2026-11-24. Esta guía define jerarquía y enlaces; no ordena mover URL existentes.

## Primer nivel y función principal

| Sección | Hub estable | Intención de usuario |
| --- | --- | --- |
| Trámites | /tramites-bebe/ | Qué gestionar y en qué orden después del nacimiento |
| Guías | /guias-familias/ | Cómo realizar trámites o resolver casos concretos |
| Ayudas | /ayudas-nacimiento/ | Localizar prestaciones, deducciones y ayudas |
| Comunidades | /comunidades/ | Localizar el contenido aplicable al territorio |
| Herramientas | /herramientas/ | Calculadoras, buscadores y flujos interactivos |
| Preparativos | /preparativos-bebe/ | Listas, comparativas y planificación de compras |

Mi panel (/mi-panel/) es una acción transversal, no un clúster informativo.
El Observatorio (/observatorio/) es un recurso editorial transversal; se enlaza desde Ayudas y Comunidades.

## Guías: segundo nivel
- Documentación: /guias-documentacion-bebe/ → registro, padrón, tarjeta sanitaria, certificados y DNI.
- Permisos: /guias-permisos-nacimiento/ → permisos, conciliación, lactancia, casos especiales.
- Fiscalidad y ayudas: /guias-fiscalidad-ayudas-bebe/ → IRPF, deducciones, IMV y prestaciones.
- Territorios y familias: /guias-familias-territorios/ → títulos de familia numerosa/monoparental.

La misma URL de guía puede tener enlaces desde Trámites, Ayudas o Comunidades, pero debe responder a UNA intención principal. La página guía tiene un único canonical y un único breadcrumb editorial. Un hub no sustituye a la ficha del trámite.

## Plantillas editoriales
- Hub: resumen de intención, categorías y enlaces descriptivos, preguntas relevantes, metodología, fecha final.
- Guía: breadcrumb visible, respuesta inicial, requisitos y documentación contrastados, pasos, incidencias, fuentes, enlaces relacionados y UNA fecha de revisión al final del contenido.
- Herramienta: qué resuelve, formulario/resultado accesibles, explicación de límites de precisión, enlaces a fuentes y guías.
- Comparativa: criterios explícitos, productos reales, fotografías autorizadas, metodología, limitaciones y enlaces de afiliación identificados.
- Territorio: administración competente, requisitos vigentes verificados, enlaces a los hubs de ayudas y guías.

## Reglas innegociables SEO/GEO
1. Las URL ya publicadas NO se migran por motivos cosméticos. Antes de mover una URL: inventario de tráfico e indexación, matriz 301 uno a uno, canonicals, enlaces, sitemap, pruebas y seguimiento.
2. Una sola URL canónica por intención; noindex solo cuando esté motivado. Las URL antiguas deben redirigir directamente al destino.
3. Breadcrumb visible consistente con BreadcrumbList cuando se incorpore y verifique el marcado. No hacer coincidir por obligación carpetas y jerarquía editorial.
4. Los enlaces importantes deben existir en HTML inicial y tener texto descriptivo; nunca depender exclusivamente de JavaScript.
5. Un solo H1; la revisión editorial es ÚNICA y termina el artículo. No modificar fechas por despliegue sin revisar el contenido.
6. Los importes, plazos, requisitos y fuentes deben estar contrastados por administración y fecha, no deducidos de otra comunidad.
7. El auditor debe inspeccionar el artefacto compilado dist y el menú estático; validar sitemap, canonicals, enlaces y referencias.
8. La clasificación temática se prueba con Search Console. No fusionar ni eliminar URL basándose solo en longitud o cero clics.
9. Priorizar UX móvil, accesibilidad y rendimiento sobre adiciones decorativas.
10. El SEO técnico facilita la comprensión, pero no garantiza indexación ni posición.

## Despliegue gradual
- Fase A: fuente única de navegación con HTML generado en build, mismas rutas en JavaScript, sin cambiar URL/canonical/sitemap.
- Fase B: normalizar plantillas y breadcrumbs mediante catálogo de rutas explícito; evitar inyección automática indiscriminada.
- Fase C: analizar canibalización con consultas reales y aplicar consolidaciones puntuales respaldadas por datos.
- Fase D: estudiar una migración de URL únicamente si su beneficio neto supera el riesgo.
