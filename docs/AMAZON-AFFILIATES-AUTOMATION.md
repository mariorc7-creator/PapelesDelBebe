# Amazon Afiliados — automatización aislada (06/11/2026)

Estado: propuesta técnica en rama feature; **sin despliegue, sin publicación programada**.

## Situación detectada
- El sitio está en un repositorio estático sin package.json en la raíz.
- `preparativos-bebe/index.html` ya contiene enlaces de búsqueda a Amazon con `tag=mariorc7-21`, disclosure y eventos de clic.
- El workflow de auditoría solo se ejecuta manualmente (workflow_dispatch), no hace commits, no publica ni modifica HTML.

## Ejecutar en local
`python3 scripts/audit_amazon_affiliates.py --expected-tag mariorc7-21`

El auditor genera `reports/amazon-affiliates-audit.json`; un código de salida distinto de cero significa incidencias para revisión. Puede detectar enlaces en HTML y URLs literales JS, pero **no** certifica disponibilidad, cookies, conversiones, destino final ni validez de productos.

## Siguiente fase (no implementada)
1. Catálogo editorial validado (categoría, guía asociada, justificación, URL especial obtenida legalmente y fecha de revisión).
2. Separar selección de productos de su presentación HTML; conservar CSS y responsive actuales.
3. Tests de enlace, rel, disclosure, accesibilidad y capturas móviles antes de crear PR.
4. Importar datos de rendimiento solo por mecanismos autorizados y sin información individual de visitantes.
5. Proponer paquetes grandes mediante PR; nunca fusionar o desplegar automáticamente sin superar controles.
6. Activar procesos periódicos solo tras revisión de permisos y fuentes.

## Reglas de cumplimiento
- No raspar Amazon, ni descargar imágenes de terceros sin licencia ni inventar precios, valoraciones o disponibilidad.
- Los precios y la disponibilidad solo se muestran mediante mecanismos expresamente autorizados por Amazon.
- Declaración visible de afiliación y `rel="sponsored nofollow noopener noreferrer"` para enlaces externos.
- No generar sub-tags individualizados por usuario ni premios por hacer clic.
- Identificador leído del código ya existente; verificar en el panel que corresponde a la cuenta y sitio.
- No publicar reseñas ficticias ni afirmaciones sin evidencia.

Documentación oficial: https://afiliados.amazon.es/help/operating/policies
