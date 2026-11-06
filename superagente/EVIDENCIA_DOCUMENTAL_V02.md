# SuperAgente V0.2 — evidencia documental reproducible

Esta entrega valida que una cita aportada está presente en una captura textual y comprueba la integridad de dicha captura. **No prueba automáticamente que la captura proceda de la web oficial ni que la interpretación legal sea correcta.**

## Flujo de verificación

1. Detectar un candidato factual del HTML y su anclaje en `claim-inventory.json`.
2. Obtener contenido oficial mediante un proceso independiente y autorizado, siguiendo redirecciones, DNS y límites de descarga seguros. Conservar URL, fecha, documento original y procedencia verificable.
3. Preparar `superagente/source-captures.json` con `captures`, cada uno con `source_url`, `text`, `sha256` (hexadecimal SHA-256 sobre UTF-8 exacto del texto) y `captured_on` (ISO fecha).
4. Preparar `semantic-triage-input.json` con afirmaciones y fragmento de evidencia `source_excerpt`, `consulted_on` y la huella del párrafo publicado.
5. CI rechaza fuentes no autorizadas, capturas inexistentes, cambios de contenido no reflejados en su SHA-256, citas ausentes, fechas incorrectas, párrafos obsoletos o reclamaciones duplicadas.
6. Una coincidencia únicamente habilita revisión editorial; nunca publicación ni actualización de fechas.

## Limitaciones críticas

- La captura puede ser suministrada por un actor no confiable: el SHA solo demuestra integridad interna, **no autenticidad de origen**. Falta un proceso fiable de recuperación y vinculación al documento original.
- El contenido puede estar sujeto a excepciones, disposiciones transitorias, criterios autonómicos o situaciones personales no expresadas en la cita.
- No debe guardarse información personal o documentos de terceros en el repositorio.
- No deben fusionarse propuestas con información normativa sin revisión independiente de vigencia y aplicabilidad.
- Aún falta validación de la ejecución CI real y QA visual/funcional, permisos mínimos y rollback probado.

## Política de despliegue

Este mecanismo no modifica HTML, fechas ni datos de negocio. La publicación autónoma está deshabilitada. Los cambios se mantienen en la rama del SuperAgente y se prepararán en paquetes grandes.
