# -*- coding: utf-8 -*-
"""Sea & Maritime Operations page."""
import streamlit as st
import plotly.graph_objects as go

from logistiq.data import vessels_data, ports_data, trucks_data, rail_schedules_data, demo_responses
from logistiq.components import maps as M, cards as K
from logistiq.utils.data import get_real_weather, vessel_fuel_cost, CITY_COORDS
from logistiq.utils.gemini import get_ai_reroute
from logistiq.utils.firebase import firebase_write


PORT_META = {
    "PRT-CHN": {"name": "Chennai Port",        "draft_limit_m": 14.0, "tidal_hours": 8,  "coords": CITY_COORDS["chennai"]},
    "PRT-VSK": {"name": "Visakhapatnam Port",  "draft_limit_m": 17.5, "tidal_hours": 22, "coords": CITY_COORDS["visakhapatnam"]},
    "PRT-KAM": {"name": "Kamarajar (Ennore)",  "draft_limit_m": 13.5, "tidal_hours": 10, "coords": CITY_COORDS["kamarajar"]},
}


def render():
    map_col, panel_col = st.columns([3, 2])

    # ── Map ────────────────────────────────────────────
    with map_col:
        st.markdown("<div class='section-header'>🌊 Maritime Operations Map</div>", unsafe_allow_html=True)
        fmap = M.make_base_map()
        M.add_ports(fmap, ports_data)
        M.add_vessels(
            fmap, vessels_data,
            at_risk_ids={"VSL-CHN-001"} if st.session_state.cyclone_triggered else set(),
        )
        # Only show vessels and sea lane — NO road trucks on maritime map
        M.add_rail_corridor(fmap, rail_schedules_data)
        if st.session_state.cyclone_triggered:
            M.add_cyclone(fmap)
        if st.session_state.reroute_accepted:
            M.add_reroute_path(fmap)
        M.render_map(fmap, height=460)

        # Vessel list
        st.markdown("#### 🚢 Active Vessels")
        for v in vessels_data:
            risk_color = "#f87171" if (st.session_state.cyclone_triggered and v["id"] == "VSL-CHN-001") else "#4ade80"
            st.markdown(f"""
<div class='glass-card' style='border-color:{risk_color}22'>
  <b style='color:{risk_color}'>{v['name']}</b>
  &nbsp;<span style='color:#94a3b8;font-size:12px'>{v['status']}</span>
  <br><span style='font-size:12px;color:#94a3b8'>
    📍 {v['lat']:.2f}°N {v['lon']:.2f}°E &nbsp;|&nbsp;
    ⚡ {v['speed_knots']} kn &nbsp;|&nbsp;
    🏷 {v['cargo_type']}
  </span>
</div>""", unsafe_allow_html=True)

    # ── Right panel ────────────────────────────────────
    with panel_col:
        tab_weather, tab_speed, tab_tidal, tab_intel = st.tabs(
            ["🌤 Weather", "⚡ Speed Optimizer", "🌊 Tidal Trap", "📡 Port Intel"]
        )

        # ── A: Port Weather ──────────────────────────
        with tab_weather:
            st.markdown("**Live Port Weather**")
            for pid, meta in PORT_META.items():
                lat, lng = meta["coords"]
                wx = get_real_weather(lat, lng, meta["name"])
                st.markdown(K.port_weather_card(
                    {"name": meta["name"]}, wx
                ), unsafe_allow_html=True)

        # ── B: Speed Optimizer ────────────────────────
        with tab_speed:
            st.markdown("**Vessel Speed Optimizer**")
            speed = st.slider("Speed (knots)", 8, 16, 12, key="speed_slider")
            voyage_h = st.number_input("Voyage duration (hrs)", 12.0, 120.0, 48.0, step=1.0, key="voyage_h")
            vessel_draft = 15.2
            port_limit = 14.0

            fc = vessel_fuel_cost(speed, voyage_h)
            eta_delta = round((12 - speed) * voyage_h / speed, 1)
            tidal_ok = vessel_draft <= port_limit

            st.markdown(f"""
<div class='glass-card'>
  <div style='display:flex;justify-content:space-between;margin-bottom:6px'>
    <span style='color:#94a3b8;font-size:12px'>Fuel cost</span>
    <b>₹{fc['cost_inr']:,}</b>
  </div>
  <div style='display:flex;justify-content:space-between;margin-bottom:6px'>
    <span style='color:#94a3b8;font-size:12px'>ETA adjustment vs 12kn</span>
    <b style='color:{"#f87171" if eta_delta>0 else "#4ade80"}'>{eta_delta:+.1f} hrs</b>
  </div>
  <div style='display:flex;justify-content:space-between;margin-bottom:6px'>
    <span style='color:#94a3b8;font-size:12px'>CO₂ emissions</span>
    <b>{fc['co2_tons']} tons</b>
  </div>
  <div style='display:flex;justify-content:space-between'>
    <span style='color:#94a3b8;font-size:12px'>Tidal window</span>
    <b style='color:{"#4ade80" if tidal_ok else "#f87171"}'>{"✅ Compatible" if tidal_ok else "❌ Draft > Limit"}</b>
  </div>
</div>""", unsafe_allow_html=True)

            if st.button("⚡ Find Optimal Speed", use_container_width=True):
                st.info("Optimal speed for Chennai tidal window: **10.5 kn** → ETA +3.2 hrs, saves ₹42,000 fuel")

        # ── C: Tidal Trap ─────────────────────────────
        with tab_tidal:
            st.markdown("**Tidal Trap Alert — MV Chennai Star**")
            vessel_draft = 15.2
            port_draft_lim = 14.0
            pct_vessel = min(100, int(vessel_draft / 20 * 100))
            pct_port   = min(100, int(port_draft_lim / 20 * 100))

            st.markdown(f"""
<div class='glass-card'>
  <div class='tidal-bar'>
    <div class='tidal-label'><span>Vessel Draft</span><b>{vessel_draft} m</b></div>
    <div class='tidal-track'>
      <div class='tidal-fill' style='width:{pct_vessel}%;background:#f87171'></div>
    </div>
  </div>
  <div class='tidal-bar'>
    <div class='tidal-label'><span>Chennai Port Limit</span><b>{port_draft_lim} m</b></div>
    <div class='tidal-track'>
      <div class='tidal-fill' style='width:{pct_port}%;background:#fbbf24'></div>
    </div>
  </div>
  <div style='text-align:center;margin-top:12px'>
    <span class='badge badge-critical'>⛔ DRAFT INCOMPATIBLE</span>
  </div>
  <div style='color:#94a3b8;font-size:12px;margin-top:10px'>
    Draft excess: <b style='color:#f87171'>+{vessel_draft - port_draft_lim:.1f} m</b><br>
    Visakhapatnam limit: <b style='color:#4ade80'>17.5 m ✅ Compatible</b><br>
    Next Chennai high-tide window: <b>11 hrs 42 min</b>
  </div>
</div>""", unsafe_allow_html=True)

        # ── D: Port Intelligence ──────────────────────
        with tab_intel:
            st.markdown("**Port Status Board**")
            for port in ports_data:
                cong = port.get("congestion_level", "Moderate")
                cong_color = "#f87171" if cong == "High" else "#fbbf24" if cong == "Moderate" else "#4ade80"
                meta = PORT_META.get(port["id"], {})
                st.markdown(f"""
<div class='port-weather-card'>
  <div class='port-weather-header'>
    <b>{port['name']}</b>
    <span class='badge' style='background:rgba(0,0,0,0.3);color:{cong_color};border:1px solid {cong_color}66'>
      {cong}
    </span>
  </div>
  <div class='port-weather-body'>
    🏗 Berths: {port.get('berths','N/A')} &nbsp;|&nbsp;
    📦 {port.get('daily_teu_capacity',0):,} TEU/day &nbsp;|&nbsp;
    ⚓ Draft limit: {meta.get('draft_limit_m','--')} m<br>
    ⏱ Tidal window: {meta.get('tidal_hours','--')} hrs/day
  </div>
</div>""", unsafe_allow_html=True)

        # ── Reroute controls ──────────────────────────
        st.markdown("---")
        if st.session_state.cyclone_triggered and not st.session_state.reroute_data:
            if st.button("🤖 Generate AI Reroute Plan", type="primary", use_container_width=True):
                with st.spinner("Calling Gemini 1.5 Pro + Google Search Grounding…"):
                    st.session_state.reroute_data = get_ai_reroute(
                        vessels_data, ports_data, rail_schedules_data, trucks_data, demo_responses
                    )
                st.rerun()

        if st.session_state.reroute_data:
            _render_command_card(st.session_state.reroute_data)


# ── Command card renderer ─────────────────────────────

def _render_command_card(data: dict):
    cascade = data.get("cascade", {})
    fin     = data.get("financial", {})
    time_d  = data.get("time", {})
    conf    = data.get("confidence", 0)

    st.markdown(f"""
<div class='cmd-card'>
  <div class='cmd-card-header'>
    🤖 AI REROUTE RECOMMENDATION &nbsp;
    <span class='badge badge-safe'>Confidence: {conf}%</span>
  </div>
  <p><b>{data.get('primary_recommendation','')}</b></p>
  <div class='cascade-step'>🚢 <b>Sea:</b> {cascade.get('sea',{}).get('action','')} — {cascade.get('sea',{}).get('reason','')}</div>
  <div class='cascade-step'>🚂 <b>Rail:</b> Train {cascade.get('rail',{}).get('train_id','')} ({cascade.get('rail',{}).get('name','')}) — {cascade.get('rail',{}).get('wagons_needed',0)} wagons — ETA: {cascade.get('rail',{}).get('full_eta','')}</div>
  <div class='cascade-step'>🚛 <b>Road:</b> {cascade.get('road',{}).get('action','')} — {cascade.get('road',{}).get('eta_hours',0)} hrs</div>
</div>""", unsafe_allow_html=True)

    air = cascade.get("air", {})
    if air.get("needed"):
        st.markdown(f"<div class='cascade-step-air' style='border-radius:8px'>✈ <b>Air Escalation ACTIVE:</b> {air.get('option','')} — ₹{air.get('cost_lakh',0)}L</div>", unsafe_allow_html=True)

    f1, f2 = st.columns(2)
    with f1:
        st.metric("Exposure w/o action", f"₹{fin.get('exposure_without_action_crore',0)} Cr")
        st.metric("Net Savings", f"₹{fin.get('net_savings_crore',0)} Cr", "+Savings")
    with f2:
        st.metric("Original ETA", f"{time_d.get('original_eta_hours',48)} hrs")
        st.metric("New ETA", f"{time_d.get('new_eta_hours',51)} hrs")

    with st.expander("🌐 Live Intelligence"):
        st.markdown(f"<div class='intel-box'>{data.get('live_intel','')}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='intel-box'><b>Tidal:</b> {data.get('tidal','')}</div>", unsafe_allow_html=True)

    st.markdown(f"<div class='social-box'>🌱 <b>Social Impact:</b> {data.get('social_impact','')}</div>", unsafe_allow_html=True)

    acc, rej = st.columns(2)
    with acc:
        if st.button("✅ ACCEPT REROUTE", type="primary", use_container_width=True, key="accept_sea"):
            st.session_state.reroute_accepted = True
            firebase_write("/active_reroutes/MV_Chennai_Star", {
                "vessel_id": "VSL-CHN-001", "status": "active",
                "instruction": "Divert to Visakhapatnam Port. Transfer to SCR 58501. Acknowledge.",
                "alt_port": cascade.get("sea", {}).get("alt_port", "Visakhapatnam"),
            })
            st.success("✅ Reroute accepted and transmitted to vessel.")
            st.rerun()
    with rej:
        if st.button("❌ REJECT", use_container_width=True, key="reject_sea"):
            st.session_state.reroute_data = None
            st.rerun()
