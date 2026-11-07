# SuperAgente — medición de Amazon Afiliados (fase de conexión)

**Estado:** solo rama de desarrollo; no despliegue a producción; no automatización periódica.

## Datos disponibles y limitaciones verificadas (7 noviembre 2026)

- La sección de Preparativos ya emite el evento `preparativos_afiliado` en el código de Vercel Analytics mediante `window.va`, con `category` como dimensión.
- La consulta autenticada de eventos personalizados de Vercel dio HTTP **402**: requiere plan Pro o Enterprise; la cuenta actual es Hobby. **No se han recuperado cifras de clics.**
- GSC Wizard rechazó las consultas por suscripción inactiva. **No se ha recuperado analítica desde GSC Wizard.**
- No hay acceso conectado a los informes privados de Amazon Associates. **No se han recuperado pedidos ni comisiones.**
- Ninguna de estas limitaciones autoriza contratar un plan de pago, extraer credenciales ni fingir cifras.

## Importación manual controlada — sin cambiar la web

Se ofrecen dos archivos CSV **normalizados por el responsable**, que se preparan localmente a partir de los informes descargados desde la cuenta correspondiente.

**Clics registrados por Vercel Analytics** (`clicks.csv`):

```csv
date,category,clicks
```

Solo incluir clics reales del evento `preparativos_afiliado`, separados por fecha y categoría. No reemplazar los eventos por visitas o impresiones.

**Informe de Amazon Associates** (`amazon.csv`):

```csv
date,ordered_items,shipped_items,commission_eur
```

Solo incluir columnas verificadas del informe oficial. `commission_eur` es importe neto, puede ser negativo por devoluciones. No reinterpretar pedidos como compras atribuidas a un producto concreto si Amazon no proporciona ese dato. Usar importes en euros y decimales con punto.

El módulo **no afirma** que los CSV estén autenticados: un editor debe comprobar su origen y correspondencia de columnas. No subir CSV privados a GitHub ni a artefactos de Actions.

Para generar el análisis en un equipo local:

```bash
python scripts/superagente_affiliate_performance.py \
  --clicks-csv /ruta/privada/clicks.csv \
  --amazon-csv /ruta/privada/amazon.csv \
  --start 2026-11-01 --end 2026-11-30 \
  --output /ruta/privada/affiliate-performance.json
```

Cada CSV puede omitirse individualmente, pero hay que aportar al menos uno. Las fuentes ausentes se muestran como `null`, **no como cero**. No se calcula tasa de conversión porque no existe atribución entre el clic en Vercel y el pedido de Amazon. El número de filas y de días es solo cobertura de los archivos suministrados; los días ausentes no equivalen a cero.

## Próximos pasos, separados de los ya realizados

1. Validar el formato del export real de cada plataforma y crear adaptadores comprobados; **no afirmar que las columnas CSV normalizadas son las columnas nativas**.
2. Comprobar autorización, disponibilidad y coste antes de activar una lectura directa por API o un export automatizado.
3. Habilitar un informe agregado mensual con evidencias verificadas, fecha y fuente, y propuestas comerciales con aprobación humana.
4. Mantener desactivado el cron y exigir QA SEO/móvil antes de cualquier cambio en páginas indexadas.

El análisis no modifica HTML, canonical, sitemap, redirecciones, diseño ni fechas de revisión.
