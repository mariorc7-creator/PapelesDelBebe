# SuperAgente V0.2 — enlace entre HTML y evidencia editorial

## Objetivo

Evitar que el agente redacte una corrección sobre contenido que haya cambiado desde la extracción.

1. `superagente_claim_inventory.py` genera candidatos desde el HTML actual.
2. Un revisor o proceso de verificación independiente prepara `superagente/semantic-triage-input.json` con los campos del contrato de triaje **más** `paragraph_sha256` del inventario.
3. `superagente_linked_triage.py` busca coincidencia exacta de URL y `claim_id`, compara huella del párrafo, valor publicado y tipo.
4. Registros inexistentes, ambiguos, duplicados, obsoletos o con evidencias incompletas quedan `blocked` y causan error en CI.
5. Las coincidencias y diferencias se clasifican para revisión editorial; **ninguna permite publicar**.

## Ejecución

```bash
python scripts/superagente_claim_inventory.py
python scripts/superagente_linked_triage.py --inventory superagente/claim-inventory.json --comparisons superagente/semantic-triage-input.json
python -m unittest discover -s scripts -p 'test_superagente_linked_triage.py' -v
```

El archivo de entrada de comparaciones es opcional, y no debe crearse con datos ficticios para dar una apariencia de verificación. El informe resultante `superagente/linked-triage-report.json` solo es una cola de trabajo.

## Limitaciones importantes

- Las huellas identifican párrafos extraídos, no ofrecen una garantía absoluta de anclaje DOM.
- Comparar valores y fuente declarada no equivale a consultar una norma ni determinar su vigencia jurídica.
- No se cambia HTML, SEO, fecha de revisión ni `dateModified`.
- La futura generación de diffs debe usar el original vigente y ejecutar regresiones visuales/funcionales.
- La publicación a producción sigue inhabilitada hasta CI comprobado, rollback probado y política de riesgos aplicada.
