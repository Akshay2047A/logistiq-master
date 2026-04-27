# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px

from logistiq.components.maps import make_base_map, add_shipment_route
from logistiq.components.charts import co2_comparison_chart
from logistiq.utils.data import get_live_exchange_rate, resolve_city_coords

def render(*args, **kwargs):
    st.markdown("### 🗺️ Full Shipment Journey")
    shp = st.session_state.get("selected_shipment")
    
    if not shp:
        st.info("No shipment selected. Please select a shipment from the sidebar.")
        return

    st.markdown(f"**Shipment ID:** {shp.get('id', 'N/A')} | **Cargo:** {shp.get('cargo_desc', 'N/A')}")
    st.markdown("---")
    
    # ── JOURNEY 1: Stages Setup ──
    origin = shp.get("origin", "Chennai Factory")
    dest = shp.get("destination", "Manesar Plant")
    weight = float(shp.get("weight_tons", 100.0))
    
    stages = [
        {"name": "Origin Factory", "party": "Origin Logistics", "planned": "Day 1, 08:00", "actual": "Day 1, 08:00", "delay": 0, "status": "Completed", "lat": 12.97, "lon": 80.12},
        {"name": "Port of Loading", "party": "Chennai Port Trust", "planned": "Day 1, 14:00", "actual": "Day 1, 15:30", "delay": 1.5, "status": "Completed", "lat": 13.0827, "lon": 80.2707},
        {"name": "Sea Vessel", "party": "Maersk Line", "planned": "Day 3, 10:00", "actual": "Day 3, 10:00", "delay": 0, "status": "Completed", "lat": 15.0, "lon": 81.5},
        {"name": "Transshipment Port", "party": "Vizag Port", "planned": "Day 5, 12:00", "actual": "Day 6, 14:00", "delay": 26, "status": "At Risk", "lat": 17.6868, "lon": 83.2185},
        {"name": "Destination Port", "party": "Vizag Customs", "planned": "Day 8, 09:00", "actual": "Pending", "delay": 26, "status": "Delayed", "lat": 17.6868, "lon": 83.2185},
        {"name": "Rail Yard", "party": "CONCOR", "planned": "Day 9, 06:00", "actual": "Pending", "delay": 0, "status": "Pending", "lat": 17.4399, "lon": 78.4983},
        {"name": "Truck", "party": "Delhivery Freight", "planned": "Day 10, 08:00", "actual": "Pending", "delay": 0, "status": "Pending", "lat": 21.1458, "lon": 79.0882},
        {"name": "Final Delivery", "party": "Consignee", "planned": "Day 10, 16:00", "actual": "Pending", "delay": 0, "status": "Pending", "lat": 28.3575, "lon": 76.9312},
    ]

    if "journey_stage" not in st.session_state:
        st.session_state.journey_stage = 3
    if "map_center" not in st.session_state:
        st.session_state.map_center = [stages[3]["lat"], stages[3]["lon"]]

    # Horizontal stepper UI
    cols = st.columns(len(stages))
    for i, stage in enumerate(stages):
        with cols[i]:
            delay = stage["delay"]
            if delay > 4:
                delay_col = "#f87171"
            elif delay > 0:
                delay_col = "#fbbf24"
            else:
                delay_col = "#4ade80"
                
            status = stage["status"]
            if status in ["Completed", "On Time"]:
                color = "#4ade80"; border_color = "rgba(74,222,128,0.5)"
            elif status in ["Delayed", "At Risk"]:
                color = "#f87171" if status == "At Risk" else "#fbbf24"
                border_color = "rgba(248,113,113,0.5)" if status == "At Risk" else "rgba(251,191,36,0.5)"
            else:
                color = "#94a3b8"; border_color = "rgba(255,255,255,0.1)"
                
            st.markdown(f"""
            <div class='glass-card' style='border-top: 4px solid {color}; border-color: {border_color}; padding: 10px; text-align: center; height: 180px; display: flex; flex-direction: column; justify-content: space-between;'>
                <div>
                    <div style='font-size: 11px; font-weight: 700; color: #e7efff; margin-bottom: 2px;'>{stage['name']}</div>
                    <div style='font-size: 9px; color: #60a5fa;'>{stage['party']}</div>
                    <div style='font-size: 9px; color: #94a3b8; margin-top: 4px;'>Plan: {stage['planned']}</div>
                    <div style='font-size: 9px; color: #94a3b8;'>Act: {stage['actual']}</div>
                </div>
                <div>
                    <div style='font-size: 10px; color: {delay_col}; margin: 4px 0;'>Delay: {stage['delay']}h</div>
                    <div style='font-size: 10px; font-weight: 700; color: {color}; background: rgba(0,0,0,0.2); padding: 4px; border-radius: 4px;'>{stage['status']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("📍 Zoom to", key=f"zoom_{i}", use_container_width=True):
                st.session_state.journey_stage = i
                st.session_state.map_center = [stage["lat"], stage["lon"]]
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Checkbox layout: Left for Map & Cost/CO2, Right for Checklist
    main_col, side_col = st.columns([3, 1], gap="large")

    with main_col:
        # ── JOURNEY 2: Synchronized live map ──
        st.markdown("#### 🗺️ Live Route Map")
        fmap = make_base_map(lat=st.session_state.map_center[0], lon=st.session_state.map_center[1], zoom=7)
        add_shipment_route(fmap, shp)
        
        # Highlight active stage
        active = stages[st.session_state.journey_stage]
        folium.Marker(
            [active["lat"], active["lon"]],
            icon=folium.DivIcon(html="<div style='font-size:24px; animation: pulse 1s infinite;'>🎯</div>"),
            tooltip=active["name"]
        ).add_to(fmap)
        
        st_folium(fmap, use_container_width=True, height=400, key="journey_map")

        st.markdown("<br>", unsafe_allow_html=True)

        # ── JOURNEY 3: Per-leg cost breakdown table ──
        st.markdown("#### 💰 Cost Breakdown")
        fx_rate = get_live_exchange_rate()
        if isinstance(fx_rate, dict):
            fx_rate = fx_rate.get("USD_INR", 83.5)
        
        costs = [
            {"Mode": "Road (First Mile)", "Carrier": "Origin Logistics", "Distance (km)": 45, "Rate (₹/km)": 150, "Quote": 6500, "Subtotal (INR)": 6750},
            {"Mode": "Sea", "Carrier": "Maersk Line", "Distance (km)": 850, "Rate (₹/km)": 450, "Quote": 380000, "Subtotal (INR)": 382500},
            {"Mode": "Rail", "Carrier": "CONCOR", "Distance (km)": 720, "Rate (₹/km)": 85, "Quote": 60000, "Subtotal (INR)": 61200},
            {"Mode": "Road (Last Mile)", "Carrier": "Delhivery Freight", "Distance (km)": 120, "Rate (₹/km)": 160, "Quote": 19200, "Subtotal (INR)": 19200},
        ]
        df_costs = pd.DataFrame(costs)
        df_costs["Subtotal (USD)"] = df_costs["Subtotal (INR)"] / fx_rate
        df_costs["vs Quote"] = df_costs["Subtotal (INR)"] - df_costs["Quote"]
        
        # Totals
        total_inr = df_costs["Subtotal (INR)"].sum()
        total_usd = df_costs["Subtotal (USD)"].sum()
        total_quote = df_costs["Quote"].sum()
        df_costs.loc["Total"] = ["Total", "-", df_costs["Distance (km)"].sum(), "-", total_quote, total_inr, total_usd, total_inr - total_quote]
        # Align columns
        df_costs = df_costs[["Mode", "Carrier", "Distance (km)", "Rate (₹/km)", "Subtotal (INR)", "Subtotal (USD)", "vs Quote"]]
        
        def highlight_overbudget(val):
            color = "#f87171" if isinstance(val, (int, float)) and val > 0 else "#4ade80" if isinstance(val, (int, float)) and val <= 0 else ""
            return f'color: {color}'

        styled_df = df_costs.style.format({
            "Subtotal (INR)": "₹{:,.2f}",
            "Subtotal (USD)": "${:,.2f}",
            "Quote": "₹{:,.2f}",
            "vs Quote": "{:+,.2f}",
        }).map(highlight_overbudget, subset=["vs Quote"])

        st.dataframe(styled_df, use_container_width=True)
        csv = df_costs.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export CSV", csv, "costs.csv", "text/csv")

        st.markdown("<br>", unsafe_allow_html=True)

        # ── JOURNEY 4: Carbon footprint tracker ──
        st.markdown("#### 🌱 Carbon Footprint Tracker")
        sea_co2  = weight * 850 * 0.010
        rail_co2 = weight * 720 * 0.025
        road_co2 = weight * (45+120) * 0.100
        total_co2 = sea_co2 + rail_co2 + road_co2
        
        c1, c2, c3 = st.columns([1, 1.5, 2])
        with c1:
            st.markdown(f"""
            <div class='metric-card' style='height: 100%; display: flex; flex-direction: column; justify-content: center;'>
                <div class='metric-label'>Total CO₂ Emitted</div>
                <div class='metric-value' style='font-size: 32px;'>{total_co2/1000:.1f}</div>
                <div class='metric-delta'>Tons</div>
            </div>
            """, unsafe_allow_html=True)
            
        with c2:
            co2_df = pd.DataFrame({
                "Mode": ["Sea", "Rail", "Road"],
                "CO2": [sea_co2, rail_co2, road_co2]
            })
            fig_pie = px.pie(co2_df, values="CO2", names="Mode", hole=0.6, 
                             color="Mode", color_discrete_map={"Sea": "#44c5ff", "Rail": "#fbbf24", "Road": "#4ade80"})
            fig_pie.update_layout(height=220, margin=dict(l=0, r=0, t=20, b=0), paper_bgcolor="rgba(0,0,0,0)", 
                                  font={"color": "#e7efff"}, showlegend=False)
            fig_pie.add_annotation(text="CO₂", x=0.5, y=0.5, font_size=20, showarrow=False)
            st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar": True, "displaylogo": False, "modeBarButtonsToAdd": ["downloadSVG"]})
            
        with c3:
            pure_sea = weight * (850+720+165) * 0.010
            pure_air = weight * (850+720+165) * 0.500
            fig_bar = co2_comparison_chart(pure_sea/1000, rail_co2/1000, road_co2/1000, pure_air/1000)
            st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": True, "displaylogo": False, "modeBarButtonsToAdd": ["downloadSVG"]})

    with side_col:
        # ── JOURNEY 5: Trade document checklist ──
        st.markdown("#### 📄 Document Checklist")
        documents = [
            ("Bill of Lading", "Issued"),
            ("Letter of Credit", "Confirmed"),
            ("Customs Declaration", "Filed"),
            ("Packing List", "Uploaded"),
            ("Certificate of Origin", "Issued"),
            ("Phytosanitary Certificate", "Missing"),
        ]
        
        for doc, status in documents:
            if status in ["Issued", "Confirmed", "Uploaded", "Cleared"]:
                icon = "✅"; badge_class = "badge-safe"
            elif status in ["Pending", "Filed", "In Review"]:
                icon = "⏳"; badge_class = "badge-amber"
            else:
                icon = "❌"; badge_class = "badge-critical"
                
            st.markdown(f"""
            <div class='glass-card' style='padding: 10px; margin-bottom: 8px;'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <span style='font-size: 12px;'>{icon} {doc}</span>
                    <span class='badge {badge_class}' style='font-size: 9px;'>{status}</span>
                </div>
                {f"<div style='font-size: 10px; color: #f87171; margin-top: 6px;'>⚠ May block port clearance</div>" if status == "Missing" else ""}
            </div>
            """, unsafe_allow_html=True)

