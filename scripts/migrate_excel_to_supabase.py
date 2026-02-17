"""
Migracion de datos desde Excel hacia Supabase.

Objetivo:
- Poblar tabla `clientes` desde Cartera + CtasxCobrar
- Poblar tabla `documentos` desde CtasxCobrar
- Poblar tabla `cobranzas` desde Detalle Cobranza, vinculando a documentos del ciclo

Modo por defecto: DRY-RUN (no escribe en Supabase).
Usa --apply para ejecutar upsert real.
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd

import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from utils.supabase_client import SupabaseClient


def compute_orphan_document_ids(
    documento_ids: Sequence[str], cobranzas_documento_ids: Sequence[str]
) -> List[str]:
    """Retorna documento_id presentes en cobranzas que no existen en documentos."""
    docs = {clean_str(x) for x in documento_ids if clean_str(x)}
    cobs = {clean_str(x) for x in cobranzas_documento_ids if clean_str(x)}
    return sorted(cobs - docs)


def normalize_text(value: str) -> str:
    txt = unicodedata.normalize("NFKD", str(value or ""))
    txt = txt.encode("ascii", "ignore").decode("ascii")
    txt = txt.strip().lower()
    txt = re.sub(r"[\s_\-]+", "", txt)
    return txt


def chunked(items: Sequence[Dict[str, Any]], size: int) -> Iterable[Sequence[Dict[str, Any]]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def safe_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    text = str(value).strip()
    if text == "" or text.lower() in {"nan", "none", "nat"}:
        return default
    text = text.replace(",", "")
    try:
        return float(text)
    except Exception:
        return default


def clean_str(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in {"nan", "none", "nat"}:
        return ""
    return text


def clean_numeric_text(value: Any) -> str:
    text = clean_str(value)
    if not text:
        return ""
    try:
        num = float(text)
        if num.is_integer():
            return str(int(num))
    except Exception:
        pass
    return text


def format_client_code(value: Any) -> str:
    text = clean_str(value)
    if not text:
        return "000000"
    try:
        return str(int(float(text))).zfill(6)
    except Exception:
        return text.zfill(6)


def parse_date_yyyy_mm_dd(value: Any) -> Optional[str]:
    text = clean_str(value)
    if not text:
        return None
    try:
        dt = pd.to_datetime(text, errors="coerce")
        if pd.isna(dt):
            return None
        return dt.date().isoformat()
    except Exception:
        return None


def map_moneda(value: Any) -> str:
    text = clean_str(value).upper()
    aliases = {
        "SOL": "PEN",
        "SOLES": "PEN",
        "PEN": "PEN",
        "S/": "PEN",
        "USD": "USD",
        "US$": "USD",
        "DOLAR": "USD",
        "DOLARES": "USD",
        "EUR": "EUR",
        "EURO": "EUR",
    }
    return aliases.get(text, "PEN")


def map_tipo_documento(coddoc: Any) -> str:
    text = clean_str(coddoc).upper()
    if text.startswith("F"):
        return "FACTURA"
    if text.startswith("B"):
        return "BOLETA"
    if "NC" in text:
        return "NOTA_CREDITO"
    if "ND" in text:
        return "NOTA_DEBITO"
    if "R" in text:
        return "RECIBO"
    return "FACTURA"


def detect_estado_documento(fecha_vencimiento: Optional[str], monto_pendiente: float) -> str:
    if monto_pendiente <= 0:
        return "PAGADO"
    if not fecha_vencimiento:
        return "PENDIENTE"
    try:
        venc = date.fromisoformat(fecha_vencimiento)
        return "VENCIDO" if venc < date.today() else "PENDIENTE"
    except Exception:
        return "PENDIENTE"


def parse_timestamp(value: Any) -> Optional[str]:
    text = clean_str(value)
    if not text:
        return None
    dt = pd.to_datetime(text, errors="coerce")
    if pd.isna(dt):
        return None
    return dt.isoformat()


def normalize_doc_key(coddoc: Any, numsun: Any) -> str:
    left = clean_str(coddoc).upper()
    right = clean_str(numsun).upper()
    return re.sub(r"[^A-Z0-9]", "", left + right)


def detect_excel_file(root: Path, aliases: Sequence[str]) -> Optional[Path]:
    files = sorted(root.glob("*.xls*"))
    if not files:
        return None

    normalized_aliases = [normalize_text(a) for a in aliases]
    scored: List[Tuple[int, Path]] = []
    for path in files:
        nname = normalize_text(path.name)
        score = sum(1 for a in normalized_aliases if a and a in nname)
        if score > 0:
            scored.append((score, path))
    if not scored:
        return None
    scored.sort(key=lambda x: (-x[0], x[1].name))
    return scored[0][1]


def get_column(df: pd.DataFrame, aliases: Sequence[str]) -> Optional[str]:
    mapping = {normalize_text(col): col for col in df.columns}
    for alias in aliases:
        key = normalize_text(alias)
        if key in mapping:
            return mapping[key]
    return None


def upsert_records(supabase, table: str, rows: List[Dict[str, Any]], on_conflict: str, batch_size: int) -> int:
    total = 0
    for batch in chunked(rows, batch_size):
        supabase.table(table).upsert(list(batch), on_conflict=on_conflict).execute()
        total += len(batch)
    return total


def print_summary(title: str, rows: List[Dict[str, Any]], errors: List[str]) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)
    print(f"Registros validos: {len(rows)}")
    print(f"Errores:           {len(errors)}")
    if rows:
        print("Muestra:")
        for sample in rows[:3]:
            print(f"- {sample}")
    if errors:
        print("Primeros errores:")
        for err in errors[:10]:
            print(f"- {err}")


def collect_no_match_rows(
    df_cobranza: pd.DataFrame,
    doc_lookup: Dict[str, Dict[str, str]],
    max_rows: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Construye reporte estructurado de filas de cobranza sin match documental.
    """
    rows: List[Dict[str, Any]] = []

    c_coddoc = get_column(df_cobranza, ["coddoc", "tipo_documento"])
    c_numsun = get_column(df_cobranza, ["numsun", "nro_documento", "numero_documento"])
    c_forpag = get_column(df_cobranza, ["forpag", "tipo_aplicacion", "forma_pago"])
    c_monpag = get_column(df_cobranza, ["monpag", "monto_aplicado", "monto"])
    c_fecpro = get_column(df_cobranza, ["fecpro", "fecha", "fecha_proceso"])
    c_codcli = get_column(df_cobranza, ["codcli", "codigo_cliente"])
    c_nomcli = get_column(df_cobranza, ["nomcli", "cliente", "razsoc"])
    c_nudopa = get_column(df_cobranza, ["nudopa", "nro_operacion", "numope"])
    c_numope = get_column(df_cobranza, ["numope", "nro_operacion"])

    required = {"coddoc": c_coddoc, "numsun": c_numsun}
    missing = [name for name, col in required.items() if col is None]
    if missing:
        return [
            {
                "fila_excel": None,
                "reason": f"columnas requeridas faltantes en cobranza: {', '.join(missing)}",
            }
        ]

    for idx, row in df_cobranza.iterrows():
        coddoc = clean_str(row.get(c_coddoc))
        numsun = clean_str(row.get(c_numsun))
        lookup_key = normalize_doc_key(coddoc, numsun)
        if doc_lookup.get(lookup_key):
            continue

        rows.append(
            {
                "fila_excel": idx + 1,
                "reason": "sin_match_documento",
                "lookup_key": lookup_key,
                "coddoc": coddoc,
                "numsun": numsun,
                "codcli_excel": clean_str(row.get(c_codcli)) if c_codcli else "",
                "nomcli_excel": clean_str(row.get(c_nomcli)) if c_nomcli else "",
                "forpag": clean_str(row.get(c_forpag)) if c_forpag else "",
                "monpag": safe_float(row.get(c_monpag), default=0.0) if c_monpag else 0.0,
                "fecpro": clean_str(row.get(c_fecpro)) if c_fecpro else "",
                "nudopa": clean_str(row.get(c_nudopa)) if c_nudopa else "",
                "numope": clean_str(row.get(c_numope)) if c_numope else "",
            }
        )
        if max_rows and len(rows) >= max_rows:
            break

    return rows


def write_no_match_reports(no_match_rows: List[Dict[str, Any]], report_dir: Path) -> Dict[str, Path]:
    """
    Escribe CSV + JSON resumen de no-match y retorna rutas generadas.
    """
    report_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    csv_path = report_dir / f"cobranzas_no_match_{stamp}.csv"
    json_path = report_dir / f"cobranzas_no_match_{stamp}_summary.json"

    pd.DataFrame(no_match_rows).to_csv(csv_path, index=False, encoding="utf-8-sig")
    summary = {
        "generated_at": datetime.now().isoformat(),
        "total_no_match": len(no_match_rows),
        "sample": no_match_rows[:10],
    }
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"csv": csv_path, "json": json_path}


def fetch_column_values(
    supabase,
    table: str,
    column: str,
    page_size: int = 1000,
) -> List[str]:
    """
    Lee valores de una columna paginando por rangos para evitar truncamiento.
    """
    values: List[str] = []
    start = 0
    while True:
        end = start + page_size - 1
        res = supabase.table(table).select(column).range(start, end).execute()
        data = res.data or []
        for row in data:
            value = clean_str(row.get(column))
            if value:
                values.append(value)
        if len(data) < page_size:
            break
        start += page_size
    return values


def run_orphan_integrity_check(supabase) -> Dict[str, Any]:
    """
    Verifica integridad de FK logica: cobranzas.documento_id debe existir en documentos.documento_id.
    """
    documento_ids = fetch_column_values(supabase, table="documentos", column="documento_id")
    cobranza_documento_ids = fetch_column_values(supabase, table="cobranzas", column="documento_id")
    orphan_ids = compute_orphan_document_ids(documento_ids, cobranza_documento_ids)
    return {
        "documentos_distinct": len(set(documento_ids)),
        "cobranzas_distinct_documentos": len(set(cobranza_documento_ids)),
        "orphan_count": len(orphan_ids),
        "orphan_sample": orphan_ids[:10],
    }


def build_clientes(df_ctas: pd.DataFrame, df_cartera: pd.DataFrame) -> Tuple[List[Dict[str, Any]], List[str]]:
    errors: List[str] = []
    records: Dict[str, Dict[str, Any]] = {}

    c_cod = get_column(df_cartera, ["codigo_cliente", "codcli", "cod cliente", "codigo"])
    c_nom = get_column(
        df_cartera,
        ["nombre_cliente", "nomcli", "razon social", "razon_social", "cliente", "nombre", "empresa"],
    )
    c_email = get_column(df_cartera, ["email", "correo", "mail", "correo_electronico"])
    c_tel = get_column(df_cartera, ["telefono", "celular", "phone"])
    c_ruc = get_column(df_cartera, ["ruc"])
    c_dir = get_column(df_cartera, ["direccion", "address"])
    c_est = get_column(df_cartera, ["estado_cliente", "estado", "status"])
    c_not = get_column(df_cartera, ["nota", "notas", "observaciones"])

    if c_cod is None:
        errors.append("Cartera sin columna codigo_cliente/codcli.")
    else:
        for _, row in df_cartera.iterrows():
            cliente_id = format_client_code(row.get(c_cod))
            if cliente_id == "000000":
                continue
            estado = clean_str(row.get(c_est)).upper() if c_est else "ACTIVO"
            if estado in {"AC", "A"}:
                estado = "ACTIVO"
            elif estado in {"IN", "I"}:
                estado = "INACTIVO"
            elif estado in {"MO", "M"}:
                estado = "MOROSO"
            if estado not in {"ACTIVO", "INACTIVO", "MOROSO"}:
                estado = "ACTIVO"
            record = {
                "cliente_id": cliente_id,
                "nombre": clean_str(row.get(c_nom)) if c_nom else "",
                "email": clean_str(row.get(c_email)).lower() if c_email else None,
                "telefono": clean_numeric_text(row.get(c_tel)) if c_tel else None,
                "ruc": clean_numeric_text(row.get(c_ruc)) if c_ruc else None,
                "direccion": clean_str(row.get(c_dir)) if c_dir else None,
                "estado": estado,
                "notas": clean_str(row.get(c_not)) if c_not else None,
            }
            if not record["nombre"]:
                record["nombre"] = f"Cliente {cliente_id}"

            prev = records.get(cliente_id)
            if prev is None:
                records[cliente_id] = record
            else:
                # Completar faltantes sin destruir datos existentes.
                for key, val in record.items():
                    if (prev.get(key) in (None, "")) and (val not in (None, "")):
                        prev[key] = val

    # Fallback desde CtasxCobrar para clientes que no esten en Cartera.
    x_cod = get_column(df_ctas, ["codcli", "codigo_cliente"])
    x_nom = get_column(df_ctas, ["nomcli", "empresa", "cliente"])
    if x_cod is None:
        errors.append("CtasxCobrar sin columna codcli.")
    else:
        for _, row in df_ctas.iterrows():
            cliente_id = format_client_code(row.get(x_cod))
            if cliente_id == "000000":
                continue
            if cliente_id not in records:
                nombre = clean_str(row.get(x_nom)) if x_nom else f"Cliente {cliente_id}"
                records[cliente_id] = {
                    "cliente_id": cliente_id,
                    "nombre": nombre or f"Cliente {cliente_id}",
                    "email": None,
                    "telefono": None,
                    "ruc": None,
                    "direccion": None,
                    "estado": "ACTIVO",
                    "notas": None,
                }

    return list(records.values()), errors


def build_documentos(
    df_ctas: pd.DataFrame, valid_clientes: set[str]
) -> Tuple[List[Dict[str, Any]], List[str], Dict[str, Dict[str, str]]]:
    errors: List[str] = []
    records: Dict[str, Dict[str, Any]] = {}
    doc_lookup: Dict[str, Dict[str, str]] = {}

    c_codcli = get_column(df_ctas, ["codcli", "codigo_cliente"])
    c_coddoc = get_column(df_ctas, ["coddoc", "tipo_documento"])
    c_sersun = get_column(df_ctas, ["sersun", "serie", "serdoc"])
    c_numsun = get_column(df_ctas, ["numsun", "numero", "nrodoc"])
    c_fecdoc = get_column(df_ctas, ["fecdoc", "fecha_emision", "fecha"])
    c_fecvct = get_column(df_ctas, ["fecvct", "fecha_vencimiento", "vencimiento"])
    c_monto = get_column(df_ctas, ["mododo", "monto_total", "mondoc"])
    c_saldo = get_column(df_ctas, ["sldacl", "saldo", "monto_pendiente"])
    c_moneda = get_column(df_ctas, ["codmnd", "moneda"])

    required = {
        "codcli": c_codcli,
        "numsun": c_numsun,
        "fecdoc": c_fecdoc,
        "fecvct": c_fecvct,
    }
    missing = [name for name, col in required.items() if col is None]
    if missing:
        errors.append(f"CtasxCobrar sin columnas requeridas: {', '.join(missing)}")
        return [], errors, {}

    for idx, row in df_ctas.iterrows():
        cliente_id = format_client_code(row.get(c_codcli))
        if cliente_id not in valid_clientes:
            errors.append(f"fila {idx + 1}: cliente_id {cliente_id} no existe en clientes")
            continue

        coddoc = clean_str(row.get(c_coddoc)) if c_coddoc else ""
        sersun = clean_str(row.get(c_sersun)) if c_sersun else ""
        numsun_raw = clean_str(row.get(c_numsun))
        try:
            numsun = str(int(float(numsun_raw))).zfill(8)
        except Exception:
            numsun = numsun_raw.zfill(8) if numsun_raw.isdigit() else numsun_raw

        numero_documento = f"{sersun}-{numsun}" if sersun else numsun
        base_id = "-".join([p for p in [cliente_id, coddoc or "DOC", sersun, numsun] if p])
        documento_id = re.sub(r"[^A-Za-z0-9_\-]", "", base_id)[:120]

        fecha_emision = parse_date_yyyy_mm_dd(row.get(c_fecdoc))
        fecha_venc = parse_date_yyyy_mm_dd(row.get(c_fecvct))
        if not fecha_emision or not fecha_venc:
            errors.append(f"fila {idx + 1}: fechas invalidas para documento {documento_id}")
            continue

        monto_total = safe_float(row.get(c_monto), default=0.0) if c_monto else 0.0
        monto_pendiente = safe_float(row.get(c_saldo), default=monto_total) if c_saldo else monto_total
        moneda = map_moneda(row.get(c_moneda)) if c_moneda else "PEN"
        estado = detect_estado_documento(fecha_venc, monto_pendiente)

        record = {
            "documento_id": documento_id or f"{cliente_id}-DOC-{idx + 1}",
            "cliente_id": cliente_id,
            "tipo_documento": map_tipo_documento(coddoc),
            "numero_documento": numero_documento or f"{idx + 1}",
            "fecha_emision": fecha_emision,
            "fecha_vencimiento": fecha_venc,
            "monto_total": round(monto_total, 2),
            "monto_pendiente": round(monto_pendiente, 2),
            "moneda": moneda,
            "estado": estado,
            "descripcion": f"Origen Excel coddoc={coddoc}" if coddoc else "Origen Excel",
            "archivo_url": None,
            "notas": None,
        }
        records[record["documento_id"]] = record
        doc_key = normalize_doc_key(coddoc, numero_documento)
        if doc_key and doc_key not in doc_lookup:
            doc_lookup[doc_key] = {
                "documento_id": record["documento_id"],
                "cliente_id": record["cliente_id"],
            }

    return list(records.values()), errors, doc_lookup


def map_tipo_gestion(forpag: str) -> str:
    # El origen es cobranza financiera (no canal de mensajeria), se guarda como gestion documental.
    if forpag in {"DT", "DET"}:
        return "CARTA"
    return "CARTA"


def map_estado_gestion(monpag: float) -> str:
    return "RESPONDIDO" if monpag > 0 else "FALLIDO"


def build_cobranzas(
    df_cobranza: pd.DataFrame, doc_lookup: Dict[str, Dict[str, str]]
) -> Tuple[List[Dict[str, Any]], List[str]]:
    errors: List[str] = []
    records: List[Dict[str, Any]] = []

    c_coddoc = get_column(df_cobranza, ["coddoc", "tipo_documento"])
    c_numsun = get_column(df_cobranza, ["numsun", "nro_documento", "numero_documento"])
    c_forpag = get_column(df_cobranza, ["forpag", "tipo_aplicacion", "forma_pago"])
    c_fecpro = get_column(df_cobranza, ["fecpro", "fecha", "fecha_proceso"])
    c_fecemi = get_column(df_cobranza, ["fecemi", "fecha_emision"])
    c_monpag = get_column(df_cobranza, ["monpag", "monto_aplicado", "monto"])
    c_nudopa = get_column(df_cobranza, ["nudopa", "nro_operacion", "numope"])
    c_numope = get_column(df_cobranza, ["numope", "nro_operacion"])
    c_nombco = get_column(df_cobranza, ["nombco", "banco"])
    c_codbco = get_column(df_cobranza, ["codbco", "codigo_banco"])
    c_codven = get_column(df_cobranza, ["codven", "vendedor"])
    c_codcli = get_column(df_cobranza, ["codcli", "codigo_cliente"])
    c_nomcli = get_column(df_cobranza, ["nomcli", "cliente", "razsoc"])

    required = {"coddoc": c_coddoc, "numsun": c_numsun}
    missing = [name for name, col in required.items() if col is None]
    if missing:
        errors.append(f"Cobranza sin columnas requeridas: {', '.join(missing)}")
        return [], errors

    for idx, row in df_cobranza.iterrows():
        coddoc = clean_str(row.get(c_coddoc))
        numsun = clean_str(row.get(c_numsun))
        lookup_key = normalize_doc_key(coddoc, numsun)
        linked = doc_lookup.get(lookup_key)

        if not linked:
            # Solo mostramos algunos para no saturar salida.
            if len(errors) < 200:
                errors.append(
                    f"fila {idx + 1}: sin match de documento para key={lookup_key} (coddoc={coddoc}, numsun={numsun})"
                )
            continue

        monpag = safe_float(row.get(c_monpag), default=0.0) if c_monpag else 0.0
        forpag = clean_str(row.get(c_forpag)).upper() if c_forpag else ""
        fecha_gestion = parse_timestamp(row.get(c_fecpro)) if c_fecpro else None
        if not fecha_gestion and c_fecemi:
            fecha_gestion = parse_timestamp(row.get(c_fecemi))
        if not fecha_gestion:
            fecha_gestion = date.today().isoformat()

        nudopa = clean_str(row.get(c_nudopa)) if c_nudopa else ""
        numope = clean_str(row.get(c_numope)) if c_numope else ""
        op_ref = nudopa or numope or f"row{idx + 1}"
        unique_seed = f"{linked['documento_id']}|{fecha_gestion}|{forpag}|{op_ref}|{monpag:.2f}"
        stable_id = str(uuid.uuid5(uuid.NAMESPACE_URL, unique_seed))

        banco = clean_str(row.get(c_nombco)) if c_nombco else ""
        codbco = clean_str(row.get(c_codbco)) if c_codbco else ""
        codcli = clean_str(row.get(c_codcli)) if c_codcli else ""
        nomcli = clean_str(row.get(c_nomcli)) if c_nomcli else ""
        responsable = clean_numeric_text(row.get(c_codven)) if c_codven else None

        record = {
            "id": stable_id,
            "documento_id": linked["documento_id"],
            "cliente_id": linked["cliente_id"],
            "tipo_gestion": map_tipo_gestion(forpag),
            "estado_gestion": map_estado_gestion(monpag),
            "fecha_gestion": fecha_gestion,
            "responsable": responsable,
            "monto_gestionado": round(monpag, 2),
            "resultado": f"Aplicacion {forpag or 'N/A'}",
            "notas": f"Banco {banco} ({codbco}) - Operacion {op_ref}",
            "metadata": {
                "source": "excel_cobranza",
                "forpag": forpag,
                "nudopa": nudopa,
                "numope": numope,
                "coddoc": coddoc,
                "numsun": numsun,
                "codcli_excel": codcli,
                "nomcli_excel": nomcli,
            },
        }
        records.append(record)

    return records, errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Migracion Excel -> Supabase (clientes/documentos/cobranzas)")
    parser.add_argument("--ctas-file", help="Ruta Excel CtasxCobrar")
    parser.add_argument("--cartera-file", help="Ruta Excel Cartera")
    parser.add_argument("--cobranza-file", help="Ruta Excel Detalle Cobranza")
    parser.add_argument("--root", default=".", help="Directorio para auto-detectar Excels (default: .)")
    parser.add_argument("--batch-size", type=int, default=200, help="Tamano de lote para upsert")
    parser.add_argument("--apply", action="store_true", help="Aplica cambios en Supabase")
    parser.add_argument(
        "--report-dir",
        default="reports",
        help="Directorio de salida para reportes operativos (no-match).",
    )
    parser.add_argument(
        "--no-match-max",
        type=int,
        default=0,
        help="Maximo de filas no-match a reportar (0 = todas).",
    )
    parser.add_argument(
        "--integrity-check",
        action="store_true",
        help="Ejecuta chequeo de huerfanos en Supabase al final.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dry_run = not args.apply

    root = Path(args.root).resolve()
    ctas_file = Path(args.ctas_file).resolve() if args.ctas_file else detect_excel_file(
        root, ["ctas", "cuentas", "cobrar"]
    )
    cartera_file = Path(args.cartera_file).resolve() if args.cartera_file else detect_excel_file(
        root, ["cartera", "clientes"]
    )
    cobranza_file = Path(args.cobranza_file).resolve() if args.cobranza_file else detect_excel_file(
        root, ["cobranza"]
    )

    print("Modo:", "DRY-RUN" if dry_run else "APPLY")
    print("Root:", root)
    print("Archivo CtasxCobrar:", ctas_file if ctas_file else "NO ENCONTRADO")
    print("Archivo Cartera:", cartera_file if cartera_file else "NO ENCONTRADO")
    print("Archivo Cobranza:", cobranza_file if cobranza_file else "NO ENCONTRADO (opcional)")

    missing = []
    if not ctas_file or not ctas_file.exists():
        missing.append("CtasxCobrar")
    if not cartera_file or not cartera_file.exists():
        missing.append("Cartera")
    if not cobranza_file or not cobranza_file.exists():
        missing.append("Cobranza")
    if missing:
        print(f"ERROR: Faltan archivos requeridos: {', '.join(missing)}")
        print("Coloca los Excel en la raiz o pasa rutas con --ctas-file --cartera-file --cobranza-file.")
        return 1

    try:
        df_ctas = pd.read_excel(ctas_file)
        df_cartera = pd.read_excel(cartera_file)
        df_cobranza = pd.read_excel(cobranza_file)
    except Exception as exc:
        print(f"ERROR leyendo Excels: {exc}")
        return 1

    clientes_rows, clientes_errors = build_clientes(df_ctas, df_cartera)
    valid_clientes = {row["cliente_id"] for row in clientes_rows}
    documentos_rows, documentos_errors, doc_lookup = build_documentos(df_ctas, valid_clientes)
    cobranzas_rows, cobranzas_errors = build_cobranzas(df_cobranza, doc_lookup)
    no_match_limit = args.no_match_max if args.no_match_max > 0 else None
    no_match_rows = collect_no_match_rows(df_cobranza, doc_lookup, max_rows=no_match_limit)

    print_summary("MIGRACION CLIENTES", clientes_rows, clientes_errors)
    print_summary("MIGRACION DOCUMENTOS", documentos_rows, documentos_errors)
    print_summary("MIGRACION COBRANZAS", cobranzas_rows, cobranzas_errors)
    print(f"\nNo-match detectados (cobranza sin documento asociado): {len(no_match_rows)}")
    if no_match_rows:
        report_paths = write_no_match_reports(no_match_rows, Path(args.report_dir))
        print(f"Reporte no-match CSV: {report_paths['csv']}")
        print(f"Resumen no-match JSON: {report_paths['json']}")

    if dry_run and not args.integrity_check:
        print("\nDry-run completado. No se escribio nada en Supabase.")
        return 0

    supabase_wrapper = SupabaseClient.get_instance()
    if not supabase_wrapper.is_available():
        print("ERROR: Supabase no disponible. Verifica SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY.")
        return 1
    supabase = supabase_wrapper.get_client()

    if not dry_run:
        try:
            count_clientes = upsert_records(
                supabase=supabase,
                table="clientes",
                rows=clientes_rows,
                on_conflict="cliente_id",
                batch_size=args.batch_size,
            )
            print(f"Upsert clientes: {count_clientes}")

            count_documentos = upsert_records(
                supabase=supabase,
                table="documentos",
                rows=documentos_rows,
                on_conflict="documento_id",
                batch_size=args.batch_size,
            )
            print(f"Upsert documentos: {count_documentos}")

            count_cobranzas = upsert_records(
                supabase=supabase,
                table="cobranzas",
                rows=cobranzas_rows,
                on_conflict="id",
                batch_size=args.batch_size,
            )
            print(f"Upsert cobranzas: {count_cobranzas}")

        except Exception as exc:
            print(f"ERROR durante upsert en Supabase: {exc}")
            return 1

    if args.integrity_check:
        try:
            integrity = run_orphan_integrity_check(supabase)
            print("\nINTEGRITY CHECK (cobranzas vs documentos)")
            print(f"- documentos distinct: {integrity['documentos_distinct']}")
            print(f"- cobranzas distinct documento_id: {integrity['cobranzas_distinct_documentos']}")
            print(f"- orphan_count: {integrity['orphan_count']}")
            if integrity["orphan_sample"]:
                print(f"- orphan_sample: {integrity['orphan_sample']}")
            if integrity["orphan_count"] > 0:
                print("ERROR: Se detectaron cobranzas huerfanas. Revisar integridad antes de cerrar migracion.")
                return 2
            print("OK: integridad validada, sin huerfanos.")
        except Exception as exc:
            print(f"ERROR durante integrity-check: {exc}")
            return 1

    if dry_run:
        print("\nDry-run completado. No se escribio nada en Supabase.")
        return 0

    print("\nMigracion aplicada exitosamente.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
