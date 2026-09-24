"""
Database Client - Singleton Pattern (PostgreSQL local)
Sistema de Cobranzas Antay

Cliente unificado de base de datos. Usa psycopg2 via PGClient para conectar
al PostgreSQL local en la PC QA (localhost:5432, cobranzas_db).
"""

import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


class DBClient:
    """
    Cliente Singleton para la BD (PostgreSQL local).

    Uso:
        client = DBClient.get_instance()
        if client.is_available():
            data = client.from_("clientes").select("*").execute()
    """

    _instance: Optional["DBClient"] = None
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
            DBClient._initialized = True

    def _initialize_client(self):
        try:
            db_url = os.getenv("DATABASE_URL")
            if not db_url:
                self._last_error = "DATABASE_URL no configurado."
                self._client = None
                return
            try:
                from utils.pg_client import PGClient
                pg = PGClient.get_instance()
                if pg and pg.is_available():
                    self._client = pg
                    self._last_error = None
                else:
                    err = pg.get_last_error() if pg else "No se pudo conectar a la BD"
                    self._last_error = f"Error BD: {err}"
                    self._client = None
            except Exception as e:
                self._last_error = f"Error BD: {e}"
                self._client = None
        except Exception as e:
            self._last_error = f"Error inesperado al inicializar BD: {e}"
            self._client = None

    @classmethod
    def get_instance(cls) -> "DBClient":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> "DBClient":
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
    def is_db_available() -> bool:
        return bool(os.getenv("DATABASE_URL"))


# Alias de compatibilidad — mantener mientras se completa la migración
SupabaseClient = DBClient


def get_db_client():
    client = DBClient.get_instance()
    return client.get_client()


def is_db_available() -> bool:
    return DBClient.is_db_available()


# Alias de compatibilidad para código que aún use los nombres anteriores
def get_supabase_client():
    return get_db_client()


def is_cloud_mode() -> bool:
    return is_db_available()


if __name__ == "__main__":
    client = DBClient.get_instance()
    if client.is_available():
        print("Base de datos disponible.")
    else:
        print(f"Base de datos no disponible: {client.get_last_error()}")
