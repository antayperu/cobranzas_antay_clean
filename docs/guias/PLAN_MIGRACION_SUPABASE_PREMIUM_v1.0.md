# Plan Maestro de Migracion a Supabase (Premium)

Fecha: 2026-02-15  
Proyecto: ReporteCobranzas (Antay)  
Referencia funcional: FRD v0.2 - ReporteCobranzas (Notion ID: `2dd7544a512b80c8a893e3b76fc51d2e`)

---

## 1. Objetivo Ejecutivo

Migrar la persistencia de datos desde memoria local (`session_state`) a Supabase sin romper:

1. El flujo funcional actual de 3 Excel.
2. La UX existente (misma UI de carga, mismos tabs).
3. El reporte/export Excel final (mismos campos, calculos y comportamiento).

Meta premium:
- Mantener la experiencia actual.
- Aumentar trazabilidad, auditabilidad y robustez operacional.

---

## 2. Principios No Negociables

1. Cero regresion funcional en logica de negocio.
2. Cero regresion UX visible para el usuario final.
3. Cero regresion en estructura y comportamiento del Excel exportado.
4. Integridad referencial obligatoria en Supabase.
5. Arquitectura cloud-only: operaciones productivas siempre contra Supabase.

---

## 3. Flujo Funcional Oficial (FRD)

El flujo de operacion se mantiene:

1. Cargar `Ctas x Cobrar`.
2. Cargar `Detalle Cobranzas`.
3. Cargar `Cartera de clientes`.
4. Fusionar datos y calcular:
   - Deuda por cliente
   - Detraccion
   - Saldo real
5. Visualizar reporte.
6. Exportar Excel.
7. Enviar notificaciones.
8. Registrar trazabilidad.

---

## 4. Contrato UX (Misma Interfaz)

La migracion NO cambia la forma de uso:

1. Se conserva la misma pantalla y uploaders del sidebar.
2. Se mantienen mismos filtros y tabs.
3. Se mantiene flujo "cargar -> revisar -> exportar -> enviar".

Cambio interno:
- El procesamiento funcional se mantiene y la persistencia obligatoria es en Supabase.

---

## 5. Contrato del Excel de Salida (Paridad Obligatoria)

El Excel generado despues de migrar debe conservar:

1. Mismos campos.
2. Mismo orden de columnas.
3. Mismas formulas/reglas de calculo.
4. Mismo comportamiento de filtros aplicados.
5. Mismo formato funcional esperado por operacion.

Condicion de aceptacion:
- Paridad funcional validada contra baseline actual (pre-migracion).

---

## 6. Modelo de Persistencia en Supabase

## 6.1 Tablas activas

1. `clientes` (maestra)
2. `documentos` (transaccional por ciclo)
3. `cobranzas` (transaccional por ciclo)
4. `notificaciones` (trazabilidad de envio por cliente/documento)
5. `ledger_last_send` (control TTL/rate limit)
6. `send_attempts` (historial tecnico de intentos)

## 6.2 Regla de integridad de cobranzas

No se insertan filas huerfanas en `cobranzas`.
Una cobranza solo se guarda si su documento existe en `documentos`.

---

## 7. Estado Actual Confirmado

## 7.1 Infraestructura

1. SQL consolidado ejecutado: `sql/EJECUTAR_EN_SUPABASE.sql`
2. Scripts SQL auxiliares en `sql/`.

## 7.2 Migracion base validada (Excel -> Supabase)

Script operativo:
- `scripts/migrate_excel_to_supabase.py`

Resultado de carga:
1. `clientes`: 199
2. `documentos`: 231
3. `cobranzas`: 165

---

## 8. Arquitectura Operacional (Post-Migracion)

## 8.1 Modo operativo cloud-only

1. Usuario carga 3 Excel en la misma UI.
2. App calcula reporte en memoria (igual que hoy).
3. App persiste datos del ciclo en Supabase.
4. App exporta Excel sin cambios funcionales.
5. App registra envios en `notificaciones` y tracking tecnico.

## 8.2 Politica de continuidad premium (sin fallback local)

Si Supabase falla:

1. Se ejecutan reintentos controlados en operaciones transitorias.
2. Se bloquean operaciones criticas de persistencia para evitar inconsistencia.
3. Se muestra mensaje claro de indisponibilidad y estado operacional.
4. Se registra evento tecnico para soporte/observabilidad.

---

## 9. Fases de Implementacion (Cierre Total)

## Fase 0. Baseline y freeze (completada)

1. Confirmar FRD y reglas no negociables.
2. Crear documento plan.
3. Definir criterios de paridad.

## Fase 1. Datos y migracion base (completada)

1. Crear esquema Supabase.
2. Implementar migracion Excel -> Supabase.
3. Validar conteos y regla no-huerfanos.

## Fase 2. Integracion con UI actual (completada)

1. Conectar la carga de 3 archivos desde la misma interfaz.
2. Ejecutar persistencia por ciclo tras carga exitosa.
3. Mantener comportamiento actual de reporte y export.

## Fase 3. Notificaciones premium persistidas (completada)

1. Persistir cada envio en `notificaciones` con `cliente_id`.
2. Vincular `documento_id` cuando aplique.
3. Mantener `send_attempts` como capa tecnica.
4. Exponer consulta por cliente en UI.

## Fase 4. Seguridad y gobierno de datos (completada)

1. Definir RLS/politicas por tabla.
2. Asegurar uso correcto de llaves.
3. Definir backup y restore.
4. Auditoria de cambios.

## Fase 5. QA E2E y release (completada)

1. Validar paridad funcional completa.
2. Validar integridad de datos.
3. Validar trazabilidad de notificaciones.
4. Validar politica cloud-only y bloqueo controlado.
5. Cierre formal de migracion.

---

## 10. Quality Gates (Obligatorios)

## Gate G1 - Integridad

1. Sin cobranzas huerfanas.
2. FK consistentes.

## Gate G2 - Paridad funcional

1. Mismos resultados de deuda y detraccion frente a baseline.
2. Mismos filtros y conteos visibles.

## Gate G3 - Paridad de export Excel

1. Mismas columnas.
2. Mismo orden.
3. Mismos calculos.

## Gate G4 - Notificaciones

1. Envio registra evidencia en DB.
2. Historial por cliente consultable.

## Gate G5 - Resiliencia

1. Si Supabase falla, la app aplica bloqueo controlado en persistencia (sin fallback local).
2. Se mantiene trazabilidad del incidente y mensaje operativo claro.

---

## 11. Definicion de Done (Migracion Completa)

Se declara completa solo cuando:

1. La UI de carga de 3 Excel funciona igual que hoy.
2. El export Excel conserva funcionalidad y campos.
3. `clientes/documentos/cobranzas` persisten por ciclo.
4. `notificaciones` persiste envios por cliente.
5. Existen reportes de notificaciones por cliente.
6. Gates G1-G5 en PASS.

---

## 12. Runbook Operativo

## 12.1 Carga manual por script (bootstrap/soporte)

```powershell
python scripts/migrate_excel_to_supabase.py
python scripts/migrate_excel_to_supabase.py --apply
```

Opcional (ticket `SUPABASE-MIG-004`):

```powershell
python scripts/migrate_excel_to_supabase.py --report-dir reports
python scripts/migrate_excel_to_supabase.py --apply --integrity-check --report-dir reports
```

Salida operativa esperada:

1. Reporte de no-match:
   - `reports/cobranzas_no_match_YYYYMMDD_HHMMSS.csv`
   - `reports/cobranzas_no_match_YYYYMMDD_HHMMSS_summary.json`
2. Integrity check:
   - `orphan_count: 0`

## 12.2 Verificacion rapida

```sql
select count(*) as clientes from clientes;
select count(*) as documentos from documentos;
select count(*) as cobranzas from cobranzas;
select count(*) as notificaciones from notificaciones;
```

```sql
select count(*) as orphan_count
from cobranzas c
left join documentos d on d.documento_id = c.documento_id
where d.documento_id is null
;
```

Expected:
- `orphan_count = 0`.

Para auditoria de no-match (fuente Excel):

1. Revisar `reports/cobranzas_no_match_*.csv`.
2. Validar muestra en `reports/cobranzas_no_match_*_summary.json`.

## 12.3 Seguridad operacional (RLS + llaves)

1. Aplicar script:

```sql
-- Copiar y ejecutar contenido de:
-- sql/06_enable_rls_policies.sql
```

2. Validar checklist:

- `docs/CHECKLIST_SEGURIDAD_SUPABASE_MIG008.md`

3. Regla de entorno:

1. `SUPABASE_SERVICE_ROLE_KEY` solo backend trusted.
2. Nunca exponer service role en frontend/repositorio.
3. Si existe frontend directo a Supabase, usar `anon key` + RLS correspondiente.

## 12.4 Backup y restore operacional (MIG-009)

1. Generar backup:

```powershell
python scripts/backup_restore_supabase.py backup --output-dir reports
```

2. Validar restore en dry-run:

```powershell
python scripts/backup_restore_supabase.py restore --backup-dir reports/supabase_backup_YYYYMMDD_HHMMSS
python scripts/backup_restore_supabase.py restore --backup-dir reports/supabase_backup_YYYYMMDD_HHMMSS --truncate
```

3. Aplicar restore seguro (sin truncate):

```powershell
python scripts/backup_restore_supabase.py restore --backup-dir reports/supabase_backup_YYYYMMDD_HHMMSS --apply --integrity-check
```

4. Aplicar restore completo (con truncado controlado):

```powershell
python scripts/backup_restore_supabase.py restore --backup-dir reports/supabase_backup_YYYYMMDD_HHMMSS --apply --truncate --integrity-check
```

Resultado esperado:
1. Restore exitoso.
2. `orphan_count = 0`.
3. Evidencia en `docs/EVIDENCIA_BACKUP_RESTORE_SUPABASE_MIG009.md`.

## 12.5 Storage de archivos e imagenes (SUPABASE-002)

1. Crear buckets operativos:

```powershell
python scripts/setup_supabase_storage.py
```

2. Buckets esperados:
1. `logos`
2. `exports`
3. `whatsapp-images`

3. Validacion de upload de export:

```powershell
python -c "import utils.storage_manager as sm; print(sm.upload_export_excel(b'test-bytes', 'smoke_storage.xlsx', 'Antay Smoke'))"
```

4. Integraciones operativas:
1. Guardado de logo en tab Configuracion sincroniza en bucket `logos`.
2. Descarga de Excel en Reporte General guarda copia en bucket `exports`.
3. Resolucion de logo en runtime intenta recuperar desde Storage si no existe archivo local.

5. Evidencia:
1. `docs/EVIDENCIA_STORAGE_SUPABASE_002.md`

---

## 13. Riesgos y Mitigaciones

1. Riesgo: historicidad de cobranza no incluida en corte actual de documentos.
   - Mitigacion: excluir huerfanos + reporte de no-match.
2. Riesgo: cambio de estructura de Excel.
   - Mitigacion: deteccion flexible de columnas + alertas.
3. Riesgo: desalineacion de KPI entre memoria y DB.
   - Mitigacion: pruebas de paridad automatizadas.
4. Riesgo: degradacion UX por cambios internos.
   - Mitigacion: contrato UX no-regresion como gate obligatorio.
5. Riesgo: indisponibilidad temporal de Supabase.
   - Mitigacion: retry controlado + bloqueo de operaciones criticas + observabilidad.

---

## 14. Decision Log

1. Fuente operativa primaria: 3 Excel (segun FRD).
2. Interfaz de usuario: se mantiene sin cambios funcionales.
3. Export Excel: paridad obligatoria sin regresion.
4. Registros huerfanos de cobranza: no se insertan.
5. Arquitectura operacional cloud-only (sin fallback local).
6. Migracion se cierra solo con trazabilidad de notificaciones por cliente.
