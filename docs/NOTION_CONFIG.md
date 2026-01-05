# Configuración de Notion para ReporteCobranzas

## Token de Acceso

**NOTION_TOKEN**: `(Configurado en GitHub Secrets)`

## Page IDs

- **Metodología Antay Fábrica de Software**: `2377544a512b804db020d8e8b62fd00d`
- **FRD v0.2 — ReporteCobranzas**: Incluido en la estructura de la metodología

## Uso

Para conectarse a Notion y descargar la última versión de la metodología:

```powershell
$env:NOTION_TOKEN="tu_token_aqui"
python utils/antay_methodology.py
```

Esto actualizará `docs/ANTAY_METHODOLOGY.md` con la última versión viva desde Notion.

## SSOT (Single Source of Truth)

✅ **Notion es la ÚNICA fuente oficial**
❌ README, /docs locales pueden estar desfasados

Siempre consultar Notion antes de hacer cambios de código.
