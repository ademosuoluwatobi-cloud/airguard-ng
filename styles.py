"""
AirGuard NG — Unified Design System & Data Logic
Optimized for: Mobile Visibility, Real-time Sync, and Multi-State Persistence
"""
import json
import os
import pandas as pd
from datetime import datetime
import streamlit as st

# ── DATA LOADING (With Cloud-Sync Caching) ───────────────────

@st.cache_data(ttl=5)  # Refreshes Hardware data every 5 seconds
def load_device_data():
    """Reads the local hardware JSON pushed from your laptop."""
    DATA_FILE = "esp32_data.json"
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                d = json.load(f)
                # Returns (latest_reading_dict, all_readings_list)
                return d.get("latest"), d.get("readings", [])
        except Exception:
            pass
    return None, []

@st.cache_data(ttl=60)  # Refreshes City CSV data every 1 minute
def load_csv_data(file_path):
    """Reads the OpenAQ city data CSVs."""
    if os.path.exists(file_path):
        try:
            return pd.read_csv(file_path)
        except Exception:
            pass
    return pd.DataFrame()

# ── UI STYLING & MOBILE FIXES ────────────────────────────────

BASE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;500;600;700;800&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* Global Styles */
html, body, [class*="css"], .stApp {
    font-family: 'Inter', sans-serif !important;
    background-color: #07110C !important;
    color: #F8FAFC !important;
}

/* Sidebar Styling */
[data-testid="stSidebar"] {
    background: #0F172A !important;
    border-right: 1px solid rgba(255,255,255,0.07) !important;
}

/* MOBILE FIX: Make the sidebar arrow visible on phones */
[data-testid="stHeader"] {
    background: transparent !important;
    color: #16A34A !important; /* Makes the mobile 'arrow' menu green */
}

/* Hide Streamlit junk but keep functional buttons */
[data-testid="stToolbar"], [data-testid="stDecoration"] {
    display: none !important;
}

/* Dashboard Containers */
.block-container {
    padding: 2rem 2.5rem 4rem !important;
    max-width: 1280px !important;
}

/* Custom Components */
[data-testid="stSidebarNavLink"][aria-current="page"] {
    background: rgba(22,163,74,0.12) !important;
    color: #16A34A !important;
    font-weight: 600 !important;
}

@keyframes ag-pulse {
    0%, 100% { box-shadow: 0 0 0 0 rgba(22,163,74,0.5); }
    50% { box-shadow: 0 0 0 6px rgba(22,163,74,0); }
}
.ag-live {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #16A34A;
    margin-right: 6px;
    vertical-align: middle;
    animation: ag-pulse 2s infinite;
}

@keyframes ag-danger { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
.ag-danger-pulse { animation: ag-danger 1.4s infinite; }

/* Mobile Card Stacking */
@media (max-width: 768px) {
    .block-container { padding: 1rem !important; }
}
</style>
"""

# ── TABLES & CONSTANTS ───────────────────────────────────────

RISK_COLORS = {"Good":"#16A34A","Moderate":"#EAB308","Unhealthy for Sensitive Groups":"#F97316","Unhealthy":"#DC2626","Very Unhealthy":"#9333EA","Hazardous":"#7E22CE","No Data":"#64748B"}
RISK_BG = {k: f"rgba({int(v[1:3],16)}, {int(v[3:5],16)}, {int(v[5:7],16)}, 0.10)" for k,v in RISK_COLORS.items()}
RISK_BORDER = {k: f"rgba({int(v[1:3],16)}, {int(v[3:5],16)}, {int(v[5:7],16)}, 0.30)" for k,v in RISK_COLORS.items()}

MONITORED_STATES = ["Lagos State", "Ogun State", "Cross River State", "FCT Abuja"]

GAS_LEVELS = [
    (150, "GOOD", "Safe", "#16A34A", "✅"),
    (200, "MODERATE", "Caution", "#EAB308", "⚠️"),
    (250, "POOR", "Warning", "#F97316", "🔶"),
    (325, "BAD", "Danger", "#DC2626", "🚨"),
    (1023, "TOXIC", "Critical", "#9333EA", "☣️"),
]

# ── CORE LOGIC ───────────────────────────────────────────────

def calculate_hrs(pm25):
    if pm25 is None or pm25 < 0: return 0, "No Data"
    elif pm25 <= 12:    return round((pm25/12)*20, 1), "Good"
    elif pm25 <= 35.4:  return round(20+((pm25-12)/23.4)*20, 1), "Moderate"
    elif pm25 <= 55.4:  return round(40+((pm25-35.4)/20)*20, 1), "Unhealthy for Sensitive Groups"
    elif pm25 <= 150.4: return round(60+((pm25-55.4)/95)*20, 1), "Unhealthy"
    elif pm25 <= 250.4: return round(80+((pm25-150.4)/100)*20, 1), "Very Unhealthy"
    else:               return 100, "Hazardous"

def classify_gas(raw):
    if raw is None: return "No Data", "#64748B", "rgba(100,116,139,0.1)", "📡", "No Data"
    r = int(raw)
    for mx, label, risk, color, icon in GAS_LEVELS:
        if r <= mx:
            bg = f"rgba({int(color[1:3],16)}, {int(color[3:5],16)}, {int(color[5:7],16)}, 0.1)"
            brd = f"rgba({int(color[1:3],16)}, {int(color[3:5],16)}, {int(color[5:7],16)}, 0.3)"
            return label, color, bg, brd, icon, risk
    return "TOXIC", "#9333EA", "rgba(147,51,234,0.1)", "rgba(147,51,234,0.3)", "☣️", "Critical"

def get_all_city_options(user_state="", user_city=""):
    """Ensures primary states NEVER disappear from dropdowns."""
    options = list(MONITORED_STATES)
    if user_state and user_state not in options:
        options.append(f"{user_state} (Your Location 📍)")
    return options

# ── UI HELPERS ───────────────────────────────────────────────

def section(st, text):
    st.markdown(f'<p style="font-size:11px;font-weight:600;color:#64748B;text-transform:uppercase;letter-spacing:.08em;margin:24px 0 12px;padding-bottom:8px;border-bottom:1px solid rgba(255,255,255,0.06)">{text}</p>', unsafe_allow_html=True)

def stat_html(label, value, unit, color):
    return (f'<div style="background:#111827;border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:18px 20px;text-align:center">'
            f'<p style="font-size:11px;font-weight:600;color:#64748B;text-transform:uppercase;letter-spacing:.07em;margin:0 0 4px">{label}</p>'
            f'<p style="font-family:Sora,sans-serif;font-size:2rem;font-weight:800;color:{color};line-height:1;margin:4px 0">{value}</p>'
            f'<p style="font-size:11px;color:#64748B;margin:0">{unit}</p></div>')

def device_status_bar(st, location_label=""):
    device, _ = load_device_data()
    if device is None:
        st.markdown('<div style="background:#111827;border:1px solid rgba(255,255,255,0.07);border-radius:12px;padding:10px 16px;margin-bottom:16px;font-size:13px;color:#4a5a7a">📡 AirGuard Device Offline — Check serial_reader.py</div>', unsafe_allow_html=True)
        return
    
    raw, ppm, temp, hum, ts = device.get("gas_raw", 0), device.get("gas_ppm", 0), device.get("temperature", "—"), device.get("humidity", "—"), device.get("timestamp", "")
    gl, gc, gbg, gbrd, gi, grisk = classify_gas(raw)
    
    st.markdown(f"""
        <div style="background:{gbg}; border:1px solid {gbrd}; border-radius:12px; padding:10px 16px; margin-bottom:16px; display:flex; align-items:center; gap:16px; flex-wrap:wrap; font-size:13px">
            <div style="display:flex; align-items:center; gap:6px"><span class="ag-live"></span><span style="font-weight:600; color:{gc}">🔩 AirGuard Live · {location_label}</span></div>
            <span style="color:#64748B">|</span>
            <span style="color:#94A3B8">Gas: <strong style="color:{gc}">{ppm} ppm</strong> {gi}</span>
            <span style="color:#64748B">|</span>
            <span style="color:#94A3B8">🌡 <strong style="color:#42a5f5">{temp}°C</strong></span>
            <span style="color:#64748B">|</span>
            <span style="color:#94A3B8">💧 <strong style="color:#26c6da">{hum}%</strong></span>
        </div>
    """, unsafe_allow_html=True)