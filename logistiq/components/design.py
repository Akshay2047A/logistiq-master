# -*- coding: utf-8 -*-
"""Global CSS design system — call apply_design_system() once in app.py."""
import streamlit as st


def apply_design_system():
    st.markdown("""
<style>
/* ── Google Fonts ───────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── CSS Tokens ─────────────────────────────────────── */
:root {
  --color-primary:  #FF6B35;
  --color-sea:      #44c5ff;
  --color-rail:     #fbbf24;
  --color-road:     #4ade80;
  --color-air:      #a78bfa;
  --color-critical: #f87171;
  --color-warning:  #fbbf24;
  --color-safe:     #4ade80;
  --color-neutral:  #60a5fa;
  --bg-card:        rgba(255,255,255,0.04);
  --border-card:    rgba(96,165,250,0.18);
  --bg-page:        radial-gradient(ellipse at top right, #18263e 0%, #0c1628 40%, #070d18 100%);
}

/* ── Global ─────────────────────────────────────────── */
html, body { font-family:'Inter',sans-serif !important; }
.stApp { background: var(--bg-page); color:#e7efff; }
.block-container { padding: 0 20px 60px !important; max-width:100% !important; }
/* Hide the Streamlit top header bar that creates the white gap */
header[data-testid="stHeader"] { display:none !important; }
[data-testid="stDecoration"] { display:none !important; }
h1 { font-size:24px !important; font-weight:800 !important; color:#fff !important; margin:0 !important; }
h2 { font-size:20px !important; font-weight:700 !important; color:#fff !important; margin:0 0 4px !important; }
h3 { font-size:16px !important; font-weight:700 !important; color:#e7efff !important; margin:0 0 4px !important; }
h4,h5,h6 { color:#e7efff !important; margin:0 !important; }

/* ── Section header ──────────────────────────────────── */
.section-header {
  font-size: 12px; font-weight: 600; color: #64748b;
  text-transform: uppercase; letter-spacing: 1px;
  margin: 4px 0 8px; padding-bottom: 6px;
  border-bottom: 1px solid rgba(96,165,250,0.1);
}

/* hide Streamlit chrome */
#MainMenu { visibility:hidden; }
footer { visibility:hidden; }
.stDeployButton { display:none; }
[data-testid="stToolbar"] { display:none; }

/* ── Sidebar ─────────────────────────────────────────── */
[data-testid="stSidebar"] {
  background: rgba(5,10,20,0.98) !important;
  border-right: 1px solid rgba(96,165,250,0.1) !important;
}
[data-testid="stSidebar"] .stButton>button {
  background: rgba(255,255,255,0.03) !important;
  border: 1px solid rgba(96,165,250,0.12) !important;
  color: #94a3b8 !important; font-size:13px !important;
  font-family:'Inter',sans-serif !important;
  text-align:left !important;
}
[data-testid="stSidebar"] .stButton>button:hover {
  background: rgba(255,107,53,0.08) !important;
  border-color: rgba(255,107,53,0.3) !important;
  color: #FF6B35 !important;
}
[data-testid="stSidebar"] .stButton>button[kind="primary"] {
  background: rgba(255,107,53,0.15) !important;
  border-color: rgba(255,107,53,0.4) !important;
  color: #FF6B35 !important;
}

/* ── Glass card ─────────────────────────────────────── */
.glass-card {
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  border-radius: 12px; padding: 16px; margin: 6px 0;
  backdrop-filter: blur(8px);
  transition: border-color 0.2s, transform 0.15s, box-shadow 0.2s;
}
.glass-card:hover {
  border-color: rgba(96,165,250,0.4);
  transform: translateY(-1px);
  box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}

/* ── Metric cards ─────────────────────────────────────── */
.metric-card {
  background: linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
  border: 1px solid var(--border-card);
  border-radius: 12px; padding: 14px 10px; text-align: center;
  transition: transform 0.2s, box-shadow 0.2s;
}
.metric-card:hover { transform: translateY(-2px); box-shadow:0 6px 20px rgba(0,0,0,0.4); }
.metric-icon  { font-size: 22px; margin-bottom: 4px; }
.metric-label { font-size: 10px; color: #475569; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }
.metric-value { font-size: 20px; font-weight: 800; color: #fff; margin: 4px 0 2px; line-height:1.1; }
.metric-delta { font-size: 10px; font-weight: 500; }

/* ── Badges ─────────────────────────────────────────── */
.badge {
  display: inline-block; padding: 2px 8px; border-radius: 20px;
  font-size: 9px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.6px;
  white-space: nowrap;
}
.badge-critical { background:#3d0a0a; color:#f87171; border:1px solid rgba(248,113,113,0.25); }
.badge-high     { background:#2d1400; color:#fb923c; border:1px solid rgba(251,146,60,0.25); }
.badge-medium   { background:#2d2200; color:#fbbf24; border:1px solid rgba(251,191,36,0.25); }
.badge-low, .badge-safe { background:#0a2d1a; color:#4ade80; border:1px solid rgba(74,222,128,0.25); }
.badge-neutral  { background:#0a1e3d; color:#60a5fa; border:1px solid rgba(96,165,250,0.25); }

/* ── Shipment list card ──────────────────────────────── */
.shipment-list-card {
  display: flex; align-items: center; gap:10px;
  padding: 9px 10px; border-radius: 8px; margin: 3px 0;
  background: rgba(255,255,255,0.02); cursor:pointer;
  transition: background 0.2s;
}
.shipment-list-card:hover { background: rgba(255,107,53,0.06); }
.card-title { font-size: 11px; font-weight: 600; color: #e7efff; }
.card-sub   { font-size: 10px; color: #475569; }

/* ── Alert card ─────────────────────────────────────── */
.alert-card {
  display:flex; align-items:flex-start; gap:10px;
  padding:10px 12px; border-radius:10px; margin:4px 0;
  background:rgba(248,113,113,0.04); border:1px solid rgba(248,113,113,0.12);
  transition: background 0.2s;
}
.alert-card:hover { background:rgba(248,113,113,0.08); }
.alert-msg { font-size:12px; color:#e7efff; line-height:1.4; }

/* ── Port weather card ───────────────────────────────── */
.port-weather-card {
  background: var(--bg-card); border:1px solid var(--border-card);
  border-radius:12px; padding:14px; margin:6px 0;
}
.port-weather-header { font-size:13px; font-weight:700; margin-bottom:8px; display:flex; align-items:center; gap:8px; color:#e7efff; }
.port-weather-body   { font-size:12px; color:#94a3b8; line-height:1.6; }

/* ── CMD card ────────────────────────────────────────── */
.cmd-card { background:rgba(10,18,35,0.9); border:1.5px solid var(--color-primary); border-radius:14px; padding:18px; margin:10px 0; }
.cmd-card-header { background:var(--color-primary); color:white; font-weight:700; font-size:13px; padding:8px 14px; border-radius:8px; margin-bottom:12px; display:flex; align-items:center; gap:8px; }
.cascade-step { border-left:3px solid var(--color-road); padding:8px 12px; margin:5px 0; border-radius:0 8px 8px 0; background:rgba(74,222,128,0.06); font-size:13px; color:#94a3b8; }
.cascade-step-air { border-left-color:var(--color-air); background:rgba(167,139,250,0.06); }
.intel-box { background:rgba(59,130,246,0.07); border:1px solid rgba(59,130,246,0.18); border-radius:8px; padding:10px; font-style:italic; font-size:12px; margin-top:6px; color:#94a3b8; line-height:1.5; }
.social-box { background:rgba(74,222,128,0.06); border:1px solid rgba(74,222,128,0.18); border-radius:8px; padding:10px; font-size:12px; color:#94a3b8; }

/* ── Ticker ─────────────────────────────────────────── */
.ticker-wrap { overflow:hidden; background:linear-gradient(90deg,#FF6B35,#ff8c5a); padding:7px 0; border-radius:8px; margin-bottom:10px; }
.ticker-move { display:inline-block; white-space:nowrap; animation:ticker 35s linear infinite; }
@keyframes ticker { from{transform:translateX(100vw)} to{transform:translateX(-100%)} }
.ticker-move span { color:rgba(255,255,255,0.95); font-size:12px; font-weight:500; padding:0 48px; }

/* ── Skeleton ────────────────────────────────────────── */
.skeleton {
  background: linear-gradient(90deg, rgba(255,255,255,0.03) 25%, rgba(255,255,255,0.07) 50%, rgba(255,255,255,0.03) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 10px;
}
@keyframes shimmer { 0%{background-position:200% 0} 100%{background-position:-200% 0} }

/* ── Empty state ─────────────────────────────────────── */
.empty-state { text-align:center; padding:32px 20px; }
.empty-title { font-size:15px; font-weight:600; color:#94a3b8; margin:10px 0 4px; }
.empty-sub   { font-size:12px; color:#475569; }

/* ── Simulation ──────────────────────────────────────── */
.sim-event { background:rgba(248,113,113,0.07); border:1px solid rgba(248,113,113,0.2); border-radius:10px; padding:14px; margin:8px 0; }
.sim-step  { display:flex; align-items:flex-start; gap:10px; padding:7px 0; font-size:13px; color:#94a3b8; border-bottom:1px solid rgba(255,255,255,0.04); }
.sim-step:last-child { border-bottom:none; }
.step-check { font-size:17px; flex-shrink:0; }

/* ── Scrollbar ───────────────────────────────────────── */
::-webkit-scrollbar { width:4px; height:4px; }
::-webkit-scrollbar-track { background:transparent; }
::-webkit-scrollbar-thumb { background:rgba(96,165,250,0.2); border-radius:2px; }

/* ── Field report ────────────────────────────────────── */
.report-card { background:var(--bg-card); border:1px solid var(--border-card); border-radius:12px; padding:14px; margin:6px 0; transition:border-color 0.2s; }
.report-card:hover { border-color:rgba(96,165,250,0.35); }
.report-header { display:flex; align-items:center; gap:10px; margin-bottom:8px; }

/* ── Tidal bars ─────────────────────────────────────── */
.tidal-bar { margin:10px 0; }
.tidal-label { font-size:12px; color:#94a3b8; margin-bottom:5px; display:flex; justify-content:space-between; }
.tidal-track { background:#0f172a; border-radius:6px; height:18px; position:relative; overflow:hidden; }
.tidal-fill  { height:18px; border-radius:6px; }

/* ── Status bar ──────────────────────────────────────── */
.status-bar {
  position:fixed; bottom:0; left:0; right:0; z-index:998;
  background:rgba(5,10,20,0.97); border-top:1px solid rgba(96,165,250,0.08);
  padding:5px 20px 5px 280px; display:flex; align-items:center; gap:14px;
  font-size:11px; color:#475569; backdrop-filter:blur(12px);
}
.status-divider { color:#1e293b; }
.status-dot { width:6px; height:6px; border-radius:50%; display:inline-block; margin-right:4px; vertical-align:middle; }
.dot-green  { background:#4ade80; box-shadow:0 0 5px #4ade8088; }
.dot-red    { background:#f87171; box-shadow:0 0 5px #f8717188; }
.dot-amber  { background:#fbbf24; box-shadow:0 0 5px #fbbf2488; }

/* ── Pulse ───────────────────────────────────────────── */
@keyframes pulse { 0%{opacity:1} 50%{opacity:0.4} 100%{opacity:1} }

/* ── Streamlit widget overrides ──────────────────────── */
.stButton>button {
  background: rgba(255,107,53,0.1) !important;
  border: 1px solid rgba(255,107,53,0.3) !important;
  color: #FF6B35 !important; border-radius: 8px !important;
  font-weight: 600 !important; font-size:13px !important;
  font-family:'Inter',sans-serif !important;
  transition: all 0.18s !important;
}
.stButton>button:hover {
  background: rgba(255,107,53,0.2) !important;
  border-color: #FF6B35 !important;
  box-shadow: 0 0 10px rgba(255,107,53,0.18) !important;
}
.stButton>button[kind="primary"] {
  background: linear-gradient(135deg,#FF6B35,#ff8c5a) !important;
  color: #fff !important; border-color: #FF6B35 !important;
  box-shadow: 0 2px 10px rgba(255,107,53,0.3) !important;
}
.stButton>button[kind="primary"]:hover {
  box-shadow: 0 4px 18px rgba(255,107,53,0.45) !important;
}
.stSelectbox label, .stTextInput label, .stNumberInput label,
.stTextArea label, .stMultiSelect label, .stSlider label,
.stDateInput label, .stFileUploader label {
  color: #94a3b8 !important; font-size:12px !important; font-weight:500 !important;
}
.stSelectbox>div>div, .stTextInput>div>div>input,
.stNumberInput>div>div>input, .stTextArea>div>div>textarea {
  background: rgba(255,255,255,0.04) !important;
  border: 1px solid rgba(96,165,250,0.18) !important;
  color: #e7efff !important; border-radius: 8px !important;
  font-family:'Inter',sans-serif !important;
}
.stExpander { border: 1px solid var(--border-card) !important; border-radius: 10px !important; overflow:hidden; }
.stExpander summary { background:rgba(255,255,255,0.02) !important; }
.stTabs [data-baseweb="tab-list"] {
  background: rgba(255,255,255,0.02) !important; gap: 2px;
  border-radius:10px; padding:3px; border:1px solid var(--border-card);
}
.stTabs [data-baseweb="tab"] {
  background: transparent !important; border-radius: 7px !important;
  color: #64748b !important; font-size: 12px !important; font-weight:500 !important;
  padding: 6px 14px !important;
}
.stTabs [aria-selected="true"] {
  background: rgba(255,107,53,0.15) !important; color: #FF6B35 !important;
}
div[data-testid="stMetric"] {
  background: var(--bg-card); border:1px solid var(--border-card);
  border-radius:10px; padding:12px 14px;
}
div[data-testid="stMetricValue"] { color:#fff !important; font-weight:700 !important; }
div[data-testid="stMetricLabel"] { color:#64748b !important; font-size:10px !important; text-transform:uppercase; letter-spacing:0.6px; }
</style>
""", unsafe_allow_html=True)
