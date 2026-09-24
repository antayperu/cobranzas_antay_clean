"""
MÓDULO LEGADO — Redirige a utils.db_client.

Este archivo se mantiene solo para compatibilidad con imports existentes.
Todo código nuevo debe importar desde utils.db_client.
"""

from utils.db_client import (  # noqa: F401
    DBClient,
    DBClient as SupabaseClient,
    get_db_client,
    get_db_client as get_supabase_client,
    is_db_available,
    is_db_available as is_cloud_mode,
)
