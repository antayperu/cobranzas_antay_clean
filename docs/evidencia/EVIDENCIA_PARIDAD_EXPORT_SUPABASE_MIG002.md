# Evidencia de Paridad Export Excel - SUPABASE-MIG-002

Fecha: 2026-02-17  
Ticket: SUPABASE-MIG-002  
Objetivo: demostrar no regresion en export Excel (columnas, orden, calculos y filtros).

---

## 1) Contrato de columnas (pre/post)

Contrato vigente centralizado en:
- `utils/excel_export.py` (`EXPORT_COLUMNS_BASELINE`)

Validacion automatizada:
- `tests/test_export_parity.py::test_export_contract_matches_legacy_baseline`

Resultado:
- PASS -> contrato actual coincide con baseline legacy pre-migracion.

---

## 2) Orden de columnas

Validaciones automatizadas:
- `tests/test_export_parity.py::test_export_columns_match_baseline_order`
- `tests/test_export_parity.py::test_build_export_dataframe_keeps_order_and_index`
- `tests/test_export_parity.py::test_generate_excel_keeps_header_order_uppercase`

Resultado:
- PASS -> mismo orden funcional en DataFrame exportado y encabezados del Excel.

---

## 3) Calculos criticos de deuda/detraccion/saldo real

Validaciones automatizadas:
- `tests/test_processing_calculation_parity.py::test_saldo_real_soles_pending_detraction`
- `tests/test_processing_calculation_parity.py::test_saldo_real_usd_pending_detraction_converted_by_fx`
- `tests/test_processing_calculation_parity.py::test_dt_applied_from_cobranza_overrides_detraction_and_preserves_saldo_real`

Resultado:
- PASS -> reglas de detraccion y saldo real validadas en SOLES y US$, incluyendo caso DT aplicado.

---

## 4) Comportamiento con filtros

Validacion automatizada:
- `tests/test_export_parity.py::test_export_dataframe_respects_filtered_subset`

Resultado:
- PASS -> el export conserva exactamente el subconjunto filtrado.

---

## 5) Ejecucion de pruebas

Comando:

```powershell
pytest tests/test_export_parity.py tests/test_processing_calculation_parity.py tests/test_supabase_cycle_service.py tests/test_ui_init.py -q -p no:cacheprovider
```

Resultado:
- 14 passed

---

## 6) Estado

- SUPABASE-MIG-001: cerrado tecnicamente.
- SUPABASE-MIG-002: criterios tecnicos cubiertos con evidencia automatizada.
