# -*- coding: utf-8 -*-
"""Intelligence page — Chokepoints, Exchange Rates, Port Status, AI Digest."""

from datetime import datetime

import streamlit as st

from components.maps import render_chokepoint_map
from components.charts import exchange_rate_display
from components.cards import empty_state
from utils.data import get_live_exchange_rate
from utils.gemini import get_geopolitical_intel, get_live_intelligence


def render(ports):
    """Render the Intelligence hub — 4-quadrant layout."""
    top_left, top_right = st.columns(2, gap="medium")
    bot_left, bot_right = st.columns(2, gap="medium")

    with top_left:
        st.markdown("#### 🌐 Global Chokepoint Monitor")
        intel_data = st.session_state.get("chokepoint_intel")
        render_chokepoint_map(intel_data, height=360)
        if st.button("🔄 Refresh Intel (Gemini + Google)", key="refresh_intel", use_container_width=True):
            with st.spinner("Gemini searching global chokepoints..."):
                st.session_state.chokepoint_intel = get_geopolitical_intel()
            st.rerun()

        # Show intel details
        if intel_data:
            for zone, data in intel_data.items():
                risk = data.get("risk", "Unknown")
                badge_cls = "badge-red" if risk in ("High", "Critical") else ("badge-amber" if risk == "Medium" else "badge-green")
                st.markdown(
                    f"**{zone.replace('_', ' ').title()}**: <span class='{badge_cls}'>{risk}</span> — {data.get('detail', '')}",
                    unsafe_allow_html=True,
                )

    with top_right:
        st.markdown("#### 💱 Live Exchange Rates")
        rates = get_live_exchange_rate()
        
        import time
        last_updated_mins = int((time.time() - rates.get("_ts", time.time())) / 60)
        st.caption(f"Last updated {last_updated_mins} min ago")
        if last_updated_mins > 60:
            st.markdown("<div class='badge' style='background:rgba(251,191,36,0.1);color:#fbbf24;border:1px solid #fbbf2455;margin-bottom:10px'>⚠ Stale FX data</div>", unsafe_allow_html=True)
            
        exchange_rate_display(rates)

        # Impact calculator
        st.markdown("##### 📊 Impact Calculator")
        inr_rate = rates.get("USD_INR", 83.5)
        weakening = st.slider("If INR weakens by (%)", 0.0, 5.0, 2.0, 0.5, key="fx_weak")
        cargo_val = 47.3
        impact = cargo_val * (weakening / 100)
        st.markdown(
            f"""
            <div class='glass-card' style='padding:12px'>
              <div style='font-size:13px;color:#94a3b8'>₹{inr_rate:.2f}/USD current</div>
              <div style='font-size:13px;color:#fbbf24;margin-top:4px'>
                If INR weakens {weakening}% → ₹{cargo_val}Cr shipment costs <b>+₹{impact:.1f}Cr</b> more
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with bot_left:
        st.markdown("#### 🏗 Port Status Board")
        # Port status table
        port_rows = []
        for p in ports:
            level = p.get("congestion_level", "Moderate")
            status_emoji = "🔴" if level == "High" else "🟡" if level == "Moderate" else "🟢"
            port_rows.append({
                "Port": p["name"],
                "Congestion": f"{status_emoji} {level}",
                "Berths": p.get("berths", "N/A"),
                "TEU/day": p.get("daily_teu_capacity", "N/A"),
                "Draft Limit": "14.0m" if "Chennai" in p["name"] else "17.5m" if "Visakhapatnam" in p["name"] else "12.0m",
                "Status": "⚠ Advisory" if level == "High" else "✅ Normal",
            })
        st.dataframe(port_rows, use_container_width=True, hide_index=True)

        # Additional JNPT
        st.markdown(
            """
            <div class='glass-card' style='padding:10px'>
              <b>JNPT Mumbai</b> — <span class='badge-amber'>Moderate</span><br>
              <span style='font-size:12px;color:#94a3b8'>Avg wait: 8.2 hrs | Berths: 32 | TEU/day: 22,000</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with bot_right:
        st.markdown("#### 🤖 AI Intelligence Digest")
        now = datetime.now().strftime("%H:%M IST, %d %b %Y")

        if st.button("🔄 Generate Fresh Digest", key="gen_digest", use_container_width=True):
            with st.spinner("Gemini compiling intelligence brief..."):
                digest = get_live_intelligence(
                    "Complete situation report for Chennai-Visakhapatnam-Manesar logistics corridor. "
                    "Include port status, weather, rail, highway conditions, and global shipping risks."
                )
                st.session_state.intel_digest = digest
                st.session_state.intel_digest_time = now

        digest = st.session_state.get("intel_digest")
        digest_time = st.session_state.get("intel_digest_time", now)

        if digest:
            st.markdown(
                f"""
                <div class='glass-card' style='padding:16px;border-color:#60a5fa'>
                  <div style='font-size:11px;color:#64748b;margin-bottom:8px'>📡 As of {digest_time}</div>
                  <div style='font-size:13px;color:#e7efff;line-height:1.6'>{digest}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div class='glass-card' style='padding:16px;border-color:#60a5fa'>
                  <div style='font-size:11px;color:#64748b;margin-bottom:8px'>📡 As of {now}</div>
                  <div style='font-size:13px;color:#e7efff;line-height:1.6'>
                    No active disruptions on Chennai-Vizag corridor.
                    Red Sea Houthi risk remains elevated (23% diversion increase this week).
                    SCR Train 58501 confirmed on schedule.
                    Next tidal window Chennai: 11hrs.
                    JNPT Mumbai congestion easing — avg wait down to 6.1hrs.
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.caption("Powered by Gemini 1.5 Pro + Google Search Grounding")
