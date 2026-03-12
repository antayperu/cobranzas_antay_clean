# 🔧 Instrucciones: Instalar Google Chrome en Servidor QA

## ⚠️ Problema Identificado
La funcionalidad de **Conectar Dispositivo WhatsApp** falla en el servidor QA con el error:
```
Error: Message: session not created: Chrome instance exited
```

**Causa:** Google Chrome no está instalado en el servidor QA.

---

## ✅ Solución: Instalar Chrome en el Servidor

### **Opción 1: Instalación Manual (Recomendado)**

#### Paso 1️⃣ - Descargar Chrome
1. Ve a [https://www.google.com/chrome/](https://www.google.com/chrome/)
2. Haz clic en "Descargar Chrome"
3. Selecciona **Windows** (64-bit o 32-bit según tu servidor)
4. Descarga el instalador `ChromeSetup.exe`

#### Paso 2️⃣ - Ejecutar el Instalador
```bash
# Ejecuta el archivo descargado
ChromeSetup.exe

# O desde línea de comandos (como Administrator):
ChromeSetup.exe --system-level
```

#### Paso 3️⃣ - Verificar la Instalación
Chrome se instalará en:
```
C:\Program Files\Google\Chrome\Application\chrome.exe
(o C:\Program Files (x86)\... si es versión 32-bit)
```

Verifica que el archivo existe:
```powershell
Test-Path "C:\Program Files\Google\Chrome\Application\chrome.exe"
# Debe retornar: True
```

#### Paso 4️⃣ - Reiniciar la Aplicación
```powershell
# En el servidor QA, reinicia el servicio:
net stop "Antay Cobranza"  # o el nombre del servicio
net start "Antay Cobranza"
```

O **reinicia completamente el servidor QA**.

---

### **Opción 2: Instalación por Línea de Comandos (PowerShell)**

```powershell
# Ejecutar como Administrator:

# Descargar Chrome installer
$chromeUrl = "https://dl.google.com/chrome/install/latest/chrome_installer.exe"
$outputPath = "C:\Temp\ChromeSetup.exe"
Invoke-WebRequest -Uri $chromeUrl -OutFile $outputPath

# Ejecutar instalador silenciosamente
& $outputPath --system-level --silent --install

# Esperar a que termine
Start-Sleep -Seconds 30

# Verificar instalación
$chromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
if (Test-Path $chromePath) {
    Write-Host "✅ Chrome instalado correctamente" -ForegroundColor Green
} else {
    Write-Host "❌ Error en la instalación" -ForegroundColor Red
}
```

---

## 🔍 Verificación Post-Instalación

### Test 1: Verificar Chrome está disponible
```powershell
# En PowerShell del servidor QA:
Test-Path "C:\Program Files\Google\Chrome\Application\chrome.exe"
```

Debe retornar `True`

### Test 2: Ver versión de Chrome
```powershell
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --version
# Debe mostrar: Google Chrome X.X.X.X
```

### Test 3: Probar conectar en la app
1. Abre la aplicación ReporteCobranzas en QA
2. Ve a pestaña **"Configuración"**
3. Sección **"📱 WhatsApp — Dispositivo de Envío"**
4. Haz clic en **"Conectar Dispositivo"**
5. Debe abrirse Chrome y mostrar el QR de WhatsApp Web

---

## ❌ Si Persisten los Errores

### Error: "ChromeDriver version mismatch"
**Solución:** Asegúrate que Chrome está actualizado a la última versión.

```powershell
# En Chrome, presiona: Ctrl+Shift+Delete → Verificar actualizaciones
# O vuelve a ejecutar el instalador
```

### Error: "Permission denied" al crear sesión
**Solución:** Asegúrate que el usuario que ejecuta la app tiene permisos de escritura en:
```
C:\Users\[USERNAME]\AppData\Local\Temp\dacta_wa_session
```

```powershell
# Crear carpeta con permisos correctos:
$path = "C:\Users\[USERNAME]\AppData\Local\Temp\dacta_wa_session"
New-Item -ItemType Directory -Force -Path $path
# Dar permisos al usuario/servicio que ejecuta la app
```

### Error: "Chrome crashed"
**Solución:** Chrome necesita recursos suficientes. En servidor:
1. Libera espacio en disco (al menos 500 MB libres)
2. Asegúrate que hay memoria RAM disponible (mínimo 1 GB libre)
3. Desactiva protección antivirus temporalmente si es necesario

---

## 📞 Soporte

Si después de instalar Chrome todavía tienes problemas:

1. **Verifica los logs de la aplicación** en servidor QA
2. **Confirma Chrome funciona manualmente:**
   ```powershell
   & "C:\Program Files\Google\Chrome\Application\chrome.exe" https://web.whatsapp.com
   ```
3. **Contacta con soporte técnico** proporcionando:
   - Versión de Chrome instalada
   - Mensajes de error específicos de la aplicación
   - Logs del servidor

---

## 📝 Referencias

- Chrome Download: https://www.google.com/chrome/
- ChromeDriver: https://chromedriver.chromium.org/
- Selenium WebDriver: https://www.selenium.dev/documentation/
