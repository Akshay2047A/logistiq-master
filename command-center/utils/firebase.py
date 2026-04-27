# -*- coding: utf-8 -*-
"""Firebase operations — REST-based for reliability."""

import os
from datetime import datetime

import requests
import streamlit as st


def _base_url():
    return os.getenv("FIREBASE_URL", "").rstrip("/")


def firebase_write(path: str, data: dict) -> bool:
    """PUT data to Firebase Realtime DB."""
    try:
        base = _base_url()
        if not base:
            return False
        url = f"{base}{path}.json"
        response = requests.put(url, json=data, timeout=10)
        return response.ok
    except Exception:  # noqa: BLE001
        return False


def firebase_read(path: str):
    """GET data from Firebase Realtime DB."""
    try:
        base = _base_url()
        if not base:
            return {}
        url = f"{base}{path}.json"
        response = requests.get(url, timeout=8)
        if response.ok:
            return response.json() or {}
        return {}
    except Exception:  # noqa: BLE001
        return {}


def firebase_push(path: str, data: dict) -> bool:
    """POST (push) data to Firebase — auto-generates key."""
    try:
        base = _base_url()
        if not base:
            return False
        url = f"{base}{path}.json"
        response = requests.post(url, json=data, timeout=10)
        return response.ok
    except Exception:  # noqa: BLE001
        return False


def check_firebase_connection() -> bool:
    """Lightweight check if Firebase is reachable."""
    try:
        base = _base_url()
        if not base:
            return False
        response = requests.get(f"{base}/.json?shallow=true", timeout=5)
        return response.ok
    except Exception:  # noqa: BLE001
        return False
