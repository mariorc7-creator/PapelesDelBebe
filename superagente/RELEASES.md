# Política de paquetes grandes y rollback
- Desarrollar en ramas y PR; agrupar PR verificados en un release candidato cada 2–4 semanas.
- Antes de fusionar: revisión de evidencias oficiales, pruebas de sitemap, SEO y responsive, capturas visuales y revisión de impacto.
- Si hay diferencias visuales no justificadas, detener publicación y revisarlas manualmente.
- Conservar el SHA de main y el identificador del despliegue estable anterior.
- En caso de incidencia confirmada, revertir mediante las capacidades de Vercel/GitHub autorizadas; comprobar páginas críticas tras la reversión.
- Los scripts incluidos en esta fase NO fusionan PR, NO cambian fechas de páginas y NO despliegan automáticamente.
- No habilitar publicación autónoma hasta contar con comprobación de rollback en entorno de prueba, protecciones de rama y credenciales de mínimo privilegio.

## Prueba editorial V0.2 (6 de noviembre de 2026)
- Se ha probado en CI el ciclo de modificación y reversión **local**, en directorio temporal, con igualdad byte a byte y SHA-256 de los dos HTML afectados. Prueba: `scripts/superagente_rollback_proof.py`; informe: artefacto `superagente-local-rollback-proof`.
- Las capturas de antes/después y las pruebas automatizadas de geometría responsive son evidencias técnicas, pero la revisión humana de esas capturas sigue pendiente.
- **No** se ha probado revertir un despliegue de Vercel ni se ha identificado/autorizado un despliegue estable para restaurar. Esto constituye un bloqueo de publicación, no una aprobación.
- Las propuestas de Cataluña y Madrid siguen pendientes de firma editorial y contraste final de vigencia. `superagente/proposals/v02-release-readiness.json` registra estas barreras y prohíbe publicación.
- Un resultado `success` de Release Gate cuando no existe `release-candidate.json` solo significa que no se presentó candidato: no es un visto bueno para publicar.
