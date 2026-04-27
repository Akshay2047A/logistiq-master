# -*- coding: utf-8 -*-
"""Reusable card + badge components (return HTML strings or render via st.markdown)."""
import streamlit as st


# ---------------------------------------------------------------------------
# Badges
# ---------------------------------------------------------------------------

LEVEL_BADGE = {
    "Critical": "<span class='badge badge-critical'>CRITICAL</span>",
    "High":     "<span class='badge badge-high'>HIGH</span>",
    "Medium":   "<span class='badge badge-medium'>MEDIUM</span>",
    "Low":      "<span class='badge badge-low'>LOW</span>",
    "Normal":   "<span class='badge badge-safe'>NORMAL</span>",
    "Advisory": "<span class='badge badge-medium'>ADVISORY</span>",
    "Port Affected": "<span class='badge badge-critical'>PORT AFFECTED</span>",
}

STATUS_BADGE = {
    "on_time":  "<span class='badge badge-safe'>ON TIME</span>",
    "delayed":  "<span class='badge badge-high'>DELAYED</span>",
    "cancelled":"<span class='badge badge-critical'>CANCELLED</span>",
}


def risk_badge(level: str) -> str:
    return LEVEL_BADGE.get(level, f"<span class='badge badge-medium'>{level}</span>")


def status_badge(status: str) -> str:
    return STATUS_BADGE.get(status, f"<span class='badge badge-medium'>{status}</span>")


# ---------------------------------------------------------------------------
# Metric card
# ---------------------------------------------------------------------------

def metric_card(label: str, value: str, delta: str = "", icon: str = "", delta_good: bool = True):
    delta_color = "#4ade80" if delta_good else "#f87171"
    delta_html = f"<div class='metric-delta' style='color:{delta_color}'>{delta}</div>" if delta else ""
    return f"""
<div class='metric-card'>
  <div class='metric-icon'>{icon}</div>
  <div class='metric-label'>{label}</div>
  <div class='metric-value'>{value}</div>
  {delta_html}
</div>"""


def render_metric_card(label: str, value: str, delta: str = "", icon: str = "", delta_good: bool = True):
    st.markdown(metric_card(label, value, delta, icon, delta_good), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Shipment compact card (sidebar list item)
# ---------------------------------------------------------------------------

def shipment_list_card(s: dict) -> str:
    risk = s.get("risk_data", {}) or {}
    level = risk.get("risk_level", "Unknown")
    colors = {"Critical": "#f87171", "High": "#fbbf24", "Medium": "#60a5fa", "Low": "#4ade80"}
    border = colors.get(level, "#60a5fa")
    sid = s.get("id", "")
    dest = s.get("destination", "")
    mode_icons = {"Sea (Vessel)": "🚢", "Rail": "🚂", "Road (Truck)": "🚛", "Air": "✈️"}
    mode_icon = mode_icons.get(s.get("transport_mode", ""), "📦")
    return f"""
<div class='shipment-list-card' style='border-left:3px solid {border}' id='sc-{sid}'>
  <span style='font-size:18px'>{mode_icon}</span>
  <div style='flex:1'>
    <div class='card-title'>{sid}</div>
    <div class='card-sub'>→ {dest}</div>
  </div>
  {risk_badge(level)}
</div>"""


# ---------------------------------------------------------------------------
# Alert feed card
# ---------------------------------------------------------------------------

def alert_card(alert: dict) -> str:
    icons = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}
    sev = alert.get("severity", "Medium")
    icon = icons.get(sev, "🔵")
    ts = alert.get("timestamp", "")
    msg = alert.get("message", "")
    return f"""
<div class='alert-card'>
  <span style='font-size:20px'>{icon}</span>
  <div style='flex:1'>
    <div class='alert-msg'>{msg}</div>
    <div class='card-sub'>{ts}</div>
  </div>
  {risk_badge(sev)}
</div>"""


# ---------------------------------------------------------------------------
# Port weather card
# ---------------------------------------------------------------------------

def port_weather_card(port: dict, weather: dict) -> str:
    wind = weather.get("wind_kph", 0) or 0
    cond = weather.get("condition", "Unknown")
    temp = weather.get("temp_c", "--")
    vis = weather.get("visibility_km", "--")
    precip = weather.get("precip_mm", 0)
    is_dang = weather.get("is_dangerous", False)
    has_alerts = bool(weather.get("alerts"))

    if has_alerts or is_dang:
        badge = LEVEL_BADGE["Port Affected"]
    elif wind > 45:
        badge = LEVEL_BADGE["Advisory"]
    else:
        badge = LEVEL_BADGE["Normal"]

    # Wind bar
    wind_pct = min(100, int(wind / 120 * 100))
    wind_color = "#f87171" if wind > 60 else "#fbbf24" if wind > 45 else "#4ade80"

    return f"""
<div class='port-weather-card'>
  <div class='port-weather-header'>
    <b>{port.get('name', '')}</b> {badge}
  </div>
  <div class='port-weather-body'>
    <div>🌡 {temp}°C &nbsp;|&nbsp; 👁 {vis} km &nbsp;|&nbsp; 🌧 {precip} mm</div>
    <div style='margin-top:6px'>
      💨 {wind} kph
      <div style='background:#1e293b;border-radius:4px;height:6px;margin-top:4px'>
        <div style='width:{wind_pct}%;height:6px;background:{wind_color};border-radius:4px'></div>
      </div>
    </div>
    <div style='margin-top:6px;font-size:12px;color:#94a3b8'>{cond}</div>
  </div>
</div>"""


# ---------------------------------------------------------------------------
# Loading skeleton
# ---------------------------------------------------------------------------

def skeleton_card(height: int = 80) -> str:
    return f"<div class='skeleton' style='height:{height}px;border-radius:10px;margin:8px 0'></div>"


def render_skeleton(rows: int = 3, height: int = 80):
    for _ in range(rows):
        st.markdown(skeleton_card(height), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Empty state
# ---------------------------------------------------------------------------

def empty_state(icon: str, title: str, subtitle: str = ""):
    st.markdown(f"""
<div class='empty-state'>
  <div style='font-size:48px'>{icon}</div>
  <div class='empty-title'>{title}</div>
  <div class='empty-sub'>{subtitle}</div>
</div>""", unsafe_allow_html=True)
