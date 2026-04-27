# -*- coding: utf-8 -*-
"""Human-as-a-Service Portal — Command Center + Field App Preview."""

from datetime import datetime

import streamlit as st

from utils.gemini import process_captain_report
from utils.firebase import firebase_write, firebase_read


def render(demo_responses):
    """Render the HaaS portal — split layout."""

    # Split: Command Center | Field App Preview
    cmd_col, field_col = st.columns([1.2, 1], gap="large")

    with cmd_col:
        st.markdown("#### 📡 Command Center — Live Field Reports")
        _render_live_feed()
        st.markdown("---")
        _render_active_reroutes()

    with field_col:
        st.markdown("#### 📱 Field App Preview")
        _render_field_app_mockup()

    # Field Report Submission below
    st.markdown("---")
    st.markdown("#### 📤 Field Report Submission")
    _render_report_form(demo_responses)


def _render_live_feed():
    """Live field reports feed from Firebase."""
    if st.button("🔄 Refresh Feed", key="haas_refresh"):
        pass  # triggers re-read

    fb_data = firebase_read("/field_reports")
    reports = []
    if isinstance(fb_data, dict):
        reports = sorted(fb_data.values(), key=lambda x: x.get("timestamp", ""), reverse=True)[:8]

    if not reports:
        reports = st.session_state.get("captain_reports", [])[-5:]

    if reports:
        for rep in reports:
            urg = rep.get("urgency", "low")
            badge = "badge-red" if urg == "critical" else ("badge-amber" if urg == "high" else "badge-green")
            ts = rep.get("timestamp", "")
            reporter_icon = {"Ship Captain": "🚢", "Truck Driver": "🚛", "Ground Staff": "👷"}.get(
                rep.get("reporter_type", ""), "📡"
            )
            action_taken = rep.get("action_taken", False)
            action_html = "<span class='badge-green'>✅ Resolved</span>" if action_taken else "<span class='badge-blue'>⏳ Pending</span>"

            st.markdown(
                f"""
                <div class='glass-card' style='padding:10px'>
                  <div style='display:flex;justify-content:space-between;align-items:center'>
                    <span>{reporter_icon} <span class='{badge}'>{urg.upper()}</span></span>
                    {action_html}
                  </div>
                  <div style='font-size:13px;color:#e7efff;margin-top:4px'>{rep.get('summary', 'No summary')}</div>
                  <div style='font-size:11px;color:#64748b;margin-top:4px'>
                    {rep.get('reporter_type', '')} | {rep.get('asset_id', '')} | {ts[:16] if ts else ''}
                  </div>
                  <div style='font-size:11px;color:#94a3b8;margin-top:2px'>
                    Delay: {rep.get('delay_hours', 0)}h | Cargo: {rep.get('cargo_status', 'N/A')} | Location: {rep.get('location', 'N/A')}
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            "<div style='text-align:center;padding:30px;opacity:0.5'>"
            "<div style='font-size:36px'>📡</div>"
            "<div style='font-size:14px;color:#94a3b8'>No field reports yet</div>"
            "<div style='font-size:12px;color:#64748b'>Submit a report below to see it here</div></div>",
            unsafe_allow_html=True,
        )


def _render_active_reroutes():
    """Active reroutes from Firebase."""
    st.markdown("##### 🔄 Active Reroutes")
    fb_reroutes = firebase_read("/active_reroutes")
    if isinstance(fb_reroutes, dict) and fb_reroutes:
        for key, reroute in fb_reroutes.items():
            ts = reroute.get("timestamp", "")
            st.markdown(
                f"""
                <div class='glass-card' style='border-color:#4ade80'>
                  <span class='badge-green'>ACTIVE</span><br>
                  <b>{key.replace('_', ' ')}</b><br>
                  Port: {reroute.get('alt_port', 'N/A')} | Train: {reroute.get('rail_train', 'N/A')}<br>
                  <span style='font-size:11px;color:#64748b'>{ts[:16] if ts else ''}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
    elif st.session_state.get("reroute_accepted"):
        st.markdown(
            """
            <div class='glass-card' style='border-color:#4ade80'>
              <span class='badge-green'>ACTIVE</span><br>
              <b>MV Chennai Star</b> → Visakhapatnam<br>
              Train 58501 | 3 trucks dispatched
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.caption("No active reroutes.")


def _render_field_app_mockup():
    """Flutter app preview mockup."""
    st.markdown(
        """
        <div style='background:#0a1628;border:2px solid #1e3a5f;border-radius:24px;padding:16px;max-width:320px;margin:0 auto'>
          <div style='background:#0d1f3c;border-radius:16px;padding:12px;margin-bottom:8px'>
            <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:10px'>
              <span style='color:#FF6B35;font-weight:700;font-size:14px'>🚢 LogistiQ Field</span>
              <span style='font-size:10px;color:#4ade80'>🟢 Synced</span>
            </div>
            <div style='font-size:11px;color:#94a3b8;margin-bottom:8px'>Captain — MV Chennai Star</div>
          </div>

          <div style='background:#0d1f3c;border-radius:12px;padding:10px;margin-bottom:8px'>
            <div style='font-size:11px;color:#fbbf24;font-weight:600;margin-bottom:4px'>📋 ACTIVE INSTRUCTION</div>
            <div style='font-size:11px;color:#e7efff'>Divert to Visakhapatnam Port</div>
            <div style='font-size:10px;color:#94a3b8'>New heading: 17.68°N 83.22°E</div>
            <div style='background:#FF6B35;color:white;text-align:center;padding:6px;border-radius:8px;margin-top:8px;font-size:11px;font-weight:600'>
              ✅ ACKNOWLEDGE
            </div>
          </div>

          <div style='background:#0d1f3c;border-radius:12px;padding:10px;margin-bottom:8px'>
            <div style='font-size:11px;color:#60a5fa;font-weight:600;margin-bottom:4px'>🌤 WEATHER AT POSITION</div>
            <div style='font-size:11px;color:#e7efff'>Clear | Wind: 22 kph | Vis: 10km</div>
          </div>

          <div style='background:#0d1f3c;border-radius:12px;padding:10px;margin-bottom:8px'>
            <div style='font-size:11px;color:#4ade80;font-weight:600;margin-bottom:4px'>📍 POSITION</div>
            <div style='font-size:11px;color:#e7efff'>14.35°N 81.98°E | Speed: 15.2 kn</div>
          </div>

          <div style='background:#FF6B35;color:white;text-align:center;padding:10px;border-radius:12px;font-size:12px;font-weight:700'>
            📤 SUBMIT FIELD REPORT
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_report_form(demo_responses):
    """Field report submission with Gemini processing."""
    in_col, out_col = st.columns(2)

    with in_col:
        st.markdown("**Submit Field Report**")
        report_text = st.text_area(
            "Type or paste field report", height=120,
            placeholder="Examples:\n• Captain: Hit squall 13.5N 83.2E, 12hrs late, cargo intact\n• Driver: TRK-CHN-101 breakdown near Nellore NH16",
            key="haas_report",
        )
        uploaded_img = st.file_uploader("📷 Attach photo (optional)", type=["jpg", "jpeg", "png", "webp"], key="haas_photo")
        st.selectbox("Reporter type", ["Ship Captain", "Truck Driver", "Train POC", "Ground Staff", "Port Authority"], key="haas_reporter")
        submit_btn = st.button("📤 PROCESS WITH GEMINI", use_container_width=True, type="primary", key="haas_submit")

    with out_col:
        if not submit_btn:
            st.markdown(
                """
                <div class='glass-card' style='opacity:0.6'>
                  <b>Example extracted output:</b><br>
                  Reporter: Ship Captain<br>
                  Delay: 12 hours<br>
                  Cargo: Intact ✅<br>
                  Urgency: <span class='badge-amber'>HIGH</span><br>
                  Location: 13.52°N 83.21°E<br>
                  Action: Reduce speed, notify port<br>
                  <i>Submit a report to see live extraction...</i>
                </div>
                """,
                unsafe_allow_html=True,
            )
        elif not report_text.strip():
            st.warning("Please enter a report before submitting.")
        else:
            with st.spinner("Gemini extracting structured data..."):
                img_bytes = uploaded_img.read() if uploaded_img else None
                result = process_captain_report(report_text, img_bytes, demo_responses)

            urg = result.get("urgency", "low")
            badge = "badge-red" if urg == "critical" else ("badge-amber" if urg == "high" else "badge-blue")

            # Side-by-side RAW vs EXTRACTED
            st.markdown(f"<div style='font-size:11px;color:#64748b;margin-bottom:4px'>RAW INPUT:</div>", unsafe_allow_html=True)
            st.code(report_text, language=None)

            st.markdown(
                f"""
                <div class='glass-card'>
                  <b>EXTRACTED — <span class='{badge}'>{urg.upper()} PRIORITY</span></b><br><br>
                  <b>Reporter:</b> {result.get('reporter_type', '')}<br>
                  <b>Asset:</b> {result.get('asset_id', '')}<br>
                  <b>Delay:</b> {result.get('delay_hours', 0)} hours<br>
                  <b>Cargo:</b> {result.get('cargo_status', '')}<br>
                  <b>Location:</b> {result.get('location', '')}<br>
                  <b>Weather:</b> {result.get('weather_conditions', '')}<br>
                  <b>Action:</b> {'YES ⚠' if result.get('action_required') else 'No'}<br>
                  <b>Recommended:</b> {result.get('recommended_action', '')}<br>
                  <b>Notify:</b> {', '.join(result.get('notify', []))}<br><br>
                  <i>{result.get('summary', '')}</i>
                </div>
                """,
                unsafe_allow_html=True,
            )

            fb_ok = firebase_write(
                f"/field_reports/{int(datetime.now().timestamp())}",
                {**result, "raw_report": report_text, "timestamp": datetime.now().isoformat()},
            )
            st.caption("✅ Synced to Firebase" if fb_ok else "⚠ Saved locally (Firebase offline)")
            if "captain_reports" not in st.session_state:
                st.session_state.captain_reports = []
            st.session_state.captain_reports.append({**result, "timestamp": datetime.now().isoformat()})
