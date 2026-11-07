# SuperAgente Papeles del Bebé — política de seguridad
Estado: fase de implementación. No hay publicación autónoma habilitada.

## Principios
- Revisar una guía NO implica modificar su contenido ni su fecha `dateModified`.
- `fecha_revision` solo se modifica después de contrastar efectivamente fuentes oficiales y guardar evidencia.
- Si no se pudo verificar una ayuda, marcar `no_verificado`; nunca inventar vigencia.
- Mantener intactos diseño, componentes, estilo visual y experiencia móvil.
- Pruebas responsive obligatorias: 320, 375, 430, 768 y 1440 px; validar enlaces, formularios, navegación y ausencia de desbordamiento.
- Aplicar SEO, GEO y UX proporcionalmente a los cambios; no reescribir por reescribir.
- Agrupar cambios en versiones grandes y coherentes (objetivo 2-4 semanas); excepciones para fallos críticos.
- Prohibido desplegar a PROD hasta que estén implantados y verificados pruebas visuales, controles de riesgo, rollback y credenciales restringidas.
- Riesgo alto (URLs, arquitectura, privacidad, credenciales, cambios masivos): aprobación humana.
- Registrar PR, fuentes, resultados de pruebas, alcance y versión desplegada.
- No generar o cambiar fechas de revisión a partir de una auditoría meramente técnica.

## Estado de los controles
- Inventario local desde sitemap: inicial.
- Validación de rutas y metadatos: inicial.
- Verificación de fuentes oficiales: pendiente.
- Pruebas visuales Playwright: pendiente.
- Paquetes y rollback automatizados: pendiente.
- Publicación autónoma: DESHABILITADA.
