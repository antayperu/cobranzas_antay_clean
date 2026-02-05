"""
Supabase Client - Singleton Pattern
Sistema de Cobranzas Antay
Autor: Antay Consultoria
Fecha: 2026-02-05

CARACTERÍSTICAS:
- Singleton pattern para una única instancia del cliente
- Lazy initialization (solo se crea cuando se necesita)
- Fallback automático a session_state si Supabase no disponible
- Thread-safe para uso con Streamlit
- Logging de errores sin interrumpir la aplicación
"""

import os
from typing import Optional
from dotenv import load_dotenv
import streamlit as st

# Cargar variables de entorno
load_dotenv()

class SupabaseClient:
    """
    Cliente Singleton para Supabase.

    Uso:
        client = SupabaseClient.get_instance()
        if client.is_available():
            data = client.from_('clientes').select('*').execute()
    """

    _instance: Optional['SupabaseClient'] = None
    _client = None
    _initialized = False

    def __new__(cls):
        """Implementación del patrón Singleton."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Inicialización del cliente (solo se ejecuta una vez)."""
        if not self._initialized:
            self._initialize_client()
            SupabaseClient._initialized = True

    def _initialize_client(self):
        """Inicializa el cliente de Supabase si las credenciales están disponibles."""
        try:
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

            if not supabase_url or not supabase_key:
                print("WARNING: Supabase credentials not found. Running in LOCAL mode with session_state.")
                self._client = None
                return

            # Importación lazy de supabase
            try:
                from supabase import create_client
                self._client = create_client(supabase_url, supabase_key)
                print("SUCCESS: Supabase client initialized successfully (CLOUD mode)")
            except ImportError:
                print("WARNING: Supabase package not installed. Install with: pip install supabase==2.3.0")
                self._client = None
            except Exception as e:
                print(f"ERROR: Error initializing Supabase client: {e}")
                self._client = None

        except Exception as e:
            print(f"ERROR: Unexpected error during Supabase initialization: {e}")
            self._client = None

    @classmethod
    def get_instance(cls) -> 'SupabaseClient':
        """
        Obtiene la instancia única del cliente.

        Returns:
            SupabaseClient: Instancia singleton del cliente
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def is_available(self) -> bool:
        """
        Verifica si el cliente de Supabase está disponible.

        Returns:
            bool: True si Supabase está configurado y disponible, False en caso contrario
        """
        return self._client is not None

    def get_client(self):
        """
        Obtiene el cliente de Supabase subyacente.

        Returns:
            Supabase client o None si no está disponible
        """
        return self._client

    def table(self, table_name: str):
        """
        Acceso directo a una tabla de Supabase.

        Args:
            table_name: Nombre de la tabla

        Returns:
            Table builder de Supabase o None si no está disponible
        """
        if self._client:
            return self._client.table(table_name)
        return None

    def from_(self, table_name: str):
        """
        Alias de table() para compatibilidad.

        Args:
            table_name: Nombre de la tabla

        Returns:
            Table builder de Supabase o None si no está disponible
        """
        return self.table(table_name)

    @staticmethod
    def get_fallback_storage():
        """
        Obtiene el storage de fallback usando session_state de Streamlit.

        Returns:
            dict: Diccionario de session_state para almacenamiento local
        """
        if 'supabase_fallback' not in st.session_state:
            st.session_state.supabase_fallback = {
                'clientes': [],
                'documentos': [],
                'cobranzas': [],
                'notificaciones': []
            }
        return st.session_state.supabase_fallback

    @staticmethod
    def is_cloud_mode() -> bool:
        """
        Verifica si la aplicación está en modo Cloud (Supabase disponible).

        Returns:
            bool: True si está en modo Cloud, False si está en modo Local
        """
        instance = SupabaseClient.get_instance()
        return instance.is_available()


# ============================================
# FUNCIONES DE CONVENIENCIA (HELPER FUNCTIONS)
# ============================================

def get_supabase_client():
    """
    Función helper para obtener el cliente de Supabase.
    Compatible con el código legacy de db_manager.py

    Returns:
        Supabase client o None si no está disponible
    """
    client = SupabaseClient.get_instance()
    return client.get_client()


def is_cloud_mode() -> bool:
    """
    Función helper para verificar modo Cloud.
    Compatible con el código legacy de db_manager.py

    Returns:
        bool: True si está en modo Cloud
    """
    return SupabaseClient.is_cloud_mode()


# ============================================
# EJEMPLO DE USO
# ============================================

if __name__ == "__main__":
    # Ejemplo de uso del cliente
    client = SupabaseClient.get_instance()

    if client.is_available():
        print("✅ Supabase está disponible (CLOUD mode)")
        # Ejemplo de consulta
        # result = client.from_('clientes').select('*').limit(5).execute()
        # print(f"Clientes encontrados: {len(result.data)}")
    else:
        print("⚠️  Supabase NO disponible (LOCAL mode - usando session_state)")
        fallback = SupabaseClient.get_fallback_storage()
        print(f"Tablas en fallback: {list(fallback.keys())}")
