# -*- coding: utf-8 -*-
"""Plotly charts — risk matrix, gauges, Gantt, sparklines."""

import plotly.graph_objects as go
import streamlit as st


def risk_matrix_chart(shipments_data):
    """Scatter bubble chart: X=Financial Exposure, Y=Disruption Prob, Size=Weight, Color=Risk."""
    if not shipments_data:
        return

    colors_map = {"Critical": "#f87171", "High": "#fbbf24", "Medium": "#60a5fa", "Low": "#4ade80"}
    x, y, sizes, colors, texts, hovers = [], [], [], [], [], []

    for s in shipments_data:
        risk = s.get("risk_data", {})
        val = float(s.get("value_crore", 10))
        score = risk.get("risk_score", 30)
        weight = float(s.get("weight_tons", 100))
        level = risk.get("risk_level", "Medium")

        x.append(val)
        y.append(score)
        sizes.append(max(15, min(60, weight / 10)))
        colors.append(colors_map.get(level, "#60a5fa"))
        texts.append(s.get("id", ""))
        hovers.append(
            f"<b>{s.get('cargo_desc', 'Shipment')}</b><br>"
            f"Value: ₹{val} Cr<br>"
            f"Risk: {level} ({score}%)<br>"
            f"Weight: {weight}t<br>"
            f"{s.get('origin', '')} → {s.get('destination', '')}"
        )

    fig = go.Figure(go.Scatter(
        x=x, y=y, mode="markers+text",
        marker=dict(size=sizes, color=colors, opacity=0.8, line=dict(width=1, color="rgba(255,255,255,0.3)")),
        text=texts, textposition="top center", textfont=dict(size=10, color="white"),
        hovertemplate="%{customdata}<extra></extra>",
        customdata=hovers,
    ))

    fig.update_layout(
        title=dict(text="Live Risk Matrix", font=dict(size=16, color="white")),
        xaxis=dict(title="Financial Exposure (₹ Cr)", color="#94a3b8", gridcolor="rgba(255,255,255,0.05)"),
        yaxis=dict(title="Disruption Probability (%)", range=[0, 100], color="#94a3b8", gridcolor="rgba(255,255,255,0.05)"),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e7efff"), height=360, margin=dict(l=50, r=20, t=50, b=50),
        # Risk zone backgrounds
        shapes=[
            dict(type="rect", x0=0, x1=1000, y0=0, y1=30, fillcolor="rgba(74,222,128,0.05)", line_width=0),
            dict(type="rect", x0=0, x1=1000, y0=30, y1=60, fillcolor="rgba(96,165,250,0.05)", line_width=0),
            dict(type="rect", x0=0, x1=1000, y0=60, y1=100, fillcolor="rgba(248,113,113,0.05)", line_width=0),
        ],
    )
    st.plotly_chart(fig, use_container_width=True, key="risk_matrix")


def risk_gauge(score, idx=0, height=180):
    """Single risk score gauge."""
    color = "red" if score > 70 else "orange" if score >= 40 else "green"
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=score,
        title={"text": "Risk Score", "font": {"size": 14, "color": "white"}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#64748b"},
            "bar": {"color": color},
            "steps": [
                {"range": [0, 30], "color": "rgba(74,222,128,0.1)"},
                {"range": [30, 60], "color": "rgba(251,191,36,0.1)"},
                {"range": [60, 100], "color": "rgba(248,113,113,0.1)"},
            ],
            "threshold": {"line": {"color": "#f87171", "width": 2}, "thickness": 0.8, "value": 70},
        },
        number={"font": {"size": 28, "color": "white"}},
    ))
    fig.update_layout(
        height=height, margin=dict(l=15, r=15, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)", font={"color": "white"},
    )
    st.plotly_chart(fig, use_container_width=True, key=f"gauge_{idx}")


def simulation_gantt(reroute_data):
    """Gantt chart for simulation timeline visualization."""
    cascade = reroute_data.get("cascade", {})
    time_d = reroute_data.get("time", {})

    sea_eta = cascade.get("sea", {}).get("new_eta_hours", 6)
    rail_hours = 8.25
    road_hours = cascade.get("road", {}).get("eta_hours", 5.4)

    fig = go.Figure()

    # Original route (blocked)
    fig.add_trace(go.Bar(y=["Original Route"], x=[48], orientation="h",
        marker=dict(color="#f87171", opacity=0.5, pattern=dict(shape="x")),
        name="Blocked", text=["BLOCKED — Chennai Port"], textposition="inside",
        textfont=dict(color="white", size=11)))

    # Sea leg
    fig.add_trace(go.Bar(y=["Sea (Vizag Diversion)"], x=[sea_eta], orientation="h",
        marker=dict(color="#44c5ff"), name="Sea Leg",
        text=[f"{sea_eta}h — Divert to Vizag"], textposition="inside",
        textfont=dict(color="white", size=11)))

    # Rail leg
    fig.add_trace(go.Bar(y=["Rail (SCR 58501)"], x=[rail_hours], base=[sea_eta], orientation="h",
        marker=dict(color="#fbbf24"), name="Rail Leg",
        text=[f"{rail_hours}h — Vizag→Secunderabad"], textposition="inside",
        textfont=dict(color="white", size=11)))

    # Road leg
    fig.add_trace(go.Bar(y=["Road (3 Trucks)"], x=[road_hours], base=[sea_eta + rail_hours], orientation="h",
        marker=dict(color="#4ade80"), name="Road Leg",
        text=[f"{road_hours}h — Sec→Manesar"], textposition="inside",
        textfont=dict(color="white", size=11)))

    # Deadline marker
    fig.add_vline(x=96, line=dict(color="#f87171", width=2, dash="dot"),
        annotation=dict(text="⏰ 96h Deadline", font=dict(color="#f87171", size=12)))

    fig.update_layout(
        title=dict(text="Cascade Reroute Timeline", font=dict(size=16, color="white")),
        xaxis=dict(title="Hours", color="#94a3b8", gridcolor="rgba(255,255,255,0.08)"),
        yaxis=dict(color="#e7efff"), barmode="overlay",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e7efff"), height=280, margin=dict(l=20, r=20, t=50, b=40),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True, key="sim_gantt")


def exchange_rate_display(rates):
    """Mini display for exchange rates."""
    usd_inr = rates.get("USD_INR", 83.5)
    eur_inr = rates.get("EUR_INR", 90.0)
    usd_cny = rates.get("USD_CNY", 7.24)

    fig = go.Figure()
    fig.add_trace(go.Indicator(mode="number+delta", value=usd_inr,
        title={"text": "USD/INR", "font": {"size": 12}},
        delta={"reference": 83.0, "relative": True, "valueformat": ".2%"},
        number={"font": {"size": 22}}, domain={"row": 0, "column": 0}))
    fig.add_trace(go.Indicator(mode="number+delta", value=eur_inr,
        title={"text": "EUR/INR", "font": {"size": 12}},
        delta={"reference": 89.0, "relative": True, "valueformat": ".2%"},
        number={"font": {"size": 22}}, domain={"row": 0, "column": 1}))
    fig.add_trace(go.Indicator(mode="number+delta", value=usd_cny,
        title={"text": "USD/CNY", "font": {"size": 12}},
        delta={"reference": 7.2, "relative": True, "valueformat": ".2%"},
        number={"font": {"size": 22}}, domain={"row": 0, "column": 2}))

    fig.update_layout(
        grid={"rows": 1, "columns": 3, "pattern": "independent"},
        height=120, margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)", font=dict(color="white"),
    )
    st.plotly_chart(fig, use_container_width=True, key="fx_rates")
