# -*- coding: utf-8 -*-
import sys
from pathlib import Path
import os
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent / "command-center"))
import app
from app import get_gemini_model, call_gemini

load_dotenv("command-center/.env")

try:
    print("Testing call_gemini...")
    res = call_gemini("return JSON: {\"test\": 123}", response_mime_type="application/json")
    print("Result:", res)
except Exception as e:
    import traceback
    traceback.print_exc()
