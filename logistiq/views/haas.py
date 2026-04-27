# -*- coding: utf-8 -*-
"""Human-as-a-Service (HaaS) — Captain's Portal."""
import streamlit as st
import time
import os
import requests
from datetime import datetime

from logistiq.data import demo_responses
from logistiq.components import cards as K
from logistiq.utils.gemini import process_captain_report
from logistiq.utils.firebase import firebase_read, firebase_push, firebase_write

REPORTER_ICONS = {
    "Ship Captain": "🚢",
    "Driver":       "🚛",
    "Ground Staff": "👷",
    "Train POC":    "🚂",
    "Port Officer": "⚓",
}

def render():
    st.markdown("### 📞 Human-as-a-Service Intelligence Portal")
    st.caption("Field reports from captains, drivers, and ground staff → AI extracts structure → Command center acts")

    # Stats row
    reports = st.session_state.get("captain_reports", [])
    count = len(reports)
    highest = "Low"
    for r in reports:
        if r.get("urgency", "").lower() == "high": highest = "High"
        elif r.get("urgency", "").lower() == "medium" and highest != "High": highest = "Medium"
        
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Reports Today", str(count))
    s2.metric("Avg Response Time", "2.3s")
    s3.metric("Urgency", highest)
    s4.metric("Firebase", "Connected ✅")

    st.markdown("---")

    col1, col2, col3 = st.columns([1.2, 1.2, 1])

    # ── COLUMN 1: Command Center view ──────────────────────
    with col1:
        st.markdown("#### 📥 Live Field Reports")
        
        # Refresh logic
        if st.button("🔄 Refresh", key="haas_refresh"):
            st.rerun()

        # Fetch from Firebase
        raw_reports = firebase_read("/field_reports") or {}
        reports_list = []
        if isinstance(raw_reports, dict):
            for k, v in raw_reports.items():
                if isinstance(v, dict):
                    v["_key"] = k
                    reports_list.append(v)
        # Include session-state reports too
        for r in st.session_state.captain_reports:
            if not any(x.get("_key") == r.get("_key") for x in reports_list):
                reports_list.append(r)
        reports_list.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        if not reports_list:
            K.empty_state("📡", "No field reports yet", "Submit a report below or wait for field personnel to sync.")
        else:
            for i, rep in enumerate(reports_list[:5]):
                urg = rep.get("urgency", "low")
                sev_color = "#f87171" if urg == "high" else "#fbbf24" if urg == "medium" else "#4ade80"
                icon = REPORTER_ICONS.get(rep.get("reporter_type", ""), "📋")
                resolved = rep.get("resolved", False)
                st.markdown(f"""
<div class='report-card' style='opacity:{"0.5" if resolved else "1"}'>
  <div class='report-header'>
    <span style='font-size:22px'>{icon}</span>
    <div style='flex:1'>
      <b style='font-size:13px'>{rep.get('asset_id','Unknown')}</b>
      &nbsp;<span class='badge' style='background:rgba(0,0,0,0.4);color:{sev_color};border:1px solid {sev_color}55'>{urg.upper()}</span>
      {"<span class='badge badge-safe' style='margin-left:4px'>RESOLVED</span>" if resolved else ""}
    </div>
    <span style='font-size:11px;color:#64748b'>{rep.get("timestamp", "2 mins ago")}</span>
  </div>
  <div style='font-size:12px;color:#e7efff;margin:4px 0'>{rep.get("summary", "")}</div>
  <div style='display:grid;grid-template-columns:1fr 1fr;gap:6px;font-size:11px;color:#94a3b8;margin-top:8px'>
    <div>📍 {rep.get("location", "N/A")}</div>
    <div>⏱ Delay: {rep.get("delay_hours", 0)} hrs</div>
    <div style='grid-column:span 2'>📦 Cargo: {rep.get("cargo_status", "N/A")}</div>
  </div>
</div>""", unsafe_allow_html=True)
                if not resolved:
                    if st.button("✅ Mark Resolved", key=f"resolve_{i}", use_container_width=True):
                        # In real app: write resolved:true to Firebase
                        rep["resolved"] = True
                        st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### 📤 Send Instruction to Field")
        asset_options = list({r.get("asset_id", "") for r in reports_list if r.get("asset_id")})
        if not asset_options: asset_options = ["MV Chennai Star", "TRK-CHN-101", "Train 58501"]
        selected_asset = st.selectbox("Select asset", asset_options, key="haas_asset", label_visibility="collapsed")
        
        # Quick fills
        qf1, qf2, qf3 = st.columns(3)
        if qf1.button("Divert Vizag", use_container_width=True): st.session_state.haas_instr = "Divert to Vizag"
        if qf2.button("Hold position", use_container_width=True): st.session_state.haas_instr = "Hold position"
        if qf3.button("Proceed 7B", use_container_width=True): st.session_state.haas_instr = "Proceed to berth 7B"
        
        instruction = st.text_area("Instruction", value=st.session_state.get("haas_instr", ""), placeholder="e.g. Divert to Vizag Port...", key="haas_instruction", label_visibility="collapsed")
        
        if st.button("📲 Send to Field App", use_container_width=True, type="primary"):
            firebase_write(f"/active_reroutes/{selected_asset.replace(' ','_')}", {
                "instruction": instruction,
                "status": "sent",
                "timestamp": datetime.now().isoformat(),
                "ack": False,
            })
            st.success("✅ Instruction transmitted — waiting for acknowledgment")

    # ── COLUMN 2: Flutter app mockup ──────────────────────
    with col2:
        st.markdown("<div style='text-align:center;font-weight:700;margin-bottom:12px'>📱 Flutter Field App</div>", unsafe_allow_html=True)
        
        # Phone Mockup HTML
        if st.session_state.reroute_accepted:
            screen_html = """
<div class='phone-header'>
  <div style='font-size:14px;font-weight:700;color:white'>LogistiQ Field</div>
  <div style='font-size:10px;color:rgba(255,255,255,0.8)'>🚢 MV Chennai Star</div>
</div>
<div style='background:#f87171;color:white;padding:8px;text-align:center;font-size:11px;font-weight:700;animation:pulse 1s infinite'>
  ⚠ NEW ORDERS — Tap to view
</div>
<div class='phone-section' style='background:rgba(255,255,255,0.05);margin:10px;border-radius:10px'>
  <div style='font-size:10px;color:#94a3b8'>INSTRUCTION</div>
  <div style='font-size:12px;color:white;font-weight:600;margin-top:4px'>Divert to Visakhapatnam Port. Transfer to SCR 58501. Acknowledge.</div>
</div>
<div style='background:#4ade80;color:#052e16;border-radius:10px;padding:12px;text-align:center;font-size:13px;font-weight:800;margin:20px 10px'>
  ✅ ACKNOWLEDGE
</div>"""
        elif st.session_state.cyclone_triggered:
            screen_html = """
<div class='phone-header'>
  <div style='font-size:14px;font-weight:700;color:white'>LogistiQ Field</div>
  <div style='font-size:10px;color:rgba(255,255,255,0.8)'>🚢 MV Chennai Star</div>
</div>
<div style='background:#fbbf24;color:#451a03;padding:8px;text-align:center;font-size:11px;font-weight:700'>
  ⚠ Weather Advisory
</div>
<div class='phone-section' style='background:rgba(255,255,255,0.05);margin:10px;border-radius:10px'>
  <div style='font-size:10px;color:#94a3b8'>CURRENT WEATHER</div>
  <div style='font-size:16px;color:white;font-weight:700'>Cyclone Cat.3</div>
  <div style='font-size:11px;color:#94a3b8;margin-top:4px'>Winds >180kph reported nearby. Provide immediate status update.</div>
</div>
<div class='phone-btn' style='background:#f87171;border:2px solid #fff'>🚨 Submit Urgent Report</div>"""
        else:
            screen_html = """
<div class='phone-header'>
  <div style='font-size:14px;font-weight:700;color:white'>LogistiQ Field</div>
  <div style='font-size:10px;color:rgba(255,255,255,0.8)'>🚢 MV Chennai Star — Capt. Rajesh</div>
</div>
<div class='phone-section'>
  <div style='font-size:11px;color:#4ade80;font-weight:700;margin-bottom:6px'>🟢 ALL CLEAR</div>
  <div style='background:rgba(255,255,255,0.05);border-radius:8px;padding:10px'>
    <div style='font-size:10px;color:#64748b'>CURRENT ASSIGNMENT</div>
    <div style='font-size:12px;font-weight:600;color:#e7efff'>4,200 Engine Blocks → Manesar</div>
  </div>
</div>
<div style='display:flex;gap:10px;padding:10px'>
  <div style='flex:1;background:rgba(255,255,255,0.05);border-radius:8px;padding:10px;text-align:center;font-size:10px'>📸 Upload<br>Docs</div>
  <div style='flex:1;background:rgba(255,255,255,0.05);border-radius:8px;padding:10px;text-align:center;font-size:10px'>💬 Chat<br>Command</div>
</div>
<div class='phone-btn'>📋 Routine Report</div>"""

        st.markdown(f"""
<div class='phone-frame'>
  <div class='phone-notch'></div>
  <div class='phone-screen'>
    <div style='display:flex;justify-content:space-between;font-size:10px;color:#94a3b8;padding:4px 8px;background:#0a1628'>
      <span>9:41 AM</span><span>🛜 5G 🔋</span>
    </div>
    {screen_html}
  </div>
</div>""", unsafe_allow_html=True)
        
        st.markdown("""
<div style='text-align:center;margin-top:16px'>
  <div style='font-size:11px;color:#4ade80;margin-bottom:4px'>🌐 Real-time sync via Firebase</div>
  <div style='font-size:11px;color:#94a3b8;margin-bottom:8px'>🌍 Multilingual support: EN | हिन्दी | తెలుగు | தமிழ்</div>
  <div style='font-size:10px;background:rgba(255,255,255,0.05);padding:8px;border-radius:8px;text-align:left;line-height:1.4'>
    <b>Demo:</b> "Divert to Vizag Port"<br>
    <span style='color:#60a5fa'>HI:</span> विजाग बंदरगाह की ओर मोड़ें<br>
    <span style='color:#f87171'>TE:</span> వైజాగ్ పోర్ట్‌కు మళ్లించండి<br>
    <span style='color:#fbbf24'>TA:</span> விசாகப்பட்டினம் துறைமுகத்திற்கு திருப்பவும்
  </div>
</div>""", unsafe_allow_html=True)

    # ── COLUMN 3: Submit & Test ────────────────────────
    with col3:
        st.markdown("#### 🧪 Test Field Report Submission")
        
        reporter_type = st.radio("Reporter Role", ["Ship Captain", "Driver", "Train POC", "Ground Staff"], horizontal=True, key="haas_type")
        
        # Multilingual selector (Section 12)
        lang = st.selectbox("Report Language", 
            ["🇬🇧 English", "🇮🇳 हिन्दी (Hindi)", "🇮🇳 తెలుగు (Telugu)", "🇮🇳 தமிழ் (Tamil)"],
            key="haas_lang")

        # Quick Fills
        st.markdown("<div style='font-size:11px;color:#94a3b8;margin-bottom:4px'>Quick Fill Templates</div>", unsafe_allow_html=True)
        qfc1, qfc2, qfc3 = st.columns(3)
        if qfc1.button("🌊 Squall"): st.session_state.haas_demo_text = "Hit squall at 13.5N 83.2E, speed reduced to 8kn, 12 hours late, cargo intact"
        if qfc2.button("🔧 Break"): st.session_state.haas_demo_text = "TRK-CHN-101 breakdown near Nellore NH16, engine failure, need recovery"
        if qfc3.button("🌡 Cold"): st.session_state.haas_demo_text = "Reefer truck temperature rising, 6°C, route blocked, cargo at risk"

        report_text = st.text_area("Report Content", value=st.session_state.get("haas_demo_text", ""), height=100, label_visibility="collapsed")
        st.caption(f"{len(report_text)} chars")
        
        uploaded = st.file_uploader("📷 Attach photo (optional)", type=["jpg","jpeg","png"], key="haas_photo")

        if st.button("🚀 PROCESS WITH GEMINI", type="primary", use_container_width=True):
            if report_text.strip():
                # Multilingual Translation
                original_text = report_text
                if lang != "🇬🇧 English":
                    st.info("Translating with Google Translate API...")
                    translate_url = "https://translation.googleapis.com/language/translate/v2"
                    try:
                        tr = requests.post(translate_url, params={
                            "key": os.getenv("MAPS_API_KEY"),
                            "q": report_text,
                            "target": "en",
                            "format": "text"
                        }, timeout=8)
                        if tr.ok:
                            translated = tr.json()["data"]["translations"][0]["translatedText"]
                            st.success(f"🌐 Translated: {translated}")
                            report_text = translated
                    except Exception:
                        pass # proceed with original

                img_bytes = uploaded.read() if uploaded else None
                with st.spinner("🤖 Extracting structured data…"):
                    parsed = process_captain_report(report_text, img_bytes, demo_responses)
                
                parsed["timestamp"] = datetime.now().strftime("%H:%M IST")
                parsed["reporter_type"] = reporter_type
                parsed["raw_text"] = original_text
                parsed["resolved"] = False
                st.session_state.captain_reports.append(parsed)
                firebase_push("/field_reports", parsed)
                st.session_state["_last_parsed_report"] = parsed
                st.success("✅ Synced to Firebase — Command center updated")
                st.rerun()
            else:
                st.warning("Please enter a report text.")

        last = st.session_state.get("_last_parsed_report")
        if last:
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            gemma_badge = ""
            if st.session_state.get("gemma_mode", False):
                gemma_badge = "<div class='gemma-badge'>⚡ Processed by Gemma 2B (Edge Mode)</div>"
                
            st.markdown(f"""
<div class='glass-card' style='border-color:#4ade80'>
  <div style='font-size:11px;color:#64748b;margin-bottom:6px'>RAW INPUT</div>
  <div style='font-size:12px;color:#94a3b8;font-style:italic;margin-bottom:12px;background:rgba(0,0,0,0.2);padding:6px;border-radius:4px'>"{last.get('raw_text','')}"</div>
  <div style='font-size:11px;color:#64748b;margin-bottom:6px'>AI EXTRACTED</div>
  <div style='display:grid;grid-template-columns:1fr 1fr;gap:6px;font-size:11px'>
    <div style='color:#94a3b8'>Asset ID</div><div style='color:#e7efff'><b>{last.get('asset_id','')}</b></div>
    <div style='color:#94a3b8'>Delay</div><div style='color:#fbbf24'><b>{last.get('delay_hours',0)} hrs</b></div>
    <div style='color:#94a3b8'>Cargo</div><div style='color:#4ade80'><b>{last.get('cargo_status','')}</b></div>
    <div style='color:#94a3b8'>Urgency</div><div style='color:#f87171'><b>{last.get('urgency','').upper()}</b></div>
  </div>
  <div style='margin-top:10px;font-size:12px;color:#60a5fa'>
    💡 {last.get('recommended_action','')}
  </div>
  {gemma_badge}
</div>""", unsafe_allow_html=True)
