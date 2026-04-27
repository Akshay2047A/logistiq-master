# -*- coding: utf-8 -*-
"""Overview Dashboard — full-width map + KPIs + Risk Matrix + Alerts."""
import streamlit as st
from datetime import datetime

from logistiq.data import vessels_data, ports_data, trucks_data, rail_schedules_data
from logistiq.components import maps as M, charts as C, cards as K


def render():
    # ── Alerts ticker ──────────────────────────────────
    alerts = st.session_state.get("alerts", [])
    ticker_items = " &nbsp;|&nbsp; ".join(
        f"{'🔴' if a['severity']=='Critical' else '🟠' if a['severity']=='High' else '🟡'} {a['message']}"
        for a in alerts
    )
    if not ticker_items:
        ticker_items = "✅ No active disruptions on Chennai–Vizag corridor today"
    st.markdown(f"""
<div class='ticker-wrap'>
  <div class='ticker-move'><span>{ticker_items}</span></div>
</div>""", unsafe_allow_html=True)

    # ── Page header ────────────────────────────────────
    h1, h2 = st.columns([3, 1])
    with h1:
        st.markdown("<h2 style='margin:0 0 4px'>🗺 Command Overview</h2>", unsafe_allow_html=True)
        st.caption(f"Chennai–Vizag–Manesar Freight Corridor · {datetime.now().strftime('%d %b %Y, %H:%M IST')}")
    with h2:
        if st.button("🌀 Run Simulation", use_container_width=True, type="primary"):
            st.query_params["p"] = "simulation"
            st.session_state.active_page = "simulation"
            st.rerun()

    # ── KPI row (top) ──────────────────────────────────
    shipments_list = st.session_state.shipments
    at_risk   = sum(1 for s in shipments_list if (s.get("risk_data") or {}).get("risk_level") in ("High", "Critical"))
    exposure  = sum(float(s.get("value_crore", 0)) for s in shipments_list)
    on_time   = len(shipments_list) - at_risk
    on_pct    = int(on_time / max(len(shipments_list), 1) * 100)
    at_sea    = sum(1 for v in vessels_data if v.get("status") == "At Sea")

    k1, k2, k3, k4, k5 = st.columns(5)
    kpi_data = [
        (k1, "🚢", "Active Vessels",    str(len(vessels_data)), f"{at_sea} at sea",     True),
        (k2, "💰", "Exposure",          f"₹{exposure:.1f}Cr",   f"{at_risk} at risk",   at_risk == 0),
        (k3, "⚠️", "SLA Risk",          "MEDIUM" if at_risk else "LOW", "",              at_risk == 0),
        (k4, "✅", "On Time",           f"{on_pct}%",           f"{on_time}/{max(len(shipments_list),1)}", on_pct >= 80),
        (k5, "📦", "Shipments",         str(len(shipments_list)), "tracked",             True),
    ]
    for col, icon, label, value, delta, good in kpi_data:
        with col:
            K.render_metric_card(label, value, delta, icon, good)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── Map + Risk Matrix ──────────────────────────────
    map_col, matrix_col = st.columns([1.5, 1])

    with map_col:
        st.markdown("<div class='section-header'>🗺 Live Operational Map</div>", unsafe_allow_html=True)
        fmap = M.make_base_map()
        M.add_ports(fmap, ports_data)
        M.add_vessels(fmap, vessels_data,
                      at_risk_ids={"VSL-CHN-001"} if st.session_state.cyclone_triggered else set())
        M.add_trucks(fmap, trucks_data)
        M.add_rail_corridor(fmap, rail_schedules_data)
        if st.session_state.cyclone_triggered:
            M.add_cyclone(fmap)
        if st.session_state.reroute_accepted:
            M.add_reroute_path(fmap)
        M.render_map(fmap, height=400)

        # Map legend
        st.markdown("""
<div style='display:flex;gap:16px;flex-wrap:wrap;font-size:11px;color:#64748b;margin-top:4px'>
  <span><span style='color:#44c5ff'>●</span> Vessels</span>
  <span><span style='color:#ff5a83'>●</span> At Risk</span>
  <span><span style='color:#22c55e'>●</span> Port: Low</span>
  <span><span style='color:#f59e0b'>●</span> Port: Moderate</span>
  <span><span style='color:#ef4444'>●</span> Port: High</span>
  <span><span style='color:#fbbf24'>──</span> Rail corridor</span>
</div>""", unsafe_allow_html=True)

    with matrix_col:
        st.markdown("<div class='section-header'>🎯 Risk Matrix</div>", unsafe_allow_html=True)
        fig = C.risk_matrix_chart(shipments_list)
        st.plotly_chart(fig, use_container_width=True, key="ov_matrix")

        if not shipments_list:
            K.empty_state("📦", "No shipments yet", "Add one to see the risk matrix.")
        else:
            # Compact shipment summary
            for s in shipments_list[:3]:
                rd = s.get("risk_data") or {}
                level = rd.get("risk_level", "Unknown")
                colors = {"Critical":"#f87171","High":"#fbbf24","Medium":"#60a5fa","Low":"#4ade80"}
                c = colors.get(level, "#94a3b8")
                score = rd.get("risk_score", 0)
                st.markdown(f"""
<div style='display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid #1e293b'>
  <div style='width:32px;height:32px;border-radius:50%;background:rgba(0,0,0,0.4);
              border:2px solid {c};display:flex;align-items:center;justify-content:center;
              font-size:11px;font-weight:700;color:{c}'>{score}</div>
  <div style='flex:1;min-width:0'>
    <div style='font-size:11px;font-weight:600;color:#e7efff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis'>{s.get("cargo_desc","")[:28]}</div>
    <div style='font-size:10px;color:#64748b'>{s.get("origin","")[:12]} → {s.get("destination","")[:12]}</div>
  </div>
  {K.risk_badge(level)}
</div>""", unsafe_allow_html=True)

    # ── Alerts feed ────────────────────────────────────
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-header'>🔔 Live Alerts</div>", unsafe_allow_html=True)

    if alerts:
        ac = st.columns(min(len(alerts[:3]), 3))
        for i, a in enumerate(alerts[:3]):
            sev = a.get("severity", "Medium")
            icons = {"Critical":"🔴","High":"🟠","Medium":"🟡","Low":"🟢"}
            sev_c = {"Critical":"#f87171","High":"#fb923c","Medium":"#fbbf24","Low":"#4ade80"}
            ic = icons.get(sev, "🔵")
            col = sev_c.get(sev, "#60a5fa")
            with ac[i]:
                st.markdown(f"""
<div class='glass-card' style='border-color:{col}33;padding:14px'>
  <div style='display:flex;align-items:center;gap:6px;margin-bottom:6px'>
    <span style='font-size:18px'>{ic}</span>
    {K.risk_badge(sev)}
  </div>
  <div style='font-size:12px;color:#e7efff;line-height:1.5'>{a.get("message","")}</div>
  <div style='font-size:10px;color:#475569;margin-top:4px'>⏱ {a.get("timestamp","")}</div>
</div>""", unsafe_allow_html=True)
    else:
        K.empty_state("✅", "All Clear", "No active alerts on any corridor.")

    # ── Quick actions ──────────────────────────────
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("🌀 Cyclone Simulation", use_container_width=True):
            st.session_state.cyclone_triggered = True
            st.query_params["p"] = "simulation"
            st.session_state.active_page = "simulation"
            st.rerun()
    with c2:
        if st.button("🚢 Sea Operations", use_container_width=True):
            st.query_params["p"] = "sea"
            st.session_state.active_page = "sea"
            st.rerun()
    with c3:
        if st.button("📡 Intelligence Hub", use_container_width=True):
            st.query_params["p"] = "intelligence"
            st.session_state.active_page = "intelligence"
            st.rerun()
    with c4:
        if st.button("➕ Add Shipment", use_container_width=True, type="primary"):
            st.query_params["p"] = "add_shipment"
            st.session_state.show_add_form = True
            st.session_state.active_page = "add_shipment"
            st.rerun()
