# -*- coding: utf-8 -*-
"""Human-as-a-Service (HaaS) — Captain's Portal."""
import streamlit as st
import time
from datetime import datetime

from logistiq.data import demo_responses
from logistiq.components import cards as K
from logistiq.utils.gemini import process_captain_report
from logistiq.utils.firebase import firebase_read, firebase_push, firebase_write

REPORTER_ICONS = {
    "Ship Captain": "🚢",
    "Driver":       "🚛",
    "Ground Staff": "👷",
    "Port Officer": "⚓",
}


def render():
    st.markdown("### 📞 Human-as-a-Service — Captain's Portal")
    st.caption("Real-time field reports from vessels, trucks, and ground staff")

    left_col, right_col = st.columns([1.2, 1])

    # ── LEFT: Command Center view ──────────────────────
    with left_col:
        st.markdown("#### 📥 Live Field Reports")

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
            reports_list.append(r)
        reports_list.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        if not reports_list:
            K.empty_state("📡", "No field reports yet",
                          "Submit a report below or wait for field personnel to sync.")
        else:
            for rep in reports_list[:10]:
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
    <span style='font-size:11px;color:#64748b'>{rep.get("timestamp", "")}</span>
  </div>
  <div style='font-size:12px;color:#e7efff;margin:4px 0'>{rep.get("summary", "")}</div>
  <div style='display:flex;gap:16px;font-size:11px;color:#64748b;margin-top:4px'>
    <span>📍 {rep.get("location", "N/A")}</span>
    <span>⏱ Delay: {rep.get("delay_hours", 0)} hrs</span>
    <span>📦 Cargo: {rep.get("cargo_status", "N/A")}</span>
  </div>
</div>""", unsafe_allow_html=True)

        # ── Response composer ─────────────────────────
        st.markdown("#### 📤 Send Instruction to Field")
        asset_options = list({r.get("asset_id", "") for r in reports_list if r.get("asset_id")}) or ["MV Chennai Star"]
        selected_asset = st.selectbox("Select asset", asset_options, key="haas_asset")
        instruction = st.text_area("Instruction", placeholder="e.g. Divert to Vizag Port. New heading 17.68N 83.22E. Acknowledge.", key="haas_instruction")
        if st.button("📲 Send to Field", use_container_width=True, key="haas_send"):
            firebase_write(f"/active_reroutes/{selected_asset.replace(' ','_')}", {
                "instruction": instruction,
                "status": "sent",
                "timestamp": datetime.now().isoformat(),
                "ack": False,
            })
            st.success(f"✅ Instruction sent to {selected_asset} via Firebase")

        # ── Active reroutes ────────────────────────────
        st.markdown("#### ⚡ Active Reroutes")
        reroutes = firebase_read("/active_reroutes") or {}
        if isinstance(reroutes, dict) and reroutes:
            for k, v in reroutes.items():
                if isinstance(v, dict):
                    ack = v.get("ack", False)
                    ack_html = "<span class='badge badge-safe'>✅ ACKNOWLEDGED</span>" if ack else "<span class='badge badge-medium'>⏳ AWAITING ACK</span>"
                    st.markdown(f"""
<div class='glass-card' style='padding:10px'>
  <div style='display:flex;justify-content:space-between'>
    <b style='font-size:12px'>{k.replace('_',' ')}</b> {ack_html}
  </div>
  <div style='font-size:11px;color:#94a3b8;margin-top:4px'>{v.get('instruction','')[:120]}</div>
</div>""", unsafe_allow_html=True)
        else:
            st.caption("No active reroutes.")

    # ── RIGHT: Flutter app mockup ──────────────────────
    with right_col:
        st.markdown("#### 📱 Field App Preview (Flutter)")
        st.markdown("""
<div style='display:flex;justify-content:center'>
<div style='width:260px;background:#0a0e1a;border-radius:36px;padding:14px;
            border:2px solid rgba(96,165,250,0.3);box-shadow:0 0 40px rgba(68,197,255,0.08)'>
  <!-- Phone notch -->
  <div style='width:80px;height:6px;background:#1e293b;border-radius:3px;margin:0 auto 12px'></div>

  <!-- Status bar -->
  <div style='display:flex;justify-content:space-between;font-size:10px;color:#64748b;margin-bottom:8px;padding:0 4px'>
    <span>9:41 AM</span><span>🛜 5G  🔋</span>
  </div>

  <!-- App header -->
  <div style='background:linear-gradient(135deg,#FF6B35,#ff8c5a);border-radius:12px;padding:10px 12px;margin-bottom:8px'>
    <div style='font-size:14px;font-weight:700;color:white'>LogistiQ Field</div>
    <div style='font-size:10px;color:rgba(255,255,255,0.8)'>🚢 MV Chennai Star — Capt. Rajesh</div>
  </div>

  <!-- Assignment card -->
  <div style='background:rgba(255,255,255,0.05);border-radius:10px;padding:10px;margin-bottom:6px'>
    <div style='font-size:10px;color:#64748b;margin-bottom:4px'>CURRENT ASSIGNMENT</div>
    <div style='font-size:12px;font-weight:600;color:#e7efff'>4,200 Engine Blocks → Manesar</div>
    <div style='font-size:10px;color:#94a3b8;margin-top:2px'>Consignee: Maruti Suzuki India Ltd</div>
    <div style='margin-top:8px;background:rgba(248,113,113,0.15);border-radius:8px;padding:8px'>
      <div style='font-size:10px;color:#f87171;font-weight:600'>⚠ NEW INSTRUCTION</div>
      <div style='font-size:10px;color:#fca5a5;margin-top:2px'>Divert to Vizag Port. New heading 17.68°N</div>
    </div>
  </div>

  <!-- Status bar buttons -->
  <div style='display:flex;gap:4px;margin-bottom:6px'>
    <div style='flex:1;background:rgba(68,197,255,0.15);border:1px solid rgba(68,197,255,0.3);
                border-radius:6px;padding:6px;text-align:center;font-size:9px;color:#44c5ff'>At Sea</div>
    <div style='flex:1;background:rgba(74,222,128,0.15);border:1px solid rgba(74,222,128,0.3);
                border-radius:6px;padding:6px;text-align:center;font-size:9px;color:#4ade80'>Diverting</div>
    <div style='flex:1;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);
                border-radius:6px;padding:6px;text-align:center;font-size:9px;color:#64748b'>Docked</div>
  </div>

  <!-- Weather mini -->
  <div style='background:rgba(255,255,255,0.03);border-radius:8px;padding:8px;margin-bottom:6px;font-size:10px;color:#94a3b8'>
    🌤 Current: 28°C | Wind: 35 kph | Wave: 1.8m
  </div>

  <!-- Report button -->
  <div style='background:#FF6B35;border-radius:10px;padding:10px;text-align:center;
              font-size:12px;font-weight:700;color:white;margin-top:4px'>
    📋 Report Issue
  </div>

  <!-- Sync indicator -->
  <div style='text-align:center;margin-top:8px;font-size:9px;color:#4ade80'>🟢 Synced to Command Center</div>
</div>
</div>""", unsafe_allow_html=True)

    # ── Field report submission ────────────────────────
    st.markdown("---")
    st.markdown("#### 📝 Submit Field Report (Demo / Testing)")
    submit_col, result_col = st.columns(2)

    with submit_col:
        st.markdown("**Quick Submit**")
        reporter_type = st.selectbox("Reporter Type", ["Ship Captain", "Driver", "Ground Staff", "Port Officer"], key="haas_type")
        report_text   = st.text_area("Report Text", placeholder='e.g. "Hit squall 13.5N 83.2E, 12 hours late, cargo fine"', key="haas_text", height=100)
        uploaded      = st.file_uploader("📷 Attach photo (optional)", type=["jpg","jpeg","png"], key="haas_photo")
        if st.button("🚀 Submit & AI Extract", type="primary", use_container_width=True, key="haas_submit"):
            if report_text.strip():
                img_bytes = uploaded.read() if uploaded else None
                with st.spinner("🤖 Gemini extracting structured data…"):
                    parsed = process_captain_report(report_text, img_bytes, demo_responses)
                parsed["timestamp"] = datetime.now().strftime("%H:%M IST")
                parsed["reporter_type"] = reporter_type
                parsed["raw_text"] = report_text
                parsed["resolved"] = False
                st.session_state.captain_reports.append(parsed)
                firebase_push("/field_reports", parsed)
                st.session_state["_last_parsed_report"] = parsed
                st.success("✅ Report submitted and synced to Firebase")
                st.rerun()
            else:
                st.warning("Please enter a report text.")

    with result_col:
        last = st.session_state.get("_last_parsed_report")
        if last:
            st.markdown("**AI Extraction Result**")
            st.markdown(f"""
<div class='glass-card'>
  <div style='font-size:11px;color:#64748b;margin-bottom:6px'>RAW INPUT</div>
  <div style='font-size:12px;color:#94a3b8;font-style:italic;margin-bottom:12px'>"{last.get('raw_text','')}"</div>
  <div style='font-size:11px;color:#64748b;margin-bottom:6px'>EXTRACTED</div>
  <div style='display:grid;grid-template-columns:1fr 1fr;gap:6px;font-size:11px'>
    <div style='color:#94a3b8'>Asset ID</div><div style='color:#e7efff'>{last.get('asset_id','')}</div>
    <div style='color:#94a3b8'>Delay</div><div style='color:#fbbf24'>{last.get('delay_hours',0)} hrs</div>
    <div style='color:#94a3b8'>Cargo</div><div style='color:#4ade80'>{last.get('cargo_status','')}</div>
    <div style='color:#94a3b8'>Location</div><div style='color:#e7efff'>{last.get('location','')}</div>
    <div style='color:#94a3b8'>Urgency</div><div style='color:#f87171'>{last.get('urgency','').upper()}</div>
    <div style='color:#94a3b8'>Action Req.</div><div style='color:#e7efff'>{"Yes" if last.get('action_required') else "No"}</div>
  </div>
  <div style='margin-top:10px;font-size:12px;color:#60a5fa'>
    💡 {last.get('recommended_action','')}
  </div>
</div>""", unsafe_allow_html=True)
        else:
            K.empty_state("🤖", "Submit a report", "AI will extract structured data and show it here.")
