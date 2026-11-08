# Política de estabilidad SEO — Papeles del Bebé

**A partir de esta activación, el SEO de producción se mantiene estable.** Google necesita tiempo para rastrear, indexar y evaluar el contenido. El SuperAgente no cambiará el SEO por calendario.

## Regla operativa

- **No** hay tareas programadas para modificar títulos SEO, metadescripciones, cabeceras H1, canonicals, URLs, redirecciones, enlazado interno estructural, `robots.txt`, `sitemap.xml`, plantilla ni diseño.
- **No** se actualizan las fechas de las páginas por el mero paso del tiempo. `dateModified` solo cambia cuando cambió materialmente el contenido y fue aprobado.
- **Sí** se comprueban en modo solo lectura las fuentes oficiales para detectar novedades de prestaciones, requisitos y plazos. Esto no significa un cambio SEO ni altera las páginas.
- Si hay una novedad **factual contrastada**, se prepara un lote editorial para revisión. El contenido puede actualizarse cuando haya una razón legítima, con pruebas y revisión independiente de los hechos.
- **Correcciones SEO excepcionales**, por ejemplo noindex incorrecto, página rota, fallo grave de indexación o canonical erróneo, deben contar con evidencia y aprobación; no son retoques rutinarios.
- No hay reescrituras masivas ni mejoras estéticas automáticas por objetivos de posicionamiento.
- El flujo de vigilancia solo tiene permiso GitHub `contents: read`; usa una versión fijada del SuperAgente, no realiza commits, PR, fusiones ni despliegues.

## Ejecución

La vigilancia se programa **de lunes a viernes, 06:17 UTC** desde el workflow de la rama principal, con cuatro solicitudes oficiales concurrentes como máximo. Compara las fuentes permitidas, solo analiza semánticamente las modificadas y guarda informes durante catorce días en GitHub Actions. Si la fuente no responde, conserva el error sin darla por revisada.

El workflow no toca HTML, CSS, URLs, SEO, sitemap, robots ni metadatos; no valida automáticamente la interpretación legal, ni cambia fechas de revisión ni publica nada.

## Lo que queda pendiente de autonomía

La primera versión **trabaja sola en vigilancia**, pero la aprobación jurídica de nuevos importes, requisitos o plazos y la publicación de las páginas continúa supervisada. No confundir «vigilancia activada» con «editor editorial autónomo».
