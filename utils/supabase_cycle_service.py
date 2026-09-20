"""
Servicios de persistencia de ciclo (Excel -> BD local) para ejecución desde UI.
"""

from __future__ import annotations

from typing import Any, Dict

import pandas as pd

from scripts.migrate_excel_to_supabase import (
    build_clientes,
    build_documentos,
    upsert_records,
)
import utils.db_manager as dbm


def persist_cycle_to_supabase(
    df_ctas: pd.DataFrame,
    df_cartera: pd.DataFrame,
    df_cobranza: pd.DataFrame,
    batch_size: int = 10,
) -> Dict[str, Any]:
    """
    Persiste el ciclo completo en Supabase.

    Returns:
        dict con:
        - ok: bool
        - message: str
        - counts: dict
        - errors: dict
        - error_samples: dict
    """
    try:
        clientes_rows, clientes_errors = build_clientes(df_ctas, df_cartera)
        valid_clientes = {row["cliente_id"] for row in clientes_rows}

        documentos_result = build_documentos(df_ctas, valid_clientes)
        if len(documentos_result) == 3:
            documentos_rows, documentos_errors, _doc_lookup = documentos_result
        elif len(documentos_result) == 2:
            # Compatibilidad defensiva si el helper retorna solo filas+errores.
            documentos_rows, documentos_errors = documentos_result
        else:
            raise ValueError("Formato invalido de salida en build_documentos.")

    except Exception as exc:
        return {
            "ok": False,
            "message": f"Error preparando datos para persistencia: {exc}",
            "counts": {},
            "errors": {},
            "error_samples": {},
        }

    if not clientes_rows:
        return {
            "ok": False,
            "message": "No se generaron registros validos para clientes.",
            "counts": {},
            "errors": {
                "clientes": len(clientes_errors),
                "documentos": len(documentos_errors),
            },
            "error_samples": {
                "clientes": clientes_errors[:10],
                "documentos": documentos_errors[:10],
            },
        }

    if not documentos_rows:
        return {
            "ok": False,
            "message": "No se generaron registros validos para documentos.",
            "counts": {},
            "errors": {
                "clientes": len(clientes_errors),
                "documentos": len(documentos_errors),
            },
            "error_samples": {
                "clientes": clientes_errors[:10],
                "documentos": documentos_errors[:10],
            },
        }

    # Verificar disponibilidad de la base de datos local
    client = dbm.get_supabase_client()
    if not client:
        return {
            "ok": False,
            "message": "Base de datos no disponible. Verifica la conexión.",
            "counts": {},
            "errors": {
                "clientes": len(clientes_errors),
                "documentos": len(documentos_errors),
            },
            "error_samples": {
                "clientes": clientes_errors[:10],
                "documentos": documentos_errors[:10],
            },
        }

    try:
        ok_clientes, msg_clientes = dbm.upsert_clientes_rows(clientes_rows, batch_size=batch_size)

        if not ok_clientes:
            return {
                "ok": False,
                "message": f"Error al guardar clientes: {msg_clientes}",
                "counts": {},
                "errors": {
                    "clientes": len(clientes_errors),
                    "documentos": len(documentos_errors),
                },
                "error_samples": {
                    "clientes": clientes_errors[:10],
                    "documentos": documentos_errors[:10],
                },
            }

        count_clientes = len(clientes_rows)
        # Intento best-effort de guardar en tabla legacy documentos
        # (la tabla documentos_ciclo es el almacén principal — este es secundario)
        try:
            count_documentos = upsert_records(
                supabase=client,
                table="documentos",
                rows=documentos_rows,
                on_conflict="documento_id",
                batch_size=batch_size,
            )
        except Exception:
            count_documentos = 0
    except Exception as exc:
        return {
            "ok": False,
            "message": f"Error durante persistencia: {exc}",
            "counts": {},
            "errors": {
                "clientes": len(clientes_errors),
                "documentos": len(documentos_errors),
            },
            "error_samples": {
                "clientes": clientes_errors[:10],
                "documentos": documentos_errors[:10],
            },
        }

    return {
        "ok": True,
        "message": "Persistencia de ciclo completada en Supabase.",
        "counts": {
            "clientes": count_clientes,
            "documentos": count_documentos,
        },
        "errors": {
            "clientes": len(clientes_errors),
            "documentos": len(documentos_errors),
        },
        "error_samples": {
            "clientes": clientes_errors[:10],
            "documentos": documentos_errors[:10],
        },
    }
