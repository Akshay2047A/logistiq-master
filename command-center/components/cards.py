# -*- coding: utf-8 -*-
"""Reusable card components rendered as styled HTML via st.markdown."""

import streamlit as st


def risk_badge(level: str) -> str:
    """Return HTML for a colored risk-level pill badge."""
    cls_map = {
        "Critical": "badge-red",
        "High": "badge-amber",
        "Medium": "badge-blue",
        "Low": "badge-green",
    }
    cls = cls_map.get(level, "badge-blue")
    return f"<span class='{cls}'>{level.upper()}</span>"


def metric_card(label, value, delta="", icon="", border_color="#60a5fa"):
    """Render a glass KPI card with optional animated counter placeholder."""
    delta_html = f"<div class='metric-delta'>{delta}</div>" if delta else ""
    icon_html = f"<span style='font-size:20px'>{icon}</span> " if icon else ""
    st.markdown(
        f"""
        <div class='glass-card metric-card' style='border-color:{border_color};text-align:center;padding:16px'>
          <div class='metric-label'>{icon_html}{label}</div>
          <div class='metric-value'>{value}</div>
          {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def shipment_card(shipment, idx=0):
    """Compact shipment card for sidebar list."""
    risk = shipment.get("risk_data", {})
    risk_level = risk.get("risk_level", "Unknown")
    badge = risk_badge(risk_level)
    desc = shipment.get("cargo_desc", "Shipment")[:40]
    route = f"{shipment.get('origin', '?')} → {shipment.get('destination', '?')}"
    deadline = shipment.get("deadline_date", "")
    return f"""
    <div class='glass-card shipment-mini' style='padding:10px;margin:4px 0;cursor:pointer' id='shp-{idx}'>
      <div style='display:flex;justify-content:space-between;align-items:center'>
        <b style='font-size:12px;color:#e7efff'>{shipment.get('id', '')}</b>
        {badge}
      </div>
      <div style='font-size:11px;color:#94a3b8;margin-top:4px'>{desc}</div>
      <div style='font-size:11px;color:#64748b'>{route}</div>
      <div style='font-size:10px;color:#64748b'>Due: {deadline}</div>
    </div>
    """


def alert_card(icon, severity, description, timestamp, border_color="#60a5fa"):
    """Single alert feed item."""
    badge = risk_badge(severity) if severity in ("Critical", "High", "Medium", "Low") else f"<span class='badge-blue'>{severity}</span>"
    return f"""
    <div class='glass-card' style='padding:10px;margin:6px 0;border-color:{border_color}'>
      <div style='display:flex;justify-content:space-between;align-items:center'>
        <span>{icon} {badge} &nbsp; <span style='font-size:13px;color:#e7efff'>{description}</span></span>
      </div>
      <div style='font-size:10px;color:#64748b;margin-top:4px'>{timestamp}</div>
    </div>
    """


def port_weather_card(port_name, weather, show_tidal=True):
    """Port weather status card with wind progress bar."""
    wind = weather.get("wind_kph", 0) or 0
    cond = weather.get("condition", "Unknown")
    temp = weather.get("temp_c", "N/A")
    vis = weather.get("visibility_km", "N/A")
    precip = weather.get("precip_mm", 0)
    humidity = weather.get("humidity", "N/A")

    # Wind bar color
    if wind > 60:
        bar_color = "#f87171"
        status_badge = "<span class='badge-red'>⚠ PORT AFFECTED</span>"
    elif wind > 45:
        bar_color = "#fbbf24"
        status_badge = "<span class='badge-amber'>⚠ ADVISORY</span>"
    else:
        bar_color = "#4ade80"
        status_badge = "<span class='badge-green'>✅ NORMAL</span>"

    wind_pct = min(wind / 80 * 100, 100)

    alerts_html = ""
    if weather.get("alerts"):
        for a in weather["alerts"][:2]:
            alerts_html += f"<div style='font-size:11px;color:#f87171;margin-top:4px'>⚠ {a[:80]}</div>"

    st.markdown(
        f"""
        <div class='glass-card' style='padding:14px'>
          <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:8px'>
            <b style='font-size:14px'>{port_name}</b>
            {status_badge}
          </div>
          <div style='font-size:13px;color:#94a3b8;margin-bottom:6px'>🌤 {cond} &nbsp;|&nbsp; {temp}°C</div>
          <div style='font-size:12px;color:#94a3b8;margin-bottom:4px'>
            💨 Wind: <b>{wind}</b> kph
          </div>
          <div style='background:rgba(255,255,255,0.1);border-radius:4px;height:8px;overflow:hidden;margin-bottom:6px'>
            <div style='width:{wind_pct}%;height:100%;background:{bar_color};border-radius:4px;transition:width 0.5s'></div>
          </div>
          <div style='font-size:11px;color:#64748b'>
            👁 Visibility: {vis}km &nbsp;|&nbsp; 🌧 Precip: {precip}mm &nbsp;|&nbsp; 💧 Humidity: {humidity}%
          </div>
          {alerts_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def command_card_html(data):
    """Render the AI reroute command card."""
    cascade = data.get("cascade", {})
    conf = data.get("confidence", 0)

    sea = cascade.get("sea", {})
    rail = cascade.get("rail", {})
    road = cascade.get("road", {})

    return f"""
    <div class='cmd-card'>
      <div class='cmd-card-header'>
        🤖 AI REROUTE RECOMMENDATION &nbsp;&nbsp;
        <span class='badge-green'>Confidence: {conf}%</span>
      </div>
      <p><b>{data.get('primary_recommendation', '')}</b></p>

      <div class='cascade-step'>
        🚢 <b>Sea:</b> {sea.get('action', '')} —
        {sea.get('reason', '')}
      </div>
      <div class='cascade-step'>
        🚂 <b>Rail:</b> Train {rail.get('train_id', '')}
        ({rail.get('name', '')}) —
        {rail.get('wagons_needed', 0)} wagons —
        ETA: {rail.get('full_eta', '')}
      </div>
      <div class='cascade-step'>
        🚛 <b>Road:</b> {road.get('action', '')} —
        {road.get('eta_hours', 0)} hrs
      </div>
    </div>
    """


def empty_state(icon, title, subtitle):
    """Render an empty state placeholder."""
    st.markdown(
        f"""
        <div style='text-align:center;padding:40px 20px;opacity:0.5'>
          <div style='font-size:48px;margin-bottom:12px'>{icon}</div>
          <div style='font-size:16px;font-weight:600;color:#e7efff;margin-bottom:6px'>{title}</div>
          <div style='font-size:13px;color:#64748b'>{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def loading_skeleton(height=120, count=3):
    """Render loading skeleton placeholders."""
    for _ in range(count):
        st.markdown(
            f"""
            <div class='glass-card skeleton' style='height:{height}px;animation:skeleton-pulse 1.5s ease-in-out infinite'>
            </div>
            """,
            unsafe_allow_html=True,
        )
