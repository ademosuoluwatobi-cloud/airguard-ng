"""
AirGuard NG — Main Dashboard
Optimized for: Mobile Visibility, Real-time Sync, and Multi-State Persistence
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import folium, json, os
from streamlit_folium import st_folium
from streamlit_autorefresh import st_autorefresh
from datetime import datetime

# Import our unified styles and logic
from styles import (
    BASE_CSS, RISK_COLORS, RISK_BG, RISK_BORDER, RISK_ADVICE, CONDITION_ADVICE,
    MONITORED_STATES, STATE_COORDS, DEFAULT_LAT, DEFAULT_LON,
    section, badge, stat_html, plotly_layout, calculate_hrs, load_device_data,
    classify_gas, gas_is_dangerous, device_status_bar,
    get_user_location, get_temp_hum_for_city, load_csv_data
)

# 1. ESSENTIAL CONFIG (Mobile Fix: Sidebar starts expanded)
st.set_page_config(
    page_title="AirGuard NG",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply our CSS with the mobile menu button fix
st.markdown(BASE_CSS, unsafe_allow_html=True)

# Auto-refresh every 10 seconds for real-time hardware updates
st_autorefresh(interval=10000, key="ov_refresh")

def md(h): st.markdown(h, unsafe_allow_html=True)

# ── SESSION DEFAULTS ─────────────────────────────────────────
for k, v in [("onboarding_done", False), ("user_name", ""), ("user_condition", ""), ("user_state", ""), ("user_city", "")]:
    if k not in st.session_state: st.session_state[k] = v

ALL_STATES = ["Abia","Adamawa","Akwa Ibom","Anambra","Bauchi","Bayelsa","Benue","Borno","Cross River","Delta","Ebonyi","Edo","Ekiti","Enugu","FCT Abuja","Gombe","Imo","Jigawa","Kaduna","Kano","Katsina","Kebbi","Kogi","Kwara","Lagos","Nasarawa","Niger","Ogun","Ondo","Osun","Oyo","Plateau","Rivers","Sokoto","Taraba","Yobe","Zamfara"]
CONDITIONS = ["", "Asthma", "COPD", "Heart Disease", "Diabetes", "Hypertension", "Pregnancy", "Child Under 12", "None"]
COND_LBL = {"": "My condition", "Asthma": "Asthma", "COPD": "COPD", "Heart Disease": "Heart Disease", "Diabetes": "Diabetes", "Hypertension": "Hypertension", "Pregnancy": "Pregnancy", "Child Under 12": "Child Under 12", "None": "No condition"}
BADGE_SHORT = {"Good": "Good", "Moderate": "Moderate", "Unhealthy for Sensitive Groups": "Sensitive", "Unhealthy": "Unhealthy", "Very Unhealthy": "Very Unhealthy", "Hazardous": "Hazardous", "No Data": "No Data"}

# ── DATA LOADING ─────────────────────────────────────────────
df = load_csv_data("transformed_data.csv")
raw = load_csv_data("raw_data.csv")
slocs = load_csv_data("sensor_locations.csv")
device, _ = load_device_data()

# ── ONBOARDING ───────────────────────────────────────────────
if not st.session_state.onboarding_done:
    _, col, _ = st.columns([1, 2, 1])
    with col:
        md("""<div style="background:#111827;border:1px solid rgba(255,255,255,0.12);border-radius:24px;padding:36px 40px;margin-top:50px;box-shadow:0 20px 60px rgba(0,0,0,0.5)">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:24px">
        <div style="width:36px;height:36px;background:rgba(22,163,74,0.12);border:1px solid rgba(22,163,74,0.28);border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:18px">🛡️</div>
        <span style="font-family:Sora,sans-serif;font-size:18px;font-weight:700;color:#F8FAFC">AirGuard <span style="color:#16A34A">NG</span></span></div>
        <h2 style="font-family:Sora,sans-serif;font-size:22px;font-weight:700;color:#F8FAFC;letter-spacing:-.02em;margin:0 0 6px">Welcome to AirGuard NG</h2>
        <p style="font-size:14px;color:#64748B;margin:0 0 24px;line-height:1.6">Set up your profile for personalised air quality insights and condition-aware health alerts across Nigeria.</p></div>""")
        
        name = st.text_input("name", placeholder="e.g. Tobi Ademosu", label_visibility="collapsed")
        condition = st.selectbox("condition", CONDITIONS, format_func=lambda x: COND_LBL.get(x, x), label_visibility="collapsed")
        
        cs, cc = st.columns(2)
        with cs:
            state = st.selectbox("state", [""] + ALL_STATES, format_func=lambda x: "Select state" if x == "" else x, label_visibility="collapsed")
        with cc:
            city = st.text_input("city", placeholder="e.g. Yaba", label_visibility="collapsed")
            
        if st.button("Continue to dashboard →", use_container_width=True):
            st.session_state.user_name = name.strip() or "Friend"
            st.session_state.user_condition = condition
            st.session_state.user_state = state
            st.session_state.user_city = city.strip()
            st.session_state.onboarding_done = True
            st.rerun()

elif st.session_state.onboarding_done:
    # ── LOGIC & VALUES ───────────────────────────────────────
    user_name = st.session_state.user_name
    user_state = st.session_state.user_state
    user_city = st.session_state.user_city
    user_condition = st.session_state.user_condition
    
    _, _, user_lat, user_lon, user_loc_label = get_user_location(st.session_state)
    now_str = datetime.now().strftime("%d %b %Y, %H:%M")
    
    # Hero Data Logic
    user_key = f"{user_state} State" if "State" not in user_state and user_state else user_state
    ur = df[df["city"] == user_key] if not df.empty else pd.DataFrame()
    
    # If no city data, use Hardware data as backup for the Hero section
    if ur.empty and device:
        user_hrs = device.get("gas_ppm", "—")
        user_risk = "Indoor Monitor"
        user_col = "#16A34A"
    else:
        user_hrs = ur.iloc[0]["hrs"] if not ur.empty else "—"
        user_risk = ur.iloc[0]["risk_level"] if not ur.empty else "No Data"
        user_col = RISK_COLORS.get(user_risk, "#64748B")

    # ── HEADER ───────────────────────────────────────────────
    md(f"""<div style="display:flex;align-items:center;gap:12px;margin-bottom:20px;padding-bottom:18px;border-bottom:1px solid rgba(255,255,255,0.06)">
    <div style="width:38px;height:38px;background:rgba(22,163,74,0.12);border:1px solid rgba(22,163,74,0.28);border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:19px">🛡️</div>
    <div><p style="font-family:Sora,sans-serif;font-size:20px;font-weight:800;color:#F8FAFC;letter-spacing:-.01em;margin:0;line-height:1.1">AirGuard <span style="color:#16A34A">NG</span></p>
    <p style="font-size:12px;color:#64748B;margin:0">Real-time Intelligence — {user_state or 'Nigeria'}</p></div>
    <div style="margin-left:auto;display:flex;align-items:center;gap:12px">
    <div style="background:#111827;border:1px solid rgba(255,255,255,0.08);border-radius:999px;padding:6px 14px 6px 8px;display:flex;align-items:center;gap:8px">
    <span class="ag-live"></span><span style="font-size:13px;font-weight:500;color:#CBD5E1">{user_name}</span></div>
    </div></div>""")

    # ── STATUS BAR ───────────────────────────────────────────
    device_status_bar(st, location_label=user_state or "")

    # ── PERSISTENT STATE CARDS ───────────────────────────────
    section(st, "Active Monitoring Locations")
    c1, c2, c3, c4, c5 = st.columns(5)
    
    # Force Lagos, Ogun, Abuja, and Cross River to ALWAYS show
    for col, state_name in zip([c1, c2, c3, c4], MONITORED_STATES):
        row = df[df["city"] == state_name] if not df.empty else pd.DataFrame()
        
        if row.empty:
            hrs, risk, pm25v = "—", "No Data", "—"
        else:
            r = row.iloc[0]
            hrs, risk, pm25v = r["hrs"], r["risk_level"], round(r["value"], 1)
            
        color = RISK_COLORS.get(risk, "#64748B")
        bg = RISK_BG.get(risk, "rgba(100,116,139,0.10)")
        brd = RISK_BORDER.get(risk, "rgba(100,116,139,0.30)")
        short = BADGE_SHORT.get(risk, risk)
        
        with col:
            md(f"""<div style="background:{bg};border:1px solid {brd};border-radius:18px;padding:18px;position:relative;min-height:240px">
            <div style="position:absolute;top:0;left:0;right:0;height:3px;background:{color}"></div>
            <p style="font-family:Sora,sans-serif;font-size:13px;font-weight:700;color:#CBD5E1;margin:0">{state_name}</p>
            <span style="background:{color}20;color:{color};border:1px solid {color}33;padding:2px 9px;border-radius:999px;font-size:10px;font-weight:600">{short}</span>
            <p style="font-family:Sora,sans-serif;font-size:2.8rem;font-weight:800;color:{color};line-height:1;margin:10px 0 0">{hrs}</p>
            <p style="font-size:10px;font-weight:600;color:#64748B;text-transform:uppercase;margin:4px 0 8px">Health Risk Score</p>
            <div style="height:1px;background:rgba(255,255,255,0.06);margin-bottom:8px"></div>
            <p style="font-family:JetBrains Mono,monospace;font-size:12px;color:#64748B">PM2.5 · {pm25v} µg/m³</p>
            </div>""")

    # 5th card — Hardware Device
    with c5:
        gas_raw = int(device.get("gas_raw", 0) or 0) if device else None
        ppm_v = device.get("gas_ppm", "—") if device else "—"
        gl, gc, gbg, gbrd, gi, grisk = classify_gas(gas_raw)
        sdot = "#16A34A" if device else "#64748B"
        
        md(f"""<div style="background:linear-gradient(135deg,#111827 0%,rgba(22,163,74,0.06) 100%);border:1px solid {gbrd};border-radius:18px;padding:18px;position:relative;min-height:240px">
        <div style="position:absolute;top:0;left:0;right:0;height:3px;background:{gc}"></div>
        <div style="display:flex;align-items:center;gap:6px;margin-bottom:6px">
        <div style="width:8px;height:8px;border-radius:50%;background:{sdot}"></div>
        <span style="font-size:10px;font-weight:600;color:{sdot};text-transform:uppercase">AirGuard Device</span></div>
        <p style="font-family:Sora,sans-serif;font-size:2.8rem;font-weight:800;color:{gc};line-height:1;margin:10px 0 0">{ppm_v}</p>
        <p style="font-size:10px;font-weight:600;color:#64748B;text-transform:uppercase;margin:4px 0 8px">Gas PPM · MQ2</p>
        <div style="height:1px;background:rgba(255,255,255,0.06);margin-bottom:8px"></div>
        <p style="font-size:11px;color:#4a5a7a">Risk: <strong style="color:{gc}">{grisk}</strong></p>
        </div>""")

    # ── MAP ──────────────────────────────────────────────────
    section(st, "📍 Live Sensor Network Map")
    m = folium.Map(location=[user_lat, user_lon], zoom_start=6, tiles="CartoDB dark_matter")
    # Add your markers logic here (keeping it simple for demo)
    st_folium(m, height=400, use_container_width=True)

    md(f"""<div style="text-align:center;padding:24px 0;margin-top:32px;border-top:1px solid rgba(255,255,255,0.05)">
    <p style="font-family:JetBrains Mono,monospace;font-size:11px;color:#3a4a6a;margin:0">
    AirGuard NG · {now_str} · Auto-refreshes every 10s</p></div>""")