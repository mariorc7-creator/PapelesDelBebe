# V0.3 — expedientes editoriales del primer lote

El generador `scripts/superagente_v03_evidence_dossiers.py` transforma el lote de doce tareas en expedientes de investigación reproducibles, anclados al SHA-256 de los HTML de la rama revisada.

Cada expediente incluye:
- Página, prioridad y estado de revisión.
- Huella SHA-256 y tamaño del HTML de partida.
- Administración y jurisdicción, si existe la ruta aprobada.
- Enlace institucional **candidato**, nunca considerado evidencia verificada por el mero hecho de estar registrado.
- Siete casillas pendientes: elegibilidad, importe, plazo, documentación, procedimiento, compatibilidad y enlace oficial.
- Siguiente acción para localizar o comprobar las fuentes.

El archivo `superagente/v03-evidence-dossiers.json` se genera como artefacto de GitHub Actions (no se publica en la web ni se incorpora como contenido legal).

## Criterio de cierre

Para dar una revisión por completada, deben documentarse textos verificables de la fuente, su procedencia y aplicabilidad temporal y territorial, la comparación precisa con las afirmaciones de la guía y la aprobación editorial independiente. Las casillas vacías no generan fechas de revisión.

**Estados por defecto:** 0 afirmaciones normativas verificadas por esta generación, 0 páginas validadas, publicación prohibida. Son plantillas que preparan el trabajo real; no sustituyen una auditoría legal.

## Barreras

No se cambian HTML, metadatos `dateModified`, fechas `lastmod`, fechas visibles de revisión, enlaces de afiliados ni producción. La prueba de reversión local funciona, pero aún falta verificar un rollback en staging.
