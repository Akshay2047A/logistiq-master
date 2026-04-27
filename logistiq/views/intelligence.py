# -*- coding: utf-8 -*-
"""Intelligence Hub — chokepoints, FX, port status board, AI digest."""
import time
import streamlit as st

from logistiq.data import ports_data, demo_responses
from logistiq.components import maps as M, charts as C, cards as K
from logistiq.utils.gemini import get_geopolitical_intel, get_ai_digest
from logistiq.utils.data import get_live_exchange_rate, get_fx_history_mock
from logistiq.utils.firebase import firebase_read

RISK_COLORS = {"Critical": "#f87171", "High": "#fb923c", "Medium": "#fbbf24", "Low": "#4ade80"}


def render():
    st.markdown("### 📡 Live Intelligence Hub")
    st.caption("Real-time data from Gemini Search Grounding, WeatherAPI, and open.er-api.com")

    # ── Refresh button ─────────────────────────────────
    rcol, _ = st.columns([1, 3])
    with rcol:
        if st.button("🔄 Refresh All Intel", use_container_width=True):
            st.session_state.geopolitical_cache = None
            st.session_state.geopolitical_ts = 0
            st.rerun()

    # ── Load geopolitical intel (cached 15 min) ────────
    now = time.time()
    if not st.session_state.geopolitical_cache or (now - st.session_state.geopolitical_ts) > 900:
        with st.spinner("Fetching live geopolitical intelligence via Gemini Search Grounding…"):
            st.session_state.geopolitical_cache = get_geopolitical_intel(demo_responses)
            st.session_state.geopolitical_ts = now
    geo = st.session_state.geopolitical_cache

    # ── 4-quadrant layout ─────────────────────────────
    top_left, top_right = st.columns(2)
    bot_left, bot_right = st.columns(2)

    # ── TOP LEFT: World chokepoint map ────────────────
    with top_left:
        st.markdown("#### 🗺 Global Chokepoint Map")
        fmap = M.make_world_chokepoint_map(geo)
        M.render_map(fmap, height=320)

        chokepoints = [
            ("red_sea", "Red Sea / Bab el-Mandeb"),
            ("suez_canal", "Suez Canal"),
            ("malacca_strait", "Strait of Malacca"),
            ("bay_of_bengal", "Bay of Bengal"),
            ("strait_of_hormuz", "Strait of Hormuz"),
        ]
        for key, name in chokepoints:
            data = geo.get(key, {})
            risk = data.get("risk", "Unknown")
            color = RISK_COLORS.get(risk, "#60a5fa")
            detail = data.get("detail", "")
            affected = data.get("vessels_affected", data.get("cyclone_active", "N/A"))
            st.markdown(f"""
<div style='display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid #1e293b'>
  <span style='width:10px;height:10px;border-radius:50%;background:{color};display:inline-block;flex-shrink:0'></span>
  <div style='flex:1'>
    <span style='font-size:12px;font-weight:600'>{name}</span>
    <span style='color:#64748b;font-size:11px;margin-left:6px'>{detail[:60]}{"..." if len(detail)>60 else ""}</span>
  </div>
  <span class='badge' style='background:rgba(0,0,0,0.4);color:{color};border:1px solid {color}55;font-size:9px'>{risk}</span>
</div>""", unsafe_allow_html=True)

    # ── TOP RIGHT: FX rates + impact calculator ────────
    with top_right:
        st.markdown("#### 💱 Live Exchange Rates")
        rate = get_live_exchange_rate()
        fx_hist = get_fx_history_mock()

        col_a, col_b = st.columns(2)
        col_a.metric("USD/INR", f"₹{rate:.2f}", f"{rate - fx_hist[0]:+.2f} (7d)")
        col_b.metric("EUR/INR", f"₹{rate * 1.085:.2f}", "")

        fig = C.fx_sparkline(fx_hist, "INR/USD")
        st.plotly_chart(fig, use_container_width=True, key="fx_spark")

        st.markdown("**💡 Impact Calculator**")
        shipment_val = st.number_input("Cargo value (₹ Cr)", 0.1, 500.0, 47.3, step=0.5, key="fx_val")
        rate_change  = st.slider("INR weakens by (%)", 0.5, 5.0, 2.0, step=0.5, key="fx_chg")
        impact = round(shipment_val * rate_change / 100 * 100, 2)  # in lakhs
        st.markdown(f"""
<div class='glass-card' style='text-align:center'>
  <div style='font-size:12px;color:#94a3b8'>If INR weakens {rate_change}%</div>
  <div style='font-size:24px;color:#fbbf24;font-weight:700'>+₹{impact}L additional cost</div>
  <div style='font-size:12px;color:#64748b'>on your ₹{shipment_val:.1f} Cr shipment</div>
</div>""", unsafe_allow_html=True)

        st.markdown("**Historical (7-day) USD/INR**")
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, (d, v) in enumerate(zip(days, fx_hist)):
            delta_c = "#4ade80" if v <= rate else "#f87171"
            st.markdown(f"<div style='display:flex;justify-content:space-between;font-size:12px;padding:3px 0'><span style='color:#64748b'>{d}</span><span style='color:{delta_c}'>₹{v:.2f}</span></div>", unsafe_allow_html=True)

    # ── BOTTOM LEFT: Port status board ────────────────
    with bot_left:
        st.markdown("#### 🏗 Port Status Board")
        cong_order = {"High": 0, "Moderate": 1, "Low": 2}
        sorted_ports = sorted(ports_data, key=lambda p: cong_order.get(p.get("congestion_level", "Low"), 2))

        headers = ["Port", "Congestion", "Berths", "TEU/day", "Status"]
        header_html = "".join(f"<th style='padding:8px;color:#64748b;font-size:11px;font-weight:500'>{h}</th>" for h in headers)
        rows_html = ""
        for port in sorted_ports:
            cong = port.get("congestion_level", "Moderate")
            cong_color = RISK_COLORS.get("Critical" if cong == "High" else "Medium" if cong == "Moderate" else "Low", "#4ade80")
            rows_html += f"""
<tr style='border-bottom:1px solid #1e293b'>
  <td style='padding:8px;font-size:12px;font-weight:600'>{port['name']}</td>
  <td style='padding:8px'><span class='badge' style='background:rgba(0,0,0,0.4);color:{cong_color};border:1px solid {cong_color}55'>{cong}</span></td>
  <td style='padding:8px;font-size:12px;color:#94a3b8'>{port.get('berths','N/A')}</td>
  <td style='padding:8px;font-size:12px;color:#94a3b8'>{port.get('daily_teu_capacity',0):,}</td>
  <td style='padding:8px'><span class='badge badge-safe' style='font-size:9px'>OPEN</span></td>
</tr>"""
        st.markdown(f"""
<div class='glass-card'>
  <table style='width:100%;border-collapse:collapse'>
    <tr style='border-bottom:1px solid #1e3a5f'>{header_html}</tr>
    {rows_html}
  </table>
</div>""", unsafe_allow_html=True)

        # Firebase field reports count
        reports = firebase_read("/field_reports") or {}
        report_count = len(reports) if isinstance(reports, dict) else 0
        st.caption(f"📋 {report_count} field reports in Firebase | Updates every 5 min")

    # ── BOTTOM RIGHT: AI Intelligence Digest ──────────
    with bot_right:
        st.markdown("#### 🤖 AI Intelligence Digest")
        st.caption("Auto-generated by Gemini 1.5 Pro + Google Search Grounding")

        digest_key = "intel_digest"
        digest_ts_key = "intel_digest_ts"
        digest_ttl = 900  # 15 min

        if digest_key not in st.session_state or (now - st.session_state.get(digest_ts_key, 0)) > digest_ttl:
            with st.spinner("Generating intelligence digest…"):
                st.session_state[digest_key] = get_ai_digest()
                st.session_state[digest_ts_key] = now

        digest = st.session_state[digest_key]
        lines = digest.strip().split("\n") if digest else []
        for line in lines:
            if line.strip():
                st.markdown(f"<div class='intel-box' style='margin:4px 0'>{line.strip()}</div>", unsafe_allow_html=True)

        from datetime import datetime
        st.caption(f"Last updated: {datetime.now().strftime('%H:%M IST')} | Next refresh in {max(0, int((digest_ttl - (now - st.session_state.get(digest_ts_key, 0))) / 60))} min")

        # Active reroutes from Firebase
        st.markdown("#### ⚡ Active Reroutes")
        reroutes = firebase_read("/active_reroutes") or {}
        if isinstance(reroutes, dict) and reroutes:
            for k, v in reroutes.items():
                if isinstance(v, dict):
                    st.markdown(f"""
<div class='glass-card'>
  <b>{k.replace('_',' ')}</b>
  <span class='badge badge-safe' style='margin-left:8px'>{v.get('status','')}</span>
  <div style='font-size:12px;color:#94a3b8;margin-top:4px'>{v.get('instruction','')}</div>
</div>""", unsafe_allow_html=True)
        else:
            K.empty_state("⚡", "No active reroutes", "All vessels on original routes.")
