"""
Script de importación: cartera_clientes29122025 - testing.xlsx → PostgreSQL local.
Uso: python scripts/import_clientes_from_excel.py
"""
import json
import os
import sys

import pandas as pd
import psycopg2
import psycopg2.extras

EXCEL_PATH = r"\\QA\antay-cobranza\cartera_clientes29122025 - testing.xlsx"
DB_URL = "postgresql://postgres:AntayPeru%2A2026@localhost:5432/cobranzas_db"

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
    print(f"Leyendo {EXCEL_PATH} ...")
    df = pd.read_excel(EXCEL_PATH)
    print(f"  -> {len(df)} filas encontradas")

    print("Conectando a PostgreSQL local ...")
    conn = psycopg2.connect(DB_URL)
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
            if not pd.isna(v) if not isinstance(v, float) else v == v:
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
    print(f"  OK Insertados/actualizados: {inserted}")
    print(f"  -- Omitidos (sin nombre):  {skipped}")
    if errors:
        print(f"  ❌ Errores ({len(errors)}):")
        for e in errors:
            print(e)
    else:
        print(f"  Sin errores")


if __name__ == "__main__":
    main()
