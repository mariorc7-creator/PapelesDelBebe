# Flujo de contraste de ayudas

La extracción de cifras y plazos solo genera **candidatos**. Una coincidencia textual no es evidencia de vigencia.

Para cada candidato:
1. Identificar la prestación concreta y la administración competente.
2. Consultar la norma y la página de tramitación oficiales, incluyendo su fecha de vigencia.
3. Contrastar requisitos, cuantía, plazo, documentación, procedimiento y ámbito territorial.
4. Distinguir fecha de publicación, fecha de revisión y `dateModified`.
5. Guardar fragmento de evidencia, URL, fecha de consulta y resultado: `coincide`, `difiere` o `no_verificable`.
6. Si difiere, generar propuesta de cambio con diff; no sobrescribir contenido sin pruebas y QA.
7. Si coincide, registrar revisión real sin modificar el contenido.
8. Agrupar las propuestas aprobadas en una versión grande antes de PROD.

## Limitaciones conocidas
- Las cantidades pueden referirse a ejemplos o a ayudas antiguas.
- Una cifra extraída de HTML no indica automáticamente que sea una cuantía vigente.
- La disponibilidad HTTP no verifica la legalidad ni el contenido.
- El sistema actual no compara automáticamente con normas oficiales; esa capacidad sigue pendiente.
