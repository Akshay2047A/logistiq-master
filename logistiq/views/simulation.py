# -*- coding: utf-8 -*-
"""Interactive Simulation Engine — the highest demo-value feature."""
import time
import streamlit as st
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

from logistiq.data import vessels_data, ports_data, trucks_data, rail_schedules_data, demo_responses
from logistiq.components import charts as C, maps as M, cards as K
from logistiq.utils.gemini import get_ai_reroute
from logistiq.utils.firebase import firebase_write

SCENARIOS = {
    "🌀 Cyclone": {
        "desc": "Cat 3 cyclone at 14.8°N 85.6°E blocks Chennai Port.",
        "cargo": "MV Chennai Star — ₹47.3 Cr",
        "full_name": "🌀 Cyclone — Bay of Bengal Cat.3",
        "color": "#f87171",
        "icon": "🌀",
    },
    "🔴 Port Strike": {
        "desc": "72-hr strike. 8 vessels affected.",
        "cargo": "8 vessels, ₹32 Cr total exposure",
        "full_name": "🔴 Port Strike — Chennai Dock Workers",
        "color": "#fb923c",
        "icon": "🔴",
    },
    "🌊 Tidal Trap": {
        "desc": "MV Chennai Star draft 15.2m exceeds Chennai limit 14.0m.",
        "cargo": "MV Chennai Star — ₹47.3 Cr",
        "full_name": "🌊 Tidal Trap — Draft Incompatibility",
        "color": "#fbbf24",
        "icon": "🌊",
    },
    "⚓ Red Sea": {
        "desc": "Insurance suspended. Cape of Good Hope diversion.",
        "cargo": "EU electronics imports",
        "full_name": "⚓ Red Sea Diversion — Houthi Risk",
        "color": "#a78bfa",
        "icon": "⚓",
    },
    "🚛 NH16 Flood": {
        "desc": "Rajahmundry–Vijayawada flooded. 72-hr closure.",
        "cargo": "12 trucks, ₹18 Cr",
        "full_name": "🚛 NH16 Highway Closure — Floods",
        "color": "#4ade80",
        "icon": "🚛",
    },
}

FINANCIAL_TABLE = {
    "🌀 Cyclone — Bay of Bengal Cat.3": [
        ("Do nothing", 9.60, "∞ (blocked)"),
        ("AI Cascade Reroute", 0.76, "51"),
        ("Emergency Air Only", 1.42, "18"),
    ],
    "🔴 Port Strike — Chennai Dock Workers": [
        ("Do nothing", 32.0, "∞"),
        ("AI Cascade (Kamarajar)", 2.10, "36"),
        ("Emergency Air", 4.80, "12"),
    ],
    "🌊 Tidal Trap — Draft Incompatibility": [
        ("Wait for tide", 4.80, "28"),
        ("Divert to Vizag", 0.38, "18"),
        ("Partial unload + tender", 1.20, "24"),
    ],
    "⚓ Red Sea Diversion — Houthi Risk": [
        ("Red Sea (risky)", 0.0, "22"),
        ("Cape of Good Hope", 8.50, "36"),
        ("Air freight (critical)", 12.0, "3"),
    ],
    "🚛 NH16 Highway Closure — Floods": [
        ("Do nothing", 18.0, "∞"),
        ("NH65 bypass (+140km)", 0.85, "14"),
        ("Rail Vijayawada switch", 0.60, "12"),
    ],
}


def render():
    if "sim_step" not in st.session_state:
        st.session_state.sim_step = 0
    if "sim_t0" not in st.session_state:
        st.session_state.sim_t0 = time.time()
        
    elapsed = time.time() - st.session_state.sim_t0
    MAX_STEPS = 5
    st.session_state.sim_step = min(int(elapsed / 1.5), MAX_STEPS)
    
    if st.session_state.get("sim_stage", 0) in (1, 2) and elapsed < 8.0:
        st_autorefresh(interval=1500, key="sim_step_refresh")

    st.markdown("### 🧪 Simulation Engine")
    st.caption("Interactive scenario modeling — powered by Gemini 1.5 Pro + real logistics data")

    # ── Control panel ──────────────────────────────────
    ctrl_col, main_col = st.columns([1.2, 2.3])

    with ctrl_col:
        st.markdown("#### ⚙ Simulation Controls")
        
        # Scenario tiles
        st.markdown("<div style='font-size:12px;color:#94a3b8;margin-bottom:8px'>Select Scenario</div>", unsafe_allow_html=True)
        keys = list(SCENARIOS.keys())
        current = st.session_state.get("sim_scenario_short", keys[0])
        
        t1, t2 = st.columns(2)
        for i, key in enumerate(keys):
            col = t1 if i % 2 == 0 else t2
            meta = SCENARIOS[key]
            with col:
                is_sel = (current == key)
                border = "border-color:#FF6B35;background:rgba(255,107,53,0.1);box-shadow:0 0 10px rgba(255,107,53,0.2)" if is_sel else ""
                if st.button(key, use_container_width=True, key=f"sim_tile_{i}"):
                    st.session_state.sim_scenario_short = key
                    st.session_state.sim_scenario = SCENARIOS[key]["full_name"]
                    st.rerun()

        current = st.session_state.get("sim_scenario_short", keys[0])
        meta = SCENARIOS[current]
        
        st.markdown(f"""
<div class='glass-card' style='border-color:{meta["color"]}44'>
  <div style='font-size:12px;font-weight:700;color:{meta["color"]};margin-bottom:4px'>SCENARIO BRIEF</div>
  <div style='font-size:12px;color:#e7efff;margin-bottom:6px'>{meta['desc']}</div>
  <div style='font-size:11px;color:#94a3b8'><b>Cargo:</b> {meta['cargo']}</div>
</div>""", unsafe_allow_html=True)

        st.markdown("**Adjust Parameters**")
        if "Cyclone" in current:
            st.slider("Storm Intensity (Cat)", 1, 5, 3, key="sim_intensity")
            cargo_val = st.slider("Cargo Value at Risk (₹ Cr)", 10, 500, 47, key="sim_val")
        elif "Strike" in current:
            st.slider("Strike Duration (hrs)", 24, 168, 72, key="sim_strike")
            cargo_val = st.slider("Cargo Value at Risk (₹ Cr)", 10, 500, 32, key="sim_val")
        else:
            cargo_val = st.slider("Cargo Value at Risk (₹ Cr)", 10, 500, 47, key="sim_val")
            st.slider("Assembly Line Buffer (hrs)", 24, 120, 96, key="sim_buf")

        st.markdown("---")
        run_btn = st.button("▶ RUN SIMULATION", type="primary", use_container_width=True, key="run_sim")
        
        if st.session_state.get("last_sim_savings"):
            st.markdown(f"<div style='font-size:12px;color:#4ade80;text-align:center;margin-top:8px'>Last run savings: ₹{st.session_state.last_sim_savings}Cr</div>", unsafe_allow_html=True)

        if st.session_state.sim_stage > 0:
            if st.button("↺ Reset Simulation", use_container_width=True, key="reset_sim"):
                st.session_state.sim_stage = 0
                st.session_state.sim_running = False
                st.session_state.reroute_data = None
                st.session_state.cyclone_triggered = False
                st.session_state.reroute_accepted = False
                st.session_state.sim_reject_mode = False
                st.rerun()

    # ── Main simulation area ───────────────────────────
    with main_col:
        if run_btn and st.session_state.sim_stage == 0:
            st.session_state.sim_stage = 1
            st.session_state.sim_t0 = time.time()
            st.session_state.sim_step = 0
            st.session_state.cyclone_triggered = True
            st.session_state.sim_reject_mode = False
            st.rerun()

        stage = st.session_state.sim_stage
        scenario_full = st.session_state.get("sim_scenario", SCENARIOS["🌀 Cyclone"]["full_name"])

        # STAGE 0: Pre-event baseline
        if stage == 0:
            st.markdown("#### 📍 Pre-Event — Normal Operations")
            st.markdown("""
<div style='background:rgba(74,222,128,0.1);color:#4ade80;padding:8px 14px;border-radius:8px;border:1px solid #4ade80;font-size:13px;font-weight:700;margin-bottom:12px'>
  System Status: ALL GREEN ✅
</div>""", unsafe_allow_html=True)
            fmap = M.make_base_map()
            M.add_ports(fmap, ports_data)
            M.add_vessels(fmap, vessels_data)
            M.add_trucks(fmap, trucks_data)
            M.add_rail_corridor(fmap, rail_schedules_data)
            M.render_map(fmap, height=360)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Vessels", "3", "At sea")
            c2.metric("Exposure", "₹0 Cr", "Safe")
            c3.metric("SLA", "96%", "High")
            c4.metric("Weather", "Clear", "Normal")
            st.caption("Select a scenario above and click RUN to see AI-powered cascade rerouting")

        # STAGE 1: Event triggered
        elif stage == 1:
            st.markdown(f"""
<div style='background:rgba(248,113,113,0.1);border:1px solid #f87171;color:#f87171;padding:12px;border-radius:8px;font-size:14px;font-weight:700;animation:pulse 1s infinite;margin-bottom:12px;text-align:center'>
  {meta['icon']} EVENT DETECTED — {scenario_full}
</div>""", unsafe_allow_html=True)

            fmap = M.make_base_map()
            M.add_ports(fmap, ports_data)
            M.add_vessels(fmap, vessels_data, at_risk_ids={"VSL-CHN-001"})
            if "Cyclone" in current: M.add_cyclone(fmap)
            M.render_map(fmap, height=320)

            # Animated Financial Counter
            progress = min(1.0, elapsed / 2.0)
            v = cargo_val * progress
            color = "#4ade80" if v < cargo_val*0.3 else "#fbbf24" if v < cargo_val*0.7 else "#f87171"
            st.markdown(
                f"<div style='font-size:36px;color:{color};font-weight:800;text-align:center;margin:10px 0;font-variant-numeric:tabular-nums'>₹{v:.1f} Cr AT RISK</div>",
                unsafe_allow_html=True
            )

            # Cascade Impact Visual
            st.markdown("#### Cascade Impact")
            impacts = [
                "🚢 MV Chennai Star — AFFECTED ⚠",
                "🏭 Maruti Manesar — Assembly line at risk",
                "🚂 SCR Train 58501 — Awaiting cargo",
                "🚛 3 trucks — Idle at Chennai Port"
            ]
            visible_impacts = min(4, max(0, int(elapsed / 0.8)))
            html = ""
            for j, imp in enumerate(impacts):
                if j < visible_impacts:
                    html += f"<div style='color:#f87171;padding:6px 12px;background:rgba(248,113,113,0.1);margin-bottom:4px;border-radius:6px;font-size:13px;font-weight:600'>❌ {imp}</div>"
                else:
                    html += f"<div style='color:#94a3b8;padding:6px 12px;margin-bottom:4px;font-size:13px'>⏳ {imp}</div>"
            st.markdown(html, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            if elapsed >= 3.0:
                if st.button("🤖 Get AI Reroute Plan", type="primary", use_container_width=True, key="stage1_next"):
                    st.session_state.sim_stage = 2
                    st.session_state.sim_t0 = time.time()
                    st.session_state.sim_step = 0
                    st.rerun()

        # STAGE 2: AI plan + results
        elif stage == 2:
            if not st.session_state.reroute_data and not st.session_state.get("sim_reject_mode", False):
                # Animate thinking
                steps = [
                    ("🔍", "Gemini searching Google for live port conditions..."),
                    ("🌊", "Checking tidal charts for Visakhapatnam..."),
                    ("🚂", "Verifying SCR Train 58501 availability..."),
                    ("💰", "Calculating financial impact..."),
                    ("✅", "Cascade reroute plan ready")
                ]
                visible_steps = min(5, int(elapsed / 0.8) + 1)
                html_accum = ""
                for icon, text in steps[:visible_steps]:
                    html_accum += f"<div style='padding:8px;font-size:13px;color:#e7efff'><b>{icon}</b> {text}</div>"
                st.markdown(f"<div class='glass-card'>{html_accum}</div>", unsafe_allow_html=True)
                
                if visible_steps >= 5:
                    st.session_state.reroute_data = get_ai_reroute(
                        vessels_data, ports_data, rail_schedules_data, trucks_data, demo_responses
                    )
                    st.session_state.sim_t0 = time.time()
                    st.session_state.sim_step = 0
                    st.rerun()

            if st.session_state.get("sim_reject_mode", False):
                st.markdown("<h3 style='color:#f87171'>Consequences of Rejection</h3>", unsafe_allow_html=True)
                msgs = [
                    ("T+0: Decision to reject reroute", 0),
                    ("T+6h: Demurrage charges begin: ₹18L/day", 0.18),
                    ("T+18h: Maruti Manesar issues stock-out alert", 0.5),
                    ("T+48h: Assembly line SHUTDOWN", 2.4),
                    ("T+96h: Contractual penalties applied", 8.5)
                ]
                visible_msgs = min(5, max(1, int(elapsed / 1.0) + 1))
                total = sum(cost for msg, cost in msgs[:visible_msgs])
                latest_msg = msgs[visible_msgs-1][0]
                
                st.markdown(
                    f"<div style='text-align:center;color:#f87171;font-size:28px;font-weight:700;background:rgba(248,113,113,0.1);padding:20px;border-radius:12px'>"
                    f"⚠ {latest_msg}<br><br>Loss: ₹{total:.2f} Cr</div>",
                    unsafe_allow_html=True
                )
                
                st.markdown("<br>", unsafe_allow_html=True)
                if elapsed >= 5.0:
                    if st.button("🤖 It's not too late — Accept the reroute?", type="primary", use_container_width=True):
                        st.session_state.sim_reject_mode = False
                        st.session_state.reroute_accepted = True
                        st.session_state.sim_stage = 3
                        st.session_state.sim_t0 = time.time()
                        st.session_state.sim_step = 0
                        st.rerun()

            else:
                data = st.session_state.reroute_data
                cascade = data.get("cascade", {})
                fin     = data.get("financial", {})
                conf    = data.get("confidence", 94)

                st.markdown(f"""
<div class='cmd-card'>
  <div class='cmd-card-header'>🤖 AI CASCADE REROUTE &nbsp; <span class='badge badge-safe'>Confidence: {conf}%</span></div>
  <p><b>{data.get('primary_recommendation','Divert MV Chennai Star to Visakhapatnam Port, execute rail-road cascade.')}</b></p>
  <div class='sim-step'><span class='step-check'>✅</span> 🚢 Sea: {cascade.get('sea',{}).get('action','Divert to Vizag')}</div>
  <div class='sim-step'><span class='step-check'>✅</span> 🚂 Rail: Train 58501 ({cascade.get('rail',{}).get('wagons_needed',12)} wagons)</div>
  <div class='sim-step'><span class='step-check'>✅</span> 🚛 Road: {cascade.get('road',{}).get('action','3 trucks repositioned')}</div>
</div>""", unsafe_allow_html=True)

                col_l, col_m, col_r = st.columns([1.2, 1, 0.8])
                with col_l:
                    st.markdown("#### Timeline")
                    st.plotly_chart(C.simulation_gantt(), use_container_width=True, key="sim_gantt", height=200)
                with col_m:
                    st.markdown("#### Financials")
                    rows = FINANCIAL_TABLE.get(scenario_full, FINANCIAL_TABLE["🌀 Cyclone — Bay of Bengal Cat.3"])
                    table_html = "<table style='width:100%;font-size:11px'>"
                    for label, cost, t in rows:
                        table_html += f"<tr><td style='padding:4px 0'>{label}</td><td style='text-align:right'>₹{cost}</td></tr>"
                    table_html += "</table>"
                    st.markdown(f"<div class='glass-card'>{table_html}</div>", unsafe_allow_html=True)
                with col_r:
                    st.markdown("#### Impact")
                    st.markdown("""
<div class='social-box' style='font-size:11px;padding:8px'>
  <div>👷 <b>340</b> dock workers</div><div style='height:4px'></div>
  <div>🏭 <b>2,300</b> plant workers</div><div style='height:4px'></div>
  <div>🚜 <b>42</b> farmers</div><div style='height:4px'></div>
  <div>💊 <b>3</b> hospitals</div>
</div>""", unsafe_allow_html=True)

                with st.expander("🌐 Live Intelligence", expanded=False):
                    st.markdown(f"<div class='intel-box'>{data.get('live_intel','')}</div>", unsafe_allow_html=True)
                    st.caption("Powered by Gemini 1.5 Pro + Google Search Grounding")

                st.markdown("---")
                if st.button("✅ ACCEPT FULL CASCADE REROUTE", type="primary", use_container_width=True):
                    st.session_state.reroute_accepted = True
                    st.session_state.sim_stage = 3
                    st.session_state.last_sim_savings = fin.get("net_savings_crore", 8.84)
                    firebase_write("/active_reroutes/MV_Chennai_Star", {
                        "vessel_id": "VSL-CHN-001", "status": "active",
                        "instruction": "Divert to Visakhapatnam Port. Transfer to SCR 58501. Acknowledge.",
                    })
                    st.rerun()
                st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
                if st.button("❌ REJECT — Show Consequences", use_container_width=True):
                    st.session_state.sim_reject_mode = True
                    st.session_state.sim_t0 = time.time()
                    st.session_state.sim_step = 0
                    st.rerun()

        # STAGE 3: Reroute accepted — animated map
        elif stage == 3:
            fmap = M.make_base_map()
            M.add_ports(fmap, ports_data)
            M.add_vessels(fmap, vessels_data, at_risk_ids={"VSL-CHN-001"})
            if "Cyclone" in current: M.add_cyclone(fmap)
            M.add_reroute_path(fmap)
            M.add_rail_corridor(fmap, rail_schedules_data)
            M.render_map(fmap, height=360)
            
            st.markdown("""
<div class='glass-card' style='border-color:#4ade80;box-shadow:0 0 20px rgba(74,222,128,0.2)'>
  <div style='font-size:16px;font-weight:800;color:#4ade80;margin-bottom:12px;text-align:center'>✅ CASCADE REROUTE COMPLETE</div>
  <div class='sim-step'><span class='step-check'>✅</span> 🚢 Captain Rajesh acknowledged — New heading set (T+0)</div>
  <div class='sim-step'><span class='step-check'>✅</span> 🚂 Train 58501 held at Platform 7B (T+2min)</div>
  <div class='sim-step'><span class='step-check'>✅</span> 🚛 3 trucks repositioned to Vizag (T+4min)</div>
  <div class='sim-step'><span class='step-check'>✅</span> 🏭 Maruti Manesar notified — ETA 51hrs (T+5min)</div>
  <div class='sim-step'><span class='step-check'>✅</span> 💰 Assembly line protected — ₹8.84Cr saved</div>
</div>""", unsafe_allow_html=True)
            st.success("✅ All changes synced to Firebase")
            st.balloons()
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Simulate Next Scenario", use_container_width=True):
                st.session_state.sim_stage = 0
                st.session_state.sim_running = False
                st.session_state.reroute_data = None
                st.session_state.cyclone_triggered = False
                st.session_state.reroute_accepted = False
                st.rerun()
