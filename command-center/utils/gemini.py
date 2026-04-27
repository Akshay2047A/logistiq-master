# -*- coding: utf-8 -*-
"""Gemini AI integration — cached model, demo fallback, structured JSON parsing."""

import base64
import json
import os
import time

import streamlit as st

try:
    import google.generativeai as genai
except Exception:  # noqa: BLE001
    genai = None


# ---------------------------------------------------------------------------
# Model management
# ---------------------------------------------------------------------------

def get_gemini_model():
    """Return a cached GenerativeModel instance, or None."""
    if genai is None:
        return None
    try:
        genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))
        for model_name in ["gemini-1.5-pro-latest", "gemini-1.5-flash-latest", "gemini-pro"]:
            try:
                return genai.GenerativeModel(model_name)
            except Exception:  # noqa: BLE001
                continue
    except Exception:  # noqa: BLE001
        return None
    return None


def _ensure_model():
    """Cache model in session state so we don't re-init every call."""
    if "gemini_model" not in st.session_state:
        st.session_state.gemini_model = get_gemini_model()
    return st.session_state.gemini_model


# ---------------------------------------------------------------------------
# Core call wrapper
# ---------------------------------------------------------------------------

def cached_gemini_call(
    prompt_text: str,
    image_bytes: bytes | None = None,
    use_grounding: bool = False,
    response_mime_type: str | None = None,
    timeout: int = 30,
    demo_fallback=None,
):
    """Single entry-point for all Gemini calls.

    • Uses session-state cached model
    • 30-second timeout (configurable)
    • Falls back to *demo_fallback* when demo mode is active or call fails
    """
    # Demo mode — return fallback immediately
    if st.session_state.get("demo_mode", False) and demo_fallback is not None:
        time.sleep(1.5)  # brief delay for realism
        return demo_fallback

    model = _ensure_model()
    if model is None:
        return demo_fallback

    try:
        tools = [{"google_search_retrieval": {}}] if use_grounding else None
        parts = [prompt_text]
        if image_bytes:
            parts.append({
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": base64.b64encode(image_bytes).decode("utf-8"),
                }
            })
        generation_config = {"response_mime_type": response_mime_type} if response_mime_type else None
        response = model.generate_content(
            parts,
            tools=tools,
            generation_config=generation_config,
            request_options={"timeout": timeout},
        )
        text = getattr(response, "text", None)
        return text.strip() if text else demo_fallback
    except Exception:  # noqa: BLE001
        return demo_fallback


# ---------------------------------------------------------------------------
# JSON extraction helpers
# ---------------------------------------------------------------------------

def parse_json_from_text(raw_text: str | None):
    """Extract the first JSON object from a free-text response."""
    if not raw_text:
        return None
    try:
        start = raw_text.find("{")
        end = raw_text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(raw_text[start : end + 1])
    except Exception:  # noqa: BLE001
        return None
    return None


# ---------------------------------------------------------------------------
# High-level AI functions
# ---------------------------------------------------------------------------

def get_live_intelligence(topic: str) -> str:
    """Use Gemini + Google Search grounding for live intelligence."""
    prompt = (
        f"Search Google right now and report the CURRENT situation for:\n{topic}\n"
        "Be specific. Include actual port names, dates, numbers, affected vessels if any.\n"
        "Format as 2-3 sentences of actionable intelligence.\n"
        "If nothing significant is happening, say 'No active disruptions detected as of today.'"
    )
    result = cached_gemini_call(
        prompt,
        use_grounding=True,
        demo_fallback="No active disruptions detected on Chennai-Vizag corridor. SCR Train 58501 confirmed on schedule. Weather clear at both ports.",
    )
    return result or "Intelligence unavailable — check network connection."


def get_ai_reroute(vessels, ports, rail, trucks, demo_responses):
    """Get a full cascade reroute recommendation from Gemini."""
    demo_fb = demo_responses.get("reroute", {})
    if st.session_state.get("demo_mode", False):
        time.sleep(2)
        return demo_fb

    prompt = (
        "You are LogistiQ AI Supply Chain Coordinator. India multimodal logistics expert.\n"
        "RESPOND WITH VALID JSON ONLY. No markdown, no explanation.\n\n"
        "DISRUPTION: Category 3 Cyclone blocking Chennai Port.\n"
        "VESSEL: MV Chennai Star at 13.5N 83.2E, draft 15.2m, 4200 Maruti engine blocks,\n"
        "        value ₹47.3Cr, ETA was 48hrs to Chennai.\n"
        "TIDAL: Chennai draft limit 14.0m — vessel cannot dock regardless of cyclone.\n"
        f"PORTS: {json.dumps(ports, indent=2)}\n"
        f"RAIL: {json.dumps(rail, indent=2)}\n"
        f"TRUCKS: {json.dumps(trucks[:5], indent=2)}\n"
        "DEADLINE: Maruti Manesar must receive in 96hrs or line shuts down (₹2.4Cr/day).\n\n"
        "Search current port and railway conditions via Google.\n\n"
        "Return JSON matching this schema exactly:\n"
        '{'
        '"primary_recommendation":"string",'
        '"cascade":{"sea":{"action":"","alt_port":"","reason":"","new_eta_hours":0},'
        '"rail":{"train_id":"","name":"","wagons_needed":0,"departure":"","full_eta":""},'
        '"road":{"trucks":[],"action":"","distance_km":0,"eta_hours":0},'
        '"air":{"needed":false,"reason":"","option":"","cost_lakh":0,"triggers_if":""}},'
        '"financial":{"exposure_without_action_crore":0,"reroute_cost_delta_crore":0,'
        '"assembly_line_risk_crore":0,"net_savings_crore":0},'
        '"time":{"original_eta_hours":48,"new_eta_hours":0,"days_saved":0},'
        '"confidence":0,"live_intel":"string","geopolitical":"string","social_impact":"string","tidal":"string"'
        "}"
    )

    result = cached_gemini_call(prompt, use_grounding=True, demo_fallback=None)
    if not result:
        return demo_fb
    parsed = parse_json_from_text(result)
    return parsed if parsed else demo_fb


def analyze_shipment_risk(shipment, weather_data, exchange_rate, live_intel):
    """Run AI risk analysis on a single shipment."""
    val_usd = round(float(shipment.get("value_crore", 0)) * 10_000_000 / exchange_rate, 0)
    prompt = f"""
You are a supply chain risk AI. Analyze this shipment against real current data.
Return ONLY valid JSON. No conversational text.

SHIPMENT DATA:
- Route: {shipment.get('origin', 'N/A')} to {shipment.get('destination', 'N/A')}
- Cargo: {shipment.get('cargo_desc', 'N/A')} ({shipment.get('weight_tons', 0)} tons)
- Value: ₹{shipment.get('value_crore', 0)} Cr (USD {val_usd})
- Mode: {shipment.get('transport_mode', 'N/A')}
- Full JSON: {json.dumps(shipment)}

REAL WEATHER AT DESTINATION RIGHT NOW:
- Wind: {weather_data.get('wind_kph', 'N/A')} kph
- Condition: {weather_data.get('condition', 'N/A')}
- Dangerous: {weather_data.get('is_dangerous', False)}
- Active alerts: {weather_data.get('alerts', [])}

LIVE INTELLIGENCE:
{live_intel}

SYSTEM INSTRUCTION: You must return ONLY a single valid JSON object containing exactly these keys, no markdown, no other text:
{{
  "risk_score": 0,
  "risk_level": "Low/Medium/High/Critical",
  "primary_risk": "one sentence",
  "detected_issues": ["list", "of", "detected", "issues"],
  "weather_risk": "Low/Medium/High",
  "geopolitical_risk": "Low/Medium/High",
  "operational_risk": "Low/Medium/High",
  "estimated_delay_hours": 0,
  "financial_impact_inr": 0,
  "recommendation": "one clear action",
  "requires_immediate_action": false
}}
"""
    fallback = {
        "risk_score": 45, "risk_level": "Medium",
        "primary_risk": "Analysis unavailable — using fallback assessment",
        "detected_issues": ["Weather data retrieved", "Manual review recommended"],
        "weather_risk": "Medium", "geopolitical_risk": "Low",
        "operational_risk": "Medium", "estimated_delay_hours": 6,
        "financial_impact_inr": 500000,
        "recommendation": "Monitor route conditions closely",
        "requires_immediate_action": False,
    }
    result = cached_gemini_call(prompt, response_mime_type="application/json", demo_fallback=json.dumps(fallback))
    try:
        text = result or ""
        start = text.find("{")
        end = text.rfind("}") + 1
        return json.loads(text[start:end])
    except Exception:  # noqa: BLE001
        return fallback


def process_captain_report(text, image_bytes=None, demo_responses=None):
    """Process a field report from captain/driver via Gemini."""
    demo_fb = (demo_responses or {}).get("captain_report", {})
    if st.session_state.get("demo_mode", False):
        time.sleep(1.5)
        return demo_fb

    prompt = (
        'Extract logistics data. Return ONLY valid JSON: '
        '{"reporter_type":"","asset_id":"","delay_hours":0,"cargo_status":"intact",'
        '"location":"","weather_conditions":"","urgency":"low","action_required":false,'
        '"recommended_action":"","notify":[],"summary":""}\n'
        f"Report: {text}"
    )
    result = cached_gemini_call(prompt, image_bytes=image_bytes, demo_fallback=None)
    parsed = parse_json_from_text(result or "")
    return parsed if parsed else demo_fb


def get_geopolitical_intel():
    """Fetch global chokepoint risk intel."""
    prompt = (
        "Search current conditions at these maritime chokepoints and return JSON only:\n"
        '{"red_sea":{"risk":"Low/Medium/High/Critical","detail":"","vessels_affected":0},'
        '"suez_canal":{"risk":"","detail":"","vessels_affected":0},'
        '"malacca_strait":{"risk":"","detail":"","vessels_affected":0},'
        '"strait_of_hormuz":{"risk":"","detail":"","vessels_affected":0},'
        '"bay_of_bengal":{"risk":"","detail":"","cyclone_active":false}}'
    )
    fallback = {
        "red_sea": {"risk": "High", "detail": "Shipping risk remains elevated due to Houthi attacks.", "vessels_affected": 120},
        "suez_canal": {"risk": "Medium", "detail": "Minor queueing reported. Average wait 6.2 hrs.", "vessels_affected": 42},
        "malacca_strait": {"risk": "Low", "detail": "Normal operations. No piracy incidents.", "vessels_affected": 12},
        "strait_of_hormuz": {"risk": "Medium", "detail": "Elevated tension, insurance premiums rising.", "vessels_affected": 35},
        "bay_of_bengal": {"risk": "High", "detail": "Cyclone system developing. IMD monitoring.", "cyclone_active": True},
    }
    result = cached_gemini_call(prompt, use_grounding=True, demo_fallback=json.dumps(fallback))
    parsed = parse_json_from_text(result or "")
    return parsed if parsed else fallback
