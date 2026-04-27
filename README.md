# LogistiQ Command Center

LogistiQ is an AI-powered multimodal supply chain command center built with Streamlit, Gemini AI, Firebase, Folium, and Plotly.

## Main Features
- **Global Overview**: A unified map tracking vessels, trucks, and trains with risk heatmaps and live alerts.
- **Sea & Maritime**: Live tracking of vessels with real-time weather, tidal conditions, and a vessel speed optimizer.
- **Multimodal Journey**: A synced horizontal stepper tracking cargo across different modes with live cost mapping and CO₂ footprint tracker.
- **Human-as-a-Service (HaaS)**: Field reporting tool for captains and drivers that extracts logistics data directly via Gemini vision capabilities.
- **AI-Powered Command Bar**: Global command input (Ctrl+K) to easily interact with the UI via Natural Language.

## Setup Instructions
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Configure Environment Variables:
   Copy `.env.example` to `.env` and fill in your API keys:
   ```bash
   cp .env.example .env
   ```
   Provide valid keys for `GEMINI_API_KEY`, `FIREBASE_URL`, `WEATHER_API_KEY`, and `MAPS_API_KEY`.

## Launch
To start the command center, run:
```bash
streamlit run logistiq/app.py
```
