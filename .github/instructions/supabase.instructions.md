---
applyTo: "sql/**,utils/supabase_*.py,utils/db_manager.py"
---

# Schema Supabase — ReporteCobranzas

Eres el guardián del schema de base de datos del proyecto ReporteCobranzas.
Aplica estas reglas en todos los archivos SQL y de operaciones Supabase.

## Principio fundamental: Cloud-only

- Supabase PostgreSQL cloud es la ÚNICA fuente de persistencia
- NO implementar fallback SQLite ni session_state como BD
- Si Supabase no responde → bloqueo controlado con mensaje de error

## Tablas y reglas

### `clientes` — MAESTRA
- **Carga:** UNA VEZ desde Excel "Cartera de Clientes"
- **Mantenimiento:** Solo desde Tab Clientes Premium en la app
- **NO se recarga** en cada ciclo de Excel
- Primary key: `cod_cliente TEXT`

### `documentos` — TRANSACCIONAL
- **Carga:** Se RECARGA en cada ciclo con Excel "Cuentas por Cobrar"
- Mantiene histórico por `fecha_carga`
- Un documento puede tener múltiples registros (uno por fecha de carga)

### `cobranzas` — TRANSACCIONAL
- **Carga:** Se RECARGA en cada ciclo con Excel "Cobranzas (Detalle)"
- Permite calcular: `SaldoReal = monto_original - SUM(monto_aplicado)`

### `notificaciones` — TRANSACCIONAL CRÍTICA
- **NUNCA se borra**
- Se llena automáticamente al enviar desde la app
- Campos críticos: `cod_cliente`, `tipo` (EMAIL/WHATSAPP), `cycle_id`, `estado`, `metadata` (JSONB)
- `metadata.source` distingue: envío automático (sin source) vs gestión manual cobrador (con source)

### `gestiones` — TRANSACCIONAL
- Registros de contacto CRM (llamadas, acuerdos verbales, resultados post-envío WA)
- Campo `resultado`: `EXITOSO` / `PROMETIO_PAGAR` / `SIN_RESPUESTA` / `ESCALAR`
- Campo `cycle_id` para trazabilidad por ciclo
- Campo `metadata` JSONB para datos adicionales (template usado, canal, etc.)

### `acuerdos_pago` — TRANSACCIONAL
- Un registro por acuerdo negociado con el cliente
- FK a `clientes.cod_cliente`

### `cuotas_acuerdo` — TRANSACCIONAL
- N registros por acuerdo (una fila por cuota)
- Estados: `PENDIENTE` / `PAGADA` / `VENCIDA`
- FK a `acuerdos_pago.id`

### `ciclos_procesamiento` — TRANSACCIONAL
- Un registro por ciclo cargado
- `cycle_id` formato: `CIC-YYYYMMDD-HHMM`
- Se ACUMULA — nunca se borra al cargar nuevos archivos
- Metadata: nombre de archivo, conteo de filas, timestamp

### `resumen_cliente_ciclo` — ANALÍTICA
- 1 fila por cliente por ciclo al cierre del ciclo
- Alimenta dashboard e informe gerencial

### `resumen_ciclo` — ANALÍTICA
- 1 fila por ciclo con totales de cartera

### `app_config` — CONFIGURACIÓN
- Plantillas WA, parámetros SMTP, configuración general
- Clave-valor con JSONB para valores complejos

## Operaciones por tabla

Toda operación pasa por `utils/db_manager.py`. Funciones clave:
- `insert_gestion()` — registrar gestión CRM
- `insert_acuerdo_pago()` — crear acuerdo (sin `.select()` encadenado — no soportado en supabase-py sync)
- `persist_notification_event()` — registrar envío
- `reconcile_ciclo_recovery()` — reconciliar documentos recuperados
- `attempt_auto_restore()` — restaurar último ciclo al abrir app

## Políticas RLS (Row Level Security)

- Usar bloque `DO $$` para crear políticas — `CREATE POLICY IF NOT EXISTS` no es compatible con PostgreSQL

```sql
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE policyname = 'nombre_policy' AND tablename = 'nombre_tabla'
  ) THEN
    CREATE POLICY nombre_policy ON nombre_tabla ...;
  END IF;
END $$;
```

## Convenciones SQL

- Nombres de tabla: `snake_case` en minúsculas
- Primary keys: `UUID DEFAULT gen_random_uuid()` o `TEXT` (cod_cliente)
- Timestamps: `TIMESTAMP DEFAULT NOW()`
- Estados como TEXT con CHECK constraint
- JSONB para metadata flexible
- Scripts en `sql/` nombrados secuencialmente: `01_`, `02_`, etc.
