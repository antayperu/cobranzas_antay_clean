"""
Script para crear tablas en Supabase usando conexión directa PostgreSQL
"""

import os
import sys
from pathlib import Path

# Agregar parent directory al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

def execute_sql_file_postgres(sql_file_path):
    """Ejecuta un archivo SQL usando psycopg2"""
    try:
        import psycopg2
        from urllib.parse import urlparse
    except ImportError:
        print("ERROR: psycopg2 no esta instalado")
        print("Instalar con: pip install psycopg2-binary")
        return False

    try:
        # Obtener URL de Supabase
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not supabase_url:
            print("ERROR: SUPABASE_URL no encontrado en .env")
            return False

        # Construir connection string para PostgreSQL
        # Supabase URL: https://PROJECT_ID.supabase.co
        # PostgreSQL: postgresql://postgres:PASSWORD@db.PROJECT_ID.supabase.co:5432/postgres

        project_id = supabase_url.replace("https://", "").replace(".supabase.co", "")

        # Nota: Necesitamos la contraseña de la base de datos, no el service role key
        print(f"\nProyecto ID: {project_id}")
        print("\nNOTA IMPORTANTE:")
        print("Para conectar directamente a PostgreSQL necesitamos:")
        print("1. Database Password (no el Service Role Key)")
        print("2. Agregarlo al .env como: SUPABASE_DB_PASSWORD=tu_password")
        print("\nLa Database Password se encuentra en:")
        print("Supabase Dashboard > Settings > Database > Connection string")
        print("\nNo se puede continuar sin la Database Password")

        return False

    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    """Función principal"""
    print("="*60)
    print("SETUP DE TABLAS SUPABASE - PostgreSQL Directo")
    print("="*60)

    # Verificar psycopg2
    try:
        import psycopg2
        print("\npsycopg2: Instalado")
    except ImportError:
        print("\nERROR: psycopg2 no esta instalado")
        print("Instalar con: pip install psycopg2-binary")
        return 1

    # Intentar ejecutar scripts
    sql_files = [
        'sql/01_create_clientes.sql',
        'sql/02_create_documentos.sql',
        'sql/03_create_cobranzas.sql',
        'sql/04_create_notificaciones.sql'
    ]

    for sql_file in sql_files:
        if not execute_sql_file_postgres(sql_file):
            break

    return 1

if __name__ == "__main__":
    sys.exit(main())
