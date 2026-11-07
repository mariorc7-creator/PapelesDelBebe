# SuperAgente — Memoria de decisiones y priorización por impacto

Estado: **prototipo aislado en rama de desarrollo**. No está conectado al cron, no publica, no modifica HTML ni fechas y no sustituye la aprobación editorial.

## Comportamiento

1. Se guarda un registro de decisiones y resultados como eventos JSONL locales, anexados sin sobrescribir el historial previo.
2. Un resultado requiere un identificador de decisión ya existente y confirmación humana con referencia a evidencia. Un resultado negativo obliga a reevaluar antes de repetir una propuesta.
3. Las propuestas incluyen categoría, urgencia, riesgo SEO, coste en euros, esfuerzo en horas, fundamento del beneficio y referencias a evidencias.
4. Se ordenan para **revisión editorial**, ponderando urgencia, impacto estimado, coste, trabajo y riesgo. Las estimaciones son hipótesis: **las puntuaciones no son ingresos previstos ni éxitos garantizados**.
5. Las propuestas de riesgo alto o crítico y las de seguridad o normativa quedan bloqueadas para revisión especializada, aunque su impacto estimado sea elevado.
6. Ningún resultado ni decisión puede permitir un despliegue o alterar por sí mismo páginas indexadas. Cualquier cambio exige pruebas SEO, móvil y aprobación antes de un lanzamiento agrupado.

## Ejemplo de candidato (datos ilustrativos, no reales)

```json
[
  {
    "id": "mejora-navegacion-empadronamiento",
    "title": "Hacer más fácil encontrar el empadronamiento",
    "evidence_ref": "incidencia-ux-por-revisar",
    "category": "ux",
    "seo_risk": "medium",
    "urgency": "high",
    "impact_basis": "unknown",
    "expected_monthly_benefit_eur": null,
    "cost_eur": "0",
    "effort_hours": "2"
  }
]
```

```bash
python scripts/superagente_decision_memory.py \
  --history /ruta/privada/historial.jsonl \
  --candidates /ruta/privada/candidatos.json \
  --output /ruta/privada/cola-editorial.json
```

Para registrar una decisión humana todavía no aprobada:

```json
{
  "schema_version": 1,
  "event_type": "decision",
  "decision_id": "mejora-navegacion-empadronamiento",
  "date": "2026-11-07",
  "title": "Hacer más fácil encontrar el empadronamiento",
  "reason": "Incidencia UX documentada",
  "evidence_ref": "incidencia-ux-por-revisar",
  "category": "ux",
  "seo_risk": "medium",
  "approved": false,
  "deployed": false
}
```

```bash
python scripts/superagente_decision_memory.py \
  --history /ruta/privada/historial.jsonl \
  --append-event /ruta/privada/decision.json
```

Un evento posterior de tipo `outcome` debe referirse al mismo `decision_id`, incluir `result` (`positive`, `negative`, `neutral` o `inconclusive`), `evidence_ref`, `manually_verified: true`, `approved: false` y `deployed: false`. Esto impide que un resultado se utilice para autorizar un despliegue.

**Limitación importante:** la aplicación valida la estructura del evento, pero **no puede comprobar la identidad del editor ni la fiabilidad del documento citado**. La validación humana queda pendiente de integración con un sistema de permisos y evidencias.

No introducir datos de usuarios, credenciales ni informes comerciales privados en el repositorio GitHub. Guardar los JSONL en un entorno privado con copia de seguridad. No alterar el histórico manualmente.

Sin dependencia de GSC Wizard. El cron del SuperAgente permanece desactivado.
