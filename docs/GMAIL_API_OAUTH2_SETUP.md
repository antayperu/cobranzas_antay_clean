# RC-FEAT-096 — Gmail API OAuth2: Envío Programado Real

## Objetivo

Reemplazar el sistema de "Programar envío para después" (que requería que la app estuviera abierta) por un sistema completamente automático basado en Gmail API OAuth2 + worker en el servidor QA.

## Arquitectura final

```
Usuario en app  →  Guarda programación en BD (tabla envios_programados)
                          ↓
Servidor QA    →  Worker Python corre cada 5 min (Windows Task Scheduler)
                          ↓
               →  Detecta envíos cuya hora ya llegó
                          ↓
               →  Envía via Gmail API (sin que la app esté abierta)
                          ↓
               →  Marca como ENVIADO en BD
```

## Configuración en Google Cloud (COMPLETADO ✅)

| Elemento | Valor |
|---|---|
| Proyecto | `antay-cobranzas-gmail` |
| Gmail API | Habilitada |
| Cliente OAuth | "Antay Cobranzas - Envío Gmail" (App de escritorio) |
| Cuenta Gmail | `cobranza.integrens@gmail.com` |
| Usuario prueba | `cobranza.integrens@gmail.com` |

### Credenciales (en `gmail_oauth_credentials.json` — NO en git)

```json
{
  "installed": {
    "client_id": "<CLIENT_ID>.apps.googleusercontent.com",
    "client_secret": "<CLIENT_SECRET>",
    "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"],
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token"
  }
}
```

> Los valores reales están en `gmail_oauth_credentials.json` (fuera de git, entregar manualmente al QA).

> ⚠️ Este archivo está en `.gitignore`. Copiar manualmente al servidor QA.

## Pasos pendientes

### Paso 1 — Obtener refresh_token (una sola vez)

Instalar dependencias:
```bash
pip install google-auth google-auth-oauthlib google-api-python-client
```

Crear y ejecutar `scripts/gmail_oauth_flow.py`:
- Abre el navegador en esta laptop
- El PO inicia sesión con `cobranza.integrens@gmail.com`
- Aprueba los permisos de Gmail
- Se genera `gmail_token.json` con el `refresh_token`
- Copiar `gmail_token.json` al servidor QA: `\\QA\antay-cobranza\`

### Paso 2 — Módulo de envío (`utils/gmail_api_sender.py`)

Usa `google-auth` + `googleapiclient.discovery` para enviar emails.  
Reemplaza `smtplib` para envíos programados (no para envíos inmediatos desde la app — esos pueden seguir usando SMTP).

### Paso 3 — Worker del servidor QA (`scripts/scheduled_email_worker.py`)

Script independiente que:
1. Se conecta a PostgreSQL local
2. Lee `SELECT * FROM envios_programados WHERE estado='PENDIENTE' AND scheduled_at <= NOW()`
3. Para cada registro, envía los correos via Gmail API
4. Actualiza `estado = 'ENVIADO'` en BD

Configurar en Windows Task Scheduler del QA:
- Trigger: cada 5 minutos
- Acción: `python C:\antay-cobranza\scripts\scheduled_email_worker.py`

### Paso 4 — Actualizar UI (tab Email)

El expander "Programar envío para después" no necesita cambios en UI, solo conectar con el worker.

### Paso 5 — Quality Gates + deploy

- Gate 0: `python -m py_compile`
- Gate 1: `pytest tests/ -v`
- Gate 3: Smoke manual staging
- Deploy a QA via `\\QA\antay-cobranza`

## Por qué esta arquitectura

| Antes | Ahora |
|---|---|
| App debe estar abierta | Servidor envía solo |
| Depende de que el PO esté en la app | Completamente automático |
| SMTP con contraseña de aplicación | OAuth2 con refresh_token (más seguro y no expira) |
| Worker falso (solo alerta) | Worker real que envía |
