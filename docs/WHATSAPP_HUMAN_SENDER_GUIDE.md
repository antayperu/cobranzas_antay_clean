# Guía: Envío Masivo WhatsApp con Comportamiento Humano Simulado

**Versión:** 2.0  
**Fecha:** 2026-09-06  
**Origen:** Aprendizaje operativo — Proyecto ReporteCobranzas (Antay Fábrica de Software)  
**Propósito:** Trasladar conocimiento crítico a nuevos proyectos que implementen envío masivo por WhatsApp Web. Con solo leer este documento, un desarrollador puede reconstruir el sistema completo correctamente desde cero.

---

## Por qué existe este documento

Durante la operación del sistema de cobranzas de Antay, la cuenta de WhatsApp del operador fue **notificada por Meta por envío masivo automatizado**. El motivo fue que el módulo de envío producía patrones de comportamiento robóticos que la inteligencia artificial de WhatsApp detecta activamente.

Este documento reúne todo lo aprendido — incluyendo la arquitectura correcta de dos pasos — para que cualquier proyecto nuevo lo haga bien desde el primer día, sin riesgo de bloqueo.

---

## Cómo funciona el sistema: arquitectura de dos pasos

El sistema **no usa la API oficial de WhatsApp**. Controla un navegador web (Chromium) como si fuera una persona sentada frente al computador, abriendo WhatsApp Web y enviando mensajes uno por uno mediante la librería **Playwright**.

La arquitectura está dividida en **dos pasos separados e independientes**:

```
┌─────────────────────────────────────────────────────────────┐
│  PASO 1 — CONEXIÓN (se hace una sola vez, con anticipación) │
│                                                             │
│  Usuario hace clic en "Conectar WhatsApp"                   │
│       → Chrome se abre                                      │
│       → WhatsApp Web muestra el código QR                   │
│       → Usuario escanea QR con su celular                   │
│       → Sesión queda GUARDADA EN DISCO                      │
│       → Chrome se cierra                                    │
│       → Estado guardado: { status: "active", phone, name }  │
└─────────────────────────────────────────────────────────────┘

         (pueden pasar horas, días o semanas)

┌─────────────────────────────────────────────────────────────┐
│  PASO 2 — ENVÍO (cuando el gestor lo decide)                │
│                                                             │
│  Usuario hace clic en "Enviar mensajes"                     │
│       → Chrome se abre con la sesión guardada               │
│       → Detecta sesión activa → entra SIN escanear QR       │
│       → Por cada cliente (uno a uno):                       │
│           1. Navega al chat del cliente                     │
│           2. Espera que cargue                              │
│           3. Pega el mensaje personalizado                  │
│           4. Presiona Enter                                 │
│           5. Espera tiempo aleatorio → siguiente cliente    │
│       → Cierra Chrome                                       │
│       → Registra resultados en base de datos                │
└─────────────────────────────────────────────────────────────┘
```

**Punto clave:** Separar la conexión del envío es correcto y necesario. Intentar hacer ambas cosas en el mismo flujo crea fricciones para el usuario y aumenta el riesgo de timeout en el QR.

---

## Duración de la sesión

La sesión de WhatsApp Web se mantiene activa **mientras el teléfono del operador tenga internet y la app de WhatsApp esté corriendo**. En la práctica, una sesión puede durar semanas sin necesidad de volver a escanear.

La sesión expira si:
- El operador cierra sesión manualmente desde el celular (Ajustes → Dispositivos vinculados → Cerrar sesión)
- El celular lleva muchos días sin conexión a internet
- WhatsApp decide cerrarla por seguridad (infrecuente)

La sesión se guarda en un directorio fijo en disco (`dacta_wa_session` dentro del directorio temporal del sistema). Contiene un archivo `_session_info.json` con:
```json
{
  "status": "active",
  "verified_at": "2026-09-06 10:30:00",
  "profile_name": "Cobranzas Antay",
  "phone": "51998080797"
}
```

---

## Cómo detecta WhatsApp el comportamiento automatizado

WhatsApp Web monitorea en tiempo real:

1. **Propiedades del navegador** — flags que delatan que es un navegador controlado por código (ej: `navigator.webdriver = true`)
2. **Patrones de tiempo** — si los mensajes se envían con intervalos exactamente iguales, es una firma de robot
3. **Velocidad de interacción** — un humano no hace clic, pega texto y presiona Enter en menos de 100ms; un robot sí
4. **Volumen y frecuencia** — muchos mensajes en poco tiempo sin variación activa el sistema de protección
5. **Consistencia de mensajes** — mensajes 100% idénticos entre todos los destinatarios es otra señal

El resultado de ser detectado va desde advertencia hasta **bloqueo permanente de la cuenta**.

---

## Las 10 protecciones obligatorias

### Protección 1 — Ocultar que es un navegador controlado por código

**Qué hace:** Elimina las propiedades del navegador que delatan automatización.  
**Dónde aplica:** En el momento de lanzar Chromium con Playwright.

```python
context = playwright.chromium.launch_persistent_context(
    user_data_dir=SESSION_DIR,
    headless=False,  # CRÍTICO: nunca True — WhatsApp lo detecta
    args=[
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--disable-software-rasterizer",
        "--start-maximized",
    ],
    ignore_default_args=["--enable-automation"],  # CRÍTICO: la más importante
)
```

**Por qué `ignore_default_args=["--enable-automation"]` es la más importante:**  
Playwright agrega esta flag automáticamente. Sin eliminarla, `navigator.webdriver` del navegador queda en `true`, y WhatsApp la lee para saber que es un robot.

---

### Protección 2 — Delays con variación aleatoria

**Qué hace:** El tiempo de espera entre mensajes es aleatorio, nunca fijo.  
**Por qué es crítica:** Si envía 30 mensajes y entre cada uno pasan exactamente 4 segundos, la IA de WhatsApp detecta el patrón en menos de 10 mensajes.

```python
import random

SPEED_RANGES = {
    "Rápida (Riesgo de bloqueo)": (3, 7),
    "Normal (Recomendado)":       (8, 15),
    "Lenta (Más seguro)":         (15, 30),
}

def human_delay(speed: str = "Normal (Recomendado)") -> float:
    min_s, max_s = SPEED_RANGES.get(speed, (8, 15))
    delay = random.uniform(min_s, max_s)
    time.sleep(delay)
    return delay
```

**Error común a evitar:**
```python
# MAL — patrón fijo, detectable
time.sleep(4)

# BIEN — patrón aleatorio, indistinguible de un humano
human_delay("Normal (Recomendado)")
```

---

### Protección 3 — Micro-pausas entre cada acción

**Qué hace:** Inserta pequeñas pausas aleatorias entre cada interacción con el navegador.

```python
def micro_pause(min_ms: int = 300, max_ms: int = 1200):
    time.sleep(random.uniform(min_ms / 1000, max_ms / 1000))

# Uso en el flujo de envío de cada mensaje:
page.goto(url)
micro_pause(800, 2000)           # "el humano llegó al chat y está leyendo"

input_box.click()
micro_pause(200, 600)            # "el humano posicionó el cursor"

page.keyboard.press("Control+V")
micro_pause(500, 1200)           # "el humano revisó el mensaje antes de enviar"

page.keyboard.press("Enter")
micro_pause(600, 1500)           # "el humano vio el check y pasó al siguiente"
```

---

### Protección 4 — Pausa larga aleatoria cada N mensajes

**Qué hace:** Cada cierto número de mensajes, el sistema espera entre 45 y 120 segundos.  
**Por qué importa:** Ningún operador humano envía 50 mensajes seguidos sin detenerse.

```python
def maybe_long_pause(i: int, every_n: int = 10, log_fn=None):
    if i > 1 and i % every_n == 0:
        pause_s = random.uniform(45, 120)
        msg = f"☕ Pausa natural (cada {every_n} mensajes) — {pause_s:.0f}s..."
        if log_fn:
            log_fn(msg)
        time.sleep(pause_s)

# Uso en el loop de envío:
for i, contact in enumerate(contacts, 1):
    maybe_long_pause(i, every_n=10, log_fn=log)
    # ... resto del envío
```

---

### Protección 5 — Sesión persistente en disco

**Qué hace:** Guarda la sesión de WhatsApp Web en un directorio fijo en disco y la reutiliza.  
**Por qué importa:** Escanear el QR repetidamente en el mismo día es señal de comportamiento anómalo. Esta protección es la base de la arquitectura de dos pasos.

```python
import tempfile, os

WA_SESSION_DIR = os.path.join(tempfile.gettempdir(), "mi_proyecto_wa_session")
WA_SESSION_INFO = os.path.join(WA_SESSION_DIR, "_session_info.json")

# Siempre usar el mismo directorio al lanzar el navegador:
context = playwright.chromium.launch_persistent_context(
    user_data_dir=WA_SESSION_DIR,
    # ...
)
```

---

### Protección 6 — Limpieza de archivos de bloqueo de sesión

**Qué hace:** Elimina archivos que Chromium deja al cerrarse inesperadamente.  
**Por qué importa:** Sin esto, aparece el popup "Chrome no se cerró correctamente", que interrumpe el flujo automático.

```python
def clean_session_locks(session_dir: str):
    profile_dir = os.path.join(session_dir, "Default")
    files_to_clean = [
        os.path.join(session_dir, "SingletonLock"),
        os.path.join(session_dir, "SingletonCookie"),
        os.path.join(session_dir, "SingletonSocket"),
        os.path.join(profile_dir, "Last Session"),
        os.path.join(profile_dir, "Last Tabs"),
        os.path.join(profile_dir, "Current Session"),
        os.path.join(profile_dir, "Current Tabs"),
    ]
    for f in files_to_clean:
        try:
            if os.path.exists(f):
                os.remove(f)
        except OSError:
            pass

# Llamar SIEMPRE antes de lanzar el navegador:
clean_session_locks(WA_SESSION_DIR)
```

---

### Protección 7 — Detección rápida de número inválido (Fast Fail)

**Qué hace:** Detecta en menos de 1 segundo si un número no existe en WhatsApp y pasa al siguiente.  
**Por qué importa:** Sin esto, el proceso espera el timeout completo (30s) por cada número inválido.

```python
INVALID_SELECTORS = [
    '//div[contains(text(), "inválido")]',
    '//div[contains(text(), "invalid")]',
    '//div[contains(text(), "url is invalid")]',
    '//div[contains(text(), "phone number")]',
]

def check_invalid_number(page) -> bool:
    for selector in INVALID_SELECTORS:
        try:
            if page.query_selector(selector):
                return True
        except Exception:
            pass
    return False

def wait_for_chat(page, timeout_s: int = 30) -> bool:
    chat_selector = '//div[@contenteditable="true"][@data-tab="10"]'
    start = time.time()
    while time.time() - start < timeout_s:
        if check_invalid_number(page):
            return False  # Fast fail: no esperar el timeout completo
        try:
            if page.query_selector(chat_selector):
                return True
        except Exception:
            pass
        time.sleep(0.8)
    return False
```

---

### Protección 8 — Timeout dinámico según posición en el lote

**Qué hace:** El primer mensaje del lote tiene más tiempo de espera que los siguientes.  
**Por qué importa:** El primer mensaje siempre tarda más porque WhatsApp Web aún está cargando datos de la sesión (carga fría).

```python
for i, contact in enumerate(contacts, 1):
    timeout_chat = 60 if i == 1 else 30  # Primer mensaje: 60s, resto: 30s
    chat_ok = wait_for_chat(page, timeout_s=timeout_chat)
```

---

### Protección 9 — Orden aleatorio de contactos

**Qué hace:** Mezcla la lista de contactos antes de enviar.  
**Por qué importa:** Si siempre se envía en el mismo orden, el patrón de destinatarios puede ser detectable estadísticamente.

```python
import random

def prepare_contacts(contacts: list, shuffle: bool = True) -> list:
    prepared = contacts.copy()
    if shuffle:
        random.shuffle(prepared)
    return prepared
```

---

### Protección 10 — Limpieza del portapapeles entre mensajes

**Qué hace:** Borra el portapapeles antes de copiar el mensaje del siguiente cliente.  
**Por qué importa:** Si un paso falla y el portapapeles queda con el mensaje del cliente anterior, el siguiente cliente recibiría el mensaje equivocado.

```python
import subprocess

def clear_clipboard():
    try:
        subprocess.run(
            ["powershell", "-command", "Set-Clipboard -Value $null"],
            check=False, capture_output=True
        )
        time.sleep(0.3)
    except Exception:
        pass

# Usar al inicio de cada iteración del loop:
for contact in contacts:
    clear_clipboard()
    # ... envío del mensaje
```

---

## Tabla resumen de protecciones

| # | Protección | Riesgo si se omite |
|---|---|---|
| 1 | `--disable-blink-features=AutomationControlled` + `ignore_default_args` | WhatsApp lee `navigator.webdriver=true` y bloquea |
| 2 | Delays **aleatorios** entre mensajes | Patrón fijo detectado en menos de 10 mensajes |
| 3 | Micro-pausas entre cada acción | Interacción a velocidad de robot — detectable |
| 4 | Pausa larga cada N mensajes | Patrón estadístico uniforme — detectable a largo plazo |
| 5 | Sesión persistente en disco | QR repetido = comportamiento anómalo |
| 6 | Limpieza de SingletonLock | Popup de error interrumpe el flujo automático |
| 7 | Fast Fail en número inválido | Timeout innecesario de 30s por número = proceso lento |
| 8 | Timeout dinámico (primer mensaje) | Fallo falso en el primer envío por carga fría |
| 9 | Orden aleatorio de contactos | Patrón geográfico o por segmento — detectable |
| 10 | Limpieza de portapapeles | Mensaje equivocado enviado al cliente incorrecto |

---

## Código completo del módulo

El módulo se divide en tres secciones funcionales que corresponden a los dos pasos de la arquitectura más las utilidades comunes.

```python
"""
whatsapp_human_sender.py

Módulo de envío masivo WhatsApp con simulación de comportamiento humano.
Arquitectura de DOS PASOS:
  1. connect_wa_session()            → conecta el dispositivo (QR) y guarda sesión
  2. send_whatsapp_messages()        → envía mensajes usando la sesión guardada

Implementa las 10 protecciones anti-detección documentadas en
WHATSAPP_HUMAN_SENDER_GUIDE.md
"""

import time
import random
import os
import json
import shutil
import tempfile
import subprocess
import logging
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    from playwright.async_api import async_playwright, TimeoutError as PWTimeoutAsync
    _PLAYWRIGHT_OK = True
except ImportError:
    _PLAYWRIGHT_OK = False

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuración de sesión (Protección 5)
# ---------------------------------------------------------------------------

WA_SESSION_DIR  = os.path.join(tempfile.gettempdir(), "mi_proyecto_wa_session")
WA_SESSION_INFO = os.path.join(WA_SESSION_DIR, "_session_info.json")

# Protección 2: Rangos de delay — NUNCA valores fijos
SPEED_RANGES = {
    "Rápida (Riesgo de bloqueo)": (3, 7),
    "Normal (Recomendado)":       (8, 15),
    "Lenta (Más seguro)":         (15, 30),
}

# Selectores WhatsApp Web
SELECTORS = {
    "pane_side":      '//div[@id="pane-side"]',
    "chat_loaded":    '//div[@contenteditable="true"][@data-tab="10"]',
    "input_box":      '//div[@contenteditable="true"][@data-tab="10"]',
    "send_button": [
        '//span[@data-icon="send"]',
        '//div[@role="button"][@aria-label="Send"]',
        '//div[@role="button"][@aria-label="Enviar"]',
    ],
    "invalid_number": [
        '//div[contains(text(), "inválido")]',
        '//div[contains(text(), "invalid")]',
        '//div[contains(text(), "url is invalid")]',
        '//div[contains(text(), "phone number")]',
    ],
    "qr_code": [
        '//canvas[@aria-label="Scan me!"]',
        '//div[@data-testid="qrcode"]',
    ],
}

# ---------------------------------------------------------------------------
# Protección 2: Delay aleatorio entre mensajes
# ---------------------------------------------------------------------------

def human_delay(speed: str = "Normal (Recomendado)") -> float:
    min_s, max_s = SPEED_RANGES.get(speed, (8, 15))
    delay = random.uniform(min_s, max_s)
    time.sleep(delay)
    return delay

# ---------------------------------------------------------------------------
# Protección 3: Micro-pausas entre acciones
# ---------------------------------------------------------------------------

def micro_pause(min_ms: int = 300, max_ms: int = 1200):
    time.sleep(random.uniform(min_ms / 1000, max_ms / 1000))

# ---------------------------------------------------------------------------
# Protección 4: Pausa larga periódica
# ---------------------------------------------------------------------------

def maybe_long_pause(i: int, every_n: int = 10, log_fn=None):
    if i > 1 and i % every_n == 0:
        pause_s = random.uniform(45, 120)
        msg = f"☕ Pausa natural (cada {every_n} mensajes) — {pause_s:.0f}s..."
        if log_fn:
            log_fn(msg)
        time.sleep(pause_s)

# ---------------------------------------------------------------------------
# Protección 6: Limpieza de archivos de bloqueo
# ---------------------------------------------------------------------------

def clean_session_locks(session_dir: str):
    profile_dir = os.path.join(session_dir, "Default")
    for fname in [
        os.path.join(session_dir, "SingletonLock"),
        os.path.join(session_dir, "SingletonCookie"),
        os.path.join(session_dir, "SingletonSocket"),
        os.path.join(profile_dir, "Last Session"),
        os.path.join(profile_dir, "Last Tabs"),
        os.path.join(profile_dir, "Current Session"),
        os.path.join(profile_dir, "Current Tabs"),
    ]:
        try:
            if os.path.exists(fname):
                os.remove(fname)
        except OSError:
            pass

# ---------------------------------------------------------------------------
# Protección 7: Detección rápida de número inválido
# ---------------------------------------------------------------------------

def check_invalid_number(page) -> bool:
    for selector in SELECTORS["invalid_number"]:
        try:
            if page.query_selector(selector):
                return True
        except Exception:
            pass
    return False


def wait_for_chat(page, timeout_s: int = 30) -> bool:
    start = time.time()
    while time.time() - start < timeout_s:
        if check_invalid_number(page):
            return False
        try:
            if page.query_selector(SELECTORS["chat_loaded"]):
                return True
        except Exception:
            pass
        time.sleep(0.8)
    return False

# ---------------------------------------------------------------------------
# Protección 10: Limpieza de portapapeles
# ---------------------------------------------------------------------------

def clear_clipboard():
    try:
        subprocess.run(
            ["powershell", "-command", "Set-Clipboard -Value $null"],
            check=False, capture_output=True
        )
        time.sleep(0.3)
    except Exception:
        pass

# ---------------------------------------------------------------------------
# Gestión de sesión (Protección 5)
# ---------------------------------------------------------------------------

def get_wa_session_info() -> dict:
    """
    Retorna el estado de la sesión guardada en disco.
    Campos: status ('active' | 'none'), verified_at, profile_name, phone
    Usar en la UI para mostrar si el dispositivo está conectado.
    """
    if not os.path.exists(WA_SESSION_INFO):
        return {"status": "none"}
    try:
        with open(WA_SESSION_INFO, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"status": "none"}


def save_wa_session_info(profile_name: str = "", phone: str = "") -> None:
    os.makedirs(WA_SESSION_DIR, exist_ok=True)
    data = {
        "status": "active",
        "verified_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "profile_name": profile_name,
        "phone": phone,
    }
    with open(WA_SESSION_INFO, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def clear_wa_session() -> bool:
    """Elimina la sesión guardada. El próximo envío pedirá QR nuevamente."""
    try:
        if os.path.exists(WA_SESSION_DIR):
            shutil.rmtree(WA_SESSION_DIR, ignore_errors=True)
        return True
    except Exception:
        return False

# ---------------------------------------------------------------------------
# Lanzamiento del navegador (Protección 1)
# ---------------------------------------------------------------------------

def launch_browser(playwright):
    """
    Lanza Chromium con todas las flags anti-detección activas.
    Aplica Protecciones 1, 5 y 6.
    """
    clean_session_locks(WA_SESSION_DIR)     # Protección 6
    os.makedirs(WA_SESSION_DIR, exist_ok=True)
    return playwright.chromium.launch_persistent_context(
        user_data_dir=WA_SESSION_DIR,       # Protección 5: sesión persistente
        headless=False,                     # NUNCA True
        args=[
            "--profile-directory=Default",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-software-rasterizer",
            "--disable-blink-features=AutomationControlled",   # Protección 1
            "--start-maximized",
        ],
        ignore_default_args=["--enable-automation"],           # Protección 1 (crítica)
    )

# ---------------------------------------------------------------------------
# Helpers de datos
# ---------------------------------------------------------------------------

def normalize_phone(phone: str, country_code: str = "51") -> str:
    """
    Normaliza número de teléfono para WhatsApp Web.
    Por defecto agrega código de Perú (+51) si el número tiene 9 dígitos.
    Cambiar country_code según el país del proyecto.
    """
    if not phone:
        return ""
    phone = str(phone).strip()
    if phone.startswith("+"):
        phone = phone[1:]
    if len(phone) == 9 and phone.isdigit():
        phone = country_code + phone
    return phone


def replace_variables(message: str, client_data: dict) -> str:
    """Reemplaza {variables} en el template con datos reales del cliente."""
    for key, value in client_data.items():
        placeholder = f"{{{key}}}"
        if placeholder in message:
            message = message.replace(placeholder, str(value))
    return message

# ---------------------------------------------------------------------------
# PASO 1 — Conexión del dispositivo
# ---------------------------------------------------------------------------

def connect_wa_session(timeout_seconds: int = 120) -> tuple:
    """
    PASO 1 DE LA ARQUITECTURA: Conecta WhatsApp Web y guarda la sesión en disco.

    Este paso se hace UNA SOLA VEZ (o cuando la sesión haya expirado).
    El usuario verá una ventana de Chrome con el código QR de WhatsApp Web.
    Debe escanearlo con su celular. Una vez escaneado, la sesión se guarda
    y Chrome se cierra. Los envíos posteriores no pedirán QR.

    Returns:
        (ok: bool, phone: str, profile_name: str, error_msg: str)

    Uso en la UI (Streamlit):
        ok, phone, name, err = connect_wa_session(timeout_seconds=120)
        if ok:
            st.success(f"Conectado: {name} ({phone})")
        else:
            st.error(err)
    """
    if not _PLAYWRIGHT_OK:
        return False, "", "", (
            "Playwright no está instalado.\n"
            "Ejecutar: pip install playwright && playwright install chromium"
        )

    try:
        with sync_playwright() as pw:
            context = launch_browser(pw)  # Protecciones 1, 5, 6
            page = context.pages[0] if context.pages else context.new_page()

            page.goto("https://web.whatsapp.com")
            micro_pause(3000, 5000)

            # Detectar si ya hay sesión activa o si necesita QR
            page_state = "needs_qr"
            try:
                page.wait_for_selector(SELECTORS["pane_side"], timeout=20000)
                page_state = "logged_in"
            except PWTimeout:
                pass  # Necesita QR

            if page_state != "logged_in":
                # El usuario ve el QR en pantalla y escanea con su celular
                try:
                    page.wait_for_selector(SELECTORS["pane_side"], timeout=timeout_seconds * 1000)
                    page_state = "logged_in"
                except PWTimeout:
                    context.close()
                    return False, "", "", f"Timeout: el QR no fue escaneado en {timeout_seconds} segundos."

            # Extraer datos del perfil
            phone = ""
            profile_name = ""
            for _ in range(5):
                try:
                    phone = page.evaluate(
                        "(() => { const u = window.Store?.User?.getMaybeMeUser?.(); "
                        "return u?.id?.user || ''; })()"
                    ) or ""
                    profile_name = page.evaluate(
                        "document.querySelector('[data-testid=\"default-user\"]')?.textContent "
                        "|| document.title || ''"
                    ) or ""
                    phone = str(phone).strip()
                    profile_name = str(profile_name).strip()
                    if phone or profile_name:
                        break
                except Exception:
                    pass
                page.wait_for_timeout(2000)

            save_wa_session_info(profile_name=profile_name, phone=phone)
            context.close()

            return True, phone, profile_name, ""

    except Exception as e:
        return False, "", "", str(e)

# ---------------------------------------------------------------------------
# PASO 2 — Envío de mensajes
# ---------------------------------------------------------------------------

def send_whatsapp_messages(
    contacts: list,
    message_template: str,
    speed: str = "Normal (Recomendado)",
    progress_callback=None,
    on_client_sent=None,
    shuffle: bool = True,
    long_pause_every: int = 10,
    country_code: str = "51",
) -> dict:
    """
    PASO 2 DE LA ARQUITECTURA: Envía mensajes masivos usando la sesión guardada.

    Prerequisito: connect_wa_session() debe haberse ejecutado previamente y
    get_wa_session_info()["status"] debe ser "active".

    Args:
        contacts:           Lista de dicts. Cada uno debe tener 'telefono' y las
                            variables que usa el template (ej: 'nombre', 'saldo').
        message_template:   Texto con variables tipo {nombre}, {saldo}, etc.
        speed:              Velocidad de envío. Ver SPEED_RANGES.
        progress_callback:  fn(current, total, status, log_text) — actualiza UI.
        on_client_sent:     fn(id_cliente, resultado, contact_dict) — registra en BD.
                            resultado es "SIN_RESPUESTA" (éxito) o "FALLIDO".
        shuffle:            True para mezclar el orden de contactos (Protección 9).
        long_pause_every:   Pausa larga cada N mensajes (Protección 4).
        country_code:       Código de país (default: "51" = Perú).

    Returns:
        dict: {
            'exitosos': int,
            'fallidos': int,
            'log': str,
            'resultados_por_cliente': dict  # id → 'SIN_RESPUESTA' | 'FALLIDO'
        }

    Nota sobre resultados:
        'SIN_RESPUESTA' = mensaje enviado exitosamente. El gestor actualiza
        manualmente el resultado cuando el cliente responde (EXITOSO,
        PROMESA_PAGO, EN_NEGOCIACION, etc.).
        'FALLIDO' = no se pudo enviar (número inválido, timeout, error).
    """
    if not _PLAYWRIGHT_OK:
        return {
            "exitosos": 0,
            "fallidos": len(contacts),
            "log": "ERROR: Playwright no instalado.",
            "resultados_por_cliente": {},
        }

    # Preparar contactos: normalizar teléfono, reemplazar variables, mezclar orden
    processed = []
    for c in contacts:
        copy = c.copy()
        copy["telefono"] = normalize_phone(c.get("telefono", ""), country_code)
        copy["mensaje"]  = replace_variables(message_template, copy)
        if "nombre" not in copy:
            copy["nombre"] = copy.get("nombre_cliente", "Cliente")
        processed.append(copy)

    if shuffle:                            # Protección 9: orden aleatorio
        random.shuffle(processed)

    exitosos   = 0
    fallidos   = 0
    errores    = []
    log_lines  = []
    resultados = {}

    def log(text: str):
        ts = datetime.now().strftime("%H:%M:%S")
        log_lines.append(f"[{ts}] {text}")

    try:
        with sync_playwright() as pw:
            log("Iniciando navegador...")
            context = launch_browser(pw)   # Protecciones 1, 5, 6
            page    = context.pages[0] if context.pages else context.new_page()

            log("Navegando a WhatsApp Web...")
            page.goto("https://web.whatsapp.com")
            micro_pause(3000, 5000)        # Protección 3

            # Detectar sesión activa
            try:
                page.wait_for_selector(SELECTORS["pane_side"], timeout=20000)
                log("✅ Sesión WhatsApp activa. No es necesario escanear QR.")
            except PWTimeout:
                log("📱 Sesión no encontrada. Escanea el código QR.")
                if progress_callback:
                    progress_callback(0, len(processed), "Esperando escaneo de QR...", "\n".join(log_lines))
                try:
                    page.wait_for_selector(SELECTORS["pane_side"], timeout=120_000)
                    log("✅ Sesión iniciada correctamente.")
                except PWTimeout:
                    log("⏰ Timeout: QR no escaneado. Abortando.")
                    context.close()
                    return {"exitosos": 0, "fallidos": len(processed),
                            "log": "\n".join(log_lines), "resultados_por_cliente": {}}

            # Actualizar info de sesión
            try:
                phone = page.evaluate(
                    "(() => { const u = window.Store?.User?.getMaybeMeUser?.(); "
                    "return u?.id?.user || ''; })()"
                ) or ""
                profile = page.evaluate("document.title || ''") or ""
                save_wa_session_info(profile_name=str(profile).strip(), phone=str(phone).strip())
                if phone:
                    log(f"📱 Dispositivo: {profile} ({phone})")
            except Exception:
                pass

            micro_pause(2000, 4000)
            log("=" * 55)
            log(f"INICIANDO ENVÍO — {len(processed)} contactos | Velocidad: {speed}")
            log("=" * 55)

            for i, contact in enumerate(processed, 1):
                phone      = contact["telefono"]
                msg        = contact["mensaje"]
                nombre     = contact["nombre"]
                id_cliente = str(contact.get("id_cliente", "") or str(i)).strip()

                maybe_long_pause(i, every_n=long_pause_every, log_fn=log)  # Protección 4
                clear_clipboard()                                           # Protección 10

                if not phone:
                    log(f"[{i}/{len(processed)}] ⚠️ Saltando {nombre}: sin número de teléfono")
                    fallidos += 1
                    resultados[id_cliente] = "FALLIDO"
                    if on_client_sent:
                        on_client_sent(id_cliente, "FALLIDO", contact)
                    continue

                try:
                    log(f"[{i}/{len(processed)}] → {nombre} ({phone})")
                    if progress_callback:
                        progress_callback(i - 1, len(processed), f"Enviando a {nombre}...", "\n".join(log_lines))

                    page.goto(f"https://web.whatsapp.com/send?phone={phone}")
                    micro_pause(800, 2000)                                  # Protección 3

                    timeout_chat = 60 if i == 1 else 30                    # Protección 8
                    chat_ok = wait_for_chat(page, timeout_s=timeout_chat)  # Protección 7

                    if not chat_ok:
                        if check_invalid_number(page):
                            log(f"    ❌ Número no encontrado en WhatsApp: {phone}")
                        else:
                            log(f"    ❌ Timeout cargando chat ({timeout_chat}s)")
                        fallidos += 1
                        resultados[id_cliente] = "FALLIDO"
                        errores.append(f"{nombre} ({phone}): inválido o timeout")
                        if on_client_sent:
                            on_client_sent(id_cliente, "FALLIDO", contact)
                        continue

                    micro_pause(1000, 2500)                                 # Protección 3

                    input_box = page.wait_for_selector(SELECTORS["input_box"], timeout=15000)
                    input_box.evaluate("el => el.focus()")
                    micro_pause(200, 500)                                   # Protección 3
                    input_box.click()
                    micro_pause(300, 700)                                   # Protección 3

                    import pyperclip
                    pyperclip.copy(msg)
                    page.keyboard.press("Control+V")
                    micro_pause(500, 1200)                                  # Protección 3

                    page.keyboard.press("Enter")
                    micro_pause(600, 1500)                                  # Protección 3

                    log(f"    ✅ Enviado correctamente")
                    exitosos += 1
                    resultados[id_cliente] = "SIN_RESPUESTA"
                    if on_client_sent:
                        on_client_sent(id_cliente, "SIN_RESPUESTA", contact)

                except Exception as e:
                    log(f"    ❌ Error: {str(e)[:150]}")
                    fallidos += 1
                    resultados[id_cliente] = "FALLIDO"
                    errores.append(f"{nombre}: {str(e)[:80]}")
                    if on_client_sent:
                        on_client_sent(id_cliente, "FALLIDO", contact)

                if i < len(processed):                                      # Protección 2
                    delay_applied = human_delay(speed)
                    log(f"    ⏳ Pausa {delay_applied:.1f}s antes del siguiente...")

            log("=" * 55)
            log(f"ENVÍO COMPLETADO — Exitosos: {exitosos} | Fallidos: {fallidos}")
            log("=" * 55)
            context.close()

    except Exception as e:
        log(f"❌ ERROR FATAL DEL NAVEGADOR: {str(e)}")

    if progress_callback:
        progress_callback(len(processed), len(processed), "Finalizado", "\n".join(log_lines))

    return {
        "exitosos":               exitosos,
        "fallidos":               fallidos,
        "log":                    "\n".join(log_lines),
        "resultados_por_cliente": resultados,
    }
```

---

## Cómo integrar en la UI (Streamlit)

La UI debe reflejar la arquitectura de dos pasos. La sección de WhatsApp necesita dos áreas claramente separadas:

### Área 1: Estado del dispositivo

```python
import streamlit as st
from whatsapp_human_sender import get_wa_session_info, connect_wa_session, clear_wa_session

info = get_wa_session_info()

if info["status"] == "active":
    st.success(f"📱 Dispositivo conectado: {info.get('profile_name','')} ({info.get('phone','')})")
    st.caption(f"Conectado el: {info.get('verified_at','')}")
    if st.button("Desconectar"):
        clear_wa_session()
        st.rerun()
else:
    st.warning("📵 Dispositivo no conectado")
    if st.button("Conectar WhatsApp"):
        with st.spinner("Abriendo WhatsApp Web... Escanea el QR en la ventana de Chrome"):
            ok, phone, name, err = connect_wa_session(timeout_seconds=120)
        if ok:
            st.success(f"✅ Conectado: {name} ({phone})")
            st.rerun()
        else:
            st.error(f"Error al conectar: {err}")
```

### Área 2: Envío de mensajes

```python
from whatsapp_human_sender import send_whatsapp_messages, get_wa_session_info

# Verificar que el dispositivo esté conectado antes de permitir el envío
if get_wa_session_info()["status"] != "active":
    st.error("Primero debes conectar el dispositivo (sección de arriba).")
    st.stop()

# Preparar contactos
contacts = [
    {"id_cliente": "000001", "telefono": "987654321", "nombre": "Empresa ABC", "saldo": "S/ 1,500.00"},
    {"id_cliente": "000002", "telefono": "912345678", "nombre": "Empresa XYZ", "saldo": "S/ 3,200.00"},
]

template = "Estimados {nombre}, tienen un saldo pendiente de {saldo}. Agradecemos su pronta atención."

speed = st.selectbox("Velocidad de envío", [
    "Normal (Recomendado)",
    "Lenta (Más seguro)",
    "Rápida (Riesgo de bloqueo)",
])

if st.button("Enviar mensajes"):
    progress_bar = st.progress(0)
    log_area     = st.empty()

    def on_progress(current, total, status, log_text):
        if total > 0:
            progress_bar.progress(current / total)
        log_area.text(log_text)

    def on_sent(id_cliente, resultado, contact):
        # Registrar en base de datos
        pass  # implementar según el proyecto

    result = send_whatsapp_messages(
        contacts         = contacts,
        message_template = template,
        speed            = speed,
        progress_callback= on_progress,
        on_client_sent   = on_sent,
    )

    st.success(f"✅ Enviados: {result['exitosos']} | ❌ Fallidos: {result['fallidos']}")
```

---

## Notas de implementación

- **Playwright vs Selenium:** Este módulo usa Playwright. Si el proyecto usa Selenium, las protecciones 1, 3, 7 y 8 aplican igual pero la sintaxis cambia. Las protecciones 2, 4, 5, 6, 9 y 10 son agnósticas a la librería.
- **No usar archivos .bat para el envío:** Todo el flujo (conexión y envío) se ejecuta desde dentro de la aplicación, invocando las funciones Python directamente. Los archivos `.bat` solo sirven para arrancar el servidor de la app (ej: `streamlit run app.py`).
- **Sistema operativo:** La protección 10 (limpieza de portapapeles) usa PowerShell y aplica solo a Windows. En Linux/Mac, reemplazar el comando por `xclip -selection clipboard /dev/null` o `pbcopy < /dev/null`.
- **Velocidad "Rápida":** Aunque se ofrece como opción, se desaconseja para lotes mayores a 20 mensajes. Para producción, usar siempre "Normal" o "Lenta".
- **Tamaño del lote:** Para cuentas nuevas o que hayan recibido advertencias, no superar 30 mensajes por sesión el primer mes. Aumentar gradualmente.
- **Horario de envío:** Los envíos en horario laboral (8am–6pm, lunes a viernes) generan menos alertas que los envíos nocturnos o en fin de semana.
- **Instalación:** `pip install playwright pyperclip && playwright install chromium`

---

## Prompt para la IA del nuevo proyecto

> Copie y pegue este bloque completo como instrucción a la IA que desarrolla el nuevo proyecto.

```
CONTEXTO:
Voy a implementar un módulo de envío masivo por WhatsApp Web en Python usando Playwright.
La cuenta que usará este sistema fue notificada en el pasado por Meta por envío automatizado.
Existe una guía técnica completa (WHATSAPP_HUMAN_SENDER_GUIDE.md) con la arquitectura
correcta y las 10 protecciones anti-detección probadas en producción.

ARQUITECTURA OBLIGATORIA — DOS PASOS SEPARADOS:

PASO 1: connect_wa_session()
  - Abre Chrome, muestra QR, espera que el usuario escanee con su celular
  - Guarda la sesión en disco (directorio persistente)
  - Extrae phone y profile_name del perfil conectado
  - Cierra Chrome
  - Retorna: (ok: bool, phone: str, profile_name: str, error_msg: str)
  - Este paso se hace UNA SOLA VEZ, luego la sesión queda guardada

PASO 2: send_whatsapp_messages()
  - Abre Chrome con la sesión guardada (sin pedir QR si está activa)
  - Por cada contacto: navega al chat, pega el mensaje, envía, espera delay aleatorio
  - Al terminar: cierra Chrome, retorna resultados
  - Parámetros: contacts (list), message_template (str), speed (str),
    progress_callback (fn), on_client_sent (fn), shuffle (bool)

FUNCIONES ADICIONALES OBLIGATORIAS:
  - get_wa_session_info() → dict con { status, verified_at, phone, profile_name }
  - clear_wa_session()    → elimina sesión guardada
  - normalize_phone()     → agrega código de país si el número tiene 9 dígitos
  - replace_variables()   → reemplaza {variables} en el template

LAS 10 PROTECCIONES ANTI-DETECCIÓN (todas obligatorias):

1. launch_persistent_context() con:
   - headless=False (NUNCA True)
   - args=["--disable-blink-features=AutomationControlled", ...]
   - ignore_default_args=["--enable-automation"]  ← LA MÁS IMPORTANTE

2. Delays ALEATORIOS entre mensajes (nunca fijos):
   SPEED_RANGES = { "Normal": (8,15), "Rápida": (3,7), "Lenta": (15,30) }
   human_delay(speed) → random.uniform(min, max)

3. Micro-pausas entre cada acción del navegador:
   micro_pause() → random.uniform(0.3, 1.2) segundos
   Después de goto(), click(), Control+V, Enter

4. Pausa larga cada 10 mensajes:
   maybe_long_pause() → random.uniform(45, 120) segundos

5. Sesión persistente en directorio fijo:
   WA_SESSION_DIR = os.path.join(tempfile.gettempdir(), "proyecto_wa_session")
   user_data_dir=WA_SESSION_DIR en launch_persistent_context()

6. Limpieza de archivos de bloqueo ANTES de lanzar el navegador:
   Eliminar: SingletonLock, SingletonCookie, SingletonSocket,
   Last Session, Last Tabs, Current Session, Current Tabs

7. Detección rápida de número inválido (Fast Fail):
   check_invalid_number() dentro del while loop de espera, no al final

8. Timeout dinámico:
   timeout_chat = 60 if i == 1 else 30  (primer mensaje = carga fría)

9. Orden aleatorio de contactos:
   random.shuffle(contacts) antes del loop

10. Limpiar portapapeles antes de cada mensaje:
    subprocess.run(["powershell", "-command", "Set-Clipboard -Value $null"])

REGLAS DE IMPLEMENTACIÓN:
- No usar archivos .bat para el envío — todo se invoca desde Python
- on_client_sent(id_cliente, resultado, contact) donde resultado es
  "SIN_RESPUESTA" (enviado) o "FALLIDO"
- progress_callback(current, total, status, log_text) para actualizar la UI
- pyperclip.copy(msg) + page.keyboard.press("Control+V") para pegar el mensaje
- Registrar en _session_info.json: { status, verified_at, phone, profile_name }
```
