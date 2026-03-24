import streamlit as st, pandas as pd, os
from datetime import datetime
try:
    from streamlit_autorefresh import st_autorefresh
    _HAS_AUTOREFRESH = True
except ImportError:
    _HAS_AUTOREFRESH = False
import sys, os
_PAGE_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_PAGE_DIR)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
from styles import render_nav_button
from styles import *

st.set_page_config(page_title="Alerts Log — AirGuard NG",page_icon="🚨",layout="wide")
st.markdown(BASE_CSS,unsafe_allow_html=True)
if _HAS_AUTOREFRESH:
    st_autorefresh(interval=10000,key="alert_r")
def md(h): st.markdown(h,unsafe_allow_html=True)

user_state=st.session_state.get("user_state","")
user_city=st.session_state.get("user_city","")
device_status_bar(st,location_label=user_state)
render_nav_button(st)
md('<p style="font-family:Sora,sans-serif;font-size:26px;font-weight:800;color:#F8FAFC;letter-spacing:-.02em;margin:0 0 4px">🚨 Alerts Log</p>')
md('<p style="font-size:14px;color:#64748B;margin:0 0 24px">Every WHO threshold breach and gas danger event recorded across all monitored locations</p>')

WHO=15.0
@st.cache_data(ttl=60)
def load():
    try:
        raw=pd.read_csv("raw_data.csv"); df=pd.read_csv("transformed_data.csv")
        raw["timestamp"]=pd.to_datetime(raw["timestamp"]); return raw,df
    except Exception:
        return pd.DataFrame(columns=["city","location_name","parameter","value","timestamp","lat","lon"]), pd.DataFrame(columns=["city","hrs","risk_level","value","lat","lon"])
raw,df=load()
device,device_hist=load_device_data()

pm25=raw[raw["parameter"]=="pm25"].copy()
br=pm25[pm25["value"]>WHO].copy().sort_values("timestamp",ascending=False)
br["risk_level"]=br["value"].apply(get_risk_level)

# Device alerts from history
device_alerts=[]
if device_hist:
    for r in device_hist:
        raw_g=int(r.get("gas_raw",0) or 0)
        if gas_is_dangerous(raw_g):
            device_alerts.append({
                "city":user_state or "Your Location","location_name":"AirGuard Device (Indoor)",
                "value":r.get("gas_ppm",0),"risk_level":r.get("risk_level","Warning"),
                "timestamp":r.get("timestamp",""),"type":"gas"})

total=len(br); total_gas=len(device_alerts); affected=br["city"].nunique()
worst_v=round(br["value"].max(),2) if not br.empty else 0
worst_c=br.loc[br["value"].idxmax(),"city"] if not br.empty else "—"

# Stats
c1,c2,c3,c4=st.columns(4)
for col,lbl,val,unit,clr in [(c1,"AQ Breaches",total,"above WHO limit","#DC2626"),(c2,"Gas Alerts",total_gas,"from device","#F97316"),(c3,"Cities Affected",affected,f"of {df['city'].nunique()} monitored","#9333EA"),(c4,"Worst Reading",worst_v,"µg/m³ PM2.5","#DC2626")]:
    with col: st.markdown(stat_html(lbl,val,unit,clr),unsafe_allow_html=True)

md("<br>")

# Device gas alerts at top
if device_alerts:
    section(st,f"🔩 Indoor Gas Alerts — {user_state or 'Your Location'} (AirGuard Device)")
    for a in device_alerts[-20:][::-1]:
        gl,gc,gbg,gbrd,gi,grisk=classify_gas(None)
        try: ts_d=datetime.fromisoformat(a["timestamp"]).strftime("%d %b %Y, %H:%M:%S")
        except: ts_d=a["timestamp"]
        md(f"""<div style="background:rgba(220,38,38,0.10);border:1px solid rgba(220,38,38,0.28);border-left:4px solid #DC2626;border-radius:12px;padding:14px 18px;margin-bottom:10px;display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap">
<div><p style="font-family:Sora,sans-serif;font-size:13px;font-weight:700;color:#CBD5E1;margin:0">🔩 {a['location_name']}</p>
<p style="font-family:JetBrains Mono,monospace;font-size:11px;color:#64748B;margin:3px 0 0">Gas: {round(float(a['value']),1)} PPM · {a['risk_level']}</p></div>
<span style="background:rgba(220,38,38,0.12);color:#DC2626;border:1px solid rgba(220,38,38,0.3);padding:3px 12px;border-radius:999px;font-size:11px;font-weight:600">🚨 Gas Danger</span>
<p style="font-family:JetBrains Mono,monospace;font-size:11px;color:#4a5a7a;margin:0">{ts_d}</p></div>""")

# Filters
section(st,"WHO Air Quality Breach Events")
cities_in_br=["All Cities"]+sorted(br["city"].unique().tolist())
if user_state and user_state not in cities_in_br: cities_in_br.append(f"{user_state} (Your Location)")
cf1,cf2,cf3=st.columns(3)
with cf1: fc=st.selectbox("Filter by location",cities_in_br)
with cf2: fr=st.selectbox("Filter by risk level",["All Levels"]+sorted(br["risk_level"].unique().tolist()))
with cf3: so=st.selectbox("Sort by",["Most Recent First","Highest Reading First"])

filtered=br.copy()
if fc!="All Cities" and "Your Location" not in fc: filtered=filtered[filtered["city"]==fc]
if fr!="All Levels": filtered=filtered[filtered["risk_level"]==fr]
if so=="Highest Reading First": filtered=filtered.sort_values("value",ascending=False)

md(f'<p style="font-family:JetBrains Mono,monospace;font-size:11px;color:#64748B;margin:0 0 12px">{len(filtered)} breach events found</p>')

if filtered.empty:
    md('<div style="background:rgba(22,163,74,0.10);border:1px solid rgba(22,163,74,0.28);border-radius:12px;padding:20px;text-align:center;color:#16A34A">✓ No breaches found for the selected filters.</div>')
else:
    for _,row in filtered.head(60).iterrows():
        color=RISK_COLORS.get(row["risk_level"],"#64748B")
        try: ts=pd.to_datetime(row["timestamp"]).strftime("%d %b %Y, %H:%M")
        except: ts="—"
        exc=round(row["value"]-WHO,1)
        md(f"""<div style="background:#111827;border:1px solid rgba(255,255,255,0.07);border-left:4px solid {color};border-radius:12px;padding:14px 18px;margin-bottom:10px;display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap">
<div><p style="font-family:Sora,sans-serif;font-size:13px;font-weight:700;color:#CBD5E1;margin:0">{row['city']}</p>
<p style="font-family:JetBrains Mono,monospace;font-size:11px;color:#64748B;margin:3px 0 0">{row['location_name']} · PM2.5: {round(row['value'],1)} µg/m³ · Exceeds WHO by {exc} µg/m³</p></div>
<span style="background:{color}18;color:{color};border:1px solid {color}33;padding:3px 12px;border-radius:999px;font-size:11px;font-weight:600">{row['risk_level']}</span>
<p style="font-family:JetBrains Mono,monospace;font-size:11px;color:#4a5a7a;margin:0">{ts}</p></div>""")
    if len(filtered)>60:
        md(f'<p style="font-family:JetBrains Mono,monospace;font-size:11px;color:#4a5a7a;text-align:center">Showing 60 of {len(filtered)}. Download CSV for full log.</p>')
    md("<br>")
    st.download_button(f"⬇ Download breach log ({len(filtered)} records)",filtered.to_csv(index=False),f"airguard_alerts_{datetime.now().strftime('%Y%m%d')}.csv","text/csv")
