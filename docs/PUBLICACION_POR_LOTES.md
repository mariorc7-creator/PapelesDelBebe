# Publicación simplificada por lotes — Papeles del Bebé

## Objetivo

Reducir las previsualizaciones innecesarias y publicar paquetes grandes, manteniendo SEO, UX móvil, fuentes oficiales y posibilidad de reversión.

**Aplicación:** futuras actualizaciones de contenido, no los cambios ya publicados. Ningún cron ni automatización del SuperAgente se activa con este flujo.

## Flujo recomendado

1. Crear una rama `batch/tema-fecha` a partir del `main` actualizado.
2. Preparar y corregir todas las páginas del lote en esa rama. Los commits intermedios **no generan despliegues automáticos de Vercel** gracias a `git.deploymentEnabled["batch/*"]=false`.
3. Abrir **un PR** hacia `main`. GitHub Actions ejecuta un control unificado de cada lote y compila la web completa una vez por ejecución. Si se reciben cambios rápidos mientras sigue ejecutándose una prueba de ese mismo PR, el job antiguo se cancela y solo se valida el estado más reciente.
4. Comprobar las fuentes oficiales y registrar la revisión editorial humana de cuantías, plazos, vigencia y estado de convocatoria. El control automático no puede garantizar que la información legal sea correcta.
5. Cuando las pruebas pasen, lanzar **una preview explícita y puntual** del SHA de la rama, comprobar las páginas en desktop y móvil y guardar el resultado. Vercel no la creará automáticamente para `batch/*`: alguien debe solicitarla deliberadamente con el proyecto y SHA correctos.
6. Una vez aprobada la preview y conocida la versión estable de reversión, **fusionar una sola vez a main**. Vercel producirá un despliegue de producción normal. Confirmar READY, alias público y HTTP de las URLs relevantes.
7. Si falla la publicación, revertir hacia el deployment estable identificado previamente y confirmar la recuperación del dominio.

## Qué verifica el control automático

- Un H1, header, main, footer, canonical HTTPS, title y viewport.
- IDs HTML no duplicados.
- Conservación de canonical, meta robots, viewport y estructura previa.
- Ausencia de nuevos enlaces HTTP inseguros o esquemas javascript.
- Que cambios en CSS, JS, sitemap, redirects o `vercel.json` se gestionan como entrega técnica separada si se mezclan con páginas de contenido.
- Compilación con `node scripts/build-static.cjs`, que realiza verificaciones adicionales de sitemap y URLs prioritarias.

## Límites honestos

- No autentica enlaces externos ni valida automáticamente la legalidad de una ayuda.
- No sustituye pruebas visuales reales de móvil ni pruebas HTTP de una preview protegida.
- El sistema no hace merge ni despliegue por sí solo.
- Cada PR o actualización del PR ejecuta las comprobaciones, pero **los pushes intermedios a ramas batch/* no crean previews automáticas**.
- Para correcciones urgentes se puede usar una rama normal y seguir el procedimiento de hotfix existente.
- No desactiva `main`: la publicación de producción permanece automática tras un merge autorizado.
- No publicar la rama del SuperAgente como sustituto de una actualización de contenido. No utilizar GSC Wizard.

Los artefactos de usuario y los datos de afiliados privados no deben entrar en este circuito.

## Comandos de prueba

```bash
python -m unittest discover -s scripts -p 'test_batch_release_check.py' -v
node scripts/build-static.cjs
python scripts/batch_release_check.py --base <SHA_BASE_40_CARACTERES> --output /tmp/batch-release.json
```

**Regla de operación:** una rama, un PR, un conjunto de pruebas por versión candidata, una preview deliberada y un merge a producción, sin microdespliegues. Los bloqueos de SEO o contenido oficial prevalecen sobre la rapidez.
