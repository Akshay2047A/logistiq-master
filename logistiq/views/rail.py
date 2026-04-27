# -*- coding: utf-8 -*-
"""Rail Freight Operations page."""
import streamlit as st
from logistiq.data import rail_schedules_data, ports_data, trucks_data
from logistiq.components import maps as M, cards as K


STATUS_COLORS = {"on_time": "#4ade80", "delayed": "#f87171", "cancelled": "#fb923c"}


def render():
    st.markdown("### 🚂 Rail Freight Operations")
    st.caption("South Central Railway corridor — Chennai–Vizag–Secunderabad")

    map_col, info_col = st.columns([1.5, 1])

    with map_col:
        fmap = M.make_base_map(lat=16.0, lon=80.5, zoom=6)
        M.add_ports(fmap, ports_data)
        M.add_rail_corridor(fmap, rail_schedules_data)
        M.render_map(fmap, height=400)

    with info_col:
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
