# -*- coding: utf-8 -*-
"""Firebase REST operations — no Admin SDK dependency issues."""
import os
import requests


def _base() -> str:
    return os.getenv("FIREBASE_URL", "").rstrip("/")


def firebase_write(path: str, data: dict) -> bool:
    base = _base()
    if not base:
        return False
    try:
        r = requests.put(f"{base}{path}.json", json=data, timeout=10)
        return r.ok
    except Exception:  # noqa: BLE001
        return False


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
