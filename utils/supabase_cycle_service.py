"""
Servicios de persistencia de ciclo (3 Excel -> Supabase) para ejecución desde UI.
"""

from __future__ import annotations

from typing import Any, Dict

import pandas as pd

from scripts.migrate_excel_to_supabase import (
    build_clientes,
    build_cobranzas,
    build_documentos,
    upsert_records,
)
import utils.db_manager as dbm
from utils.supabase_client import SupabaseClient


def persist_cycle_to_supabase(
    df_ctas: pd.DataFrame,
    df_cartera: pd.DataFrame,
    df_cobranza: pd.DataFrame,
    batch_size: int = 50,
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
            documentos_rows, documentos_errors, doc_lookup = documentos_result
        elif len(documentos_result) == 2:
            # Compatibilidad defensiva si el helper retorna solo filas+errores.
            documentos_rows, documentos_errors = documentos_result
            doc_lookup = {}
        else:
            raise ValueError("Formato invalido de salida en build_documentos.")

        cobranzas_rows, cobranzas_errors = build_cobranzas(df_cobranza, doc_lookup)
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
                "cobranzas": len(cobranzas_errors),
            },
            "error_samples": {
                "clientes": clientes_errors[:10],
                "documentos": documentos_errors[:10],
                "cobranzas": cobranzas_errors[:10],
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
                "cobranzas": len(cobranzas_errors),
            },
            "error_samples": {
                "clientes": clientes_errors[:10],
                "documentos": documentos_errors[:10],
                "cobranzas": cobranzas_errors[:10],
            },
        }

    wrapper = SupabaseClient.get_instance()
    if not wrapper.is_available():
        return {
            "ok": False,
            "message": "Supabase no disponible. Verifica credenciales y conectividad.",
            "counts": {},
            "errors": {
                "clientes": len(clientes_errors),
                "documentos": len(documentos_errors),
                "cobranzas": len(cobranzas_errors),
            },
            "error_samples": {
                "clientes": clientes_errors[:10],
                "documentos": documentos_errors[:10],
                "cobranzas": cobranzas_errors[:10],
            },
        }

    supabase = wrapper.get_client()
    try:
        ok_clientes, msg_clientes = dbm.upsert_clientes_rows(clientes_rows, batch_size=batch_size)
        if not ok_clientes:
            return {
                "ok": False,
                "message": f"Error durante persistencia en Supabase: {msg_clientes}",
                "counts": {},
                "errors": {
                    "clientes": len(clientes_errors),
                    "documentos": len(documentos_errors),
                    "cobranzas": len(cobranzas_errors),
                },
                "error_samples": {
                    "clientes": clientes_errors[:10],
                    "documentos": documentos_errors[:10],
                    "cobranzas": cobranzas_errors[:10],
                },
            }

        count_clientes = len(clientes_rows)
        count_documentos = upsert_records(
            supabase=supabase,
            table="documentos",
            rows=documentos_rows,
            on_conflict="documento_id",
            batch_size=batch_size,
        )
        count_cobranzas = upsert_records(
            supabase=supabase,
            table="cobranzas",
            rows=cobranzas_rows,
            on_conflict="id",
            batch_size=batch_size,
        )
    except Exception as exc:
        return {
            "ok": False,
            "message": f"Error durante persistencia en Supabase: {exc}",
            "counts": {},
            "errors": {
                "clientes": len(clientes_errors),
                "documentos": len(documentos_errors),
                "cobranzas": len(cobranzas_errors),
            },
            "error_samples": {
                "clientes": clientes_errors[:10],
                "documentos": documentos_errors[:10],
                "cobranzas": cobranzas_errors[:10],
            },
        }

    return {
        "ok": True,
        "message": "Persistencia de ciclo completada en Supabase.",
        "counts": {
            "clientes": count_clientes,
            "documentos": count_documentos,
            "cobranzas": count_cobranzas,
        },
        "errors": {
            "clientes": len(clientes_errors),
            "documentos": len(documentos_errors),
            "cobranzas": len(cobranzas_errors),
        },
        "error_samples": {
            "clientes": clientes_errors[:10],
            "documentos": documentos_errors[:10],
            "cobranzas": cobranzas_errors[:10],
        },
    }
