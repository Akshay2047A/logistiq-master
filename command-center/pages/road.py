# -*- coding: utf-8 -*-
"""Road Logistics page."""

import time
import streamlit as st
from components.maps import render_road_map
from utils.data import get_real_road_route


def render(trucks, ports):
    st.markdown("#### 🚛 Road Logistics — FASTag Telemetry Dashboard")

    # Route calculator
    st.markdown("##### 🗺 Real Route Calculator")
    c1, c2 = st.columns(2)
    orig = c1.text_input("Truck departure point", placeholder="Chennai Port", key="road_orig")
    dest = c2.text_input("Delivery destination", placeholder="Manesar, Haryana", key="road_dest")
    if st.button("Calculate Real Route (Google Maps)", use_container_width=True, key="calc_route"):
        if orig and dest:
            with st.spinner("Calculating via Google Maps..."):
                r = get_real_road_route(orig, dest)
            if r.get("route_found"):
                r1, r2, r3, r4 = st.columns(4)
                r1.metric("Distance", f"{r['distance_km']} km")
                r2.metric("Drive Time", f"{r['duration_hours']} hours")
                r3.metric("Est. Fuel Cost", f"₹{r['distance_km'] * 12 * 2.5 / 100:,.0f}")
                r4.metric("Est. Toll", f"₹{r['distance_km'] * 1.5:,.0f}")
                st.caption("Route data from Google Maps Routes API | Traffic-aware")
            else:
                st.warning("Could not find route. Check city names.")

    st.markdown("---")

    # Fleet metrics
    available = sum(1 for t in trucks if t.get("availability") in ("Waiting", "Standby"))
    t1, t2, t3, t4 = st.columns(4)
    t1.metric("Trucks Tracked", len(trucks))
    t2.metric("Available", available)
    t3.metric("Deadhead Saved", "1,240 km")
    t4.metric("Fuel Saved", "₹3.8L")

    render_road_map(trucks, cyclone_on=st.session_state.get("cyclone_triggered", False), height=380)

    st.dataframe(
        [{"Truck": t["id"], "Driver": t.get("driver", ""), "Status": t.get("availability", ""),
          "Cargo": t.get("cargo", ""), "Load (t)": t.get("load_tons", ""),
          "Hub": t.get("origin_hub", ""), "ETA": t.get("eta_local", "")}
         for t in trucks],
        use_container_width=True, hide_index=True,
    )

    # Cold chain monitor
    st.markdown(
        """
        <div class='glass-card' style='border-color:#60a5fa'>
          <b>❄ Cold Chain Monitor</b><br>
          <span class='badge-blue'>2 Reefer Trucks Active</span><br><br>
          TRK-REEF-01 — Temp: <b>4°C ✅</b> — Cipla medical → Apollo Hospitals Chennai<br>
          TRK-REEF-02 — <span class='badge-amber'>⚠ ROUTE BLOCKED</span> — 8.4 tons Andhra vegetables<br>
          Spoilage risk: HIGH if not rerouted within 2 hours. Farmer income: ₹8.4L
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("🤖 Emergency Cold Chain Reroute", use_container_width=True, key="cold_reroute"):
        with st.spinner("Finding nearest cold storage..."):
            time.sleep(1.5)
        st.success("Rerouted to Nellore Cold Storage (NH16, 62km). ETA 1.8hrs. 12 farmers protected.")

    # Checkpoint
    st.markdown(
        """
        <div class='glass-card' style='border-color:#fbbf24'>
          📍 <b>AP–Telangana Border — NH16 Checkpoint</b><br>
          Current wait: 2.3 hrs | E-way bills: ✅ Auto-verified via FASTag<br>
          Toll per truck: ₹847 | 3 trucks in queue
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("🤖 Match Empty Trucks to Outbound Cargo", use_container_width=True, key="match_trucks"):
        with st.spinner("Matching..."):
            time.sleep(1.5)
        st.success("TRK-CHN-509 matched with Delhivery outbound (14.2t electronics). Saves 340 deadhead km.")
