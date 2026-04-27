# -*- coding: utf-8 -*-
"""LogistiQ Command Center — single-page Streamlit app (v2.2)."""
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# ── Load env ──────────────────────────────────────────────────────────────────
_env_search = [
    Path(__file__).parent.parent / "command-center" / ".env",
    Path(__file__).parent.parent / ".env",
]
for _ep in _env_search:
    if _ep.exists():
        load_dotenv(dotenv_path=_ep)
        break
else:
    load_dotenv()

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="LogistiQ — Supply Chain Command Center",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Internal imports ──────────────────────────────────────────────────────────
from logistiq.data import init_session_state
from logistiq.components.design import apply_design_system
from logistiq.components import cards as K
from logistiq.views import (
    overview, sea, rail, road, air,
    intelligence, simulation, haas, shipments,
)

# ── Boot ──────────────────────────────────────────────────────────────────────
init_session_state()
apply_design_system()

# ── Navigation via query params (instant, no stale-render bug) ─────────────
# Query param ?p=sea is used as the source of truth for current page.
# When a nav button is clicked we SET the query param and rerun — the read
# at the top of the next run is always fresh.

_VALID_PAGES = {
    "overview", "sea", "rail", "road", "air",
    "intelligence", "simulation", "haas", "add_shipment", "shipment_detail", "journey",
}

def _go(page: str):
    """Navigate to a page instantly via query params."""
    st.query_params["p"] = page
    st.session_state.active_page = page
    if page != "add_shipment":
        st.session_state.show_add_form = False
    st.rerun()

# Resolve active page: prefer query param → session state → default
_qp = st.query_params.get("p", "")
if _qp in _VALID_PAGES:
    # Keep session state in sync with query param
    if st.session_state.active_page != _qp:
        st.session_state.active_page = _qp
active = st.session_state.active_page or "overview"

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR — navigation + shipments list
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    # Logo
    st.markdown("""
<div style='padding:10px 4px 6px;'>
  <div style='font-size:22px;font-weight:800;letter-spacing:-0.5px;color:#fff'>
    Logisti<span style='color:#FF6B35'>Q</span>
    <span style='font-size:11px;font-weight:400;color:#64748b;margin-left:6px'>v3.0</span>
  </div>
  <div style='font-size:11px;color:#64748b;margin-top:2px'>Chennai · Vizag · Manesar</div>
  <div style='margin-top:6px;display:flex;gap:4px'>
    <span class='enterprise-badge'>🚀 Enterprise</span>
    <span class='enterprise-badge'>🔒 SOC2</span>
  </div>
</div>
""", unsafe_allow_html=True)

    # Status pills
    fb_ok      = bool(os.getenv("FIREBASE_URL", ""))
    gemini_ok  = bool(os.getenv("GEMINI_API_KEY", ""))
    weather_ok = bool(os.getenv("WEATHER_API_KEY", ""))
    cyclone_on = st.session_state.cyclone_triggered

    def _dot(ok: bool) -> str:
        return "dot-green" if ok else "dot-red"

    st.markdown(f"""
<div style='display:flex;flex-wrap:wrap;gap:8px;margin:0 0 8px;'>
  <span style='font-size:11px;color:#94a3b8'><span class='status-dot {_dot(gemini_ok)}'></span>Gemini</span>
  <span style='font-size:11px;color:#94a3b8'><span class='status-dot {_dot(fb_ok)}'></span>Firebase</span>
  <span style='font-size:11px;color:#94a3b8'><span class='status-dot {_dot(weather_ok)}'></span>Weather</span>
  <span style='font-size:11px;color:#94a3b8'><span class='status-dot {"dot-amber" if cyclone_on else "dot-green"}'></span>{"⚠ CYCLONE" if cyclone_on else "Clear"}</span>
</div>""", unsafe_allow_html=True)

    if st.session_state.demo_mode:
        st.warning("🟡 **Demo Mode** active", icon="⚠️")

    st.markdown("<hr style='border-color:rgba(96,165,250,0.1);margin:0 0 8px'>", unsafe_allow_html=True)

    # ── Navigation ────────────────────────────────────
    st.markdown("<div style='font-size:10px;color:#475569;font-weight:700;letter-spacing:1px;margin-bottom:4px'>NAVIGATION</div>", unsafe_allow_html=True)

    NAV_ITEMS = [
        ("🗺",  "Overview",       "overview"),
        ("🌊",  "Sea & Maritime", "sea"),
        ("🚂",  "Rail",          "rail"),
        ("🚛",  "Road",          "road"),
        ("✈️",  "Air Cargo",     "air"),
        ("📡",  "Intelligence",  "intelligence"),
        ("🧪",  "Simulation",    "simulation"),
        ("📞",  "Field Reports", "haas"),
        ("🗺️",  "Journey",       "journey"),
    ]

    for icon, label, key in NAV_ITEMS:
        is_active = active == key
        btn_type  = "primary" if is_active else "secondary"
        if st.button(f"{icon}  {label}", key=f"nav_{key}",
                     use_container_width=True, type=btn_type):
            _go(key)

    st.markdown("<hr style='border-color:rgba(96,165,250,0.1);margin:8px 0'>", unsafe_allow_html=True)

    # ── Shipments ─────────────────────────────────────
    n_ships = len(st.session_state.shipments)
    st.markdown(f"<div style='font-size:10px;color:#475569;font-weight:700;letter-spacing:1px;margin-bottom:4px'>MY SHIPMENTS ({n_ships})</div>", unsafe_allow_html=True)

    if st.button("➕  Add Shipment", key="sb_add",
                 use_container_width=True, type="primary"):
        _go("add_shipment")

    shipments.render_shipment_list()

    # ── Toggles ───────────────────────────────────
    st.markdown("<hr style='border-color:rgba(96,165,250,0.1);margin:8px 0'>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:10px;color:#475569;font-weight:700;letter-spacing:1px;margin-bottom:4px'>SYSTEM SETTINGS</div>", unsafe_allow_html=True)
    
    # Gemma Edge Mode
    gemma_label = "⚡ Gemma Edge Mode: ON" if st.session_state.get("gemma_mode") else "Gemma Edge Mode: OFF"
    if st.button(gemma_label, key="sb_gemma", use_container_width=True):
        st.session_state.gemma_mode = not st.session_state.get("gemma_mode", False)
        st.rerun()

    # Disaster Relief Mode
    relief_label = "🆘 Disaster Relief: ON" if st.session_state.get("relief_mode") else "Disaster Relief: OFF"
    if st.button(relief_label, key="sb_relief", use_container_width=True):
        st.session_state.relief_mode = not st.session_state.get("relief_mode", False)
        st.rerun()

    # Demo toggle
    demo_label = "🔴 Disable Demo Mode" if st.session_state.demo_mode else "🟡 Enable Demo Mode"
    if st.button(demo_label, key="sb_demo", use_container_width=True):
        st.session_state.demo_mode = not st.session_state.demo_mode
        st.session_state.gemini_model = None
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# MAIN CONTENT — route using the query-param-synced `active` variable
# ─────────────────────────────────────────────────────────────────────────────
if active == "add_shipment" or st.session_state.show_add_form:
    shipments.render_add_form()
elif active == "sea":
    sea.render()
elif active == "rail":
    rail.render()
elif active == "road":
    road.render()
elif active == "air":
    air.render()
elif active == "intelligence":
    intelligence.render()
elif active == "simulation":
    simulation.render()
elif active == "haas":
    haas.render()
elif active == "journey":
    from logistiq.views import journey
    journey.render()
elif active == "shipment_detail":
    if st.session_state.get("selected_shipment"):
        shipments.render_shipment_detail(st.session_state.selected_shipment)
    else:
        overview.render()
else:
    overview.render()

# ─────────────────────────────────────────────────────────────────────────────
# BOTTOM STATUS BAR
# ─────────────────────────────────────────────────────────────────────────────
from datetime import datetime
now_str    = datetime.now().strftime("%H:%M:%S IST")
maps_ok    = bool(os.getenv("MAPS_API_KEY", ""))
mode_color = "#fbbf24" if st.session_state.demo_mode else "#4ade80"
mode_label = "🟡 Demo" if st.session_state.demo_mode else "🟢 Live"

st.markdown(f"""
<div class='status-bar'>
  <span>🕐 {now_str}</span>
  <span class='status-divider'>│</span>
  <span><span class='status-dot {_dot(gemini_ok)}'></span>Gemini</span>
  <span><span class='status-dot {_dot(fb_ok)}'></span>Firebase</span>
  <span><span class='status-dot {_dot(weather_ok)}'></span>Weather</span>
  <span><span class='status-dot {_dot(maps_ok)}'></span>Maps</span>
  <span class='status-divider'>│</span>
  <span style='color:{mode_color}'>{mode_label}</span>
  <div style='flex:1'></div>
  <span style='color:#334155;font-size:10px'>LogistiQ v3.0 · Chennai–Vizag–Manesar</span>
</div>
<div style='height:44px'></div>
""", unsafe_allow_html=True)
