# -*- coding: utf-8 -*-
"""All external API calls — weather, exchange rates, routing, live data."""
import math
import os
import time

import requests
import streamlit as st


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

CITY_COORDS: dict[str, tuple[float, float]] = {
    "chennai": (13.0827, 80.2707),
    "visakhapatnam": (17.6868, 83.2185),
    "vizag": (17.6868, 83.2185),
    "mumbai": (18.9388, 72.8354),
    "delhi": (28.6139, 77.2090),
    "pune": (18.5204, 73.8567),
    "kolkata": (22.5726, 88.3639),
    "hyderabad": (17.3850, 78.4867),
    "manesar": (28.3575, 76.9312),
    "secunderabad": (17.4399, 78.4983),
    "kamarajar": (13.2567, 80.3650),
    "ennore": (13.2567, 80.3650),
    "vijayawada": (16.5062, 80.6480),
    "nagpur": (21.1458, 79.0882),
}


def resolve_city_coords(location: str, default=(17.0, 81.0)) -> tuple[float, float]:
    loc = location.lower().strip()
    for k, v in CITY_COORDS.items():
        if k in loc:
            return v
    return default


def haversine_km(a: tuple, b: tuple) -> float:
    lat1, lon1, lat2, lon2 = *a, *b
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    val = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(val))


# ---------------------------------------------------------------------------
# Weather — timestamp-based 5-minute cache
# ---------------------------------------------------------------------------

_WEATHER_TTL = 300  # seconds


def get_real_weather(lat: float, lng: float, location_name: str = "") -> dict:
    cache_key = f"wx_{lat:.3f}_{lng:.3f}"
    now = time.time()
    cached = st.session_state.get("weather_cache", {}).get(cache_key)
    if cached and (now - cached.get("_ts", 0)) < _WEATHER_TTL:
        return cached

    key = os.getenv("WEATHER_API_KEY")
    base = "http://api.weatherapi.com/v1"
    result = {
        "location": location_name, "lat": lat, "lng": lng,
        "temp_c": None, "wind_kph": None, "condition": "Unknown",
        "is_dangerous": False, "wave_warning": False,
        "visibility_km": None, "precip_mm": None,
        "alerts": [], "fetched": False, "_ts": now,
    }
    try:
        r = requests.get(f"{base}/current.json",
                         params={"key": key, "q": f"{lat},{lng}", "aqi": "no"}, timeout=8)
        if r.ok:
            c = r.json().get("current", {})
            result.update({
                "temp_c": c.get("temp_c"),
                "wind_kph": c.get("wind_kph", 0),
                "condition": c.get("condition", {}).get("text", "Unknown"),
                "visibility_km": c.get("vis_km"),
                "precip_mm": c.get("precip_mm", 0),
                "is_dangerous": c.get("wind_kph", 0) > 60,
                "wave_warning": c.get("wind_kph", 0) > 45,
                "fetched": True,
            })
        r2 = requests.get(f"{base}/forecast.json",
                          params={"key": key, "q": f"{lat},{lng}", "days": 3, "alerts": "yes"}, timeout=8)
        if r2.ok:
            alerts = r2.json().get("alerts", {}).get("alert", [])
            result["alerts"] = [a.get("headline", "") for a in alerts] if isinstance(alerts, list) else []
    except Exception:  # noqa: BLE001
        pass

    if "weather_cache" not in st.session_state:
        st.session_state.weather_cache = {}
    st.session_state.weather_cache[cache_key] = result
    return result


# ---------------------------------------------------------------------------
# Exchange rate
# ---------------------------------------------------------------------------

def get_live_exchange_rate() -> float:
    now = time.time()
    cached_ts = st.session_state.get("_fx_ts", 0)
    if (now - cached_ts) < 600:  # 10-min cache
        return st.session_state.get("_fx_rate", 83.5)
    try:
        r = requests.get("https://open.er-api.com/v6/latest/USD", timeout=6)
        if r.ok:
            rate = r.json().get("rates", {}).get("INR", 83.5)
            st.session_state._fx_rate = rate
            st.session_state._fx_ts = now
            return rate
    except Exception:  # noqa: BLE001
        pass
    return st.session_state.get("_fx_rate", 83.5)


def get_fx_history_mock() -> list[float]:
    """7-day mock INR/USD trend for sparklines."""
    import random
    base = get_live_exchange_rate()
    trend = []
    for i in range(7):
        trend.append(round(base + random.uniform(-0.8, 0.8), 2))
    trend[-1] = base
    return trend


# ---------------------------------------------------------------------------
# Google Maps Routes API
# ---------------------------------------------------------------------------

def get_real_road_route(origin_name: str, dest_name: str) -> dict:
    key = os.getenv("MAPS_API_KEY")
    try:
        r = requests.post(
            "https://routes.googleapis.com/directions/v2:computeRoutes",
            headers={
                "Content-Type": "application/json",
                "X-Goog-Api-Key": key or "",
                "X-Goog-FieldMask": "routes.duration,routes.distanceMeters",
            },
            json={
                "origin": {"address": origin_name},
                "destination": {"address": dest_name},
                "travelMode": "DRIVE",
                "routingPreference": "TRAFFIC_AWARE",
            },
            timeout=10,
        )
        if r.ok:
            routes = r.json().get("routes", [])
            if routes:
                dist_m = routes[0].get("distanceMeters", 0)
                dur_s = int(routes[0].get("duration", "0s").replace("s", ""))
                return {
                    "distance_km": round(dist_m / 1000, 1),
                    "duration_hours": round(dur_s / 3600, 1),
                    "route_found": True,
                }
    except Exception:  # noqa: BLE001
        pass
    return {"distance_km": 0, "duration_hours": 0, "route_found": False}


# ---------------------------------------------------------------------------
# Fuel + CO2 calculations
# ---------------------------------------------------------------------------

BASE_FUEL_LITERS_PER_HOUR = 180.0   # vessel at 12kn
DIESEL_PRICE_INR = 92.0             # ₹/litre (IOCL approximate)
CO2_PER_LITRE = 2.68                # kg CO2 per litre diesel


def vessel_fuel_cost(speed_knots: float, voyage_hours: float) -> dict:
    """Cubic speed-fuel model."""
    fuel = BASE_FUEL_LITERS_PER_HOUR * (speed_knots / 12) ** 3 * voyage_hours
    cost_inr = fuel * DIESEL_PRICE_INR
    co2_tons = fuel * CO2_PER_LITRE / 1000
    return {"fuel_litres": round(fuel), "cost_inr": round(cost_inr), "co2_tons": round(co2_tons, 2)}


def cargo_insurance_cost(risk_score: int, value_crore: float, route_factor: float = 1.0) -> float:
    """₹ Lakh. Higher risk → higher premium."""
    base_rate = 0.0025  # 0.25% of cargo value
    risk_multiplier = 1 + (risk_score / 100) * 2.5
    return round(value_crore * base_rate * risk_multiplier * route_factor * 100, 2)  # in lakhs


def sla_breach_predictor(deadline_hours: float, current_eta_hours: float, penalty_per_hour_lakh: float = 10.0) -> dict:
    buffer = deadline_hours - current_eta_hours
    breach = buffer < 0
    penalty = round(abs(buffer) * penalty_per_hour_lakh, 2) if breach else 0
    probability = min(100, max(0, int((1 - buffer / max(deadline_hours, 1)) * 100))) if breach else max(0, int((1 - buffer / max(deadline_hours, 1)) * 100))
    return {
        "breach": breach,
        "buffer_hours": round(buffer, 1),
        "penalty_lakh": penalty,
        "breach_probability_pct": probability,
    }
