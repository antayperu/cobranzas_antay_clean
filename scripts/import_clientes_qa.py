"""
Script de importacion: cartera_clientes29122025 - testing.xlsx -> PostgreSQL local QA.
Ejecutar en la PC QA: python C:\antay-cobranza\scripts\import_clientes_qa.py
"""
import json
import sys

import pandas as pd
import psycopg2

EXCEL_PATH = r"C:\antay-cobranza\cartera_cliente_oficial.xlsx"

ESTADO_MAP = {"AC": "ACTIVO", "IN": "INACTIVO", "SR": "INACTIVO", "MO": "MOROSO"}

EXTRA_COLS = [
    "empresa", "division", "oficina", "unicas", "domicilio", "codigo_anterior",
    "flag_deuda", "limite_credito", "secuencia_visita", "estado_domicilio",
    "ubigeo", "codigo_pais", "pais", "codigo_departamento", "departamento",
    "codigo_provincia", "provincia", "localidad", "codigo_condicion_venta",
    "condicion_venta", "canal", "tipo_negocio", "zona", "ruta", "fuerza",
    "mesa", "vendedor", "dia_visita", "frecuencia_visita", "giro", "tipo_local",
    "frecuencia_venta", "Categoria", "Codigo_localidad", "Latitud", "Longitud",
    "Codigo_frecuencia", "categoria_cliente",
]


def clean(val):
    if pd.isna(val):
        return None
    if isinstance(val, float) and val == int(val):
        return str(int(val))
    return str(val).strip() or None


def main():
    print("Leyendo Excel ...")
    df = pd.read_excel(EXCEL_PATH)
    print(f"  -> {len(df)} filas encontradas")

    print("Conectando a PostgreSQL local ...")
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        dbname="cobranzas_db",
        user="postgres",
        password="AntayPeru*2026",
    )
    conn.autocommit = False
    cur = conn.cursor()

    inserted = 0
    skipped = 0
    errors = []

    for _, row in df.iterrows():
        cliente_id = str(int(row["codigo_cliente"])).zfill(6)
        nombre = clean(row.get("nombre_cliente"))
        if not nombre:
            skipped += 1
            continue

        email = clean(row.get("correo"))
        telefono = clean(row.get("telefono"))
        ruc = clean(row.get("ruc"))
        dni = clean(row.get("dni"))
        direccion = clean(row.get("direccion"))
        enviar_email = str(row.get("Enviar Email", "SIN CONFIGURAR")).strip().upper()
        if enviar_email not in ("SI", "NO"):
            enviar_email = "SIN CONFIGURAR"
        notas = clean(row.get("nota"))
        estado_raw = str(row.get("estado_cliente", "AC")).strip().upper()
        estado = ESTADO_MAP.get(estado_raw, "INACTIVO")

        extra = {}
        for col in EXTRA_COLS:
            v = row.get(col)
            try:
                if not pd.isna(v):
                    extra[col] = clean(v)
            except Exception:
                extra[col] = clean(v)

        try:
            cur.execute(
                """
                INSERT INTO public.clientes
                    (cliente_id, nombre, email, dni, telefono, ruc, direccion,
                     enviar_email, estado, notas, extra_fields)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (cliente_id) DO UPDATE SET
                    nombre       = EXCLUDED.nombre,
                    email        = EXCLUDED.email,
                    telefono     = EXCLUDED.telefono,
                    ruc          = EXCLUDED.ruc,
                    direccion    = EXCLUDED.direccion,
                    enviar_email = EXCLUDED.enviar_email,
                    estado       = EXCLUDED.estado,
                    notas        = EXCLUDED.notas,
                    extra_fields = EXCLUDED.extra_fields,
                    updated_at   = now()
                """,
                (
                    cliente_id, nombre, email, dni, telefono, ruc, direccion,
                    enviar_email, estado, notas,
                    json.dumps(extra, ensure_ascii=False),
                ),
            )
            inserted += 1
        except Exception as exc:
            errors.append(f"  cliente_id={cliente_id}: {exc}")

    conn.commit()
    cur.close()
    conn.close()

    print(f"\nResultado:")
    print(f"  OK  Insertados/actualizados: {inserted}")
    print(f"  --  Omitidos (sin nombre):   {skipped}")
    if errors:
        print(f"  ERR Errores ({len(errors)}):")
        for e in errors:
            print(e)
    else:
        print("  Sin errores")


if __name__ == "__main__":
    main()
