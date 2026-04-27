# -*- coding: utf-8 -*-
"""LogistiQ Command Center — Main application router.

Multimodal supply chain intelligence for the Chennai–Vizag–Manesar corridor.
"""

import json
import math
import os
import time
from datetime import datetime
from pathlib import Path

import streamlit as st

try:
    from dotenv import load_dotenv
except Exception:  # noqa: BLE001
    load_dotenv = None

# ---------------------------------------------------------------------------
# Paths & env
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "data"
ENV_PATH = BASE_DIR / ".env"

if load_dotenv:
    load_dotenv(dotenv_path=ENV_PATH)

st.set_page_config(page_title="LogistiQ", page_icon="🚢", layout="wide")

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_json(file_path: Path):
    try:
        with file_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:  # noqa: BLE001
        return [] if file_path.name.endswith(".json") else {}


vessels_data = load_json(DATA_DIR / "vessels.json")
ports_data = load_json(DATA_DIR / "ports.json")
trucks_data = load_json(DATA_DIR / "trucks.json")
rail_schedules_data = load_json(DATA_DIR / "rail_schedules.json")
demo_responses_data = load_json(DATA_DIR / "demo_responses.json")

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

def init_session_state():
    defaults = {
        "cyclone_triggered": False,
        "reroute_data": None,
        "reroute_accepted": False,
        "active_page": "overview",
        "captain_reports": [],
        "firebase_ok": False,
        "demo_mode": False,
        "shipments": [],
        "weather_cache": {},
        "show_add_form": False,
        "sim_complete": False,
        "chokepoint_intel": None,
        "intel_digest": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ---------------------------------------------------------------------------
# Design system CSS
# ---------------------------------------------------------------------------

def apply_design_system():
    st.markdown(
        """
        <style>
            /* === IMPORTS === */
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

            /* === CSS VARIABLES === */
            :root {
                --color-primary: #FF6B35;
                --color-sea: #44c5ff;
                --color-rail: #fbbf24;
                --color-road: #4ade80;
                --color-air: #a78bfa;
                --color-critical: #f87171;
                --color-warning: #fbbf24;
                --color-safe: #4ade80;
                --color-neutral: #60a5fa;
                --bg-card: rgba(255,255,255,0.05);
                --border-card: rgba(96,165,250,0.35);
                --bg-page: radial-gradient(circle at top right, #18263e, #070d18 55%);
            }

            /* === BASE === */
            .stApp {
                background: var(--bg-page);
                color: #e7efff;
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            }

            /* Hide default Streamlit nav */
            [data-testid="stSidebarNav"] { display: none; }
            header[data-testid="stHeader"] { background: transparent; }

            /* === GLASS CARD === */
            .glass-card {
                background: var(--bg-card);
                border: 1px solid var(--border-card);
                border-radius: 12px;
                padding: 12px;
                margin: 8px 0;
                backdrop-filter: blur(8px);
                transition: border-color 0.3s ease, transform 0.2s ease;
            }
            .glass-card:hover {
                border-color: rgba(96,165,250,0.6);
                transform: translateY(-1px);
            }

            /* === METRIC CARD === */
            .metric-card { text-align: center; }
            .metric-label { font-size: 12px; font-weight: 500; color: #94a3b8; margin-bottom: 4px; }
            .metric-value { font-size: 24px; font-weight: 700; color: #e7efff; }
            .metric-delta { font-size: 11px; color: #64748b; margin-top: 2px; }

            /* === BADGES === */
            .badge-green { background:#166534; color:#4ade80; padding:3px 10px; border-radius:12px; font-size:11px; font-weight:700; }
            .badge-red { background:#7f1d1d; color:#f87171; padding:3px 10px; border-radius:12px; font-size:11px; font-weight:700; }
            .badge-amber { background:#78350f; color:#fbbf24; padding:3px 10px; border-radius:12px; font-size:11px; font-weight:700; }
            .badge-blue { background:#1e3a5f; color:#60a5fa; padding:3px 10px; border-radius:12px; font-size:11px; font-weight:700; }

            /* === TICKER === */
            .ticker-wrap {
                overflow: hidden; background: var(--color-primary);
                padding: 8px 0; margin-bottom: 12px; border-radius: 8px;
            }
            .ticker-move {
                display: inline-block; white-space: nowrap;
                animation: ticker 28s linear infinite;
            }
            @keyframes ticker { from { transform: translateX(100vw); } to { transform: translateX(-100%); } }
            .ticker-move span { color: white; font-size: 13px; font-weight: 500; padding: 0 40px; }

            /* === COMMAND CARD === */
            .cmd-card {
                background: rgba(20,30,48,0.85);
                border: 1.5px solid var(--color-primary);
                border-radius: 14px; padding: 18px; margin: 10px 0;
            }
            .cmd-card-header {
                background: var(--color-primary); color: white; font-weight: 700;
                font-size: 14px; padding: 8px 14px; border-radius: 8px;
                margin-bottom: 12px;
            }

            /* === CASCADE STEPS === */
            .cascade-step {
                border-left: 3px solid var(--color-safe); padding: 8px 12px;
                margin: 6px 0; border-radius: 0 8px 8px 0;
                background: rgba(74,222,128,0.08);
            }
            .cascade-step-air {
                border-left-color: var(--color-warning);
                background: rgba(251,191,36,0.08);
            }

            /* === INTEL & SOCIAL BOXES === */
            .intel-box {
                background: rgba(59,130,246,0.12);
                border: 1px solid rgba(59,130,246,0.4);
                border-radius: 8px; padding: 10px; font-style: italic;
                font-size: 13px; margin-top: 8px;
            }
            .social-box {
                background: rgba(74,222,128,0.10);
                border: 1px solid rgba(74,222,128,0.3);
                border-radius: 8px; padding: 10px; font-size: 13px;
            }

            /* === TOP NAV BAR === */
            .top-nav {
                display: flex; align-items: center; gap: 6px;
                padding: 8px 16px; margin: -12px -16px 12px -16px;
                background: rgba(10,22,40,0.9);
                border-bottom: 1px solid rgba(96,165,250,0.2);
                border-radius: 0 0 12px 12px;
                backdrop-filter: blur(12px);
                flex-wrap: wrap;
            }
            .nav-logo {
                color: var(--color-primary); font-weight: 700; font-size: 18px;
                margin-right: 16px; white-space: nowrap;
            }
            .nav-btn {
                background: transparent; color: #94a3b8; border: none;
                padding: 6px 14px; border-radius: 8px; font-size: 13px;
                cursor: pointer; font-weight: 500; transition: all 0.2s;
            }
            .nav-btn:hover { background: rgba(255,255,255,0.08); color: white; }
            .nav-btn.active {
                background: rgba(255,107,53,0.15); color: var(--color-primary);
                border: 1px solid rgba(255,107,53,0.4); font-weight: 600;
            }

            /* === SKELETON LOADING === */
            @keyframes skeleton-pulse {
                0% { opacity: 0.3; }
                50% { opacity: 0.5; }
                100% { opacity: 0.3; }
            }
            .skeleton {
                background: rgba(255,255,255,0.05);
                border-radius: 12px;
            }

            /* === PULSE ANIMATION === */
            @keyframes pulse {
                0% { transform: scale(1); opacity: 1; }
                50% { transform: scale(1.3); opacity: 0.7; }
                100% { transform: scale(1); opacity: 1; }
            }

            /* === STATUS BAR === */
            .status-bar {
                position: fixed; bottom: 0; left: 0; right: 0; z-index: 999;
                background: rgba(10,22,40,0.95); border-top: 1px solid rgba(96,165,250,0.2);
                padding: 6px 20px; font-size: 11px; color: #64748b;
                display: flex; justify-content: space-between; align-items: center;
                backdrop-filter: blur(8px);
            }

            /* === STREAMLIT OVERRIDES === */
            .stButton > button {
                border-radius: 8px; font-weight: 500; font-size: 13px;
                transition: all 0.2s;
            }
            .stButton > button:hover { transform: translateY(-1px); }
            [data-testid="stMetric"] {
                background: var(--bg-card);
                border: 1px solid var(--border-card);
                border-radius: 12px; padding: 12px;
            }
            .stDataFrame { border-radius: 12px; overflow: hidden; }
            div[data-testid="stExpander"] {
                background: var(--bg-card);
                border: 1px solid var(--border-card);
                border-radius: 12px;
            }

            /* bottom padding for status bar */
            .main .block-container { padding-bottom: 60px; }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------

def render_top_nav():
    """Top navigation bar using Streamlit columns + buttons."""
    pages = {
        "overview": "Overview",
        "sea": "Sea",
        "rail": "Rail",
        "road": "Road",
        "air": "Air",
        "intelligence": "Intel",
        "simulation": "Simulate",
        "haas": "Field",
        "journey": "Journey",
    }

    nav_cols = st.columns([1.8] + [1] * len(pages) + [1.2, 0.8], gap="small")

    with nav_cols[0]:
        st.markdown("<span style='color:#FF6B35;font-weight:700;font-size:18px'>🚢 LogistiQ</span>", unsafe_allow_html=True)

    for i, (key, label) in enumerate(pages.items(), 1):
        with nav_cols[i]:
            btn_type = "primary" if st.session_state.active_page == key else "secondary"
            if st.button(label, key=f"nav_{key}", use_container_width=True, type=btn_type):
                st.session_state.active_page = key
                st.rerun()

    # Alerts count
    with nav_cols[-2]:
        n_alerts = 3 if st.session_state.get("cyclone_triggered") else 1
        st.button(f"🔔 ({n_alerts})", key="nav_alerts", use_container_width=True)

    with nav_cols[-1]:
        if st.session_state.get("demo_mode"):
            st.markdown("<span class='badge-amber'>DEMO</span>", unsafe_allow_html=True)
        else:
            st.markdown("<span class='badge-green'>LIVE</span>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def render_sidebar():
    """Persistent sidebar with shipment list and controls."""
    with st.sidebar:
        st.markdown("<h3 style='color:#FF6B35'>🚢 LogistiQ</h3>", unsafe_allow_html=True)
        st.caption("Supply Chain Intelligence Platform")
        st.divider()

        # Demo mode toggle
        st.session_state.demo_mode = st.toggle(
            "⚡ Demo Mode (offline)",
            value=st.session_state.demo_mode,
            help="Uses cached responses. Enable if APIs are slow.",
        )

        # Firebase status
        from utils.firebase import check_firebase_connection
        fb_ok = st.session_state.get("firebase_ok", False)
        fb_color = "🟢" if fb_ok else "🔴"
        st.caption(f"{fb_color} Firebase {'Connected' if fb_ok else 'Offline'}")

        st.divider()

        # Company filter
        st.selectbox(
            "Filter Company",
            ["All Companies", "Maruti Suzuki", "Delhivery", "Maersk India", "DHL Express"],
            key="company_filter",
        )

        st.divider()

        # My Shipments
        st.markdown("**📦 MY SHIPMENTS**")
        n_shipments = len(st.session_state.get("shipments", []))
        st.caption(f"{n_shipments} active shipments")

        if st.button("➕ Add New Shipment", use_container_width=True, key="add_shp_btn"):
            st.session_state.show_add_form = not st.session_state.show_add_form

        # Compact shipment list
        from components.cards import shipment_card
        for idx, shp in enumerate(st.session_state.get("shipments", [])):
            st.markdown(shipment_card(shp, idx), unsafe_allow_html=True)

        st.divider()
        st.caption("Powered by Gemini • Firebase • Cloud Run")


# ---------------------------------------------------------------------------
# Ticker
# ---------------------------------------------------------------------------

def render_ticker():
    ticker_items = [
        "🔴 LIVE: Cyclone Mocha tracking toward Bay of Bengal",
        "⚠ Port Congestion: JNPT Mumbai — 8.2hr average wait",
        "📡 ULIP FASTag: 847 trucks tracked on NH16 corridor",
        "🌊 Tidal Alert: Chennai — draft restriction >14m for next 11 hours",
        "🌐 Red Sea: Houthi vessel diversions up 23% this week",
        "🚂 FOIS: SCR Train 58501 on schedule — Platform 7B",
    ]
    html = " &nbsp;&nbsp;•&nbsp;&nbsp; ".join(f"<span>{t}</span>" for t in ticker_items)
    st.markdown(f"<div class='ticker-wrap'><div class='ticker-move'>{html}</div></div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Status bar
# ---------------------------------------------------------------------------

def render_status_bar():
    now = datetime.now().strftime("%H:%M:%S IST, %d %b %Y")
    demo = "DEMO" if st.session_state.get("demo_mode") else "LIVE"
    fb = "🟢 Firebase" if st.session_state.get("firebase_ok") else "🔴 Firebase"
    st.markdown(
        f"""
        <div class='status-bar'>
          <span>{demo} | Last refresh: {now}</span>
          <span>{fb} | WeatherAPI ✅ | Gemini ✅ | Google Maps ✅</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Add shipment form (drawer-style)
# ---------------------------------------------------------------------------

def render_add_shipment_drawer():
    """Right-side add shipment form."""
    from utils.data import get_real_weather, get_inr_rate, lookup_city_coords
    from utils.gemini import analyze_shipment_risk, get_live_intelligence
    from utils.firebase import firebase_write

    st.markdown("### ➕ Add Shipment / Cargo")
    with st.form("add_shipment_form"):
        col1, col2 = st.columns(2)
        cargo_type = col1.selectbox("Cargo Type", [
            "Auto Parts", "Electronics", "Pharmaceuticals / Medical",
            "Food / Perishable", "Industrial Equipment", "Chemicals",
            "Textiles", "General Merchandise",
        ])
        transport_mode = col2.selectbox("Transport Mode", [
            "🚢 Sea (Vessel)", "🚂 Rail", "🚛 Road (Truck)", "✈ Air",
            "🚢+🚂 Sea + Rail", "🚢+🚛 Sea + Road",
        ])

        cargo_desc = st.text_input("Cargo Description", placeholder="e.g. 4200 engine blocks for Maruti Manesar")

        col3, col4 = st.columns(2)
        value_crore = col3.number_input("Cargo Value (₹ Crore)", 0.1, 5000.0, 10.0, step=0.1)
        weight_tons = col4.number_input("Weight (Tons)", 0.1, 50000.0, 100.0)

        col5, col6 = st.columns(2)
        origin = col5.text_input("Origin", placeholder="e.g. Chennai Port")
        destination = col6.text_input("Destination", placeholder="e.g. Manesar Plant")

        col7, col8 = st.columns(2)
        departure_date = col7.date_input("Departure Date")
        deadline_date = col8.date_input("Must Arrive By")

        consignee = st.text_input("Consignee", placeholder="e.g. Maruti Suzuki India Ltd")
        special_reqs = st.multiselect("Special Requirements", [
            "Cold Chain", "Hazmat", "Oversized", "Fragile", "Priority / Express",
        ])

        sub_col, cancel_col = st.columns(2)
        submitted = sub_col.form_submit_button("🚀 Analyze Risk →", use_container_width=True)
        cancelled = cancel_col.form_submit_button("Cancel", use_container_width=True)

    if cancelled:
        st.session_state.show_add_form = False
        st.rerun()

    if submitted:
        shipment = {
            "id": f"SHP-{int(time.time())}",
            "cargo_type": cargo_type,
            "cargo_desc": cargo_desc,
            "transport_mode": transport_mode,
            "value_crore": value_crore,
            "weight_tons": weight_tons,
            "origin": origin,
            "destination": destination,
            "departure_date": str(departure_date),
            "deadline_date": str(deadline_date),
            "consignee": consignee,
            "special_reqs": special_reqs,
            "added_at": datetime.now().isoformat(),
            "risk_analyzed": False,
            "risk_data": None,
            "weather_data": None,
        }

        # Progress indicators
        progress = st.empty()
        progress.markdown("✅ Exchange rate fetched...")
        rate = get_inr_rate()
        shipment["exchange_rate"] = rate

        coords = lookup_city_coords(destination)
        progress.markdown("✅ Weather fetched...")
        weather = get_real_weather(coords[0], coords[1], destination)
        shipment["weather_data"] = weather

        progress.markdown("⏳ Running Gemini risk analysis...")
        intel_topic = f"Current shipping conditions between {origin} and {destination}. Port disruptions or delays."
        live_intel = get_live_intelligence(intel_topic)

        risk = analyze_shipment_risk(shipment, weather, rate, live_intel)
        shipment["risk_data"] = risk
        shipment["risk_analyzed"] = True
        shipment["live_intel"] = live_intel

        progress.markdown(f"✅ Risk Level: **{risk.get('risk_level', 'Medium')}** — {risk.get('recommendation', '')}")

        st.session_state.shipments.append(shipment)
        st.session_state.show_add_form = False
        firebase_write(f"/shipments/{shipment['id']}", shipment)
        st.success(f"✅ Shipment {shipment['id']} added. Risk: {risk['risk_level']}")
        time.sleep(1)
        st.rerun()


# ---------------------------------------------------------------------------
# My Shipments display
# ---------------------------------------------------------------------------

def render_my_shipments():
    """Render shipment cards with risk gauges."""
    from components.charts import risk_gauge

    st.markdown("### 📦 My Shipments — Live Risk Monitor")
    for idx, shipment in enumerate(st.session_state.shipments):
        risk = shipment.get("risk_data", {})
        risk_level = risk.get("risk_level", "Unknown")
        risk_score = risk.get("risk_score", 0)
        weather = shipment.get("weather_data", {})

        border_color = (
            "#f87171" if risk_level == "Critical" else
            "#fbbf24" if risk_level == "High" else
            "#60a5fa" if risk_level == "Medium" else "#4ade80"
        )

        st.markdown(f"<div class='glass-card' style='border-color:{border_color}'>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns([1.5, 3, 2, 1.5])

        with c1:
            risk_gauge(risk_score, idx=idx, height=180)

        with c2:
            st.markdown(f"**{shipment.get('cargo_desc', '')}**")
            st.markdown(f"{shipment.get('origin', '')} → {shipment.get('destination', '')}")
            st.caption(f"Mode: {shipment.get('transport_mode', '')} | Weight: {shipment.get('weight_tons', '')}t | Value: ₹{shipment.get('value_crore', '')}Cr")
            st.caption(f"Consignee: {shipment.get('consignee', '')} | Deadline: {shipment.get('deadline_date', '')}")
            st.markdown(f"<span style='color:{border_color}'>⚠ {risk.get('primary_risk', '')}</span>", unsafe_allow_html=True)

        with c3:
            cond = weather.get("condition", "N/A")
            is_dang = weather.get("is_dangerous", False)
            st.markdown(f"{'🌀' if is_dang else '🌤'} **{cond}**")
            st.caption(f"Wind: {weather.get('wind_kph', 'N/A')} kph")
            if weather.get("alerts"):
                st.markdown("<span class='badge-red'>WEATHER ALERT</span>", unsafe_allow_html=True)
            st.caption(f"Rate: ₹{shipment.get('exchange_rate', 83.5)}/USD")

        with c4:
            if st.button("🗑 Remove", key=f"remove_{idx}", use_container_width=True):
                st.session_state.shipments.pop(idx)
                st.rerun()

        with st.expander("📊 Full Analysis", expanded=(risk_level in ("High", "Critical"))):
            st.markdown("**Detected Issues:**")
            for issue in risk.get("detected_issues", []):
                st.markdown(f"- ⚠ {issue}")
            r1, r2, r3 = st.columns(3)
            r1.metric("Weather Risk", risk.get("weather_risk", "Unknown"))
            r2.metric("Geopolitical Risk", risk.get("geopolitical_risk", "Unknown"))
            r3.metric("Operational Risk", risk.get("operational_risk", "Unknown"))
            st.markdown(f"**Estimated delay:** {risk.get('estimated_delay_hours', 0)} hours")
            st.markdown(f"**Financial impact:** ₹{risk.get('financial_impact_inr', 0):,}")
            st.markdown(f"**Recommendation:** {risk.get('recommendation', '')}")
            st.markdown(f"<div class='intel-box'>{shipment.get('live_intel', '')}</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    apply_design_system()
    init_session_state()

    # Check Firebase
    from utils.firebase import check_firebase_connection
    if "firebase_ok" not in st.session_state or not st.session_state.firebase_ok:
        st.session_state.firebase_ok = check_firebase_connection()

    render_sidebar()
    render_ticker()
    render_top_nav()

    # Add shipment form (if toggled)
    if st.session_state.get("show_add_form", False):
        render_add_shipment_drawer()

    # Shipment list
    if st.session_state.get("shipments"):
        render_my_shipments()
        st.divider()

    # Page routing
    page = st.session_state.get("active_page", "overview")

    if page == "overview":
        from pages.overview import render as render_overview
        render_overview(vessels_data, ports_data, trucks_data, rail_schedules_data)

    elif page == "sea":
        from pages.sea import render as render_sea
        render_sea(vessels_data, ports_data, trucks_data, rail_schedules_data, demo_responses_data)

    elif page == "rail":
        from pages.rail import render as render_rail
        render_rail(rail_schedules_data, trucks_data)

    elif page == "road":
        from pages.road import render as render_road
        render_road(trucks_data, ports_data)

    elif page == "air":
        from pages.air import render as render_air
        render_air()

    elif page == "intelligence":
        from pages.intelligence import render as render_intel
        render_intel(ports_data)

    elif page == "simulation":
        from pages.simulation import render as render_sim
        render_sim(vessels_data, ports_data, trucks_data, rail_schedules_data, demo_responses_data)

    elif page == "haas":
        from pages.haas import render as render_haas
        render_haas(demo_responses_data)
        
    elif page == "journey":
        from pages.journey import render as render_journey
        render_journey()

    # Status bar
    render_status_bar()


if __name__ == "__main__":
    main()
