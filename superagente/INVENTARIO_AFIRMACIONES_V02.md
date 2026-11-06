# SuperAgente V0.2 — inventario de afirmaciones en páginas reales

## Qué hace
`python scripts/superagente_claim_inventory.py` recorre las URLs relevantes de `sitemap.xml`, busca sus archivos `index.html`, extrae candidatos de cuantías y plazos de bloques de texto y emite `superagente/claim-inventory.json`.

Cada candidato incluye:
- URL y archivo real de la web.
- `claim_id` reproducible para esa combinación de URL, posición aproximada, tipo y valor.
- Texto del párrafo, huella SHA-256 y pista de ubicación `selector_hint`.
- Estado `pending_official_source`.

**Cuidado:** las pistas de ubicación no son selectores CSS fiables: `nth-of-type` refleja el orden de extracción, no necesariamente el de todos los hermanos del DOM. El identificador puede variar si se modifican valores o la estructura; no es un ID permanente. El texto del párrafo puede incluir lenguaje legal ambiguo o cifras de ejemplos.

## Garantías
- El script no escribe HTML, fechas de revisión, metadatos ni páginas.
- La salida se genera únicamente como artefacto de CI con retención limitada.
- Las cifras detectadas NO acreditan su vigencia ni significado normativo.
- La coincidencia con una fuente oficial NO acredita equivalencia legal; requiere contraste de jurisdicción, elegibilidad y fecha de vigencia.
- No hay despliegue autónomo ni permisos de escritura en el workflow.

## Próxima integración
1. Vincular candidatos de inventario con evidencia oficial verdaderamente comprobada, no introducida de forma ficticia.
2. Mantener el anclaje contra cambios concurrentes en el HTML y detectar obsolescencia de evidencias.
3. Preparar diffs de texto mínimo, conservando diseño y UX móvil.
4. Añadir pruebas visuales y funcionales a cada propuesta editorial.
5. Requerir gates completos antes de publicar paquetes; rollback probado.

## Ejecutar pruebas
```bash
python -m unittest discover -s scripts -p 'test_superagente_claim_inventory.py' -v
```
