import streamlit as st, pandas as pd, plotly.graph_objects as go, os
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import sys; sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from styles import *

st.set_page_config(page_title="City Deep Dive — AirGuard NG",page_icon="🔍",layout="wide")
st.markdown(BASE_CSS,unsafe_allow_html=True)
st_autorefresh(interval=10000,key="dive_r")
def md(h): st.markdown(h,unsafe_allow_html=True)

user_state=st.session_state.get("user_state","")
user_city=st.session_state.get("user_city","")
user_condition=st.session_state.get("user_condition","")
device_status_bar(st,location_label=user_state)
render_nav_button(st)
md('<p style="font-family:Sora,sans-serif;font-size:26px;font-weight:800;color:#F8FAFC;letter-spacing:-.02em;margin:0 0 4px">🔍 City Deep Dive</p>')
md(f'<p style="font-size:14px;color:#64748B;margin:0 0 24px">Full sensor breakdown and 24-hour PM2.5 trend · Monitoring {user_city+", " if user_city else ""}{user_state or "Nigeria"}</p>')

@st.cache_data(ttl=300)
def load():
    try:
        df=pd.read_csv("transformed_data.csv"); raw=pd.read_csv("raw_data.csv")
        raw["timestamp"]=pd.to_datetime(raw["timestamp"]); return df,raw
    except:
        return pd.DataFrame(columns=["city","hrs","risk_level","value","lat","lon"]), pd.DataFrame(columns=["city","location_name","parameter","value","timestamp","lat","lon"])
df,raw=load()
device,device_hist=load_device_data()

# Build city options including user's state
cities=list(df["city"].tolist())
user_in=any(user_state.split()[0].lower() in c.lower() for c in cities) if user_state else True
user_city_option=None
if user_state and not user_in:
    user_city_option=f"{user_state}{' — '+user_city if user_city else ''} 📍 Your Location"
    cities=[user_city_option]+cities

selected=st.selectbox("Select location",cities)
is_user_loc = selected==user_city_option

md("<br>")
col_left,col_right=st.columns([1,1.6])

if is_user_loc:
    # Use device data for user's own state
    gl,gc,gbg,gbrd,gi,grisk=classify_gas(int(device.get("gas_raw",0) or 0) if device else None)
    ppm_v=device.get("gas_ppm","—") if device else "—"
    tmp_v=device.get("temperature","—") if device else "—"
    hmd_v=device.get("humidity","—") if device else "—"
    ts_d="—"
    if device:
        try: ts_d=datetime.fromisoformat(device.get("timestamp","")).strftime("%d %b %Y, %H:%M")
        except: pass

    with col_left:
        md(f"""<div style="background:{gbg};border:1px solid {gbrd};border-radius:22px;padding:32px;text-align:center;position:relative;overflow:hidden">
<div style="position:absolute;top:0;left:0;right:0;height:3px;background:{gc}"></div>
<p style="font-family:Sora,sans-serif;font-size:13px;font-weight:700;color:{gc};text-transform:uppercase;letter-spacing:.08em;margin:0 0 10px">📍 {user_state}{' · '+user_city if user_city else ''}</p>
<p style="font-family:Sora,sans-serif;font-size:5rem;font-weight:800;color:{gc};line-height:1;letter-spacing:-.04em;margin:0">{ppm_v}</p>
<p style="font-size:11px;font-weight:600;color:#64748B;text-transform:uppercase;letter-spacing:.07em;margin:6px 0 14px">Gas PPM · Indoor Sensor</p>
<span style="background:{gc}20;color:{gc};border:1px solid {gc}33;padding:3px 12px;border-radius:999px;font-size:11px;font-weight:600">{gi} {grisk}</span>
<div style="height:1px;background:rgba(255,255,255,0.07);margin:20px 0"></div>
<div style="display:flex;justify-content:space-between;padding:9px 0;border-bottom:1px solid rgba(255,255,255,0.05);font-size:13px">
<span style="color:#4a5a7a">Temperature</span><span style="font-family:JetBrains Mono,monospace;font-size:12px;color:#42a5f5">{tmp_v} °C</span></div>
<div style="display:flex;justify-content:space-between;padding:9px 0;border-bottom:1px solid rgba(255,255,255,0.05);font-size:13px">
<span style="color:#4a5a7a">Humidity</span><span style="font-family:JetBrains Mono,monospace;font-size:12px;color:#26c6da">{hmd_v} %</span></div>
<div style="display:flex;justify-content:space-between;padding:9px 0;font-size:13px">
<span style="color:#4a5a7a">Last updated</span><span style="font-family:JetBrains Mono,monospace;font-size:12px;color:#CBD5E1">{ts_d}</span></div></div>
<div style="background:#111827;border:1px solid {gbrd};border-left:3px solid {gc};border-radius:12px;padding:16px 18px;margin-top:14px">
<p style="font-size:11px;font-weight:600;color:{gc};text-transform:uppercase;letter-spacing:.07em;margin:0 0 6px">{gi} Indoor Air — {grisk}</p>
<p style="font-size:13px;color:#94A3B8;line-height:1.65;margin:0">{CONDITION_ADVICE.get(user_condition,'Check indoor air quality regularly. Run the AirGuard device continuously for best protection.')}</p></div>""")

    with col_right:
        section(st,"Indoor Device Readings History")
        if device_hist and len(device_hist)>1:
            hdf=pd.DataFrame(device_hist); hdf["timestamp"]=pd.to_datetime(hdf["timestamp"]); hdf=hdf.sort_values("timestamp")
            fig=go.Figure()
            fig.add_trace(go.Scatter(x=hdf["timestamp"],y=hdf["gas_ppm"],mode="lines+markers",name="Gas PPM",line=dict(color="#F97316",width=2),marker=dict(size=4)))
            if "temperature" in hdf.columns:
                fig.add_trace(go.Scatter(x=hdf["timestamp"],y=hdf["temperature"],mode="lines",name="Temp °C",line=dict(color="#42a5f5",width=1.5,dash="dot"),yaxis="y2"))
            lay=plotly_layout(height=380); lay["yaxis"]["title"]="Gas PPM"; lay["yaxis"]["title_font"]=dict(size=10,color="#F97316")
            lay["yaxis2"]=dict(title="Temp °C",overlaying="y",side="right",gridcolor="rgba(0,0,0,0)")
            fig.update_layout(**lay); st.plotly_chart(fig,use_container_width=True)
        else:
            md('<div style="background:#111827;border:1px solid rgba(255,255,255,0.07);border-radius:12px;padding:32px;text-align:center;color:#64748B">Device reading history will appear here as readings accumulate.</div>')

else:
    # Regular city from OpenAQ
    row=df[df["city"]==selected].iloc[0]
    city_raw=raw[raw["city"]==selected]
    pm25_raw=city_raw[city_raw["parameter"]=="pm25"].sort_values("timestamp")
    temp_raw=city_raw[city_raw["parameter"]=="temperature"]
    hum_raw=city_raw[city_raw["parameter"]=="relativehumidity"]
    color=RISK_COLORS.get(row["risk_level"],"#64748B"); bg=RISK_BG.get(row["risk_level"],"rgba(100,116,139,0.10)"); brd=RISK_BORDER.get(row["risk_level"],"rgba(100,116,139,0.30)")
    exc=round(max(0,row["value"]-15),1); now_s=datetime.now().strftime("%d %b %Y, %H:%M")
    t_v=round(temp_raw.sort_values("timestamp").iloc[-1]["value"],1) if not temp_raw.empty else "—"
    h_v=round(hum_raw.sort_values("timestamp").iloc[-1]["value"],1) if not hum_raw.empty else "—"

    with col_left:
        md(f"""<div style="background:{bg};border:1px solid {brd};border-radius:22px;padding:32px;text-align:center;position:relative;overflow:hidden">
<div style="position:absolute;top:0;left:0;right:0;height:3px;background:{color}"></div>
<p style="font-family:Sora,sans-serif;font-size:13px;font-weight:700;color:{color};text-transform:uppercase;letter-spacing:.08em;margin:0 0 10px">{selected}</p>
<p style="font-family:Sora,sans-serif;font-size:5rem;font-weight:800;color:{color};line-height:1;letter-spacing:-.04em;margin:0">{row['hrs']}</p>
<p style="font-size:11px;font-weight:600;color:#64748B;text-transform:uppercase;letter-spacing:.07em;margin:6px 0 14px">Health Risk Score</p>
{badge(row['risk_level'])}
<div style="height:1px;background:rgba(255,255,255,0.07);margin:20px 0"></div>
<div style="display:flex;justify-content:space-between;padding:9px 0;border-bottom:1px solid rgba(255,255,255,0.05);font-size:13px"><span style="color:#4a5a7a">PM2.5</span><span style="font-family:JetBrains Mono,monospace;font-size:12px;color:#CBD5E1">{round(row['value'],2)} µg/m³</span></div>
<div style="display:flex;justify-content:space-between;padding:9px 0;border-bottom:1px solid rgba(255,255,255,0.05);font-size:13px"><span style="color:#4a5a7a">WHO Limit</span><span style="font-family:JetBrains Mono,monospace;font-size:12px;color:#CBD5E1">15.0 µg/m³</span></div>
<div style="display:flex;justify-content:space-between;padding:9px 0;border-bottom:1px solid rgba(255,255,255,0.05);font-size:13px"><span style="color:#4a5a7a">Exceeds by</span><span style="font-family:JetBrains Mono,monospace;font-size:12px;color:{color}">{exc} µg/m³</span></div>
<div style="display:flex;justify-content:space-between;padding:9px 0;border-bottom:1px solid rgba(255,255,255,0.05);font-size:13px"><span style="color:#4a5a7a">Temperature</span><span style="font-family:JetBrains Mono,monospace;font-size:12px;color:#42a5f5">{t_v} °C</span></div>
<div style="display:flex;justify-content:space-between;padding:9px 0;font-size:13px"><span style="color:#4a5a7a">Humidity</span><span style="font-family:JetBrains Mono,monospace;font-size:12px;color:#26c6da">{h_v} %</span></div></div>
<div style="background:#111827;border:1px solid {brd};border-left:3px solid {color};border-radius:12px;padding:16px 18px;margin-top:14px">
<p style="font-size:11px;font-weight:600;color:{color};text-transform:uppercase;letter-spacing:.07em;margin:0 0 6px">Health Guidance</p>
<p style="font-size:13px;color:#94A3B8;line-height:1.65;margin:0">{RISK_ADVICE.get(row['risk_level'],'')}</p>
{('<p style="font-size:13px;color:#CBD5E1;line-height:1.65;margin:10px 0 0"><strong>Your condition ('+user_condition+'):</strong> '+CONDITION_ADVICE.get(user_condition,'')+'</p>') if user_condition and user_condition not in ['','None'] else ''}</div>""")

    with col_right:
        section(st,"Sensor Readings by Location")
        locs=pm25_raw["location_name"].unique()
        if len(locs)==0:
            md('<div style="background:#111827;border:1px solid rgba(255,255,255,0.07);border-radius:12px;padding:24px;text-align:center;color:#64748B">No sensor data available.</div>')
        else:
            for loc in locs:
                ld=pm25_raw[pm25_raw["location_name"]==loc]
                if ld.empty: continue
                lv=ld.sort_values("timestamp").iloc[-1]["value"]; lts=ld.sort_values("timestamp").iloc[-1]["timestamp"].strftime("%H:%M")
                lr=get_risk_level(lv); lc=RISK_COLORS.get(lr,"#64748B")
                md(f"""<div style="background:#111827;border:1px solid rgba(255,255,255,0.07);border-left:3px solid {lc};border-radius:12px;padding:14px 18px;margin-bottom:10px;display:flex;align-items:center;justify-content:space-between">
<div><p style="font-family:Sora,sans-serif;font-size:13px;font-weight:700;color:#CBD5E1;margin:0">{loc}</p><p style="font-family:JetBrains Mono,monospace;font-size:11px;color:#64748B;margin:3px 0 0">Updated {lts}</p></div>
<div style="text-align:right"><p style="font-family:Sora,sans-serif;font-size:1.8rem;font-weight:800;color:{lc};margin:0;line-height:1">{round(lv,1)}</p><p style="font-size:10px;color:#64748B;margin:0">µg/m³</p></div></div>""")
        c1,c2=st.columns(2)
        with c1: st.markdown(metric_html("🌡 Temperature",t_v,"°C","#42a5f5"),unsafe_allow_html=True)
        with c2: st.markdown(metric_html("💧 Humidity",h_v,"%","#26c6da"),unsafe_allow_html=True)

    section(st,"24-Hour PM2.5 Trend")
    if not pm25_raw.empty:
        fig=go.Figure()
        for loc in pm25_raw["location_name"].unique():
            ld=pm25_raw[pm25_raw["location_name"]==loc].sort_values("timestamp")
            fig.add_trace(go.Scatter(x=ld["timestamp"],y=ld["value"],mode="lines",name=loc,line=dict(width=2),opacity=0.9))
        for y,tc,lbl in [(15,"#16A34A","WHO Safe (15)"),(35.4,"#F97316","Moderate"),(55.4,"#DC2626","Unhealthy")]:
            fig.add_hline(y=y,line_dash="dot",line_color=tc,line_width=1,annotation_text=lbl,annotation_font_size=9,annotation_font_color=tc)
        lay=plotly_layout(height=300); lay["yaxis"]["title"]="PM2.5 (µg/m³)"; lay["yaxis"]["title_font"]=dict(size=10,color="#4a5a7a")
        fig.update_layout(**lay); st.plotly_chart(fig,use_container_width=True)
