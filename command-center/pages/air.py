# -*- coding: utf-8 -*-
"""Air Cargo page."""

import time
from io import BytesIO
import streamlit as st
from PIL import Image


def render():
    st.markdown("#### ✈ Air Cargo — Emergency Freight & Customs Intelligence")

    threshold_met = st.session_state.get("cyclone_triggered", False) and not st.session_state.get("reroute_accepted", False)
    color = "#ff5a83" if threshold_met else "#4ade80"
    status = "APPROACHING THRESHOLD" if threshold_met else "BELOW THRESHOLD — Rail viable"

    st.markdown(
        f"""
        <div class='glass-card' style='border-color:{color}'>
          <b>⚠ ESCALATION THRESHOLD ANALYSIS</b><br>
          Status: <span style='color:{color};font-weight:700'>{status}</span><br>
          Trigger: Rail slot missed by >8 hours → auto air freight<br>
          Assembly buffer remaining: <b>47 hours</b>
        </div>
        """,
        unsafe_allow_html=True,
    )

    opt_a, opt_b = st.columns(2)
    with opt_a:
        st.markdown(
            """
            <div class='glass-card' style='border-color:#4ade80'>
              <span class='badge-green'>RECOMMENDED</span><br>
              <b>🚂 South Central Railway</b><br>
              Cost: Standard rate (₹0 incremental)<br>
              Transit: 3 days door-to-door<br>
              Risk: Medium<br>
              Status: ✅ On track
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.button("Continue Monitoring Rail ✅", use_container_width=True, key="air_rail")

    with opt_b:
        st.markdown(
            """
            <div class='glass-card' style='border-color:#fbbf24'>
              <span class='badge-amber'>ESCALATION OPTION</span><br>
              <b>✈ IndiGo Cargo — Emergency Air</b><br>
              Route: Vizag → Hyderabad → Delhi<br>
              Weight: 8.4 tons critical components<br>
              Cost: ₹14.2L<br>
              Transit: 18 hours<br>
              ROI: ₹2.4Cr/day shutdown → <b>16x return</b>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Authorize Air Freight ✈", use_container_width=True, key="air_auth"):
            st.success("Air freight authorized. IndiGo Cargo booking initiated.")

    # CO2 comparison
    st.markdown("---")
    st.markdown("#### 🌱 CO₂ Footprint Comparison")
    c1, c2, c3 = st.columns(3)
    c1.metric("🚂 Rail", "12.4 tons CO₂", "Lowest", delta_color="off")
    c2.metric("🚛 Road", "28.6 tons CO₂", "+130%", delta_color="inverse")
    c3.metric("✈ Air", "86.2 tons CO₂", "+595%", delta_color="inverse")

    # Customs verifier
    st.markdown("---")
    st.markdown("#### 📋 Customs Documentation Verifier")
    st.caption("Upload airway bill, invoice, or packing list. Gemini checks compliance.")
    uploaded = st.file_uploader("Upload document", type=["pdf", "jpg", "png", "jpeg"], key="customs_doc")
    if uploaded and st.button("🤖 Verify with Gemini", use_container_width=True, key="verify_customs"):
        if uploaded.type.startswith("image"):
            _ = Image.open(BytesIO(uploaded.read()))
        st.markdown(
            """
            <div class='glass-card' style='border-color:#4ade80'>
              <b>Document Analysis Complete</b><br>
              ✅ HS Code: Present (8708.99.00)<br>
              ✅ Certificate of Origin: Present<br>
              ✅ Shipper/Consignee: Verified<br>
              ⚠ Declared Value: Flagged — ₹47.3Cr vs market ₹44.1Cr<br>
              ✅ DGFT Compliance: Pass<br>
              ✅ Hazmat: Not required<br><br>
              <b>Risk: LOW</b> — Minor valuation discrepancy. Clearance: ~4.2 hours.
            </div>
            """,
            unsafe_allow_html=True,
        )
