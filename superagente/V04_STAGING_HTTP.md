# V0.4 — ensayo HTTP de staging efímero y reversión

Implementado en `scripts/superagente_cataluna_staging_http.py`.

## Qué se prueba

1. Leer la propuesta **no aprobada** de dos correcciones para `ayuda-nacimiento-cataluna/index.html`.
2. Comprobar los anchors y la evidencia editorial asociada.
3. Crear una carpeta temporal **fuera del checkout**, con la página original.
4. Servir la misma carpeta con un servidor HTTP ligado exclusivamente a `127.0.0.1` y puerto efímero.
5. Hacer una solicitud HTTP de la versión inicial y verificar código 200 y SHA-256.
6. Sustituir únicamente la página temporal por la versión propuesta y comprobar otra solicitud HTTP.
7. Restaurar los bytes originales **en la misma ruta servida**, volver a solicitar la página y comprobar la igualdad exacta con la respuesta inicial.
8. Verificar que el archivo original del checkout no se haya modificado y cerrar servidor y carpeta temporal.

Se genera `superagente/proposals/cataluna-local-staging-rollback.json` como artefacto de **SuperAgente - Editorial Evidence CI**. El resultado incluye tres huellas, tres códigos HTTP y declaraciones explícitas `remote_staging_deployment_tested=false`, `production_rollback_tested=false`, `publication_allowed=false`.

## Interpretación precisa

Esta es una prueba real de ciclo HTTP en **staging local efímero de CI**, no un despliegue en Vercel, GitHub Pages u otro hosting de staging real. Comprueba integridad y reversibilidad del contenido servido, pero no CDN, configuración de rutas del hosting, cachés, variables de entorno o rollback de despliegue en proveedor.

## Pendiente antes de un despliegue

- Sincronizar la rama de desarrollo con `main` (hay cuatro commits posteriores en el momento de preparar esta prueba, relacionados con cómics y Buffer X).
- Obtener aprobación editorial independiente para los dos cambios y sus excepciones normativas.
- Probar un despliegue real en un entorno remoto de staging y un rollback del proveedor.
- Revisar el resultado en móvil y los metadatos SEO.
- Mantener las publicaciones y fechas de revisión bloqueadas hasta la aprobación y el paquete de versión grande.
