# SuperAgente V0.3 — justificantes de revisión editorial

## Objetivo

Documentar revisiones de ayudas y trámites sin confundir la existencia de una URL con una verificación jurídica real. Este módulo está separado de los metadatos públicos; por diseño **no escribe HTML, `dateModified`, `lastmod` ni `last_reviewed`**.

## Registro de una revisión

Si existe `superagente/review-receipts.json`, el workflow `superagente-audit.yml` lo valida. Su estructura es:

```json
{
  "schema_version": 1,
  "receipts": [
    {
      "page": "https://www.papelesdelbebe.es/URL-DE-LA-GUIA/",
      "page_sha256": "SHA256 hexadecimal del HTML exacto",
      "reviewed_on": "2026-11-06",
      "reviewer": "Identidad del revisor",
      "result": "unchanged",
      "checks": {
        "eligibility": {"finding": "confirmed", "reason": "Explicación concreta de la comprobación.", "source_url": "https://fuente-oficial/"}
      }
    }
  ]
}
```

El ejemplo debe ampliarse con **siete claves** de `checks`: `eligibility`, `amount`, `deadline`, `documents`, `procedure`, `compatibility` y `official_link`. Cada una exige `finding` (confirmed/difference/not_applicable/unverifiable), una explicación específica y un enlace HTTPS si se considera corroborada.

Los resultados de la guía son `unchanged`, `change_proposed` o `unverifiable`. No se permite declarar `unchanged` si un control reporta discrepancia o no se puede verificar. La huella del HTML evita dar por revisada una versión distinta de la examinada.

## Barreras y límites

- Un recibo completo **solo queda listo para revisión editorial**; su contenido es aportado por un revisor y aún requiere comprobar de forma independiente las fuentes y la aplicación legal.
- Si no existen recibos, el CI ejecuta las pruebas pero no marca ninguna página como revisada.
- Un resultado `unverifiable` requiere escalado; no debe actualizarse ninguna fecha pública.
- La actualización visible de «Última revisión» únicamente se considerará después de que exista evidencia validada, aprobación editorial y control de regresiones.
- La revisión **sin cambios** no debe cambiar contenido, fechas `dateModified` ni `lastmod`.
- No almacenar datos personales en los justificantes.
- Sigue deshabilitado publicar automáticamente y no hay rollback de un despliegue real validado.
