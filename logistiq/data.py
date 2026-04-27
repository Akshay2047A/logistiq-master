# -*- coding: utf-8 -*-
"""Central data loader — reads JSON files and initialises session state."""
import json
import os
from pathlib import Path

import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent  # repo root (c:\Users\omaks\logistiq)
DATA_DIR = BASE_DIR / "data"


def load_json(path: Path, default=None):
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:  # noqa: BLE001
        return default if default is not None else []


# Load static reference data once at module level
vessels_data        = load_json(DATA_DIR / "vessels.json", default=[])
ports_data          = load_json(DATA_DIR / "ports.json", default=[])
trucks_data         = load_json(DATA_DIR / "trucks.json", default=[])
rail_schedules_data = load_json(DATA_DIR / "rail_schedules.json", default=[])
demo_responses      = load_json(DATA_DIR / "demo_responses.json", default={})
# Safety guard — demo_responses must be a dict
if not isinstance(demo_responses, dict):
    demo_responses = {}


def init_session_state():
    defaults = {
        "cyclone_triggered":  False,
        "reroute_data":       None,
        "reroute_accepted":   False,
        "active_page":        "overview",
        "captain_reports":    [],
        "demo_mode":          False,
        "shipments":          [],
        "weather_cache":      {},
        "show_add_form":      False,
        "gemini_model":       None,
        "_fx_rate":           83.5,
        "_fx_ts":             0,
        "sim_running":        False,
        "sim_stage":          0,
        "sim_scenario":       "🌀 Cyclone — Bay of Bengal Cat.3",
        "alerts":             [
            {"severity": "High",   "message": "Cat.3 Cyclone forming in Bay of Bengal — Chennai corridor at risk",   "timestamp": "14:32 IST"},
            {"severity": "Medium", "message": "Visakhapatnam Port congestion HIGH — berth wait 4.5 hrs",            "timestamp": "13:15 IST"},
            {"severity": "Low",    "message": "SCR Train 77601 delayed 2.5 hrs — Rajdhani 12723 priority conflict", "timestamp": "11:40 IST"},
        ],
        "geopolitical_cache": None,
        "geopolitical_ts":    0,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val
