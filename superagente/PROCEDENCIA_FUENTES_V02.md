# SuperAgente V0.2 — procedencia de evidencias oficiales

## Qué se ha añadido
- `scripts/superagente_source_provenance.py` valida que una propuesta editorial solo cite dominios expresamente autorizados en `superagente/official-watchlist.json`.
- El control es de denegación por defecto (fail-closed): no se aceptan HTTP, credenciales en URL, puertos no estándar ni subdominios que no figuren exactamente en la lista.
- La ejecución de CI comprueba los dominios **antes** de enlazar la propuesta con el párrafo actual y generar el triaje.
- Las pruebas de regresión comprueban bloqueos y aceptación de dominios exactos.

## Alcance actual de la lista
La lista existente contiene `www.boe.es` y `administracion.gob.es`. Es intencionadamente pequeña: **NO es cobertura completa** de fuentes de ayudas y trámites en España. Antes de usar comprobación editorial operativa deben revisarse y autorizarse URLs concretas y hosts de Seguridad Social, AEAT, Generalitat y administraciones territoriales competentes, evitando confianza automática en subdominios.

## Límites de seguridad
Un dominio permitido solo acredita coincidencia con la lista, **no** que el documento citado exista, se haya descargado, sea aplicable ni esté vigente. La verificación normativa real sigue pendiente y requiere inspección del documento, comparación semántica, jurisdicción, fecha de vigencia y evidencia archivada.

La publicación y la modificación de páginas siguen **prohibidas** por estos scripts. No tocan PROD ni alteran fechas de revisión.
