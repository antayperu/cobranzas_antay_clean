# 🚀 Integración Supabase - Sistema de Cobranzas Antay

**Versión:** 1.0
**Fecha:** 2026-02-05
**Autor:** Antay Consultoría

---

## 📋 Tabla de Contenidos

1. [Introducción](#introducción)
2. [Arquitectura Híbrida](#arquitectura-híbrida)
3. [Configuración Inicial](#configuración-inicial)
4. [Estructura de Base de Datos](#estructura-de-base-de-datos)
5. [Uso del Cliente Supabase](#uso-del-cliente-supabase)
6. [Migración de Datos](#migración-de-datos)
7. [Testing y Validación](#testing-y-validación)
8. [Troubleshooting](#troubleshooting)

---

## 🎯 Introducción

Este sistema implementa una **arquitectura híbrida** que permite operar en dos modos:

- **MODO LOCAL:** Usa SQLite + session_state (sin configuración de Supabase)
- **MODO CLOUD:** Usa Supabase para persistencia en la nube (requiere credenciales)

La aplicación detecta automáticamente qué modo usar basándose en la presencia de credenciales de Supabase en `.env`.

---

## 🏗️ Arquitectura Híbrida

### Flujo de Decisión

```
┌─────────────────────────────────────┐
│  Inicio de Aplicación               │
└──────────────┬──────────────────────┘
               │
               ▼
        ¿Credenciales
         Supabase en .env?
               │
       ┌───────┴───────┐
       │               │
      SÍ              NO
       │               │
       ▼               ▼
┌──────────────┐  ┌──────────────┐
│ MODO CLOUD   │  │ MODO LOCAL   │
│ (Supabase)   │  │ (SQLite)     │
└──────────────┘  └──────────────┘
```

### Componentes

1. **SupabaseClient** (`utils/supabase_client.py`)
   - Singleton pattern
   - Lazy initialization
   - Fallback automático a session_state

2. **Scripts SQL** (`sql/`)
   - 4 tablas principales
   - Índices optimizados
   - Triggers para updated_at

3. **db_manager.py** (existente)
   - Maneja ledger_last_send y send_attempts
   - Compatible con ambos modos

---

## ⚙️ Configuración Inicial

### Paso 1: Crear Proyecto en Supabase

1. Ir a [https://supabase.com](https://supabase.com)
2. Crear cuenta o iniciar sesión
3. Crear nuevo proyecto:
   - **Name:** cobranzas-antay
   - **Database Password:** (guardar en lugar seguro)
   - **Region:** South America (sao-paulo) o más cercana

### Paso 2: Obtener Credenciales

1. En Supabase Dashboard:
   - Ir a **Settings** > **API**
   - Copiar **Project URL**
   - Copiar **Service Role Key** (⚠️ NO usar anon key)

### Paso 3: Configurar Variables de Entorno

1. Copiar `.env.example` a `.env`:
   ```bash
   cp .env.example .env
   ```

2. Editar `.env` con tus credenciales:
   ```env
   SUPABASE_URL=https://tu-proyecto.supabase.co
   SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

### Paso 4: Instalar Dependencias

```bash
pip install -r requirements.txt
```

### Paso 5: Crear Tablas en Supabase

1. En Supabase Dashboard:
   - Ir a **SQL Editor**
   - Crear nueva query

2. Ejecutar cada script SQL en orden:
   ```sql
   -- Ejecutar en este orden:
   -- 1. sql/01_create_clientes.sql
   -- 2. sql/02_create_documentos.sql
   -- 3. sql/03_create_cobranzas.sql
   -- 4. sql/04_create_notificaciones.sql
   ```

3. Verificar que las tablas se crearon:
   ```sql
   SELECT table_name
   FROM information_schema.tables
   WHERE table_schema = 'public'
     AND table_name IN ('clientes', 'documentos', 'cobranzas', 'notificaciones')
   ORDER BY table_name;
   ```

---

## 🗄️ Estructura de Base de Datos

### Tabla: clientes

| Campo       | Tipo      | Descripción                  |
|-------------|-----------|------------------------------|
| id          | UUID      | PK, auto-generado            |
| cliente_id  | TEXT      | ID único de negocio          |
| nombre      | TEXT      | Nombre del cliente           |
| email       | TEXT      | Email del cliente            |
| telefono    | TEXT      | Teléfono                     |
| ruc         | TEXT      | RUC/documento                |
| estado      | TEXT      | ACTIVO/INACTIVO/MOROSO       |
| created_at  | TIMESTAMP | Fecha de creación            |
| updated_at  | TIMESTAMP | Última actualización         |

### Tabla: documentos

| Campo              | Tipo      | Descripción                  |
|--------------------|-----------|------------------------------|
| id                 | UUID      | PK, auto-generado            |
| documento_id       | TEXT      | ID único del documento       |
| cliente_id         | TEXT      | FK a clientes                |
| tipo_documento     | TEXT      | FACTURA/BOLETA/etc           |
| numero_documento   | TEXT      | Número de documento          |
| fecha_emision      | DATE      | Fecha de emisión             |
| fecha_vencimiento  | DATE      | Fecha de vencimiento         |
| monto_total        | DECIMAL   | Monto total del documento    |
| monto_pendiente    | DECIMAL   | Monto pendiente de pago      |
| moneda             | TEXT      | PEN/USD/EUR                  |
| estado             | TEXT      | PENDIENTE/PAGADO/VENCIDO     |

### Tabla: cobranzas

| Campo           | Tipo      | Descripción                  |
|-----------------|-----------|------------------------------|
| id              | UUID      | PK, auto-generado            |
| documento_id    | TEXT      | FK a documentos              |
| cliente_id      | TEXT      | FK a clientes                |
| tipo_gestion    | TEXT      | EMAIL/WHATSAPP/LLAMADA       |
| estado_gestion  | TEXT      | ENVIADO/ENTREGADO/FALLIDO    |
| fecha_gestion   | TIMESTAMP | Fecha de la gestión          |
| responsable     | TEXT      | Usuario que gestionó         |
| resultado       | TEXT      | Resultado de la gestión      |
| metadata        | JSONB     | Datos adicionales            |

### Tabla: notificaciones

| Campo              | Tipo      | Descripción                  |
|--------------------|-----------|------------------------------|
| id                 | UUID      | PK, auto-generado            |
| tipo_notificacion  | TEXT      | VENCIMIENTO/PAGO_RECIBIDO    |
| prioridad          | TEXT      | BAJA/NORMAL/ALTA/URGENTE     |
| destinatario       | TEXT      | Email o teléfono             |
| asunto             | TEXT      | Asunto de la notificación    |
| mensaje            | TEXT      | Cuerpo del mensaje           |
| estado             | TEXT      | PENDIENTE/ENVIADO/LEIDO      |
| fecha_envio        | TIMESTAMP | Fecha de envío               |

---

## 💻 Uso del Cliente Supabase

### Ejemplo Básico

```python
from utils.supabase_client import SupabaseClient

# Obtener instancia del cliente (singleton)
client = SupabaseClient.get_instance()

# Verificar si Supabase está disponible
if client.is_available():
    print("✅ Modo CLOUD - Usando Supabase")

    # Consultar clientes
    result = client.from_('clientes').select('*').limit(10).execute()
    print(f"Clientes encontrados: {len(result.data)}")

else:
    print("⚠️  Modo LOCAL - Usando session_state")
    # Usar fallback
    fallback = SupabaseClient.get_fallback_storage()
    clientes = fallback['clientes']
```

### Operaciones CRUD

#### CREATE (Insertar)

```python
client = SupabaseClient.get_instance()

nuevo_cliente = {
    "cliente_id": "CLI-001",
    "nombre": "Empresa ABC SAC",
    "email": "contacto@empresaabc.com",
    "ruc": "20123456789",
    "estado": "ACTIVO"
}

result = client.from_('clientes').insert(nuevo_cliente).execute()
```

#### READ (Consultar)

```python
# Todos los clientes activos
result = client.from_('clientes')\
    .select('*')\
    .eq('estado', 'ACTIVO')\
    .execute()

# Buscar por cliente_id
result = client.from_('clientes')\
    .select('*')\
    .eq('cliente_id', 'CLI-001')\
    .single()\
    .execute()
```

#### UPDATE (Actualizar)

```python
result = client.from_('clientes')\
    .update({'estado': 'MOROSO'})\
    .eq('cliente_id', 'CLI-001')\
    .execute()
```

#### DELETE (Eliminar)

```python
result = client.from_('clientes')\
    .delete()\
    .eq('cliente_id', 'CLI-001')\
    .execute()
```

### Funciones Helper Compatibles

```python
from utils.supabase_client import get_supabase_client, is_cloud_mode

# Compatible con código legacy
client = get_supabase_client()
if is_cloud_mode():
    # Lógica para modo cloud
    pass
```

---

## 🔄 Migración de Datos

### De SQLite a Supabase

```python
import sqlite3
import pandas as pd
from utils.supabase_client import SupabaseClient

def migrate_to_supabase():
    """Migra datos de SQLite local a Supabase."""
    client = SupabaseClient.get_instance()

    if not client.is_available():
        print("❌ Supabase no disponible")
        return

    # Conectar a SQLite
    conn = sqlite3.connect("email_ledger.db")

    # Migrar send_attempts
    df = pd.read_sql_query("SELECT * FROM send_attempts", conn)
    records = df.to_dict('records')

    for record in records:
        client.from_('cobranzas').insert({
            'tipo_gestion': 'EMAIL',
            'estado_gestion': record['status'],
            'fecha_gestion': record['timestamp'],
            # Mapear campos según necesidad
        }).execute()

    conn.close()
    print("✅ Migración completada")
```

---

## ✅ Testing y Validación

### Gate 0: Verificar que el código compila

```bash
cd /c/dev/ReporteCobranzas
python -c "from utils.supabase_client import SupabaseClient; print('✅ Import exitoso')"
```

### Verificar conexión a Supabase

```python
from utils.supabase_client import SupabaseClient

client = SupabaseClient.get_instance()
print(f"Supabase disponible: {client.is_available()}")
print(f"Modo Cloud: {SupabaseClient.is_cloud_mode()}")
```

### Test de inserción simple

```python
from utils.supabase_client import SupabaseClient

client = SupabaseClient.get_instance()

if client.is_available():
    # Insertar cliente de prueba
    result = client.from_('clientes').insert({
        'cliente_id': 'TEST-001',
        'nombre': 'Cliente de Prueba',
        'estado': 'ACTIVO'
    }).execute()

    print(f"✅ Inserción exitosa: {result.data}")

    # Limpiar
    client.from_('clientes').delete().eq('cliente_id', 'TEST-001').execute()
```

---

## 🔧 Troubleshooting

### Error: "Supabase package not installed"

**Solución:**
```bash
pip install supabase==2.3.0
```

### Error: "Supabase credentials not found"

**Causa:** Falta configurar `.env`

**Solución:**
1. Verificar que `.env` existe
2. Verificar que contiene `SUPABASE_URL` y `SUPABASE_SERVICE_ROLE_KEY`
3. Reiniciar la aplicación

### Error: "Connection refused"

**Causa:** URL de Supabase incorrecta o proyecto pausado

**Solución:**
1. Verificar URL en Supabase Dashboard
2. Verificar que el proyecto está activo (no pausado)
3. Verificar conexión a internet

### La app usa LOCAL mode en lugar de CLOUD

**Diagnóstico:**
```python
import os
from dotenv import load_dotenv

load_dotenv()
print(f"SUPABASE_URL: {os.getenv('SUPABASE_URL')}")
print(f"SUPABASE_KEY: {os.getenv('SUPABASE_SERVICE_ROLE_KEY')[:20]}...")
```

**Solución:** Verificar que las variables están en `.env` y el archivo está en la raíz del proyecto.

### Error: "Foreign key constraint failed"

**Causa:** Intentar insertar documentos antes de crear el cliente

**Solución:** Siempre insertar en orden:
1. clientes
2. documentos
3. cobranzas/notificaciones

---

## 📚 Referencias

- [Documentación Supabase](https://supabase.com/docs)
- [Supabase Python Client](https://github.com/supabase-community/supabase-py)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

---

## 🤝 Soporte

Para soporte o preguntas:
- **Email:** consultas@antayperu.com
- **Metodología Antay:** Seguir procedimientos documentados en `utils/antay_methodology.py`

---

**Última actualización:** 2026-02-05
**Versión:** 1.0
