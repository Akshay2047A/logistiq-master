# -*- coding: utf-8 -*-
"""Air Cargo Operations page."""
import streamlit as st
from logistiq.components import charts as C, cards as K


AIR_ROUTES = [
    {"route": "Chennai ✈ Delhi (IGI)", "airline": "IndiGo Cargo", "freq": "3x daily", "cost_per_ton": 22000, "transit_hrs": 3.5, "co2_factor": 8.2},
    {"route": "Hyderabad ✈ Delhi (IGI)", "airline": "Air India Cargo", "freq": "5x daily", "cost_per_ton": 19500, "transit_hrs": 2.8, "co2_factor": 7.1},
    {"route": "Chennai ✈ Mumbai", "airline": "Blue Dart", "freq": "2x daily", "cost_per_ton": 14000, "transit_hrs": 2.2, "co2_factor": 5.6},
    {"route": "Vizag ✈ Delhi (IGI)", "airline": "SpiceJet Cargo", "freq": "1x daily", "cost_per_ton": 21000, "transit_hrs": 3.0, "co2_factor": 7.8},
]


def render():
    st.markdown("### ✈ Air Cargo Operations")
    st.caption("Emergency escalation routes — use when deadline risk is critical")

    col_routes, col_calc = st.columns([1.4, 1])

    with col_routes:
        st.markdown("#### 🛫 Available Air Routes")
        for r in AIR_ROUTES:
            cost_str = f"₹{r['cost_per_ton']:,}/ton"
            st.markdown(f"""
<div class='glass-card' style='border-color:rgba(167,139,250,0.3)'>
  <div style='display:flex;justify-content:space-between;margin-bottom:4px'>
    <b style='font-size:13px'>{r['route']}</b>
    <span style='font-size:12px;color:#a78bfa'>{r['airline']}</span>
  </div>
  <div style='display:flex;gap:16px;font-size:11px;color:#94a3b8'>
    <span>🕐 {r['transit_hrs']} hrs</span>
    <span>✈ {r['freq']}</span>
    <span>💰 {cost_str}</span>
    <span>🌱 {r['co2_factor']}x CO₂ vs rail</span>
  </div>
</div>""", unsafe_allow_html=True)

    with col_calc:
        st.markdown("#### 💰 Air Freight Cost Calculator")
        weight = st.number_input("Cargo weight (tons)", 0.5, 200.0, 5.0, step=0.5, key="air_weight")
        selected_route = st.selectbox("Route", [r["route"] for r in AIR_ROUTES], key="air_route")
        route_data = next((r for r in AIR_ROUTES if r["route"] == selected_route), AIR_ROUTES[0])

        cost_total = weight * route_data["cost_per_ton"]
        co2 = weight * route_data["co2_factor"]

        st.markdown(f"""
<div class='glass-card' style='text-align:center'>
  <div style='font-size:12px;color:#94a3b8'>Total Air Freight Cost</div>
  <div style='font-size:30px;font-weight:700;color:#a78bfa'>₹{cost_total:,.0f}</div>
  <div style='font-size:12px;color:#64748b;margin-top:4px'>Transit: {route_data['transit_hrs']} hrs | CO₂: {co2:.1f} tons</div>
</div>""", unsafe_allow_html=True)

        st.markdown("**CO₂ Footprint Comparison**")
        fig = C.co2_comparison_chart(
            sea=weight * 0.8, rail=weight * 0.3, road=weight * 1.2, air=co2
        )
        st.plotly_chart(fig, use_container_width=True, key="air_co2", config={"displayModeBar": True, "displaylogo": False, "modeBarButtonsToAdd": ["downloadSVG"]})

    # ── Escalation threshold ───────────────────────────
    st.markdown("---")
    st.markdown("#### 🚨 Escalation Decision Matrix")
    st.markdown("""
<div class='glass-card'>
  <table style='width:100%;border-collapse:collapse;font-size:12px'>
    <tr style='border-bottom:1px solid #1e3a5f'>
      <th style='padding:8px;color:#64748b;text-align:left'>Condition</th>
      <th style='padding:8px;color:#64748b'>Sea</th>
      <th style='padding:8px;color:#64748b'>Rail</th>
      <th style='padding:8px;color:#64748b'>Air</th>
    </tr>
    <tr style='border-bottom:1px solid #1e293b'>
      <td style='padding:8px'>Normal conditions</td>
      <td style='padding:8px;text-align:center;color:#4ade80'>✅ Primary</td>
      <td style='padding:8px;text-align:center;color:#4ade80'>✅ Primary</td>
      <td style='padding:8px;text-align:center;color:#f87171'>❌ Too expensive</td>
    </tr>
    <tr style='border-bottom:1px solid #1e293b'>
      <td style='padding:8px'>Deadline &lt; 48 hrs</td>
      <td style='padding:8px;text-align:center;color:#fbbf24'>⚠ Risk</td>
      <td style='padding:8px;text-align:center;color:#4ade80'>✅ If available</td>
      <td style='padding:8px;text-align:center;color:#fbbf24'>⚠ Evaluate</td>
    </tr>
    <tr>
      <td style='padding:8px'>Deadline &lt; 18 hrs</td>
      <td style='padding:8px;text-align:center;color:#f87171'>❌ Too slow</td>
      <td style='padding:8px;text-align:center;color:#f87171'>❌ Too slow</td>
      <td style='padding:8px;text-align:center;color:#4ade80'>✅ ESCALATE</td>
    </tr>
  </table>
</div>""", unsafe_allow_html=True)
