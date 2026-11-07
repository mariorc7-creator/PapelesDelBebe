# SuperAgente — Entrega de integración V1 (7 noviembre 2026)

**Alcance ejecutado:** coordinador offline sobre los módulos de inventario Amazon, recomendaciones mensuales de afiliación, memoria de decisiones, clasificación por impacto/coste/riesgo SEO, revisión de presupuesto y comprobación del estado de reversión Vercel. Genera una **cola editorial consolidada** y un **informe ejecutivo**.

**No significa que haya un SuperAgente autónomo de extremo a extremo en producción**. Las fuentes oficiales, la indexación, los informes privados y el análisis UX siguen dependiendo de sus propios conectores y comprobaciones. La publicación no está conectada ni autorizada.

## Ejecutar una auditoría integrada sobre las fuentes disponibles

```bash
python scripts/superagente_amazon_audit.py --output /tmp/amazon-static-audit.json
python scripts/superagente_integrated.py \
  --amazon-audit /tmp/amazon-static-audit.json \
  --staging-report superagente/V04_REMOTE_STAGING_REPORT.json \
  --output-dir /tmp/superagente-integracion
```

Produce `superagente-integrado.json` (cola completa, evidencias, puntos de control) y `superagente-ejecutivo.md` (resumen legible).

El reporte de staging conocido evidencia que el rollback del Git está comprobado pero **la reversión remota de Vercel no se ha verificado**. Esto impide dar un futuro despliegue por seguro.

## Entradas opcionales privadas

- `--affiliate-monthly /ruta/privada/affiliate-monthly-YYYY-MM.json`: cifras importadas desde informes privados; la integración no calcula atribuciones ni ingresos inexistentes.
- `--history /ruta/privada/historial.jsonl`: memoria local con decisiones y resultados verificados.
- `--proposals /ruta/privada/propuestas.json`: array de candidatos de SEO, UX, contenido y mantenimiento, **cada uno con evidencias** siguiendo `DECISION_MEMORY_V01.md`.
- `--budget-eur 100`: tope opcional de coste estimado de ejecución; una estimación superior bloquea la autorización (que sigue deshabilitada en todos los casos).

No subir archivos privados o datos de usuarios a GitHub. Los artefactos de GitHub Actions solo incluyen la auditoría estática y el reporte de staging del repositorio. El motor no añade datos falsos de tráfico, clics, comisiones o conversiones.

## Reglas no negociables

1. No habilitar la automatización semanal todavía.
2. Sin GSC Wizard.
3. No ejecutar despliegues, merge a main, comprar planes ni modificar páginas indexadas desde este coordinador.
4. Mantener estructura de URLs, canonical, sitemap, fechas de revisión, estilo y UX móvil hasta revisión humana y comprobaciones.
5. Una propuesta con riesgo SEO alto/crítico, materia legal/seguridad o antecedentes negativos queda retenida.
6. Las puntuaciones indican **orden de análisis**, nunca una promesa de ingresos.
7. Generar paquetes grandes y documentados **cuando** exista autorización, validación real de Vercel/QA y procedimientos de reversión confirmados.

## Pendiente para la versión operativa

- Integrar señales SEO oficiales verificadas con los correspondientes módulos sin crear dependencia de servicios excluidos.
- Fuentes privadas autorizadas para clics de afiliación, pedidos y comisiones; actualmente no hay lectura automática válida de estas métricas.
- Completar la captura formal de decisiones de publicación y las mediciones posteriores.
- Validar reversión remota Vercel, permisos y pruebas visuales de móvil, antes de plantear despliegue.
- Conectar una ejecución coordinada periódica **solo después de autorización expresa**.

**Esta entrega transforma módulos existentes en un informe coordinado, pero no autoriza el funcionamiento desatendido de un negocio ni garantiza rentabilidad.**
