# V0.3 — integridad documental de afirmaciones

Se ha añadido `scripts/superagente_exact_document_links.py` para comprobar que cada afirmación sometida a validación usa una **URL exacta**, no solo un dominio oficial.

Al recibir `superagente/semantic-triage-input.json` junto con `superagente/source-captures.json`, el CI comprueba conjuntamente:

1. La URL de la afirmación coincide exactamente con un documento expresamente autorizado en `superagente/official-watchlist.json` (las portadas genéricas no habilitan afirmaciones).
2. Existe una captura asociada a esa misma URL sin entradas duplicadas.
3. El SHA-256 del texto capturado coincide con el texto aportado.
4. El extracto de la afirmación aparece realmente en el texto de la captura.

Se rechaza que una referencia de `official-document-candidates.json` autorice una afirmación por sí sola. No se han promovido a autorizadas las cinco referencias candidatas. El manifiesto de capturas sigue vacío/no presentado.

**Limitación crítica:** estas comprobaciones prueban integridad interna del material aportado, **no** que la descarga proceda realmente del organismo emisor ni que la interpretación jurídica sea válida. El capturador HTTPS V0.3 ya selecciona una IP pública tras una única resolución DNS y conecta a esa IP literal, conservando SNI y la validación del certificado TLS del dominio original. Esto evita una segunda resolución DNS al conectar y reduce el riesgo TOCTOU del capturador anterior. Aun así, hay que validar el proceso de captura frente a fuentes concretas y mantenerlo bajo demanda. La conexión TLS y el hash no sustituyen el contraste de vigencia, procedencia editorial o aplicabilidad jurídica. La ejecución bajo demanda sigue separada de las auditorías periódicas.

No hay actualización automática de páginas, fechas ni despliegues. Los 12 expedientes del primer lote siguen pendientes de evidencia independiente.
