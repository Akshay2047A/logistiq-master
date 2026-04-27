# -*- coding: utf-8 -*-
"""Plotly chart builders for LogistiQ."""
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd


# ---------------------------------------------------------------------------
# Risk Matrix (scatter)
# ---------------------------------------------------------------------------

RISK_COLORS_MAP = {"Critical": "#f87171", "High": "#fb923c", "Medium": "#fbbf24", "Low": "#4ade80", "Unknown": "#60a5fa"}


def risk_matrix_chart(shipments: list) -> go.Figure:
    if not shipments:
        fig = go.Figure()
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font={"color": "#94a3b8"}, height=340,
            title={"text": "Risk Matrix — No Active Shipments", "font": {"size": 14}},
        )
        return fig

    rows = []
    for s in shipments:
        rd = s.get("risk_data") or {}
        rows.append({
            "id": s.get("id", ""),
            "label": s.get("cargo_desc", s.get("id", ""))[:30],
            "exposure": float(s.get("value_crore", 0)),
            "probability": float(rd.get("risk_score", 0)),
            "weight": float(s.get("weight_tons", 50)),
            "risk_level": rd.get("risk_level", "Unknown"),
            "route": f"{s.get('origin','')} → {s.get('destination','')}",
            "recommendation": rd.get("recommendation", ""),
        })
    df = pd.DataFrame(rows)

    fig = go.Figure()
    for level, grp in df.groupby("risk_level"):
        fig.add_trace(go.Scatter(
            x=grp["exposure"], y=grp["probability"],
            mode="markers+text",
            name=level,
            text=grp["label"],
            textposition="top center",
            textfont={"size": 9, "color": "#e7efff"},
            marker=dict(
                size=grp["weight"].apply(lambda w: max(14, min(50, w / 10))),
                color=RISK_COLORS_MAP.get(level, "#60a5fa"),
                opacity=0.82,
                line=dict(width=1, color="rgba(255,255,255,0.13)"),
            ),
            customdata=grp[["route", "recommendation", "weight"]].values,
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Route: %{customdata[0]}<br>"
                "Exposure: ₹%{x:.1f} Cr<br>"
                "Risk Score: %{y}<br>"
                "Weight: %{customdata[2]} t<br>"
                "Action: %{customdata[1]}<extra></extra>"
            ),
        ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(14,22,38,0.6)",
        font={"color": "#e7efff"}, height=340,
        xaxis=dict(title="Financial Exposure (₹ Crore)", gridcolor="#1e3a5f", zeroline=False),
        yaxis=dict(title="Disruption Probability (%)", gridcolor="#1e3a5f", range=[0, 105], zeroline=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=10, r=10, t=30, b=10),
        title={"text": "Live Risk Matrix", "font": {"size": 14, "color": "#e7efff"}},
    )
    # Red quadrant annotation
    fig.add_shape(type="rect", x0=20, x1=500, y0=60, y1=105,
                  fillcolor="rgba(248,113,113,0.05)", line=dict(width=0))
    fig.add_annotation(x=25, y=103, text="⚠ High Risk Zone", showarrow=False,
                       font={"color": "#f87171", "size": 10})
    return fig


# ---------------------------------------------------------------------------
# Risk gauge
# ---------------------------------------------------------------------------

def risk_gauge(risk_score: int, label: str = "Risk Score", height: int = 180) -> go.Figure:
    color = "#f87171" if risk_score > 70 else "#fbbf24" if risk_score >= 40 else "#4ade80"
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=risk_score,
        title={"text": label, "font": {"size": 13, "color": "#94a3b8"}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#94a3b8"},
            "bar": {"color": color},
            "steps": [
                {"range": [0, 40], "color": "rgba(74,222,128,0.1)"},
                {"range": [40, 70], "color": "rgba(251,191,36,0.1)"},
                {"range": [70, 100], "color": "rgba(248,113,113,0.1)"},
            ],
            "threshold": {"line": {"color": color, "width": 3}, "thickness": 0.75, "value": risk_score},
        },
        number={"font": {"size": 28, "color": color}},
    ))
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=30, b=5),
                      paper_bgcolor="rgba(0,0,0,0)", font={"color": "#e7efff"})
    return fig


# ---------------------------------------------------------------------------
# Simulation Gantt chart
# ---------------------------------------------------------------------------

def simulation_gantt() -> go.Figure:
    tasks = [
        dict(Task="Original Route", Start=0,  Finish=48,  Color="#f87171",   Label="BLOCKED"),
        dict(Task="Sea (Vizag)",    Start=0,  Finish=18,  Color="#44c5ff",   Label="Sea Diversion"),
        dict(Task="Rail SCR 58501", Start=18, Finish=36,  Color="#fbbf24",   Label="SCR Godavari"),
        dict(Task="Road (3 Trucks)",Start=36, Finish=51,  Color="#4ade80",   Label="Manesar delivery"),
    ]
    fig = go.Figure()
    for t in tasks:
        fig.add_trace(go.Bar(
            x=[t["Finish"] - t["Start"]],
            base=[t["Start"]],
            y=[t["Task"]],
            orientation="h",
            name=t["Label"],
            marker=dict(color=t["Color"], opacity=0.85, line=dict(width=1, color="rgba(255,255,255,0.13)")),
            text=t["Label"],
            textposition="inside",
            insidetextanchor="middle",
            hovertemplate=f"<b>{t['Task']}</b><br>Start: {t['Start']}h → End: {t['Finish']}h<extra></extra>",
        ))
    # Deadline line
    fig.add_vline(x=96, line=dict(color="#f87171", width=2, dash="dash"))
    fig.add_annotation(x=96, y=3.5, text="96h DEADLINE", showarrow=False,
                       font={"color": "#f87171", "size": 11}, xanchor="left")
    fig.update_layout(
        barmode="overlay",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(14,22,38,0.6)",
        font={"color": "#e7efff"}, height=260,
        xaxis=dict(title="Hours from Event", gridcolor="#1e3a5f", range=[0, 100]),
        yaxis=dict(autorange="reversed", gridcolor="#1e3a5f"),
        showlegend=False,
        margin=dict(l=10, r=10, t=20, b=30),
    )
    return fig


# ---------------------------------------------------------------------------
# FX sparkline
# ---------------------------------------------------------------------------

def fx_sparkline(values: list[float], label: str = "INR/USD") -> go.Figure:
    fig = go.Figure(go.Scatter(
        y=values,
        mode="lines+markers",
        line=dict(color="#44c5ff", width=2),
        marker=dict(size=4),
        fill="tozeroy",
        fillcolor="rgba(68,197,255,0.08)",
        hovertemplate=f"{label}: %{{y:.2f}}<extra></extra>",
    ))
    fig.update_layout(
        height=80, margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        showlegend=False,
    )
    return fig


# ---------------------------------------------------------------------------
# CO2 comparison bar
# ---------------------------------------------------------------------------

def co2_comparison_chart(sea: float, rail: float, road: float, air: float) -> go.Figure:
    modes = ["Sea", "Rail", "Road", "Air"]
    values = [sea, rail, road, air]
    colors = ["#44c5ff", "#fbbf24", "#4ade80", "#a78bfa"]
    fig = go.Figure(go.Bar(
        x=modes, y=values, marker_color=colors,
        text=[f"{v:.1f} t" for v in values], textposition="outside",
        hovertemplate="%{x}: %{y:.2f} tons CO₂<extra></extra>",
    ))
    fig.update_layout(
        height=220, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(14,22,38,0.6)",
        font={"color": "#e7efff"}, margin=dict(l=10, r=10, t=20, b=10),
        yaxis=dict(title="CO₂ (tons)", gridcolor="#1e3a5f"),
        xaxis=dict(gridcolor="#1e3a5f"),
        title={"text": "CO₂ Footprint by Mode", "font": {"size": 13}},
    )
    return fig
