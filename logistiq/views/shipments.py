# -*- coding: utf-8 -*-
"""My Shipments drawer — add + view shipment details."""
import time
from datetime import datetime

import streamlit as st
import plotly.graph_objects as go

from logistiq.data import demo_responses
from logistiq.components import cards as K, charts as C
from logistiq.utils.data import (
    get_real_weather, get_live_exchange_rate, resolve_city_coords,
    cargo_insurance_cost, sla_breach_predictor,
)
from logistiq.utils.gemini import analyze_shipment_risk, get_live_intelligence
from logistiq.utils.firebase import firebase_write

CARGO_TYPES = [
    ("🔩", "Auto Parts"),
    ("💻", "Electronics"),
    ("💊", "Pharmaceuticals"),
    ("🌾", "Food/Perishable"),
    ("⚙️", "Industrial Equipment"),
    ("🧪", "Chemicals"),
    ("👗", "Textiles"),
    ("📦", "General Merchandise"),
]

TRANSPORT_MODES = [
    ("🚢", "Sea (Vessel)"),
    ("🚂", "Rail"),
    ("🚛", "Road (Truck)"),
    ("✈️", "Air"),
    ("🚢🚂", "Sea + Rail"),
    ("🚢🚛", "Sea + Road"),
]


def render_add_form():
    """Add Shipment — shown as the main panel when show_add_form is True."""
    st.markdown("### ➕ Add Shipment")
    st.caption("Fill in shipment details — Gemini AI will run live risk analysis")

    # Section 1: What
    st.markdown("**1. What are you shipping?**")
    cols = st.columns(4)
    if "selected_cargo" not in st.session_state:
        st.session_state.selected_cargo = "Auto Parts"
    for i, (icon, label) in enumerate(CARGO_TYPES):
        with cols[i % 4]:
            selected = st.session_state.selected_cargo == label
            if st.button(f"{icon}\n{label}", key=f"cargo_{i}",
                         use_container_width=True,
                         type="primary" if selected else "secondary"):
                st.session_state.selected_cargo = label
                st.rerun()

    cargo_type = st.session_state.selected_cargo
    cargo_desc = st.text_input("Description", placeholder="e.g. 4,200 engine blocks for Maruti Suzuki Manesar")

    wt_col, val_col = st.columns(2)
    weight_tons = wt_col.number_input("Weight (tons)", 0.1, 50000.0, 100.0)
    value_crore = val_col.number_input("Value (₹ Crore)", 0.1, 5000.0, 10.0, step=0.1)

    # Section 2: Where and when
    st.markdown("**2. Where and when?**")
    oc, dc = st.columns(2)
    origin      = oc.text_input("Origin", placeholder="e.g. Chennai Port")
    destination = dc.text_input("Destination", placeholder="e.g. Manesar Plant")
    d1c, d2c = st.columns(2)
    departure_date = d1c.date_input("Departure Date")
    deadline_date  = d2c.date_input("Must Arrive By")
    consignee = st.text_input("Consignee", placeholder="e.g. Maruti Suzuki India Ltd")

    # Transport mode
    st.markdown("**Transport Mode**")
    mode_cols = st.columns(len(TRANSPORT_MODES))
    if "selected_mode" not in st.session_state:
        st.session_state.selected_mode = "Sea (Vessel)"
    for i, (icon, label) in enumerate(TRANSPORT_MODES):
        with mode_cols[i]:
            selected = st.session_state.selected_mode == label
            short = label.split(" ")[0]
            if st.button(f"{icon}\n{short}", key=f"mode_{i}",
                         use_container_width=True,
                         type="primary" if selected else "secondary"):
                st.session_state.selected_mode = label
                st.rerun()
    transport_mode = st.session_state.selected_mode

    # Section 3: Special requirements
    st.markdown("**3. Special Requirements**")
    special_reqs = st.multiselect(
        "Tags",
        ["Cold Chain (Refrigerated)", "Hazmat Declaration Required",
         "Oversized / Heavy Lift", "Fragile", "Priority / Express"],
        label_visibility="collapsed",
    )

    # Vessel details
    if "Sea" in transport_mode:
        v1, v2 = st.columns(2)
        vessel_name  = v1.text_input("Vessel Name", placeholder="e.g. MV Chennai Star")
        vessel_draft = v2.number_input("Vessel Draft (m)", 5.0, 25.0, 12.0, step=0.1)
    else:
        vessel_name, vessel_draft = "", 0.0

    # ── Submit ─────────────────────────────────────────
    st.markdown("---")
    s_col, c_col = st.columns(2)
    submitted = s_col.button("🔍 Analyze Risk →", type="primary", use_container_width=True)
    cancelled = c_col.button("Cancel", use_container_width=True)

    if cancelled:
        st.session_state.show_add_form = False
        st.rerun()

    if submitted:
        shipment = {
            "id":              f"SHP-{int(time.time())}",
            "cargo_type":      cargo_type,
            "cargo_desc":      cargo_desc or f"{cargo_type} shipment",
            "transport_mode":  transport_mode,
            "value_crore":     value_crore,
            "weight_tons":     weight_tons,
            "origin":          origin,
            "destination":     destination,
            "departure_date":  str(departure_date),
            "deadline_date":   str(deadline_date),
            "consignee":       consignee,
            "special_reqs":    special_reqs,
            "vessel_name":     vessel_name,
            "vessel_draft":    vessel_draft,
            "added_at":        datetime.now().isoformat(),
            "risk_analyzed":   False,
            "risk_data":       None,
            "weather_data":    None,
        }

        # Live progress
        progress_placeholder = st.empty()
        steps = [
            ("💱", "Fetching live USD/INR exchange rate…"),
            ("🌤", f"Fetching real-time weather at {destination or 'destination'}…"),
            ("🌐", "Calling Gemini with Google Search Grounding for live intel…"),
            ("🤖", "Running Gemini 1.5 Pro risk analysis…"),
            ("✅", "Analysis complete!"),
        ]
        results = []
        for i, (icon, msg) in enumerate(steps):
            step_html = ""
            for j, (ic, m) in enumerate(steps[:i+1]):
                done = j < i
                spin = "⏳" if j == i else "✅"
                step_html += f"<div class='sim-step'><span class='step-check'>{spin if not done else '✅'}</span> {ic} {m}</div>"
            progress_placeholder.markdown(f"<div class='glass-card'>{step_html}</div>", unsafe_allow_html=True)

            if i == 0:
                rate = get_live_exchange_rate()
                results.append(rate)
            elif i == 1:
                coords = resolve_city_coords(destination)
                weather = get_real_weather(coords[0], coords[1], destination)
                shipment["weather_data"] = weather
                results.append(weather)
            elif i == 2:
                intel = get_live_intelligence(
                    f"Current shipping conditions: {origin} to {destination} India. Any disruptions today."
                )
                shipment["live_intel"] = intel
                results.append(intel)
            elif i == 3:
                risk = analyze_shipment_risk(shipment, results[1], results[0], results[2])
                shipment["risk_data"] = risk
                shipment["risk_analyzed"] = True
                shipment["exchange_rate"] = results[0]
                # SLA + insurance
                deadline_h = 96.0
                eta_h = float(risk.get("estimated_delay_hours", 0)) + 24.0
                shipment["sla"] = sla_breach_predictor(deadline_h, eta_h)
                shipment["insurance_cost_lakh"] = cargo_insurance_cost(
                    risk.get("risk_score", 45), value_crore
                )
                results.append(risk)

        # Done
        progress_placeholder.empty()
        st.session_state.shipments.append(shipment)
        st.session_state.show_add_form = False
        firebase_write(f"/shipments/{shipment['id']}", shipment)
        level = (shipment.get("risk_data") or {}).get("risk_level", "Unknown")
        st.success(f"✅ Shipment added. Risk Level: **{level}**")
        st.rerun()


def render_shipment_list():
    """Compact shipment cards for sidebar."""
    shipments = st.session_state.shipments
    if not shipments:
        K.empty_state("📦", "No shipments", "Add one via '+ Add Shipment'")
        return

    for idx, s in enumerate(shipments):
        risk = s.get("risk_data") or {}
        level = risk.get("risk_level", "Unknown")
        level_colors = {"Critical": "#f87171", "High": "#fbbf24", "Medium": "#60a5fa", "Low": "#4ade80"}
        color = level_colors.get(level, "#94a3b8")
        mode_icons = {"Sea (Vessel)": "🚢", "Rail": "🚂", "Road (Truck)": "🚛", "Air": "✈️"}
        mode_icon = next((v for k, v in mode_icons.items() if k in s.get("transport_mode", "")), "📦")

        st.markdown(f"""
<div class='shipment-list-card' style='border-left:3px solid {color}'>
  <span style='font-size:18px'>{mode_icon}</span>
  <div style='flex:1;min-width:0'>
    <div class='card-title' style='white-space:nowrap;overflow:hidden;text-overflow:ellipsis'>{s.get('id','')}</div>
    <div class='card-sub'>→ {s.get('destination','')[:20]}</div>
  </div>
  <span class='badge' style='background:rgba(0,0,0,0.5);color:{color};border:1px solid {color}55;white-space:nowrap'>{level}</span>
</div>""", unsafe_allow_html=True)


def render_shipment_detail(s: dict):
    """Full shipment detail panel."""
    risk    = s.get("risk_data") or {}
    weather = s.get("weather_data") or {}
    level   = risk.get("risk_level", "Unknown")
    score   = risk.get("risk_score", 0)
    colors  = {"Critical": "#f87171", "High": "#fbbf24", "Medium": "#60a5fa", "Low": "#4ade80"}
    color   = colors.get(level, "#94a3b8")

    g1, g2 = st.columns([1, 2])
    with g1:
        fig = C.risk_gauge(score)
        st.plotly_chart(fig, use_container_width=True, key=f"det_gauge_{s.get('id')}")
    with g2:
        st.markdown(f"**{s.get('cargo_desc','')}**")
        st.markdown(f"`{s.get('origin','')}` → `{s.get('destination','')}`")
        st.caption(f"Mode: {s.get('transport_mode','')} | {s.get('weight_tons','')}t | ₹{s.get('value_crore','')}Cr")
        st.markdown(f"<span style='color:{color}'>⚠ {risk.get('primary_risk','')}</span>", unsafe_allow_html=True)

    with st.expander("📊 Full Risk Analysis", expanded=True):
        r1, r2, r3 = st.columns(3)
        r1.metric("Weather Risk",      risk.get("weather_risk",      "N/A"))
        r2.metric("Geopolitical Risk", risk.get("geopolitical_risk", "N/A"))
        r3.metric("Operational Risk",  risk.get("operational_risk",  "N/A"))

        st.markdown(f"**Est. delay:** {risk.get('estimated_delay_hours',0)} hrs")
        st.markdown(f"**Financial impact:** ₹{risk.get('financial_impact_inr',0):,}")
        st.markdown(f"**Recommendation:** {risk.get('recommendation','')}")

        if s.get("sla"):
            sla = s["sla"]
            breach_c = "#f87171" if sla.get("breach") else "#4ade80"
            st.markdown(f"**SLA Status:** <span style='color:{breach_c}'>{'⚠ BREACH RISK' if sla.get('breach') else '✅ On Track'}</span> — Buffer: {sla.get('buffer_hours',0)} hrs", unsafe_allow_html=True)
            if sla.get("penalty_lakh"):
                st.markdown(f"**Penalty exposure:** ₹{sla['penalty_lakh']}L")

        if s.get("insurance_cost_lakh"):
            st.markdown(f"**Cargo insurance estimate:** ₹{s['insurance_cost_lakh']}L")

        for issue in risk.get("detected_issues", []):
            st.markdown(f"- ⚠ {issue}")

        if s.get("live_intel"):
            st.markdown(f"<div class='intel-box'>{s['live_intel']}</div>", unsafe_allow_html=True)

    with st.expander("🌤 Weather at Destination"):
        cond = weather.get("condition", "N/A")
        wind = weather.get("wind_kph", "N/A")
        temp = weather.get("temp_c", "N/A")
        st.markdown(f"**{cond}** | 🌡 {temp}°C | 💨 {wind} kph")
        if weather.get("alerts"):
            for a in weather["alerts"]:
                st.warning(f"🚨 {a}")
