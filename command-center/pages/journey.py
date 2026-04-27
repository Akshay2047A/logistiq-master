# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd

def render(*args, **kwargs):
    st.markdown("### 🗺️ Full Shipment Journey")
    shp = st.session_state.get("selected_shipment")
    
    if not shp:
        st.info("No shipment selected. Please select a shipment from the sidebar.")
        return

    st.markdown(f"**Shipment ID:** {shp.get('id', 'N/A')} | **Cargo:** {shp.get('cargo_desc', 'N/A')}")
    st.markdown("---")
    
    stages = [
        {"name": "Origin", "planned": "Day 1, 08:00", "actual": "Day 1, 08:00", "delay": 0, "status": "✅ Done", "cost_inr": 45000, "cost_usd": 540},
        {"name": "Port of Loading", "planned": "Day 1, 14:00", "actual": "Day 1, 15:30", "delay": 1.5, "status": "✅ Done", "cost_inr": 18000, "cost_usd": 215},
        {"name": "Sea", "planned": "Day 3, 10:00", "actual": "Day 3, 10:00", "delay": 0, "status": "✅ Done", "cost_inr": 650000, "cost_usd": 7800},
        {"name": "Transshipment", "planned": "Day 5, 12:00", "actual": "Day 6, 14:00", "delay": 26, "status": "⚠️ Delayed", "cost_inr": 120000, "cost_usd": 1440},
        {"name": "Destination Port", "planned": "Day 8, 09:00", "actual": "Pending", "delay": 26, "status": "🔄 Active", "cost_inr": 25000, "cost_usd": 300},
        {"name": "Rail Yard", "planned": "Day 9, 06:00", "actual": "Pending", "delay": 0, "status": "⏳ Pending", "cost_inr": 90000, "cost_usd": 1080},
        {"name": "Truck", "planned": "Day 10, 08:00", "actual": "Pending", "delay": 0, "status": "⏳ Pending", "cost_inr": 35000, "cost_usd": 420},
        {"name": "Delivery", "planned": "Day 10, 16:00", "actual": "Pending", "delay": 0, "status": "⏳ Pending", "cost_inr": 0, "cost_usd": 0},
    ]

    # Horizontal stepper
    cols = st.columns(len(stages))
    for i, stage in enumerate(stages):
        with cols[i]:
            if "Done" in stage["status"]:
                color = "#4ade80"
                border_color = "rgba(74,222,128,0.5)"
            elif "Delayed" in stage["status"]:
                color = "#fbbf24"
                border_color = "rgba(251,191,36,0.5)"
            elif "Active" in stage["status"]:
                color = "#60a5fa"
                border_color = "rgba(96,165,250,0.5)"
            else:
                color = "#94a3b8"
                border_color = "rgba(255,255,255,0.1)"
                
            st.markdown(f"""
            <div class='glass-card' style='border-top: 4px solid {color}; border-color: {border_color}; padding: 10px; text-align: center; height: 160px; display: flex; flex-direction: column; justify-content: space-between;'>
                <div>
                    <div style='font-size: 13px; font-weight: 700; color: #e7efff; margin-bottom: 6px;'>{stage['name']}</div>
                    <div style='font-size: 10px; color: #94a3b8;'>Plan: {stage['planned']}</div>
                    <div style='font-size: 10px; color: #94a3b8;'>Act: {stage['actual']}</div>
                </div>
                <div>
                    <div style='font-size: 10px; color: #f87171; margin: 4px 0;'>Delay: {stage['delay']}h</div>
                    <div style='font-size: 11px; font-weight: 700; color: {color}; background: rgba(0,0,0,0.2); padding: 4px; border-radius: 4px;'>{stage['status']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("#### 💰 Cost Table per Leg")
    
    df = pd.DataFrame(stages)
    df = df[['name', 'cost_inr', 'cost_usd']]
    df.columns = ["Leg", "Cost (INR)", "Cost (USD)"]
    df.loc["Total"] = pd.Series({"Leg": "Total", "Cost (INR)": df["Cost (INR)"].sum(), "Cost (USD)": df["Cost (USD)"].sum()})
    
    # Format currency
    df["Cost (INR)"] = df["Cost (INR)"].apply(lambda x: f"₹ {x:,.2f}" if isinstance(x, (int, float)) else x)
    df["Cost (USD)"] = df["Cost (USD)"].apply(lambda x: f"$ {x:,.2f}" if isinstance(x, (int, float)) else x)
    
    st.table(df)
