# -*- coding: utf-8 -*-
"""Interactive Simulation Engine — the highest demo-value feature."""
import time
import streamlit as st
import plotly.graph_objects as go

from logistiq.data import vessels_data, ports_data, trucks_data, rail_schedules_data, demo_responses
from logistiq.components import charts as C, maps as M, cards as K
from logistiq.utils.gemini import get_ai_reroute
from logistiq.utils.firebase import firebase_write

SCENARIOS = {
    "🌀 Cyclone — Bay of Bengal Cat.3": {
        "desc": "Category 3 cyclone at 14.8°N 85.6°E blocking Chennai Port.",
        "cargo": "MV Chennai Star — 4,200 Maruti engine blocks — ₹47.3 Cr",
        "color": "#f87171",
        "icon": "🌀",
    },
    "🔴 Port Strike — Chennai Dock Workers": {
        "desc": "72-hour strike. 8 vessels affected. No loading/unloading at Chennai Port.",
        "cargo": "8 vessels, ₹32 Cr total exposure",
        "color": "#fb923c",
        "icon": "🔴",
    },
    "🌊 Tidal Trap — Draft Incompatibility": {
        "desc": "MV Chennai Star draft 15.2m exceeds Chennai Port limit of 14.0m.",
        "cargo": "MV Chennai Star — ₹47.3 Cr — cannot dock",
        "color": "#fbbf24",
        "icon": "🌊",
    },
    "⚓ Red Sea Diversion — Houthi Risk": {
        "desc": "Insurance suspended for Red Sea transit. Cape of Good Hope diversion required.",
        "cargo": "Europe-origin electronics imports — 3-week delay",
        "color": "#a78bfa",
        "icon": "⚓",
    },
    "🚛 NH16 Highway Closure — Floods": {
        "desc": "Rajahmundry–Vijayawada section flooded. 72-hr closure. All road freight diverted.",
        "cargo": "12 trucks, Chennai→Hyderabad corridor, ₹18 Cr",
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
    st.markdown("### 🧪 Simulation Engine")
    st.caption("Interactive scenario modeling — powered by Gemini 1.5 Pro + real logistics data")

    # ── Control panel ──────────────────────────────────
    ctrl_col, main_col = st.columns([1, 2.5])

    with ctrl_col:
        st.markdown("#### ⚙ Simulation Controls")
        scenario = st.selectbox(
            "Choose Scenario", list(SCENARIOS.keys()),
            index=list(SCENARIOS.keys()).index(st.session_state.sim_scenario),
            key="sim_scenario_select",
        )
        st.session_state.sim_scenario = scenario
        meta = SCENARIOS[scenario]

        st.markdown(f"""
<div class='sim-event'>
  <div style='font-size:24px'>{meta['icon']}</div>
  <div style='font-size:12px;color:#94a3b8;margin-top:4px'>{meta['desc']}</div>
  <div style='font-size:11px;color:#64748b;margin-top:4px'>Cargo: {meta['cargo']}</div>
</div>""", unsafe_allow_html=True)

        st.markdown("**Scenario Parameters**")
        intensity = st.slider("Storm Intensity (Cat)", 1, 5, 3, key="sim_intensity")
        strike_dur = st.slider("Strike Duration (hrs)", 24, 168, 72, key="sim_strike")
        cargo_val  = st.slider("Cargo Value at Risk (₹ Cr)", 10, 500, 47, key="sim_val")
        buffer_hrs = st.slider("Assembly Line Buffer (hrs)", 24, 120, 96, key="sim_buf")

        st.markdown("---")
        run_btn = st.button("▶ RUN SIMULATION", type="primary", use_container_width=True, key="run_sim")
        if st.session_state.sim_stage > 0:
            if st.button("↺ Reset", use_container_width=True, key="reset_sim"):
                st.session_state.sim_stage = 0
                st.session_state.sim_running = False
                st.session_state.reroute_data = None
                st.session_state.cyclone_triggered = False
                st.session_state.reroute_accepted = False
                st.rerun()

    # ── Main simulation area ───────────────────────────
    with main_col:
        if run_btn and st.session_state.sim_stage == 0:
            st.session_state.sim_stage = 1
            st.session_state.cyclone_triggered = True
            st.rerun()

        stage = st.session_state.sim_stage

        # STAGE 0: Pre-event baseline
        if stage == 0:
            st.markdown("#### 📍 Pre-Event Baseline — All Systems Normal")
            fmap = M.make_base_map()
            M.add_ports(fmap, ports_data)
            M.add_vessels(fmap, vessels_data)
            M.add_trucks(fmap, trucks_data)
            M.add_rail_corridor(fmap, rail_schedules_data)
            M.render_map(fmap, height=380)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Vessels", "3", "All green")
            c2.metric("Exposure", "₹47.3 Cr", "At risk")
            c3.metric("ETA Confidence", "96%", "High")
            c4.metric("SLA Status", "ON TIME", "✅")

        # STAGE 1: Event triggered
        elif stage == 1:
            st.markdown(f"#### {meta['icon']} T+0: Event Detected")
            st.error(f"**{scenario}**\n\n{meta['desc']}")
            fmap = M.make_base_map()
            M.add_ports(fmap, ports_data)
            M.add_vessels(fmap, vessels_data, at_risk_ids={"VSL-CHN-001"})
            M.add_cyclone(fmap)
            M.render_map(fmap, height=340)

            with st.container():
                st.markdown("""
<div class='sim-step'><span class='step-check'>✅</span> Cyclone detected at 14.8°N 85.6°E — Cat.3</div>
<div class='sim-step'><span class='step-check'>✅</span> MV Chennai Star flagged at risk — flashing red on map</div>
<div class='sim-step'><span class='step-check'>🔄</span> Calculating financial exposure...</div>
""", unsafe_allow_html=True)

            exposure_placeholder = st.empty()
            for val in range(0, cargo_val + 1, max(1, cargo_val // 20)):
                exposure_placeholder.markdown(
                    f"<div style='font-size:32px;color:#f87171;font-weight:700;text-align:center'>₹{val:.1f} Cr AT RISK</div>",
                    unsafe_allow_html=True
                )
                time.sleep(0.04)

            if st.button("⟶ Get AI Reroute Plan", type="primary", use_container_width=True, key="stage1_next"):
                with st.spinner("🤖 Gemini 1.5 Pro analyzing with Google Search Grounding…"):
                    st.session_state.reroute_data = get_ai_reroute(
                        vessels_data, ports_data, rail_schedules_data, trucks_data, demo_responses
                    )
                st.session_state.sim_stage = 2
                st.rerun()

        # STAGE 2: AI plan + results
        elif stage == 2:
            data = st.session_state.reroute_data or demo_responses.get("reroute", {})

            st.markdown("#### 🤖 AI Cascade Reroute Plan")
            cascade = data.get("cascade", {})
            fin     = data.get("financial", {})
            time_d  = data.get("time", {})
            conf    = data.get("confidence", 94)

            # Animate cascade steps
            steps = [
                ("✅", f"🚢 Sea: {cascade.get('sea',{}).get('action','Divert to Vizag')} — {cascade.get('sea',{}).get('reason','')}"),
                ("✅", f"🚂 Rail: Train {cascade.get('rail',{}).get('train_id','58501')} ({cascade.get('rail',{}).get('wagons_needed',12)} wagons) — ETA: {cascade.get('rail',{}).get('full_eta','36 hrs')}"),
                ("✅", f"🚛 Road: {cascade.get('road',{}).get('action','3 trucks repositioned')} — {cascade.get('road',{}).get('eta_hours',5.4)} hrs"),
            ]
            st.markdown(f"""
<div class='cmd-card'>
  <div class='cmd-card-header'>🤖 AI CASCADE REROUTE &nbsp; <span class='badge badge-safe'>Confidence: {conf}%</span></div>
  <p><b>{data.get('primary_recommendation','Divert MV Chennai Star to Visakhapatnam Port, execute rail-road cascade.')}</b></p>
  {''.join(f"<div class='sim-step'><span class='step-check'>{s[0]}</span> {s[1]}</div>" for s in steps)}
</div>""", unsafe_allow_html=True)

            # Gantt + financial
            st.markdown("#### 📅 Route Timeline")
            st.plotly_chart(C.simulation_gantt(), use_container_width=True, key="sim_gantt")

            st.markdown("#### 💰 Financial Comparison")
            rows = FINANCIAL_TABLE.get(scenario, FINANCIAL_TABLE["🌀 Cyclone — Bay of Bengal Cat.3"])
            table_html = """
<table style='width:100%;border-collapse:collapse;font-size:13px'>
  <tr style='border-bottom:1px solid #1e3a5f'>
    <th style='text-align:left;padding:8px;color:#94a3b8'>Scenario</th>
    <th style='text-align:right;padding:8px;color:#94a3b8'>Cost (₹ Cr)</th>
    <th style='text-align:right;padding:8px;color:#94a3b8'>Time (hrs)</th>
  </tr>"""
            row_styles = ["color:#f87171", "color:#4ade80", "color:#fbbf24"]
            for i, (label, cost, t) in enumerate(rows):
                table_html += f"<tr style='border-bottom:1px solid #1e293b'><td style='padding:8px;{row_styles[i]}'>{label}</td><td style='text-align:right;padding:8px'>{cost}</td><td style='text-align:right;padding:8px'>{t}</td></tr>"
            table_html += "</table>"
            st.markdown(f"<div class='glass-card'>{table_html}</div>", unsafe_allow_html=True)

            # Social impact
            st.markdown("#### 🌱 Social Impact Protected")
            st.markdown("""
<div class='social-box' style='display:flex;flex-wrap:wrap;gap:12px;justify-content:center;font-size:20px'>
  <div>👷 <b style='font-size:13px'>340 dock workers</b></div>
  <div>🏭 <b style='font-size:13px'>2,300 plant workers</b></div>
  <div>🚜 <b style='font-size:13px'>42 farmers</b></div>
  <div>💊 <b style='font-size:13px'>3 hospitals</b></div>
</div>""", unsafe_allow_html=True)

            # Accept / Reject
            st.markdown("---")
            acc_col, rej_col = st.columns(2)
            with acc_col:
                if st.button("✅ ACCEPT FULL CASCADE REROUTE", type="primary", use_container_width=True, key="sim_accept"):
                    st.session_state.reroute_accepted = True
                    st.session_state.sim_stage = 3
                    firebase_write("/active_reroutes/MV_Chennai_Star", {
                        "vessel_id": "VSL-CHN-001", "status": "active",
                        "instruction": "Divert to Visakhapatnam Port. Transfer to SCR 58501. Acknowledge.",
                    })
                    st.rerun()
            with rej_col:
                if st.button("❌ REJECT — Show Consequences", use_container_width=True, key="sim_reject"):
                    st.error("**Rejecting reroute…**")
                    cost_ph = st.empty()
                    for t in range(0, 241, 10):
                        cost_ph.markdown(
                            f"<div style='text-align:center;color:#f87171;font-size:28px;font-weight:700'>"
                            f"₹{t * 10_00_000:,} total losses at T+{t} hrs</div>",
                            unsafe_allow_html=True
                        )
                        time.sleep(0.04)

        # STAGE 3: Reroute accepted — animated map
        elif stage == 3:
            st.success("✅ Reroute accepted and transmitted to MV Chennai Star")
            fmap = M.make_base_map()
            M.add_ports(fmap, ports_data)
            M.add_vessels(fmap, vessels_data, at_risk_ids={"VSL-CHN-001"})
            M.add_cyclone(fmap)
            M.add_reroute_path(fmap)
            M.add_rail_corridor(fmap, rail_schedules_data)
            M.render_map(fmap, height=380)
            st.markdown("""
<div class='glass-card'>
  <div class='sim-step'><span class='step-check'>✅</span> Captain acknowledged — new heading set to 17.68°N 83.22°E</div>
  <div class='sim-step'><span class='step-check'>✅</span> SCR Train 58501 held at Vizag platform 7B</div>
  <div class='sim-step'><span class='step-check'>✅</span> 3 trucks repositioned from Chennai to Vizag SCR Terminal</div>
  <div class='sim-step'><span class='step-check'>✅</span> Maruti Manesar notified — ETA 51 hrs (within 96 hr deadline)</div>
  <div class='sim-step'><span class='step-check'>✅</span> Firebase updated — all active reroutes written</div>
</div>""", unsafe_allow_html=True)
            st.balloons()
