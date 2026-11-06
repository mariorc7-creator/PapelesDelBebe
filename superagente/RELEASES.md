# Política de paquetes grandes y rollback
- Desarrollar en ramas y PR; agrupar PR verificados en un release candidato cada 2–4 semanas.
- Antes de fusionar: revisión de evidencias oficiales, pruebas de sitemap, SEO y responsive, capturas visuales y revisión de impacto.
- Si hay diferencias visuales no justificadas, detener publicación y revisarlas manualmente.
- Conservar el SHA de main y el identificador del despliegue estable anterior.
- En caso de incidencia confirmada, revertir mediante las capacidades de Vercel/GitHub autorizadas; comprobar páginas críticas tras la reversión.
- Los scripts incluidos en esta fase NO fusionan PR, NO cambian fechas de páginas y NO despliegan automáticamente.
- No habilitar publicación autónoma hasta contar con comprobación de rollback en entorno de prueba, protecciones de rama y credenciales de mínimo privilegio.
