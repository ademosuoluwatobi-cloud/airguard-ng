import streamlit as st, pandas as pd, plotly.graph_objects as go, os
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import sys; sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from styles import *

st.set_page_config(page_title="Compare Cities — AirGuard NG",page_icon="⚖️",layout="wide")
st.markdown(BASE_CSS,unsafe_allow_html=True)
st_autorefresh(interval=10000,key="cmp_r")
def md(h): st.markdown(h,unsafe_allow_html=True)

user_state=st.session_state.get("user_state","")
user_city=st.session_state.get("user_city","")
user_condition=st.session_state.get("user_condition","")
device_status_bar(st,location_label=user_state)
render_nav_button(st)
md('<p style="font-family:Sora,sans-serif;font-size:26px;font-weight:800;color:#F8FAFC;letter-spacing:-.02em;margin:0 0 4px">⚖️ Compare Cities</p>')
md('<p style="font-size:14px;color:#64748B;margin:0 0 24px">Select two or more locations to compare air quality side by side</p>')

@st.cache_data(ttl=300)
def load():
    try:
        df=pd.read_csv("transformed_data.csv"); raw=pd.read_csv("raw_data.csv")
        raw["timestamp"]=pd.to_datetime(raw["timestamp"]); return df,raw
    except:
        return pd.DataFrame(columns=["city","hrs","risk_level","value","lat","lon"]), pd.DataFrame(columns=["city","location_name","parameter","value","timestamp","lat","lon"])
df,raw=load()
device,_=load_device_data()

# Build options including user state
all_cities=list(df["city"].tolist())
user_label=None
user_in=any(user_state.split()[0].lower() in c.lower() for c in all_cities) if user_state else True
if user_state and not user_in:
    user_label=f"{user_state}{' — '+user_city if user_city else ''} 📍 (Your Location)"
    all_cities=[user_label]+all_cities

default_sel=all_cities[:2]
selected=st.multiselect("Select locations to compare",all_cities,default=default_sel)

if len(selected)<2:
    md('<div style="background:rgba(234,179,8,0.10);border:1px solid rgba(234,179,8,0.28);border-radius:12px;padding:14px 18px;color:#EAB308;font-size:14px">⚠️ Please select at least 2 locations to compare.</div>')
    st.stop()

# Build unified dataframe including device data for user's location
def get_row(city_name):
    if city_name == user_label:
        # Use device data
        if device:
            raw_g=int(device.get("gas_raw",0) or 0)
            ppm=float(device.get("gas_ppm",0) or 0)
            _,_,_,_,_,grisk=classify_gas(raw_g)
            hrs_e=min(100,round(ppm/5,1))
            return {"city":city_name,"hrs":hrs_e,"risk_level":grisk,"value":ppm,"is_device":True}
        return {"city":city_name,"hrs":0,"risk_level":"No Data","value":0,"is_device":True}
    r=df[df["city"]==city_name]
    if r.empty: return {"city":city_name,"hrs":0,"risk_level":"No Data","value":0,"is_device":False}
    return r.iloc[0].to_dict()|{"is_device":False}

rows=[get_row(c) for c in selected]
cdf=pd.DataFrame(rows)
safest=cdf.loc[cdf["hrs"].idxmin(),"city"]
worst=cdf.loc[cdf["hrs"].idxmax(),"city"]

section(st,"Health Risk Score Comparison")
cols=st.columns(len(selected))
for i,city in enumerate(selected):
    r=cdf[cdf["city"]==city].iloc[0]
    color=RISK_COLORS.get(r["risk_level"],"#64748B"); bg=RISK_BG.get(r["risk_level"],"rgba(100,116,139,0.10)"); brd=RISK_BORDER.get(r["risk_level"],"rgba(100,116,139,0.30)")
    exc=round(max(0,float(r["value"])-15),1)
    crown=""
    if city==worst: crown=f'<div style="background:rgba(220,38,38,0.12);color:#DC2626;border:1px solid rgba(220,38,38,0.28);padding:3px 10px;border-radius:999px;font-size:10px;font-weight:600;display:inline-block;margin-bottom:8px">⚠ Highest Risk</div>'
    elif city==safest: crown=f'<div style="background:rgba(22,163,74,0.12);color:#16A34A;border:1px solid rgba(22,163,74,0.28);padding:3px 10px;border-radius:999px;font-size:10px;font-weight:600;display:inline-block;margin-bottom:8px">✓ Cleanest</div>'
    dev_badge='<span style="background:rgba(249,115,22,0.15);color:#F97316;border:1px solid rgba(249,115,22,0.3);padding:1px 7px;border-radius:999px;font-size:10px;margin-left:4px">📍 You</span>' if r.get("is_device") else ""
    val_label="PPM (Indoor)" if r.get("is_device") else "PM2.5 µg/m³"
    # Get temp/hum
    t,h=get_temp_hum_for_city(raw,city) if not r.get("is_device") else (device.get("temperature","—") if device else "—", device.get("humidity","—") if device else "—")
    temp_str=f'🌡 <span style="color:#42a5f5">{t}{"°C" if t!="—" else ""}</span> &nbsp; 💧 <span style="color:#26c6da">{h}{"%"if h!="—" else ""}</span>'
    with cols[i]:
        md(f"""<div style="background:{bg};border:1px solid {brd};border-radius:20px;padding:24px 20px;text-align:center;position:relative;overflow:hidden">
<div style="position:absolute;top:0;left:0;right:0;height:3px;background:{color}"></div>
{crown}
<p style="font-family:Sora,sans-serif;font-size:14px;font-weight:700;color:#CBD5E1;margin:0 0 6px">{city}{dev_badge}</p>
<p style="font-family:Sora,sans-serif;font-size:3.2rem;font-weight:800;color:{color};line-height:1;letter-spacing:-.04em;margin:0">{r['hrs']}</p>
<p style="font-size:11px;font-weight:600;color:#64748B;text-transform:uppercase;letter-spacing:.07em;margin:4px 0 12px">Health Risk Score</p>
{badge(r['risk_level'])}
<div style="height:1px;background:rgba(255,255,255,0.06);margin:16px 0"></div>
<div style="display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid rgba(255,255,255,0.04);font-size:12px">
<span style="color:#4a5a7a">{val_label}</span><span style="font-family:JetBrains Mono,monospace;color:#CBD5E1">{round(float(r['value']),1)}</span></div>
<div style="display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid rgba(255,255,255,0.04);font-size:12px">
<span style="color:#4a5a7a">Exceeds WHO by</span><span style="font-family:JetBrains Mono,monospace;color:{color}">{exc}</span></div>
<p style="font-size:12px;color:#64748B;margin:8px 0 0">{temp_str}</p>
</div>""")

md("<br>")
col_bar,col_trend=st.columns(2)

with col_bar:
    section(st,"HRS Comparison")
    fig=go.Figure(go.Bar(
        x=cdf["city"],y=cdf["hrs"],
        marker=dict(color=[RISK_COLORS.get(r,"#64748B") for r in cdf["risk_level"]],opacity=0.85,line=dict(width=0)),
        text=[str(h) for h in cdf["hrs"]],textposition="outside",
        textfont=dict(family="JetBrains Mono",size=11,color="#94A3B8")))
    lay=plotly_layout(height=300,legend=False); lay["yaxis"]["title"]="Health Risk Score"; lay["yaxis"]["range"]=[0,max(cdf["hrs"])*1.35]
    fig.update_layout(**lay); st.plotly_chart(fig,use_container_width=True)

with col_trend:
    section(st,"PM2.5 Trend Comparison")
    pm25r=raw[raw["parameter"]=="pm25"]
    fig2=go.Figure()
    for city in selected:
        if city==user_label: continue
        cd=pm25r[pm25r["city"]==city].sort_values("timestamp")
        if cd.empty: continue
        hourly=cd.groupby(cd["timestamp"].dt.floor("h"))["value"].mean().reset_index()
        c_color=RISK_COLORS.get(cdf[cdf["city"]==city].iloc[0]["risk_level"],"#64748B")
        fig2.add_trace(go.Scatter(x=hourly["timestamp"],y=hourly["value"],mode="lines",name=city,line=dict(width=2,color=c_color),opacity=0.9))
    # Add device history if user's state selected
    if user_label and user_label in selected:
        _,hist=load_device_data()
        if hist:
            hdf=pd.DataFrame(hist); hdf["timestamp"]=pd.to_datetime(hdf["timestamp"])
            fig2.add_trace(go.Scatter(x=hdf["timestamp"],y=hdf["gas_ppm"],mode="lines",name=f"{user_state} (Indoor)",line=dict(color="#F97316",width=2,dash="dot"),opacity=0.9))
    fig2.add_hline(y=15,line_dash="dot",line_color="#16A34A",line_width=1,annotation_text="WHO Safe",annotation_font_size=9,annotation_font_color="#16A34A")
    lay2=plotly_layout(height=300); lay2["yaxis"]["title"]="PM2.5 (µg/m³)"; lay2["yaxis"]["title_font"]=dict(size=10,color="#4a5a7a")
    fig2.update_layout(**lay2); st.plotly_chart(fig2,use_container_width=True)

section(st,"Comparison Table")
tbl=cdf[["city","value","hrs","risk_level"]].copy()
tbl.columns=["Location","Value","Health Risk Score","Risk Level"]
tbl["Value"]=tbl["Value"].apply(lambda x: round(float(x),2))
st.dataframe(tbl.set_index("Location"),use_container_width=True)

if user_condition and user_condition not in ["","None"]:
    section(st,f"Advice for {user_condition} — Based on Current Conditions")
    safest_row=cdf.loc[cdf["hrs"].idxmin()]
    md(f"""<div style="background:#111827;border:1px solid rgba(22,163,74,0.28);border-left:4px solid #16A34A;border-radius:14px;padding:18px">
<p style="font-family:Sora,sans-serif;font-size:14px;font-weight:700;color:#16A34A;margin:0 0 8px">Recommendation for {user_condition} patients today</p>
<p style="font-size:13px;color:#94A3B8;line-height:1.7;margin:0">{CONDITION_ADVICE.get(user_condition,'')} <br><br>Based on today's data, <strong style="color:#CBD5E1">{safest_row['city']}</strong> has the lowest risk (HRS {safest_row['hrs']}). If you must be outdoors, early morning before 7am is safest.</p></div>""")
