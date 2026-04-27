# -*- coding: utf-8 -*-
"""Overview Dashboard — full-width map + KPIs + Risk Matrix + Alerts."""
import streamlit as st
from datetime import datetime

from logistiq.data import vessels_data, ports_data, trucks_data, rail_schedules_data
from logistiq.components import maps as M, charts as C, cards as K


def render():
    shipments_list = st.session_state.shipments

    # ── PART A — Onboarding welcome ────────────────────
    if len(shipments_list) == 0 and not st.session_state.cyclone_triggered:
        st.markdown("""
        <div class='welcome-card'>
          <div style='font-size:48px'>🚢</div>
          <div>
            <div class='welcome-title'>Welcome to LogistiQ Command Center</div>
            <div class='welcome-sub'>
              Monitor your supply chain across Sea, Rail, Road and Air in real time.<br>
              Start by <b>adding a shipment</b> or <b>running a simulation</b> to see how AI
              protects your cargo from disruptions.
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)
        w1, w2 = st.columns(2)
        with w1:
            if st.button("📦 Add My First Shipment", type="primary", use_container_width=True):
                st.query_params["p"] = "add_shipment"
                st.session_state.show_add_form = True
                st.session_state.active_page = "add_shipment"
                st.rerun()
        with w2:
            if st.button("🧪 Run Demo Simulation", use_container_width=True):
                st.session_state.cyclone_triggered = True
                st.session_state.active_page = "simulation"
                st.session_state.sim_stage = 1
                st.rerun()

    # ── PART B — Ticker ────────────────────────────────
    alerts = st.session_state.get("alerts", [])
    ticker_text = ""
    if st.session_state.cyclone_triggered:
        ticker_text += "🔴 LIVE: CYCLONE CAT.3 ACTIVE — Chennai Port BLOCKED &nbsp;|&nbsp; "
    
    ticker_items = " &nbsp;|&nbsp; ".join(
        f"{'🔴' if a['severity']=='Critical' else '🟠' if a['severity']=='High' else '🟡'} {a['message']}"
        for a in alerts
    )
    if not ticker_items and not st.session_state.cyclone_triggered:
        ticker_text += "✅ No active disruptions on Chennai–Vizag corridor today"
    else:
        ticker_text += ticker_items
        
    st.markdown(f"""
<div class='ticker-wrap'>
  <div class='ticker-move'><span>{ticker_text}</span></div>
</div>""", unsafe_allow_html=True)

    # ── PART C — Page header row ───────────────────────
    h1, h2 = st.columns([3, 1])
    with h1:
        st.markdown("<h2 style='margin:0 0 4px'>🗺 Command Overview</h2>", unsafe_allow_html=True)
        st.caption(f"Chennai–Vizag–Manesar Freight Corridor · {datetime.now().strftime('%d %b %Y, %H:%M IST')}")
    with h2:
        if st.session_state.cyclone_triggered:
            st.markdown("<div style='text-align:right;margin-top:10px'><span class='badge badge-critical' style='animation:pulse 1s infinite'>CYCLONE ACTIVE</span></div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='text-align:right;margin-top:10px'><span class='badge badge-safe'>All Clear</span></div>", unsafe_allow_html=True)

    # ── PART D — KPI row (5 metrics) ───────────────────
    if not st.session_state.get("dismiss_risk_banner", False) and shipments_list:
        curr_hash = hash(str([(s.get('id'), s.get('risk_analyzed')) for s in shipments_list]))
        if st.session_state.get("banner_shipment_hash") != curr_hash:
            try:
                from logistiq.utils.gemini import cached_gemini_call
                shipment_subset = [{"id": s.get("id"), "cargo": s.get("cargo_desc"), "risk_data": s.get("risk_data")} for s in shipments_list]
                prompt = f"Given these shipments: {shipment_subset}. Return JSON with up to top 3 at-risk shipments. Format: {{\"at_risk\": [{{\"id\": \"...\", \"reason\": \"...\", \"delay_hrs\": ...}}]}}"
                res = cached_gemini_call(prompt, response_mime_type="application/json")
                import json
                data = json.loads(res)
                st.session_state.at_risk_banner_data = data.get("at_risk", [])
            except Exception:
                st.session_state.at_risk_banner_data = []
            st.session_state.banner_shipment_hash = curr_hash

        banner_data = st.session_state.get("at_risk_banner_data", [])
        if banner_data:
            with st.container(border=True):
                st.markdown("#### 🚨 AI Alert: Top At-Risk Shipments")
                cols = st.columns(len(banner_data) + 1)
                for i, r in enumerate(banner_data):
                    with cols[i]:
                        st.markdown(f"**{r.get('id')}**\n\n*{r.get('reason')}*\n\n**Predicted Delay:** {r.get('delay_hrs')} hrs")
                        if st.button("🗺️ View Journey", key=f"btn_journey_banner_{r.get('id')}", use_container_width=True):
                            shp = next((s for s in shipments_list if s.get('id') == r.get('id')), None)
                            if shp:
                                st.session_state.selected_shipment = shp
                                st.session_state.active_page = "journey"
                                st.query_params["p"] = "journey"
                                st.rerun()
                with cols[-1]:
                    if st.button("✖ Dismiss", key="dismiss_banner", use_container_width=True):
                        st.session_state.dismiss_risk_banner = True
                        st.rerun()

    # Disaster Relief Mode Override Check
    if st.session_state.get("relief_mode", False):
        st.markdown("""
        <div class='glass-card' style='border-color:#60a5fa;background:rgba(96,165,250,0.05)'>
          <div style='font-size:14px;font-weight:700;color:#60a5fa;margin-bottom:8px'>
            🆘 DISASTER RELIEF OPERATIONS — Andhra Pradesh Flood Response
          </div>
          <div style='display:flex;gap:20px;flex-wrap:wrap;font-size:12px;color:#94a3b8'>
            <span>💊 2,400 Medical Kits</span>
            <span>💧 840 Water Purifiers</span>
            <span>🍱 12 tons Food Packets</span>
            <span>🏥 Consignee: AP SDMA</span>
            <span>⏰ Delivery window: 18 hrs (CRITICAL)</span>
          </div>
        </div>""", unsafe_allow_html=True)
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Lives Supported", "24,000+", "Estimated")
        r2.metric("Medicine ETA", "14 hrs", "On track")
        r3.metric("Road Clearance", "NH16 open", "Confirmed")
        r4.metric("Hospital Reach", "3 / 3", "All covered")
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    else:
        at_risk   = sum(1 for s in shipments_list if (s.get("risk_data") or {}).get("risk_level") in ("High", "Critical"))
        exposure  = sum(float(s.get("value_crore", 0)) for s in shipments_list)
        on_time   = len(shipments_list) - at_risk
        on_pct    = int(on_time / max(len(shipments_list), 1) * 100)
        at_sea    = sum(1 for v in vessels_data if v.get("status") == "At Sea")

        k1, k2, k3, k4, k5 = st.columns(5)
        kpi_data = [
            (k1, "🚢", "Active Vessels",    str(len(vessels_data)), f"{at_sea} at sea",     True),
            (k2, "💰", "Exposure",          f"₹{exposure:.1f}Cr",   f"{at_risk} at risk",   at_risk == 0),
            (k3, "⚠️", "SLA Risk",          "MEDIUM" if at_risk else "LOW", "",              at_risk == 0),
            (k4, "✅", "On Time",           f"{on_pct}%",           f"{on_time}/{max(len(shipments_list),1)}", on_pct >= 80),
            (k5, "📦", "Shipments",         str(len(shipments_list)), "tracked",             True),
        ]
        for col, icon, label, value, delta, good in kpi_data:
            with col:
                K.render_metric_card(label, value, delta, icon, good)
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── PART E — Two column layout ─────────────────────
    map_col, matrix_col = st.columns([3, 2])

    with map_col:
        st.markdown("<div class='section-header'>🗺 Live Operational Map</div>", unsafe_allow_html=True)
        fmap = M.make_base_map()
        M.add_ports(fmap, ports_data)
        M.add_vessels(fmap, vessels_data,
                      at_risk_ids={"VSL-CHN-001"} if st.session_state.cyclone_triggered else set())
        M.add_trucks(fmap, trucks_data)
        M.add_rail_corridor(fmap, rail_schedules_data)
        if st.session_state.cyclone_triggered:
            M.add_cyclone(fmap)
        if st.session_state.reroute_accepted:
            M.add_reroute_path(fmap)
        M.render_map(fmap, height=400)
        
        # Compact vessel list below map
        vc1, vc2, vc3 = st.columns(3)
        for i, v in enumerate(vessels_data[:3]):
            col = [vc1, vc2, vc3][i]
            is_risk = st.session_state.cyclone_triggered and v.get("id") == "VSL-CHN-001"
            border = "border:1px solid #f87171; animation:pulse 1.2s infinite" if is_risk else "border:1px solid rgba(96,165,250,0.18)"
            pill = f"<span class='badge {'badge-critical' if is_risk else 'badge-safe'}'>{v.get('status')}</span>"
            with col:
                st.markdown(f"""
                <div class='glass-card' style='padding:10px;{border}'>
                  <div style='font-size:12px;font-weight:700;color:#e7efff;margin-bottom:4px'>{v.get("name")}</div>
                  <div style='font-size:10px;color:#94a3b8;margin-bottom:4px'>{v.get("cargo")} | {v.get("speed_knots")} kn</div>
                  <div style='display:flex;justify-content:space-between;align-items:center'>
                    {pill} <span style='font-size:10px'>ETA: {v.get("eta")}</span>
                  </div>
                </div>""", unsafe_allow_html=True)

    with matrix_col:
        st.markdown("<div class='section-header'>🎯 Risk Matrix</div>", unsafe_allow_html=True)
        if not shipments_list:
            st.markdown("""
            <div class='empty-state glass-card' style='height:300px;display:flex;flex-direction:column;justify-content:center'>
              <div style='font-size:32px;margin-bottom:10px'>📊</div>
              <div class='empty-title'>Risk matrix will appear here once you add shipments</div>
            </div>""", unsafe_allow_html=True)
            if st.button("➕ Add Shipment", use_container_width=True):
                st.query_params["p"] = "add_shipment"
                st.session_state.show_add_form = True
                st.session_state.active_page = "add_shipment"
                st.rerun()
        else:
            fig = C.risk_matrix_chart(shipments_list)
            st.plotly_chart(fig, use_container_width=True, key="ov_matrix")

            # Compact shipment summary
            for s in shipments_list[:3]:
                rd = s.get("risk_data") or {}
                level = rd.get("risk_level", "Unknown")
                colors = {"Critical":"#f87171","High":"#fbbf24","Medium":"#60a5fa","Low":"#4ade80"}
                c = colors.get(level, "#94a3b8")
                score = rd.get("risk_score", 0)
                st.markdown(f"""
<div style='display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid #1e293b'>
  <div class='risk-ring' style='width:32px;height:32px;border-width:2px;font-size:11px;border-color:{c};color:{c}'>{score}</div>
  <div style='flex:1;min-width:0'>
    <div style='font-size:11px;font-weight:600;color:#e7efff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis'>{s.get("cargo_desc","")[:28]}</div>
    <div style='font-size:10px;color:#64748b'>{s.get("origin","")[:12]} → {s.get("destination","")[:12]}</div>
  </div>
  {K.risk_badge(level)}
</div>""", unsafe_allow_html=True)

    # ── PART F — Alerts feed ───────────────────────────
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-header'>🔔 Live Alerts</div>", unsafe_allow_html=True)

    if alerts:
        ac = st.columns(min(len(alerts[:3]), 3))
        for i, a in enumerate(alerts[:3]):
            sev = a.get("severity", "Medium")
            icons = {"Critical":"🔴","High":"🟠","Medium":"🟡","Low":"🟢"}
            sev_c = {"Critical":"#f87171","High":"#fb923c","Medium":"#fbbf24","Low":"#4ade80"}
            ic = icons.get(sev, "🔵")
            col = sev_c.get(sev, "#60a5fa")
            is_cyclone = st.session_state.cyclone_triggered and "Cyclone" in a.get("message", "")
            anim = "animation:pulse 1.2s infinite;" if is_cyclone else ""
            with ac[i]:
                st.markdown(f"""
<div class='glass-card' style='border-color:{col}33;padding:14px;{anim}'>
  <div style='display:flex;align-items:center;gap:6px;margin-bottom:6px'>
    <span style='font-size:18px'>{ic}</span>
    {K.risk_badge(sev)}
  </div>
  <div style='font-size:12px;color:#e7efff;line-height:1.5'>{a.get("message","")}</div>
  <div style='font-size:10px;color:#475569;margin-top:4px'>⏱ {a.get("timestamp","")}</div>
</div>""", unsafe_allow_html=True)
    else:
        K.empty_state("✅", "All Clear", "No active alerts on any corridor.")

    # ── PART G — Quick actions ─────────────────────────
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("🌀 Cyclone Simulation", use_container_width=True):
            st.session_state.cyclone_triggered = True
            st.query_params["p"] = "simulation"
            st.session_state.active_page = "simulation"
            st.rerun()
    with c2:
        if st.button("🚢 Sea Ops", use_container_width=True):
            st.query_params["p"] = "sea"
            st.session_state.active_page = "sea"
            st.rerun()
    with c3:
        if st.button("📡 Intelligence", use_container_width=True):
            st.query_params["p"] = "intelligence"
            st.session_state.active_page = "intelligence"
            st.rerun()
    with c4:
        if st.button("📦 Add Shipment", use_container_width=True, type="primary"):
            st.query_params["p"] = "add_shipment"
            st.session_state.show_add_form = True
            st.session_state.active_page = "add_shipment"
            st.rerun()
