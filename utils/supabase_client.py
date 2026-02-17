"""
Supabase Client - Singleton Pattern (Cloud-Only)
Sistema de Cobranzas Antay
"""

import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


class SupabaseClient:
    """
    Cliente Singleton para Supabase en modo cloud-only.

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
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

            if not supabase_url or not supabase_key:
                self._last_error = "Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY."
                self._client = None
                return

            try:
                from supabase import create_client

                self._client = create_client(supabase_url, supabase_key)
                self._last_error = None
                print("SUCCESS: Supabase client initialized successfully.")
            except ImportError:
                self._last_error = "Supabase package not installed. Use: pip install supabase==2.3.0"
                self._client = None
            except Exception as e:
                self._last_error = f"Error initializing Supabase client: {e}"
                self._client = None

        except Exception as e:
            self._last_error = f"Unexpected error during Supabase initialization: {e}"
            self._client = None

    @classmethod
    def get_instance(cls) -> "SupabaseClient":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

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
        instance = SupabaseClient.get_instance()
        return instance.is_available()


def get_supabase_client():
    client = SupabaseClient.get_instance()
    return client.get_client()


def is_cloud_mode() -> bool:
    return SupabaseClient.is_cloud_mode()


if __name__ == "__main__":
    client = SupabaseClient.get_instance()

    if client.is_available():
        print("Supabase is available (cloud-only mode).")
    else:
        print(f"Supabase is not available: {client.get_last_error()}")
