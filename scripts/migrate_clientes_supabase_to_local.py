"""
Migra clientes desde Supabase produccion -> PostgreSQL local (QA).
Ejecutar en la PC QA:
  C:\antay-cobranza\venv_prod\Scripts\python.exe C:\antay-cobranza\scripts\migrate_clientes_supabase_to_local.py
"""
import json
import psycopg2
import requests

SUPABASE_URL = "https://<PROJECT_ID>.supabase.co"   # reemplazar con URL real
SUPABASE_KEY = "<SUPABASE_SERVICE_KEY>"              # reemplazar con clave de .env

LOCAL_DB = dict(host="localhost", port=5432, dbname="cobranzas_db",
                user="postgres", password="<LOCAL_DB_PASSWORD>")  # reemplazar

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

COLS = ["cliente_id", "nombre", "email", "telefono", "dni", "ruc",
        "direccion", "estado", "enviar_email", "notas", "extra_fields"]


def fetch_all_clientes():
    rows = []
    page_size = 1000
    offset = 0
    while True:
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/clientes",
            headers={**HEADERS, "Range": f"{offset}-{offset + page_size - 1}"},
            params={"select": ",".join(COLS), "order": "cliente_id.asc"},
            timeout=30,
        )
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        rows.extend(batch)
        print(f"  Descargados: {len(rows)} clientes...")
        if len(batch) < page_size:
            break
        offset += page_size
    return rows


def main():
    print("Descargando clientes desde Supabase produccion...")
    clientes = fetch_all_clientes()
    print(f"  Total: {len(clientes)} clientes")

    if not clientes:
        print("No se encontraron clientes en Supabase. Verifica la conexion.")
        return

    print("Insertando en PostgreSQL local...")
    conn = psycopg2.connect(**LOCAL_DB)
    conn.autocommit = False
    cur = conn.cursor()

    inserted = 0
    errors = []

    for row in clientes:
        extra = row.get("extra_fields")
        if isinstance(extra, dict):
            extra = json.dumps(extra, ensure_ascii=False)
        elif extra is None:
            extra = "{}"

        estado = row.get("estado") or "ACTIVO"
        if estado not in ("ACTIVO", "INACTIVO", "MOROSO"):
            estado = "INACTIVO"

        try:
            cur.execute(
                """
                INSERT INTO public.clientes
                    (cliente_id, nombre, email, telefono, dni, ruc, direccion,
                     estado, enviar_email, notas, extra_fields)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (cliente_id) DO UPDATE SET
                    nombre       = EXCLUDED.nombre,
                    email        = EXCLUDED.email,
                    telefono     = EXCLUDED.telefono,
                    dni          = EXCLUDED.dni,
                    ruc          = EXCLUDED.ruc,
                    direccion    = EXCLUDED.direccion,
                    estado       = EXCLUDED.estado,
                    enviar_email = EXCLUDED.enviar_email,
                    notas        = EXCLUDED.notas,
                    extra_fields = EXCLUDED.extra_fields,
                    updated_at   = now()
                """,
                (
                    row.get("cliente_id"),
                    row.get("nombre"),
                    row.get("email"),
                    row.get("telefono"),
                    row.get("dni"),
                    row.get("ruc"),
                    row.get("direccion"),
                    estado,
                    row.get("enviar_email") or "SIN CONFIGURAR",
                    row.get("notas"),
                    extra,
                ),
            )
            inserted += 1
        except Exception as exc:
            errors.append(f"  {row.get('cliente_id')}: {exc}")

    conn.commit()
    cur.close()
    conn.close()

    print(f"\nResultado:")
    print(f"  OK  Insertados/actualizados: {inserted}")
    if errors:
        print(f"  ERR Errores ({len(errors)}):")
        for e in errors:
            print(e)
    else:
        print("  Sin errores")
    print("\nListo. Reinicia la app para ver los clientes.")


if __name__ == "__main__":
    main()
