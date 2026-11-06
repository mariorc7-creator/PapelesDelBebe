# V0.3 — integridad documental de afirmaciones

Se ha añadido `scripts/superagente_exact_document_links.py` para comprobar que cada afirmación sometida a validación usa una **URL exacta**, no solo un dominio oficial.

Al recibir `superagente/semantic-triage-input.json` junto con `superagente/source-captures.json`, el CI comprueba conjuntamente:

1. La URL de la afirmación coincide exactamente con un documento expresamente autorizado en `superagente/official-watchlist.json` (las portadas genéricas no habilitan afirmaciones).
2. Existe una captura asociada a esa misma URL sin entradas duplicadas.
3. El SHA-256 del texto capturado coincide con el texto aportado.
4. El extracto de la afirmación aparece realmente en el texto de la captura.

Se rechaza que una referencia de `official-document-candidates.json` autorice una afirmación por sí sola. No se han promovido a autorizadas las cinco referencias candidatas. El manifiesto de capturas sigue vacío/no presentado.

**Limitación crítica:** estas comprobaciones prueban integridad interna del material aportado, **no** que la descarga proceda realmente del organismo emisor ni que la interpretación jurídica sea válida. El capturador HTTP aún presenta riesgo de cambio de DNS entre validación y conexión (TOCTOU), por lo que no debe habilitarse una captura autónoma generalizada hasta usar una conexión que fije y verifique el destino de red. La ejecución bajo demanda sigue separada de las auditorías periódicas.

No hay actualización automática de páginas, fechas ni despliegues. Los 12 expedientes del primer lote siguen pendientes de evidencia independiente.
