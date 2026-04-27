# -*- coding: utf-8 -*-
"""Firebase operations — REST-based for reliability."""

import os
from datetime import datetime

import requests
import streamlit as st


def _base_url():
    return os.getenv("FIREBASE_URL", "").rstrip("/")

def firebase_write(path: str, data: dict) -> bool:
    """PUT data to Firebase Realtime DB with offline queue."""
    if "firebase_queue" not in st.session_state:
        st.session_state.firebase_queue = []
        
    try:
        base = _base_url()
        if not base:
            _queue_write(path, data)
            return False
        url = f"{base}{path}.json"
        response = requests.put(url, json=data, timeout=10)
        if response.ok:
            st.session_state.firebase_sync_status = "ok"
            return True
        _queue_write(path, data)
        return False
    except Exception:  # noqa: BLE001
        _queue_write(path, data)
        return False

def _queue_write(path: str, data: dict):
    if "firebase_queue" not in st.session_state:
        st.session_state.firebase_queue = []
    st.session_state.firebase_queue.append({
        "path": path,
        "data": data,
        "timestamp": datetime.now().isoformat(),
        "retry_count": 0
    })
    st.session_state.firebase_sync_status = "pending"

def firebase_flush_queue():
    if "firebase_queue" not in st.session_state or not st.session_state.firebase_queue:
        return
    
    base = _base_url()
    if not base:
        return
        
    remaining = []
    for item in st.session_state.firebase_queue:
        if item["retry_count"] > 5:
            continue
            
        try:
            r = requests.put(f"{base}{item['path']}.json", json=item["data"], timeout=10)
            if not r.ok:
                item["retry_count"] += 1
                remaining.append(item)
        except Exception:
            item["retry_count"] += 1
            remaining.append(item)
            
    st.session_state.firebase_queue = remaining
    if not remaining:
        st.session_state.firebase_sync_status = "ok"
    else:
        st.session_state.firebase_sync_status = "pending"



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
