# -*- coding: utf-8 -*-
"""Map rendering functions using Folium."""
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
import streamlit as st


def make_base_map(lat: float = 15.0, lon: float = 82.0, zoom: int = 6) -> folium.Map:
    return folium.Map(
        location=[lat, lon],
        zoom_start=zoom,
        tiles="CartoDB Dark_Matter",
        control_scale=True,
    )


# ---------------------------------------------------------------------------
# Port circles
# ---------------------------------------------------------------------------

CONGESTION_COLORS = {"Low": "#22c55e", "Moderate": "#f59e0b", "High": "#ef4444"}


def add_ports(fmap: folium.Map, ports: list, scale_by_teu: bool = True):
    for port in ports:
        clr = CONGESTION_COLORS.get(port.get("congestion_level", "Moderate"), "#f59e0b")
        teu = port.get("daily_teu_capacity", 5000)
        radius = 8 + (teu / 15000) * 14 if scale_by_teu else 12
        folium.CircleMarker(
            location=[port["lat"], port["lon"]],
            radius=radius,
            color=clr,
            fill=True,
            fill_opacity=0.55,
            popup=(
                f"<b>{port['name']}</b><br>"
                f"Congestion: {port.get('congestion_level','Moderate')}<br>"
                f"Berths: {port.get('berths','N/A')}<br>"
                f"TEU/day: {teu:,}"
            ),
        ).add_to(fmap)


# ---------------------------------------------------------------------------
# Vessel markers (animated SVG ship icons)
# ---------------------------------------------------------------------------

SHIP_SVG = (
    "<svg width='22' height='22' viewBox='0 0 16 16' xmlns='http://www.w3.org/2000/svg'>"
    "<path fill='{color}' d='M0 14s1.5 2 4 2 4-2 4-2 1.5 2 4 2 4-2 4-2v-1l-1-.5V8.5L8 4 1 8.5V12.5L0 13v1z'/>"
    "</svg>"
)


def add_vessels(fmap: folium.Map, vessels: list, at_risk_ids: set | None = None):
    at_risk_ids = at_risk_ids or set()
    for v in vessels:
        is_risk = v.get("id") in at_risk_ids
        color = "#ff5a83" if is_risk else "#44c5ff"
        pulse = "animation:pulse 1s infinite;" if is_risk else ""
        svg = SHIP_SVG.format(color=color)
        folium.Marker(
            [v["lat"], v["lon"]],
            tooltip=v["name"],
            popup=(
                f"<b>{v['name']}</b><br>Status: {v.get('status','N/A')}<br>"
                f"Cargo: {v.get('cargo_type','N/A')}<br>"
                f"ETA: {v.get('eta_utc','N/A')}<br>Speed: {v.get('speed_knots','N/A')} kn"
            ),
            icon=folium.DivIcon(html=f"<div style='{pulse}'>{svg}</div>"),
        ).add_to(fmap)


# ---------------------------------------------------------------------------
# Trucks
# ---------------------------------------------------------------------------

def add_trucks(fmap: folium.Map, trucks: list):
    for t in trucks:
        avail = t.get("availability", "")
        color = "#4ade80" if avail == "En Route" else "#fbbf24" if avail in ("Loading", "Waiting") else "#94a3b8"
        folium.Marker(
            [t["lat"], t["lon"]],
            tooltip=t["id"],
            popup=(
                f"<b>{t['id']}</b><br>Driver: {t.get('driver','N/A')}<br>"
                f"Status: {avail}<br>Cargo: {t.get('cargo','N/A')}<br>"
                f"Load: {t.get('load_tons','N/A')}t"
            ),
            icon=folium.DivIcon(
                html=f"<div style='font-size:20px;color:{color}'>🚛</div>"
            ),
        ).add_to(fmap)


# ---------------------------------------------------------------------------
# Cyclone overlay
# ---------------------------------------------------------------------------

def add_cyclone(fmap: folium.Map, lat: float = 14.8, lon: float = 85.6, radius_km: int = 320):
    folium.Circle(
        location=[lat, lon],
        radius=radius_km * 1000,
        color="#ff5a83",
        fill=True,
        fill_opacity=0.12,
        dash_array="8,6",
    ).add_to(fmap)
    folium.Marker(
        [lat, lon],
        icon=folium.DivIcon(html="<div style='font-size:16px;color:#ff5a83'>🌀 Cat.3 Cyclone</div>"),
    ).add_to(fmap)


# ---------------------------------------------------------------------------
# Reroute path
# ---------------------------------------------------------------------------

def add_reroute_path(fmap: folium.Map):
    AntPath([[13.5, 83.2], [17.6868, 83.2818]], color="#FF6B35", weight=4, delay=800, dash_array=[10, 20]).add_to(fmap)
    folium.PolyLine([[17.6868, 83.2818], [17.68, 83.21]], color="#fbbf24", weight=4).add_to(fmap)
    folium.PolyLine([[17.68, 83.21], [17.4399, 78.4983]], color="#22c55e", weight=4).add_to(fmap)
    legend = """
    <div style='position:fixed;bottom:30px;left:30px;z-index:9999;
                background:rgba(8,15,30,.9);color:#fff;padding:8px 12px;
                border-radius:8px;font-size:12px;'>
      <div><span style='color:#FF6B35'>━━</span> Sea diversion</div>
      <div><span style='color:#fbbf24'>━━</span> Port → Rail terminal</div>
      <div><span style='color:#22c55e'>━━</span> Rail inland leg</div>
    </div>"""
    fmap.get_root().html.add_child(folium.Element(legend))


# ---------------------------------------------------------------------------
# Rail corridor line
# ---------------------------------------------------------------------------

def add_rail_corridor(fmap: folium.Map, rail_schedules: list):
    for r in rail_schedules:
        orig = (r.get("origin_lat"), r.get("origin_lng"))
        dest = (r.get("destination_lat"), r.get("destination_lng"))
        if all(orig) and all(dest):
            folium.PolyLine(
                [list(orig), list(dest)],
                color="#fbbf24",
                weight=2,
                dash_array="6,4",
                opacity=0.7,
                tooltip=f"Train {r.get('train_id')} — {r.get('name')}",
            ).add_to(fmap)


# ---------------------------------------------------------------------------
# Global chokepoint world map
# ---------------------------------------------------------------------------

CHOKEPOINTS = [
    {"name": "Red Sea / Bab el-Mandeb", "lat": 12.5, "lon": 43.3, "key": "red_sea"},
    {"name": "Suez Canal", "lat": 30.4, "lon": 32.3, "key": "suez_canal"},
    {"name": "Strait of Malacca", "lat": 2.5, "lon": 101.5, "key": "malacca_strait"},
    {"name": "Bay of Bengal", "lat": 12.0, "lon": 87.0, "key": "bay_of_bengal"},
    {"name": "Strait of Hormuz", "lat": 26.5, "lon": 56.3, "key": "strait_of_hormuz"},
]

RISK_COLORS = {"Critical": "#f87171", "High": "#fb923c", "Medium": "#fbbf24", "Low": "#4ade80"}


def make_world_chokepoint_map(intel: dict) -> folium.Map:
    fmap = folium.Map(location=[20.0, 50.0], zoom_start=3, tiles="CartoDB Dark_Matter")
    for cp in CHOKEPOINTS:
        data = intel.get(cp["key"], {})
        risk = data.get("risk", "Low")
        color = RISK_COLORS.get(risk, "#60a5fa")
        detail = data.get("detail", "")
        affected = data.get("vessels_affected", data.get("cyclone_active", ""))
        folium.CircleMarker(
            location=[cp["lat"], cp["lon"]],
            radius=14,
            color=color,
            fill=True,
            fill_opacity=0.7,
            popup=f"<b>{cp['name']}</b><br>Risk: {risk}<br>{detail}<br>Vessels affected: {affected}",
            tooltip=f"{cp['name']} — {risk}",
        ).add_to(fmap)
    return fmap


def render_map(fmap: folium.Map, height: int = 520):
    map_data = st_folium(fmap, use_container_width=True, height=height, returned_objects=["last_object_clicked", "zoom"])
    if map_data:
        st.session_state.map_click = map_data
    
    if st.session_state.get("map_click"):
        click = st.session_state.map_click.get("last_object_clicked")
        zoom = st.session_state.map_click.get("zoom")
        if click:
            st.markdown(f"<div class='glass-card' style='font-size:12px;margin-top:10px'><b>🗺 Map Data</b> | Clicked: {click.get('lat'):.4f}, {click.get('lng'):.4f} | Zoom: {zoom}</div>", unsafe_allow_html=True)
