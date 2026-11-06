# Contrato de evidencias editoriales — SuperAgente V0.2

Este contrato valida la **estructura y trazabilidad** de las evidencias. No prueba por sí mismo la interpretación jurídica ni autoriza publicación.

## Entrada opcional al CI

Archivo `superagente/editorial-evidence.json` con objeto `{"records": [...]}` (array no vacío cuando existe). Cada registro debe incluir:

- `page`: URL o ruta de la página revisada.
- `claim`: afirmación concreta que se verifica (por ejemplo, cuantía y requisito).
- `jurisdiction`: ámbito territorial y organismo competente.
- `source_url`: URL HTTPS de evidencia primaria.
- `source_title`: denominación de la fuente.
- `consulted_on`: fecha real de consulta, ISO 8601, nunca futura.
- `effective_on`: fecha de entrada en vigor identificada, ISO 8601.
- `evidence_excerpt`: fragmento preciso de la fuente.
- `verdict`: `coincide`, `difiere` o `no_verificable`.
- `reviewer`: identidad o identificador trazable de quien realizó la revisión.
- `proposed_correction`: obligatorio si `verdict` es `difiere`.

Ejemplo de una **estructura ilustrativa**, NO una revisión realizada ni una afirmación de vigencia:

```json
{
  "records": [{
    "page": "/ayudas/ejemplo/",
    "claim": "Plazo de solicitud ficticio",
    "jurisdiction": "Ejemplo",
    "source_url": "https://www.boe.es/",
    "source_title": "Fuente oficial de ejemplo",
    "consulted_on": "2026-11-06",
    "effective_on": "2026-01-01",
    "evidence_excerpt": "Extracto ficticio para demostrar el formato",
    "verdict": "no_verificable",
    "reviewer": "editor-demo"
  }]
}
```

**No añadir este ejemplo como evidencia real.** El validador comprueba formato, no autenticidad de las afirmaciones, oficialidad del dominio ni correspondencia entre extracto y fuente.

## Invariantes

1. `approved_for_publication: true` es siempre rechazado. La revisión editorial y la autorización de publicación son procesos independientes.
2. `no_verificable` jamás se interpreta como página vigente.
3. Un cambio de huella HTML solo crea una alerta, nunca una corrección automática.
4. La fecha de revisión de página se actualiza únicamente después de verificar contenido y fuente; el `dateModified` se reserva a cambios sustanciales.
5. El control de evidencia es **adicional**, no sustituto, de revisión jurídica, control SEO, QA móvil, aprobación según riesgo, despliegue y rollback.
6. Ningún workflow de evidencia tiene credenciales de escritura ni despliega a PROD.

## Ejecutar

```bash
python -m unittest discover -s scripts -p 'test_superagente_evidence_gate.py' -v
python scripts/superagente_evidence_gate.py superagente/editorial-evidence.json
```

La segunda orden solo se ejecuta cuando exista el archivo con revisiones reales.
