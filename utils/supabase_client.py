"""
Database Client - Singleton Pattern (PostgreSQL local / Cloud-Only)
Sistema de Cobranzas Antay

Cliente unificado de base de datos. Usa psycopg2 via NeonClient para conectar
al PostgreSQL local en la PC QA.
"""

import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


class SupabaseClient:
    """
    Cliente Singleton para la BD (Neon PostgreSQL en modo cloud-only).
    Mantiene la interfaz original de SupabaseClient para compatibilidad.

    Uso:
        client = SupabaseClient.get_instance()
        if client.is_available():
            data = client.from_("clientes").select("*").execute()
    """

    _instance: Optional["SupabaseClient"] = None
    _client = None
    _initialized = False
    _last_error: Optional[str] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._initialize_client()
            SupabaseClient._initialized = True

    def _initialize_client(self):
        try:
            neon_url = os.getenv("NEON_DATABASE_URL")
            if not neon_url:
                self._last_error = "NEON_DATABASE_URL no configurado."
                self._client = None
                return
            try:
                from utils.neon_client import NeonClient
                neon = NeonClient.get_instance()
                if neon and neon.is_available():
                    self._client = neon
                    self._last_error = None
                else:
                    err = neon.get_last_error() if neon else "No se pudo conectar a la BD"
                    self._last_error = f"Error BD: {err}"
                    self._client = None
            except Exception as e:
                self._last_error = f"Error BD: {e}"
                self._client = None
        except Exception as e:
            self._last_error = f"Error inesperado al inicializar BD: {e}"
            self._client = None

    @classmethod
    def get_instance(cls) -> "SupabaseClient":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> "SupabaseClient":
        """Reinicializa el cliente de BD sin cerrar el pool compartido."""
        cls._instance = None
        cls._initialized = False
        cls._client = None
        cls._last_error = None
        return cls.get_instance()

    def is_available(self) -> bool:
        return self._client is not None

    def get_last_error(self) -> Optional[str]:
        return self._last_error

    def get_client(self):
        return self._client

    def table(self, table_name: str):
        if self._client:
            return self._client.table(table_name)
        return None

    def from_(self, table_name: str):
        return self.table(table_name)

    @staticmethod
    def is_cloud_mode() -> bool:
        return bool(os.getenv("NEON_DATABASE_URL"))


def get_supabase_client():
    client = SupabaseClient.get_instance()
    return client.get_client()


def is_cloud_mode() -> bool:
    return SupabaseClient.is_cloud_mode()


if __name__ == "__main__":
    client = SupabaseClient.get_instance()
    if client.is_available():
        print("Database client available (Neon/cloud mode).")
    else:
        print(f"Database client not available: {client.get_last_error()}")
