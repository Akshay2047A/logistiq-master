# -*- coding: utf-8 -*-
"""Map rendering functions using Folium."""
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath, HeatMap
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
    from logistiq.utils.data import CITY_COORDS
    port_coords = {
        "PRT-VSK": CITY_COORDS.get("vizag", (17.6868, 83.2185)),
        "PRT-CHN": CITY_COORDS.get("chennai", (13.0827, 80.2707)),
    }
    
    for v in vessels:
        is_risk = v.get("id") in at_risk_ids
        color = "#ff5a83" if is_risk else "#44c5ff"
        pulse = "animation:pulse 1s infinite;" if is_risk else ""
        svg = SHIP_SVG.format(color=color)
        
        if v.get("status") == "At Sea":
            orig = port_coords.get(v.get("origin_port_id"))
            if orig:
                AntPath(
                    locations=[orig, [v["lat"], v["lon"]]], 
                    color=color, weight=2, dash_array=[10, 20]
                ).add_to(fmap)
                
        folium.Marker(
            [v["lat"], v["lon"]],
            tooltip=f"{v['name']} | {v.get('speed_knots', 'N/A')} kn",
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
    radii = [150, 250, 350]  # km
    opacities = [0.25, 0.15, 0.08]
    for r, op in zip(radii, opacities):
        folium.Circle([lat, lon], radius=r*1000, color="#ff5a83",
            fill=True, fill_opacity=op, weight=1).add_to(fmap)
    folium.Marker(
        [lat, lon],
        icon=folium.DivIcon(html="<div style='font-size:14px;color:#ff5a83;white-space:nowrap;transform:translate(-50%,-100%);background:rgba(0,0,0,0.5);padding:2px 6px;border-radius:4px;'>🌀 Cat.3 — 180kph</div>"),
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


def add_risk_heatmap(fmap: folium.Map, shipments: list, intel_data: dict):
    from folium.plugins import HeatMap
    from logistiq.utils.data import resolve_city_coords
    points = []
    
    # Vessel / Shipment positions
    for s in shipments:
        lat = s.get("lat")
        lon = s.get("lon")
        if lat is None or lon is None:
            lat, lon = resolve_city_coords(s.get("origin", ""))
        
        score = (s.get("risk_data") or {}).get("risk_score", 0)
        # Fallback logic if passed vessels directly
        if score == 0 and "status" in s:
            score = 80 if s.get("id") in st.session_state.get("at_risk_vessels", []) else 20
            
        if lat is not None and lon is not None:
            points.append([lat, lon, score / 100.0])
            
    # Chokepoints
    for zone, data in intel_data.items():
        risk = data.get("risk", "Low")
        if risk in ["High", "Critical"]:
            for cp in CHOKEPOINTS:
                if cp["key"] == zone:
                    weight = 1.0 if risk == "Critical" else 0.8
                    points.append([cp["lat"], cp["lon"], weight])
                    
    HeatMap(points, radius=35, blur=20, max_zoom=6, name="Risk Heatmap").add_to(fmap)
    folium.LayerControl().add_to(fmap)


def add_shipment_route(fmap: folium.Map, shipment: dict):
    from logistiq.utils.data import resolve_city_coords
    orig = resolve_city_coords(shipment.get("origin", ""))
    dest_port = resolve_city_coords("Visakhapatnam" if shipment.get("vessel_name") else shipment.get("destination", ""))
    rail_yard = resolve_city_coords("Secunderabad")
    final_dest = resolve_city_coords(shipment.get("destination", ""))
    
    # 1. Sea leg: blue dashed PolyLine
    folium.PolyLine([orig, dest_port], color="#44c5ff", weight=3, dash_array="5,10").add_to(fmap)
    # 2. Rail leg: yellow solid PolyLine
    folium.PolyLine([dest_port, rail_yard], color="#fbbf24", weight=3).add_to(fmap)
    # 3. Road leg: green solid PolyLine
    folium.PolyLine([rail_yard, final_dest], color="#4ade80", weight=3).add_to(fmap)
    
    # 4. Handoff points
    handoffs = [
        (dest_port, "Port (Handoff to Rail)", "ETA: 48hrs"),
        (rail_yard, "Rail Yard (Handoff to Truck)", "ETA: 72hrs"),
        (final_dest, "Final Delivery", "ETA: 96hrs")
    ]
    for coords, name, eta in handoffs:
        folium.CircleMarker(
            location=coords,
            radius=10,
            color="#ffffff",
            fill=True,
            fill_opacity=0.8,
            popup=f"<b>{name}</b><br>{eta}"
        ).add_to(fmap)


def render_map(fmap: folium.Map, height: int = 520):
    map_data = st_folium(fmap, use_container_width=True, height=height, returned_objects=["last_object_clicked", "zoom"])
    if map_data:
        st.session_state.map_click = map_data
    
    if st.session_state.get("map_click"):
        click = st.session_state.map_click.get("last_object_clicked")
        zoom = st.session_state.map_click.get("zoom")
        if click:
            st.markdown(f"<div class='glass-card' style='font-size:12px;margin-top:10px'><b>🗺 Map Data</b> | Clicked: {click.get('lat'):.4f}, {click.get('lng'):.4f} | Zoom: {zoom}</div>", unsafe_allow_html=True)
