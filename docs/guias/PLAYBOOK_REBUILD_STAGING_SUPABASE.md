# Playbook Rebuild Staging Supabase

Objetivo: reiniciar schema operativo, recrear todo el modelo y validar contrato de integridad antes de usar la app.

## Orden obligatorio

1. Ejecutar reset total:
- Archivo: sql/90_reset_transaccional_total.sql
- Resultado esperado: SELECT final con RESET_TOTAL_OK.

2. Ejecutar bootstrap completo:
- Archivo: sql/91_bootstrap_schema_full.sql
- Resultado esperado: SELECT final con BOOTSTRAP_SCHEMA_OK.

3. Ejecutar verificacion de contrato:
- Archivo: sql/92_verify_schema_contract.sql
- Resultado esperado: SELECT final con SCHEMA_CONTRACT_OK.
- Si falla cualquier DO $$ ... RAISE EXCEPTION, NO usar la app.

4. Recien despues, iniciar app en staging:
- PowerShell: .\\start_staging.ps1
- URL: http://localhost:8502

## Criterio de bloqueo

- Si el paso 3 falla: ambiente NO APTO.
- Si al procesar ciclo la app muestra error de persistencia cloud: detener pruebas y corregir schema.

## Politica operativa

- Fuente de verdad: Supabase.
- No aprobar smoke test ni liberar release sin SCHEMA_CONTRACT_OK en el ambiente objetivo.
- Repetir este playbook para cada nueva base QA/staging antes del primer uso.
