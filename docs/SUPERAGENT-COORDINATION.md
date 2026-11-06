# SuperAgente: coordinación SEO + Amazon + QA (fase staging)

El SuperAgente es **un coordinador lógico**, no cuatro procesos autónomos en ejecución.
`config/superagent-modules.json` recoge permisos, etapas y puertas de calidad.

## Ejecutar en rama de pruebas
`python3 scripts/superagent_coordinator.py`

Genera `reports/amazon-affiliates-audit.json` y
`reports/superagent-coordination.json`. La ejecución es de solo lectura
sobre el sitio: únicamente escribe informes locales. **No** modifica la
web, ni activa cron, ni fusiona PR, ni llama a Vercel.

## Contrato de integración
- SEO propone contenido; Amazon propone productos y enlaces autorizados.
- QA valida compatibilidad con CSS actual, responsive móvil, atribución, accesibilidad y fuentes.
- El coordinador agrupa varias mejoras en un PR en borrador, con posibilidad de reversión.
- No se publica contenido sin evidencia editorial ni se presumen ventas o comisiones.
- La verificación visual móvil no está automatizada aún y bloquea la publicación.
- Los módulos SEO y Growth están definidos como responsabilidades, no conectados de
  forma operativa en esta rama.

## Estado y límite
La automatización diaria de ChatGPT **no se ha modificado** desde esta
implementación. La integración de su prompt/ejecución con este manifiesto
requiere acceso a la tarea activa y confirmación de capacidades en cada ejecución.
No se debe afirmar que una ejecución programada revisó GitHub si no hay logs.
