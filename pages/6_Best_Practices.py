import streamlit as st, pandas as pd, os
from streamlit_autorefresh import st_autorefresh
import sys; sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from styles import render_nav_button
from styles import *

st.set_page_config(page_title="Best Practices — AirGuard NG",page_icon="✅",layout="wide")
st.markdown(BASE_CSS,unsafe_allow_html=True)
st_autorefresh(interval=30000,key="bp_r")
def md(h): st.markdown(h,unsafe_allow_html=True)

user_state=st.session_state.get("user_state","")
user_condition=st.session_state.get("user_condition","")
user_name=st.session_state.get("user_name","")
device_status_bar(st,location_label=user_state)
render_nav_button(st)

md('<p style="font-family:Sora,sans-serif;font-size:26px;font-weight:800;color:#F8FAFC;letter-spacing:-.02em;margin:0 0 4px">✅ Best Practices</p>')
md(f'<p style="font-size:14px;color:#64748B;margin:0 0 24px">Evidence-based safety protocols for every risk level{" — personalised for "+user_condition if user_condition and user_condition not in ["","None"] else ""}{" · "+user_state if user_state else ""}</p>')

@st.cache_data(ttl=300)
def load():
    df=pd.read_csv("transformed_data.csv"); return df
df=load()
device,_=load_device_data()

# ── TODAY'S STATUS BANNER ───────────────────────────────────
worst=df.loc[df["hrs"].idxmax()]
wc=RISK_COLORS.get(worst["risk_level"],"#64748B"); wb=RISK_BG.get(worst["risk_level"],"rgba(100,116,139,0.10)"); wbrd=RISK_BORDER.get(worst["risk_level"],"rgba(100,116,139,0.30)")
best=df.loc[df["hrs"].idxmin()]
bc=RISK_COLORS.get(best["risk_level"],"#64748B")

md(f"""<div style="background:#111827;border:1px solid rgba(255,255,255,0.07);border-radius:16px;padding:20px 24px;margin-bottom:24px;display:flex;gap:24px;flex-wrap:wrap">
<div style="flex:1;min-width:200px">
<p style="font-size:11px;font-weight:600;color:#64748B;text-transform:uppercase;letter-spacing:.07em;margin:0 0 6px">Today's Action Level</p>
<p style="font-family:Sora,sans-serif;font-size:1.8rem;font-weight:800;color:{wc};margin:0">{worst['risk_level']}</p>
<p style="font-size:12px;color:#64748B;margin:4px 0 0">Highest risk: {worst['city']} · HRS {worst['hrs']}</p></div>
<div style="flex:1;min-width:200px">
<p style="font-size:11px;font-weight:600;color:#64748B;text-transform:uppercase;letter-spacing:.07em;margin:0 0 6px">Safest Location</p>
<p style="font-family:Sora,sans-serif;font-size:1.8rem;font-weight:800;color:{bc};margin:0">{best['city']}</p>
<p style="font-size:12px;color:#64748B;margin:4px 0 0">HRS {best['hrs']} · {best['risk_level']}</p></div>
<div style="flex:1;min-width:200px">
<p style="font-size:11px;font-weight:600;color:#64748B;text-transform:uppercase;letter-spacing:.07em;margin:0 0 6px">Your Condition</p>
<p style="font-family:Sora,sans-serif;font-size:1.4rem;font-weight:700;color:#42a5f5;margin:0">{user_condition or 'Not set'}</p>
<p style="font-size:12px;color:#64748B;margin:4px 0 0">{user_state or 'Location not set'}</p></div></div>""")

# ── CONDITION-SPECIFIC PRACTICES ─────────────────────────────
COND_PRACTICES = {
    "Asthma": [
        ("Check AirGuard NG before leaving home","Every single morning before going outside. This is non-negotiable. The 10 seconds it takes to check your city's HRS could prevent your next emergency visit.","#16A34A"),
        ("Pre-medicate on moderate or worse days","If HRS is 21 or above and you must go outside, take your reliever inhaler 15–30 minutes before exposure. Do not wait for symptoms — by then your airways are already inflamed.","#42a5f5"),
        ("Avoid the 7–10am traffic window","This is when NO₂ concentrations peak in Lagos and Abuja. If your commute is during this window, close all vehicle windows and use air recirculation. If you take public transport, consider an N95 mask.","#EAB308"),
        ("Carry your inhaler everywhere, always","When HRS is above 40, carry both your reliever and preventer inhalers. Do not rely on having one available at your destination.","#F97316"),
        ("Stock medication before harmattan","Every October, ensure you have at least one month's supply of your asthma medications. November to February is your highest-risk season and medication shortages during this period are dangerous.","#9333EA"),
        ("Keep a symptom diary","Record your peak flow readings and symptoms alongside AirGuard NG readings. This gives your doctor invaluable data for optimising your treatment.","#26c6da"),
    ],
    "COPD": [
        ("Treat HRS 30 as your personal red line","For COPD patients, the safe threshold is lower than the general population. Any HRS above 30 should trigger precautions. Do not wait for Unhealthy classifications designed for healthy adults.","#DC2626"),
        ("Prepare your exacerbation action plan now","Work with your doctor to have a written plan for what to do when your symptoms worsen. Keep prednisolone and antibiotics at home if your doctor has prescribed them for self-management.","#F97316"),
        ("Never enter a room with a running generator","Generator exhaust contains SO₂, NO₂, and CO — all three are dangerous for COPD patients. Even brief exposure can trigger an exacerbation that requires hospitalisation.","#EAB308"),
        ("Pulmonary rehabilitation exercises indoors","On bad air quality days, maintain your breathing exercises and physical conditioning indoors with a fan for ventilation. Deconditioning during bad air periods worsens long-term outcomes.","#42a5f5"),
        ("Nutrition and hydration","Adequate nutrition supports respiratory muscle strength. Dehydration thickens mucus secretions. On harmattan days, drink more water to help keep airways clear.","#16A34A"),
        ("Annual flu and pneumonia vaccination","Respiratory infections trigger COPD exacerbations. Get vaccinated every year before the harmattan season starts. Discuss with your doctor.","#9333EA"),
    ],
    "Heart Disease": [
        ("Morning blood pressure log","On any day AirGuard shows your city above Moderate, take your blood pressure morning and evening. Bring 2 weeks of readings to your next cardiology appointment.","#DC2626"),
        ("Avoid morning traffic exposure","The 7–10am traffic window combines peak PM2.5, NO₂, and CO exposure with your body's naturally higher blood pressure in the morning. This combination is the highest-risk window for cardiac events.","#F97316"),
        ("Never skip cardiac medications","On high pollution days, your heart is under additional physiological stress. This is the worst time to miss a dose of your blood thinners, beta blockers, or antihypertensives.","#EAB308"),
        ("Keep GTN spray accessible","If your doctor has prescribed GTN (glyceryl trinitrate) spray for angina, keep it with you on all days HRS is above 40. High pollution days increase the probability of angina episodes.","#42a5f5"),
        ("Recognise pollution-related symptoms","Shortness of breath, chest pressure, unusual fatigue, or palpitations on a high pollution day should be treated the same as cardiac symptoms — do not attribute them to pollution and wait.","#9333EA"),
        ("Indoor air quality matters too","Generator CO at night is a significant cardiac risk. Run your AirGuard device in your bedroom. Ensure adequate ventilation. If the gas alert sounds, open windows immediately.","#16A34A"),
    ],
    "Diabetes": [
        ("Increase glucose monitoring on high AQ days","On any day HRS is above 40, check your blood sugar 2 hours after each meal in addition to your usual schedule. Pollution-induced cortisol rise makes blood sugar harder to control.","#EAB308"),
        ("Maintain medication schedule absolutely","Never skip or delay diabetes medications on high pollution days. The physiological stress of pollution raises blood sugar and your medication needs to be working.","#DC2626"),
        ("Exercise before 7am or indoors","Physical activity is critical for glucose control but outdoor exercise during traffic hours exposes you to peak pollution. Exercise before 7am, at a gym, or indoors.","#42a5f5"),
        ("Protect peripheral circulation","PM2.5 damages small blood vessels — critical for diabetic foot health. Inspect your feet daily, keep them moisturised, and wear properly fitting footwear. Report any sore or wound to your doctor immediately.","#F97316"),
        ("Anti-oxidant nutrition","Vitamins C and E help neutralise pollution-induced oxidative stress that worsens insulin resistance. Include fruits, vegetables, and nuts in your diet, especially on high pollution days.","#16A34A"),
        ("Generator CO awareness","CO exposure raises cortisol which raises blood sugar. If you live in an area with frequent generator use, run your AirGuard device continuously and ensure ventilation.","#9333EA"),
    ],
    "Hypertension": [
        ("Monitor blood pressure twice daily on high AQ days","On any day HRS is above 40 for your city, check your blood pressure morning and evening. Keep a log. Share it with your doctor. This data is clinically valuable.","#9333EA"),
        ("Take antihypertensive medication at the same time daily","Consistency is more important on high pollution days. Even missing one dose when PM2.5 is elevated can allow blood pressure to spike to dangerous levels.","#DC2626"),
        ("Reduce dietary sodium on high pollution days","Salt raises blood pressure independently of pollution. On days when pollution is already elevating your blood pressure, cutting sodium reduces the combined load on your cardiovascular system.","#EAB308"),
        ("Avoid traffic exposure when possible","Commuting through Lagos or Abuja traffic is a daily blood pressure stress event. If you can leave before 7am or after 9am, your morning blood pressure will be meaningfully lower.","#F97316"),
        ("Manage stress alongside air quality","Stress and pollution compound each other's blood pressure effects. On high AQ days, practice stress reduction — prayer, breathing exercises, or meditation — to reduce the combined cardiovascular load.","#42a5f5"),
        ("Know your target blood pressure number","Ask your doctor for your personalised target. On high pollution days, if your reading exceeds your upper limit, contact your doctor rather than waiting for your next appointment.","#16A34A"),
    ],
    "Pregnancy": [
        ("Check AirGuard NG before any outdoor activity","During pregnancy, you are making decisions for two. This is the most important daily habit you can build. Any day above WHO limits requires you to limit outdoor time.","#42a5f5"),
        ("Eliminate generator exposure at home","Never run a generator within 10 metres of where you sleep or spend time. CO is invisible and odourless but crosses the placental barrier rapidly. The AirGuard device is essential equipment for Nigerian pregnant women.","#DC2626"),
        ("Change commute timing and mode","If you commute, shift to before 7am or after 8pm to avoid peak traffic pollution. If you use okada or keke, consider switching to vehicles with windows for the duration of your pregnancy.","#EAB308"),
        ("Prenatal nutrition to combat pollution stress","Folic acid, iron, omega-3s, and antioxidants help protect both you and your baby from pollution-induced oxidative stress. Discuss supplementation with your obstetrician.","#16A34A"),
        ("Document your exposure for your antenatal record","Keep a weekly log of your city's AirGuard NG HRS readings and bring it to every antenatal appointment. Pollution exposure data helps your doctor assess and manage risk more effectively.","#9333EA"),
        ("Indoor air quality in your sleeping area","Ensure your bedroom is well ventilated on good air quality days and sealed on bad ones. Avoid cooking in enclosed spaces with charcoal or firewood during pregnancy.","#F97316"),
    ],
    "Child Under 12": [
        ("Check AirGuard NG before school every morning","This should become as automatic as checking the weather. On Unhealthy days, consider keeping your child home if possible or limiting outdoor time at school.","#26c6da"),
        ("Schedule outdoor play before 2pm or after 6pm","This avoids the afternoon ozone peak (2–5pm) and the evening traffic peak. Early morning outdoor play before 7am is the safest window in most Nigerian cities.","#16A34A"),
        ("N95 masks for school commutes on bad air days","A well-fitted children's N95 mask reduces PM2.5 inhalation by 95%. On any day HRS is above 50, consider a mask for your child's school commute, especially if they walk or use public transport.","#42a5f5"),
        ("Keep children away from generator exhaust","Children are more susceptible to CO poisoning than adults. Never allow children to play near a running generator. The AirGuard device should alert you before CO reaches dangerous levels.","#DC2626"),
        ("Harmattan season precautions (Nov–Feb)","During harmattan, reduce outdoor play dramatically. Keep children indoors during the peak dusty hours (10am–4pm). Saline nasal rinses can help clear inhaled dust particles.","#F97316"),
        ("Discuss air quality at school","Talk to your child's school about checking air quality before outdoor activities. Many schools in Nigeria have no air quality awareness protocols. Parent advocacy for this change is impactful.","#9333EA"),
    ],
    "None": [
        ("Build the daily AirGuard NG check habit","Check before leaving home every morning. This single habit, consistently maintained, gives you the information to make better decisions about your day.","#16A34A"),
        ("Exercise before 7am for cleanest air","Traffic-related PM2.5 and NO₂ are at their lowest before rush hour. If you exercise outdoors, this is your optimal window in any Nigerian city.","#42a5f5"),
        ("Use air recirculation during traffic commutes","Keep vehicle windows closed during traffic jams and use internal air recirculation. This reduces your PM2.5 exposure by up to 70% compared to open windows.","#EAB308"),
        ("N95 for unavoidable high exposure","Standard surgical masks do not filter PM2.5. If you must be outdoors on an Unhealthy day, only N95 or KN95 masks provide meaningful protection.","#F97316"),
        ("Generator safety","Never run a generator inside, in an attached garage, or within 3 metres of any open window. CO is the leading cause of indoor air poisoning deaths in Nigeria.","#9333EA"),
    ],
}

practices=COND_PRACTICES.get(user_condition,COND_PRACTICES["None"])
section(st,f"✅ Your Personalised Best Practices{' — '+user_condition if user_condition and user_condition not in ['','None'] else ''}")
for i,(title,body,color) in enumerate(practices):
    md(f"""<div style="display:flex;gap:16px;padding:16px 0;border-bottom:1px solid rgba(255,255,255,0.04);align-items:flex-start">
<div style="width:28px;height:28px;border-radius:50%;background:{color}20;color:{color};border:1px solid {color}40;display:flex;align-items:center;justify-content:center;font-family:JetBrains Mono,monospace;font-size:12px;font-weight:700;flex-shrink:0;margin-top:2px">{i+1}</div>
<div><p style="font-family:Sora,sans-serif;font-size:14px;font-weight:700;color:#CBD5E1;margin:0 0 5px">{title}</p>
<p style="font-size:13px;color:#64748B;line-height:1.75;margin:0">{body}</p></div></div>""")

# ── RISK LEVEL ACTIONS ────────────────────────────────────────
section(st,"🎯 What To Do at Each Risk Level")
ACTIONS=[
    ("Good · HRS 0–20","#16A34A","Go outside freely. Exercise outdoors. Open windows. All activities are safe today."+(f" {user_condition} patients can engage in all normal outdoor activities." if user_condition and user_condition not in ["","None"] else "")),
    ("Moderate · HRS 21–40","#EAB308","Acceptable for most people. "+("Take your rescue medication preemptively if going outside." if user_condition and user_condition not in ["","None"] else "Sensitive individuals should consider reducing prolonged outdoor exertion.")),
    ("Sensitive Groups · HRS 41–60","#F97316",""+("As a "+user_condition+" patient, avoid outdoor activity. Wear N95 if unavoidable. Pre-medicate." if user_condition and user_condition not in ["","None"] else "Chronic disease patients must reduce outdoor activity. Healthy adults should limit strenuous exercise.")),
    ("Unhealthy · HRS 61–80","#DC2626","Everyone should reduce outdoor time. "+("As a "+user_condition+" patient, stay indoors with windows closed and all medications on schedule." if user_condition and user_condition not in ["","None"] else "All patients must stay indoors. Avoid cooking with charcoal indoors.")),
    ("Very Unhealthy · HRS 81–99","#9333EA","Health emergency for all. Stay indoors. "+("Call your specialist if you develop symptoms." if user_condition and user_condition not in ["","None"] else "Contact your doctor if symptoms worsen.")),
    ("Hazardous · HRS 100","#7E22CE","Maximum emergency. Do not go outside. Seek medical attention immediately if breathing is difficult. Call 112."),
]
for level,color,action in ACTIONS:
    md(f"""<div style="background:{color}10;border:1px solid {color}28;border-left:4px solid {color};border-radius:12px;padding:14px 20px;margin-bottom:10px;display:flex;align-items:flex-start;gap:16px;flex-wrap:wrap">
<span style="background:{color}20;color:{color};padding:4px 14px;border-radius:999px;font-size:11px;font-weight:700;font-family:JetBrains Mono,monospace;white-space:nowrap;flex-shrink:0;display:inline-block;margin-top:2px">{level}</span>
<p style="font-size:13px;color:#94A3B8;line-height:1.65;flex:1;margin:0">{action}</p></div>""")

# ── NIGERIA-SPECIFIC TIPS ─────────────────────────────────────
section(st,"🇳🇬 Nigeria-Specific Protective Measures")
TIPS=[
    ("😷","#42a5f5","N95 Masks","Standard surgical masks do not filter PM2.5. Only N95 or KN95 masks provide protection. Use one whenever HRS is Unhealthy or above and outdoor exposure is unavoidable."),
    ("⚡","#EAB308","Generator Safety","Never run a generator inside the house or within 3 metres of any open window. CO from generators is the leading cause of indoor air poisoning in Nigeria. The AirGuard device monitors for this."),
    ("🌬️","#F97316","Harmattan Season","November to February brings Saharan dust. Stock all prescription medications before October. Children and elderly should stay indoors on peak harmattan mornings (dust visible in air)."),
    ("🏠","#16A34A","Indoor Ventilation","Ventilate well on Good air days to clear cooking fumes, dust, and CO residue. Seal your home on Unhealthy days. The quality difference between a ventilated and sealed room on a bad air day is significant."),
    ("💧","#26c6da","Hydration","Adequate water intake helps your respiratory tract clear inhaled particles. On high pollution days, increase water intake and avoid alcohol which dehydrates the respiratory lining."),
    ("🚗","#9333EA","Commuter Protection","Danfo, okada, and keke passengers face the highest traffic pollution exposure. On days HRS is Moderate or above, consider a mask for your commute or shift your travel timing by 1–2 hours to avoid rush hour."),
]
t1,t2,t3=st.columns(3)
for i,(icon,color,title,body) in enumerate(TIPS):
    with [t1,t2,t3][i%3]:
        md(f"""<div style="background:#111827;border:1px solid rgba(255,255,255,0.07);border-top:3px solid {color};border-radius:14px;padding:18px;margin-bottom:14px;text-align:center">
<p style="font-size:1.8rem;margin:0 0 8px">{icon}</p>
<p style="font-family:Sora,sans-serif;font-size:14px;font-weight:700;color:{color};margin:0 0 8px">{title}</p>
<p style="font-size:13px;color:#94A3B8;line-height:1.65;text-align:left;margin:0">{body}</p></div>""")
