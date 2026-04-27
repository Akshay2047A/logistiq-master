# -*- coding: utf-8 -*-
"""Folium map rendering functions for all pages."""

import folium
from folium.plugins import AntPath
import streamlit as st
from streamlit_folium import st_folium

def _render_and_store(fmap, height):
    map_data = st_folium(fmap, use_container_width=True, height=height, returned_objects=["last_object_clicked", "zoom"])
    if map_data:
        st.session_state.map_click = map_data
    if st.session_state.get("map_click"):
        click = st.session_state.map_click.get("last_object_clicked")
        if click:
            st.markdown(f"<div class='glass-card' style='font-size:12px;margin-top:10px;padding:8px'><b>🗺 Map Click</b> | Lat: {click.get('lat'):.4f}, Lng: {click.get('lng'):.4f}</div>", unsafe_allow_html=True)


def _ship_svg(color="#44c5ff"):
    return (
        "<svg width='22' height='22' viewBox='0 0 16 16' xmlns='http://www.w3.org/2000/svg'>"
        f"<path fill='{color}' d='M0 14s1.5 2 4 2 4-2 4-2 1.5 2 4 2 4-2 4-2v-1l-1-.5V8.5L8 4 1 8.5V12.5L0 13v1z'/>"
        "</svg>"
    )


def render_overview_map(vessels, ports, trucks, cyclone_on=False, reroute_on=False, height=520):
    fmap = folium.Map(location=[15.0, 82.0], zoom_start=6, tiles="CartoDB Dark_Matter", control_scale=True)

    cg_colors = {"Low": "#22c55e", "Moderate": "#f59e0b", "High": "#ef4444"}
    for port in ports:
        clr = cg_colors.get(port.get("congestion_level", "Moderate"), "#f59e0b")
        teu = port.get("daily_teu_capacity", 10000)
        folium.CircleMarker([port["lat"], port["lon"]], radius=max(8, min(18, teu / 1000)),
            color=clr, fill=True, fill_opacity=0.6,
            popup=f"<b>{port['name']}</b><br>Congestion: {port.get('congestion_level')}<br>Berths: {port.get('berths')}<br>TEU/day: {teu}").add_to(fmap)

    for v in vessels:
        risk = cyclone_on and v.get("name") == "MV Chennai Star"
        c = "#ff5a83" if risk else "#44c5ff"
        pulse = "animation:pulse 1.5s ease-in-out infinite;" if risk else ""
        folium.Marker([v["lat"], v["lon"]], tooltip=v["name"],
            popup=f"<b>{v['name']}</b><br>Status: {v.get('status')}<br>Cargo: {v.get('cargo_type')}<br>Speed: {v.get('speed_knots')} kn",
            icon=folium.DivIcon(html=f"<div style='{pulse}'>{_ship_svg(c)}</div>")).add_to(fmap)

    for t in trucks:
        av = t.get("availability", "")
        c = "#4ade80" if av in ("Waiting", "Standby") else "#ffd56a"
        folium.Marker([t["lat"], t["lon"]], tooltip=f"{t['id']} — {av}",
            icon=folium.DivIcon(html=f"<div style='font-size:18px;color:{c}'>🚛</div>")).add_to(fmap)

    # Rail corridor dashed line
    folium.PolyLine([[17.6868, 83.2818], [17.2041, 80.3523], [17.4399, 78.4983], [18.5204, 73.8567]],
        color="#fbbf24", weight=3, dash_array="10,8", tooltip="SCR Freight Corridor", opacity=0.6).add_to(fmap)

    if cyclone_on:
        folium.Circle([14.8, 85.6], radius=320000, color="#ff5a83", fill=True, fill_opacity=0.12, dash_array="8,6").add_to(fmap)
        folium.Marker([14.8, 85.6], icon=folium.DivIcon(html="<div style='font-size:16px;color:#ff5a83'>🌀 Cat.3 Cyclone</div>")).add_to(fmap)

    if reroute_on:
        AntPath([[13.5, 83.2], [17.6868, 83.2818]], color="#FF6B35", weight=4, delay=800, dash_array=[10, 20]).add_to(fmap)
        folium.PolyLine([[17.6868, 83.2818], [17.68, 83.21]], color="#fbbf24", weight=4).add_to(fmap)
        folium.PolyLine([[17.68, 83.21], [17.4399, 78.4983]], color="#22c55e", weight=4).add_to(fmap)

    _render_and_store(fmap, height)


def render_rail_map(height=350):
    fmap = folium.Map(location=[17.0, 80.5], zoom_start=6, tiles="CartoDB Dark_Matter")
    wps = [[17.6868, 83.2818], [17.2041, 80.3523], [17.4399, 78.4983], [18.5204, 73.8567]]
    labels = ["Visakhapatnam", "Vijayawada", "Secunderabad", "Pune"]
    folium.PolyLine(wps, color="#fbbf24", weight=4, dash_array="10,6", tooltip="SCR Freight Corridor").add_to(fmap)
    for wp, lb in zip(wps, labels):
        folium.Marker(wp, tooltip=lb, icon=folium.Icon(color="orange", icon="train", prefix="fa")).add_to(fmap)
    _render_and_store(fmap, height)


def render_road_map(trucks, cyclone_on=False, height=380):
    fmap = folium.Map(location=[15.5, 81.9], zoom_start=6, tiles="CartoDB Dark_Matter")
    for t in trucks:
        repo = cyclone_on and t.get("waiting_port_id") == "PRT-CHN"
        c = "#FF6B35" if repo else "#ffd56a"
        folium.Marker([t["lat"], t["lon"]], tooltip=t["id"] + (" — REPOSITIONING" if repo else ""),
            popup=f"{t['id']} | {t.get('driver', '')} | {t.get('availability', '')}",
            icon=folium.DivIcon(html=f"<div style='font-size:18px;color:{c}'>🚛</div>")).add_to(fmap)
    _render_and_store(fmap, height)


def render_chokepoint_map(intel_data=None, height=420):
    fmap = folium.Map(location=[20, 50], zoom_start=3, tiles="CartoDB Dark_Matter")
    cps = {
        "Red Sea": {"lat": 12.6, "lon": 43.4, "key": "red_sea"},
        "Suez Canal": {"lat": 30.5, "lon": 32.3, "key": "suez_canal"},
        "Strait of Malacca": {"lat": 2.5, "lon": 101.5, "key": "malacca_strait"},
        "Strait of Hormuz": {"lat": 26.5, "lon": 56.3, "key": "strait_of_hormuz"},
        "Bay of Bengal": {"lat": 14.0, "lon": 87.0, "key": "bay_of_bengal"},
    }
    rc = {"Critical": "#f87171", "High": "#fbbf24", "Medium": "#60a5fa", "Low": "#4ade80"}
    for name, cp in cps.items():
        d = (intel_data or {}).get(cp["key"], {})
        risk = d.get("risk", "Medium")
        folium.CircleMarker([cp["lat"], cp["lon"]], radius=14, color=rc.get(risk, "#60a5fa"),
            fill=True, fill_opacity=0.7, popup=f"<b>{name}</b><br>Risk: {risk}<br>{d.get('detail', 'N/A')}",
            tooltip=f"{name} — {risk}").add_to(fmap)
    _render_and_store(fmap, height)
