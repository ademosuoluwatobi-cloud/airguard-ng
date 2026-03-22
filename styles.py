"""AirGuard NG — Shared Design System"""
import json, os, pandas as pd
from datetime import datetime

BASE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;500;600;700;800&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap');
html,body,[class*="css"],.stApp{font-family:'Inter',sans-serif!important;background-color:#07110C!important;color:#F8FAFC!important;}
.stApp{background:#07110C!important;}
.block-container{padding:2rem 2.5rem 4rem!important;max-width:1280px!important;}
#MainMenu,footer{visibility:hidden!important;}
[data-testid="stHeader"]{display:none!important;}
[data-testid="stToolbar"]{display:none!important;}
[data-testid="stDecoration"]{display:none!important;}
[data-testid="stSidebar"]{background:#0F172A!important;border-right:1px solid rgba(255,255,255,0.07)!important;}
[data-testid="stSidebarNavLink"]{color:#64748B!important;border-radius:8px!important;font-family:'Inter',sans-serif!important;font-size:14px!important;font-weight:500!important;padding:8px 12px!important;}
[data-testid="stSidebarNavLink"]:hover{background:rgba(255,255,255,0.05)!important;color:#F8FAFC!important;}
[data-testid="stSidebarNavLink"][aria-current="page"]{background:rgba(22,163,74,0.12)!important;color:#16A34A!important;font-weight:600!important;}
[data-testid="stSelectbox"]>div>div,[data-testid="stMultiSelect"]>div>div{background:#111827!important;border:1px solid rgba(255,255,255,0.12)!important;border-radius:12px!important;color:#F8FAFC!important;}
[data-testid="stSelectbox"] label,[data-testid="stMultiSelect"] label{font-size:11px!important;font-weight:600!important;color:#64748B!important;text-transform:uppercase!important;letter-spacing:.06em!important;}
[data-testid="stDownloadButton"] button,[data-testid="stButton"] button{background:rgba(22,163,74,0.12)!important;color:#16A34A!important;border:1px solid rgba(22,163,74,0.28)!important;border-radius:10px!important;font-family:'Inter',sans-serif!important;font-weight:600!important;}
[data-testid="stDataFrameResizable"]{border:1px solid rgba(255,255,255,0.08)!important;border-radius:12px!important;background:#111827!important;}
::-webkit-scrollbar{width:5px;}
::-webkit-scrollbar-track{background:#0F172A;}
::-webkit-scrollbar-thumb{background:rgba(255,255,255,0.12);border-radius:99px;}
@keyframes ag-pulse{0%,100%{box-shadow:0 0 0 0 rgba(22,163,74,.5);}50%{box-shadow:0 0 0 6px rgba(22,163,74,0);}}
.ag-live{display:inline-block;width:8px;height:8px;border-radius:50%;background:#16A34A;margin-right:6px;vertical-align:middle;animation:ag-pulse 2s infinite;}
@keyframes ag-danger{0%,100%{opacity:1;}50%{opacity:.5;}}
.ag-danger-pulse{animation:ag-danger 1.4s infinite;}
</style>
"""

# ── RISK TABLES ──────────────────────────────────────────────
RISK_COLORS = {
    "Good":"#16A34A","Moderate":"#EAB308",
    "Unhealthy for Sensitive Groups":"#F97316","Unhealthy":"#DC2626",
    "Very Unhealthy":"#9333EA","Hazardous":"#7E22CE","No Data":"#64748B",
}
RISK_BG = {
    "Good":"rgba(22,163,74,0.10)","Moderate":"rgba(234,179,8,0.10)",
    "Unhealthy for Sensitive Groups":"rgba(249,115,22,0.10)","Unhealthy":"rgba(220,38,38,0.10)",
    "Very Unhealthy":"rgba(147,51,234,0.10)","Hazardous":"rgba(126,34,206,0.10)","No Data":"rgba(100,116,139,0.10)",
}
RISK_BORDER = {
    "Good":"rgba(22,163,74,0.30)","Moderate":"rgba(234,179,8,0.30)",
    "Unhealthy for Sensitive Groups":"rgba(249,115,22,0.30)","Unhealthy":"rgba(220,38,38,0.30)",
    "Very Unhealthy":"rgba(147,51,234,0.30)","Hazardous":"rgba(126,34,206,0.30)","No Data":"rgba(100,116,139,0.30)",
}
RISK_ADVICE = {
    "Good":"Air quality is safe. All outdoor activities are appropriate today.",
    "Moderate":"Acceptable for most people. Sensitive individuals should reduce prolonged outdoor exertion.",
    "Unhealthy for Sensitive Groups":"People with asthma, COPD, heart disease, or diabetes should avoid outdoor activity.",
    "Unhealthy":"Everyone should reduce outdoor time. Patients must stay indoors with windows closed.",
    "Very Unhealthy":"Health emergency. Avoid all outdoor activity. Keep all windows and doors closed.",
    "Hazardous":"Emergency conditions. Do not go outside. Seek medical attention if breathing is difficult.",
    "No Data":"No recent sensor data available.",
}
CONDITION_ADVICE = {
    "Asthma":"Avoid outdoor activity between 7–10am (NO₂ peak) and 2–5pm (ozone peak). Always carry your reliever inhaler when HRS is above 40.",
    "COPD":"During harmattan season, treat any HRS above 30 as your personal danger threshold.",
    "Heart Disease":"Avoid outdoor activity during morning traffic (7–10am). Be especially cautious in evenings when generator CO emissions rise.",
    "Diabetes":"Long-term PM2.5 exposure worsens insulin resistance. Monitor blood sugar more frequently on high pollution days.",
    "Hypertension":"PM2.5 causes measurable blood pressure spikes within hours. Avoid prolonged outdoor time when HRS is above 40.",
    "Pregnancy":"There is no safe level of PM2.5 exposure during pregnancy. Avoid outdoor exposure on any day above WHO limits.",
    "Child Under 12":"Children's lungs are still developing. Treat the safe threshold as 50% of the adult WHO limit.",
    "None":"No specific condition. Exercise general air quality caution on days above Moderate.","":"",
}
CITY_RENAME = {
    "Other":"Lagos State","Lagos":"Lagos State","Abuja":"FCT Abuja",
    "Cross River":"Cross River State","Ogun":"Ogun State",
}

# Monitored states that have real sensor data
MONITORED_STATES = ["Lagos State","Ogun State","Cross River State","FCT Abuja"]

# State → approximate centre coords for map
STATE_COORDS = {
    "Lagos State":       (6.52,  3.38),
    "Ogun State":        (6.90,  3.35),
    "Cross River State": (5.03,  8.35),
    "FCT Abuja":         (9.07,  7.40),
}

# Default user location: University of Ibadan, First Gate
DEFAULT_LAT = 7.4381
DEFAULT_LON = 3.8966
DEFAULT_LOCATION = "University of Ibadan, First Gate"

GAS_LEVELS = [
    (150,  "GOOD",     "Safe",     "#16A34A","rgba(22,163,74,0.10)",  "rgba(22,163,74,0.30)",  "✅"),
    (200,  "MODERATE", "Caution",  "#EAB308","rgba(234,179,8,0.10)",  "rgba(234,179,8,0.30)",  "⚠️"),
    (250,  "POOR",     "Warning",  "#F97316","rgba(249,115,22,0.10)", "rgba(249,115,22,0.30)", "🔶"),
    (325,  "BAD",      "Danger",   "#DC2626","rgba(220,38,38,0.10)",  "rgba(220,38,38,0.30)",  "🚨"),
    (1023, "TOXIC",    "Critical", "#9333EA","rgba(147,51,234,0.10)", "rgba(147,51,234,0.30)", "☣️"),
]

def classify_gas(raw):
    if raw is None: return "No Data","#64748B","rgba(100,116,139,0.10)","rgba(100,116,139,0.30)","📡","No Data"
    r = int(raw)
    for mx,label,risk,color,bg,brd,icon in GAS_LEVELS:
        if r <= mx: return label,color,bg,brd,icon,risk
    return "TOXIC","#9333EA","rgba(147,51,234,0.10)","rgba(147,51,234,0.30)","☣️","Critical"

def gas_is_dangerous(raw):
    return raw is not None and int(raw) >= 250

def calculate_hrs(pm25):
    if pm25 is None or pm25 < 0: return 0,"No Data"
    elif pm25<=12:    return round((pm25/12)*20,1),"Good"
    elif pm25<=35.4:  return round(20+((pm25-12)/23.4)*20,1),"Moderate"
    elif pm25<=55.4:  return round(40+((pm25-35.4)/20)*20,1),"Unhealthy for Sensitive Groups"
    elif pm25<=150.4: return round(60+((pm25-55.4)/95)*20,1),"Unhealthy"
    elif pm25<=250.4: return round(80+((pm25-150.4)/100)*20,1),"Very Unhealthy"
    else:             return 100,"Hazardous"

def get_risk_level(pm25): return calculate_hrs(pm25)[1]

def load_device_data():
    if os.path.exists("esp32_data.json"):
        try:
            with open("esp32_data.json") as f:
                d = json.load(f)
            return d.get("latest"), d.get("readings",[])
        except Exception: pass
    return None, []

def get_user_location(st_session):
    """Returns (state, city, lat, lon, display_label) for the signed-in user."""
    state = st_session.get("user_state","")
    city  = st_session.get("user_city","")
    # Look up coords for known monitored states
    coords = STATE_COORDS.get(state)
    if coords:
        lat, lon = coords
    else:
        lat, lon = DEFAULT_LAT, DEFAULT_LON
    location_label = city if city else (state if state else DEFAULT_LOCATION)
    return state, city, lat, lon, location_label

def get_temp_hum_for_city(raw_df, city_key):
    """Returns (temp, hum) latest readings for a city from raw_data."""
    try:
        city_data = raw_df[raw_df["city"]==city_key]
        temp_r = city_data[city_data["parameter"]=="temperature"]
        hum_r  = city_data[city_data["parameter"]=="relativehumidity"]
        temp = round(temp_r.sort_values("timestamp").iloc[-1]["value"],1) if not temp_r.empty else None
        hum  = round(hum_r.sort_values("timestamp").iloc[-1]["value"],1)  if not hum_r.empty else None
        return temp, hum
    except Exception:
        return None, None

def get_all_city_options(user_state="", user_city=""):
    """Returns list of city display options including user's state if signed in."""
    options = list(MONITORED_STATES)
    if user_state and user_state not in options:
        label = user_state + (f" — {user_city}" if user_city else "") + " (Your Location 📍)"
        options.append(label)
    return options

# ── UI HELPERS ───────────────────────────────────────────────
def section(st, text):
    st.markdown(
        f'<p style="font-size:11px;font-weight:600;color:#64748B;text-transform:uppercase;'
        f'letter-spacing:.08em;margin:24px 0 12px;padding-bottom:8px;'
        f'border-bottom:1px solid rgba(255,255,255,0.06)">{text}</p>',
        unsafe_allow_html=True)

def badge(risk):
    c=RISK_COLORS.get(risk,"#64748B");bg=RISK_BG.get(risk,"rgba(100,116,139,0.10)");b=RISK_BORDER.get(risk,"rgba(100,116,139,0.30)")
    return f'<span style="display:inline-block;padding:3px 12px;border-radius:999px;font-size:11px;font-weight:600;background:{bg};color:{c};border:1px solid {b}">{risk}</span>'

def stat_html(label, value, unit, color):
    return (f'<div style="background:#111827;border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:18px 20px;text-align:center">'
            f'<p style="font-size:11px;font-weight:600;color:#64748B;text-transform:uppercase;letter-spacing:.07em;margin:0 0 4px">{label}</p>'
            f'<p style="font-family:Sora,sans-serif;font-size:2rem;font-weight:800;color:{color};line-height:1;margin:4px 0">{value}</p>'
            f'<p style="font-size:11px;color:#64748B;margin:0">{unit}</p></div>')

def metric_html(label, value, unit, color="#CBD5E1"):
    return (f'<div style="background:#111827;border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:14px 16px">'
            f'<p style="font-size:10px;font-weight:600;color:#64748B;text-transform:uppercase;letter-spacing:.06em;margin:0 0 6px">{label}</p>'
            f'<p style="font-family:JetBrains Mono,monospace;font-size:20px;font-weight:600;color:{color};margin:0">'
            f'{value} <span style="font-size:11px;color:#64748B">{unit}</span></p></div>')

def plotly_layout(height=300, legend=True):
    d = dict(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(17,24,39,0.9)",
        font=dict(family="Inter",color="#64748B",size=11),
        margin=dict(l=10,r=10,t=20,b=10), height=height,
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)",linecolor="rgba(255,255,255,0.05)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)",linecolor="rgba(255,255,255,0.05)"),
    )
    if legend:
        d["legend"] = dict(bgcolor="rgba(0,0,0,0)",font=dict(size=10),
                           orientation="h",yanchor="bottom",y=1.02,xanchor="left",x=0)
    return d

def device_status_bar(st, location_label=""):
    device, _ = load_device_data()
    now_str = datetime.now().strftime("%H:%M:%S")
    if device is None:
        st.markdown(
            f'<div style="background:#111827;border:1px solid rgba(255,255,255,0.07);'
            f'border-radius:12px;padding:10px 16px;margin-bottom:16px;font-size:13px;color:#4a5a7a">'
            f'📡 AirGuard Device not connected — run '
            f'<code style="background:rgba(255,255,255,0.05);padding:1px 6px;border-radius:4px">serial_reader.py</code>'
            f' to connect your Arduino</div>',
            unsafe_allow_html=True)
        return
    raw   = device.get("gas_raw",0)
    ppm   = device.get("gas_ppm",0)
    temp  = device.get("temperature","—")
    hum   = device.get("humidity","—")
    ts    = device.get("timestamp","")
    gl,gc,gbg,gbrd,gi,grisk = classify_gas(raw)
    danger = gas_is_dangerous(raw)
    try: ts_fmt = datetime.fromisoformat(ts).strftime("%H:%M:%S")
    except: ts_fmt = now_str
    loc_txt = f" · {location_label}" if location_label else ""
    if danger:
        st.markdown(
            f'<div class="ag-danger-pulse" style="background:rgba(220,38,38,0.15);'
            f'border:1px solid rgba(220,38,38,0.5);border-radius:12px;'
            f'padding:12px 18px;margin-bottom:12px;font-size:14px">'
            f'<strong style="color:#DC2626">🚨 GAS DANGER{loc_txt}:</strong>'
            f'<span style="color:#94A3B8;margin-left:8px">{ppm} PPM detected — {grisk}. '
            f'Open windows now. Check gas cylinder. Do not use electrical switches.</span></div>',
            unsafe_allow_html=True)
    st.markdown(
        f'<div style="background:{gbg};border:1px solid {gbrd};border-radius:12px;'
        f'padding:10px 16px;margin-bottom:16px;display:flex;align-items:center;'
        f'gap:16px;flex-wrap:wrap;font-size:13px">'
        f'<div style="display:flex;align-items:center;gap:6px">'
        f'<span class="ag-live"></span>'
        f'<span style="font-weight:600;color:{gc}">🔩 AirGuard Device{loc_txt}</span></div>'
        f'<span style="color:#64748B">|</span>'
        f'<span style="color:#94A3B8">Gas: <strong style="color:{gc}">{ppm} ppm</strong>'
        f'<span style="background:{gc}20;color:{gc};border:1px solid {gc}33;'
        f'padding:1px 8px;border-radius:999px;font-size:10px;font-weight:600;margin-left:6px">'
        f'{gi} {gl}</span></span>'
        f'<span style="color:#64748B">|</span>'
        f'<span style="color:#94A3B8">🌡 <strong style="color:#42a5f5">{temp}°C</strong></span>'
        f'<span style="color:#64748B">|</span>'
        f'<span style="color:#94A3B8">💧 <strong style="color:#26c6da">{hum}%</strong></span>'
        f'<span style="color:#64748B">|</span>'
        f'<span style="font-family:JetBrains Mono,monospace;font-size:10px;color:#3a4a6a">Updated {ts_fmt}</span>'
        f'</div>',
        unsafe_allow_html=True)
