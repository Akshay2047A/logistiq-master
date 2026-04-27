# -*- coding: utf-8 -*-
"""Sea & Maritime Operations page."""
import streamlit as st
import time

from logistiq.data import vessels_data, ports_data, trucks_data, rail_schedules_data, demo_responses
from logistiq.components import maps as M, cards as K
from logistiq.utils.data import get_real_weather, vessel_fuel_cost, CITY_COORDS, get_vessel_position_estimate
from logistiq.utils.gemini import get_ai_reroute, get_live_intelligence, get_geopolitical_intel
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
        
        # Estimate vessel positions (Section 11)
        vessels_estimated = []
        for v in vessels_data:
            v_est = dict(v)
            if v["status"] == "At Sea":
                est = get_vessel_position_estimate(v)
                v_est["lat"] = est["estimated_lat"]
                v_est["lon"] = est["estimated_lon"]
            vessels_estimated.append(v_est)

        M.add_vessels(
            fmap, vessels_estimated,
            at_risk_ids={"VSL-CHN-001"} if st.session_state.cyclone_triggered else set(),
        )
        # Only show vessels and sea lane — NO road trucks on maritime map
        M.add_rail_corridor(fmap, rail_schedules_data)
        if st.session_state.cyclone_triggered:
            M.add_cyclone(fmap)
        if st.session_state.reroute_accepted:
            M.add_reroute_path(fmap)
        M.render_map(fmap, height=460)
        st.caption("🛰 Vessel positions estimated via ULIP LDB telemetry")

        # Vessel list
        st.markdown("#### 🚢 Active Vessels")
        for v in vessels_estimated:
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
        
        # Live Telemetry indicator (Section 11)
        st.markdown("""
<div style='font-size:11px;color:#94a3b8;margin-bottom:10px;text-align:right'>
  📡 <b>Live Telemetry:</b> Last AIS sync: just now | Speed: 15.2 kn | Heading: 287° NW | Source: ULIP LDB
</div>""", unsafe_allow_html=True)

        tab_weather, tab_speed, tab_tidal, tab_intel = st.tabs(
            ["🌤 Weather", "⚡ Speed Optimizer", "🌊 Tidal Trap", "📡 Port Intel"]
        )

        # ── A: Port Weather ──────────────────────────
        with tab_weather:
            st.markdown("**Live Port Weather**")
            # Fetch all weathers
            wx_data = {}
            any_danger = False
            danger_msg = ""
            for pid, meta in PORT_META.items():
                lat, lng = meta["coords"]
                wx = get_real_weather(lat, lng, meta["name"])
                wx_data[pid] = wx
                if wx.get("is_dangerous", False):
                    any_danger = True
                    danger_msg = f"{meta['name']}: Wind {wx.get('wind_kph')} kph"

            if any_danger:
                st.markdown(f"""
<div style='background:rgba(251,146,60,0.2);border:1px solid #fb923c;color:#fb923c;padding:10px;border-radius:8px;font-size:13px;font-weight:700;margin-bottom:10px'>
  ⚠ ADVERSE WEATHER DETECTED — {danger_msg}
</div>""", unsafe_allow_html=True)

            for pid, meta in PORT_META.items():
                wx = wx_data[pid]
                st.markdown(K.port_weather_card({"name": meta["name"]}, wx), unsafe_allow_html=True)
                st.markdown("<div style='font-size:11px;color:#f87171;margin-top:-4px;margin-bottom:10px'>🌊 Wave Warning: Moderate swells (2.5m)</div>", unsafe_allow_html=True)

        # ── B: Speed Optimizer ────────────────────────
        with tab_speed:
            st.markdown("**Vessel Speed Optimizer**")
            
            # Preset buttons
            sc1, sc2, sc3 = st.columns(3)
            if "speed_val" not in st.session_state:
                st.session_state.speed_val = 12
            
            with sc1:
                if st.button("🌱 Eco (9kn)", use_container_width=True): st.session_state.speed_val = 9
            with sc2:
                if st.button("⚖ Standard (12kn)", use_container_width=True): st.session_state.speed_val = 12
            with sc3:
                if st.button("⚡ Fast (16kn)", use_container_width=True): st.session_state.speed_val = 16

            speed = st.slider("Speed (knots)", 8, 16, st.session_state.speed_val, key="speed_slider")
            st.session_state.speed_val = speed
            
            voyage_h = st.number_input("Voyage duration (hrs)", 12.0, 120.0, 48.0, step=1.0, key="voyage_h")
            vessel_draft = 15.2
            port_limit = 14.0

            fc = vessel_fuel_cost(speed, voyage_h)
            eta_delta = round((12 - speed) * voyage_h / speed, 1)
            tidal_ok = vessel_draft <= port_limit
            
            # SLA Check
            new_eta_h = voyage_h + eta_delta
            sla_met = new_eta_h <= 96.0

            st.markdown(f"""
<div class='glass-card'>
  <div style='margin-bottom:10px;font-size:12px;color:{"#4ade80" if sla_met else "#f87171"}'>
    <b>SLA Check:</b> {"✅ Meets 96hr deadline" if sla_met else f"❌ Breaches deadline (ETA {new_eta_h:.1f}h)"}
  </div>
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
            
            # Comparison table
            fc_9 = vessel_fuel_cost(9, voyage_h)
            fc_12 = vessel_fuel_cost(12, voyage_h)
            fc_16 = vessel_fuel_cost(16, voyage_h)
            
            table_html = f"""
<table style='width:100%;font-size:11px;margin-top:10px;text-align:right'>
  <tr style='color:#94a3b8;border-bottom:1px solid #1e293b'>
    <th style='text-align:left'>Speed</th><th>ETA Adj</th><th>Fuel Cost</th><th>CO₂</th><th>Tidal?</th>
  </tr>
  <tr><td style='text-align:left'>9 kn</td><td>+{(12-9)*voyage_h/9:.1f}h</td><td>₹{fc_9['cost_inr']:,}</td><td>{fc_9['co2_tons']}t</td><td>{"✅" if tidal_ok else "❌"}</td></tr>
  <tr><td style='text-align:left'>12 kn</td><td>0.0h</td><td>₹{fc_12['cost_inr']:,}</td><td>{fc_12['co2_tons']}t</td><td>{"✅" if tidal_ok else "❌"}</td></tr>
  <tr><td style='text-align:left'>16 kn</td><td>{(12-16)*voyage_h/16:.1f}h</td><td>₹{fc_16['cost_inr']:,}</td><td>{fc_16['co2_tons']}t</td><td>{"✅" if tidal_ok else "❌"}</td></tr>
</table>"""
            st.markdown(table_html, unsafe_allow_html=True)

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
    Visakhapatnam limit: <b style='color:#4ade80'>17.5 m ✅ Always compatible</b><br>
    Chennai Next Window: <b>In 11h 42m ⏰</b>
  </div>
</div>""", unsafe_allow_html=True)

            if st.button("⚡ Slow-steam to hit tidal window", use_container_width=True):
                st.info("Optimal speed for Chennai tidal window: **10.5 kn** → ETA +3.2 hrs, saves ₹42,000 fuel")

        # ── D: Port Intelligence ──────────────────────
        with tab_intel:
            st.markdown("**Port Status Board**")
            
            if st.button("🔍 Scan Route for Disruptions", use_container_width=True):
                with st.spinner("Scanning via Gemini Search Grounding..."):
                    intel = get_live_intelligence("Current shipping conditions Bay of Bengal ports Chennai Visakhapatnam")
                    st.markdown(f"<div class='intel-box'>{intel} <br><br><i>Powered by Gemini Search</i></div>", unsafe_allow_html=True)

            with st.expander("⚡ Additional Scenarios"):
                if st.button("🔴 Port Strike — Chennai Dock Workers", use_container_width=True):
                    st.session_state.sim_scenario = "🔴 Port Strike — Chennai Dock Workers"
                    st.session_state.cyclone_triggered = True
                    st.query_params["p"] = "simulation"
                    st.session_state.active_page = "simulation"
                    st.rerun()
                if st.button("🌐 Live Geopolitical Intel", use_container_width=True):
                    with st.spinner("Fetching geopolitical intel..."):
                        geo = get_geopolitical_intel(demo_responses)
                        st.markdown(f"<div class='intel-box'><b>{geo['primary_chokepoint']}</b><br>{geo['analysis']}</div>", unsafe_allow_html=True)

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
        
        # Scenario Launcher Card
        st.markdown("""
<div class='sim-event-card'>
  <div style='font-size:13px;font-weight:600;color:#fbbf24;margin-bottom:8px'>
    🎯 Quick Scenario Launcher
  </div>
</div>""", unsafe_allow_html=True)
        q1, q2, q3 = st.columns(3)
        with q1:
            if st.button("🌀 Cyclone Cat.3", use_container_width=True, key="q_cyc"):
                st.session_state.sim_scenario = "🌀 Cyclone — Bay of Bengal Cat.3"
                st.session_state.cyclone_triggered = True
                st.query_params["p"] = "simulation"
                st.session_state.active_page = "simulation"
                st.rerun()
        with q2:
            if st.button("🔴 Port Strike", use_container_width=True, key="q_str"):
                st.session_state.sim_scenario = "🔴 Port Strike — Chennai Dock Workers"
                st.session_state.cyclone_triggered = True
                st.query_params["p"] = "simulation"
                st.session_state.active_page = "simulation"
                st.rerun()
        with q3:
            if st.button("⚓ Tidal Trap", use_container_width=True, key="q_tid"):
                st.session_state.sim_scenario = "🌊 Tidal Trap — Draft Incompatibility"
                st.session_state.cyclone_triggered = True
                st.query_params["p"] = "simulation"
                st.session_state.active_page = "simulation"
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
