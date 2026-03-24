import streamlit as st, pandas as pd, plotly.graph_objects as go, os
from streamlit_autorefresh import st_autorefresh
import sys; sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from styles import *

st.set_page_config(page_title="Historical Trends — AirGuard NG",page_icon="📈",layout="wide")
st.markdown(BASE_CSS,unsafe_allow_html=True)
st_autorefresh(interval=10000,key="hist_r")
def md(h): st.markdown(h,unsafe_allow_html=True)

user_state=st.session_state.get("user_state","")
user_city=st.session_state.get("user_city","")
device_status_bar(st,location_label=user_state)
render_nav_button(st)
md('<p style="font-family:Sora,sans-serif;font-size:26px;font-weight:800;color:#F8FAFC;letter-spacing:-.02em;margin:0 0 4px">📈 Historical Trends</p>')
md('<p style="font-size:14px;color:#64748B;margin:0 0 24px">Analyse pollution patterns over time — by location, parameter, hour of day, and day of week</p>')

@st.cache_data(ttl=300)
def load():
    try:
        raw=pd.read_csv("raw_data.csv"); raw["timestamp"]=pd.to_datetime(raw["timestamp"]); return raw
    except:
        return pd.DataFrame(columns=["city","location_name","parameter","value","timestamp","lat","lon"])
raw=load()
device,device_hist=load_device_data()

# Build city options
CITY_OPT=sorted(raw["city"].unique().tolist())
user_in=any(user_state.split()[0].lower() in c.lower() for c in CITY_OPT) if user_state else True
user_label=None
if user_state and not user_in:
    user_label=f"{user_state}{' — '+user_city if user_city else ''} 📍 (Your Location)"
    CITY_OPT=[user_label]+CITY_OPT

cf1,cf2=st.columns(2)
with cf1:
    default_city=user_label or (CITY_OPT[0] if CITY_OPT else None)
    default_idx=CITY_OPT.index(default_city) if default_city in CITY_OPT else 0
    sel_city=st.selectbox("Location",CITY_OPT,index=default_idx)
with cf2:
    params=["pm25","temperature","relativehumidity","pm10","no2"]
    avail_params=[p for p in params if p in raw["parameter"].unique()]
    sel_param=st.selectbox("Parameter",avail_params if avail_params else params)

if sel_city==user_label:
    # Show device history
    section(st,"Indoor Device Readings — Your Location")
    if device_hist and len(device_hist)>1:
        hdf=pd.DataFrame(device_hist); hdf["timestamp"]=pd.to_datetime(hdf["timestamp"]); hdf=hdf.sort_values("timestamp")
        param_col="gas_ppm" if sel_param=="pm25" else ("temperature" if sel_param=="temperature" else ("humidity" if sel_param=="relativehumidity" else "gas_ppm"))
        if param_col not in hdf.columns: param_col="gas_ppm"
        avg_v=round(hdf[param_col].mean(),2); max_v=round(hdf[param_col].max(),2); min_v=round(hdf[param_col].min(),2)
        c1,c2,c3,c4=st.columns(4)
        for col,lbl,val,unit,clr in [(c1,"Average",avg_v,"","#42a5f5"),(c2,"Peak",max_v,"","#DC2626"),(c3,"Lowest",min_v,"","#16A34A"),(c4,"Readings",len(hdf),"pts","#EAB308")]:
            with col: st.markdown(stat_html(lbl,val,unit,clr),unsafe_allow_html=True)
        fig=go.Figure()
        fig.add_trace(go.Scatter(x=hdf["timestamp"],y=hdf[param_col],mode="lines+markers",name=param_col,line=dict(color="#42a5f5",width=2),marker=dict(size=4)))
        lay=plotly_layout(height=300); lay["yaxis"]["title"]=param_col; lay["yaxis"]["title_font"]=dict(size=10,color="#4a5a7a")
        fig.update_layout(**lay); st.plotly_chart(fig,use_container_width=True)
        st.download_button("⬇ Download device history",hdf.to_csv(index=False),f"airguard_device_history.csv","text/csv")
    else:
        md(f'<div style="background:#111827;border:1px solid rgba(255,255,255,0.07);border-radius:12px;padding:32px;text-align:center;color:#64748B">No device history yet for {user_state}. Keep serial_reader.py running to accumulate readings.</div>')
else:
    data=raw[(raw["city"]==sel_city)&(raw["parameter"]==sel_param)].sort_values("timestamp")
    if data.empty:
        md(f'<div style="background:rgba(234,179,8,0.10);border:1px solid rgba(234,179,8,0.28);border-radius:12px;padding:20px;text-align:center;color:#EAB308">No {sel_param} data for {sel_city}.</div>')
        st.stop()

    avg_v=round(data["value"].mean(),2); max_v=round(data["value"].max(),2); min_v=round(data["value"].min(),2)
    section(st,"Summary Statistics")
    c1,c2,c3,c4=st.columns(4)
    for col,lbl,val,unit,clr in [(c1,"Average",avg_v,"µg/m³","#42a5f5"),(c2,"Peak",max_v,"µg/m³","#DC2626"),(c3,"Lowest",min_v,"µg/m³","#16A34A"),(c4,"Readings",len(data),"data points","#EAB308")]:
        with col: st.markdown(stat_html(lbl,val,unit,clr),unsafe_allow_html=True)
    md(f'<p style="font-family:JetBrains Mono,monospace;font-size:11px;color:#4a5a7a;margin:8px 0 0">Data window: {data["timestamp"].min().strftime("%d %b %Y, %H:%M")} → {data["timestamp"].max().strftime("%d %b %Y, %H:%M")}</p>')

    section(st,"Full Timeline")
    fig=go.Figure()
    for loc in data["location_name"].unique():
        ld=data[data["location_name"]==loc]
        fig.add_trace(go.Scatter(x=ld["timestamp"],y=ld["value"],mode="lines",name=loc,line=dict(width=1.8),opacity=0.88))
    if sel_param=="pm25":
        for y,tc,lbl in [(15,"#16A34A","WHO Safe (15)"),(35.4,"#F97316","Moderate"),(55.4,"#DC2626","Unhealthy")]:
            fig.add_hline(y=y,line_dash="dot",line_color=tc,line_width=1,annotation_text=lbl,annotation_font_size=9,annotation_font_color=tc)
    lay=plotly_layout(height=320); lay["yaxis"]["title"]=sel_param; lay["yaxis"]["title_font"]=dict(size=10,color="#4a5a7a")
    fig.update_layout(**lay); st.plotly_chart(fig,use_container_width=True)

    data=data.copy(); data["hour"]=data["timestamp"].dt.hour; data["dayofweek"]=data["timestamp"].dt.day_name()
    ch,cd=st.columns(2)
    with ch:
        section(st,"Hour of Day Pattern")
        ha=data.groupby("hour")["value"].mean().reset_index()
        fig2=go.Figure(go.Bar(x=ha["hour"],y=ha["value"],marker=dict(color="#42a5f5",opacity=0.82,line=dict(width=0)),text=ha["value"].round(1),textposition="outside",textfont=dict(family="JetBrains Mono",size=9,color="#64748B")))
        lay2=plotly_layout(height=280,legend=False); lay2["xaxis"]["title"]="Hour"; lay2["yaxis"]["title"]="Avg Value"
        fig2.update_layout(**lay2); st.plotly_chart(fig2,use_container_width=True)
    with cd:
        section(st,"Day of Week Pattern")
        day_order=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        da=data.groupby("dayofweek")["value"].mean().reindex(day_order).reset_index(); da.columns=["day","value"]
        fig3=go.Figure(go.Bar(x=da["day"],y=da["value"],marker=dict(color="#ab47bc",opacity=0.82,line=dict(width=0)),text=da["value"].round(1),textposition="outside",textfont=dict(family="JetBrains Mono",size=9,color="#64748B")))
        lay3=plotly_layout(height=280,legend=False); lay3["yaxis"]["title"]="Avg Value"
        fig3.update_layout(**lay3); st.plotly_chart(fig3,use_container_width=True)

    section(st,"Download Data")
    st.download_button(f"⬇ Download {sel_city} — {sel_param} as CSV",data.to_csv(index=False),f"airguard_{sel_city}_{sel_param}.csv","text/csv")
