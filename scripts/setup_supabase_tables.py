"""
Script para crear tablas en Supabase
Ejecuta los scripts SQL en orden para crear la estructura de base de datos
"""

import os
import sys
from pathlib import Path

# Agregar parent directory al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.supabase_client import SupabaseClient

def execute_sql_file(client, sql_file_path):
    """Ejecuta un archivo SQL en Supabase"""
    try:
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        # Limpiar el SQL de comandos no soportados
        sql_content = sql_content.replace('\\i ', '--')  # Comentar includes

        # Dividir por statements (separados por ;)
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip() and not stmt.strip().startswith('--')]

        print(f"\nEjecutando: {os.path.basename(sql_file_path)}")
        print(f"Total statements: {len(statements)}")

        for i, statement in enumerate(statements, 1):
            # Saltar comentarios y líneas vacías
            if not statement or statement.startswith('--'):
                continue

            try:
                # Usar postgrest para ejecutar SQL directo
                result = client.get_client().rpc('exec_sql', {'query': statement}).execute()
                print(f"  [{i}/{len(statements)}] OK")
            except Exception as e:
                # Intentar con método alternativo si rpc no está disponible
                print(f"  [{i}/{len(statements)}] Metodo RPC no disponible, usando metodo alternativo...")
                # Nota: Supabase Python client no tiene método directo para ejecutar SQL arbitrario
                # El usuario necesitará ejecutar estos manualmente en el dashboard
                return False

        print(f"COMPLETADO: {os.path.basename(sql_file_path)}")
        return True

    except Exception as e:
        print(f"ERROR en {os.path.basename(sql_file_path)}: {e}")
        return False

def main():
    """Función principal"""
    print("="*60)
    print("SETUP DE TABLAS SUPABASE")
    print("="*60)

    # Obtener cliente
    client = SupabaseClient.get_instance()

    if not client.is_available():
        print("\nERROR: No se pudo conectar a Supabase")
        print("Verifica las credenciales en .env")
        return 1

    print("\nConexion a Supabase: OK")

    # Lista de archivos SQL en orden
    sql_files = [
        'sql/01_create_clientes.sql',
        'sql/02_create_documentos.sql',
        'sql/03_create_cobranzas.sql',
        'sql/04_create_notificaciones.sql'
    ]

    # Ejecutar cada archivo
    success = True
    for sql_file in sql_files:
        if not execute_sql_file(client, sql_file):
            success = False
            break

    print("\n" + "="*60)
    if success:
        print("RESULTADO: Todas las tablas fueron creadas exitosamente")
        print("="*60)
        return 0
    else:
        print("RESULTADO: Error al crear tablas")
        print("\nNOTA: El cliente Python de Supabase no soporta ejecucion directa de SQL.")
        print("ACCION REQUERIDA: Ejecutar scripts manualmente en Supabase Dashboard")
        print("\nPasos:")
        print("1. Ir a https://gnsetbdjxbtaqchdhgpi.supabase.co")
        print("2. SQL Editor > New Query")
        print("3. Copiar contenido de cada archivo .sql")
        print("4. Ejecutar en orden: 01, 02, 03, 04")
        print("="*60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
