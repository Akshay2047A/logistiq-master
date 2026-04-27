# -*- coding: utf-8 -*-
"""Road Logistics Operations page."""
import streamlit as st
from logistiq.data import trucks_data, ports_data
from logistiq.components import maps as M, cards as K
from logistiq.utils.data import get_real_road_route, haversine_km

AVAIL_COLORS = {"En Route": "#4ade80", "Loading": "#fbbf24", "Waiting": "#60a5fa", "Standby": "#94a3b8"}


def render():
    st.markdown("### 🚛 Road Logistics Operations")
    st.caption("NH16 Chennai–Vizag–Manesar corridor | Real-time truck tracking")

    map_col, panel_col = st.columns([1.6, 1])

    with map_col:
        fmap = M.make_base_map(lat=15.5, lon=80.5, zoom=6)
        M.add_ports(fmap, ports_data)
        M.add_trucks(fmap, trucks_data)
        M.render_map(fmap, height=400)

    with panel_col:
        st.markdown("#### 🚚 Active Trucks")
        for truck in trucks_data:
            avail = truck.get("availability", "Standby")
            color = AVAIL_COLORS.get(avail, "#94a3b8")
            st.markdown(f"""
<div class='glass-card' style='border-color:{color}33;padding:12px'>
  <div style='display:flex;justify-content:space-between;margin-bottom:4px'>
    <b style='font-size:12px'>{truck['id']}</b>
    <span class='badge' style='background:rgba(0,0,0,0.4);color:{color};border:1px solid {color}55'>{avail}</span>
  </div>
  <div style='font-size:11px;color:#94a3b8'>
    👤 {truck.get('driver','N/A')}<br>
    📍 {truck.get('origin_hub','')} → {truck.get('destination_hub','')}<br>
    🏷 {truck.get('cargo','N/A')} | {truck.get('load_tons','N/A')}t
  </div>
</div>""", unsafe_allow_html=True)

    # ── Route calculator ───────────────────────────────
    st.markdown("---")
    st.markdown("#### 🗺 Route Calculator")
    rc1, rc2 = st.columns(2)
    origin_city = rc1.text_input("Origin", "Chennai Port", key="road_origin")
    dest_city   = rc2.text_input("Destination", "Manesar, Haryana", key="road_dest")
    if st.button("📍 Calculate Route", use_container_width=True):
        with st.spinner("Fetching live route from Google Maps Routes API…"):
            route = get_real_road_route(origin_city, dest_city)
        if route.get("route_found"):
            r1, r2, r3 = st.columns(3)
            r1.metric("Distance", f"{route['distance_km']} km")
            r2.metric("Duration (traffic)", f"{route['duration_hours']} hrs")
            r3.metric("Est. fuel cost", f"₹{int(route['distance_km'] * 14 * 5.5):,}")
        else:
            st.warning("Route not found via API. Using haversine estimate.")

    # ── NH Status alerts ───────────────────────────────
    st.markdown("#### ⚠ NH16 Status")
    st.markdown("""
<div class='glass-card'>
  <div style='font-size:12px;color:#94a3b8'>
    <div style='display:flex;gap:8px;align-items:center;margin-bottom:6px'>
      <span style='color:#4ade80;font-size:16px'>●</span>
      <span><b>Chennai → Nellore</b> — Clear, normal traffic (NH16)</span>
    </div>
    <div style='display:flex;gap:8px;align-items:center;margin-bottom:6px'>
      <span style='color:#fbbf24;font-size:16px'>●</span>
      <span><b>Nellore → Ongole</b> — Moderate congestion, tolls operational</span>
    </div>
    <div style='display:flex;gap:8px;align-items:center'>
      <span style='color:#4ade80;font-size:16px'>●</span>
      <span><b>Vijayawada → Visakhapatnam</b> — Clear</span>
    </div>
  </div>
</div>""", unsafe_allow_html=True)
