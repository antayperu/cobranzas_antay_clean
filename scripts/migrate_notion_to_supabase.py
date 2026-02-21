"""
Migra datos desde bases de Notion hacia tablas de Supabase.

Objetivo principal (SUPABASE-001):
- Migrar clientes -> tabla public.clientes
- Migrar documentos -> tabla public.documentos

Caracteristicas:
- Modo seguro por defecto (dry-run)
- Upsert por clave de negocio
- Mapeo flexible de propiedades de Notion (alias por nombre)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from utils.supabase_client import SupabaseClient


def chunked(items: Sequence[Dict[str, Any]], size: int) -> Iterable[Sequence[Dict[str, Any]]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def _normalize_key(value: str) -> str:
    return (
        value.strip()
        .lower()
        .replace(" ", "")
        .replace("_", "")
        .replace("-", "")
    )


def _normalize_notion_id(value: str) -> str:
    return str(value).strip().replace("-", "").lower()


def get_notion_token(explicit_token: Optional[str]) -> Optional[str]:
    if explicit_token:
        return explicit_token.strip()

    env_token = os.getenv("NOTION_TOKEN")
    if env_token:
        return env_token.strip()

    mcp_path = ROOT / ".mcp.json"
    if not mcp_path.exists():
        return None

    try:
        config = json.loads(mcp_path.read_text(encoding="utf-8"))
        raw_headers = (
            config.get("mcpServers", {})
            .get("notion", {})
            .get("env", {})
            .get("OPENAPI_MCP_HEADERS", "")
        )
        headers = json.loads(raw_headers) if raw_headers else {}
        auth = headers.get("Authorization", "")
        if auth.lower().startswith("bearer "):
            return auth[7:].strip()
    except Exception:
        return None
    return None


def get_notion_client(token: str):
    try:
        from notion_client import Client
    except ImportError as exc:
        raise RuntimeError(
            "Paquete 'notion-client' no instalado. Instala con: pip install notion-client"
        ) from exc
    return Client(auth=token)


def property_value(prop: Dict[str, Any]) -> Any:
    ptype = prop.get("type")

    if ptype == "title":
        parts = prop.get("title", [])
        return "".join(part.get("plain_text", "") for part in parts).strip()
    if ptype == "rich_text":
        parts = prop.get("rich_text", [])
        return "".join(part.get("plain_text", "") for part in parts).strip()
    if ptype == "number":
        return prop.get("number")
    if ptype == "select":
        selected = prop.get("select")
        return selected.get("name") if selected else None
    if ptype == "status":
        status = prop.get("status")
        return status.get("name") if status else None
    if ptype == "date":
        date_obj = prop.get("date")
        return date_obj.get("start") if date_obj else None
    if ptype == "email":
        return prop.get("email")
    if ptype == "phone_number":
        return prop.get("phone_number")
    if ptype == "url":
        return prop.get("url")
    if ptype == "checkbox":
        return bool(prop.get("checkbox"))
    if ptype == "formula":
        formula = prop.get("formula", {})
        ftype = formula.get("type")
        return formula.get(ftype)
    if ptype == "relation":
        rel = prop.get("relation", [])
        if not rel:
            return None
        return rel[0].get("id")
    if ptype == "people":
        people = prop.get("people", [])
        if not people:
            return None
        first = people[0]
        return first.get("name") or first.get("id")
    if ptype == "multi_select":
        items = prop.get("multi_select", [])
        return ",".join(item.get("name", "") for item in items if item.get("name"))
    return None


def pick_property(properties: Dict[str, Dict[str, Any]], aliases: Sequence[str]) -> Any:
    normalized_aliases = {_normalize_key(alias) for alias in aliases}
    for key, value in properties.items():
        if _normalize_key(key) in normalized_aliases:
            parsed = property_value(value)
            if parsed not in (None, ""):
                return parsed
    return None


def safe_float(value: Any, default: float = 0.0) -> float:
    if value in (None, ""):
        return default
    try:
        return float(str(value).replace(",", "").strip())
    except Exception:
        return default


def as_date(value: Any) -> Optional[str]:
    if value in (None, ""):
        return None
    text = str(value).strip()
    if not text:
        return None
    # Notion date usually comes in ISO-8601. For DATE column we keep YYYY-MM-DD.
    return text[:10]


def normalize_moneda(value: Any) -> str:
    text = str(value or "PEN").strip().upper()
    aliases = {
        "S/": "PEN",
        "SOLES": "PEN",
        "PEN": "PEN",
        "USD": "USD",
        "US$": "USD",
        "DOLARES": "USD",
        "DOLARES AMERICANOS": "USD",
        "EUR": "EUR",
        "EURO": "EUR",
    }
    return aliases.get(text, "PEN")


def normalize_estado_cliente(value: Any) -> str:
    text = str(value or "").strip().upper()
    mapping = {
        "ACTIVO": "ACTIVO",
        "INACTIVO": "INACTIVO",
        "MOROSO": "MOROSO",
    }
    return mapping.get(text, "ACTIVO")


def normalize_tipo_documento(value: Any) -> str:
    text = str(value or "").strip().upper()
    mapping = {
        "FACTURA": "FACTURA",
        "BOLETA": "BOLETA",
        "NOTA_CREDITO": "NOTA_CREDITO",
        "NOTA CREDITO": "NOTA_CREDITO",
        "NOTA_DEBITO": "NOTA_DEBITO",
        "NOTA DEBITO": "NOTA_DEBITO",
        "RECIBO": "RECIBO",
    }
    return mapping.get(text, "FACTURA")


def normalize_estado_documento(value: Any) -> str:
    text = str(value or "").strip().upper()
    mapping = {
        "PENDIENTE": "PENDIENTE",
        "PAGADO": "PAGADO",
        "VENCIDO": "VENCIDO",
        "CANCELADO": "CANCELADO",
    }
    return mapping.get(text, "PENDIENTE")


def resolve_data_source_id(notion_client, source_id: str) -> str:
    """
    Resuelve el ID de data_source compatible con la API nueva de Notion.

    Acepta:
    - data_source_id (actual)
    - database_id legado (mapea al primer data_source asociado)
    """
    candidate = str(source_id).strip()

    # Caso 1: ya es data_source_id
    try:
        notion_client.data_sources.retrieve(data_source_id=candidate)
        return candidate
    except Exception:
        pass

    # Caso 2: ID legado de database
    try:
        database = notion_client.databases.retrieve(database_id=candidate)
        data_sources = database.get("data_sources", []) or []
        if data_sources and data_sources[0].get("id"):
            return str(data_sources[0]["id"])
    except Exception:
        pass

    raise RuntimeError(
        f"No se pudo resolver un data_source_id para el identificador '{source_id}'."
    )


def fetch_database_pages(notion_client, data_source_id: str, page_size: int, limit: Optional[int]) -> List[Dict[str, Any]]:
    pages: List[Dict[str, Any]] = []
    cursor: Optional[str] = None

    while True:
        payload: Dict[str, Any] = {"data_source_id": data_source_id, "page_size": page_size}
        if cursor:
            payload["start_cursor"] = cursor
        response = notion_client.data_sources.query(**payload)

        batch = response.get("results", [])
        pages.extend(batch)

        if limit and len(pages) >= limit:
            return pages[:limit]

        if not response.get("has_more"):
            return pages
        cursor = response.get("next_cursor")


def map_cliente(page: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    props = page.get("properties", {})

    cliente_id = pick_property(
        props,
        ["cliente_id", "id_cliente", "codigo_cliente", "cod_cliente", "codcli", "codigo", "id"],
    )
    nombre = pick_property(props, ["nombre", "razon_social", "cliente", "name"])
    email = pick_property(props, ["email", "correo", "mail", "correo_electronico"])
    telefono = pick_property(props, ["telefono", "celular", "phone"])
    ruc = pick_property(props, ["ruc", "documento", "dni"])
    direccion = pick_property(props, ["direccion", "address"])
    estado = pick_property(props, ["estado", "status"])
    notas = pick_property(props, ["notas", "nota", "observaciones", "comentarios"])

    if not cliente_id:
        cliente_id = f"NOTION-{page.get('id', '')[:8].upper()}"

    if not nombre:
        return None, f"cliente_id={cliente_id}: campo 'nombre' no encontrado"

    record = {
        "cliente_id": str(cliente_id).strip(),
        "nombre": str(nombre).strip(),
        "email": str(email).strip() if email else None,
        "telefono": str(telefono).strip() if telefono else None,
        "ruc": str(ruc).strip() if ruc else None,
        "direccion": str(direccion).strip() if direccion else None,
        "estado": normalize_estado_cliente(estado),
        "notas": str(notas).strip() if notas else None,
    }
    return record, None


def map_documento(page: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    props = page.get("properties", {})

    documento_id = pick_property(
        props, ["documento_id", "id_documento", "codigo_documento", "document_id", "id"]
    )
    cliente_id = pick_property(props, ["cliente_id", "id_cliente", "codigo_cliente", "codcli", "cliente"])
    tipo_documento = pick_property(props, ["tipo_documento", "tipo", "tipo_doc"])
    numero_documento = pick_property(props, ["numero_documento", "numero", "nro_documento", "nro"])
    fecha_emision = pick_property(props, ["fecha_emision", "emision", "fecha"])
    fecha_vencimiento = pick_property(props, ["fecha_vencimiento", "vencimiento", "fecha_vence"])
    monto_total = pick_property(props, ["monto_total", "monto", "total", "importe_total"])
    monto_pendiente = pick_property(props, ["monto_pendiente", "saldo", "saldo_pendiente", "pendiente"])
    moneda = pick_property(props, ["moneda", "currency"])
    estado = pick_property(props, ["estado", "status"])
    descripcion = pick_property(props, ["descripcion", "detalle", "concepto"])
    archivo_url = pick_property(props, ["archivo_url", "url", "link", "adjunto"])
    notas = pick_property(props, ["notas", "nota", "observaciones"])

    if not documento_id:
        base_num = str(numero_documento).strip() if numero_documento else ""
        documento_id = base_num or f"NOTION-{page.get('id', '')[:8].upper()}"

    if not numero_documento:
        numero_documento = str(documento_id)

    fecha_emision_norm = as_date(fecha_emision)
    fecha_vencimiento_norm = as_date(fecha_vencimiento) or fecha_emision_norm

    if not cliente_id:
        return None, f"documento_id={documento_id}: campo 'cliente_id' no encontrado"
    if not fecha_emision_norm:
        return None, f"documento_id={documento_id}: campo 'fecha_emision' no encontrado"
    if not fecha_vencimiento_norm:
        return None, f"documento_id={documento_id}: campo 'fecha_vencimiento' no encontrado"

    total = safe_float(monto_total, default=0.0)
    pendiente = safe_float(monto_pendiente, default=total)

    record = {
        "documento_id": str(documento_id).strip(),
        "cliente_id": str(cliente_id).strip(),
        "tipo_documento": normalize_tipo_documento(tipo_documento),
        "numero_documento": str(numero_documento).strip(),
        "fecha_emision": fecha_emision_norm,
        "fecha_vencimiento": fecha_vencimiento_norm,
        "monto_total": total,
        "monto_pendiente": pendiente,
        "moneda": normalize_moneda(moneda),
        "estado": normalize_estado_documento(estado),
        "descripcion": str(descripcion).strip() if descripcion else None,
        "archivo_url": str(archivo_url).strip() if archivo_url else None,
        "notas": str(notas).strip() if notas else None,
    }
    return record, None


def upsert_records(supabase, table: str, rows: List[Dict[str, Any]], on_conflict: str, batch_size: int) -> int:
    inserted = 0
    for batch in chunked(rows, batch_size):
        supabase.table(table).upsert(list(batch), on_conflict=on_conflict).execute()
        inserted += len(batch)
    return inserted


def print_summary(title: str, total: int, valid: int, errors: List[str]) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)
    print(f"Total leidos: {total}")
    print(f"Validos:      {valid}")
    print(f"Con error:    {len(errors)}")
    if errors:
        print("\nPrimeros errores:")
        for err in errors[:10]:
            print(f"- {err}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Migracion Notion -> Supabase (clientes/documentos)")
    parser.add_argument("--clientes-db-id", required=True, help="Database ID de Notion para clientes")
    parser.add_argument("--documentos-db-id", help="Database ID de Notion para documentos")
    parser.add_argument(
        "--skip-documentos",
        action="store_true",
        help="Solo migra clientes (omite documentos)",
    )
    parser.add_argument(
        "--notion-token",
        help="Token de Notion. Si se omite, usa NOTION_TOKEN o .mcp.json",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=100,
        help="Tamano de pagina en query de Notion (default: 100)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=200,
        help="Tamano de lote para upsert en Supabase (default: 200)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limita la cantidad total de registros por base (para pruebas)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Ejecuta upsert real en Supabase. Sin este flag: dry-run",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dry_run = not args.apply

    token = get_notion_token(args.notion_token)
    if not token:
        print("ERROR: No se encontro token de Notion (NOTION_TOKEN o .mcp.json).")
        return 1

    try:
        notion = get_notion_client(token)
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1

    supabase_wrapper = SupabaseClient.get_instance()
    if not supabase_wrapper.is_available():
        print("ERROR: Supabase no disponible. Verifica SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY.")
        return 1
    supabase = supabase_wrapper.get_client()

    print("Modo:", "DRY-RUN" if dry_run else "APPLY")

    # ------------------------
    # Clientes
    # ------------------------
    clientes_source_id = resolve_data_source_id(notion, args.clientes_db_id)
    print("Data source clientes:", clientes_source_id)

    clientes_pages = fetch_database_pages(
        notion_client=notion,
        data_source_id=clientes_source_id,
        page_size=args.page_size,
        limit=args.limit,
    )

    clientes_rows: List[Dict[str, Any]] = []
    clientes_errors: List[str] = []
    cliente_page_to_id: Dict[str, str] = {}

    for page in clientes_pages:
        record, error = map_cliente(page)
        if error:
            clientes_errors.append(error)
            continue
        assert record is not None
        clientes_rows.append(record)
        notion_page_id = page.get("id")
        if notion_page_id:
            cliente_page_to_id[_normalize_notion_id(notion_page_id)] = record["cliente_id"]

    # Deduplicar por cliente_id (ultima version gana)
    dedup_clientes = {row["cliente_id"]: row for row in clientes_rows}
    clientes_rows = list(dedup_clientes.values())

    print_summary(
        "MIGRACION CLIENTES",
        total=len(clientes_pages),
        valid=len(clientes_rows),
        errors=clientes_errors,
    )

    if clientes_rows:
        print("\nEjemplo cliente:", clientes_rows[0])

    if not dry_run and clientes_rows:
        migrated = upsert_records(
            supabase=supabase,
            table="clientes",
            rows=clientes_rows,
            on_conflict="cliente_id",
            batch_size=args.batch_size,
        )
        print(f"Upsert clientes completado: {migrated} registros.")

    cliente_ids_validos = {row["cliente_id"] for row in clientes_rows}

    # ------------------------
    # Documentos
    # ------------------------
    if args.skip_documentos:
        print("\nDocumentos omitidos por --skip-documentos.")
        return 0

    if not args.documentos_db_id:
        print("\nNo se migro documentos: falta --documentos-db-id.")
        return 0

    documentos_source_id = resolve_data_source_id(notion, args.documentos_db_id)
    print("Data source documentos:", documentos_source_id)

    documentos_pages = fetch_database_pages(
        notion_client=notion,
        data_source_id=documentos_source_id,
        page_size=args.page_size,
        limit=args.limit,
    )

    documentos_rows: List[Dict[str, Any]] = []
    documentos_errors: List[str] = []

    for page in documentos_pages:
        record, error = map_documento(page)
        if error:
            documentos_errors.append(error)
            continue
        assert record is not None

        # Si cliente_id viene de una relation, puede ser el page_id de Notion.
        raw_cliente_id = record["cliente_id"]
        mapped_cliente_id = cliente_page_to_id.get(_normalize_notion_id(raw_cliente_id))
        if mapped_cliente_id:
            record["cliente_id"] = mapped_cliente_id

        # Evitar FK fail cuando cliente no esta en dataset de clientes.
        if record["cliente_id"] not in cliente_ids_validos:
            documentos_errors.append(
                f"documento_id={record['documento_id']}: cliente_id={record['cliente_id']} no existe en clientes"
            )
            continue
        documentos_rows.append(record)

    # Deduplicar por documento_id (ultima version gana)
    dedup_documentos = {row["documento_id"]: row for row in documentos_rows}
    documentos_rows = list(dedup_documentos.values())

    print_summary(
        "MIGRACION DOCUMENTOS",
        total=len(documentos_pages),
        valid=len(documentos_rows),
        errors=documentos_errors,
    )

    if documentos_rows:
        print("\nEjemplo documento:", documentos_rows[0])

    if not dry_run and documentos_rows:
        migrated = upsert_records(
            supabase=supabase,
            table="documentos",
            rows=documentos_rows,
            on_conflict="documento_id",
            batch_size=args.batch_size,
        )
        print(f"Upsert documentos completado: {migrated} registros.")

    print("\nProceso completado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
