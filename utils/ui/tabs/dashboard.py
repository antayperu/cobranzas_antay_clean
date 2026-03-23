"""
RC-FEAT-038: Dashboard de Efectividad de Cobranza

Tab de visibilidad gerencial: proceso de cobranza, KPIs ejecutivos,
efectividad por plantilla WA y ranking de clientes críticos.
Solo lectura — nunca modifica df_final ni df_filtered.
"""
from __future__ import annotations

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import utils.db_manager as dbm
from utils.ui.styles import COLORS


# ---------------------------------------------------------------------------
# Helpers de presentación
# ---------------------------------------------------------------------------

def _fmt_moneda(valor: float) -> str:
    """Formatea un número como moneda S/ con separador de miles."""
    try:
        return f"S/ {valor:,.2f}"
    except Exception:
        return "S/ 0.00"


def _fmt_pct(valor: float) -> str:
    return f"{valor:.1f}%"


def _resultado_label(codigo: str) -> str:
    _MAP = {
        "EXITOSO":        "✅ Acordó pagar",
        "PROMESA_PAGO":   "✅ Acordó pagar",        # legado — mismo significado que EXITOSO
        "SOLICITO_PLAZO": "⏳ Solicitó más plazo",
        "EN_NEGOCIACION": "💬 En negociación",
        "SIN_RESPUESTA":  "📵 Sin respuesta",
        "ESCALAR_LEGAL":  "⚖️ Derivar a Legal",
        "DISPUTA":        "❓ Disputó la deuda",
        "SIN_GESTION":    "— Sin gestión",
        "PENDIENTE":      "✅ Acordó pagar",         # legado
        "REPROGRAMADO":   "⚖️ Derivar a Legal",      # legado
        "FALLIDO":        "❌ Falló",                 # legado
    }
    return _MAP.get(codigo, codigo)


def _resultado_color(codigo: str) -> str:
    _COL = {
        "EXITOSO":        COLORS["success"],
        "PROMESA_PAGO":   COLORS["accent"],
        "SOLICITO_PLAZO": COLORS["warning"],
        "EN_NEGOCIACION": COLORS.get("primary_soft", COLORS["primary"]),
        "SIN_RESPUESTA":  COLORS["text_muted"],
        "ESCALAR_LEGAL":  COLORS["danger"],
        "DISPUTA":        "#7C3AED",
        "SIN_GESTION":    COLORS["border"],
    }
    return _COL.get(codigo, COLORS["text_muted"])


# ---------------------------------------------------------------------------
# Bloques del Dashboard
# ---------------------------------------------------------------------------

def _render_selector_periodo() -> tuple[str, str, Optional[str]]:
    """Selector de período + ciclo. Retorna (date_from, date_to, cycle_id)."""
    col_p, col_c = st.columns([2, 2])

    with col_p:
        periodo = st.selectbox(
            "📅 Período",
            options=["Hoy", "Últimos 7 días", "Últimos 30 días", "Este mes", "Trimestre actual"],
            index=1,
            key="dash_periodo",
        )

    today = datetime.now().date()
    if periodo == "Hoy":
        date_from = str(today)
        date_to = str(today)
    elif periodo == "Últimos 7 días":
        date_from = str(today - timedelta(days=7))
        date_to = str(today)
    elif periodo == "Últimos 30 días":
        date_from = str(today - timedelta(days=30))
        date_to = str(today)
    elif periodo == "Este mes":
        date_from = today.replace(day=1).isoformat()
        date_to = str(today)
    else:  # Trimestre actual
        month = today.month
        q_start_month = ((month - 1) // 3) * 3 + 1
        date_from = today.replace(month=q_start_month, day=1).isoformat()
        date_to = str(today)

    with col_c:
        cycle_id = st.session_state.get("active_cycle_id") or st.session_state.get("cycle_id")
        if cycle_id:
            st.info(f"🔄 Ciclo activo: **{cycle_id}**")
        else:
            st.caption("ℹ️ Sin ciclo activo — mostrando datos globales")

    return date_from, date_to, cycle_id


# ---------------------------------------------------------------------------
# [A] Header del Ciclo
# ---------------------------------------------------------------------------

def _render_header_ciclo(
    cycle_id: Optional[str],
    criticos: List[Dict[str, Any]],
    funnel: Optional[Dict[str, Any]] = None,
) -> None:
    """Bloque A: Una línea de contexto con el resumen financiero del ciclo activo."""
    if not cycle_id:
        return

    total_sol  = sum(float(c.get("saldo_sol", 0)) for c in criticos)
    total_usd  = sum(float(c.get("saldo_usd", 0)) for c in criticos)

    cartera_notificable = (funnel or {}).get("cartera", 0)
    cartera_total       = (funnel or {}).get("cartera_total", cartera_notificable)
    especiales          = max(cartera_total - cartera_notificable, 0)

    partes = [f"**Ciclo:** {cycle_id}"]
    if cartera_notificable:
        partes.append(f"**En gestión:** {cartera_notificable} clientes")
    if especiales:
        partes.append(f"**Especiales:** {especiales} (trato directo, sin notificación)")
    if total_sol > 0:
        partes.append(f"**S/** {total_sol:,.0f}")
    if total_usd > 0:
        partes.append(f"**US$** {total_usd:,.0f} pendiente de cobro")

    st.markdown(
        "<div style='background:#EFF6FF;border-left:4px solid #0D3B66;"
        "padding:10px 16px;border-radius:6px;margin-bottom:4px;font-size:0.92rem;'>"
        + "  ·  ".join(partes) +
        "</div>",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# [B] KPIs Ejecutivos — 5 métricas de negocio
# ---------------------------------------------------------------------------

def _render_kpis_principales(kpis: Dict[str, Any], funnel: Dict[str, int]) -> None:
    """Bloque B: 5 KPIs ejecutivos que resumen el estado del ciclo en una fila."""
    st.markdown("### 📊 Resumen Ejecutivo")

    if not kpis:
        st.info("Sin datos para el período seleccionado.")
        return

    # Todas las métricas del Resumen Ejecutivo se derivan del funnel (ciclo activo)
    # para garantizar coherencia con el cuadro "Proceso de Cobranza".
    # Antes usaban get_kpis_periodo() (rango de fechas) → daban números distintos
    # y podían producir tasas > 100% (ej: 109.4%), lo que destruye la credibilidad.
    cartera     = funnel.get("cartera", 0)
    contactados = funnel.get("alcanzados", 0)       # Total alcanzados únicos del ciclo
    gestionados = funnel.get("con_respuesta", 0)     # Con resultado registrado del ciclo

    cobertura_pct = round(contactados / cartera * 100, 1) if cartera > 0 else 0.0
    tasa_gestion  = round(gestionados / contactados * 100, 1) if contactados > 0 else 0.0
    tasa_recuper  = kpis.get("tasa_exito_pct", 0.0)

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            label="🎯 Alcanzados",
            value=f"{contactados:,}",
            help="Clientes contactados por cualquier vía en el ciclo activo: WA masivo, Email o gestión directa (llamada/visita)",
        )
    with col2:
        st.metric(
            label="💬 Gestionados",
            value=f"{gestionados:,}",
            help="Clientes del ciclo activo a los que el gestor registró un resultado de cobranza",
        )
    with col3:
        st.metric(
            label="Cobertura en gestión",
            value=_fmt_pct(cobertura_pct),
            help="% de la cartera activa que fue alcanzada (excluye especiales con trato directo)",
        )
    with col4:
        st.metric(
            label="Tasa de gestión",
            value=_fmt_pct(tasa_gestion),
            help="% de los alcanzados que ya tienen un resultado registrado por el gestor",
        )
    with col5:
        st.metric(
            label="Tasa de recuperación",
            value=_fmt_pct(tasa_recuper),
            help="% de gestiones con resultado EXITOSO (acordó pagar) sobre el total gestionado",
        )


# ---------------------------------------------------------------------------
# [C] Canal de Notificaciones
# ---------------------------------------------------------------------------

def _render_canal_notificaciones(kpis: Dict[str, Any]) -> None:
    """Bloque C: Desglose compacto de mensajes enviados por canal."""
    if not kpis:
        return

    notif_wa    = kpis.get("notificaciones_wa", 0)
    notif_email = kpis.get("notificaciones_email", 0)
    total       = notif_wa + notif_email
    tasa_entrega = kpis.get("tasa_notif_exitosa_pct", 0.0)

    st.markdown(
        "<div style='background:#F8FAFC;border:1px solid #D9E2EC;border-radius:8px;"
        "padding:10px 20px;display:flex;gap:32px;align-items:center;flex-wrap:wrap;"
        "margin-bottom:4px;font-size:0.9rem;'>"
        f"<span>📱 <b>WA enviados:</b> {notif_wa}</span>"
        f"<span>📧 <b>Email enviados:</b> {notif_email}</span>"
        f"<span>📨 <b>Total mensajes:</b> {total}</span>"
        f"<span style='color:#2B8A3E;'>✔ <b>Tasa de entrega:</b> {tasa_entrega:.1f}%</span>"
        "</div>",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# [D] Proceso de Cobranza (antes "Funnel")
# ---------------------------------------------------------------------------

def _render_funnel(funnel: Dict[str, int]) -> None:
    """Bloque D: Proceso de cobranza — etapas del ciclo activo."""
    st.markdown("### 🔄 Proceso de Cobranza")

    if not funnel:
        st.info("Sin datos para el ciclo activo.")
        return

    cartera       = funnel.get("cartera", 0)
    cartera_total = funnel.get("cartera_total", cartera)
    especiales    = max(cartera_total - cartera, 0)
    notif_wa      = funnel.get("notificados_wa", 0)
    notif_email   = funnel.get("notificados_email", 0)
    contacto_dir  = funnel.get("contacto_directo", 0)
    alcanzados    = funnel.get("alcanzados", notif_wa + notif_email)
    sin_contactar = funnel.get("sin_contactar", max(cartera - alcanzados, 0))
    con_resultado = funnel.get("con_respuesta", 0)
    pendientes    = funnel.get("pendientes_seg", max(alcanzados - con_resultado, 0))
    comprometidos = funnel.get("recuperados", 0)
    con_acuerdo   = funnel.get("con_acuerdo", 0)

    # Base del embudo: cartera_total si hay especiales, cartera si todos son notificables.
    # Así la barra de progreso cuenta la historia completa desde el universo financiero real.
    base = cartera_total if cartera_total > cartera else cartera

    def pct(parte: int) -> float:
        return round(parte / base * 100, 1) if base > 0 else 0.0

    # Filas contextuales de cartera total — solo se muestran cuando hay clientes especiales
    rows = []
    if especiales > 0:
        rows += [
            {"Etapa":      "🏢 Toda la cartera del ciclo",
             "Clientes":   cartera_total,
             "% del total": pct(cartera_total)},
            {"Etapa":      "  ↳ ⭐ Clientes especiales (trato directo · no notificar)",
             "Clientes":   especiales,
             "% del total": pct(especiales)},
        ]

    # Pirámide de cobertura: cartera → cómo llegamos → qué resultados
    # Filas del proceso de cobranza — diseño adaptativo:
    # Las filas de alerta gritan cuando hay problema y desaparecen cuando todo está bien.
    # Las filas informativas solo se muestran si aportan valor (valor > 0).

    # -- Cartera base — siempre visible --
    rows.append({"Etapa": "📋 Cartera activa del ciclo",
                 "Clientes": cartera, "% del total": pct(cartera)})

    # -- Cobertura: cómo llegamos a ellos --
    # Notificados WA solo si se enviaron WA masivos
    if notif_wa > 0:
        rows.append({"Etapa": "📱 Notificados por WhatsApp",
                     "Clientes": notif_wa, "% del total": pct(notif_wa)})
    # Notificados Email solo si se enviaron emails
    if notif_email > 0:
        rows.append({"Etapa": "📧 Notificados por Email",
                     "Clientes": notif_email, "% del total": pct(notif_email)})
    # Gestión directa — solo si el gestor hizo trabajo proactivo.
    # Opción B: desglose en paréntesis "X llamadas · Y visitas · Z notas"
    if contacto_dir > 0:
        _llamadas = funnel.get("llamadas_dir", 0)
        _visitas  = funnel.get("visitas_dir", 0)
        _notas    = funnel.get("notas_dir", 0)
        _otros    = funnel.get("otros_dir", 0)
        _partes = []
        if _llamadas: _partes.append(f"{_llamadas} {'llamada' if _llamadas == 1 else 'llamadas'}")
        if _visitas:  _partes.append(f"{_visitas} {'visita' if _visitas == 1 else 'visitas'}")
        if _notas:    _partes.append(f"{_notas} {'nota' if _notas == 1 else 'notas'}")
        if _otros:    _partes.append(f"{_otros} {'otro' if _otros == 1 else 'otros'}")
        _detalle = f" ({' · '.join(_partes)})" if _partes else ""
        rows.append({"Etapa": f"📞 Con gestión directa{_detalle}",
                     "Clientes": contacto_dir, "% del total": pct(contacto_dir)})

    # Total alcanzados — siempre visible (métrica principal de cobertura)
    rows.append({"Etapa": "🎯 Total alcanzados (únicos)",
                 "Clientes": alcanzados, "% del total": pct(alcanzados)})

    # Sin contacto — siempre visible: es la ALERTA CRÍTICA del gerente
    # Cuando es 0, confirma cobertura total. Cuando es > 0, requiere acción inmediata.
    alerta_sin_contacto = "❌ Sin ningún contacto — REQUIERE ACCIÓN" if sin_contactar > 0 else "✅ Sin contacto: 0 (cobertura completa)"
    rows.append({"Etapa": alerta_sin_contacto,
                 "Clientes": sin_contactar, "% del total": pct(sin_contactar)})

    # -- Profundidad: qué resultados tenemos --
    rows.append({"Etapa": "💬 Con resultado registrado",
                 "Clientes": con_resultado, "% del total": pct(con_resultado)})

    # Pendientes solo si hay clientes sin resultado aún (lista de trabajo del gestor)
    if pendientes > 0:
        rows.append({"Etapa": "⏳ Pendientes de seguimiento",
                     "Clientes": pendientes, "% del total": pct(pendientes)})

    # Comprometidos solo si hay compromisos registrados
    if comprometidos > 0:
        rows.append({"Etapa": "  ↳ ✅ Comprometidos a pagar",
                     "Clientes": comprometidos, "% del total": pct(comprometidos)})

    # Acuerdos de pago solo si hay acuerdos activos
    if con_acuerdo > 0:
        rows.append({"Etapa": "🤝 Con acuerdo de pago activo",
                     "Clientes": con_acuerdo, "% del total": pct(con_acuerdo)})

    df = pd.DataFrame(rows)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Clientes":    st.column_config.NumberColumn("Clientes", format="%d"),
            "% del total": st.column_config.ProgressColumn(
                "% del total",
                min_value=0,
                max_value=100,
                format="%.1f%%",
                help="Porcentaje sobre la cartera total del ciclo (incluye especiales)" if especiales > 0
                     else "Porcentaje sobre la cartera activa del ciclo",
            ),
        },
    )


# ---------------------------------------------------------------------------
# [E] ¿Qué respondieron? (antes "Distribución de Resultados")
# ---------------------------------------------------------------------------

def _render_distribucion_resultados(kpis: Dict[str, Any]) -> None:
    """Bloque E: Distribución de resultados de gestión registrados por el gestor."""
    by_resultado = kpis.get("by_resultado", {})
    if not by_resultado:
        return

    st.markdown("### 📊 ¿Qué respondieron los clientes?")
    st.caption("Resultados registrados manualmente por el gestor en el período seleccionado · No incluye envíos automáticos")

    rows = [
        {"Respuesta del cliente": _resultado_label(k), "Cantidad": v}
        for k, v in sorted(by_resultado.items(), key=lambda x: -x[1])
    ]
    df = pd.DataFrame(rows)
    total = df["Cantidad"].sum()
    df["% del total"] = df["Cantidad"].apply(lambda x: round(x / total * 100, 1) if total > 0 else 0.0)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "% del total": st.column_config.ProgressColumn(
                "% del total",
                min_value=0,
                max_value=100,
                format="%.1f%%",
            ),
        },
    )


# ---------------------------------------------------------------------------
# [F] Efectividad por Plantilla WhatsApp
# ---------------------------------------------------------------------------

def _render_efectividad_plantillas(plantillas: List[Dict[str, Any]]) -> None:
    """Bloque F: Efectividad por plantilla WhatsApp."""
    st.markdown("### 📋 Efectividad por Plantilla WhatsApp")
    st.caption("¿Qué mensaje generó más compromisos de pago?")

    if not plantillas:
        st.info("Sin datos de plantillas para el ciclo seleccionado.")
        return

    df = pd.DataFrame(plantillas)
    df = df.rename(columns={
        "plantilla":      "Plantilla",
        "total_enviados": "Enviados",
        "exitosos":       "Comprometidos",
        "tasa_pct":       "Tasa éxito (%)",
    })

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Tasa éxito (%)": st.column_config.ProgressColumn(
                "Tasa éxito (%)",
                min_value=0,
                max_value=100,
                format="%.1f%%",
            ),
            "Enviados":      st.column_config.NumberColumn(format="%d"),
            "Comprometidos": st.column_config.NumberColumn(
                format="%d",
                help="Clientes que respondieron con resultado EXITOSO tras recibir esta plantilla",
            ),
        },
    )


# ---------------------------------------------------------------------------
# [G] Top Clientes por Saldo Pendiente
# ---------------------------------------------------------------------------

def _categoria_riesgo(dias: int, gestiones: int) -> str:
    """Categoría de riesgo operativa para cobranza B2B."""
    if dias >= 90:
        return "🔴 CRÍTICO"
    if dias >= 60:
        return "🟠 ALTO"
    if dias >= 30:
        return "🟡 MEDIO"
    return "🟢 BAJO"


def _accion_sugerida(dias: int, gestiones: int, ultimo: str) -> str:
    """Acción de cobranza recomendada según el perfil del cliente."""
    if dias >= 90 and gestiones == 0:
        return "⚖️ Derivar a Legal"
    if dias >= 60 and gestiones == 0:
        return "📞 Llamada URGENTE"
    if dias >= 30 and gestiones == 0:
        return "📱 Primer contacto WA"
    if ultimo == "SIN_RESPUESTA":
        return "📞 Llamada directa"
    if ultimo == "PROMESA_PAGO":
        return "🔄 Verificar pago"
    if ultimo in ("SOLICITO_PLAZO", "EN_NEGOCIACION"):
        return "🤝 Continuar negociación"
    if ultimo == "EXITOSO":
        return "✅ Confirmar recepción"
    if ultimo == "ESCALAR_LEGAL":
        return "⚖️ Actualizar Legal"
    return "📋 Seguimiento"


def _fmt_fecha_gestion(fecha_str: str) -> str:
    """Convierte timestamp ISO a 'dd/mm/yy' o '—' si está vacío."""
    if not fecha_str:
        return "—"
    try:
        dt = datetime.fromisoformat(fecha_str.replace("Z", "+00:00"))
        return dt.strftime("%d/%m/%y")
    except Exception:
        return "—"


def _render_top_clientes(criticos: List[Dict[str, Any]]) -> None:
    """Bloque G: Ranking ejecutivo de clientes críticos."""
    st.markdown("### 🔴 Top Clientes por Saldo Pendiente")

    if not criticos:
        st.info("Sin datos de clientes para el ciclo seleccionado.")
        return

    # --- Selector de perspectiva ---
    vista = st.radio(
        "Perspectiva",
        options=["📊 Vista financiera — toda la cartera", "🎯 Vista operativa — solo en gestión"],
        index=0,
        horizontal=True,
        key="dash_top_clientes_vista",
        label_visibility="collapsed",
    )
    solo_notificables = "operativa" in vista

    # Filtrado según perspectiva
    criticos_vista = (
        [c for c in criticos if not c.get("es_especial")]
        if solo_notificables else criticos
    )

    if not criticos_vista:
        st.info("Sin clientes notificables para el ciclo seleccionado.")
        return

    # --- Metric cards ---
    total_sol      = sum(float(c.get("saldo_sol", 0)) for c in criticos_vista)
    total_usd      = sum(float(c.get("saldo_usd", 0)) for c in criticos_vista)
    # "Sin gestionar" excluye especiales en AMBAS vistas — ellos nunca se gestionan vía sistema
    sin_gestion    = sum(
        1 for c in criticos_vista
        if int(c.get("gestiones_count", 0)) == 0 and not c.get("es_especial")
    )
    criticos_count = sum(1 for c in criticos_vista if int(c.get("dias_mora_max", 0)) >= 90)
    n              = len(criticos_vista)

    mk1, mk2, mk3, mk4 = st.columns(4)
    mk1.metric(
        label="💰 Saldo S/ en riesgo",
        value=_fmt_moneda(total_sol),
        help="Suma de saldo pendiente en Soles de los clientes mostrados",
    )
    mk2.metric(
        label="💵 Saldo US$ en riesgo",
        value=f"US$ {total_usd:,.2f}",
        help="Suma de saldo pendiente en Dólares de los clientes mostrados",
    )
    mk3.metric(
        label="🚫 Sin gestionar",
        value=f"{sin_gestion} clientes",
        help=f"{sin_gestion} de {n} del top no tienen ningún contacto registrado en este ciclo ({round(sin_gestion / n * 100) if n else 0}%)",
    )
    mk4.metric(
        label="🔴 Mora > 90 días",
        value=str(criticos_count),
        help="Clientes con mora crítica — candidatos prioritarios para acción legal",
        delta_color="inverse",
    )

    st.markdown("<br>", unsafe_allow_html=True)

    rows = []
    for i, c in enumerate(criticos_vista, start=1):
        saldo_sol   = float(c.get("saldo_sol", 0))
        saldo_usd   = float(c.get("saldo_usd", 0))
        mora        = int(c.get("dias_mora_max", 0))
        gestiones   = int(c.get("gestiones_count", 0))
        ultimo      = c.get("ultimo_resultado", "SIN_GESTION")
        fecha_ult   = _fmt_fecha_gestion(c.get("fecha_ultimo_gestion", ""))
        pct         = round(saldo_sol / total_sol * 100, 1) if total_sol > 0 else 0.0
        es_especial = c.get("es_especial", False)

        _mora_emoji = "🔴" if mora >= 90 else "🟠" if mora >= 60 else "🟡" if mora >= 30 else "🟢"

        row: Dict[str, Any] = {
            "#":       i,
            "Cliente": c.get("nombre", c.get("cliente_id", "—")),
        }
        # Columna "Tipo" solo en Vista financiera (en operativa todos son estándar — la columna es ruido)
        if not solo_notificables:
            row["Tipo"] = "⭐ Especial" if es_especial else "Estándar"
        row.update({
            "Saldo S/":       saldo_sol,
            "Saldo US$":      saldo_usd,
            "% top S/":       pct,
            "Mora":           f"{_mora_emoji} {mora}d",
            "Gestiones":      gestiones,
            "Contacto":       fecha_ult,
            "Próxima acción": "— Trato directo" if es_especial else _accion_sugerida(mora, gestiones, ultimo),
        })
        rows.append(row)

    df = pd.DataFrame(rows)

    col_cfg: Dict[str, Any] = {
        "#": st.column_config.NumberColumn("#", format="%d", width="small"),
        "Saldo S/": st.column_config.NumberColumn(
            "Saldo S/", format="S/ %.2f",
            help="Saldo pendiente en Soles (excluye DSP y PAV)",
        ),
        "Saldo US$": st.column_config.NumberColumn(
            "Saldo US$", format="$ %.2f",
            help="Saldo pendiente en Dólares",
        ),
        "% top S/": st.column_config.ProgressColumn(
            "% top S/",
            min_value=0,
            max_value=100,
            format="%.1f%%",
            help="Peso del cliente en el ranking por saldo en Soles",
        ),
        "Gestiones": st.column_config.NumberColumn(
            "Gestor.", format="%d", width="small",
            help="Gestiones manuales registradas por el gestor en este ciclo",
        ),
        "Contacto": st.column_config.TextColumn(
            "Contacto", width="small",
            help="Fecha del último contacto registrado (dd/mm/aa)",
        ),
    }
    if not solo_notificables:
        col_cfg["Tipo"] = st.column_config.TextColumn(
            "Tipo", width="small",
            help="Estándar = incluido en KPIs · ⭐ Especial = trato directo, excluido del Proceso de Cobranza",
        )

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        height=min(36 * len(rows) + 38, 540),
        column_config=col_cfg,
    )

    st.caption(
        f"Mostrando **{n} clientes** · "
        f"Saldo S/: **{_fmt_moneda(total_sol)}** · "
        f"Saldo US$: **US$ {total_usd:,.2f}** · "
        f"**{sin_gestion}** sin contactar · "
        f"**{criticos_count}** en mora crítica · "
        f"Excluye tipos de pedido: DSP, PAV"
    )


# ---------------------------------------------------------------------------
# Punto de entrada del tab
# ---------------------------------------------------------------------------

def render_tab(df_final: Any, config: Dict[str, Any]) -> None:
    """Render del tab Dashboard de Efectividad.

    Args:
        df_final: SSOT de cartera (solo lectura — no se modifica).
        config: CONFIG global de la app.
    """
    st.markdown("## 📊 Dashboard de Efectividad de Cobranza")
    st.caption("Visibilidad en tiempo real para supervisores y directivos · Solo lectura")

    st.markdown("---")

    # Selector de período
    date_from, date_to, cycle_id = _render_selector_periodo()

    st.markdown("---")

    # Carga de datos con spinner
    with st.spinner("Cargando indicadores..."):
        kpis      = dbm.get_kpis_periodo(date_from, date_to)
        funnel    = dbm.get_funnel_cobranza(cycle_id)
        plantillas = dbm.get_efectividad_por_plantilla(cycle_id)
        criticos  = dbm.get_top_clientes_criticos(n=15, cycle_id=cycle_id)

    # [A] Header del ciclo — contexto financiero en una línea
    _render_header_ciclo(cycle_id, criticos, funnel)

    st.markdown("---")

    # [B] KPIs Ejecutivos — 5 métricas de negocio
    _render_kpis_principales(kpis, funnel)

    # [C] Canal de Notificaciones — desglose compacto debajo de los KPIs
    st.markdown("")
    _render_canal_notificaciones(kpis)

    st.markdown("---")

    # [D] Proceso de Cobranza + [E] ¿Qué respondieron? — lado a lado
    col_proceso, col_resp = st.columns([1, 1])
    with col_proceso:
        _render_funnel(funnel)
    with col_resp:
        _render_distribucion_resultados(kpis)

    st.markdown("---")

    # [F] Efectividad por Plantilla
    _render_efectividad_plantillas(plantillas)

    st.markdown("---")

    # [G] Top Clientes Críticos
    _render_top_clientes(criticos)

    st.markdown("---")
    st.caption(
        f"Datos al {datetime.now().strftime('%d/%m/%Y %H:%M')} · "
        "Período: " + date_from + " → " + date_to
    )
