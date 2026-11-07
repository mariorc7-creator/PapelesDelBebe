# SuperAgente — cola de revisión editorial

## Proceso verificable
1. Seleccionar una URL del inventario de `sitemap.xml`.
2. Identificar la administración competente y la fuente primaria vigente.
3. Comprobar individualmente: elegibilidad, cuantía, plazo, documentos, procedimiento, compatibilidades y enlace oficial.
4. Registrar evidencias específicas, fecha, revisor y URL de fuente con `python scripts/superagente_reviews.py verify ...`.
5. Si el resultado es `changed`, preparar una propuesta editorial separada y revisar SEO/GEO/UX.
6. Si el resultado es `unchanged`, no cambiar el contenido ni el `dateModified`. La fecha visible de revisión solo se actualizará cuando exista integración editorial que la vincule a evidencia real.
7. Si la fuente no permite verificar la información, registrar `unverifiable` y escalar; no afirmar vigencia.

## Seguridad
El monitor HTTP solo acepta una lista reducida de dominios oficiales, sin redirecciones. Los demás quedan pendientes de revisión manual. Disponibilidad de una fuente no equivale a validez legal ni a revisión de la página.

## Límites actuales
La verificación semántica y jurídica sigue requiriendo un proceso fiable adicional. No hay cambios editoriales automáticos ni despliegue a PROD. La cola de trabajo se agrupará en versiones grandes.
