"""AirGuard NG — Main Dashboard"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import folium, json, os
from streamlit_folium import st_folium
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
from styles import (
    BASE_CSS, RISK_COLORS, RISK_BG, RISK_BORDER, RISK_ADVICE, CONDITION_ADVICE,
    CITY_RENAME, MONITORED_STATES, STATE_COORDS, DEFAULT_LAT, DEFAULT_LON,
    section, badge, plotly_layout, calculate_hrs, load_device_data,
    classify_gas, gas_is_dangerous, device_status_bar,
    get_user_location, get_temp_hum_for_city,
)

st.set_page_config(page_title="AirGuard NG",page_icon="🛡️",layout="wide",initial_sidebar_state="expanded")
st.markdown(BASE_CSS, unsafe_allow_html=True)
st_autorefresh(interval=10000, key="ov_refresh")

def md(h): st.markdown(h, unsafe_allow_html=True)

# ── MOBILE + SIDEBAR NAVIGATION ─────────────────────────────
st.markdown("""
<style>
/* Sidebar nav styles */
.nav-section {
    font-size:10px;font-weight:600;color:#3a4a6a;text-transform:uppercase;
    letter-spacing:.09em;padding:14px 16px 6px;
}
.nav-link {
    display:flex;align-items:center;gap:10px;padding:9px 16px;
    border-radius:10px;margin:2px 8px;font-size:13px;font-weight:500;
    color:#64748B;text-decoration:none;
}
.nav-link:hover{background:rgba(255,255,255,0.05);color:#F8FAFC;}
.nav-link.active{background:rgba(22,163,74,0.12);color:#16A34A;font-weight:600;}
.nav-icon{font-size:15px;width:22px;text-align:center;}
.nav-divider{height:1px;background:rgba(255,255,255,0.06);margin:8px 16px;}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    # Logo
    st.markdown(
        '<div style="display:flex;align-items:center;gap:10px;padding:18px 16px 12px;'
        'border-bottom:1px solid rgba(255,255,255,0.07);margin-bottom:8px">'
        '<div style="width:32px;height:32px;background:rgba(22,163,74,0.12);'
        'border:1px solid rgba(22,163,74,0.28);border-radius:9px;display:flex;'
        'align-items:center;justify-content:center;font-size:16px">&#x1F6E1;&#xFE0F;</div>'
        '<span style="font-family:Sora,sans-serif;font-size:17px;font-weight:800;color:#F8FAFC">'
        'AirGuard <span style="color:#16A34A">NG</span></span></div>',
        unsafe_allow_html=True
    )
    # Nav links
    st.markdown(
        '<div class="nav-section">Dashboard</div>'
        '<a class="nav-link active" href="/" target="_self">'
        '<span class="nav-icon">&#x1F3E0;</span> Overview</a>'
        '<div class="nav-section">Air Quality</div>'
        '<a class="nav-link" href="/1_City_Deep_Dive" target="_self">'
        '<span class="nav-icon">&#x1F50D;</span> City Deep Dive</a>'
        '<a class="nav-link" href="/2_Compare_Cities" target="_self">'
        '<span class="nav-icon">&#x2696;&#xFE0F;</span> Compare Cities</a>'
        '<a class="nav-link" href="/3_Historical_Trends" target="_self">'
        '<span class="nav-icon">&#x1F4C8;</span> Historical Trends</a>'
        '<a class="nav-link" href="/4_Alerts_Log" target="_self">'
        '<span class="nav-icon">&#x1F6A8;</span> Alerts Log</a>'
        '<div class="nav-section">Health &amp; Safety</div>'
        '<a class="nav-link" href="/5_Health_Guide" target="_self">'
        '<span class="nav-icon">&#x1F3E5;</span> Health Guide</a>'
        '<a class="nav-link" href="/6_Best_Practices" target="_self">'
        '<span class="nav-icon">&#x2705;</span> Best Practices</a>'
        '<div class="nav-section">Hardware</div>'
        '<a class="nav-link" href="/8_Device" target="_self">'
        '<span class="nav-icon">&#x1F529;</span> AirGuard Device</a>'
        '<div class="nav-divider"></div>'
        '<div class="nav-section">Info</div>'
        '<a class="nav-link" href="/7_About" target="_self">'
        '<span class="nav-icon">&#x2139;&#xFE0F;</span> About</a>',
        unsafe_allow_html=True
    )
    # Device mini-badge
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    _dev, _ = load_device_data()
    if _dev:
        _ppm  = _dev.get("gas_ppm","—")
        _temp = _dev.get("temperature","—")
        st.markdown(
            f'<div style="margin:0 8px;background:rgba(22,163,74,0.08);'
            f'border:1px solid rgba(22,163,74,0.2);border-radius:10px;padding:10px 14px;font-size:12px">'
            f'<div style="display:flex;align-items:center;gap:6px;margin-bottom:5px">'
            f'<span style="width:7px;height:7px;border-radius:50%;background:#16A34A;display:inline-block"></span>'
            f'<span style="color:#16A34A;font-weight:600;font-size:11px">DEVICE LIVE</span></div>'
            f'<span style="color:#94A3B8">Gas {_ppm} ppm &nbsp;&#x1F321; {_temp}&#xB0;C</span></div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<div style="margin:0 8px;background:#111827;border:1px solid rgba(255,255,255,0.06);'
            'border-radius:10px;padding:10px 14px;font-size:11px;color:#3a4a6a">'
            '&#x1F4E1; Device not connected</div>',
            unsafe_allow_html=True
        )


# ── SESSION DEFAULTS ─────────────────────────────────────────
for k,v in [("onboarding_done",False),("user_name",""),("user_condition",""),("user_state",""),("user_city","")]:
    if k not in st.session_state: st.session_state[k] = v

ALL_STATES=["Abia","Adamawa","Akwa Ibom","Anambra","Bauchi","Bayelsa","Benue","Borno","Cross River","Delta","Ebonyi","Edo","Ekiti","Enugu","FCT Abuja","Gombe","Imo","Jigawa","Kaduna","Kano","Katsina","Kebbi","Kogi","Kwara","Lagos","Nasarawa","Niger","Ogun","Ondo","Osun","Oyo","Plateau","Rivers","Sokoto","Taraba","Yobe","Zamfara"]
CONDITIONS=["","Asthma","COPD","Heart Disease","Diabetes","Hypertension","Pregnancy","Child Under 12","None"]
COND_LBL={"":"My condition","Asthma":"Asthma","COPD":"COPD","Heart Disease":"Heart Disease","Diabetes":"Diabetes","Hypertension":"Hypertension","Pregnancy":"Pregnancy","Child Under 12":"Child Under 12","None":"No condition"}
BADGE_SHORT={"Good":"Good","Moderate":"Moderate","Unhealthy for Sensitive Groups":"Sensitive","Unhealthy":"Unhealthy","Very Unhealthy":"Very Unhealthy","Hazardous":"Hazardous","No Data":"No Data"}
DISPLAY={"Lagos State":"Lagos State","Ogun State":"Ogun State","Cross River State":"Cross River State","FCT Abuja":"FCT Abuja"}
STATE_KEY={"Lagos":"Lagos State","Ogun":"Ogun State","Cross River":"Cross River State","FCT Abuja":"FCT Abuja"}
FIXED_CARDS=[
    ("Lagos State","Lagos State","18+ sensors","Asthma & heart patients should limit outdoor activity today."),
    ("Ogun State","Ogun State","3 sensors","Generally safe. Sensitive individuals may reduce strenuous activity."),
    ("Cross River State","Cross River State","2 sensors","Chronic disease patients should avoid prolonged outdoor time."),
    ("FCT Abuja","FCT Abuja","3 sensors","Limit all outdoor activity. Keep windows closed today."),
]

@st.cache_data(ttl=300)
def load_state():
    try: return pd.read_csv("transformed_data.csv")
    except: return pd.DataFrame(columns=["city","hrs","risk_level","value","lat","lon"])
@st.cache_data(ttl=300)
def load_raw():
    try:
        raw=pd.read_csv("raw_data.csv"); raw["timestamp"]=pd.to_datetime(raw["timestamp"]); return raw
    except: return pd.DataFrame(columns=["city","location_name","parameter","value","timestamp","lat","lon"])
@st.cache_data(ttl=300)
def load_sensors():
    try: return pd.read_csv("sensor_locations.csv")
    except: return pd.DataFrame()

# ── ONBOARDING ───────────────────────────────────────────────
if not st.session_state.onboarding_done:
    _,col,_=st.columns([1,2,1])
    with col:
        md("""<div style="background:#111827;border:1px solid rgba(255,255,255,0.12);border-radius:24px;padding:36px 40px;margin-top:50px;box-shadow:0 20px 60px rgba(0,0,0,0.5)">
<div style="display:flex;align-items:center;gap:10px;margin-bottom:24px">
<div style="width:36px;height:36px;background:rgba(22,163,74,0.12);border:1px solid rgba(22,163,74,0.28);border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:18px">🛡️</div>
<span style="font-family:Sora,sans-serif;font-size:18px;font-weight:700;color:#F8FAFC">AirGuard <span style="color:#16A34A">NG</span></span></div>
<h2 style="font-family:Sora,sans-serif;font-size:22px;font-weight:700;color:#F8FAFC;letter-spacing:-.02em;margin:0 0 6px">Welcome to AirGuard NG</h2>
<p style="font-size:14px;color:#64748B;margin:0 0 24px;line-height:1.6">Set up your profile for personalised air quality insights and condition-aware health alerts across Nigeria.</p></div>""")
        md('<p style="font-size:11px;font-weight:600;color:#64748B;text-transform:uppercase;letter-spacing:.06em;margin:0 0 6px">YOUR NAME</p>')
        name=st.text_input("name",placeholder="e.g. Tobi Ademosu",label_visibility="collapsed")
        md('<p style="font-size:11px;font-weight:600;color:#64748B;text-transform:uppercase;letter-spacing:.06em;margin:16px 0 6px">HEALTH CONDITION</p>')
        condition=st.selectbox("condition",CONDITIONS,format_func=lambda x:COND_LBL.get(x,x),label_visibility="collapsed")
        cs,cc=st.columns(2)
        with cs:
            md('<p style="font-size:11px;font-weight:600;color:#64748B;text-transform:uppercase;letter-spacing:.06em;margin:16px 0 6px">YOUR STATE</p>')
            state=st.selectbox("state",[""]+ALL_STATES,format_func=lambda x:"Select state" if x=="" else x,label_visibility="collapsed")
        with cc:
            md('<p style="font-size:11px;font-weight:600;color:#64748B;text-transform:uppercase;letter-spacing:.06em;margin:16px 0 6px">CITY / LGA</p>')
            city=st.text_input("city",placeholder="e.g. Yaba",label_visibility="collapsed")
        md("<br>")
        if st.button("Continue to dashboard →",use_container_width=True):
            st.session_state.user_name=name.strip() or "Friend"
            st.session_state.user_condition=condition
            st.session_state.user_state=state
            st.session_state.user_city=city.strip()
            st.session_state.onboarding_done=True
            st.rerun()

elif st.session_state.onboarding_done:
    user_name      = st.session_state.user_name
    user_condition = st.session_state.user_condition
    user_state     = st.session_state.user_state
    user_city      = st.session_state.user_city
    user_state_s,user_city_s,user_lat,user_lon,user_loc_label = get_user_location(st.session_state)
    now_str = datetime.now().strftime("%d %b %Y, %H:%M")
    hour    = datetime.now().hour
    greeting= "Good morning" if hour<12 else "Good afternoon" if hour<17 else "Good evening"
    fn      = user_name.split()[0]

    df   = load_state()
    raw  = load_raw()
    slocs= load_sensors()
    device, _ = load_device_data()

    worst     = df.loc[df["hrs"].idxmax()]
    worst_col = RISK_COLORS.get(worst["risk_level"],"#64748B")
    worst_bg  = RISK_BG.get(worst["risk_level"],"rgba(100,116,139,0.10)")
    worst_brd = RISK_BORDER.get(worst["risk_level"],"rgba(100,116,139,0.30)")
    worst_lbl = DISPLAY.get(worst["city"],worst["city"])

    # User's nearest monitored state for HRS
    user_key = STATE_KEY.get(user_state,"")
    ur = df[df["city"]==user_key] if user_key else pd.DataFrame()
    user_hrs  = ur.iloc[0]["hrs"]  if not ur.empty else (device.get("gas_ppm","—") if device else "—")
    user_risk = ur.iloc[0]["risk_level"] if not ur.empty else "No Data"
    user_col  = RISK_COLORS.get(user_risk,"#64748B")
    cond_adv  = CONDITION_ADVICE.get(user_condition,"")
    hero_sub  = (cond_adv[:130]+"…" if len(cond_adv)>130 else cond_adv) if cond_adv else "Monitor real-time air quality across Nigeria and get personalised health guidance for your location."

    # ── HEADER ───────────────────────────────────────────────
    md(f"""<div style="display:flex;align-items:center;gap:12px;margin-bottom:20px;padding-bottom:18px;border-bottom:1px solid rgba(255,255,255,0.06)">
  <div style="width:38px;height:38px;background:rgba(22,163,74,0.12);border:1px solid rgba(22,163,74,0.28);border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:19px">🛡️</div>
  <div><p style="font-family:Sora,sans-serif;font-size:20px;font-weight:800;color:#F8FAFC;letter-spacing:-.01em;margin:0;line-height:1.1">AirGuard <span style="color:#16A34A">NG</span></p>
  <p style="font-size:12px;color:#64748B;margin:0">Real-time Air Quality and Health Risk Intelligence — {user_state or 'Nigeria'}</p></div>
  <div style="margin-left:auto;display:flex;align-items:center;gap:12px">
    <div style="background:#111827;border:1px solid rgba(255,255,255,0.08);border-radius:999px;padding:6px 14px 6px 8px;display:flex;align-items:center;gap:8px">
      <span class="ag-live"></span><span style="font-size:13px;font-weight:500;color:#CBD5E1">{user_name}</span></div>
    <span style="font-family:JetBrains Mono,monospace;font-size:11px;color:#3a4a6a">{now_str}</span>
  </div></div>""")

    # ── DEVICE BAR ───────────────────────────────────────────
    device_status_bar(st, location_label=user_state or "")

    # ── GAS DANGER BANNER ────────────────────────────────────
    if device and gas_is_dangerous(int(device.get("gas_raw",0) or 0)):
        ppm=device.get("gas_ppm",0); gl,gc,_,_,gi,grisk=classify_gas(int(device.get("gas_raw",0)))
        md(f"""<div class="ag-danger-pulse" style="background:rgba(220,38,38,0.15);border:2px solid rgba(220,38,38,0.6);border-radius:14px;padding:16px 20px;margin-bottom:16px">
<p style="font-family:Sora,sans-serif;font-size:16px;font-weight:800;color:#DC2626;margin:0 0 6px">🚨 GAS DANGER — AirGuard Device · {user_state}</p>
<p style="font-size:14px;color:#94A3B8;margin:0">Indoor sensor reading <strong style="color:#DC2626">{ppm} PPM</strong> — {grisk}. Open all windows immediately. Do not use electrical switches. Turn off gas at the cylinder.</p></div>""")

    # ── AQ ALERT ─────────────────────────────────────────────
    if worst["risk_level"] in ["Unhealthy","Very Unhealthy","Hazardous"]:
        md(f"""<div style="background:{worst_bg};border:1px solid {worst_brd};border-radius:12px;padding:14px 18px;margin-bottom:20px;font-size:14px">
<span style="font-size:1.2rem">🚨</span><strong style="color:{worst_col};margin-left:6px">{worst_lbl} Air Quality Alert:</strong>
<span style="color:#94A3B8;margin-left:6px">{RISK_ADVICE.get(worst['risk_level'],'')}</span></div>""")

    # ── PERSONALISED HERO ────────────────────────────────────
    # Location-specific heading
    loc_heading = f"{user_state} Air Quality" if user_state else "Nigeria Air Quality Overview"
    loc_sub_heading = f"{user_city}, {user_state}" if user_city and user_state else (user_state or "Nigeria")

    md(f"""<div style="background:linear-gradient(135deg,rgba(5,46,22,0.85) 0%,rgba(15,23,42,0.9) 100%);border:1px solid rgba(22,163,74,0.28);border-radius:22px;padding:30px 36px;margin-bottom:28px;display:flex;align-items:center;justify-content:space-between;gap:24px;flex-wrap:wrap;position:relative;overflow:hidden">
  <div style="position:absolute;top:-60px;right:-60px;width:260px;height:260px;background:radial-gradient(circle,rgba(22,163,74,0.09) 0%,transparent 70%);pointer-events:none"></div>
  <div style="flex:1;min-width:260px">
    <p style="font-size:12px;font-weight:600;color:#16A34A;text-transform:uppercase;letter-spacing:.08em;margin:0 0 6px">{greeting}, {fn} · {loc_sub_heading}</p>
    <p style="font-family:Sora,sans-serif;font-size:24px;font-weight:700;color:#F8FAFC;letter-spacing:-.02em;line-height:1.25;margin:0 0 8px">{loc_heading}</p>
    <p style="font-size:14px;color:#64748B;max-width:440px;line-height:1.6;margin:0">{hero_sub}</p>
  </div>
  <div style="background:rgba(22,163,74,0.10);border:1px solid rgba(22,163,74,0.28);border-radius:14px;padding:16px 22px;min-width:190px;flex-shrink:0;text-align:right">
    <p style="font-size:11px;font-weight:600;color:#16A34A;text-transform:uppercase;letter-spacing:.07em;margin:0 0 4px">📍 {user_state or 'Nigeria'} Risk</p>
    <p style="font-family:Sora,sans-serif;font-size:2.5rem;font-weight:800;color:{user_col};letter-spacing:-.03em;line-height:1;margin:0 0 4px">{user_hrs}</p>
    <p style="font-size:12px;color:#64748B;margin:0 0 8px">{user_city or user_state or 'Nigeria'}</p>
    <span class="ag-live"></span><span style="font-family:JetBrains Mono,monospace;font-size:10px;color:#3a4a6a">Updated {now_str}</span>
  </div>
</div>""")

    # ── 5 CARDS (4 states + device) ──────────────────────────
    section(st,"Active Monitoring Locations")
    FULL={"Good":"Good","Moderate":"Moderate — Acceptable","Unhealthy for Sensitive Groups":"Unhealthy for Sensitive Groups","Unhealthy":"Unhealthy — Everyone at risk","Very Unhealthy":"Very Unhealthy","Hazardous":"Hazardous","No Data":"No Data"}
    c1,c2,c3,c4,c5=st.columns(5)

    for col,(key,label,sensors_lbl,note) in zip([c1,c2,c3,c4],FIXED_CARDS):
        row=df[df["city"]==key]
        if row.empty: hrs,risk,pm25v="—","No Data","—"
        else: r=row.iloc[0]; hrs,risk,pm25v=r["hrs"],r["risk_level"],round(r["value"],1)
        color=RISK_COLORS.get(risk,"#64748B"); bg=RISK_BG.get(risk,"rgba(100,116,139,0.10)"); brd=RISK_BORDER.get(risk,"rgba(100,116,139,0.30)")
        short=BADGE_SHORT.get(risk,risk)
        # Get temp and humidity for this state
        t,h = get_temp_hum_for_city(raw,key)
        temp_str = f'<span style="color:#42a5f5">🌡 {t}°C</span>' if t is not None else '<span style="color:#3a4a6a">🌡 —</span>'
        hum_str  = f'<span style="color:#26c6da">💧 {h}%</span>'  if h is not None else '<span style="color:#3a4a6a">💧 —</span>'
        # Show device pin if user's state roughly matches
        dev_pin=""
        if user_state and (user_state.split()[0].lower() in key.lower() or key.lower() in user_state.lower()):
            dev_pin='<span style="background:rgba(249,115,22,0.15);color:#F97316;border:1px solid rgba(249,115,22,0.3);padding:1px 7px;border-radius:999px;font-size:10px;font-weight:600;margin-left:6px">📍 You</span>'
        with col:
            md(f"""<div style="background:{bg};border:1px solid {brd};border-radius:18px;padding:18px;position:relative;overflow:hidden;min-height:260px">
<div style="position:absolute;top:0;left:0;right:0;height:3px;background:{color}"></div>
<p style="font-family:Sora,sans-serif;font-size:13px;font-weight:700;color:#CBD5E1;margin:0 0 2px">{label}{dev_pin}</p>
<p style="font-size:11px;color:#64748B;margin:0 0 8px">{sensors_lbl}</p>
<span style="background:{color}20;color:{color};border:1px solid {color}33;padding:2px 9px;border-radius:999px;font-size:10px;font-weight:600">{short}</span>
<p style="font-family:Sora,sans-serif;font-size:2.8rem;font-weight:800;color:{color};line-height:1;letter-spacing:-.04em;margin:10px 0 0">{hrs}</p>
<p style="font-size:10px;font-weight:600;color:#64748B;text-transform:uppercase;letter-spacing:.07em;margin:4px 0 8px">Health Risk Score</p>
<div style="height:1px;background:rgba(255,255,255,0.06);margin-bottom:8px"></div>
<p style="font-family:JetBrains Mono,monospace;font-size:12px;color:#64748B;margin:0 0 4px">PM2.5 · {pm25v} µg/m³</p>
<p style="font-size:12px;color:{color};margin:0 0 6px">{FULL.get(risk,risk)}</p>
<p style="font-size:12px;color:#4a5a7a;margin:0 0 6px">{temp_str} &nbsp; {hum_str}</p>
<p style="font-size:11px;color:#4a5a7a;line-height:1.5;margin:0">{note}</p>
</div>""")

    # 5th card — device
    with c5:
        gas_raw=int(device.get("gas_raw",0) or 0) if device else None
        ppm_v=device.get("gas_ppm","—") if device else "—"
        tmp_v=device.get("temperature","—") if device else "—"
        hmd_v=device.get("humidity","—") if device else "—"
        ts_d="—"
        if device:
            try: ts_d=datetime.fromisoformat(device.get("timestamp","")).strftime("%H:%M:%S")
            except: pass
        gl,gc,gbg,gbrd,gi,grisk=classify_gas(gas_raw)
        sdot="#16A34A" if device else "#64748B"
        slbl="Live" if device else "Not connected"
        city_label=user_city if user_city else (user_state if user_state else "Location not set")
        md(f"""<div style="background:linear-gradient(135deg,#111827 0%,rgba(249,115,22,0.06) 100%);border:1px solid {gbrd};border-radius:18px;padding:18px;position:relative;overflow:hidden;min-height:260px">
<div style="position:absolute;top:0;left:0;right:0;height:3px;background:{gc}"></div>
<div style="display:flex;align-items:center;gap:6px;margin-bottom:6px">
<div style="width:8px;height:8px;border-radius:50%;background:{sdot}"></div>
<span style="font-size:10px;font-weight:600;color:{sdot};text-transform:uppercase;letter-spacing:.06em">AirGuard Device · {slbl}</span></div>
<p style="font-family:JetBrains Mono,monospace;font-size:10px;color:#64748B;margin:0 0 6px">airguard-uno-01 · 📍{city_label}</p>
<span style="background:{gc}20;color:{gc};border:1px solid {gc}33;padding:2px 9px;border-radius:999px;font-size:10px;font-weight:600">{gi} {gl}</span>
<p style="font-family:Sora,sans-serif;font-size:2.8rem;font-weight:800;color:{gc};line-height:1;letter-spacing:-.04em;margin:10px 0 0">{ppm_v}</p>
<p style="font-size:10px;font-weight:600;color:#64748B;text-transform:uppercase;letter-spacing:.07em;margin:4px 0 8px">Gas PPM · MQ2 Sensor</p>
<div style="height:1px;background:rgba(255,255,255,0.06);margin-bottom:8px"></div>
<p style="font-size:12px;color:#64748B;margin:0 0 4px">🌡 <span style="color:#42a5f5;font-weight:600">{tmp_v}°C</span> &nbsp; 💧 <span style="color:#26c6da;font-weight:600">{hmd_v}%</span></p>
<p style="font-size:11px;color:#4a5a7a;margin:4px 0 0">Risk: <strong style="color:{gc}">{grisk}</strong></p>
<p style="font-family:JetBrains Mono,monospace;font-size:10px;color:#3a4a6a;margin:6px 0 0">Last: {ts_d}</p>
</div>""")

    md("<br>")

    # ── MAP ──────────────────────────────────────────────────
    col_map,col_trend=st.columns([1.15,0.85])
    with col_map:
        section(st,"📍 Sensor Network Map — All Active Locations")
        map_data=slocs.copy() if not slocs.empty else pd.DataFrame()
        if map_data.empty:
            pm25m=raw[raw["parameter"]=="pm25"].copy()
            map_data=(pm25m.sort_values("timestamp",ascending=False).groupby("location_name").first().reset_index()[["location_name","city","value","lat","lon","timestamp"]])
            map_data[["hrs","risk_level"]]=map_data["value"].apply(lambda v: pd.Series(calculate_hrs(float(v))))

        # Centre map on user's location
        map_center_lat = user_lat
        map_center_lon = user_lon
        m=folium.Map(location=[map_center_lat,map_center_lon],zoom_start=6,tiles="CartoDB dark_matter")

        for _,sr in map_data.iterrows():
            color=RISK_COLORS.get(sr.get("risk_level","No Data"),"#64748B")
            pv=round(float(sr["value"]),1) if pd.notna(sr["value"]) else "—"
            hv=sr.get("hrs","—"); rv=sr.get("risk_level","—")
            tv=f'{round(float(sr["temperature"]),1)} °C' if "temperature" in sr and pd.notna(sr.get("temperature")) else "—"
            huv=f'{round(float(sr["relativehumidity"]),1)} %' if "relativehumidity" in sr and pd.notna(sr.get("relativehumidity")) else "—"
            popup=f"""<div style='font-family:sans-serif;background:#111827;color:#F8FAFC;border-radius:10px;padding:12px;min-width:190px;font-size:13px'>
<b style='color:{color}'>{sr['location_name']}</b><br><span style='font-size:11px;color:#64748B'>{sr.get('city','')}</span><br>
<span style='font-size:18px;font-weight:700;color:{color}'>HRS: {hv}</span><br>PM2.5: {pv} µg/m³<br>Temp: {tv} · Hum: {huv}<br><span style='color:{color}'>{rv}</span></div>"""
            folium.CircleMarker(location=[float(sr["lat"]),float(sr["lon"])],radius=9,color=color,fill=True,fill_color=color,fill_opacity=0.85,weight=2,popup=folium.Popup(popup,max_width=240),tooltip=f"{sr['location_name']} · PM2.5 {pv} µg/m³ · {rv}").add_to(m)

        # User's location marker
        city_display = user_city if user_city else (user_state if user_state else "Your Location")
        folium.Marker(
            location=[user_lat, user_lon],
            popup=folium.Popup(f"""<div style='font-family:sans-serif;background:#111827;color:#F8FAFC;border-radius:10px;padding:12px;min-width:180px'>
<b style='color:#16A34A'>📍 {city_display}</b><br>
<span style='font-size:11px;color:#64748B'>{user_state}</span><br>
Your registered location</div>""",max_width=220),
            tooltip=f"📍 {city_display} — Your Location",
            icon=folium.Icon(color="green",icon="home"),
        ).add_to(m)

        # Device marker
        if device:
            gp=float(device.get("gas_ppm",0) or 0); gl2,gc2,_,_,gi2,_=classify_gas(int(device.get("gas_raw",0) or 0))
            folium.Marker(location=[user_lat+0.02,user_lon+0.02],
                popup=folium.Popup(f"""<div style='font-family:sans-serif;background:#111827;color:#F8FAFC;border-radius:10px;padding:12px;min-width:180px'><b style='color:{gc2}'>🔩 AirGuard Device</b><br>{city_display}<br>Gas: {gp} ppm · {gl2}<br>Temp: {device.get('temperature','—')} °C<br>Hum: {device.get('humidity','—')} %</div>""",max_width=220),
                tooltip=f"AirGuard Device · {gp} ppm · {gl2}",icon=folium.Icon(color="orange",icon="star")).add_to(m)

        md(f'<p style="font-family:JetBrains Mono,monospace;font-size:11px;color:#64748B;margin:0 0 8px"><span class="ag-live"></span>{len(map_data)} sensors live · 📍 Map centred on {city_display}</p>')
        st_folium(m,height=440,use_container_width=True)

    # ── TREND ────────────────────────────────────────────────
    with col_trend:
        section(st,"📈 PM2.5 Trend — Last 24 Hours")
        pm25_raw=raw[raw["parameter"]=="pm25"].copy()
        CITY_LBL={"Lagos State":"Lagos State","Ogun State":"Ogun State","Cross River State":"Cross River State","FCT Abuja":"FCT Abuja"}
        available=[c for c in CITY_LBL if c in pm25_raw["city"].unique()]
        options=[CITY_LBL[c] for c in available]
        lbl2key=dict(zip(options,available))

        # Add user's state to dropdown if not already in monitored list
        user_in_list = any(user_state.split()[0].lower() in o.lower() for o in options) if user_state else True
        default_idx=0
        if user_state and not user_in_list:
            user_option=f"{user_state}{' — '+user_city if user_city else ''} (Your Location 📍)"
            options.append(user_option)
            lbl2key[user_option] = None  # no sensor data — will show device data
            default_idx=len(options)-1
        elif user_state:
            for i,o in enumerate(options):
                if user_state.split()[0].lower() in o.lower():
                    default_idx=i; break

        if not options:
            md('<div style="background:#111827;border:1px solid rgba(255,255,255,0.07);border-radius:12px;padding:32px;text-align:center;color:#64748B">No PM2.5 data. Run extraction.py first.</div>')
        else:
            sel=st.selectbox("",options,index=default_idx,label_visibility="collapsed")
            sel_key=lbl2key.get(sel)

            if sel_key is None:
                # User's own state — show device data if available
                if device:
                    _, hist = load_device_data()
                    if hist:
                        hdf=pd.DataFrame(hist); hdf["timestamp"]=pd.to_datetime(hdf["timestamp"]); hdf=hdf.sort_values("timestamp")
                        fig=go.Figure()
                        fig.add_trace(go.Scatter(x=hdf["timestamp"],y=hdf["gas_ppm"],mode="lines",name="Gas PPM (Indoor)",line=dict(color="#F97316",width=2)))
                        lay=plotly_layout(height=380); lay["yaxis"]["title"]="Gas PPM"; lay["yaxis"]["title_font"]=dict(size=10,color="#4a5a7a")
                        fig.update_layout(**lay); st.plotly_chart(fig,use_container_width=True)
                        md(f'<p style="font-size:12px;color:#64748B;margin-top:8px">Showing indoor AirGuard device readings for {user_state}. No OpenAQ sensors in this state yet.</p>')
                    else:
                        md(f'<div style="background:#111827;border:1px solid rgba(255,255,255,0.07);border-radius:12px;padding:24px;text-align:center;color:#64748B">No OpenAQ sensors in {user_state}. Device readings will appear here once your sensor has history.</div>')
                else:
                    md(f'<div style="background:#111827;border:1px solid rgba(255,255,255,0.07);border-radius:12px;padding:24px;text-align:center;color:#64748B">No sensor data available for {user_state} yet.</div>')
            else:
                cdata=pm25_raw[pm25_raw["city"]==sel_key].sort_values("timestamp")
                if cdata.empty:
                    md('<div style="background:#111827;border:1px solid rgba(255,255,255,0.07);border-radius:12px;padding:32px;text-align:center;color:#64748B">No data for this location.</div>')
                else:
                    fig=go.Figure()
                    for loc in cdata["location_name"].unique():
                        ld=(cdata[cdata["location_name"]==loc].set_index("timestamp").resample("30min")["value"].mean().dropna().reset_index())
                        fig.add_trace(go.Scatter(x=ld["timestamp"],y=ld["value"],mode="lines",name=loc,line=dict(width=1.8),opacity=0.88))
                    for y,tc,lbl in [(15,"#16A34A","WHO Safe (15)"),(35.4,"#F97316","Moderate (35.4)"),(55.4,"#DC2626","Unhealthy (55.4)")]:
                        fig.add_hline(y=y,line_dash="dot",line_color=tc,line_width=1,annotation_text=lbl,annotation_font_size=9,annotation_font_color=tc)
                    lay=plotly_layout(height=380); lay["yaxis"]["title"]="PM2.5 (µg/m³)"; lay["yaxis"]["title_font"]=dict(size=10,color="#4a5a7a")
                    fig.update_layout(**lay); st.plotly_chart(fig,use_container_width=True)

    md("<br>")

    # ── BAR CHART ────────────────────────────────────────────
    section(st,"📊 State Risk Comparison")
    sdf=df.sort_values("hrs",ascending=False).copy(); sdf["label"]=sdf["city"].map(lambda x:DISPLAY.get(x,x))
    # Add user's state bar if device data available and state not in monitored list
    if device and user_state and user_state not in [r["city"] for _,r in df.iterrows()]:
        gl_b,gc_b,_,_,gi_b,grisk_b=classify_gas(int(device.get("gas_raw",0) or 0))
        ppm_hrs=min(100,round(float(device.get("gas_ppm",0) or 0)/5,1))  # rough HRS estimate from PPM
        extra=pd.DataFrame([{"city":user_state,"hrs":ppm_hrs,"risk_level":grisk_b,"value":device.get("gas_ppm",0),"label":f"{user_state} (Device 📍)"}])
        sdf=pd.concat([sdf,extra],ignore_index=True).sort_values("hrs",ascending=False)

    fig2=go.Figure(go.Bar(x=sdf["label"],y=sdf["hrs"],marker=dict(color=[RISK_COLORS.get(r,"#64748B") for r in sdf["risk_level"]],opacity=0.85,line=dict(width=0)),text=[f"HRS {h}" for h in sdf["hrs"]],textposition="outside",textfont=dict(family="JetBrains Mono",size=11,color="#94A3B8")))
    lay2=plotly_layout(height=320,legend=False); lay2["yaxis"]["title"]="Health Risk Score"; lay2["yaxis"]["title_font"]=dict(size=10,color="#4a5a7a"); lay2["yaxis"]["range"]=[0,max(sdf["hrs"])*1.28]
    fig2.update_layout(**lay2); st.plotly_chart(fig2,use_container_width=True)

    # ── HEALTH CARDS ─────────────────────────────────────────
    section(st,"🏥 Personalised Health Recommendations")
    avg_pm25=round(df["value"].mean(),1)
    HCARDS=[
        ("⏰","rgba(249,115,22,0.12)","Best time to go outside",f"For {user_state or 'Nigeria'} today","The safest outdoor window is before 7:00 AM or after 7:00 PM when traffic-related PM2.5 and NO₂ are at their lowest."),
        ("🫁","rgba(220,38,38,0.12)","Highest risk today",f"Alert: {worst_lbl}",f"{worst_lbl} has HRS {worst['hrs']} today. {RISK_ADVICE.get(worst['risk_level'],'')[:100]}"),
        ("💊","rgba(22,163,74,0.12)","Medication reminder","Pre-emptive dosing" if user_condition else "General guidance",CONDITION_ADVICE.get(user_condition,"Check AirGuard NG before going outside every morning. This single habit could prevent a hospitalisation.")[:130]),
        ("🏥","rgba(14,165,233,0.12)","For your doctor visit","Weekly exposure summary",f"Average PM2.5 across monitored locations: {avg_pm25} µg/m³ — {round(avg_pm25/15,1)}× the WHO safe annual limit. Show this to your doctor."),
    ]
    h1,h2,h3,h4=st.columns(4)
    for col,(icon,ibg,title,sub,body) in zip([h1,h2,h3,h4],HCARDS):
        with col:
            md(f"""<div style="background:#111827;border:1px solid rgba(255,255,255,0.07);border-radius:16px;padding:18px">
<div style="display:flex;align-items:flex-start;gap:10px;margin-bottom:10px">
<div style="width:34px;height:34px;border-radius:9px;background:{ibg};display:flex;align-items:center;justify-content:center;font-size:16px;flex-shrink:0">{icon}</div>
<div><p style="font-family:Sora,sans-serif;font-size:13px;font-weight:700;color:#F8FAFC;letter-spacing:-.01em;margin:0">{title}</p>
<p style="font-size:11px;color:#64748B;margin:2px 0 0">{sub}</p></div></div>
<p style="font-size:13px;color:#94A3B8;line-height:1.65;margin:0">{body}</p></div>""")

    md(f"""<div style="text-align:center;padding:24px 0;margin-top:32px;border-top:1px solid rgba(255,255,255,0.05)">
<p style="font-family:JetBrains Mono,monospace;font-size:11px;color:#3a4a6a;margin:0">
AirGuard NG · OpenAQ v3 · WHO 2021 · 3MTT NextGen · Environment Pillar · Nigeria 2026 · {now_str} · Auto-refreshes every 10s</p></div>""")

