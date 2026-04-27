# -*- coding: utf-8 -*-
"""Simulation Engine — Interactive scenario runner with animated results."""

import json
import time
from datetime import datetime

import streamlit as st

from components.cards import command_card_html, empty_state, metric_card
from components.charts import simulation_gantt
from components.maps import render_overview_map
from utils.data import get_real_weather
from utils.gemini import get_ai_reroute
from utils.firebase import firebase_write


SCENARIOS = {
    "cyclone": {
        "name": "🌀 Cyclone — Bay of Bengal Cat.3",
        "event": "Category 3 Cyclone at 14.8°N 85.6°E, 180kph winds",
        "affected": "Chennai Port (blocked), 3 vessels in path",
        "cargo": "MV Chennai Star — 4200 engine blocks — ₹47.3Cr",
        "exposure": 9.6, "reroute_cost": 0.76, "savings": 8.84,
    },
    "strike": {
        "name": "🔴 Port Strike — Chennai Dock Workers",
        "event": "72-hour strike, 8 vessels affected, no loading/unloading",
        "affected": "Chennai Port — all berths",
        "cargo": "8 vessels, ₹32Cr total exposure",
        "exposure": 32.0, "reroute_cost": 2.1, "savings": 29.9,
    },
    "tidal": {
        "name": "🌊 Tidal Trap — Draft Incompatibility",
        "event": "Vessel draft 15.2m exceeds Chennai port limit 14.0m",
        "affected": "MV Chennai Star cannot dock",
        "cargo": "4200 engine blocks — ₹47.3Cr",
        "exposure": 4.8, "reroute_cost": 0.3, "savings": 4.5,
    },
    "canal": {
        "name": "⚓ Canal Blockage — Suez/Red Sea",
        "event": "Vessel insurance suspended for Red Sea transit",
        "affected": "Europe→India routes, +14 days via Cape",
        "cargo": "Electronics from Europe — ₹180Cr pipeline",
        "exposure": 180.0, "reroute_cost": 12.5, "savings": 167.5,
    },
    "highway": {
        "name": "🚛 NH16 Highway Closure — Floods",
        "event": "Rajahmundry–Vijayawada flooded, 72hr closure",
        "affected": "All Chennai→Hyderabad road freight",
        "cargo": "15 trucks, ₹8.4Cr cargo",
        "exposure": 8.4, "reroute_cost": 0.6, "savings": 7.8,
    },
    "air": {
        "name": "✈️ Air Freight Escalation",
        "event": "Rail slot missed by >8 hours, assembly buffer critical",
        "affected": "Maruti Manesar line — ₹2.4Cr/day shutdown cost",
        "cargo": "8.4 tons critical components",
        "exposure": 7.2, "reroute_cost": 0.142, "savings": 7.06,
    },
}


def render(vessels, ports, trucks, rail, demo_responses):
    """Render the full Simulation Engine page."""

    # Simulation control panel in sidebar-like left column
    ctrl_col, main_col = st.columns([1.2, 3], gap="large")

    with ctrl_col:
        st.markdown("#### 🎮 Simulation Controls")

        scenario_key = st.selectbox(
            "Choose Scenario",
            list(SCENARIOS.keys()),
            format_func=lambda k: SCENARIOS[k]["name"],
            key="sim_scenario",
        )
        scenario = SCENARIOS[scenario_key]

        # Scenario info card
        st.markdown(
            f"""
            <div class='glass-card' style='padding:14px'>
              <div style='font-size:13px;color:#fbbf24;font-weight:600;margin-bottom:6px'>SCENARIO BRIEF</div>
              <div style='font-size:12px;color:#e7efff;margin-bottom:4px'><b>Event:</b> {scenario['event']}</div>
              <div style='font-size:12px;color:#94a3b8;margin-bottom:4px'><b>Affected:</b> {scenario['affected']}</div>
              <div style='font-size:12px;color:#94a3b8'><b>Cargo:</b> {scenario['cargo']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("##### Adjust Parameters")
        storm_cat = st.slider("Storm Intensity", 1, 5, 3, key="sim_storm") if scenario_key == "cyclone" else 3
        strike_hrs = st.slider("Strike Duration (hrs)", 24, 168, 72, key="sim_strike_dur") if scenario_key == "strike" else 72
        cargo_value = st.slider("Cargo Value (₹ Cr)", 10, 500, int(scenario["exposure"] * 10), key="sim_value")
        buffer_hrs = st.slider("Assembly Buffer (hrs)", 24, 120, 96, key="sim_buffer")

        run_btn = st.button("🚀 RUN SIMULATION", use_container_width=True, type="primary", key="run_sim")

        if st.button("🔄 Reset Simulation", use_container_width=True, key="reset_sim"):
            st.session_state.sim_running = False
            st.session_state.sim_complete = False
            st.session_state.cyclone_triggered = False
            st.session_state.reroute_data = None
            st.session_state.reroute_accepted = False
            st.rerun()

    with main_col:
        sim_state = st.session_state.get("sim_complete", False)

        if run_btn:
            _run_simulation(scenario_key, scenario, vessels, ports, trucks, rail, demo_responses, main_col)

        elif sim_state and st.session_state.get("reroute_data"):
            _render_results(scenario, vessels, ports, trucks, rail, demo_responses)

        else:
            # Pre-event: Normal map, all green
            st.markdown("#### 📍 Pre-Event — Normal Operations")
            render_overview_map(vessels, ports, trucks, cyclone_on=False, reroute_on=False, height=400)
            st.info("Select a scenario and click **RUN SIMULATION** to begin.")


def _run_simulation(scenario_key, scenario, vessels, ports, trucks, rail, demo_responses, container):
    """Animated simulation sequence."""

    # T+0: Trigger event
    progress = st.progress(0, text="Initializing simulation...")
    time.sleep(0.5)

    # T+1: Show event on map
    progress.progress(15, text="🌀 Event detected — updating threat map...")
    st.session_state.cyclone_triggered = True
    time.sleep(1)

    # T+2: Update risk badges
    progress.progress(30, text="⚠ Assessing vessel risk exposure...")
    time.sleep(1)

    # T+3: Financial exposure counter
    progress.progress(45, text="💰 Calculating financial exposure...")
    time.sleep(0.8)

    # T+4: Run AI reroute
    progress.progress(60, text="🤖 Running AI Cascade Reroute Engine (Gemini 1.5 Pro)...")
    reroute = get_ai_reroute(vessels, ports, rail, trucks, demo_responses)
    st.session_state.reroute_data = reroute
    time.sleep(0.5)

    # T+5: Generate cascade steps
    progress.progress(80, text="✅ Building cascade response plan...")
    time.sleep(0.5)

    progress.progress(100, text="✅ Simulation complete — results ready")
    time.sleep(0.3)

    st.session_state.sim_complete = True
    st.rerun()


def _render_results(scenario, vessels, ports, trucks, rail, demo_responses):
    """Render complete simulation results."""
    data = st.session_state.reroute_data
    cascade = data.get("cascade", {})
    fin = data.get("financial", {})
    time_d = data.get("time", {})

    st.markdown("#### 🌀 Event Active — AI Cascade Response")

    # Map with cyclone
    render_overview_map(
        vessels, ports, trucks,
        cyclone_on=True,
        reroute_on=st.session_state.get("reroute_accepted", False),
        height=380,
    )

    # AI Recommendation Card
    st.markdown(command_card_html(data), unsafe_allow_html=True)

    # Air escalation
    air = cascade.get("air", {})
    if air.get("needed"):
        st.markdown(
            f"<div class='cascade-step cascade-step-air' style='border-radius:8px'>✈ <b>Air Escalation ACTIVE:</b> {air.get('option', '')} — ₹{air.get('cost_lakh', 0)}L</div>",
            unsafe_allow_html=True,
        )
    else:
        with st.expander("✈ Air Freight Option (threshold not met)"):
            st.info(f"Triggers if: {air.get('triggers_if', '')}\nOption: {air.get('option', '')}\nCost: ₹{air.get('cost_lakh', 0)}L")

    st.markdown("---")

    # Timeline Gantt chart
    st.markdown("#### ⏱ Cascade Timeline")
    simulation_gantt(data)

    # Financial comparison table
    st.markdown("#### 💰 Financial Comparison")
    exp = fin.get("exposure_without_action_crore", 9.6)
    reroute_cost = fin.get("reroute_cost_delta_crore", 0.76)
    savings = fin.get("net_savings_crore", 8.84)

    st.markdown(
        f"""
        <div class='glass-card' style='padding:16px'>
          <table style='width:100%;border-collapse:collapse;color:#e7efff'>
            <tr style='border-bottom:1px solid rgba(96,165,250,0.3)'>
              <th style='text-align:left;padding:8px;color:#94a3b8'>Scenario</th>
              <th style='text-align:right;padding:8px;color:#94a3b8'>Cost (₹ Cr)</th>
              <th style='text-align:right;padding:8px;color:#94a3b8'>Time (hrs)</th>
            </tr>
            <tr style='border-bottom:1px solid rgba(96,165,250,0.15)'>
              <td style='padding:8px'>❌ Do Nothing</td>
              <td style='text-align:right;padding:8px;color:#f87171;font-weight:700'>{exp}</td>
              <td style='text-align:right;padding:8px;color:#f87171'>∞ (blocked)</td>
            </tr>
            <tr style='border-bottom:1px solid rgba(96,165,250,0.15)'>
              <td style='padding:8px'>🤖 AI Cascade Reroute</td>
              <td style='text-align:right;padding:8px;color:#4ade80;font-weight:700'>{reroute_cost}</td>
              <td style='text-align:right;padding:8px;color:#4ade80'>{time_d.get("new_eta_hours", 51)}</td>
            </tr>
            <tr>
              <td style='padding:8px'>✈ Emergency Air Only</td>
              <td style='text-align:right;padding:8px;color:#fbbf24'>1.42</td>
              <td style='text-align:right;padding:8px;color:#fbbf24'>18</td>
            </tr>
          </table>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Social Impact
    st.markdown("#### 🌱 Social Impact")
    s1, s2, s3, s4 = st.columns(4)
    s1.markdown("<div class='glass-card' style='text-align:center;padding:16px'><div style='font-size:28px'>👷</div><div style='font-size:20px;font-weight:700;color:#4ade80'>340</div><div style='font-size:11px;color:#94a3b8'>Dock Workers</div></div>", unsafe_allow_html=True)
    s2.markdown("<div class='glass-card' style='text-align:center;padding:16px'><div style='font-size:28px'>🏭</div><div style='font-size:20px;font-weight:700;color:#4ade80'>2,300</div><div style='font-size:11px;color:#94a3b8'>Plant Workers</div></div>", unsafe_allow_html=True)
    s3.markdown("<div class='glass-card' style='text-align:center;padding:16px'><div style='font-size:28px'>🚜</div><div style='font-size:20px;font-weight:700;color:#4ade80'>42</div><div style='font-size:11px;color:#94a3b8'>Farmers</div></div>", unsafe_allow_html=True)
    s4.markdown("<div class='glass-card' style='text-align:center;padding:16px'><div style='font-size:28px'>💊</div><div style='font-size:20px;font-weight:700;color:#4ade80'>3</div><div style='font-size:11px;color:#94a3b8'>Hospitals</div></div>", unsafe_allow_html=True)

    # Live Intel
    with st.expander("🌐 Live Intelligence (Google Search Grounding)"):
        st.markdown(f"<div class='intel-box'>{data.get('live_intel', '')}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='intel-box'><b>Geopolitical:</b> {data.get('geopolitical', '')}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='intel-box'><b>Tidal:</b> {data.get('tidal', '')}</div>", unsafe_allow_html=True)

    st.markdown(f"<div class='social-box'>🌱 <b>Social Impact:</b> {data.get('social_impact', '')}</div>", unsafe_allow_html=True)

    # Accept / Reject
    st.markdown("---")
    acc_col, rej_col = st.columns(2)
    with acc_col:
        if st.button("✅ ACCEPT FULL CASCADE REROUTE", use_container_width=True, type="primary", key="sim_accept"):
            st.session_state.reroute_accepted = True
            firebase_write(
                "/active_reroutes/MV_Chennai_Star",
                {
                    "vessel_id": "VSL-CHN-001", "status": "active",
                    "instruction_for_captain": "Divert immediately to Visakhapatnam Port.",
                    "alt_port": cascade.get("sea", {}).get("alt_port", "Visakhapatnam"),
                    "rail_train": cascade.get("rail", {}).get("train_id", "58501"),
                    "timestamp": datetime.now().isoformat(),
                },
            )
            st.rerun()
    with rej_col:
        if st.button("❌ REJECT — Show Consequence", use_container_width=True, key="sim_reject"):
            st.error(f"⚠ Assembly line shutdown in {st.session_state.get('sim_buffer', 96)} hours. Cost: ₹2.4 Cr/day escalating.")
