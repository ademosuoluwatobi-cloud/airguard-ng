import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from styles import render_nav_button
from styles import *

st.set_page_config(page_title="AirGuard Device — AirGuard NG", page_icon="🔩", layout="wide")
st.markdown(BASE_CSS, unsafe_allow_html=True)
st_autorefresh(interval=5000, key="device_refresh")   # refresh every 5 seconds on device page

def md(h): st.markdown(h, unsafe_allow_html=True)

user_state = st.session_state.get("user_state", "")

# ── DEVICE STATUS BAR ────────────────────────────────────────
device_status_bar(st, location_label=user_state)
render_nav_button(st)

md('<p style="font-family:Sora,sans-serif;font-size:26px;font-weight:800;color:#F8FAFC;letter-spacing:-.02em;margin:0 0 4px">🔩 AirGuard Device</p>')
md('<p style="font-size:14px;color:#64748B;margin:0 0 24px;line-height:1.6">Indoor air quality monitor · Arduino Uno + MQ2 + DHT11 + OLED · Real-time gas leakage detection</p>')

# ── LOAD DEVICE DATA ─────────────────────────────────────────
device, history = load_device_data()

GAS_SCALE = [
    (150,  "Safe",     "#16A34A", "rgba(22,163,74,0.10)",  "rgba(22,163,74,0.30)",  "✅", "Indoor air is clean. No harmful gases detected. All occupants are safe."),
    (200,  "Caution",  "#EAB308", "rgba(234,179,8,0.10)",  "rgba(234,179,8,0.30)",  "⚠️", "Slightly elevated gas levels. Ensure room is well ventilated. Check gas cylinder seal."),
    (250,  "Warning",  "#F97316", "rgba(249,115,22,0.10)", "rgba(249,115,22,0.30)", "🔶", "Gas levels are rising. Open all windows and doors immediately. Check for leaks."),
    (325,  "Danger",   "#DC2626", "rgba(220,38,38,0.10)",  "rgba(220,38,38,0.30)",  "🚨", "DANGER — High gas concentration. Evacuate the room. Turn off gas cylinder. Do NOT use any electrical switches."),
    (1023, "Critical", "#9333EA", "rgba(147,51,234,0.10)", "rgba(147,51,234,0.30)", "☣️", "CRITICAL — Extreme gas concentration. Leave the building immediately. Call emergency services."),
]

if device is None:
    # ── NOT CONNECTED ────────────────────────────────────────
    md("""
<div style="background:rgba(100,116,139,0.10);border:1px solid rgba(100,116,139,0.28);
border-radius:16px;padding:28px;text-align:center;margin-bottom:20px">
    <p style="font-size:2rem;margin:0 0 10px">📡</p>
    <p style="font-family:Sora,sans-serif;font-size:16px;font-weight:700;color:#CBD5E1;margin:0 0 6px">
    AirGuard Device Not Connected</p>
    <p style="font-size:14px;color:#64748B;margin:0">
    Run <code style="background:rgba(255,255,255,0.07);padding:2px 8px;border-radius:4px">
    python serial_reader.py</code> in a terminal and connect your Arduino via USB.
    This page auto-refreshes every 5 seconds.</p>
</div>
""")

else:
    # ── LIVE READINGS ────────────────────────────────────────
    raw_g = int(device.get("gas_raw", 0) or 0)
    ppm   = device.get("gas_ppm",      0)
    temp  = device.get("temperature",  0)
    hum   = device.get("humidity",     0)
    did   = device.get("device_id",    "airguard-uno-01")
    risk  = device.get("risk_level",   "Safe")
    ts_raw = device.get("timestamp",   "")

    try:
        ts_d = datetime.fromisoformat(ts_raw).strftime("%d %b %Y, %H:%M:%S")
    except Exception:
        ts_d = "—"

    gl, gc, gbg, gbrd, gi, grisk = classify_gas(raw_g)
    danger = gas_is_dangerous(raw_g)

    # DANGER FLASHING BANNER
    if danger:
        md(f"""
<div class="ag-danger-pulse" style="background:rgba(220,38,38,0.18);
border:2px solid rgba(220,38,38,0.65);border-radius:16px;
padding:20px 24px;margin-bottom:20px">
    <p style="font-family:Sora,sans-serif;font-size:20px;font-weight:800;
    color:#DC2626;margin:0 0 8px">🚨 GAS DANGER ALERT — Immediate Action Required</p>
    <p style="font-size:14px;color:#94A3B8;margin:0 0 12px">
    Your AirGuard sensor is reading <strong style="color:#DC2626">{ppm} PPM</strong> —
    <strong style="color:#DC2626">{grisk}</strong> level detected{' in ' + user_state if user_state else ''}.</p>
    <div style="display:flex;gap:12px;flex-wrap:wrap">
        <span style="background:rgba(220,38,38,0.15);color:#DC2626;border:1px solid rgba(220,38,38,0.3);padding:4px 14px;border-radius:999px;font-size:13px;font-weight:600">• Open ALL windows now</span>
        <span style="background:rgba(220,38,38,0.15);color:#DC2626;border:1px solid rgba(220,38,38,0.3);padding:4px 14px;border-radius:999px;font-size:13px;font-weight:600">• Do NOT use electrical switches</span>
        <span style="background:rgba(220,38,38,0.15);color:#DC2626;border:1px solid rgba(220,38,38,0.3);padding:4px 14px;border-radius:999px;font-size:13px;font-weight:600">• Turn off gas cylinder</span>
        <span style="background:rgba(220,38,38,0.15);color:#DC2626;border:1px solid rgba(220,38,38,0.3);padding:4px 14px;border-radius:999px;font-size:13px;font-weight:600">• Evacuate the room</span>
    </div>
</div>
""")

    # ── 4 METRIC CARDS ───────────────────────────────────────
    section(st, "Live Sensor Readings")
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        md(f"""
<div style="background:{gbg};border:1px solid {gbrd};border-radius:16px;
padding:22px;text-align:center;position:relative;overflow:hidden">
    <div style="position:absolute;top:0;left:0;right:0;height:3px;background:{gc}"></div>
    <p style="font-size:11px;font-weight:600;color:#64748B;text-transform:uppercase;
    letter-spacing:.07em;margin:0 0 8px">Gas Level (PPM)</p>
    <p style="font-family:Sora,sans-serif;font-size:3rem;font-weight:800;
    color:{gc};line-height:1;margin:0">{round(ppm, 1)}</p>
    <p style="font-size:10px;color:#64748B;margin:4px 0 10px">MQ2 Sensor · Raw: {raw_g}</p>
    <span style="background:{gc}20;color:{gc};border:1px solid {gc}33;
    padding:3px 12px;border-radius:999px;font-size:11px;font-weight:600">
    {gi} {gl}</span>
</div>
""")

    with c2:
        t_color = "#42a5f5" if temp < 35 else "#F97316" if temp < 45 else "#DC2626"
        t_label = "Normal" if temp < 35 else "Hot" if temp < 45 else "Extreme"
        md(f"""
<div style="background:#111827;border:1px solid rgba(255,255,255,0.08);
border-radius:16px;padding:22px;text-align:center">
    <p style="font-size:11px;font-weight:600;color:#64748B;text-transform:uppercase;
    letter-spacing:.07em;margin:0 0 8px">Temperature</p>
    <p style="font-family:Sora,sans-serif;font-size:3rem;font-weight:800;
    color:{t_color};line-height:1;margin:0">{round(temp, 1)}</p>
    <p style="font-size:10px;color:#64748B;margin:4px 0 10px">DHT11 · °C</p>
    <span style="background:{t_color}20;color:{t_color};border:1px solid {t_color}33;
    padding:3px 12px;border-radius:999px;font-size:11px;font-weight:600">
    {t_label}</span>
</div>
""")

    with c3:
        h_color = "#26c6da"
        h_label = "Dry" if hum < 30 else "Humid" if hum > 70 else "Normal"
        md(f"""
<div style="background:#111827;border:1px solid rgba(255,255,255,0.08);
border-radius:16px;padding:22px;text-align:center">
    <p style="font-size:11px;font-weight:600;color:#64748B;text-transform:uppercase;
    letter-spacing:.07em;margin:0 0 8px">Humidity</p>
    <p style="font-family:Sora,sans-serif;font-size:3rem;font-weight:800;
    color:{h_color};line-height:1;margin:0">{round(hum, 1)}</p>
    <p style="font-size:10px;color:#64748B;margin:4px 0 10px">DHT11 · %</p>
    <span style="background:{h_color}20;color:{h_color};border:1px solid {h_color}33;
    padding:3px 12px;border-radius:999px;font-size:11px;font-weight:600">
    {h_label}</span>
</div>
""")

    with c4:
        md(f"""
<div style="background:#111827;border:1px solid rgba(255,255,255,0.08);
border-radius:16px;padding:22px;text-align:center">
    <p style="font-size:11px;font-weight:600;color:#64748B;text-transform:uppercase;
    letter-spacing:.07em;margin:0 0 8px">Device Info</p>
    <p style="font-family:JetBrains Mono,monospace;font-size:12px;font-weight:600;
    color:#CBD5E1;margin:0 0 8px;line-height:1.4">{did}</p>
    <p style="font-size:10px;color:#64748B;margin:0 0 4px">
    📍 {user_state or 'Location not set'}</p>
    <p style="font-size:10px;color:#64748B;margin:0 0 8px">Last reading</p>
    <p style="font-family:JetBrains Mono,monospace;font-size:11px;
    color:#4a5a7a;margin:0">{ts_d}</p>
</div>
""")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── GAS SAFETY ASSESSMENT ────────────────────────────────
    ca, cb = st.columns(2)

    with ca:
        section(st, "Indoor Gas Safety Assessment")
        # Find current level details
        cur_action = "Air quality is acceptable."
        for mx, label, color, bg_c, brd_c, icon, action in GAS_SCALE:
            if raw_g <= mx:
                cur_action = action
                break

        md(f"""
<div style="background:{gbg};border:1px solid {gbrd};border-left:4px solid {gc};
border-radius:14px;padding:20px;margin-bottom:14px">
    <p style="font-family:Sora,sans-serif;font-size:14px;font-weight:700;
    color:{gc};margin:0 0 8px">{gi} Current Status: {gl}</p>
    <p style="font-size:13px;color:#94A3B8;line-height:1.7;margin:0 0 16px">{cur_action}</p>
    <p style="font-size:11px;font-weight:600;color:#64748B;text-transform:uppercase;
    letter-spacing:.06em;margin:0 0 8px">PPM Reference Scale</p>
""")

        for mx, label, color, bg_c, brd_c, icon, action in GAS_SCALE:
            is_cur = (label == gl)
            md(f"""
<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;
background:{"rgba(255,255,255,0.04)" if is_cur else "transparent"};
border-radius:6px;padding:4px 8px;
border:{"1px solid " + color + "55" if is_cur else "1px solid transparent"}">
    <div style="width:9px;height:9px;border-radius:50%;
    background:{color};flex-shrink:0"></div>
    <span style="font-size:12px;color:{"#CBD5E1" if is_cur else "#64748B"};
    font-weight:{"700" if is_cur else "400"}">{icon} {label}</span>
    <span style="font-family:JetBrains Mono,monospace;font-size:11px;
    color:#3a4a6a;margin-left:auto">≤ {mx} raw</span>
</div>
""")
        md("</div>")

    with cb:
        section(st, "Why Temperature + Gas Together Matter")
        md(f"""
<div style="background:#111827;border:1px solid rgba(255,255,255,0.07);
border-left:4px solid #42a5f5;border-radius:14px;padding:20px;margin-bottom:14px">
    <p style="font-family:Sora,sans-serif;font-size:14px;font-weight:700;
    color:#42a5f5;margin:0 0 10px">🌡 Temperature Assessment</p>
    <p style="font-size:13px;color:#94A3B8;line-height:1.7;margin:0 0 14px">
    High room temperature accelerates gas diffusion — gas leaks spread faster in hot rooms.
    Combined high PPM and high temperature is an escalated emergency.
    The AirGuard device monitors both simultaneously for this reason.</p>
    <div style="display:flex;justify-content:space-between;padding:8px 0;
    border-bottom:1px solid rgba(255,255,255,0.05);font-size:13px">
        <span style="color:#4a5a7a">Current Temperature</span>
        <span style="font-family:JetBrains Mono,monospace;font-size:12px;
        color:#42a5f5;font-weight:700">{round(temp,1)} °C</span>
    </div>
    <div style="display:flex;justify-content:space-between;padding:8px 0;
    border-bottom:1px solid rgba(255,255,255,0.05);font-size:13px">
        <span style="color:#4a5a7a">Current Humidity</span>
        <span style="font-family:JetBrains Mono,monospace;font-size:12px;
        color:#26c6da;font-weight:700">{round(hum,1)} %</span>
    </div>
    <div style="display:flex;justify-content:space-between;padding:8px 0;font-size:13px">
        <span style="color:#4a5a7a">Gas Risk Level</span>
        <span style="font-family:JetBrains Mono,monospace;font-size:12px;
        color:{gc};font-weight:700">{grisk}</span>
    </div>
</div>
<div style="background:#111827;border:1px solid rgba(255,255,255,0.07);
border-radius:12px;padding:16px">
    <p style="font-size:11px;font-weight:600;color:#64748B;text-transform:uppercase;
    letter-spacing:.06em;margin:0 0 8px">Generator CO Warning</p>
    <p style="font-size:13px;color:#64748B;line-height:1.65;margin:0">
    Generators running indoors or near open windows produce CO — colourless and odourless.
    This is exactly why the AirGuard device monitors indoor air continuously.
    Never run a generator within 3 metres of any open window.</p>
</div>
""")

    # ── TREND CHART ──────────────────────────────────────────
    if history and len(history) > 1:
        section(st, "Reading History — Gas & Temperature Trend")
        hdf = pd.DataFrame(history)
        hdf["timestamp"] = pd.to_datetime(hdf["timestamp"])
        hdf = hdf.sort_values("timestamp")

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=hdf["timestamp"], y=hdf["gas_ppm"],
            mode="lines+markers", name="Gas PPM",
            line=dict(color="#F97316", width=2),
            marker=dict(size=4), yaxis="y1"
        ))
        if "temperature" in hdf.columns:
            fig.add_trace(go.Scatter(
                x=hdf["timestamp"], y=hdf["temperature"],
                mode="lines", name="Temperature °C",
                line=dict(color="#42a5f5", width=2, dash="dot"),
                yaxis="y2"
            ))
        if "humidity" in hdf.columns:
            fig.add_trace(go.Scatter(
                x=hdf["timestamp"], y=hdf["humidity"],
                mode="lines", name="Humidity %",
                line=dict(color="#26c6da", width=1.5, dash="dot"),
                yaxis="y2"
            ))
        for y, tc, lbl in [
            (150, "#16A34A", "Safe (150)"),
            (250, "#F97316", "Warning (250)"),
            (325, "#DC2626", "Danger (325)"),
        ]:
            fig.add_hline(
                y=y, line_dash="dot", line_color=tc, line_width=1,
                annotation_text=lbl, annotation_font_size=9,
                annotation_font_color=tc, yref="y1"
            )

        lay = plotly_layout(height=320)
        lay["yaxis"]["title"] = "Gas PPM (raw)"
        lay["yaxis"]["title_font"] = dict(size=10, color="#F97316")
        lay["yaxis2"] = dict(
            title="Temp °C / Hum %",
            title_font=dict(size=10, color="#42a5f5"),
            overlaying="y", side="right",
            gridcolor="rgba(0,0,0,0)",
            linecolor="rgba(255,255,255,0.05)",
        )
        fig.update_layout(**lay)
        st.plotly_chart(fig, use_container_width=True)

        # Session stats
        section(st, "Session Statistics")
        s1, s2, s3, s4 = st.columns(4)
        with s1: st.markdown(stat_html("Peak Gas",    round(hdf["gas_ppm"].max(),1),    "PPM",    "#DC2626"), unsafe_allow_html=True)
        with s2: st.markdown(stat_html("Average Gas", round(hdf["gas_ppm"].mean(),1),   "PPM",    "#F97316"), unsafe_allow_html=True)
        with s3:
            t_col = "temperature" if "temperature" in hdf.columns else None
            avg_t = round(hdf[t_col].mean(),1) if t_col else "—"
            st.markdown(stat_html("Avg Temp", avg_t, "°C", "#42a5f5"), unsafe_allow_html=True)
        with s4: st.markdown(stat_html("Total Readings", len(hdf), "data points", "#EAB308"), unsafe_allow_html=True)

# ── SETUP STEPS ──────────────────────────────────────────────
section(st, "Device Setup Instructions")
STEPS = [
    ("#16A34A", "Wire your Arduino Uno",
     "MQ2 analog output → A0. DHT11 data → Pin 2. OLED SDA → A4, SCL → A5. All sensors connect to 5V and GND."),
    ("#42a5f5", "Install Arduino libraries",
     "In Arduino IDE: Sketch → Include Library → Manage Libraries. Install: DHT sensor library by Adafruit, Adafruit SSD1306, Adafruit GFX Library, U8glib."),
    ("#EAB308", "Upload the sketch",
     "Open airguard_uno.ino. Select Tools → Board → Arduino Uno. Select the correct COM port. Click Upload."),
    ("#F97316", "Start the serial reader",
     "Close Arduino IDE Serial Monitor. Open a new terminal and run: python serial_reader.py. It will auto-detect your COM port."),
    ("#9333EA", "Run the dashboard",
     "Open a second terminal and run: python -m streamlit run overview.py. The Device card will show live readings within 30 seconds."),
    ("#26c6da", "Start the Telegram bot",
     "Open a third terminal and run: python telegram_bot.py. You will receive a startup message. It will alert you automatically when gas is dangerous."),
]
for color, title, body in STEPS:
    md(f"""
<div style="display:flex;gap:14px;padding:12px 0;
border-bottom:1px solid rgba(255,255,255,0.04);align-items:flex-start">
    <div style="width:10px;height:10px;border-radius:50%;background:{color};
    flex-shrink:0;margin-top:4px"></div>
    <div>
        <p style="font-family:Sora,sans-serif;font-size:13px;font-weight:700;
        color:#CBD5E1;margin:0 0 3px">{title}</p>
        <p style="font-size:13px;color:#64748B;line-height:1.65;margin:0">{body}</p>
    </div>
</div>
""")

# ── EMERGENCY CONTACTS ───────────────────────────────────────
section(st, "Emergency Contacts — Gas Leak")
CONTACTS = [
    ("Lagos Fire Service", "01-7944996",    "#DC2626"),
    ("Nigeria Emergency",  "112",           "#DC2626"),
    ("NEMA Emergency",     "0800-CALLNEMA", "#F97316"),
    ("DPR Gas Safety",     "0803 450 5765", "#F97316"),
]
ec1, ec2, ec3, ec4 = st.columns(4)
for col, (name, number, color) in zip([ec1, ec2, ec3, ec4], CONTACTS):
    with col:
        md(f"""
<div style="background:{color}10;border:1px solid {color}28;
border-radius:12px;padding:14px;text-align:center">
    <p style="font-size:12px;color:#64748B;margin:0 0 4px">{name}</p>
    <p style="font-family:JetBrains Mono,monospace;font-size:16px;
    font-weight:700;color:{color};margin:0">{number}</p>
</div>
""")

st.markdown("<br>", unsafe_allow_html=True)
if st.button("🔄 Refresh Device Reading"):
    st.rerun()
md('<p style="font-family:JetBrains Mono,monospace;font-size:11px;color:#3a4a6a;margin-top:6px">This page auto-refreshes every 5 seconds. Telegram bot sends automatic alerts when gas is dangerous.</p>')
