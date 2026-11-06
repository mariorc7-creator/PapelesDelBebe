# Primera auditoría editorial real · 6 de noviembre de 2026

**Alcance:** cinco guías del repositorio, contrastadas con páginas institucionales accesibles. **Resultado: revisión inicial, no verificación jurídica integral ni autorización de publicación.** No se han editado páginas, fechas de revisión ni datos estructurados.

## Resumen

| Página | Primera comprobación | Acción |
| --- | --- | --- |
| Alta del bebé en Seguridad Social | Flujo general coherente con INSS | Verificar enlace transaccional concreto |
| Deducción por maternidad | Máximo de 1.200 €/año coherente con AEAT | Revisar excepciones y guardería por separado |
| Permiso por nacimiento | 19/32 semanas y reparto 6+11+2 coherentes con Seguridad Social | Revisar cohortes y excepciones |
| Ayuda de nacimiento en Cataluña | 650/750 € y límites de renta contrastados | **P1:** concretar plazo histórico de un mes |
| Natalidad Madrid | 500 €/mes, edad, renta y residencia contrastados | **P2:** aclarar que el pago empieza en el mes de solicitud |

## Observación principal · Cataluña

La guía publicada explica que para hechos anteriores al 14 de julio de 2026 existen otras reglas de plazo, sin cuantificar la duración. La ficha de Tràmits Gencat indica un **mes** para hechos causantes hasta el 13 de julio de 2026, inclusive, y **tres meses** desde el 14 de julio de 2026. Proponer incorporar ambos tramos de forma explícita, sin tocar bloques visuales o datos estructurados hasta revisión de la redacción.

Fuente: https://tramits.gencat.cat/es/tramits/tramits-temes/Prestacio-per-a-families-amb-infants?moda=1

## Observación secundaria · Madrid

La guía ya indica el comienzo desde el mes de solicitud; se recomienda hacer más visible esta limitación para evitar que el usuario interprete los 500 €/mes como retroactivos al nacimiento.

Fuente: https://www.comunidad.madrid/asuntos-sociales/ayudas-economicas-natalidad

## Fuentes de contraste adicionales

- INSS, asistencia sanitaria y beneficiarios: https://www.seg-social.es/wps/portal/wss/internet/InformacionUtil/44539/45195?changeLanguage=es
- Revista Seguridad Social, alta de beneficiarios: https://revista.seg-social.es/-/como-dar-de-alta-a-un-beneficiario-en-la-seguridad-social?redirect=%2F
- AEAT, importe de deducción: https://sede.agenciatributaria.gob.es/Sede/ciudadanos-familias-personas-discapacidad/deducciones-relacionadas-hijos-descendientes/deduccion-maternidad/importe-deduccion.html
- AEAT, derecho a deducción: https://sede.agenciatributaria.gob.es/Sede/ciudadanos-familias-personas-discapacidad/deducciones-relacionadas-hijos-descendientes/deduccion-maternidad/quien-corresponde-deduccion.html
- Seguridad Social, prestación: https://prestaciones.seg-social.es/servicio/prestacion-nacimiento-adopcion-cuidado-menor

## Antes de proponer un cambio

1. Volver a comprobar la fuente vigente y asociar captura verificable a cada afirmación concreta.
2. Revisar excepciones y disposiciones transitorias, especialmente fechas de nacimiento.
3. Preparar diff editorial mínimo contra el blob SHA registrado en el JSON adjunto.
4. Ejecutar pruebas de contenidos, SEO y regresión visual móvil.
5. Agrupar en una versión; **sin despliegue ni alteración de fechas por este informe**.

El registro estructurado y los SHA de cada HTML están en `2026-11-06-first-five.json`. La auditoría no certifica la vigencia completa de ninguna guía.
