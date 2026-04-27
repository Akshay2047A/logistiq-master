# -*- coding: utf-8 -*-
"""Rail Freight Operations page."""
import streamlit as st
from logistiq.data import rail_schedules_data, ports_data, trucks_data
from logistiq.components import maps as M, cards as K


STATUS_COLORS = {"on_time": "#4ade80", "delayed": "#f87171", "cancelled": "#fb923c"}


def render():
    st.markdown("### 🚂 Rail Freight Operations")
    st.caption("South Central Railway corridor — Chennai–Vizag–Secunderabad")

    map_col, info_col = st.columns([1.5, 1.2])

    with map_col:
        st.markdown("<div class='section-header'>🚆 Live Rail Tracking</div>", unsafe_allow_html=True)
        fmap = M.make_base_map(lat=16.0, lon=80.5, zoom=6)
        M.add_ports(fmap, ports_data)
        M.add_rail_corridor(fmap, rail_schedules_data)
        if st.session_state.get("reroute_accepted"):
            M.add_reroute_path(fmap)
        M.render_map(fmap, height=500)

    with info_col:
        tab_track, tab_co2 = st.tabs(["🚆 Live Tracking", "🌱 Sustainability"])

        with tab_track:
            st.markdown("#### 🚆 Active Rail Schedules")
            for train in rail_schedules_data:
                status = train.get("status", "on_time")
                color  = STATUS_COLORS.get(status, "#60a5fa")
                delay_reason = train.get("delay_reason", "")
                st.markdown(f"""
<div class='glass-card' style='border-color:{color}44'>
  <div style='display:flex;justify-content:space-between;margin-bottom:6px'>
    <b>Train {train['train_id']} — {train['name']}</b>
    <span class='badge' style='background:rgba(0,0,0,0.4);color:{color};border:1px solid {color}55'>
      {status.replace('_',' ').upper()}
    </span>
  </div>
  <div style='font-size:12px;color:#94a3b8'>
    📍 {train['origin']} → {train['destination']}<br>
    🕐 Departs {train['departure_time']} | Arrives {train['arrival_time']} ({train['journey_hours']} hrs)<br>
    🚃 {train['available_wagons']} wagons available | Max {train['max_load_tons']}t<br>
    🏷 Platform {train.get('platform','N/A')}
  </div>
  {f"<div style='margin-top:6px;font-size:11px;color:#fbbf24'>⚠ {delay_reason}</div>" if delay_reason else ""}
</div>""", unsafe_allow_html=True)

        with tab_co2:
            st.markdown("#### 📊 Carbon Displacement: Rail vs Road")
            st.markdown("<div style='font-size:12px;color:#94a3b8;margin-bottom:14px'>Moving cargo via SCR reduces carbon footprint by ~80% per ton-km vs trucking on NH16.</div>", unsafe_allow_html=True)

            co2_data = [
                ("Auto Parts", 220, 40, 180),
                ("Electronics", 150, 30, 120),
                ("Textiles", 310, 60, 250),
                ("Pharma", 140, 25, 115),
            ]

            for label, road_co2, rail_co2, saved in co2_data:
                road_pct = 100
                rail_pct = int((rail_co2 / road_co2) * 100)
                st.markdown(f"""
<div class='glass-card' style='padding:12px'>
  <div style='font-size:12px;font-weight:700;color:#e7efff;margin-bottom:8px'>{label}</div>
  <div class='co2-row'>
    <div class='co2-label' style='color:#f87171'>Road</div>
    <div class='co2-track'><div class='co2-fill' style='width:{road_pct}%;background:#f87171'></div></div>
    <div class='co2-value' style='color:#f87171'>{road_co2}t</div>
  </div>
  <div class='co2-row'>
    <div class='co2-label' style='color:#4ade80'>Rail</div>
    <div class='co2-track'><div class='co2-fill' style='width:{rail_pct}%;background:#4ade80'></div></div>
    <div class='co2-value' style='color:#4ade80'>{rail_co2}t</div>
  </div>
  <div style='font-size:10px;color:#94a3b8;margin-top:6px'>Saved: <b>{saved} tons CO₂</b></div>
</div>""", unsafe_allow_html=True)

            total_saved = sum(saved for _, _, _, saved in co2_data)
            st.markdown(f"""
<div style='background:rgba(74,222,128,0.1);border:1px solid #4ade80;border-radius:12px;padding:16px;text-align:center;margin-top:16px'>
  <div style='font-size:12px;color:#4ade80;font-weight:700;text-transform:uppercase'>Total Carbon Saved (MTD)</div>
  <div style='font-size:36px;font-weight:800;color:#4ade80;margin:6px 0;line-height:1'>{total_saved} tons</div>
  <div style='font-size:11px;color:#94a3b8'>Equivalent to planting 14,000 trees 🌳</div>
</div>""", unsafe_allow_html=True)

    # ── KPIs ───────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### 📊 Rail Corridor KPIs")
    k1, k2, k3, k4 = st.columns(4)
    on_time_count = sum(1 for t in rail_schedules_data if t.get("status") == "on_time")
    delayed_count = sum(1 for t in rail_schedules_data if t.get("status") == "delayed")
    total_wagons  = sum(t.get("available_wagons", 0) for t in rail_schedules_data)
    total_capacity = sum(t.get("max_load_tons", 0) for t in rail_schedules_data)
    k1.metric("Trains On Time", str(on_time_count), f"{on_time_count}/{len(rail_schedules_data)}")
    k2.metric("Delayed Trains", str(delayed_count), "⚠ Rajdhani priority" if delayed_count else "None")
    k3.metric("Available Wagons", str(total_wagons))
    k4.metric("Total Capacity", f"{total_capacity:,}t")
