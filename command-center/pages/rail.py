# -*- coding: utf-8 -*-
"""Rail Freight page."""

import json
import streamlit as st
from components.maps import render_rail_map
from utils.gemini import cached_gemini_call


def render(rail_schedules, trucks):
    st.markdown("#### 🚂 Rail Freight — South Central Railway Integration")

    r1, r2, r3 = st.columns(3)
    r1.metric("Freight Trains Tracked", len(rail_schedules))
    r2.metric("SCR Corridor", "Vizag → Sec → Pune")
    r3.metric("On-Time Performance", "87%")

    render_rail_map(height=350)

    st.markdown("#### Train Schedule")
    for train in rail_schedules:
        is_sync = train.get("train_id") == "58501" and st.session_state.get("cyclone_triggered", False)
        border = "#FF6B35" if is_sync else "#4ade80" if train.get("status") == "on_time" else "#f87171"
        sync_banner = (
            "<div class='badge-amber' style='margin-top:6px;display:inline-block'>"
            "⚡ SYNC ADVISORY — Hold 90min for MV Chennai Star cargo transfer</div>"
            if is_sync else ""
        )
        status_badge = "badge-green" if train.get("status") == "on_time" else "badge-red"
        st.markdown(
            f"""
            <div class='glass-card' style='border-color:{border}'>
              <b>{train.get('name', '')}</b> — Train {train.get('train_id', '')}<br>
              Route: {train.get('origin', '')} → {train.get('destination', '')}<br>
              Departs: {train.get('departure_time', '')} | Arrives: {train.get('arrival_time', '')}<br>
              Wagons available: {train.get('available_wagons', '')} | Max: {train.get('max_load_tons', '')} tons<br>
              Platform: {train.get('platform', '')} | Status: <span class='{status_badge}'>{train.get('status', '').upper()}</span>
              {sync_banner}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Passenger priority conflict
    st.markdown(
        """
        <div class='glass-card' style='border-color:#f87171'>
          <b>🚄 Passenger Train Priority Conflict Detected</b><br>
          Rajdhani Express 12723 running 47 minutes late on Vizag–Secunderabad corridor.<br>
          Freight Train 77601 will be held at Vijayawada Junction: estimated <b>65 minutes</b>.<br>
          <span class='badge-amber'>Action: Pre-alert truck fleet at Secunderabad to avoid demurrage</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("🤖 Optimize Rail Schedule with Gemini", use_container_width=True, key="rail_optimize"):
        with st.spinner("Optimizing..."):
            prompt = (
                f"Given these rail schedules and a vessel diversion to Vizag, which train best handles the cargo? "
                f"Schedules: {json.dumps(rail_schedules)}. Return a 3-sentence recommendation."
            )
            rec = cached_gemini_call(
                prompt,
                demo_fallback="Train 58501 recommended. Hold departure 90min. Wagons 12 confirmed on Platform 7B.",
            )
        st.info(f"🤖 {rec}")
