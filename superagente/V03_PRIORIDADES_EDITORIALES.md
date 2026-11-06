# SuperAgente V0.3 — motor de prioridades editoriales

El workplan V0.3 está basado en `sitemap.xml`, `reviews.json`, `source-routing.json` y `official-document-candidates.json`, sin peticiones de red, escritura en páginas o despliegues.

## Qué produce

`python scripts/superagente_v03_review_workplan.py` genera `superagente/v03-review-workplan.json` con una acción y prioridad para **cada URL del sitemap**, junto a su categoría, fecha de última revisión documentada (si existe), antigüedad de esa revisión y estado de las referencias.

Las seis páginas priorizadas en el piloto reciben prioridad P0/P1. Para otras páginas de ayudas, trámites y herramientas se emplea una prioridad heurística. No se utiliza tráfico real de Search Console todavía; este informe no debe presentarse como análisis SEO de oportunidades.

## Garantías

- `candidate_unverified` significa únicamente que existe una referencia candidata: jamás equivale a revisión oficial de requisitos, importes o plazos.
- Una fecha guardada sin historial de evidencias no se utiliza para afirmar que una página fue revisada.
- Los historiales sin fuentes HTTPS, revisor, observación específica y fecha válida no cuentan como revisión documentada.
- Los resultados `unverifiable` no se convierten en revisiones legales completadas.
- El plan nunca cambia el HTML, `dateModified`, `lastmod` ni ninguna fecha visible o interna de revisión.
- No autoriza publicar. El flujo de aprobación editorial y el rollback de despliegue siguen siendo barreras separadas.

## Próximos pasos

Vincular nuevas fichas oficiales concretas a los temas de mayor valor, integrar datos reales de Search Console con ventanas ya consolidadas, y construir una revisión documental con evidencias de contenido y permisos mínimos. La publicación y el cambio de fechas requerirán confirmación de la revisión de cada afirmación pertinente, no únicamente una prueba técnica.
