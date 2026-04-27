# -*- coding: utf-8 -*-
"""External data APIs — weather, exchange rates, road routes."""

import os
import time
from datetime import datetime

import requests
import streamlit as st


# ---------------------------------------------------------------------------
# Weather (WeatherAPI.com)
# ---------------------------------------------------------------------------

def _weather_cache_key(lat, lng):
    return f"weather_{lat:.2f}_{lng:.2f}"


def get_real_weather(lat, lng, location_name=""):
    """Fetch weather from WeatherAPI.com with 5-minute session-state cache."""
    cache_key = _weather_cache_key(lat, lng)
    cached = st.session_state.get("weather_cache", {}).get(cache_key)
    if cached:
        cached_ts = cached.get("_cached_at", 0)
        if time.time() - cached_ts < 300:  # 5-minute expiry
            return cached

    key = os.getenv("WEATHER_API_KEY")
    base = "http://api.weatherapi.com/v1"
    result = {
        "location": location_name,
        "lat": lat, "lng": lng,
        "temp_c": None,
        "wind_kph": None,
        "condition": "Unknown",
        "is_dangerous": False,
        "wave_warning": False,
        "visibility_km": None,
        "precip_mm": None,
        "humidity": None,
        "alerts": [],
        "fetched": False,
    }
    try:
        r = requests.get(
            f"{base}/current.json",
            params={"key": key, "q": f"{lat},{lng}", "aqi": "no"},
            timeout=8,
        )
        if r.ok:
            d = r.json()
            c = d.get("current", {})
            result.update({
                "temp_c": c.get("temp_c"),
                "wind_kph": c.get("wind_kph", 0),
                "condition": c.get("condition", {}).get("text", "Unknown"),
                "visibility_km": c.get("vis_km"),
                "precip_mm": c.get("precip_mm", 0),
                "humidity": c.get("humidity"),
                "is_dangerous": c.get("wind_kph", 0) > 60,
                "wave_warning": c.get("wind_kph", 0) > 45,
                "fetched": True,
            })
        r2 = requests.get(
            f"{base}/forecast.json",
            params={"key": key, "q": f"{lat},{lng}", "days": 3, "alerts": "yes"},
            timeout=8,
        )
        if r2.ok:
            alerts = r2.json().get("alerts", {}).get("alert", [])
            result["alerts"] = [a.get("headline", "") for a in alerts] if isinstance(alerts, list) else []
    except Exception:  # noqa: BLE001
        pass

    # Cache result
    result["_cached_at"] = time.time()
    if "weather_cache" not in st.session_state:
        st.session_state.weather_cache = {}
    st.session_state.weather_cache[cache_key] = result
    return result


# ---------------------------------------------------------------------------
# Exchange rates
# ---------------------------------------------------------------------------

def get_live_exchange_rate():
    """Fetch USD→INR (and others) from open.er-api.com."""
    cached = st.session_state.get("exchange_rate_cache")
    if cached and time.time() - cached.get("_ts", 0) < 600:
        return cached

    try:
        r = requests.get("https://open.er-api.com/v6/latest/USD", timeout=6)
        if r.ok:
            rates = r.json().get("rates", {})
            data = {
                "USD_INR": rates.get("INR", 83.5),
                "EUR_INR": rates.get("INR", 83.5) / rates.get("EUR", 0.93) if rates.get("EUR") else 90.0,
                "USD_CNY": rates.get("CNY", 7.24),
                "_ts": time.time(),
            }
            st.session_state.exchange_rate_cache = data
            return data
    except Exception:  # noqa: BLE001
        pass
    return {"USD_INR": 83.5, "EUR_INR": 90.0, "USD_CNY": 7.24, "_ts": 0}


def get_inr_rate():
    """Simple convenience: returns just the USD→INR number."""
    return get_live_exchange_rate().get("USD_INR", 83.5)


# ---------------------------------------------------------------------------
# Road routes (Google Maps Routes API)
# ---------------------------------------------------------------------------

def get_real_road_route(origin_name, dest_name):
    """Compute driving route via Google Maps Routes API v2."""
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
# City coordinates lookup (India)
# ---------------------------------------------------------------------------

CITY_COORDS = {
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
    "vijayawada": (16.5062, 80.6480),
    "nellore": (14.4426, 79.9865),
    "bengaluru": (12.9716, 77.5946),
    "bangalore": (12.9716, 77.5946),
    "sriperumbudur": (12.9625, 79.9425),
    "oragadam": (12.8185, 79.9671),
}


def lookup_city_coords(city_text):
    """Return (lat, lng) for a known Indian city, or a default."""
    lower = city_text.lower().strip()
    for name, coords in CITY_COORDS.items():
        if name in lower:
            return coords
    return (17.0, 81.0)  # default: central-ish AP/Telangana
