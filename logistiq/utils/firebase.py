# -*- coding: utf-8 -*-
"""Firebase REST operations — no Admin SDK dependency issues."""
import os
import requests
from datetime import datetime
import streamlit as st


def _base() -> str:
    return os.getenv("FIREBASE_URL", "").rstrip("/")


def firebase_write(path: str, data: dict) -> bool:
    if "firebase_queue" not in st.session_state:
        st.session_state.firebase_queue = []
        
    base = _base()
    if not base:
        _queue_write(path, data)
        return False
    try:
        r = requests.put(f"{base}{path}.json", json=data, timeout=10)
        if r.ok:
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
    
    base = _base()
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


def firebase_push(path: str, data: dict) -> str | None:
    """POST → Firebase auto-generates a key, returns it."""
    base = _base()
    if not base:
        return None
    try:
        r = requests.post(f"{base}{path}.json", json=data, timeout=10)
        if r.ok:
            return r.json().get("name")
    except Exception:  # noqa: BLE001
        pass
    return None


def firebase_read(path: str) -> dict | list:
    base = _base()
    if not base:
        return {}
    try:
        r = requests.get(f"{base}{path}.json", timeout=8)
        if r.ok:
            return r.json() or {}
    except Exception:  # noqa: BLE001
        pass
    return {}


def firebase_delete(path: str) -> bool:
    base = _base()
    if not base:
        return False
    try:
        r = requests.delete(f"{base}{path}.json", timeout=8)
        return r.ok
    except Exception:  # noqa: BLE001
        return False

def check_firebase_connection() -> bool:
    """Lightweight check if Firebase is reachable."""
    base = _base()
    if not base:
        return False
    try:
        r = requests.get(f"{base}/.json?shallow=true", timeout=5)
        return r.ok
    except Exception:  # noqa: BLE001
        return False
