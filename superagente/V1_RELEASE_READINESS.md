# SuperAgente V1.0 — Entrega técnica y bloqueo operativo

Fecha de comprobación: **2026-11-07**.

## Qué está integrado

- Coordinador de tareas y priorización editorial con memoria de decisiones y resultados.
- Auditorías de enlaces de afiliación de Amazon; importación normalizada de clics y comisiones; informes mensuales sin datos inventados.
- Revisiones técnicas y colas de fuentes oficiales, contenido, SEO y experiencia móvil a través de workflows de CI independientes.
- Puerta de publicación que exige evidencia editorial, controles SEO/móvil y reversión.
- `scripts/superagente_v1_readiness.py`: evaluación explícita de si se puede **plantear** una activación supervisada.
- Informes de GitHub Actions sin datos comerciales privados ni secretos.

## Resultado actual y límites

La **base técnica está desarrollada**, pero la **operación autónoma V1.0 no está lista ni habilitada**. No existe publicación automática, no se garantiza acceso a informes Amazon ni a clics de Vercel, y la reversión remota de la preview anterior aún no consta verificada.

Antes de activar el agente faltan:

1. Evidencias oficiales y protección SEO de una base verificada.
2. Pruebas de UX móvil completas y revisión de los contenidos específicos.
3. Prueba de reversión remota en Vercel documentada y validada.
4. Validación de accesos y permisos para datos privados, sin contratar planes sin autorización.
5. Aprobación editorial formal de la versión candidata.

El fichero `superagente/v1-readiness-evidence.json` mantiene esos requisitos en `false` deliberadamente. **No se debe rellenar con `true` sin evidencias y revisión humana.**

## Prueba local de integración

```bash
python scripts/superagente_amazon_audit.py --output /tmp/amazon-audit.json
python scripts/superagente_integrated.py \
  --amazon-audit /tmp/amazon-audit.json \
  --staging-report superagente/V04_REMOTE_STAGING_REPORT.json \
  --output-dir /tmp/superagente-v1
python scripts/superagente_v1_readiness.py \
  --integrated-json /tmp/superagente-v1/superagente-integrado.json \
  --evidence superagente/v1-readiness-evidence.json \
  --output /tmp/superagente-v1/preparacion.json
```

El resultado correcto actual es **blocked**. Esta salida es una garantía de cautela, no un fallo del código. Los workflows automatizados pueden ejecutarse en PR para validar el código, pero **no hay cron de GitHub que active vigilancia desatendida en la rama del SuperAgente**.

## Separación respecto al paquete regional

El despliegue regional **v2.5–v3.1** utiliza la rama `release/regional-v25-v31-20261107` y el PR borrador **#30**. Su puerta de publicación sigue bloqueada hasta que estén implementadas las siete regiones con fuentes oficiales, pruebas SEO/móvil y reversión remota comprobada. Nunca fusionar la rama completa de SuperAgente como sustituto de ese paquete regional.

## Instrucciones permanentes

- **No utilizar GSC Wizard.**
- **No activar las automatizaciones periódicas** hasta autorización explícita del propietario.
- No fusionar PR #26 a `main` por el mero hecho de superar pruebas unitarias.
- No modificar páginas indexadas, fechas de revisión, canonical, sitemap, URLs ni UX móvil sin comprobaciones y revisión.
- Priorizar paquetes grandes de cambios sustanciales, con reversión comprobada antes de desplegar.
- No hacer afirmaciones sobre ventas, resultados SEO o beneficios futuros sin datos contrastados.

La distinción de producto es: **V1.0 técnica en rama de desarrollo**, **V1.0 operativa pendiente de requisitos externos comprobables**.
