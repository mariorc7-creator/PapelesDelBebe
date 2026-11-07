# SuperAgente — circuito editorial integrado V1

## Qué puede ejecutar ya

`superagente_official_watch.py` consulta las URLs oficiales autorizadas y calcula huellas. Cuando existe una línea base confirmada, señala cambios de texto. `superagente_official_content_tasks.py` identifica las guías afectadas. `superagente_editorial_loop.py` crea plantillas de revisión con **SHA de fuente y SHA del HTML**.

Una propuesta **NO implica un cambio normativo**. Los cambios de huella pueden proceder de cookies, navegación, fechas de página u otros elementos ajenos a la ayuda. Para actualizar un importe o un plazo es obligatoria una verificación independiente de la fuente y de los hechos.

## Ciclo completo (sin desplegar)

1. Ejecutar GitHub Actions: **SuperAgente - Vigilancia fuentes oficiales** manualmente en la rama de SuperAgente. El workflow produce tres artefactos: candidatos de línea base, tareas por fuente y cola editorial por guía.
2. Para cada cambio relevante, contrastar cuantía, personas beneficiarias, municipio/CCAA, período de aplicación, convocatoria, fecha de cierre y texto oficial de origen.
3. Construir un manifiesto de revisión editorial incluyendo `path`, `original_sha256`, `official_source_url`, `source_sha256`, `action`, `search`, `replacement`, `review_date`, `evidence_ref`, `reviewer`, `independent_source_verification=true`, `editorial_approval=true` y `publication_allowed=false`.
4. Crear rama **`batch/...`** desde el último `main`, con el script integrado ya disponible en esa rama, y ejecutar:

```bash
python scripts/superagente_editorial_loop.py \
  --watchlist superagente/official-watchlist.json \
  --report /ruta/official-watch-report.json \
  --approved-manifest /ruta/revision-contrastada.json \
  --output /tmp/preflight.json

python scripts/superagente_editorial_loop.py \
  --watchlist superagente/official-watchlist.json \
  --report /ruta/official-watch-report.json \
  --approved-manifest /ruta/revision-contrastada.json \
  --apply \
  --output /tmp/lote.json
```

5. Pasar el QA de `batch-release`, comprobar visualmente una sola preview y abrir un PR de **solo contenido**. Fusiones y producción necesitan autorización y controles externos.

Para una fuente **sin cambios**, el revisor puede certificar que los hechos de la guía siguen vigentes y generar una entrada `action=review_only`. El script modifica únicamente la fecha visible de revisión; nunca utiliza una huella idéntica como revisión jurídica por sí misma ni toca `dateModified`.

## Seguridad

- La línea base de fuentes debe revisarse y persistirse; de otro modo el agente solo detectará la primera consulta, sin cambios comparables.
- Todas las entradas se vinculan a una fuente exacta autorizada y a un archivo exacto de la web. Fuente y página deben conservar sus huellas entre verificación y edición.
- No escribe fuera de ramas `batch/*`, no modifica HTML sin autorización editorial, no crea PR, no fusiona, no despliega.
- Un error en una página impide aplicar el lote. El módulo no acepta sustituciones HTML arbitrarias.
- No se activa cron ni monitorización periódica. No utiliza GSC Wizard.

## Limitaciones actuales

El agente **todavía no compara autónomamente la semántica jurídica** de documentos oficiales ni está autorizado para publicar modificaciones legales de forma desatendida. Hay cobertura inicial de siete fuentes, no de todas las ayudas autonómicas.

El objetivo del siguiente incremento es incorporar contraste semántico verificable con citas de documentos primarios y una prueba de reversión remota real, no fingir que un cambio de hash es una nueva ley.

**Estado:** integrado en la rama de desarrollo, listo para pruebas de recepción de novedades, pero no activado en producción.
