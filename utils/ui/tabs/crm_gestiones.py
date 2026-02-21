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
RESULTADOS = ["EXITOSO", "FALLIDO", "PENDIENTE", "SIN_RESPUESTA", "REPROGRAMADO"]

TIPO_ICONS = {
    "EMAIL": "📧",
    "WHATSAPP": "💬",
    "LLAMADA": "📞",
    "VISITA": "🏢",
    "NOTA": "📝",
    "OTRO": "📌",
}

RESULTADO_COLORS = {
    "EXITOSO": "success",
    "FALLIDO": "danger",
    "PENDIENTE": "warning",
    "SIN_RESPUESTA": "neutral",
    "REPROGRAMADO": "neutral",
}


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
        ["Timeline de Actividad", "Historial por Cliente", "Registrar Gestion"],
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
    _df_ciclo_tl = st.session_state.get("df_final", pd.DataFrame())
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
    df_ciclo = st.session_state.get("df_final", pd.DataFrame())
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
            history.append({
                "Cliente":   _cname,
                "Fecha":     str(n.get("fecha_envio") or n.get("created_at", ""))[:16].replace("T", " "),
                "Canal":     f"{TIPO_ICONS.get('EMAIL', '📧')} Email",
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

    # ── Cargar todos los clientes: Supabase + ciclo activo ──────────────────
    nombre_map_reg: Dict[str, str] = dbm.get_clientes_nombres_map()
    df_ciclo_reg = st.session_state.get("df_final", pd.DataFrame())
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
        key="crm_reg_client",
        format_func=lambda x: "— Selecciona un cliente —" if x is None else x,
    )

    cliente_id_selected = None
    if selected_option:
        cliente_id_selected = selected_option.split(" — ")[0].strip()

    # Form
    fc1, fc2, fc3 = st.columns(3)
    tipo = fc1.selectbox("Tipo de gestion", TIPOS_GESTION, index=2, key="crm_reg_tipo")  # Default: LLAMADA
    resultado = fc2.selectbox("Resultado", RESULTADOS, key="crm_reg_resultado")
    fecha = fc3.date_input("Fecha", value=date.today(), key="crm_reg_fecha")

    fc4, fc5 = st.columns(2)
    duracion = fc4.number_input("Duracion (minutos)", min_value=0, max_value=480, value=0, key="crm_reg_duracion")
    usuario = fc5.text_input("Operador / Usuario", key="crm_reg_usuario")

    notas = st.text_area(
        "Notas / Observaciones",
        placeholder="Detalla la gestion realizada...",
        key="crm_reg_notas",
        height=100,
    )

    if st.button("Registrar Gestion", type="primary", key="crm_reg_submit"):
        if not cliente_id_selected:
            st.warning("Selecciona un cliente antes de registrar.")
            return

        ok, msg = dbm.insert_gestion(
            cliente_id=cliente_id_selected,
            tipo_gestion=tipo,
            resultado=resultado,
            notas=notas,
            usuario=usuario if usuario else None,
            duracion_minutos=duracion if duracion > 0 else None,
            fecha=datetime.combine(fecha, datetime.min.time()).isoformat(),
        )

        if ok:
            st.success(f"Gestion registrada para cliente {cliente_id_selected}")
            st.balloons()
        else:
            st.error(msg)
