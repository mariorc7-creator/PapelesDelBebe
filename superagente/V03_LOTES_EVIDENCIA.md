# SuperAgente V0.3 — lotes de revisión con evidencia

El generador `scripts/superagente_v03_editorial_batch.py` combina el plan de prioridades procedente del sitemap con los justificantes de revisión aportados, sin tocar las páginas ni actualizar fechas. Produce `superagente/v03-editorial-batch.json` durante el workflow de auditoría.

## Estados posibles

- `no_receipt`: no hay justificante; localizar documentación y registrar comprobaciones específicas.
- `receipt_invalid`: hay justificante, pero falta algún dato obligatorio o contiene una inconsistencia; corregirlo y revalidar.
- `stale_snapshot`: el SHA-256 del HTML cambió después de preparar el justificante; examinar la nueva versión y recopilar evidencia otra vez.
- `awaiting_independent_signoff`: justificante completo a nivel de formato, **pendiente** de contraste de fuentes y aprobación editorial. No implica verificación legal, nueva fecha de revisión ni permiso de publicación.

## Priorización

Se respeta la prioridad editorial P0/P1 y la del resto de páginas. Dentro de una misma prioridad, se atienden primero evidencias obsoletas, luego justificantes inválidos, después los completos pendientes de aprobación y finalmente las páginas sin justificante. El paquete predeterminado recoge 12 tareas; el backlog completo no se pierde.

La ausencia de `review-receipts.json` produce un lote de trabajo sin revisiones completadas; no se inventan justificantes.

## Bloqueos vigentes

- No se actualizan ni el HTML ni los metadatos `dateModified`/`lastmod`.
- No se cambian fechas de revisión sin un procedimiento separado con evidencia confirmada.
- No se realizan solicitudes de red, fusiones de ramas ni despliegues.
- La aprobación editorial independiente y el rollback de un despliegue de staging siguen pendientes.
- La priorización actual no utiliza métricas de Search Console porque GSC Wizard no tiene una suscripción activa.
