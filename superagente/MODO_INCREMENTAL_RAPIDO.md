# SuperAgente rápido — modo incremental

El agente ya no ejecuta análisis semántico ni cola editorial de comparación cuando **no hay cambios en las fuentes oficiales**. Siempre conserva en el informe las consultas fallidas y fuentes sin línea base para revisión; nunca las interpreta como novedades confirmadas.

## Circuito de ejecución

1. Consultar todas las URLs oficiales vigiladas con un máximo de **4 conexiones concurrentes**, HTTPS, límite por respuesta y sin redirecciones; mantener el orden estable.
2. Comparar los hashes con `official-baseline.json`. No reemplazar la línea base automáticamente.
3. `superagente_fast_path.py` clasifica `changed_needs_review`, `unchanged`, `fetch_failed` y `baseline_missing`.
4. Solo pasar `changed_needs_review` a `superagente_editorial_loop.py` y `superagente_semantic_evidence.py`. El resto se informa, pero no genera análisis profundo. Un hash idéntico **no** prueba que la ayuda siga vigente.
5. En eventos de PR ejecutar las baterías de regresión; en la ejecución manual ordinaria omitir tests de desarrollo.
6. Ninguna ejecución activa publicación, revisión legal automática o modificación de `dateModified`.

## Medición real (GitHub Actions, siete fuentes)

| Fase | Ejecución secuencial | Ejecución optimizada |
|---|---:|---:|
| Vigilancia HTTPS | ~29 s | ~18 s |
| Enrutador | ~0,003 s | ~0,002 s |
| Fuentes para análisis profundo | 2 de 7 | 2 de 7 |
| Fuentes sin cambios descartadas del análisis profundo | 0 | 4 |
| Fuentes con fallo preservadas en incidencias | 1 | 1 |

Las dos mediciones proceden de ejecuciones distintas de la red: son observaciones, no una promesa de latencia fija. No se ha cuantificado aún el ahorro en grandes lotes; se puede medir cuando haya más fuentes.

**Regla de seguridad:** cachear o saltar una consulta no es lo mismo que verificar vigencia legal. Para el modo rápido seguimos consultando cada fuente en cada ejecución, pero dejamos de reprocesar lo que no ha cambiado.

**Estado:** integrado solo en rama de desarrollo del SuperAgente. No se activa cron ni despliegue a producción.
