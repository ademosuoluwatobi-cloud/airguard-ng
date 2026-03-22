import streamlit as st, os
from streamlit_autorefresh import st_autorefresh
import sys; sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from styles import *

st.set_page_config(page_title="About — AirGuard NG",page_icon="ℹ️",layout="wide")
st.markdown(BASE_CSS,unsafe_allow_html=True)
st_autorefresh(interval=60000,key="ab_r")
def md(h): st.markdown(h,unsafe_allow_html=True)

user_state=st.session_state.get("user_state","")
device_status_bar(st,location_label=user_state)
md('<p style="font-family:Sora,sans-serif;font-size:26px;font-weight:800;color:#F8FAFC;letter-spacing:-.02em;margin:0 0 4px">ℹ️ About AirGuard NG</p>')
md('<p style="font-size:14px;color:#64748B;margin:0 0 24px">Project documentation, data methodology, hardware details, and scale-up roadmap</p>')

cm,cb=st.columns([1.4,1])
with cm:
    md("""<div style="background:rgba(22,163,74,0.08);border:1px solid rgba(22,163,74,0.22);border-left:4px solid #16A34A;border-radius:18px;padding:26px">
<p style="font-family:Sora,sans-serif;font-size:15px;font-weight:700;color:#16A34A;margin:0 0 12px">🎯 Mission Statement</p>
<p style="font-size:14px;color:#94A3B8;line-height:1.8;margin:0">
Nigeria has one doctor for every 5,000 patients. AirGuard NG gives every one of those 5,000 patients the environmental health intelligence their doctor never has time to provide.<br><br>
AirGuard NG is Nigeria's first personalised chronic disease environmental health platform. It monitors real-time air quality across Nigerian cities using OpenAQ v3 sensor data, calculates a Health Risk Score benchmarked against WHO 2021 guidelines, and delivers condition-specific health advice that tells each user exactly what the air is doing to their specific body — right now, before it harms them.<br><br>
The AirGuard hardware device extends this into the home — an Arduino Uno with MQ2 gas sensor and DHT11 monitors indoor air for CO, LPG, and other dangerous gases, sending real-time alerts via Telegram and the Streamlit dashboard.<br><br>
Built as part of the <strong style="color:#CBD5E1">3MTT NextGen Knowledge Showcase</strong> under the <strong style="color:#CBD5E1">Environment Pillar</strong>, aligned with Airtel Nigeria.
</p></div>""")
with cb:
    rows=[("Builder","3MTT NextGen Fellow"),("Track","Data Science"),("Programme","3MTT Nigeria"),("Challenge","NextGen Knowledge Showcase"),("Pillar","Environment"),("Alignment","Airtel Nigeria"),("Hardware","Arduino Uno + MQ2 + DHT11 + OLED"),("Backend","Python + Flask + Serial"),("Frontend","Streamlit + Folium + Plotly")]
    rhtml="".join([f'<div style="display:flex;justify-content:space-between;padding:9px 0;border-bottom:1px solid rgba(255,255,255,0.04);font-size:13px"><span style="color:#4a5a7a">{k}</span><span style="font-family:JetBrains Mono,monospace;font-size:12px;color:#CBD5E1">{v}</span></div>' for k,v in rows])
    md(f'<div style="background:#111827;border:1px solid rgba(255,255,255,0.07);border-radius:18px;padding:24px"><p style="font-family:Sora,sans-serif;font-size:15px;font-weight:700;color:#42a5f5;margin:0 0 14px">👨‍💻 Project Details</p>{rhtml}</div>')

section(st,"Health Risk Score Algorithm")
md("""<div style="background:#111827;border:1px solid rgba(255,255,255,0.07);border-radius:16px;padding:24px">
<p style="font-size:14px;color:#94A3B8;line-height:1.75;margin:0 0 16px">The Health Risk Score (HRS) is a 0–100 scale calculated from PM2.5 sensor readings, benchmarked against WHO 2021 Air Quality Guidelines. The algorithm maps raw µg/m³ values onto a linear scale within each WHO risk band.</p>
<div style="background:#060d1a;border:1px solid rgba(255,255,255,0.08);border-radius:10px;padding:18px 22px;font-family:JetBrains Mono,monospace;font-size:12px;color:#16A34A;line-height:2.1">
PM2.5 ≤ 12.0   µg/m³  →  HRS  0–20   (Good)<br>
PM2.5 ≤ 35.4   µg/m³  →  HRS 21–40   (Moderate)<br>
PM2.5 ≤ 55.4   µg/m³  →  HRS 41–60   (Unhealthy for Sensitive Groups)<br>
PM2.5 ≤ 150.4  µg/m³  →  HRS 61–80   (Unhealthy)<br>
PM2.5 ≤ 250.4  µg/m³  →  HRS 81–99   (Very Unhealthy)<br>
PM2.5  > 250.4 µg/m³  →  HRS 100     (Hazardous)<br><br>
# Within each band, HRS is interpolated linearly:<br>
HRS = band_start + ((pm25 - band_low) / band_width) × 20
</div></div>""")

section(st,"Tech Stack")
STACK=[("#42a5f5","Python 3.14"),("#F97316","Streamlit"),("#16A34A","Pandas"),("#9333EA","Plotly"),("#26c6da","Folium"),("#EAB308","OpenAQ v3 API"),("#DC2626","Flask"),("#42a5f5","python-dotenv"),("#F97316","pyserial"),("#9333EA","ArduinoJson v7"),("#16A34A","Adafruit SSD1306"),("#EAB308","streamlit-autorefresh")]
badges=" ".join([f'<span style="background:{c}18;color:{c};border:1px solid {c}33;padding:5px 14px;border-radius:999px;font-size:12px;font-weight:600;font-family:JetBrains Mono,monospace;display:inline-block;margin:4px 4px 4px 0">{t}</span>' for c,t in STACK])
md(f'<div style="margin-bottom:24px">{badges}</div>')

section(st,"Scale-Up Roadmap")
ROADMAP=[("#16A34A","Phase 1 — Current","5 cities, 56+ sensors, PM2.5 HRS, temperature/humidity, 8-page Streamlit dashboard, Arduino Uno gas sensor with OLED, Telegram alerts, real-time USB serial data pipeline."),("#42a5f5","Phase 2 — Expand Coverage","Integrate additional APIs to cover all 36 Nigerian states. Add Kano, Port Harcourt, Enugu, and Kaduna as monitored cities."),("#EAB308","Phase 3 — Patient Features","Personal condition profiles, caregiver WhatsApp alerts, personal exposure log, weekly doctor report PDF export."),("#F97316","Phase 4 — Hardware Network","Deploy AirGuard Devices in schools, markets, and hospitals across Lagos and Abuja. ESP32 WiFi edition for wireless deployment."),("#9333EA","Phase 5 — National Platform","Partner with NESREA and state ministries of environment to make AirGuard NG Nigeria's official citizen air quality platform.")]
for color,title,body in ROADMAP:
    md(f'<div style="display:flex;gap:14px;align-items:flex-start;padding:12px 0;border-bottom:1px solid rgba(255,255,255,0.04)"><div style="width:10px;height:10px;border-radius:50%;background:{color};flex-shrink:0;margin-top:5px"></div><div><p style="font-family:Sora,sans-serif;font-size:13px;font-weight:700;color:{color};margin:0 0 3px">{title}</p><p style="font-size:13px;color:#64748B;line-height:1.6;margin:0">{body}</p></div></div>')

md('<div style="background:#111827;border:1px solid rgba(255,255,255,0.06);border-radius:12px;padding:18px 22px;margin-top:28px;text-align:center"><p style="font-family:Sora,sans-serif;font-size:14px;font-weight:700;color:#CBD5E1;margin:0 0 6px">AirGuard NG</p><p style="font-family:JetBrains Mono,monospace;font-size:11px;color:#3a4a6a;margin:0">Python 3.14 · Streamlit · OpenAQ v3 · Arduino Uno · WHO 2021 · 3MTT NextGen Data Science · Environment Pillar · Airtel Nigeria · Nigeria 2026</p></div>')
