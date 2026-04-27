# -*- coding: utf-8 -*-
"""Root launcher — delegates to logistiq/app.py.

Run with:
    python -m streamlit run run.py
"""
# This file exists so Streamlit can be launched from the repo root.
# All actual logic lives in logistiq/app.py.
import runpy, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
runpy.run_path(str(Path(__file__).parent / "logistiq" / "app.py"), run_name="__main__")
