# -*- coding: utf-8 -*-
"""Sea & Maritime Operations page."""

import json
import time
from datetime import datetime

import streamlit as st

from components.cards import port_weather_card, command_card_html
from components.maps import render_overview_map
from utils.data import get_real_weather
from utils.gemini import get_ai_reroute, get_live_intelligence
from utils.firebase import firebase_write


def render(vessels, ports, trucks, rail, demo_responses):
    """Render Sea & Maritime operations page."""
    map_col, right_col = st.columns([3, 2], gap="large")

    with map_col:
        render_overview_map(
            vessels, ports, trucks,
            cyclone_on=st.session_state.get("cyclone_triggered", False),
            reroute_on=st.session_state.get("reroute_accepted", False),
            height=480,
        )
        # Vessel table
        st.markdown("#### Active Vessels")
        vessel_rows = [
            {"Vessel": v["name"], "Status": v.get("status", ""), "Cargo": v.get("cargo_type", ""),
             "Speed (kn)": v.get("speed_knots", ""), "Destination": v.get("destination_port_id", "")}
            for v in vessels
        ]
        st.dataframe(vessel_rows, use_container_width=True, hide_index=True)

    with right_col:
        _render_right_panel(vessels, ports, trucks, rail, demo_responses)


def _render_right_panel(vessels, ports, trucks, rail, demo_responses):
    """Right panel with 4 collapsible sections."""

    # SECTION A: Port Weather
    with st.expander("🌤 PORT WEATHER (LIVE)", expanded=True):
        if st.button("🔄 Refresh Weather", use_container_width=True, key="refresh_weather"):
            st.session_state.weather_cache = {}

        w_chennai = get_real_weather(13.0827, 80.2707, "Chennai")
        w_vizag = get_real_weather(17.6868, 83.2185, "Visakhapatnam")

        c1, c2 = st.columns(2)
        with c1:
            port_weather_card("Chennai Port", w_chennai)
        with c2:
            port_weather_card("Vizag Port", w_vizag)

    # SECTION B: Speed Optimizer
    with st.expander("🚀 VESSEL SPEED OPTIMIZER", expanded=True):
        speed = st.slider("MV Chennai Star speed (knots)", 8, 16, 12, key="speed_slider")
        base_fuel = 24.2
        fuel = base_fuel * (speed / 12) ** 3
        eta_adj = 48 * (12 / speed)
        co2 = fuel * 0.32  # rough CO2 estimate

        f1, f2 = st.columns(2)
        f1.metric("Fuel Cost", f"₹{fuel:.1f}L", f"{'+' if fuel > base_fuel else ''}{fuel - base_fuel:.1f}L")
        f2.metric("ETA", f"{eta_adj:.0f} hrs", f"{eta_adj - 48:+.0f} hrs")

        f3, f4 = st.columns(2)
        tidal_ok = eta_adj <= 59  # within tidal window
        f3.metric("Tidal Window", "✅ Compatible" if tidal_ok else "❌ Missed")
        f4.metric("CO₂ Estimate", f"{co2:.1f} tons")

        if st.button("🎯 Calculate Optimal Speed for Tidal Window", use_container_width=True, key="opt_speed"):
            # Back-calculate: need to arrive in ≤ 59 hours
            optimal = max(8, 48 * 12 / 59)
            st.success(f"Optimal speed: **{optimal:.1f} knots** — arrives within tidal window with fuel cost ₹{base_fuel * (optimal/12)**3:.1f}L")

    # SECTION C: Tidal Trap
    with st.expander("⚓ TIDAL TRAP ALERT", expanded=True):
        vessel_draft = 15.2
        port_limit = 14.0
        draft_pct = vessel_draft / 20 * 100
        limit_pct = port_limit / 20 * 100

        st.markdown(
            f"""
            <div class='glass-card' style='border-color:#fbbf24;padding:14px'>
              <b>⚓ Draft Incompatibility Detected</b>
              <div style='margin-top:10px'>
                <div style='font-size:12px;color:#94a3b8;margin-bottom:4px'>Vessel Draft: <b>{vessel_draft}m</b></div>
                <div style='background:rgba(255,255,255,0.1);border-radius:4px;height:10px;overflow:hidden;margin-bottom:8px'>
                  <div style='width:{draft_pct}%;height:100%;background:#f87171;border-radius:4px'></div>
                </div>
                <div style='font-size:12px;color:#94a3b8;margin-bottom:4px'>Port Limit: <b>{port_limit}m</b></div>
                <div style='background:rgba(255,255,255,0.1);border-radius:4px;height:10px;overflow:hidden;margin-bottom:8px'>
                  <div style='width:{limit_pct}%;height:100%;background:#fbbf24;border-radius:4px'></div>
                </div>
                <span class='badge-red'>INCOMPATIBLE — Excess: {vessel_draft - port_limit:.1f}m</span>
                <div style='margin-top:8px;font-size:12px;color:#94a3b8'>
                  Next compatible tidal window: <b>11 hours</b><br>
                  Anchoring cost: ₹18L/day
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # SECTION D: Port Intelligence
    with st.expander("🏗 PORT INTELLIGENCE"):
        for port in ports:
            level = port.get("congestion_level", "Moderate")
            badge = "badge-red" if level == "High" else ("badge-amber" if level == "Moderate" else "badge-green")
            st.markdown(
                f"""
                <div class='glass-card' style='padding:12px'>
                  <b>{port['name']}</b><br>
                  Berths: {port.get('berths', '')} | TEU/day: {port.get('daily_teu_capacity', '')}<br>
                  Draft limit: {'14.0m' if 'Chennai' in port['name'] else '17.5m'}<br>
                  Congestion: <span class='{badge}'>{level}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Route Intelligence
    st.markdown("**🌐 Live Route Intelligence**")
    if st.button("🔍 Scan Route for Disruptions", use_container_width=True, key="scan_route"):
        with st.spinner("Scanning via Gemini + Google Search..."):
            intel = get_live_intelligence("Current disruptions on Chennai-Visakhapatnam-Secunderabad corridor. Port news today.")
            st.markdown(f"<div class='intel-box'>{intel}</div>", unsafe_allow_html=True)

    st.markdown("---")

    # Simulation trigger
    if not st.session_state.get("cyclone_triggered", False):
        if st.button("🌀 SIMULATE CYCLONE — Bay of Bengal Cat.3", use_container_width=True, type="primary", key="sea_cyclone"):
            st.session_state.cyclone_triggered = True
            st.session_state.reroute_data = None
            st.session_state.reroute_accepted = False
            st.rerun()

    elif st.session_state.get("reroute_data") is None:
        st.error("🌀 **CYCLONE ALERT** — Category 3 forming. Chennai Port projected BLOCKED.")
        if st.button("🤖 GET AI REROUTE PLAN", use_container_width=True, type="primary", key="sea_reroute"):
            with st.spinner("Gemini analyzing live conditions..."):
                st.session_state.reroute_data = get_ai_reroute(vessels, ports, rail, trucks, demo_responses)
            st.rerun()
        if st.button("❌ Reset", use_container_width=True, key="sea_reset1"):
            st.session_state.cyclone_triggered = False
            st.rerun()

    elif not st.session_state.get("reroute_accepted", False):
        st.markdown(command_card_html(st.session_state.reroute_data), unsafe_allow_html=True)
        a1, a2 = st.columns(2)
        with a1:
            if st.button("✅ ACCEPT REROUTE", use_container_width=True, type="primary", key="sea_accept"):
                st.session_state.reroute_accepted = True
                st.rerun()
        with a2:
            if st.button("❌ REJECT", use_container_width=True, key="sea_reject"):
                st.session_state.reroute_data = None
                st.rerun()
    else:
        st.success("✅ **CASCADE REROUTE ACTIVATED** — All legs executing.")
        if st.button("🔄 Reset Simulation", key="sea_reset2"):
            st.session_state.cyclone_triggered = False
            st.session_state.reroute_data = None
            st.session_state.reroute_accepted = False
            st.rerun()
