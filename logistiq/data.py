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
        "shipments":          [
            {
                "id": "SHP-90210",
                "cargo_type": "Auto Parts",
                "cargo_desc": "4,200 Engine Blocks for Maruti",
                "transport_mode": "Sea (Vessel)",
                "value_crore": 47.3,
                "weight_tons": 1120.0,
                "origin": "Chennai Port",
                "destination": "Manesar Plant",
                "departure_date": "2026-04-25",
                "deadline": "2026-05-02",
                "status": "In Transit",
                "risk_score": 78,
                "vessel_name": "MV Chennai Star",
                "vessel_draft": 15.2,
                "route_leg": "Sea -> Rail -> Road",
                "risk_factors": ["Cyclone Warning", "Port Congestion"]
            },
            {
                "id": "SHP-77412",
                "cargo_type": "Cold Chain",
                "cargo_desc": "Fresh Produce (Mangoes)",
                "transport_mode": "Road (Truck)",
                "value_crore": 2.1,
                "weight_tons": 18.5,
                "origin": "Visakhapatnam",
                "destination": "Hyderabad",
                "departure_date": "2026-04-27",
                "deadline": "2026-04-29",
                "status": "In Transit",
                "risk_score": 12,
                "truck_id": "TRK-AP-552",
                "temp_monitored": True,
                "risk_factors": []
            },
            {
                "id": "SHP-33219",
                "cargo_type": "Electronics",
                "cargo_desc": "High-end Server Racks",
                "transport_mode": "Air Cargo",
                "value_crore": 115.0,
                "weight_tons": 4.2,
                "origin": "Kamarajar Port (Air Wing)",
                "destination": "Gurugram Tech Park",
                "departure_date": "2026-04-28",
                "deadline": "2026-04-29",
                "status": "Awaiting Pickup",
                "risk_score": 5,
                "flight_id": "AI-902",
                "risk_factors": ["High Value"]
            },
            {
                "id": "SHP-11204",
                "cargo_type": "Raw Materials",
                "cargo_desc": "Steel Coils",
                "transport_mode": "Rail (Freight)",
                "value_crore": 12.8,
                "weight_tons": 450.0,
                "origin": "Vizag Steel Plant",
                "destination": "Chennai Industrial Zone",
                "departure_date": "2026-04-26",
                "deadline": "2026-04-30",
                "status": "In Transit",
                "risk_score": 45,
                "train_id": "SCR-58501",
                "wagons": 12,
                "risk_factors": ["Rail Blockage"]
            },
            {
                "id": "SHP-88591",
                "cargo_type": "Hazmat",
                "cargo_desc": "Industrial Chemicals (UN1263)",
                "transport_mode": "Sea (Vessel)",
                "value_crore": 8.4,
                "weight_tons": 85.0,
                "origin": "Singapore",
                "destination": "Chennai Port",
                "departure_date": "2026-04-20",
                "deadline": "2026-04-28",
                "status": "Critical",
                "risk_score": 92,
                "vessel_name": "Ever Zenith",
                "risk_factors": ["Extreme Weather", "Deadline Breach"]
            }
        ],
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
        "map_click": None,
        "selected_map_entity": None,
        "journey_stage": 0,
        "map_center": [15.0, 82.0],
        "firebase_queue": [],
        "firebase_sync_status": "ok",
        "gemini_status": "ok",
        "selected_shipment": None,
        "at_risk_banner_data": [],
        "banner_shipment_hash": None,
        "dismiss_risk_banner": False,
        "sim_t0": 0,
        "sim_step": 0,
        "sim_scenario_short": "🌀 Cyclone",
        "sim_reject_mode": False,
        "last_sim_savings": None,
        "gemma_mode": False,
        "relief_mode": False,
        "intel_digest": None,
        "intel_digest_ts": 0,
        "haas_demo_text": "",
        "haas_instr": "",
        "speed_val": 12,
        "cmd_result": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val
