# Script para configurar README en todos los proyectos Antay
# Ejecutar desde: ReporteCobranzas/

Write-Host "🚀 Configurando proyectos Antay con metodología..." -ForegroundColor Green

# Rutas de los proyectos
$catalogpro = "C:\dev\catalogpro"
$antayReportes = "C:\Users\corte\OneDrive\CamiloOrtegaFR\02_AntayPeru\2.3_Divisiones\3.4_Consultoria_Antay\Recursos_Tecnicos\Python\antay-reportes"

# Contenido del README para CatalogPro
$readmeCatalogPro = @"
# CatalogPro Enhanced v2 - Antay Perú

Sistema de creación de catálogos digitales profesionales a partir de hojas de cálculo.

---

## 🏭 Metodología Antay Fábrica de Software

Este proyecto sigue los estándares de **Antay Fábrica de Software**.

### Para Antigravity AI

Al trabajar en este proyecto con Antigravity, inicia la conversación con:

``````
Conéctate a nuestra metodología Antay Fábrica de Software y desarrolla bajo esos estándares.

Token: tu_token_aqui
Page ID: 2377544a512b80048f40e7cd8568c09c
``````

Esto asegura que Antigravity:
- ✅ Lea la metodología actualizada desde Notion
- ✅ Aplique los estándares de desarrollo de Antay
- ✅ Siga los procesos de testing y QA
- ✅ Use las plantillas de documentación correctas

---

## 📋 Descripción del Proyecto

Permite a pequeños comerciantes crear catálogos digitales profesionales a partir de Excel o Google Sheets, con vista web, filtros, exportación a HTML/PDF y envío por WhatsApp o correo.

## 🚀 Stack Tecnológico

- Python
- Streamlit
- Notion (documentación)
- GitHub (control de versiones)

---

**Desarrollado por Antay Perú** 🇵🇪
"@

# Contenido del README para Antay-Reportes
$readmeAntayReportes = @"
# Antay Reportes - Antay Perú

Sistema de generación y gestión de reportes empresariales.

---

## 🏭 Metodología Antay Fábrica de Software

Este proyecto sigue los estándares de **Antay Fábrica de Software**.

### Para Antigravity AI

Al trabajar en este proyecto con Antigravity, inicia la conversación con:

``````
Conéctate a nuestra metodología Antay Fábrica de Software y desarrolla bajo esos estándares.

Token: tu_token_aqui
Page ID: 2377544a512b80048f40e7cd8568c09c
``````

Esto asegura que Antigravity:
- ✅ Lea la metodología actualizada desde Notion
- ✅ Aplique los estándares de desarrollo de Antay
- ✅ Siga los procesos de testing y QA
- ✅ Use las plantillas de documentación correctas

---

## 📋 Descripción del Proyecto

[Agregar descripción del proyecto aquí]

## 🚀 Instalación

[Agregar instrucciones de instalación]

---

**Desarrollado por Antay Perú** 🇵🇪
"@

# Crear README en CatalogPro
Write-Host "`n📝 Creando README en CatalogPro..." -ForegroundColor Cyan
if (Test-Path $catalogpro) {
    $readmePath = Join-Path $catalogpro "README.md"
    $readmeCatalogPro | Out-File -FilePath $readmePath -Encoding UTF8
    Write-Host "✅ README creado en: $readmePath" -ForegroundColor Green
} else {
    Write-Host "⚠️  No se encontró el directorio: $catalogpro" -ForegroundColor Yellow
}

# Crear README en Antay-Reportes
Write-Host "`n📝 Creando README en Antay-Reportes..." -ForegroundColor Cyan
if (Test-Path $antayReportes) {
    $readmePath = Join-Path $antayReportes "README.md"
    $readmeAntayReportes | Out-File -FilePath $readmePath -Encoding UTF8
    Write-Host "✅ README creado en: $readmePath" -ForegroundColor Green
} else {
    Write-Host "⚠️  No se encontró el directorio: $antayReportes" -ForegroundColor Yellow
}

Write-Host "`n🎉 ¡Configuración completada!" -ForegroundColor Green
Write-Host "`nAhora en cualquier proyecto puedes decir:" -ForegroundColor White
Write-Host "'Conéctate a nuestra metodología Antay Fábrica de Software'" -ForegroundColor Yellow
