"""
NeonClient — Capa de compatibilidad psycopg2 que imita la API de supabase-py.

Permite cambiar toda la capa de base de datos de Supabase a Neon PostgreSQL
sin reescribir db_manager.py. Solo cambia el "plomero", no la logica de negocio.

Interfaz compatible con supabase-py:
    client = NeonClient.get_instance()
    res = client.table("clientes").select("*").eq("estado", "ACTIVO").execute()
    rows = res.data     # list[dict]
    count = res.count   # int | None
"""
from __future__ import annotations

import json
import os
import threading
from typing import Any, List, Optional

import psycopg2
import psycopg2.extras
import psycopg2.pool


# ─────────────────────────────────────────────────────────────────────────────
# Resultado compatible con supabase-py APIResponse
# ─────────────────────────────────────────────────────────────────────────────

class NeonResult:
    __slots__ = ("data", "count", "error")

    def __init__(self, data=None, count=None, error=None):
        self.data: List[dict] = data if data is not None else []
        self.count: Optional[int] = count
        self.error: Optional[str] = error


# ─────────────────────────────────────────────────────────────────────────────
# Query Builder — imita la API fluida de supabase-py
# ─────────────────────────────────────────────────────────────────────────────

class NeonQueryBuilder:
    def __init__(self, conn_factory, table: str):
        self._conn_factory = conn_factory
        self._table = table
        self._operation = "select"
        self._select_cols = "*"
        self._count_mode: Optional[str] = None
        self._filters: List[tuple] = []
        self._order_col: Optional[str] = None
        self._order_desc = False
        self._limit_n: Optional[int] = None
        self._range_start: Optional[int] = None
        self._range_end: Optional[int] = None
        self._payload = None
        self._on_conflict: Optional[str] = None

    # ── select / write operations ────────────────────────────────────────────

    def select(self, cols: str = "*", count: Optional[str] = None) -> "NeonQueryBuilder":
        self._operation = "select"
        self._select_cols = cols
        self._count_mode = count
        return self

    def insert(self, data) -> "NeonQueryBuilder":
        self._operation = "insert"
        self._payload = data
        return self

    def upsert(self, data, on_conflict: Optional[str] = None) -> "NeonQueryBuilder":
        self._operation = "upsert"
        self._payload = data
        self._on_conflict = on_conflict
        return self

    def update(self, data) -> "NeonQueryBuilder":
        self._operation = "update"
        self._payload = data
        return self

    def delete(self) -> "NeonQueryBuilder":
        self._operation = "delete"
        return self

    # ── filters ──────────────────────────────────────────────────────────────

    def eq(self, col: str, val) -> "NeonQueryBuilder":
        self._filters.append(("=", col, val))
        return self

    def neq(self, col: str, val) -> "NeonQueryBuilder":
        self._filters.append(("!=", col, val))
        return self

    def gt(self, col: str, val) -> "NeonQueryBuilder":
        self._filters.append((">", col, val))
        return self

    def gte(self, col: str, val) -> "NeonQueryBuilder":
        self._filters.append((">=", col, val))
        return self

    def lt(self, col: str, val) -> "NeonQueryBuilder":
        self._filters.append(("<", col, val))
        return self

    def lte(self, col: str, val) -> "NeonQueryBuilder":
        self._filters.append(("<=", col, val))
        return self

    def in_(self, col: str, vals: list) -> "NeonQueryBuilder":
        self._filters.append(("IN", col, vals))
        return self

    def not_(self, col: str, op: str, val) -> "NeonQueryBuilder":
        if op.lower() == "is" and val is None:
            self._filters.append(("IS NOT NULL", col, None))
        else:
            self._filters.append((f"NOT_{op.upper()}", col, val))
        return self

    def is_(self, col: str, val) -> "NeonQueryBuilder":
        if val is None:
            self._filters.append(("IS NULL", col, None))
        else:
            self._filters.append(("=", col, val))
        return self

    # ── ordering / pagination ────────────────────────────────────────────────

    def order(self, col: str, desc: bool = False) -> "NeonQueryBuilder":
        self._order_col = col
        self._order_desc = desc
        return self

    def limit(self, n: int) -> "NeonQueryBuilder":
        self._limit_n = n
        return self

    def range(self, start: int, end: int) -> "NeonQueryBuilder":
        self._range_start = start
        self._range_end = end
        return self

    # ── SQL builders ─────────────────────────────────────────────────────────

    def _build_where(self, params: list) -> str:
        clauses = []
        for op, col, val in self._filters:
            if op == "IN":
                if not val:
                    clauses.append("FALSE")
                else:
                    ph = ",".join(["%s"] * len(val))
                    clauses.append(f'"{col}" IN ({ph})')
                    params.extend(val)
            elif op == "IS NULL":
                clauses.append(f'"{col}" IS NULL')
            elif op == "IS NOT NULL":
                clauses.append(f'"{col}" IS NOT NULL')
            else:
                clauses.append(f'"{col}" {op} %s')
                params.append(val)
        return " AND ".join(clauses) if clauses else ""

    @staticmethod
    def _serialize(v: Any) -> Any:
        if isinstance(v, (dict, list)):
            return json.dumps(v, ensure_ascii=False)
        return v

    # ── execute ──────────────────────────────────────────────────────────────

    def execute(self) -> NeonResult:
        conn = self._conn_factory()
        if conn is None:
            return NeonResult(error="No database connection available")
        try:
            return self._run(conn)
        except Exception as exc:
            try:
                conn.rollback()
            except Exception:
                pass
            return NeonResult(error=str(exc))

    def _run(self, conn) -> NeonResult:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SET statement_timeout = 60000")
            tbl = f'public."{self._table}"'
            params: list = []

            if self._operation == "select":
                return self._run_select(cur, tbl, params, conn)

            if self._operation == "insert":
                return self._run_insert(cur, tbl, conn)

            if self._operation == "upsert":
                return self._run_upsert(cur, tbl, conn)

            if self._operation == "update":
                return self._run_update(cur, tbl, params, conn)

            if self._operation == "delete":
                return self._run_delete(cur, tbl, params, conn)

        return NeonResult(error=f"Unknown operation: {self._operation}")

    def _run_select(self, cur, tbl: str, params: list, conn) -> NeonResult:
        where = self._build_where(params)
        where_clause = f" WHERE {where}" if where else ""

        if self._count_mode == "exact":
            count_sql = f"SELECT COUNT(*) AS cnt FROM {tbl}{where_clause}"
            cur.execute(count_sql, params)
            row = cur.fetchone()
            return NeonResult(data=[], count=int(row["cnt"]))

        cols = self._select_cols if self._select_cols != "*" else "*"
        sql = f"SELECT {cols} FROM {tbl}{where_clause}"

        if self._order_col:
            direction = "DESC" if self._order_desc else "ASC"
            sql += f' ORDER BY "{self._order_col}" {direction}'

        if self._range_start is not None and self._range_end is not None:
            row_count = self._range_end - self._range_start + 1
            sql += f" LIMIT {row_count} OFFSET {self._range_start}"
        elif self._limit_n is not None:
            sql += f" LIMIT {self._limit_n}"

        cur.execute(sql, params)
        rows = [dict(r) for r in cur.fetchall()]
        return NeonResult(data=rows, count=len(rows))

    def _run_insert(self, cur, tbl: str, conn) -> NeonResult:
        payload = self._payload
        if isinstance(payload, dict):
            payload = [payload]
        results = []
        for row in payload:
            cols = list(row.keys())
            col_str = ", ".join(f'"{c}"' for c in cols)
            ph = ", ".join(["%s"] * len(cols))
            sql = f"INSERT INTO {tbl} ({col_str}) VALUES ({ph}) RETURNING *"
            vals = [self._serialize(row[c]) for c in cols]
            cur.execute(sql, vals)
            fetched = cur.fetchone()
            if fetched:
                results.append(dict(fetched))
        conn.commit()
        return NeonResult(data=results)

    def _run_upsert(self, cur, tbl: str, conn) -> NeonResult:
        payload = self._payload
        if isinstance(payload, dict):
            payload = [payload]
        results = []
        conflict_cols = self._on_conflict or "id"
        conflict_targets = ", ".join(f'"{c.strip()}"' for c in conflict_cols.split(","))
        for row in payload:
            cols = list(row.keys())
            col_str = ", ".join(f'"{c}"' for c in cols)
            ph = ", ".join(["%s"] * len(cols))
            update_set = ", ".join(
                f'"{c}" = EXCLUDED."{c}"'
                for c in cols
                if c not in {c.strip() for c in conflict_cols.split(",")}
            )
            if update_set:
                on_conf = f"ON CONFLICT ({conflict_targets}) DO UPDATE SET {update_set}"
            else:
                on_conf = f"ON CONFLICT ({conflict_targets}) DO NOTHING"
            sql = f"INSERT INTO {tbl} ({col_str}) VALUES ({ph}) {on_conf} RETURNING *"
            vals = [self._serialize(row[c]) for c in cols]
            cur.execute(sql, vals)
            fetched = cur.fetchone()
            if fetched:
                results.append(dict(fetched))
        conn.commit()
        return NeonResult(data=results)

    def _run_update(self, cur, tbl: str, params: list, conn) -> NeonResult:
        data = self._payload or {}
        set_parts = []
        set_vals = []
        for col, val in data.items():
            set_parts.append(f'"{col}" = %s')
            set_vals.append(self._serialize(val))
        where = self._build_where(params)
        where_clause = f" WHERE {where}" if where else ""
        sql = f"UPDATE {tbl} SET {', '.join(set_parts)}{where_clause} RETURNING *"
        cur.execute(sql, set_vals + params)
        rows = [dict(r) for r in cur.fetchall()]
        conn.commit()
        return NeonResult(data=rows)

    def _run_delete(self, cur, tbl: str, params: list, conn) -> NeonResult:
        where = self._build_where(params)
        where_clause = f" WHERE {where}" if where else ""
        if not where_clause:
            return NeonResult(error="DELETE sin WHERE rechazado por seguridad")
        sql = f"DELETE FROM {tbl}{where_clause} RETURNING id"
        cur.execute(sql, params)
        rows = [dict(r) for r in cur.fetchall()]
        conn.commit()
        return NeonResult(data=rows)


# ─────────────────────────────────────────────────────────────────────────────
# Cliente principal — Singleton thread-safe con pool de conexiones
# ─────────────────────────────────────────────────────────────────────────────

class NeonClient:
    _instance: Optional["NeonClient"] = None
    _lock = threading.Lock()

    def __init__(self, database_url: str):
        self._url = database_url
        self._pool: Optional[psycopg2.pool.ThreadedConnectionPool] = None
        self._error: Optional[str] = None
        self._connect()

    def _connect(self):
        try:
            # connect_timeout: TCP handshake limit (seconds).
            # statement_timeout: server-side query limit (ms) — prevents cold-start hangs on Neon free tier.
            # keepalives_*: OS-level TCP probes to detect dead connections without waiting forever.
            dsn = self._url
            if "connect_timeout" not in dsn:
                sep = "&" if "?" in dsn else "?"
                dsn = f"{dsn}{sep}connect_timeout=15"
            self._pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=5,
                dsn=dsn,
                options="-c search_path=public -c statement_timeout=60000",
                keepalives=1,
                keepalives_idle=30,
                keepalives_interval=5,
                keepalives_count=5,
            )
            self._error = None
        except Exception as exc:
            self._pool = None
            self._error = str(exc)

    @classmethod
    def get_instance(cls) -> Optional["NeonClient"]:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    url = os.getenv("NEON_DATABASE_URL")
                    if not url:
                        return None
                    cls._instance = cls(url)
        return cls._instance

    @classmethod
    def reset(cls) -> Optional["NeonClient"]:
        with cls._lock:
            if cls._instance and cls._instance._pool:
                try:
                    cls._instance._pool.closeall()
                except Exception:
                    pass
            cls._instance = None
        return cls.get_instance()

    def is_available(self) -> bool:
        return self._pool is not None

    def get_last_error(self) -> Optional[str]:
        return self._error

    def _get_conn(self):
        if not self._pool:
            return None
        try:
            return self._pool.getconn()
        except Exception as exc:
            self._error = str(exc)
            return None

    def _put_conn(self, conn):
        if self._pool and conn:
            try:
                self._pool.putconn(conn)
            except Exception:
                pass

    def _conn_factory(self):
        return self._get_conn()

    def table(self, table_name: str) -> NeonQueryBuilder:
        conn = self._get_conn()

        class _PooledQueryBuilder(NeonQueryBuilder):
            def execute(inner_self) -> NeonResult:
                if conn is None:
                    return NeonResult(error="No database connection available")
                try:
                    result = inner_self._run(conn)
                    return result
                except Exception as exc:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                    return NeonResult(error=str(exc))
                finally:
                    self._put_conn(conn)

        return _PooledQueryBuilder(lambda: conn, table_name)


def get_neon_client() -> Optional[NeonClient]:
    """Punto de entrada principal. Retorna el cliente Neon singleton."""
    return NeonClient.get_instance()


def is_neon_available() -> bool:
    client = NeonClient.get_instance()
    return client is not None and client.is_available()
