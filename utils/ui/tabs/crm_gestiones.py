"""
Centro de Gestiones (CRM) — Tab Module
Unified view for notification history, manual interactions, and client drill-down.
"""

import io
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st

import utils.db_manager as dbm
import utils.ui.styles as styles


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TIPOS_GESTION = ["EMAIL", "WHATSAPP", "LLAMADA", "VISITA", "NOTA", "OTRO"]
TIPOS_GESTION_MANUAL = ["LLAMADA", "VISITA", "NOTA", "OTRO"]

TIPO_ICONS = {
    "EMAIL": "📧",
    "WHATSAPP": "💬",
    "LLAMADA": "📞",
    "VISITA": "🏢",
    "NOTA": "📝",
    "OTRO": "📌",
}


def _build_resultado_maps():
    """Construye los mapas de resultados desde el catálogo de BD (con caché de Supabase)."""
    catalogo = dbm.get_catalogo_resultados(include_legado=True)
    codigos = [r["codigo"] for r in catalogo]
    labels = {r["codigo"]: f"{r['icono']} {r['etiqueta']}" for r in catalogo}
    colors = {r["codigo"]: r["color_scheme"] for r in catalogo}
    return codigos, labels, colors


def _get_resultados_activos():
    """Lista de códigos de resultados activos (no legado) para nuevas gestiones."""
    return [r["codigo"] for r in dbm.get_catalogo_resultados(include_legado=False)]


# ---------------------------------------------------------------------------
# Main render
# ---------------------------------------------------------------------------

def render_tab(df_final: pd.DataFrame, config: dict):
    # ── Header ──────────────────────────────────────────────────────────
    st.markdown(
        """
        <div style="display:flex; align-items:center; gap:12px; margin-bottom:4px;">
            <h2 style="margin:0; font-weight:780; color:#0D3B66;">Centro de Gestiones</h2>
            <span class="antay-pill" style="background:rgba(11,114,133,0.12); color:#0B7285; border-color:#8ec5ce;">
                CRM
            </span>
        </div>
        <p style="color:#486581; font-size:0.88rem; margin-top:0;">
            Historial completo de notificaciones y gestiones. Registra llamadas, visitas y seguimiento por cliente.
        </p>
        """,
        unsafe_allow_html=True,
    )

    # ── Dashboard KPIs ──────────────────────────────────────────────────
    _render_dashboard_kpis()

    st.markdown("---")

    # ── Section selector ────────────────────────────────────────────────
    section = st.radio(
        "Seccion",
        ["Timeline de Actividad", "Historial por Cliente", "Registrar Gestion",
         "Acuerdos de Pago", "🔔 Bandeja de Pendientes"],
        horizontal=True,
        key="crm_section",
        label_visibility="collapsed",
    )

    if section == "Timeline de Actividad":
        _render_timeline()
    elif section == "Historial por Cliente":
        _render_client_drilldown()
    elif section == "Registrar Gestion":
        _render_register_gestion()
    elif section == "Acuerdos de Pago":
        _render_acuerdos_pago()
    elif section == "🔔 Bandeja de Pendientes":
        _render_bandeja_pendientes()


# ---------------------------------------------------------------------------
# Dashboard KPIs
# ---------------------------------------------------------------------------

_MONTHS_ES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}


def _render_dashboard_kpis():
    # ── Leer filtro de periodo desde session_state (lo setea el Timeline) ──
    _today = date.today()
    _period_from: date = st.session_state.get("crm_date_from", _today)
    _period_to:   date = st.session_state.get("crm_date_to",   _today)

    # ── Stats globales: k1 (última notificación) + k5 (gestiones) ──────────
    stats = dbm.get_crm_dashboard_stats()

    last_notif = stats.get("last_mass_notification")
    if last_notif:
        try:
            last_dt = datetime.fromisoformat(str(last_notif).replace("Z", "+00:00"))
            last_label = last_dt.strftime("%d/%m/%Y %H:%M")
        except Exception:
            last_label = str(last_notif)[:16]
    else:
        last_label = "Sin registro"

    # ── k2 + k4: notificaciones del período seleccionado ───────────────────
    _period_notifs = dbm.get_notifications_report(
        date_from=str(_period_from),
        date_to=str(_period_to),
        limit=5000,
    )
    _period_count = len(_period_notifs)
    _period_sent  = sum(
        1 for n in _period_notifs
        if str(n.get("estado", "")).upper() in ("ENVIADO", "SENT")
    )
    _period_rate  = round(_period_sent / _period_count * 100, 1) if _period_count > 0 else 0.0

    # Etiqueta dinámica k2 según rango seleccionado
    if _period_from == _period_to:
        if _period_from == _today:
            _k2_label = "Emails Enviados Hoy"
            _k2_tip   = "Emails enviados hoy según el filtro de fecha activo en el Timeline."
        else:
            _k2_label = f"Emails · {_period_from.strftime('%d/%m/%Y')}"
            _k2_tip   = f"Emails enviados el {_period_from.strftime('%d/%m/%Y')} según el filtro del Timeline."
    else:
        _k2_label = f"Emails · {_period_from.strftime('%d/%m')} al {_period_to.strftime('%d/%m')}"
        _k2_tip   = (
            f"Emails enviados entre {_period_from.strftime('%d/%m/%Y')} "
            f"y {_period_to.strftime('%d/%m/%Y')} según el filtro del Timeline."
        )

    _k2_status = "success" if _period_count > 0 else "neutral"

    # ── k3: acumulado del mes en curso ─────────────────────────────────────
    _first_of_month = _today.replace(day=1)
    _month_notifs   = dbm.get_notifications_report(
        date_from=str(_first_of_month),
        date_to=str(_today),
        limit=10000,
    )
    _month_count    = len(_month_notifs)
    _month_name     = f"{_MONTHS_ES.get(_today.month, '')} {_today.year}"

    # ── Render ──────────────────────────────────────────────────────────────
    k1, k2, k3, k4, k5 = st.columns(5)

    k1.markdown(
        styles.kpi_card_html(
            "Ultima Notificacion",
            last_label,
            tooltip="Fecha y hora del último envío masivo de email registrado en el sistema. Independiente del filtro.",
        ),
        unsafe_allow_html=True,
    )
    k2.markdown(
        styles.kpi_card_html(
            _k2_label,
            f"{_period_count:,}",
            status=_k2_status,
            tooltip=_k2_tip,
        ),
        unsafe_allow_html=True,
    )
    k3.markdown(
        styles.kpi_card_html(
            "Email Acumulado del Mes",
            f"{_month_count:,}",
            sub_value=_month_name,
            status="neutral",
            tooltip=(
                f"Total de emails enviados en {_month_name} "
                f"(del 01/{_today.month:02d} al {_today.strftime('%d/%m/%Y')}). "
                "Independiente del filtro de fecha del Timeline."
            ),
        ),
        unsafe_allow_html=True,
    )
    k4.markdown(
        styles.kpi_card_html(
            "Tasa de Exito",
            f"{_period_rate:.1f}%" if _period_count > 0 else "—",
            status="success" if _period_rate >= 80 else ("warning" if _period_count > 0 else "neutral"),
            tooltip=(
                f"% de emails con estado ENVIADO sobre el total del período seleccionado "
                f"({_period_from.strftime('%d/%m')} al {_period_to.strftime('%d/%m')}). Meta: >= 80%."
            ),
        ),
        unsafe_allow_html=True,
    )
    k5.markdown(
        styles.kpi_card_html(
            "Gestiones CRM",
            f"{stats.get('total_gestiones', 0):,}",
            sub_value=f"Hoy: {stats.get('gestiones_today', 0):,}",
            status="neutral",
            tooltip=(
                "Total acumulado de interacciones manuales en la tabla gestiones: "
                "llamadas, visitas, WhatsApp y notas. Hoy = registradas en el día actual. "
                "Independiente del filtro de fecha."
            ),
        ),
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Timeline view
# ---------------------------------------------------------------------------

def _render_timeline():
    st.markdown("#### Timeline de Actividad")

    # Filters
    fc1, fc2, fc3, fc4 = st.columns([1, 1, 1, 1])
    date_from = fc1.date_input("Desde", value=date.today(), key="crm_date_from")
    date_to = fc2.date_input("Hasta", value=date.today(), key="crm_date_to")
    tipo_filter = fc3.selectbox("Tipo", ["TODOS"] + TIPOS_GESTION, key="crm_tipo_filter")
    source_filter = fc4.selectbox("Fuente", ["TODAS", "Notificaciones", "Gestiones"], key="crm_source_filter")

    # Mapa cliente_id → empresa: Nivel 1 = tabla clientes Supabase, Nivel 2 = ciclo activo
    _nombre_map_tl: Dict[str, str] = dbm.get_clientes_nombres_map()
    _df_ciclo_tl = (_v if (_v := st.session_state.get("df_final")) is not None else pd.DataFrame())
    if not _df_ciclo_tl.empty and "COD CLIENTE" in _df_ciclo_tl.columns and "EMPRESA" in _df_ciclo_tl.columns:
        for _, _r in _df_ciclo_tl[["COD CLIENTE", "EMPRESA"]].drop_duplicates().iterrows():
            _c = str(_r["COD CLIENTE"]).strip()
            if _c and _c not in _nombre_map_tl:
                _nombre_map_tl[_c] = str(_r["EMPRESA"]).strip()

    # Fetch data from both sources
    timeline_rows: List[Dict[str, Any]] = []

    if source_filter in ("TODAS", "Notificaciones"):
        notifs = dbm.get_notifications_report(
            date_from=str(date_from),
            date_to=str(date_to),
            canal=tipo_filter if tipo_filter not in ("TODOS", "LLAMADA", "VISITA", "NOTA", "OTRO") else None,
            limit=1000,
        )
        for n in notifs:
            canal_meta = (n.get("metadata") or {}).get("channel", "EMAIL")
            _cid_n = str(n.get("cliente_id") or "").strip()
            empresa_n = _nombre_map_tl.get(_cid_n) or _cid_n
            timeline_rows.append({
                "Fecha": str(n.get("fecha_envio") or n.get("created_at", ""))[:16].replace("T", " "),
                "Tipo": canal_meta.upper() if canal_meta else "EMAIL",
                "Cliente": empresa_n,
                "Destinatario": n.get("destinatario", ""),
                "Estado": n.get("estado", ""),
                "Asunto": n.get("asunto", "")[:60],
                "Fuente": "Notificacion",
            })

    if source_filter in ("TODAS", "Gestiones"):
        gestiones = dbm.get_gestiones_list(
            date_from=str(date_from),
            date_to=str(date_to),
            tipo=tipo_filter if tipo_filter != "TODOS" else None,
            limit=1000,
        )
        for g in gestiones:
            _cid_g = str(g.get("cliente_id") or "").strip()
            empresa_g = _nombre_map_tl.get(_cid_g) or _cid_g
            timeline_rows.append({
                "Fecha": str(g.get("fecha", "") or g.get("created_at", ""))[:16].replace("T", " "),
                "Tipo": g.get("tipo_gestion", "OTRO"),
                "Cliente": empresa_g,
                "Destinatario": g.get("usuario", "") or "",
                "Estado": g.get("resultado", ""),
                "Asunto": (g.get("notas", "") or "")[:60],
                "Fuente": "Gestion CRM",
            })

    if not timeline_rows:
        st.info("No hay registros para el periodo seleccionado.")
        return

    df_timeline = pd.DataFrame(timeline_rows)
    df_timeline = df_timeline.sort_values("Fecha", ascending=False).reset_index(drop=True)

    # Add icons to Tipo column
    df_timeline["Tipo"] = df_timeline["Tipo"].apply(lambda t: f"{TIPO_ICONS.get(t, '📌')} {t}")

    # Correlative column
    df_timeline.insert(0, "#", range(1, len(df_timeline) + 1))

    st.dataframe(
        df_timeline,
        use_container_width=True,
        hide_index=True,
        height=450,
        column_config={
            "#":           st.column_config.NumberColumn("#", width="small"),
            "Fecha":       st.column_config.TextColumn("Fecha", width="medium"),
            "Tipo":        st.column_config.TextColumn("Tipo", width="small"),
            "Cliente":     st.column_config.TextColumn("Cliente", width="medium"),
            "Destinatario": st.column_config.TextColumn("Destinatario", width="medium"),
            "Estado":      st.column_config.TextColumn("Estado", width="small"),
            "Asunto":      st.column_config.TextColumn("Detalle", width="large"),
            "Fuente":      st.column_config.TextColumn("Fuente", width="small"),
        },
    )

    # Export
    ec1, ec2 = st.columns([1, 4])
    with ec1:
        csv = df_timeline.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Exportar CSV",
            data=csv,
            file_name=f"timeline_gestiones_{date_from}_{date_to}.csv",
            mime="text/csv",
            key="crm_export_timeline",
        )
    with ec2:
        st.caption(f"{len(df_timeline)} registros en el periodo seleccionado")


# ---------------------------------------------------------------------------
# Client drill-down
# ---------------------------------------------------------------------------

def _render_client_drilldown():
    """Vista CRM: Cartera Gestionada — tabla + multiselect + detalle combinado + export profesional."""

    st.markdown("#### Cartera Gestionada")
    st.caption("Clientes contactados en el período · ordenados por saldo pendiente.")

    # ── Filtros de fecha ──────────────────────────────────────────────────
    hf1, hf2 = st.columns([1, 1])
    h_date_from = hf1.date_input("Desde", value=date.today(), key="hist_date_from")
    h_date_to   = hf2.date_input("Hasta", value=date.today(), key="hist_date_to")

    # ── Mapas desde ciclo activo (saldo, correo, teléfono, estado deuda) ──
    df_ciclo = (_v if (_v := st.session_state.get("df_final")) is not None else pd.DataFrame())
    saldo_map: Dict[str, float] = {}
    email_map: Dict[str, str]   = {}
    tel_map:   Dict[str, str]   = {}
    deuda_map: Dict[str, str]   = {}

    if not df_ciclo.empty and "COD CLIENTE" in df_ciclo.columns:
        for _cod, _grp in df_ciclo.groupby("COD CLIENTE"):
            _c = str(_cod).strip()
            if not _c:
                continue
            if "SALDO REAL" in _grp.columns:
                try:
                    _vals = pd.to_numeric(_grp["SALDO REAL"], errors="coerce")
                    saldo_map[_c] = float(_vals.sum())
                except Exception:
                    pass
            if "CORREO" in _grp.columns:
                _v = _grp["CORREO"].dropna()
                email_map[_c] = str(_v.iloc[0]).strip() if len(_v) > 0 else ""
            if "TELÉFONO" in _grp.columns:
                _v = _grp["TELÉFONO"].dropna()
                tel_map[_c] = str(_v.iloc[0]).strip() if len(_v) > 0 else ""
            if "ESTADO DEUDA" in _grp.columns:
                _v = _grp["ESTADO DEUDA"].dropna()
                deuda_map[_c] = str(_v.iloc[0]).strip() if len(_v) > 0 else ""

    # ── Mapa nombre: Supabase clientes → ciclo activo ─────────────────────
    nombre_map: Dict[str, str] = dbm.get_clientes_nombres_map()
    if not df_ciclo.empty and "COD CLIENTE" in df_ciclo.columns and "EMPRESA" in df_ciclo.columns:
        for _, _r in df_ciclo[["COD CLIENTE", "EMPRESA"]].drop_duplicates().iterrows():
            _c = str(_r["COD CLIENTE"]).strip()
            if _c and _c not in nombre_map:
                nombre_map[_c] = str(_r["EMPRESA"]).strip()

    # ── Interacciones del período ─────────────────────────────────────────
    all_notifs    = dbm.get_notifications_report(date_from=str(h_date_from), date_to=str(h_date_to), limit=2000)
    all_gestiones = dbm.get_gestiones_list(date_from=str(h_date_from), date_to=str(h_date_to), limit=2000)

    if not all_notifs and not all_gestiones:
        st.info(f"Sin interacciones registradas entre {h_date_from} y {h_date_to}. "
                "Envía emails o WhatsApp primero, o amplía el rango de fechas.")
        return

    # ── Agrupar por cliente ───────────────────────────────────────────────
    resumen: Dict[str, Dict[str, Any]] = {}

    for n in all_notifs:
        cid = str(n.get("cliente_id") or "").strip()
        if not cid:
            continue
        if cid not in resumen:
            resumen[cid] = {"emails": 0, "whatsapp": 0, "manual": 0,
                            "ultimo": "", "canales": set(), "ultimo_estado": ""}
        resumen[cid]["emails"] += 1
        resumen[cid]["canales"].add("📧 Email")
        fn = str(n.get("fecha_envio") or n.get("created_at", ""))[:16].replace("T", " ")
        if fn > resumen[cid]["ultimo"]:
            resumen[cid]["ultimo"] = fn
            resumen[cid]["ultimo_estado"] = n.get("estado", "")

    for g in all_gestiones:
        cid = str(g.get("cliente_id") or "").strip()
        if not cid:
            continue
        if cid not in resumen:
            resumen[cid] = {"emails": 0, "whatsapp": 0, "manual": 0,
                            "ultimo": "", "canales": set(), "ultimo_estado": ""}
        tipo_g = str(g.get("tipo_gestion", "OTRO")).upper()
        if tipo_g == "WHATSAPP":
            resumen[cid]["whatsapp"] += 1
            resumen[cid]["canales"].add("💬 WA")
        else:
            resumen[cid]["manual"] += 1
            resumen[cid]["canales"].add(f"{TIPO_ICONS.get(tipo_g, '📌')} {tipo_g.title()}")
        fg = str(g.get("fecha") or g.get("created_at", ""))[:16].replace("T", " ")
        if fg > resumen[cid]["ultimo"]:
            resumen[cid]["ultimo"] = fg
            resumen[cid]["ultimo_estado"] = g.get("resultado", "")

    # ── Construir filas de resumen ────────────────────────────────────────
    today_dt = date.today()
    rows_summary = []
    for cid, data in resumen.items():
        nombre = nombre_map.get(cid, cid)
        saldo  = saldo_map.get(cid, 0.0)

        try:
            ultimo_dt = pd.to_datetime(data["ultimo"]).date() if data["ultimo"] else None
            dias_sin  = (today_dt - ultimo_dt).days if ultimo_dt else 999
        except Exception:
            dias_sin = 999

        ult = str(data["ultimo_estado"]).upper()
        if ult in ("SENT", "ENVIADO", "EXITOSO"):
            resultado = "✅ Enviado"
        elif ult in ("FAILED", "FALLIDO"):
            resultado = "❌ Fallido"
        elif ult in ("PENDIENTE",):
            resultado = "⏳ Pendiente"
        else:
            resultado = ult or "—"

        rows_summary.append({
            "_cid":              cid,
            "Cliente":           nombre,
            "Saldo S/":          saldo,
            "Estado Deuda":      deuda_map.get(cid, ""),
            "Días sin contacto": dias_sin,
            "📧":                resumen[cid]["emails"],
            "💬 WA":             resumen[cid]["whatsapp"],
            "📞 Manual":         resumen[cid]["manual"],
            "Canales":           " | ".join(sorted(data["canales"])),
            "Última Gestión":    data["ultimo"][:16] if data["ultimo"] else "—",
            "Resultado":         resultado,
        })

    # Ordenar: mayor saldo primero; empate → más días sin contacto primero
    df_summary = (
        pd.DataFrame(rows_summary)
        .sort_values(["Saldo S/", "Días sin contacto"], ascending=[False, False])
        .reset_index(drop=True)
    )

    if df_summary.empty:
        st.info(f"Sin interacciones registradas entre {h_date_from} y {h_date_to}. "
                "Envía emails o WhatsApp primero, o amplía el rango de fechas.")
        return

    # ── Multiselect de clientes (filtro de tabla — no controla el detalle) ──
    _all_options = [f"{r['_cid']} — {r['Cliente']}" for _, r in df_summary.iterrows()]
    _valid_set = set(_all_options)
    if "hist_client_filter" in st.session_state:
        st.session_state["hist_client_filter"] = [
            x for x in st.session_state["hist_client_filter"] if x in _valid_set
        ]

    h_clients: List[str] = st.multiselect(
        f"Seleccione Clientes ({len(_all_options)} con actividad en el período):",
        options=_all_options,
        placeholder="Todos los clientes · selecciona uno o varios para filtrar...",
        key="hist_client_filter",
    )

    # Aplicar filtro a la tabla de resumen
    _selected_cids: List[str] = []
    if h_clients:
        _selected_cids = [opt.split(" — ")[0].strip() for opt in h_clients]
        df_summary = df_summary[df_summary["_cid"].isin(_selected_cids)].reset_index(drop=True)

    # ── KPIs de resumen (reflejan la selección actual) ────────────────────
    total_gestionados = len(df_summary)
    total_saldo_gest  = df_summary["Saldo S/"].sum()
    con_fallo         = (df_summary["Resultado"] == "❌ Fallido").sum()
    dias_prom_val     = df_summary["Días sin contacto"].replace(999, pd.NA).mean()
    dias_prom_str     = f"{dias_prom_val:.0f} días" if pd.notna(dias_prom_val) else "—"

    kc1, kc2, kc3, kc4 = st.columns(4)
    kc1.metric("Clientes Gestionados", total_gestionados)
    kc2.metric("Saldo Total Gestionado", f"S/ {total_saldo_gest:,.0f}")
    kc3.metric("Fallidos / Sin Respuesta", con_fallo)
    kc4.metric("Prom. Días Sin Contacto", dias_prom_str)

    # ── Tabla de cartera gestionada (checkbox en cabecera = seleccionar todos) ──
    st.caption(f"Ordenado por saldo pendiente · {total_gestionados} clientes · "
               "clic en fila para seleccionar · checkbox en cabecera para seleccionar todos")
    display_cols = ["Cliente", "Saldo S/", "Estado Deuda", "Días sin contacto",
                    "📧", "💬 WA", "📞 Manual", "Canales", "Última Gestión", "Resultado"]
    has_saldo = total_saldo_gest > 0

    _tbl_sel = st.dataframe(
        df_summary[display_cols],
        use_container_width=True,
        hide_index=True,
        height=300,
        on_select="rerun",
        selection_mode="multi-row",
        column_config={
            "Cliente":           st.column_config.TextColumn("Cliente", width="large"),
            "Saldo S/":          st.column_config.NumberColumn("Saldo S/", format="S/ %.2f", width="medium")
                                 if has_saldo else st.column_config.TextColumn("Saldo S/", width="small"),
            "Estado Deuda":      st.column_config.TextColumn("Estado Deuda", width="medium"),
            "Días sin contacto": st.column_config.NumberColumn("Días s/Contacto", width="small"),
            "📧":                st.column_config.NumberColumn("📧", width="small"),
            "💬 WA":             st.column_config.NumberColumn("💬 WA", width="small"),
            "📞 Manual":         st.column_config.NumberColumn("📞", width="small"),
            "Canales":           st.column_config.TextColumn("Canales", width="medium"),
            "Última Gestión":    st.column_config.TextColumn("Última Gestión", width="medium"),
            "Resultado":         st.column_config.TextColumn("Resultado", width="small"),
        },
    )

    # ── Detalle combinado de filas seleccionadas ──────────────────────────
    _sel_rows = (_tbl_sel.selection.rows if _tbl_sel and hasattr(_tbl_sel, "selection") else [])

    if not _sel_rows:
        st.caption("Selecciona una o varias filas · el checkbox en la cabecera de la tabla selecciona todos.")
        return

    _sel_cids = [df_summary.iloc[i]["_cid"] for i in _sel_rows]

    # Construir historial combinado
    history: List[Dict[str, Any]] = []
    for _cid in _sel_cids:
        _cname = nombre_map.get(_cid, _cid)
        for n in dbm.get_notifications_history([_cid], limit=500):
            canal_meta = str((n.get("metadata") or {}).get("channel", "EMAIL")).strip().upper()
            canal_icon = TIPO_ICONS.get(canal_meta, "📧")
            history.append({
                "Cliente":   _cname,
                "Fecha":     str(n.get("fecha_envio") or n.get("created_at", ""))[:16].replace("T", " "),
                "Canal":     f"{canal_icon} {canal_meta.title()}",
                "Resultado": n.get("estado", ""),
                "Detalle":   (n.get("asunto", "") or "")[:120],
            })
        for g in dbm.get_gestiones_by_client(_cid, limit=500):
            _tipo = g.get("tipo_gestion", "OTRO")
            history.append({
                "Cliente":   _cname,
                "Fecha":     str(g.get("fecha") or g.get("created_at", ""))[:16].replace("T", " "),
                "Canal":     f"{TIPO_ICONS.get(_tipo, '📌')} {_tipo.title()}",
                "Resultado": g.get("resultado", ""),
                "Detalle":   (g.get("notas", "") or "")[:120],
            })

    if not history:
        st.info("Sin interacciones registradas para los clientes seleccionados.")
        return

    df_drill = pd.DataFrame(history).sort_values(["Fecha", "Cliente"], ascending=[False, True]).reset_index(drop=True)

    # 1 cliente → ocultar columna Cliente; varios → mostrarla
    _is_single   = len(_sel_cids) == 1
    _det_cols    = ["Fecha", "Canal", "Resultado", "Detalle"] if _is_single \
                   else ["Cliente", "Fecha", "Canal", "Resultado", "Detalle"]
    _det_label   = nombre_map.get(_sel_cids[0], _sel_cids[0]) if _is_single \
                   else f"{len(_sel_cids)} clientes seleccionados"

    st.caption(f"Detalle de interacciones · {_det_label} · {len(df_drill)} registros")
    st.dataframe(
        df_drill[_det_cols],
        use_container_width=True,
        hide_index=True,
        height=280,
        column_config={
            "Cliente":   st.column_config.TextColumn("Cliente", width="medium"),
            "Fecha":     st.column_config.TextColumn("Fecha", width="medium"),
            "Canal":     st.column_config.TextColumn("Canal", width="small"),
            "Resultado": st.column_config.TextColumn("Resultado", width="small"),
            "Detalle":   st.column_config.TextColumn("Detalle / Asunto", width="large"),
        },
    )

    # ── Export profesional de evidencia de gestión ────────────────────────
    _now_export = datetime.now()
    _periodo    = f"{h_date_from.strftime('%d/%m/%Y')} al {h_date_to.strftime('%d/%m/%Y')}"
    _sel_saldo  = sum(saldo_map.get(c, 0.0) for c in _sel_cids)
    _tasa_exito = round(
        (df_summary[df_summary["_cid"].isin(_sel_cids)]["Resultado"] == "✅ Enviado").sum()
        / max(len(_sel_cids), 1) * 100, 1
    )

    _buf = io.StringIO()
    _buf.write("REPORTE DE GESTIÓN DE COBRANZA\n")
    _buf.write(f"Generado por,Antay Consultoria — Sistema ReporteCobranzas\n")
    _buf.write(f"Fecha de emisión,{_now_export.strftime('%d/%m/%Y %H:%M:%S')}\n")
    _buf.write(f"Período analizado,{_periodo}\n")
    _buf.write(f"Clientes en reporte,{len(_sel_cids)}\n")
    _buf.write(f"Saldo total pendiente,S/ {_sel_saldo:,.2f}\n")
    _buf.write(f"Tasa de éxito,{_tasa_exito}%\n")
    _buf.write("\n")

    # Sección 1: ficha de cada cliente seleccionado
    _buf.write("SECCIÓN 1 — DATOS DE CLIENTES\n")
    _buf.write("COD Cliente,Empresa,Saldo Pendiente,Estado Deuda,Correo,Teléfono\n")
    for _cid in _sel_cids:
        _buf.write(
            f"{_cid},"
            f"{nombre_map.get(_cid, _cid)},"
            f"S/ {saldo_map.get(_cid, 0.0):,.2f},"
            f"{deuda_map.get(_cid, '—')},"
            f"{email_map.get(_cid, '—') or '—'},"
            f"{tel_map.get(_cid, '—') or '—'}\n"
        )
    _buf.write("\n")

    # Sección 2: historial de interacciones
    _buf.write("SECCIÓN 2 — HISTORIAL DE INTERACCIONES\n")
    df_drill.to_csv(_buf, index=False)

    _csv_bytes = _buf.getvalue().encode("utf-8")
    _suffix    = _sel_cids[0] if _is_single else f"{len(_sel_cids)}clientes"
    _fname     = f"gestion_{_suffix}_{h_date_from.strftime('%Y%m%d')}_{h_date_to.strftime('%Y%m%d')}.csv"

    st.download_button(
        label=f"Descargar Reporte de Gestión · {_det_label[:45]} · {_periodo}",
        data=_csv_bytes,
        file_name=_fname,
        mime="text/csv",
        key="crm_export_drill",
        type="primary",
    )


def _render_client_info_card(client: dict):
    nombre = client.get("nombre", "Sin nombre")
    email = client.get("email", "Sin correo")
    telefono = client.get("telefono", "Sin telefono")
    estado = client.get("estado", "ACTIVO")
    enviar = client.get("enviar_email", "SIN CONFIGURAR")

    estado_color = {"ACTIVO": "#2B8A3E", "INACTIVO": "#486581", "MOROSO": "#C92A2A"}.get(estado, "#486581")

    st.markdown(
        f"""
        <div class="kpi-card" style="border-left:4px solid {estado_color}; margin-bottom:16px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div style="font-size:16px; font-weight:700; color:#102A43;">{nombre}</div>
                    <div style="font-size:13px; color:#486581; margin-top:4px;">
                        📧 {email} &nbsp;|&nbsp; 📞 {telefono} &nbsp;|&nbsp;
                        Estado: <strong style="color:{estado_color};">{estado}</strong> &nbsp;|&nbsp;
                        Enviar Email: <strong>{enviar}</strong>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Register gestion (manual interaction)
# ---------------------------------------------------------------------------

def _render_register_gestion():
    st.markdown("#### Registrar Gestion Manual")
    st.markdown(
        """
        <div class="antay-inline-note">
            Registra llamadas, visitas, notas u otras interacciones con clientes
            para mantener trazabilidad completa en el CRM.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Contador de formulario: al incrementar, todos los keys cambian y los widgets se limpian ──
    _fv = st.session_state.get("crm_reg_form_v", 0)

    # Mensaje de éxito (se muestra antes del formulario, tras el rerun)
    if st.session_state.pop("crm_reg_success", None):
        st.success("✓ Gestión registrada correctamente.")

    # ── Cargar todos los clientes: Supabase + ciclo activo ──────────────────
    nombre_map_reg: Dict[str, str] = dbm.get_clientes_nombres_map()
    df_ciclo_reg = (_v if (_v := st.session_state.get("df_final")) is not None else pd.DataFrame())
    if not df_ciclo_reg.empty and "COD CLIENTE" in df_ciclo_reg.columns and "EMPRESA" in df_ciclo_reg.columns:
        for _, _r in df_ciclo_reg[["COD CLIENTE", "EMPRESA"]].drop_duplicates().iterrows():
            _c = str(_r["COD CLIENTE"]).strip()
            if _c and _c not in nombre_map_reg:
                nombre_map_reg[_c] = str(_r["EMPRESA"]).strip()

    client_options = sorted(
        [f"{cid} — {nombre}" for cid, nombre in nombre_map_reg.items() if cid],
        key=lambda x: x.split(" — ")[0],
    )

    # ── Selectbox con búsqueda nativa (filtra al escribir) ──────────────────
    selected_option = st.selectbox(
        f"Buscar cliente ({len(client_options)} disponibles):",
        options=[None] + client_options,
        index=0,
        placeholder="Escribe código o nombre para buscar...",
        key=f"crm_reg_client_{_fv}",
        format_func=lambda x: "— Selecciona un cliente —" if x is None else x,
    )

    cliente_id_selected = None
    if selected_option:
        cliente_id_selected = selected_option.split(" — ")[0].strip()

    # Form
    _codigos_resultado, _labels_resultado, _ = _build_resultado_maps()
    _codigos_activos = _get_resultados_activos()
    fc1, fc2, fc3 = st.columns(3)
    tipo = fc1.selectbox("Tipo de gestion", TIPOS_GESTION_MANUAL, index=0, key=f"crm_reg_tipo_{_fv}")
    resultado = fc2.selectbox(
        "Resultado",
        _codigos_activos,
        key=f"crm_reg_resultado_{_fv}",
        format_func=lambda c: _labels_resultado.get(c, c),
    )
    fecha = fc3.date_input("Fecha", value=date.today(), key=f"crm_reg_fecha_{_fv}")

    fc4, fc5 = st.columns(2)
    duracion = fc4.number_input("Duracion (minutos)", min_value=0, max_value=480, value=0, key=f"crm_reg_duracion_{_fv}")
    usuario = fc5.text_input("Operador / Usuario", key=f"crm_reg_usuario_{_fv}")

    notas = st.text_area(
        "Notas / Observaciones",
        placeholder="Detalla la gestion realizada...",
        key=f"crm_reg_notas_{_fv}",
        height=100,
    )

    if st.button("Registrar Gestion", type="primary", key=f"crm_reg_submit_{_fv}"):
        if not cliente_id_selected:
            st.warning("Selecciona un cliente antes de registrar.")
            return

        _cycle = (
            st.session_state.get("active_cycle_id")
            or st.session_state.get("current_cycle_id")
            or st.session_state.get("cycle_id")
        )
        ok, msg = dbm.insert_gestion(
            cliente_id=cliente_id_selected,
            tipo_gestion=tipo,
            resultado=resultado,
            notas=notas,
            usuario=usuario if usuario else None,
            duracion_minutos=duracion if duracion > 0 else None,
            fecha=datetime.combine(fecha, datetime.min.time()).isoformat(),
            cycle_id=_cycle,
        )

        if ok:
            st.session_state["crm_reg_form_v"] = _fv + 1
            st.session_state["crm_reg_success"] = True
            st.rerun()
        else:
            st.error(msg)


# ---------------------------------------------------------------------------
# RC-FEAT-021: Acuerdos de Pago con Cuotas
# ---------------------------------------------------------------------------

_CUOTA_ESTADO_ICONS = {
    "PENDIENTE": "🕐",
    "PAGADO": "✅",
    "VENCIDO": "🔴",
    "REPACTADO": "🔄",
}

_ACUERDO_ESTADO_COLORS = {
    "ACTIVO": "#1a7f37",
    "CUMPLIDO": "#0b7285",
    "INCUMPLIDO": "#c62828",
    "CANCELADO": "#888888",
}


def _render_acuerdos_pago():
    st.markdown("#### Acuerdos de Pago")
    st.markdown(
        """
        <div class="antay-inline-note">
            Registra y gestiona acuerdos de pago en cuotas.
            Manten el seguimiento de cada cuota para recuperar deuda de forma ordenada.
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab1, tab2 = st.tabs(["📋 Ver Acuerdos por Cliente", "➕ Nuevo Acuerdo"])

    with tab1:
        _render_ver_acuerdos()

    with tab2:
        _render_nuevo_acuerdo()


def _render_ver_acuerdos():
    """Show acuerdos and allow updating cuota states."""
    nombre_map_ap: Dict[str, str] = dbm.get_clientes_nombres_map()
    client_opts_ap = sorted(
        [f"{cid} — {nombre}" for cid, nombre in nombre_map_ap.items() if cid],
        key=lambda x: x.split(" — ")[0],
    )

    sel_ap = st.selectbox(
        f"Buscar cliente ({len(client_opts_ap)} disponibles):",
        options=[None] + client_opts_ap,
        index=0,
        placeholder="Escribe código o nombre...",
        key="acuerdo_ver_client",
        format_func=lambda x: "— Selecciona un cliente —" if x is None else x,
    )

    if not sel_ap:
        st.info("Selecciona un cliente para ver sus acuerdos.")
        return

    cliente_id_ap = sel_ap.split(" — ")[0].strip()
    acuerdos = dbm.get_acuerdos_by_cliente(cliente_id_ap)

    if not acuerdos:
        st.info(f"El cliente **{sel_ap}** no tiene acuerdos de pago registrados.")
        return

    for idx, acuerdo in enumerate(acuerdos):
        estado_color = _ACUERDO_ESTADO_COLORS.get(acuerdo.get("estado", ""), "#555")
        with st.expander(
            f"📄 Acuerdo {acuerdo['fecha_acuerdo']} — "
            f"S/ {float(acuerdo.get('monto_total', 0)):,.2f} — "
            f"{acuerdo.get('numero_cuotas', 0)} cuota(s)",
            expanded=(idx == 0),
        ):
            col_est, col_ges, col_ciclo = st.columns(3)
            col_est.markdown(
                f"**Estado:** <span style='color:{estado_color}; font-weight:700;'>"
                f"{acuerdo.get('estado','—')}</span>",
                unsafe_allow_html=True,
            )
            col_ges.markdown(f"**Gestor:** {acuerdo.get('gestor') or '—'}")
            col_ciclo.markdown(f"**Ciclo:** {acuerdo.get('ciclo_id') or '—'}")

            if acuerdo.get("notas"):
                st.caption(f"📝 {acuerdo['notas']}")

            cuotas = acuerdo.get("cuotas", [])
            if not cuotas:
                st.warning("Este acuerdo no tiene cuotas registradas.")
                continue

            st.markdown("**Cuotas:**")
            for cuota in cuotas:
                c_ico = _CUOTA_ESTADO_ICONS.get(cuota.get("estado", ""), "❓")
                c_c1, c_c2, c_c3, c_c4, c_c5 = st.columns([1, 2, 2, 2, 3])
                c_c1.markdown(f"**#{cuota['numero_cuota']}**")
                c_c2.markdown(f"S/ {float(cuota.get('monto_cuota', 0)):,.2f}")
                c_c3.markdown(f"Vence: {cuota.get('fecha_vencimiento','—')}")
                c_c4.markdown(f"{c_ico} {cuota.get('estado','—')}")

                if cuota.get("estado") == "PENDIENTE":
                    btn_key = f"cuota_pagar_{cuota['id']}"
                    if c_c5.button("✅ Marcar Pagado", key=btn_key):
                        ok, msg = dbm.update_cuota_estado(
                            cuota["id"], "PAGADO",
                            fecha_pago=date.today().isoformat(),
                        )
                        if ok:
                            st.success(f"Cuota #{cuota['numero_cuota']} marcada como PAGADO.")
                            st.rerun()
                        else:
                            st.error(msg)


def _render_nuevo_acuerdo():
    """Form to create a new acuerdo de pago with N cuotas."""
    nombre_map_np: Dict[str, str] = dbm.get_clientes_nombres_map()
    client_opts_np = sorted(
        [f"{cid} — {nombre}" for cid, nombre in nombre_map_np.items() if cid],
        key=lambda x: x.split(" — ")[0],
    )

    with st.form("form_nuevo_acuerdo"):
        sel_np = st.selectbox(
            "Cliente",
            options=[None] + client_opts_np,
            index=0,
            key="acuerdo_nuevo_client",
            format_func=lambda x: "— Selecciona un cliente —" if x is None else x,
        )

        n_c1, n_c2, n_c3 = st.columns(3)
        monto_total = n_c1.number_input(
            "Monto Total (S/)", min_value=0.01, value=1000.00, step=100.0, format="%.2f"
        )
        num_cuotas = n_c2.number_input(
            "Número de Cuotas", min_value=1, max_value=24, value=3, step=1
        )
        fecha_acuerdo = n_c3.date_input("Fecha del Acuerdo", value=date.today())

        n_c4, n_c5 = st.columns(2)
        gestor = n_c4.text_input("Gestor / Responsable")
        primera_cuota_fecha = n_c5.date_input(
            "Fecha 1ª Cuota",
            value=date.today().replace(day=1),
            help="Las cuotas siguientes se programan mensualmente.",
        )

        notas_acuerdo = st.text_area(
            "Notas del Acuerdo",
            placeholder="Detalles del acuerdo pactado con el cliente...",
            height=80,
        )

        submitter = st.form_submit_button("💾 Crear Acuerdo", type="primary")

    if submitter:
        if not sel_np:
            st.warning("Selecciona un cliente.")
            return

        cliente_id_np = sel_np.split(" — ")[0].strip()
        monto_cuota = round(float(monto_total) / int(num_cuotas), 2)
        cuotas_list = []
        from dateutil.relativedelta import relativedelta
        fecha_base = primera_cuota_fecha
        for i in range(int(num_cuotas)):
            cuotas_list.append({
                "numero_cuota": i + 1,
                "monto_cuota": monto_cuota,
                "fecha_vencimiento": (fecha_base + relativedelta(months=i)).isoformat(),
            })

        ciclo_actual = st.session_state.get("current_cycle_id")
        ok, result = dbm.insert_acuerdo_pago(
            cliente_id=cliente_id_np,
            monto_total=float(monto_total),
            numero_cuotas=int(num_cuotas),
            fecha_acuerdo=fecha_acuerdo.isoformat(),
            cuotas=cuotas_list,
            gestor=gestor.strip() if gestor else None,
            ciclo_id=ciclo_actual,
            notas=notas_acuerdo.strip() if notas_acuerdo else None,
        )
        if ok:
            st.success(
                f"✅ Acuerdo creado (ID: `{result}`) — "
                f"{int(num_cuotas)} cuotas de S/ {monto_cuota:,.2f} para **{sel_np}**."
            )
        else:
            st.error(f"❌ {result}")


# ---------------------------------------------------------------------------
# RC-FEAT-022: Bandeja de Pendientes
# ---------------------------------------------------------------------------

def _render_bandeja_pendientes():
    st.markdown("#### 🔔 Bandeja de Pendientes")
    st.markdown(
        """
        <div class="antay-inline-note">
            Vista consolidada de cuotas vencidas/pendientes de hoy y clientes sin gestión en el ciclo activo.
            Actúa directamente desde aquí para no dejar ningún pendiente.
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_cuotas, tab_sin_gestion = st.tabs(["📅 Cuotas Vencidas/Hoy", "⚠️ Sin Gestión en Ciclo"])

    with tab_cuotas:
        _render_cuotas_pendientes()

    with tab_sin_gestion:
        _render_sin_gestion()


def _render_cuotas_pendientes():
    """Show cuotas with estado=PENDIENTE and fecha_vencimiento <= today."""
    cuotas = dbm.get_cuotas_pendientes_hoy(limit=200)

    if not cuotas:
        st.success("✅ No hay cuotas vencidas ni pendientes para hoy.")
        return

    st.markdown(f"**{len(cuotas)} cuota(s)** con vencimiento pendiente:")

    nombre_map_bp: Dict[str, str] = dbm.get_clientes_nombres_map()

    for cuota in cuotas:
        # Extract cliente_id from joined acuerdos_pago
        acuerdo_info = cuota.get("acuerdos_pago") or {}
        if isinstance(acuerdo_info, list):
            acuerdo_info = acuerdo_info[0] if acuerdo_info else {}
        cid = str(acuerdo_info.get("cliente_id", "")).strip()
        nombre = nombre_map_bp.get(cid, cid)
        gestor = acuerdo_info.get("gestor") or "—"

        vence = cuota.get("fecha_vencimiento", "—")
        monto = float(cuota.get("monto_cuota", 0))
        estado = cuota.get("estado", "PENDIENTE")
        icono = _CUOTA_ESTADO_ICONS.get(estado, "❓")
        cuota_id = cuota.get("id", "")
        num = cuota.get("numero_cuota", "?")

        col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 1, 2])
        col1.markdown(f"**{nombre}**")
        col2.markdown(f"Cuota #{num} · S/ {monto:,.2f}")
        col3.markdown(f"Vence: **{vence}**")
        col4.markdown(f"{icono} {estado}")

        btn_k = f"bp_pagar_{cuota_id}"
        if col5.button("✅ Marcar Pagado", key=btn_k):
            ok, msg = dbm.update_cuota_estado(
                cuota_id, "PAGADO", fecha_pago=date.today().isoformat(),
            )
            if ok:
                st.success(f"Cuota #{num} de **{nombre}** marcada como PAGADO.")
                st.rerun()
            else:
                st.error(msg)


def _render_sin_gestion():
    """Show clients in the active cycle with no gestiones registered."""
    cycle_id = st.session_state.get("current_cycle_id") or st.session_state.get("cycle_id")

    if not cycle_id:
        st.info("No hay un ciclo activo en la sesión. Carga archivos primero.")
        return

    sin_gestion = dbm.get_clientes_sin_gestion_ciclo(cycle_id, limit=200)
    nombre_map_sg: Dict[str, str] = dbm.get_clientes_nombres_map()

    if not sin_gestion:
        st.success(f"✅ Todos los clientes del ciclo `{cycle_id}` tienen al menos una gestión registrada.")
        return

    st.markdown(
        f"**{len(sin_gestion)} cliente(s)** sin gestión en el ciclo activo `{cycle_id}`:"
    )
    st.caption("Estos clientes no tienen ninguna llamada, visita, WhatsApp ni nota registrada.")

    for cid in sin_gestion:
        nombre = nombre_map_sg.get(cid, cid)
        col_n, col_btn = st.columns([5, 2])
        col_n.markdown(f"**{cid}** — {nombre}")
        if col_btn.button("📝 Registrar Gestión", key=f"sg_reg_{cid}"):
            st.session_state["crm_section"] = "Registrar Gestion"
            st.session_state["crm_reg_client"] = f"{cid} — {nombre}"
            st.rerun()
