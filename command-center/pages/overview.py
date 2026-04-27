# -*- coding: utf-8 -*-
"""Overview Dashboard — KPIs, Risk Matrix, Map, Alerts Feed."""

import streamlit as st
from datetime import datetime

from components.maps import render_overview_map
from components.charts import risk_matrix_chart
from components.cards import metric_card, alert_card, empty_state


def render(vessels, ports, trucks, rail):
    """Render the full Overview dashboard."""
    shipments_list = st.session_state.get("shipments", [])
    if not st.session_state.get("dismiss_risk_banner", False) and shipments_list:
        curr_hash = hash(str([(s.get('id'), s.get('risk_analyzed')) for s in shipments_list]))
        if st.session_state.get("banner_shipment_hash") != curr_hash:
            try:
                from utils.gemini import cached_gemini_call
                shipment_subset = [{"id": s.get("id"), "cargo": s.get("cargo_desc"), "risk_data": s.get("risk_data")} for s in shipments_list]
                prompt = f"Given these shipments: {shipment_subset}. Return JSON with up to top 3 at-risk shipments. Format: {{\"at_risk\": [{{\"id\": \"...\", \"reason\": \"...\", \"delay_hrs\": ...}}]}}"
                res = cached_gemini_call(prompt, response_mime_type="application/json")
                import json
                data = json.loads(res)
                st.session_state.at_risk_banner_data = data.get("at_risk", [])
            except Exception:
                st.session_state.at_risk_banner_data = []
            st.session_state.banner_shipment_hash = curr_hash

        banner_data = st.session_state.get("at_risk_banner_data", [])
        if banner_data:
            with st.container(border=True):
                st.markdown("#### 🚨 AI Alert: Top At-Risk Shipments")
                cols = st.columns(len(banner_data) + 1)
                for i, r in enumerate(banner_data):
                    with cols[i]:
                        st.markdown(f"**{r.get('id')}**\n\n*{r.get('reason')}*\n\n**Predicted Delay:** {r.get('delay_hrs')} hrs")
                        if st.button("🗺️ View Journey", key=f"btn_journey_banner_{r.get('id')}", use_container_width=True):
                            shp = next((s for s in shipments_list if s.get('id') == r.get('id')), None)
                            if shp:
                                st.session_state.selected_shipment = shp
                                st.session_state.active_page = "journey"
                                st.query_params["p"] = "journey"
                                st.rerun()
                with cols[-1]:
                    if st.button("✖ Dismiss", key="dismiss_banner", use_container_width=True):
                        st.session_state.dismiss_risk_banner = True
                        st.rerun()

    # Full-width interactive map
    render_overview_map(
        vessels, ports, trucks,
        cyclone_on=st.session_state.get("cyclone_triggered", False),
        reroute_on=st.session_state.get("reroute_accepted", False),
        height=480,
    )

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # 3-column layout below map
    col_kpi, col_matrix, col_alerts = st.columns([1.2, 2, 1.3], gap="medium")

    with col_kpi:
        st.markdown("#### 📊 Key Metrics")
        _render_kpis()

    with col_matrix:
        st.markdown("#### 🎯 Live Risk Matrix")
        _render_risk_matrix()

    with col_alerts:
        st.markdown("#### 🔔 Live Alerts")
        _render_alerts_feed()


def _render_kpis():
    """KPI cards with state-aware values."""
    cyclone = st.session_state.get("cyclone_triggered", False)
    rerouted = st.session_state.get("reroute_accepted", False)
    n_shipments = len(st.session_state.get("shipments", []))

    if not cyclone:
        metric_card("Active Vessels", "3", "All monitored", "🚢", "#44c5ff")
        metric_card("At-Risk", "1", "MV Chennai Star", "⚠", "#fbbf24")
        metric_card("Financial Exposure", "₹47.3 Cr", "1 vessel", "💰", "#FF6B35")
        metric_card("SLA Breach Risk", "LOW", "Stable", "🛡", "#4ade80")
    elif not rerouted:
        metric_card("Active Vessels", "3", "2 at risk", "🚢", "#f87171")
        metric_card("At-Risk", "3", "+2 critical", "⚠", "#f87171")
        metric_card("Financial Exposure", "₹127.6 Cr", "+₹80.3 Cr", "💰", "#f87171")
        metric_card("SLA Breach Risk", "CRITICAL", "3 clients", "🛡", "#f87171")
    else:
        metric_card("Active Vessels", "3", "Reroute active", "🚢", "#4ade80")
        metric_card("At-Risk", "1", "Managed", "⚠", "#60a5fa")
        metric_card("Net Savings", "₹8.84 Cr", "Cascade executed", "💰", "#4ade80")
        metric_card("SLA Breach Risk", "MANAGED", "Line safe", "🛡", "#4ade80")

    if n_shipments:
        metric_card("My Shipments", str(n_shipments), "Tracked", "📦", "#a78bfa")


def _render_risk_matrix():
    """Risk matrix scatter chart for all tracked shipments."""
    shipments = st.session_state.get("shipments", [])

    # Add demo vessels as pseudo-shipments for the matrix
    demo_shipments = [
        {"id": "VSL-001", "cargo_desc": "MV Chennai Star — Engine Blocks", "value_crore": 47.3,
         "weight_tons": 1120, "origin": "Chennai", "destination": "Manesar",
         "risk_data": {"risk_score": 72, "risk_level": "High"}},
        {"id": "VSL-002", "cargo_desc": "MV Coromandel Wave — Auto Parts", "value_crore": 28.5,
         "weight_tons": 860, "origin": "Chennai", "destination": "Vizag",
         "risk_data": {"risk_score": 35, "risk_level": "Medium"}},
        {"id": "VSL-003", "cargo_desc": "MV Bay Runner — Machinery", "value_crore": 15.2,
         "weight_tons": 640, "origin": "Chennai", "destination": "Vizag",
         "risk_data": {"risk_score": 18, "risk_level": "Low"}},
    ]

    all_shipments = demo_shipments + shipments
    risk_matrix_chart(all_shipments)


def _render_alerts_feed():
    """Live alerts feed — newest first."""
    now = datetime.now().strftime("%H:%M IST")

    alerts = [
        ("🌀", "High", "Cyclone Mocha tracking Bay of Bengal — IMD monitoring", now),
        ("🚢", "Medium", "MV Chennai Star — tidal trap at Chennai (draft 15.2m > 14.0m limit)", now),
        ("⚓", "High", "Red Sea diversions up 23% — Houthi risk elevated", now),
        ("🚂", "Low", "SCR Train 58501 — on schedule, Platform 7B", now),
        ("🚛", "Medium", "NH16 checkpoint wait: 2.3 hrs — 3 trucks queued", now),
        ("📦", "Low", "JNPT Mumbai — congestion easing, 6.1hr avg wait", now),
    ]

    cyclone = st.session_state.get("cyclone_triggered", False)
    if cyclone:
        alerts.insert(0, ("🌀", "Critical", "CYCLONE CAT.3 — Chennai Port BLOCKED — ₹127.6Cr at risk", now))

    for icon, sev, desc, ts in alerts[:6]:
        border = "#f87171" if sev == "Critical" else "#fbbf24" if sev == "High" else "#60a5fa" if sev == "Medium" else "#4ade80"
        st.markdown(alert_card(icon, sev, desc, ts, border), unsafe_allow_html=True)

    if st.button("View All Intelligence →", key="view_all_intel", use_container_width=True):
        st.session_state.active_page = "intelligence"
        st.rerun()
