# Vigilancia de cambios oficiales

El workflow `SuperAgente - Vigilancia fuentes oficiales` comprueba dos URLs oficiales iniciales los lunes y jueves, además de ejecutarse manualmente y en PR.

- El listado de URLs está en `official-watchlist.json`. Cada dominio debe coincidir exactamente con el host aprobado.
- Se rechazan redirecciones, hosts privados, contenido no HTML y respuestas superiores a 1 MB.
- Se normaliza el texto visible y se calcula SHA-256.
- Si falta una huella anterior, el resultado es `baseline_missing`, no una alerta legal.
- Para comparar en futuras ejecuciones debe proporcionarse un `official-baseline.json` revisado. **No existe actualización automática de la línea base**.
- Un cambio de huella significa que cambió el texto visible, no necesariamente la norma.
- El informe no modifica la web, el registro de revisión ni las fechas.

**Pendiente:** seleccionar URLs oficiales específicas para cada ayuda, registrar una línea base validada, persistir historial de cambios y realizar comparación semántica con fuentes primarias. Las dos URLs iniciales son generales y no bastan para verificar prestaciones concretas.
