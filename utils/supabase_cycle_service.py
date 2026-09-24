"""
MÓDULO LEGADO — Redirige a utils.cycle_service.

Este archivo se mantiene solo para compatibilidad con imports existentes.
Todo código nuevo debe importar desde utils.cycle_service.
"""

from utils.cycle_service import (  # noqa: F401
    persist_cycle,
    persist_cycle_to_supabase,
)

# Re-exportar también las dependencias que los tests mockean directamente
from scripts.migrate_excel_to_supabase import (  # noqa: F401
    build_clientes,
    build_documentos,
    upsert_records,
)
import utils.db_manager as dbm  # noqa: F401
