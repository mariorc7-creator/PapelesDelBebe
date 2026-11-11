# Inteligencia de producto — competencia España
Revisión: 20/10/2026 · Responsable: Competencia
Estado: propuesta para el próximo despliegue agrupado. NO activar Premium, Stripe, Gestoría, leads ni cobros.

## Referencia operativa
Leer `AGENTES-COORDINACION.md` y trabajar desde `main` reciente. Mantener cabecera global `global-ui.js`, `analytics.js`, no duplicar Mi panel. Validar en preview y producción mediante Vercel.

## Oportunidades verificadas y producto propio
| Competidor / fuente | Característica observada | Propuesta original | Responsable | Prioridad |
|---|---|---|---|---|
| Automa-Time https://automa-time.com/calculadora/ | Planifica permiso, lactancia, vacaciones, festivos y retorno | Integrar escenarios para ambos progenitores, desglose editable por semanas, exportación accesible con advertencias de convenio y festivos locales | Mantenimiento + Contenido | P0 |
| Prestaciones por Nacimiento https://prestacionespornacimiento.es/guias/conciliacion/ | Calculadora de reducción de jornada y modelos | Módulo «Conciliación» de horas, reducción salarial bruta orientativa y escrito rellenable; casos de adaptación sin reducción salarial separados | Contenido + Mantenimiento | P0 |
| Prestaciones por Nacimiento https://prestacionespornacimiento.es/guias/excedencia/ | Cálculo de fechas de excedencia y reserva | Simulador de excedencia con límites sujetos a convenio, modelos descargables y fuentes legales | Contenido + Mantenimiento | P1 |
| Tus Ayudas https://tus-ayudas.es/comunidad/ayudas-natalidad/ | Comparativa 17 CCAA + 2 ciudades y simulador | Radar de ayudas con municipio, convocatoria abierta/cerrada, fuente, fecha de verificación, documentos y vencimiento calculado solo si plazo confirmado | Contenido + SEO | P0 |
| BabyBeLegal https://babybelegal.com/ | Portal privado de documentos, estados, mensajes | Evolucionar Mi panel gratuito con estado único de trámites, siguiente acción y documentos sin subir documentos personales a servidores | Mantenimiento | P1 |
| Prestaciones por Nacimiento https://prestacionespornacimiento.es/observatorio/ | Informe y datos citables para medios | Observatorio propio basado primero en datos oficiales, metodología, descarga CSV, atribución y revisión | SEO + Contenido | P1 |
| Prestaciones por Nacimiento https://prestacionespornacimiento.es/guias/tramites-nacimiento/ | Cronología 0-90 días | Conectar calendario existente con checklist y progreso; distinguir tareas sugeridas de plazos legales verificados | Mantenimiento | P1 |

## Criterios para ser mejores
1. Una experiencia: preguntas compartidas y progreso coherente entre Mi panel, simulador y calendario.
2. Precisión superior: motor de reglas versionado, referencias legales, casos especiales, límites y pruebas automatizadas. Nunca dar como definitivas fechas de disfrute flexibles o reglas dependientes de convenio.
3. UX «menos por más»: respuesta accionable en menos de 2 minutos, buen móvil, accesibilidad WCAG, errores visibles y datos mínimos.
4. SEO/AEO/GEO: indexar solo páginas útiles con respuesta directa, datos estructurados fieles y enlaces oficiales; priorizar Search Console (consultas posición 10-20, ≥20 impresiones/28 días) antes de crear nuevas URLs.
5. No reproducir textos, gráficos, marcas ni interfaces ajenas. Inspiración funcional con diseño y lógica propios.
6. No publicar importes/plazos de ayudas sin comprobación oficial, y no generar falsas alertas de vencimiento.

## Plan de paquete grande
- Fase A: inventario y tests de calculadora actual (`/herramientas/calculadora-permiso-nacimiento/`), calendario (`/herramientas/calendario-primeros-90-dias/`) y simulador (`/herramientas/buscador-ayudas/`). Comprobar endpoints `/api/calcular-permiso` y `/api/calendario-90-dias`, casos vacíos/futuros/fraccionados, móvil y 404.
- Fase B: desarrollar un solo módulo de conciliación completo, integrado con Mi panel; no lanzar herramientas incompletas.
- Fase C: ampliar Radar de ayudas con un lote pequeño de convocatorias oficialmente verificadas y pruebas de vencimiento.
- Fase D: QA de navegación global, enlaces, sitemap, canonicals, indexabilidad, analítica respetuosa con privacidad y despliegue Vercel READY.
- Una sola PR de release y un único merge a `main` tras revisión coordinada del Organizador/Mantenimiento.

## Notas de inteligencia
No se ha verificado que estas funcionalidades sean nuevas hoy; son capacidades públicas observadas a 20/10/2026. No se han validado los flujos privados de los competidores ni métricas de tráfico.