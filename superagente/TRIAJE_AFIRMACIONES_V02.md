# SuperAgente V0.2 — comparación de afirmaciones

## Entregado
- `scripts/superagente_semantic_triage.py` clasifica afirmaciones emparejadas explícitamente con una fuente, fecha de consulta, fecha de vigencia y revisor.
- `scripts/test_superagente_semantic_triage.py` contiene pruebas unitarias de seguridad.
- `superagente-evidence.yml` ejecuta las pruebas y procesa opcionalmente `superagente/semantic-triage-input.json`.

## Formato de entrada
```json
{
  "claims": [{
    "page": "/ayudas/ejemplo/",
    "claim_id": "cuantia-1",
    "kind": "amount",
    "published_value": "100 euros",
    "official_value": "200 euros",
    "source_url": "https://www.boe.es/",
    "source_excerpt": "EJEMPLO FICTICIO. No es evidencia real.",
    "consulted_on": "2026-11-06",
    "effective_on": "2026-01-01",
    "jurisdiction": "España",
    "reviewer": "ejemplo-editor"
  }]
}
```

No incorporar el ejemplo al repositorio como evidencia real. La entrada debe provenir de un proceso de verificación independiente.

## Salidas
- `difference_needs_review`: los textos comparados difieren; se incluye `proposed_value` sin generar cambios en la web.
- `text_matches_needs_review`: coincidencia normalizada de texto; **no** garantiza vigencia ni equivalencia jurídica.
- `blocked`: datos incompletos, URL de fuente inválida o fecha de vigencia/consulta futura.

Todas las salidas exigen revisión semántica y jurídica; `publishable` siempre es falso en los registros válidos. No se cambian fechas, páginas ni configuración de despliegue.

## Pendiente para llamarlo 'motor semántico'
1. Vincular afirmaciones a párrafos y campos concretos de cada página mediante IDs estables.
2. Obtener evidencia real de páginas y normas oficiales, con trazabilidad y límites de confianza.
3. Interpretar la vigencia según ámbito territorial, perfil familiar, compatibilidades y disposiciones transitorias.
4. Aprobar cambios con revisión independiente y diffs sobre el HTML.
5. Integrar el gate con controles responsive/visual y con publicación segura por paquetes.

**Esta entrega es clasificación reproducible, no verificación normativa automática.**
