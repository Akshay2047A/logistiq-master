# -*- coding: utf-8 -*-
"""LogistiQ Command Center — single-page Streamlit app (v3.1)."""
import os
import time
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

# Auto-refresh (wrapped to prevent crash if package missing)
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=30000, key="global_30s_autorefresh")
except Exception:
    pass

try:
    dialog_decorator = st.dialog
except AttributeError:
    dialog_decorator = st.experimental_dialog

@dialog_decorator("🔔 Active Alerts")
def show_alert_panel():
    from logistiq.utils.firebase import firebase_read, firebase_write
    raw_alerts = firebase_read("/alerts") or {}
    unread = {k: v for k, v in raw_alerts.items() if not v.get("ack")}
    
    if not unread:
        st.success("All caught up! No unread alerts.")
        return
        
    for k, a in unread.items():
        st.error(f"**{a.get('shipment_id', 'Unknown')}**: {a.get('msg', '')}")
        col1, col2 = st.columns(2)
        if col1.button("✅ Acknowledge", key=f"ack_{k}"):
            firebase_write(f"/alerts/{k}/ack", True)
            st.rerun()
        if col2.button("🗺️ Go to Shipment", key=f"go_{k}"):
            st.session_state.active_page = "journey"
            st.query_params["p"] = "journey"
            shps = st.session_state.get("shipments", [])
            shp = next((s for s in shps if s.get('id') == a.get("shipment_id")), None)
            if shp:
                st.session_state.selected_shipment = shp
            st.rerun()
            
    if st.button("🗑️ Clear All", use_container_width=True):
        for k in unread.keys():
            firebase_write(f"/alerts/{k}/ack", True)
        st.rerun()

# ── Navigation via query params ────────────────────────────────────────────
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
    if st.session_state.active_page != _qp:
        st.session_state.active_page = _qp
active = st.session_state.active_page or "overview"

# ─────────────────────────────────────────────────────────────────────────────
# TOP NAVIGATION BAR
# ─────────────────────────────────────────────────────────────────────────────
def render_top_navbar(active_page: str):
    pages = [
        ("🗺", "Overview",   "overview"),
        ("🌊", "Sea",        "sea"),
        ("🚂", "Rail",       "rail"),
        ("🚛", "Road",       "road"),
        ("✈", "Air",        "air"),
        ("📡", "Intel",      "intelligence"),
        ("🧪", "Simulate",   "simulation"),
        ("📞", "Field",      "haas"),
        ("🗺️", "Journey",    "journey"),
    ]

    logo_col, *nav_cols, mode_col = st.columns([2] + [1] * len(pages) + [1.5])
    with logo_col:
        st.markdown(
            "<div style='padding-top:2px'><span style='color:#FF6B35;font-weight:800;font-size:22px;letter-spacing:-0.5px;'>🚢 LogistiQ</span></div>",
            unsafe_allow_html=True
        )
    for i, (icon, label, key) in enumerate(pages):
        with nav_cols[i]:
            btn_type = "primary" if active_page == key else "secondary"
            if st.button(
                f"{icon} {label}",
                key=f"topnav_{key}",
                use_container_width=True,
                type=btn_type,
            ):
                _go(key)

    with mode_col:
        mode_text = "🟡 DEMO" if st.session_state.get("demo_mode") else "🟢 LIVE"
        st.markdown(f"<div style='padding-top:8px;text-align:right;font-weight:700;font-size:12px;color:#94a3b8'>{mode_text}</div>", unsafe_allow_html=True)

    st.markdown("<hr style='border-color:rgba(96,165,250,0.1);margin:4px 0 16px'>", unsafe_allow_html=True)

render_top_navbar(active)

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR — navigation + shipments list
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    # Logo
    st.markdown("""
<div style='padding:10px 4px 6px;'>
  <div style='font-size:22px;font-weight:800;letter-spacing:-0.5px;color:#fff'>
    Logisti<span style='color:#FF6B35'>Q</span>
    <span style='font-size:11px;font-weight:400;color:#64748b;margin-left:6px'>v3.1</span>
  </div>
  <div style='font-size:11px;color:#64748b;margin-top:2px'>Chennai · Vizag · Manesar</div>
  <div style='margin-top:6px;display:flex;gap:4px'>
    <span class='enterprise-badge'>🚀 Enterprise</span>
    <span class='enterprise-badge'>🔒 SOC2</span>
  </div>
</div>
""", unsafe_allow_html=True)

    # Status pills
    from logistiq.utils.firebase import check_firebase_connection
    fb_ok      = check_firebase_connection()
    gemini_ok  = bool(os.getenv("GEMINI_API_KEY", ""))
    weather_ok = bool(os.getenv("WEATHER_API_KEY", ""))
    cyclone_on = st.session_state.cyclone_triggered

    # ── AI Command Bar ───────────────────────────────────
    st.markdown("""
        <script>
        const doc = window.parent.document;
        doc.addEventListener('keydown', function(e) {
            if (e.ctrlKey && e.key === 'k') {
                e.preventDefault();
                const inputs = doc.querySelectorAll('input');
                for (let i = 0; i < inputs.length; i++) {
                    if (inputs[i].getAttribute('aria-label') === 'Command Bar') {
                        inputs[i].focus();
                        break;
                    }
                }
            }
        });
        </script>
    """, unsafe_allow_html=True)
    
    def process_command():
        cmd = st.session_state.get("global_cmd", "").strip()
        if not cmd: return
        try:
            from logistiq.utils.gemini import cached_gemini_call
            prompt = f"""You are a logistics ops assistant. The user typed: "{cmd}"
Available actions: navigate_to_page, filter_shipments, trigger_reroute, show_vessel_detail, show_alert_detail, zoom_map_to_location, toggle_mode.
Available pages: overview, sea, rail, road, air, intelligence, simulation, haas, journey.
Return ONLY valid JSON (no markdown): 
{{"action": "...", "target": "...", "params": {{}}, "user_reply": "..."}}"""
            res = cached_gemini_call(prompt, response_mime_type="application/json")
            import json
            data = json.loads(res)
            st.session_state.cmd_result = data
        except Exception as e:
            st.session_state.cmd_result = {"action": "error", "user_reply": f"Error: {str(e)}"}
        st.session_state.global_cmd = ""
        
    st.text_input("Command Bar", key="global_cmd", placeholder="Ctrl+K to command AI...", label_visibility="collapsed", on_change=process_command)
    
    if "cmd_result" in st.session_state and st.session_state.cmd_result:
        res = st.session_state.cmd_result
        st.session_state.cmd_result = None
        st.toast(res.get("user_reply", "Command executed"))
        action = res.get("action")
        target = res.get("target")
        params = res.get("params", {})
        
        if action == "navigate_to_page" and target in _VALID_PAGES:
            st.session_state.active_page = target
            st.query_params["p"] = target
        elif action == "toggle_mode":
            if target in st.session_state:
                st.session_state[target] = not st.session_state[target]
        elif action == "zoom_map_to_location":
            if "coords" in params:
                st.session_state.map_center = params["coords"]

    # ── Alerts Bell ───────────────────────────────────
    from logistiq.utils.firebase import firebase_read, firebase_write
    raw_alerts = firebase_read("/alerts") or {}
    if not raw_alerts:
        mock_alert = {"msg": "Cyclone Warning: MV Chennai Star at risk", "shipment_id": "VSL-001", "ack": False}
        firebase_write("/alerts/alert_1", mock_alert)
        raw_alerts = {"alert_1": mock_alert}
        
    unread_count = sum(1 for a in raw_alerts.values() if not a.get("ack"))
    if st.button(f"🔔 Notifications ({unread_count})", key="nav_alerts_bell", use_container_width=True):
        show_alert_panel()
        
    st.markdown("<hr style='border-color:rgba(96,165,250,0.1);margin:8px 0'>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    def _dot(ok: bool) -> str:
        return "dot-green" if ok else "dot-red"

    gem_status = st.session_state.get("gemini_status", "ok") if gemini_ok else "failed"
    gem_dot = "dot-green" if gem_status == "ok" else "dot-amber" if gem_status == "retrying" else "dot-red"
    gem_label = f"Gemini ({gem_status})"
    elapsed = (time.time() % 30)
    remaining = int(30 - elapsed)

    st.markdown(f"""
<div style='display:flex;flex-wrap:wrap;gap:8px;margin:0 0 8px;'>
  <span style='font-size:11px;color:#94a3b8'><span class='status-dot {gem_dot}'></span>{gem_label}</span>
  <span style='font-size:11px;color:#94a3b8'><span class='status-dot {_dot(fb_ok)}'></span>Firebase</span>
  <span style='font-size:11px;color:#94a3b8'><span class='status-dot {_dot(weather_ok)}'></span>Weather</span>
  <span style='font-size:11px;color:#94a3b8'><span class='status-dot {"dot-amber" if cyclone_on else "dot-green"}'></span>{"⚠ CYCLONE" if cyclone_on else "Clear"}</span>
  <span style='font-size:11px;color:#94a3b8'>⏱ Next refresh in {remaining}s</span>
</div>""", unsafe_allow_html=True)

    if st.session_state.demo_mode:
        st.markdown("<div style='background:rgba(251,191,36,0.15);color:#fbbf24;padding:6px;border-radius:4px;font-size:12px;font-weight:700;text-align:center'>🟡 DEMO MODE</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='background:rgba(74,222,128,0.15);color:#4ade80;padding:6px;border-radius:4px;font-size:12px;font-weight:700;text-align:center'>🟢 LIVE MODE</div>", unsafe_allow_html=True)

    st.markdown("<hr style='border-color:rgba(96,165,250,0.1);margin:0 0 8px'>", unsafe_allow_html=True)

    # ── Sync Status ───────────────────────────────────
    st.markdown("<div style='font-size:10px;color:#475569;font-weight:700;letter-spacing:1px;margin-bottom:4px'>SYNC STATUS</div>", unsafe_allow_html=True)
    
    from logistiq.utils.firebase import firebase_flush_queue
    queue = st.session_state.get("firebase_queue", [])
    if queue:
        st.markdown(f"""
<div style='display:flex;align-items:center;gap:6px;color:#fbbf24;font-size:12px;margin-bottom:4px'>
  <span style='width:8px;height:8px;border-radius:50%;background:#fbbf24;animation:pulse 1s infinite;display:inline-block;flex-shrink:0'></span>
  {len(queue)} items pending sync
</div>""", unsafe_allow_html=True)
        if st.button("↺ Retry Sync", key="retry_sync", use_container_width=True):
            firebase_flush_queue()
            st.rerun()
    else:
        st.markdown("<div style='color:#4ade80;font-size:12px;margin-bottom:4px'>✅ All synced</div>", unsafe_allow_html=True)
        
    st.markdown("<hr style='border-color:rgba(96,165,250,0.1);margin:0 0 8px'>", unsafe_allow_html=True)

    # ── Navigation ────────────────────────────────────
    st.markdown("<div style='font-size:10px;color:#475569;font-weight:700;letter-spacing:1px;margin-bottom:4px'>NAVIGATION</div>", unsafe_allow_html=True)

    NAV_ITEMS = [
        ("🗺",  "Overview",       "overview"),
        ("🌊",  "Sea & Maritime", "sea"),
        ("🚂",  "Rail",           "rail"),
        ("🚛",  "Road",           "road"),
        ("✈️",  "Air Cargo",      "air"),
        ("📡",  "Intelligence",   "intelligence"),
        ("🧪",  "Simulation",     "simulation"),
        ("📞",  "Field Reports",  "haas"),
        ("🗺️",  "Journey",        "journey"),
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

    if st.button("➕  Add Shipment", key="sb_add", use_container_width=True, type="primary"):
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

    # ── Keyboard Shortcuts ────────────────────────────
    st.markdown("<hr style='border-color:rgba(96,165,250,0.1);margin:8px 0'>", unsafe_allow_html=True)
    with st.expander("⌨️ Keyboard Shortcuts"):
        st.markdown("""
- `Ctrl+K` — AI Command Bar
- `Ctrl+1-9` — Navigate pages
- `Ctrl+R` — Refresh page
        """)

# ─────────────────────────────────────────────────────────────────────────────
# MAIN CONTENT — route using the query-param-synced `active` variable
# ─────────────────────────────────────────────────────────────────────────────
if active == "add_shipment" or st.session_state.show_add_form:
    shipments.render_add_form()
elif active == "sea":
    with st.spinner("Loading Sea & Maritime..."):
        sea.render()
elif active == "rail":
    with st.spinner("Loading Rail Operations..."):
        rail.render()
elif active == "road":
    with st.spinner("Loading Road Logistics..."):
        road.render()
elif active == "air":
    with st.spinner("Loading Air Cargo..."):
        air.render()
elif active == "intelligence":
    with st.spinner("Loading Intelligence Hub..."):
        intelligence.render()
elif active == "simulation":
    simulation.render()
elif active == "haas":
    with st.spinner("Loading Field Reports..."):
        haas.render()
elif active == "journey":
    with st.spinner("Loading Journey Tracker..."):
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

gem_status = st.session_state.get("gemini_status", "ok") if os.getenv("GEMINI_API_KEY") else "failed"
gem_dot = "dot-green" if gem_status == "ok" else "dot-amber" if gem_status == "retrying" else "dot-red"
gem_label = f"Gemini ({gem_status})"

st.markdown(f"""
<div class='status-bar'>
  <span>🕐 {now_str}</span>
  <span class='status-divider'>│</span>
  <span><span class='status-dot {gem_dot}'></span>{gem_label}</span>
  <span><span class='status-dot {"dot-green" if fb_ok else "dot-red"}'></span>Firebase</span>
  <span><span class='status-dot {"dot-green" if weather_ok else "dot-red"}'></span>Weather</span>
  <span><span class='status-dot {"dot-green" if maps_ok else "dot-red"}'></span>Maps</span>
  <span class='status-divider'>│</span>
  <span style='color:{mode_color}'>{mode_label}</span>
  <div style='flex:1'></div>
  <span style='color:#334155;font-size:10px'>LogistiQ v3.1 · Chennai–Vizag–Manesar</span>
</div>
<div style='height:44px'></div>
""", unsafe_allow_html=True)
