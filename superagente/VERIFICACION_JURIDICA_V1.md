# SuperAgente — Verificación jurídica documental V1

## Qué queda implementado

1. **Vigilancia oficial:** captura páginas públicas autorizadas, conserva SHA del texto y detecta posibles novedades contra una línea base.
2. **Comparación:** identifica posibles cláusulas de importes y plazos que no coincidan con la guía. Una diferencia es una alerta, no una nueva ley.
3. **Verificación documental:** `scripts/superagente_legal_evidence_gate.py` exige cita literal incluida en el texto oficial capturado, SHA de fuente, SHA de la guía, cambio textual único, territorio, beneficiarios, ayuda, vigencia, excepciones y estado de convocatoria. Rechaza fechas invertidas, capturas fallidas, evidencia obsoleta y contradicciones marcadas.
4. **Aprobación independiente:** necesita un revisor identificable que declare haber contrastado hechos, ámbito y excepciones con una referencia documental. Un texto con nombre o un booleano no es garantía criptográfica ni razonamiento legal autónomo.
5. **Aplicación segura:** `scripts/superagente_verified_batch.py` ejecuta secuencialmente la verificación, crea el manifiesto revisado y llama a `superagente_editorial_loop.py` para editar **solo en ramas batch/**, sin tocar producción. Los SHA impiden aplicar instrucciones sobre versiones desactualizadas.
6. **QA y publicación:** pasan por la validación SEO/móvil del flujo de lotes y la aprobación de despliegue ya existentes. No hay merge, cron, pagos ni publicación automática aquí.

## Ejecución manual con evidencias reales

```bash
python scripts/superagente_verified_batch.py \
  --watchlist superagente/official-watchlist.json \
  --watch-report /ruta/watch-report.json \
  --snapshots /ruta/official-text-snapshots.json \
  --claims /ruta/claims-reviewed.json \
  --review-date 2026-11-07 \
  --output /tmp/verified-batch-preflight.json
```

Solo después de revisar la salida, crear una rama `batch/*` e invocar con `--apply` sobre esa rama. No registrar en GitHub evidencias confidenciales ni inventar firmas de revisión.

## Qué NO puede afirmarse todavía

- **No hace interpretación jurídica autónoma de todas las ayudas.** Detectar un importe y comprobar una cita no garantiza que se aplique a esa familia, fecha o municipio.
- **No completa cobertura nacional.** Hay siete fuentes vigiladas, una de ellas falla; el BOE y muchas convocatorias no están incorporados.
- **No demuestra revisión humana auténtica:** los datos de revisión son atestaciones y aún no se vinculan a identidad de un proveedor con firma verificable.
- **No está activo en producción.** El módulo permanece en la rama del SuperAgente; la reversión de Vercel y la QA visual móvil de una versión autónoma siguen pendientes.
- Una **revisión sin novedades** puede actualizar únicamente su fecha de revisión tras comprobación independiente; `dateModified` conserva la fecha del último cambio real.

**Criterio para declarar completado el módulo autónomo:** pruebas con fuentes oficiales de distintas CCAA, negativas y excepciones legales, detección de cambios que no alteran requisitos, vigencias futuras y convocatorias cerradas; revisión editorial fiable, control de identidad, lote QA y reversión remota confirmados. Si cualquiera falla, no se publica.
