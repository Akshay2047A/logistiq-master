# -*- coding: utf-8 -*-
"""All Gemini AI calls — single cached wrapper with demo-mode fallback."""
import json
import time
import os
import base64

import streamlit as st

try:
    import google.generativeai as genai
except Exception:  # noqa: BLE001
    genai = None


# ---------------------------------------------------------------------------
# Model initialisation (cached in session_state)
# ---------------------------------------------------------------------------

def get_gemini_model():
    if "gemini_model" in st.session_state and st.session_state.gemini_model is not None:
        return st.session_state.gemini_model
    if genai is None:
        return None
    try:
        genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))
        for name in ["gemini-1.5-pro-latest", "gemini-1.5-flash-latest", "gemini-pro"]:
            try:
                model = genai.GenerativeModel(name)
                st.session_state.gemini_model = model
                return model
            except Exception:  # noqa: BLE001
                continue
    except Exception:  # noqa: BLE001
        pass
    return None


# ---------------------------------------------------------------------------
# Core call wrapper
# ---------------------------------------------------------------------------

def cached_gemini_call(
    prompt_text: str,
    image_bytes: bytes | None = None,
    use_grounding: bool = False,
    response_mime_type: str | None = None,
    timeout_seconds: int = 30,
    demo_fallback=None,
):
    """Single entry point for all Gemini calls.

    Falls back to *demo_fallback* if demo_mode is on OR the API fails.
    """
    if st.session_state.get("demo_mode", False) and demo_fallback is not None:
        time.sleep(0.4)
        return demo_fallback

    model = get_gemini_model()
    if model is None:
        return demo_fallback

    try:
        tools = [{"google_search_retrieval": {}}] if use_grounding else None
        parts = [prompt_text]
        if image_bytes:
            parts.append(
                {
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": base64.b64encode(image_bytes).decode("utf-8"),
                    }
                }
            )
        gen_cfg = {"response_mime_type": response_mime_type} if response_mime_type else None
        response = model.generate_content(parts, tools=tools, generation_config=gen_cfg)
        text = getattr(response, "text", None)
        return text.strip() if text else demo_fallback
    except Exception:  # noqa: BLE001
        return demo_fallback


# ---------------------------------------------------------------------------
# JSON helpers
# ---------------------------------------------------------------------------

def parse_json_from_text(raw: str) -> dict | None:
    if not raw:
        return None
    try:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(raw[start:end])
    except Exception:  # noqa: BLE001
        pass
    return None


# ---------------------------------------------------------------------------
# Specific AI calls
# ---------------------------------------------------------------------------

def analyze_shipment_risk(shipment: dict, weather: dict, exchange_rate: float, live_intel: str) -> dict:
    from logistiq.data import demo_responses  # lazy import to avoid circular
    val_usd = round(float(shipment.get("value_crore", 0)) * 10_000_000 / exchange_rate, 0)
    prompt = f"""
You are a supply chain risk AI. Analyze this shipment against real current data.
Return ONLY valid JSON. No conversational text.

SHIPMENT DATA:
- Route: {shipment.get('origin', 'N/A')} to {shipment.get('destination', 'N/A')}
- Cargo: {shipment.get('cargo_desc', 'N/A')} ({shipment.get('weight_tons', 0)} tons)
- Value: ₹{shipment.get('value_crore', 0)} Cr (USD {val_usd})
- Mode: {shipment.get('transport_mode', 'N/A')}

REAL WEATHER AT DESTINATION:
- Wind: {weather.get('wind_kph', 'N/A')} kph
- Condition: {weather.get('condition', 'N/A')}
- Dangerous: {weather.get('is_dangerous', False)}
- Active alerts: {weather.get('alerts', [])}

LIVE INTELLIGENCE:
{live_intel}

Return ONLY this JSON structure:
{{
  "risk_score": 0,
  "risk_level": "Low/Medium/High/Critical",
  "primary_risk": "one sentence",
  "detected_issues": ["list", "of", "issues"],
  "weather_risk": "Low/Medium/High",
  "geopolitical_risk": "Low/Medium/High",
  "operational_risk": "Low/Medium/High",
  "estimated_delay_hours": 0,
  "financial_impact_inr": 0,
  "recommendation": "one clear action",
  "requires_immediate_action": false,
  "co2_tons": 0,
  "insurance_cost_lakh": 0,
  "sla_breach_probability": 0
}}
"""
    fallback = {
        "risk_score": 45, "risk_level": "Medium",
        "primary_risk": "Analysis unavailable — using fallback assessment",
        "detected_issues": ["Manual review recommended"],
        "weather_risk": "Medium", "geopolitical_risk": "Low",
        "operational_risk": "Medium", "estimated_delay_hours": 6,
        "financial_impact_inr": 500_000,
        "recommendation": "Monitor route conditions closely",
        "requires_immediate_action": False,
        "co2_tons": 12.5, "insurance_cost_lakh": 2.3, "sla_breach_probability": 25,
    }
    raw = cached_gemini_call(prompt, response_mime_type="application/json", demo_fallback=None)
    result = parse_json_from_text(raw or "") if raw else None
    return result or fallback


def get_ai_reroute(vessels, ports, rail, trucks, demo_responses) -> dict:
    demo = demo_responses.get("reroute", {})
    prompt = (
        "You are LogistiQ AI Supply Chain Coordinator. India multimodal logistics expert.\n"
        "RESPOND WITH VALID JSON ONLY. No markdown, no explanation.\n\n"
        "DISRUPTION: Category 3 Cyclone blocking Chennai Port.\n"
        "VESSEL: MV Chennai Star at 13.5N 83.2E, draft 15.2m, 4200 Maruti engine blocks,\n"
        "        value ₹47.3Cr, ETA was 48hrs to Chennai.\n"
        "TIDAL: Chennai draft limit 14.0m — vessel cannot dock regardless of cyclone.\n"
        f"PORTS: {json.dumps([p for p in ports], indent=2)}\n"
        f"RAIL: {json.dumps(rail, indent=2)}\n"
        f"TRUCKS: {json.dumps(trucks[:5], indent=2)}\n"
        "DEADLINE: Maruti Manesar must receive in 96hrs or line shuts (₹2.4Cr/day).\n\n"
        "Search current port and railway conditions via Google.\n\n"
        'Return JSON with keys: primary_recommendation, cascade(sea,rail,road,air), '
        'financial(exposure_without_action_crore,reroute_cost_delta_crore,assembly_line_risk_crore,net_savings_crore), '
        'time(original_eta_hours,new_eta_hours,days_saved), confidence, live_intel, geopolitical, social_impact, tidal'
    )
    raw = cached_gemini_call(prompt, use_grounding=True, demo_fallback=demo)
    if isinstance(raw, dict):
        return raw
    parsed = parse_json_from_text(raw or "")
    return parsed if parsed else demo


def process_captain_report(text: str, image_bytes=None, demo_responses=None) -> dict:
    demo = (demo_responses or {}).get("captain_report", {})
    prompt = (
        'Extract logistics data. Return ONLY valid JSON: '
        '{"reporter_type":"","asset_id":"","delay_hours":0,"cargo_status":"intact",'
        '"location":"","weather_conditions":"","urgency":"low","action_required":false,'
        '"recommended_action":"","notify":[],"summary":"","lat":null,"lon":null}\n'
        f"Report: {text}"
    )
    raw = cached_gemini_call(prompt, image_bytes=image_bytes, demo_fallback=demo)
    if isinstance(raw, dict):
        return raw
    parsed = parse_json_from_text(raw or "")
    return parsed if parsed else demo


def get_geopolitical_intel(demo_responses=None) -> dict:
    demo = (demo_responses or {}).get("geopolitical", {
        "red_sea": {"risk": "High", "detail": "Houthi attacks ongoing.", "vessels_affected": 120},
        "suez_canal": {"risk": "Medium", "detail": "Minor queueing.", "vessels_affected": 42},
        "malacca_strait": {"risk": "Low", "detail": "Normal operations.", "vessels_affected": 12},
        "bay_of_bengal": {"risk": "High", "detail": "Cyclone system active.", "cyclone_active": True},
        "strait_of_hormuz": {"risk": "Medium", "detail": "Elevated tension.", "vessels_affected": 55},
    })
    prompt = (
        "Search current conditions at maritime chokepoints and return JSON only:\n"
        '{"red_sea":{"risk":"Low/Medium/High/Critical","detail":"","vessels_affected":0},'
        '"suez_canal":{"risk":"","detail":"","vessels_affected":0},'
        '"malacca_strait":{"risk":"","detail":"","vessels_affected":0},'
        '"bay_of_bengal":{"risk":"","detail":"","cyclone_active":false},'
        '"strait_of_hormuz":{"risk":"","detail":"","vessels_affected":0}}'
    )
    raw = cached_gemini_call(prompt, use_grounding=True, demo_fallback=demo)
    if isinstance(raw, dict):
        return raw
    parsed = parse_json_from_text(raw or "")
    return parsed if parsed else demo


def get_live_intelligence(topic: str) -> str:
    prompt = (
        f"Search Google right now and report the CURRENT situation for:\n{topic}\n"
        "Be specific. Include actual port names, dates, numbers.\n"
        "Format as 2-3 sentences of actionable intelligence.\n"
        "If nothing significant, say 'No active disruptions detected as of today.'"
    )
    return cached_gemini_call(prompt, use_grounding=True,
                               demo_fallback="No active disruptions detected on this corridor today.") or ""


def get_ai_digest() -> str:
    from datetime import datetime
    now = datetime.now().strftime("%H:%M IST, %d %b %Y")
    prompt = (
        f"As of {now}, generate a logistics intelligence digest for the Chennai–Vizag–Manesar corridor.\n"
        "Cover: port conditions, any active disruptions, Red Sea situation, key train/vessel status.\n"
        "Format: 3-4 bullet points, each starting with an emoji. Be factual and current."
    )
    return cached_gemini_call(prompt, use_grounding=True,
                               demo_fallback=(
                                   "• No active disruptions on Chennai-Vizag corridor as of today.\n"
                                   "• Red Sea Houthi risk remains elevated — 23% diversion increase this week.\n"
                                   "• SCR Train 58501 confirmed on schedule per FOIS.\n"
                                   "• Next tidal window Chennai: 11 hrs."
                               )) or ""
