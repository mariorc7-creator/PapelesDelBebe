# Actualizador de contenido del SuperAgente V1 — Handoff real

**Objetivo:** unir detección de novedades oficiales con la edición segura de guías y las fechas de revisión, de forma que el agente deje de ser únicamente un auditor.

## Piezas existentes y nuevas

1. `superagente_official_watch.py`: consulta fuentes oficiales exactas y compara huellas digitales con una línea base. *Cambio de huella no significa que haya cambiado una norma.*
2. `superagente_official_content_tasks.py` (nuevo): mapea cada fuente alterada a la página concreta de Papeles del Bebé y crea tareas de contraste semántico; no afirma importes ni plazos no comprobados.
3. **Verificación editorial independiente de hechos**: sigue siendo un control necesario. Debe determinar convocatoria, cuantía, rango de fechas, requisitos, jurisdicción y texto exacto frente a la publicación oficial. No hay todavía un verificador semántico autónomo de garantías equivalentes.
4. `superagente_content_updater.py` (nuevo): aplica **en un único lote** cambios exactos que hayan sido contrastados y aprobados, con SHA de cada HTML para impedir cambios sobre versiones desactualizadas.
5. Después, una rama `batch/*`, pruebas SEO y móvil, una única preview y despliegue de producción revisado mediante el flujo ya disponible en `main`.

## Cómo prepara una modificación real

Un manifiesto privado de revisión, en JSON, debe tener este esquema:

```json
{
  "schema_version": 1,
  "status": "editorially_verified_for_branch_only",
  "publication_allowed": false,
  "changes": [
    {
      "path": "comunidades/asturias/index.html",
      "original_sha256": "SHA256_REAL_DEL_HTML_ACTUAL",
      "action": "change",
      "search": "FRASE_EXACTA_Y_UNICA_A_MODIFICAR",
      "replacement": "FRASE_CONTRASTADA_CON_LA_FUENTE_OFICIAL",
      "review_date": "FECHA_REAL_EN_FORMATO_YYYY-MM-DD",
      "official_source_url": "https://URL_OFICIAL_REAL",
      "independent_source_verification": true,
      "editorial_approval": true,
      "reviewer": "REVISOR_REAL",
      "evidence_ref": "REFERENCIA_A_UNA_EVIDENCIA_REAL"
    }
  ]
}
```

Para una **revisión sin cambios**, indicar `action: "review_only"`, `unchanged_confirmed: true` y omitir `search` y `replacement`. El actualizador cambiará únicamente la fecha visible de revisión si existe, **sin modificar `dateModified`**, para no simular que hubo cambios de contenido.

Primero ejecutar sin modificar:

```bash
python scripts/superagente_content_updater.py --manifest /ruta/privada/revision.json --output /tmp/preflight.json
```

Tras revisión de las propuestas y únicamente en rama aislada:

```bash
python scripts/superagente_content_updater.py --manifest /ruta/privada/revision.json --apply --output /tmp/lote.json
```

El comando no utiliza GitHub ni Vercel, no hace commits, no publica ni autoriza despliegues. Rechaza cambios de canonical, meta SEO, H1, IDs, navegación y estructura, y archivos que no coincidan con la huella original.

## Límites todavía pendientes

- **Cobertura:** la lista inicial de vigilancia contiene muy pocas fuentes (ahora AEAT y Cataluña). Hay que ampliar con URLs oficiales verificadas por CCAA, BOE y normas relevantes.
- **Semántica:** no basta un hash distinto. Es necesario extraer la parte relevante de los documentos, identificar diferencias jurídicas y contrastar cada propuesta antes de que el actualizador la aplique.
- **Autonomía:** sin un verificador de hechos autorizado y sin pruebas de reversión remota, no se debe dejar que cambios legales se publiquen sin supervisión.
- **Periodicidad:** la vigilancia automática continua permanece deliberadamente desactivada. Se pueden realizar ejecuciones manuales sin habilitar despliegues.
- **Revisión de fuentes:** no se inventan fechas de revisión ni se cambian cuando la consulta falla o se detecta una diferencia sin estudiar.

**Estado correcto:** el actualizador de HTML con controles ya existe en rama de desarrollo, pero no se debe describir como autónomo de extremo a extremo ni como desplegado en producción.
