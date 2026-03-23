import streamlit as st, pandas as pd, os
from streamlit_autorefresh import st_autorefresh
import sys; sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from styles import render_nav_button
from styles import *

st.set_page_config(page_title="Health Guide — AirGuard NG",page_icon="🏥",layout="wide")
st.markdown(BASE_CSS,unsafe_allow_html=True)
st_autorefresh(interval=30000,key="hg_r")
def md(h): st.markdown(h,unsafe_allow_html=True)

user_state=st.session_state.get("user_state","")
user_condition=st.session_state.get("user_condition","")
user_name=st.session_state.get("user_name","")
device_status_bar(st,location_label=user_state)
render_nav_button(st)

md('<p style="font-family:Sora,sans-serif;font-size:26px;font-weight:800;color:#F8FAFC;letter-spacing:-.02em;margin:0 0 4px">🏥 Health Guide</p>')
md(f'<p style="font-size:14px;color:#64748B;margin:0 0 24px">Personalised air quality health guidance{" for "+user_condition if user_condition and user_condition not in ["","None"] else ""}{" · "+user_state if user_state else ""}</p>')

@st.cache_data(ttl=300)
def load():
    df=pd.read_csv("transformed_data.csv"); return df
df=load()
device,_=load_device_data()

# ── PERSONALISED BANNER ──────────────────────────────────────
if user_condition and user_condition not in ["","None"]:
    worst=df.loc[df["hrs"].idxmax()]
    wc=RISK_COLORS.get(worst["risk_level"],"#64748B"); wb=RISK_BG.get(worst["risk_level"],"rgba(100,116,139,0.10)"); wbrd=RISK_BORDER.get(worst["risk_level"],"rgba(100,116,139,0.30)")
    md(f"""<div style="background:linear-gradient(135deg,rgba(14,165,233,0.12) 0%,rgba(22,163,74,0.08) 100%);border:1px solid rgba(14,165,233,0.28);border-radius:18px;padding:22px 26px;margin-bottom:24px">
<p style="font-family:Sora,sans-serif;font-size:15px;font-weight:700;color:#38bdf8;margin:0 0 8px">👤 Personalised for {user_name or 'You'} — {user_condition}{' · '+user_state if user_state else ''}</p>
<p style="font-size:14px;color:#94A3B8;line-height:1.7;margin:0 0 10px">{CONDITION_ADVICE.get(user_condition,'')}</p>
<p style="font-size:13px;margin:0">Today's highest risk city is <strong style="color:{wc}">{worst['city']}</strong> with HRS <strong style="color:{wc}">{worst['hrs']}</strong> — <span style="color:{wc}">{worst['risk_level']}</span>. {RISK_ADVICE.get(worst['risk_level'],'')}</p>
</div>""")

# ── CONDITION-SPECIFIC DEEP GUIDE ───────────────────────────
CONDITION_GUIDES = {
    "Asthma": {
        "color":"#F97316","icon":"🫁",
        "triggers":[
            ("PM2.5 Fine Particles","#DC2626","The most dangerous trigger for asthma patients in Nigeria. Particles penetrate deep into your airways and trigger inflammation within minutes of exposure. Lagos traffic during rush hour routinely produces PM2.5 spikes above 100 µg/m³ — 7 times the WHO limit."),
            ("NO₂ Nitrogen Dioxide","#EAB308","Released from generator exhaust and vehicle emissions. NO₂ causes airway narrowing and makes your lungs more sensitive to other triggers. Morning traffic hours (7–10am) produce peak NO₂ concentrations in Lagos and Abuja."),
            ("Ground-Level Ozone","#42a5f5","Forms in sunlight from traffic emissions. Peaks between 2pm and 5pm on sunny days. Ozone damages the lining of your airways and reduces lung function even in moderate concentrations."),
            ("Harmattan Dust (PM10)","#F97316","November to February brings Saharan dust winds across Nigeria. PM10 particles irritate your upper airways and can trigger attacks within hours. This is your most dangerous season."),
        ],
        "daily_plan":[
            ("5:00 AM","Check AirGuard NG. Note your city's HRS before you do anything else."),
            ("6:00 AM","If HRS is below 40, this is your best outdoor window for exercise or commuting."),
            ("7:00–10:00 AM","Peak NO₂ from traffic. Stay indoors or wear N95 mask if commuting."),
            ("Pre-medication","If HRS is Moderate or above and you must go outside, take your reliever inhaler 15–30 minutes before exposure."),
            ("2:00–5:00 PM","Peak ozone. Avoid outdoor exercise during this window on sunny days."),
            ("Evening","Ventilate your home if outdoor HRS is Good. Keep windows closed if Moderate or above."),
        ],
        "warning_signs":["Coughing more than usual","Chest tightness","Shortness of breath after minimal activity","Waking at night to use your inhaler","Using your reliever more than 2 times per week"],
        "emergency":"If you are using your reliever inhaler more than every 4 hours and not improving, go to your nearest hospital immediately. Do not wait."
    },
    "COPD": {
        "color":"#DC2626","icon":"💨",
        "triggers":[
            ("PM2.5 Fine Particles","#DC2626","PM2.5 is the leading environmental cause of COPD exacerbations. Even short-term exposure above 25 µg/m³ increases your risk of hospitalisation. During a bad air quality day in Lagos or Abuja, indoor PM2.5 can be nearly as high as outdoors due to generator exhaust seeping in."),
            ("PM10 Harmattan Dust","#F97316","November to February is your highest risk season. PM10 from Saharan dust settles in your upper airways and causes inflammation that can persist for days after the exposure. Stock your prescriptions before October."),
            ("SO₂ Sulphur Dioxide","#EAB308","Released from burning diesel in generators. SO₂ causes immediate bronchoconstriction in COPD patients and can trigger a severe exacerbation within minutes. Avoid being near running generators."),
            ("CO Carbon Monoxide","#9333EA","Generators produce CO. If you have COPD, even low-level CO exposure significantly reduces your blood oxygen saturation. The AirGuard device monitors for this. Run it continuously at home."),
        ],
        "daily_plan":[
            ("Morning","Check HRS before leaving bed. If above 40, call your doctor for phone guidance before going outside."),
            ("Travel","Plan all trips before 9am or after 7pm when traffic-related pollution is lowest."),
            ("Harmattan Season","Treat every HRS above 30 as your personal danger threshold — more conservative than the general population guideline."),
            ("Medication","Ensure you have at least 2 weeks of your maintenance medication at all times. Never run out during harmattan season."),
            ("Indoor air","Run a fan on days you keep windows closed. Poor indoor ventilation raises CO from cooking and generators."),
        ],
        "warning_signs":["Increased breathlessness compared to your usual","Sputum changing colour to yellow or green","Ankle swelling","Confusion or drowsiness","Bluish tinge to lips or fingernails — emergency"],
        "emergency":"Blue lips or fingernails means dangerously low oxygen. Call emergency services and go to hospital immediately — do not drive yourself."
    },
    "Heart Disease": {
        "color":"#DC2626","icon":"❤️",
        "triggers":[
            ("PM2.5","#DC2626","PM2.5 particles enter your bloodstream directly and cause inflammation in your arteries within hours. Studies show that on high PM2.5 days, hospital admissions for heart attacks rise significantly. In Lagos, PM2.5 during traffic hours regularly exceeds levels that trigger cardiovascular events."),
            ("CO Carbon Monoxide","#9333EA","Generator CO reduces the amount of oxygen your heart muscle receives. For heart patients, even low-level CO exposure can trigger chest pain, arrhythmia, or heart failure episodes. Never stay in a room where a generator is running nearby."),
            ("NO₂","#EAB308","NO₂ causes vascular inflammation and raises blood pressure. Morning traffic hours are your highest risk window. If you commute daily in Lagos or Abuja traffic, you face significant daily cardiovascular stress from air pollution alone."),
            ("Extreme Heat","#F97316","High temperatures combined with poor air quality dramatically increase cardiovascular strain. When AirGuard shows both high HRS and your device reads high temperature, stay indoors with a fan or air conditioning."),
        ],
        "daily_plan":[
            ("Before leaving home","Check HRS. If above 50, call your cardiologist before any outdoor activity."),
            ("7–10 AM","Peak traffic emissions. If you must commute, keep windows up and use air recirculation in your vehicle."),
            ("Exercise","Any outdoor exercise should be before 7am when air quality is best. Cancel planned outdoor exercise on any day HRS is above 40."),
            ("Medications","Take all cardiac medications as prescribed, especially on high pollution days when your heart is under more stress."),
            ("Evenings","Generator CO rises in evenings in most Nigerian homes. Run your AirGuard device continuously and ensure rooms are ventilated."),
        ],
        "warning_signs":["Chest pain or pressure","Unusual shortness of breath","Palpitations (irregular heartbeat)","Dizziness or lightheadedness","Swelling in legs or ankles worsening"],
        "emergency":"Chest pain lasting more than 5 minutes is a medical emergency. Call 112 immediately or go to the nearest hospital. Do not drive yourself."
    },
    "Diabetes": {
        "color":"#EAB308","icon":"🩸",
        "triggers":[
            ("PM2.5 Long-Term Exposure","#DC2626","Research shows that long-term exposure to PM2.5 at Nigerian urban levels (30–80 µg/m³) worsens insulin resistance and makes blood sugar harder to control. On high pollution days, you may find your blood sugar is higher than usual even without dietary changes."),
            ("Ozone (O₃)","#F97316","Ozone causes oxidative stress that disrupts glucose metabolism. Afternoon ozone peaks (2–5pm) in Lagos and Abuja correspond to periods of elevated blood sugar in diabetic patients exposed to outdoor air."),
            ("CO from Generators","#9333EA","CO exposure causes mild hypoxia that stresses the body and raises cortisol levels — which in turn raises blood sugar. Monitor your glucose more carefully on evenings when generators are running nearby."),
        ],
        "daily_plan":[
            ("Morning","Check HRS. On Unhealthy days, plan to monitor your blood sugar more frequently than usual."),
            ("Meals","On high pollution days, your body may process glucose differently. Keep your glucose meter handy and check 2 hours after meals."),
            ("Exercise","Exercise improves insulin sensitivity but outdoor exercise on high-AQ days can worsen oxidative stress. Exercise indoors or in the early morning when HRS is below 30."),
            ("Medication","Never skip diabetes medication on high pollution days. The physiological stress from pollution raises blood sugar and your medication is working harder."),
            ("Feet and circulation","Poor air quality affects peripheral circulation. Check your feet daily and raise any concerns with your doctor immediately."),
        ],
        "warning_signs":["Blood sugar higher than your usual range on multiple consecutive days","Increased thirst or urination","Unusual fatigue — could be pollution-related","Slow-healing cuts or sores","Blurred vision"],
        "emergency":"Blood sugar above 400 mg/dL or below 50 mg/dL requires immediate medical attention. Keep glucagon emergency kit accessible."
    },
    "Hypertension": {
        "color":"#9333EA","icon":"💊",
        "triggers":[
            ("PM2.5","#DC2626","PM2.5 causes measurable blood pressure increases within 1–2 hours of exposure. In a 2022 study, each 10 µg/m³ increase in PM2.5 was associated with a 1–3 mmHg rise in systolic blood pressure. On a Lagos traffic day at 80 µg/m³ PM2.5, your blood pressure may rise by 5–10 mmHg from pollution alone."),
            ("NO₂","#EAB308","NO₂ stiffens blood vessels and raises peripheral vascular resistance — both of which increase blood pressure. Your morning commute through Lagos or Abuja traffic may be raising your blood pressure before you even get to work."),
            ("Noise and Stress","#F97316","High pollution days correlate with heavy traffic, which also means noise stress. Chronic noise exposure raises cortisol and blood pressure independently of air quality."),
        ],
        "daily_plan":[
            ("Morning medication","Take antihypertensive medication at the same time every day without fail. Consistency is especially important on high pollution days."),
            ("Blood pressure check","On any day AirGuard shows HRS above 50 for your city, take your blood pressure morning and evening. Keep a log for your doctor."),
            ("Outdoor activity","Avoid vigorous outdoor exercise when HRS is above 40. Blood pressure peaks during exertion are amplified by PM2.5 exposure."),
            ("Salt and diet","High pollution days increase inflammatory stress. Reduce sodium intake and increase potassium (fruits, vegetables) to help your blood vessels cope."),
            ("Generator exposure","Diesel generator exhaust raises both PM2.5 and blood pressure. Avoid being near running generators, especially while stationary."),
        ],
        "warning_signs":["Blood pressure consistently above your target range","Severe headache especially at the back of the head","Blurred vision","Chest pain or shortness of breath","Nosebleed"],
        "emergency":"Blood pressure above 180/120 mmHg is a hypertensive crisis. Go to hospital immediately even if you feel well."
    },
    "Pregnancy": {
        "color":"#42a5f5","icon":"🤱",
        "triggers":[
            ("PM2.5","#DC2626","There is no safe level of PM2.5 during pregnancy. Fine particles cross the placental barrier and have been found in placental tissue. Nigerian urban PM2.5 levels are consistently above the level associated with premature birth, low birth weight, and developmental effects on the child."),
            ("NO₂","#EAB308","NO₂ exposure during pregnancy is associated with increased risk of preeclampsia and gestational hypertension. Morning traffic hours are the most critical exposure window to avoid."),
            ("CO","#9333EA","Carbon monoxide from generators is particularly dangerous during pregnancy. CO binds to fetal haemoglobin more readily than adult haemoglobin, meaning your baby receives less oxygen. The AirGuard device is especially important in Nigerian homes with generator use."),
            ("Ozone","#F97316","Ozone exposure during pregnancy is linked to reduced foetal growth. Afternoon outdoor exposure during the dry season carries the highest ozone risk."),
        ],
        "daily_plan":[
            ("Every morning","Check AirGuard NG. This is non-negotiable during pregnancy. Any day your city is above WHO safe levels requires you to limit outdoor time."),
            ("Transport","If commuting, keep vehicle windows closed and use air recirculation. Avoid okada and keke during traffic hours — open-air exposure to traffic pollution is highest for these passengers."),
            ("Generator safety","Never run a generator within 10 metres of where you sleep or spend time. Ensure windows and doors near the generator are sealed. The AirGuard device will alert you to dangerous CO accumulation."),
            ("Prenatal visits","Bring your AirGuard NG weekly exposure summary to every prenatal appointment. Your doctor needs to know about your pollution exposure, especially if you live near a road or in a high-traffic area."),
            ("Nutrition","Vitamins C, E, and folate help your body defend against oxidative stress from air pollution. Maintain a balanced diet with fruits and vegetables, especially on high pollution days."),
        ],
        "warning_signs":["Reduced fetal movement (less than 10 movements in 2 hours)","Severe headache or visual changes","Sudden swelling in face or hands","Vaginal bleeding","Difficulty breathing or shortness of breath at rest"],
        "emergency":"Any sudden change in your baby's movements or bleeding requires immediate hospital attendance. Do not wait to see if it improves."
    },
    "Child Under 12": {
        "color":"#26c6da","icon":"👶",
        "triggers":[
            ("PM2.5","#DC2626","Children's lungs are still developing until age 18. PM2.5 exposure during childhood permanently reduces lung capacity — this effect cannot be reversed in adulthood. Nigerian urban PM2.5 levels are exposing millions of children to lifetime health consequences. Treat the WHO safe limit as a maximum, not a target."),
            ("NO₂","#EAB308","NO₂ is a major cause of childhood asthma development. Children living near roads with high traffic density have significantly higher rates of asthma. Morning school commutes through Lagos traffic are a daily NO₂ exposure event."),
            ("PM10 Harmattan","#F97316","Children are more affected by harmattan dust than adults because they breathe more air relative to body weight. During November to February, reduce outdoor playtime dramatically on any day where the air has a dusty or hazy quality."),
        ],
        "daily_plan":[
            ("School morning","Check HRS before sending your child to school. On Unhealthy days, consider keeping your child indoors if possible."),
            ("School transport","If your child walks to school or takes public transport, schedule it before 7am or after 7pm to avoid peak traffic pollution. On harmattan days, consider a face mask."),
            ("Outdoor play","Afternoon outdoor play should be limited to before 2pm or after 6pm (ozone risk). On any day HRS is above 40, restrict outdoor playtime to under 30 minutes."),
            ("Indoor air","Keep your child away from rooms where a generator is running nearby. Children are more susceptible to CO poisoning than adults."),
            ("Signs to watch","Persistent cough, frequent respiratory infections, or unusual fatigue after normal activity may indicate pollution-related effects. Discuss with your paediatrician."),
        ],
        "warning_signs":["Persistent cough for more than 2 weeks","Wheezing or high-pitched breathing sounds","Frequent respiratory infections","Unusual shortness of breath during play","Bluish tinge to lips — emergency"],
        "emergency":"A child with laboured breathing, blue lips, or stridor (high-pitched breathing sound) requires emergency hospital treatment immediately."
    },
    "None": {
        "color":"#16A34A","icon":"👤",
        "triggers":[
            ("PM2.5","#F97316","Even healthy individuals are affected by sustained PM2.5 exposure above WHO limits. Long-term exposure at Nigerian urban levels is associated with reduced life expectancy, cardiovascular disease development, and cognitive effects. The impact builds silently over years."),
            ("Peak Traffic Hours","#EAB308","Lagos and Abuja traffic hours (7–10am, 4–7pm) produce acute PM2.5 and NO₂ spikes that cause measurable inflammation in healthy lungs. Frequent commuters face cumulative daily exposure."),
        ],
        "daily_plan":[
            ("Daily habit","Check AirGuard NG every morning. 10 seconds of awareness could save you from a preventable exposure event."),
            ("Exercise","Exercise before 7am or after 7pm when traffic pollution is lowest. Avoid jogging along roads during traffic hours."),
            ("Commuting","On days HRS is above 40, close vehicle windows and use air recirculation. If using public transport, consider an N95 mask."),
        ],
        "warning_signs":["Persistent dry cough","Unusual fatigue after normal activity","Eye irritation on bad air quality days"],
        "emergency":"Consult a doctor if you experience persistent respiratory symptoms after high pollution days."
    },
}

guide=CONDITION_GUIDES.get(user_condition, CONDITION_GUIDES["None"])
cond_color=guide["color"]; cond_icon=guide["icon"]

# ── TRIGGERS ─────────────────────────────────────────────────
section(st,f"⚠️ Your Key Pollution Triggers{' — '+user_condition if user_condition and user_condition not in ['','None'] else ''}")
for trig_name,trig_color,trig_body in guide["triggers"]:
    md(f"""<div style="background:#111827;border:1px solid rgba(255,255,255,0.07);border-left:4px solid {trig_color};border-radius:14px;padding:18px;margin-bottom:12px">
<p style="font-family:Sora,sans-serif;font-size:14px;font-weight:700;color:{trig_color};margin:0 0 8px">{trig_name}</p>
<p style="font-size:13px;color:#94A3B8;line-height:1.75;margin:0">{trig_body}</p></div>""")

# ── DAILY PLAN ───────────────────────────────────────────────
section(st,f"📅 Your Daily Air Quality Action Plan{' in '+user_state if user_state else ''}")
for time_lbl,action in guide["daily_plan"]:
    md(f"""<div style="display:flex;gap:14px;padding:12px 0;border-bottom:1px solid rgba(255,255,255,0.04);align-items:flex-start">
<div style="min-width:110px;flex-shrink:0"><span style="font-family:JetBrains Mono,monospace;font-size:11px;font-weight:600;color:{cond_color};background:{cond_color}18;padding:3px 10px;border-radius:6px">{time_lbl}</span></div>
<p style="font-size:13px;color:#94A3B8;line-height:1.65;margin:0">{action}</p></div>""")

# ── WARNING SIGNS ─────────────────────────────────────────────
section(st,"🔴 Warning Signs — When to See a Doctor")
c1,c2=st.columns(2)
signs=guide["warning_signs"]
mid=len(signs)//2+len(signs)%2
for col,sign_list in [(c1,signs[:mid]),(c2,signs[mid:])]:
    with col:
        for s in sign_list:
            md(f'<div style="display:flex;align-items:flex-start;gap:10px;padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.04)"><div style="width:8px;height:8px;border-radius:50%;background:#DC2626;flex-shrink:0;margin-top:5px"></div><p style="font-size:13px;color:#94A3B8;margin:0">{s}</p></div>')

# ── EMERGENCY ────────────────────────────────────────────────
md(f"""<div style="background:rgba(220,38,38,0.10);border:1px solid rgba(220,38,38,0.30);border-radius:14px;padding:18px 20px;margin-top:20px">
<p style="font-family:Sora,sans-serif;font-size:14px;font-weight:700;color:#DC2626;margin:0 0 8px">🚨 Emergency Guidance</p>
<p style="font-size:13px;color:#94A3B8;line-height:1.7;margin:0">{guide['emergency']}</p>
<div style="display:flex;gap:12px;flex-wrap:wrap;margin-top:12px">
<span style="background:rgba(220,38,38,0.12);color:#DC2626;border:1px solid rgba(220,38,38,0.28);padding:4px 14px;border-radius:999px;font-size:12px;font-weight:600">📞 Emergency: 112</span>
<span style="background:rgba(220,38,38,0.12);color:#DC2626;border:1px solid rgba(220,38,38,0.28);padding:4px 14px;border-radius:999px;font-size:12px;font-weight:600">📞 Lagos Fire: 01-7944996</span></div></div>""")

# ── HRS SCALE ─────────────────────────────────────────────────
section(st,"📊 Health Risk Score — What Each Level Means For You")
LEVELS=[("Good","HRS 0–20","#16A34A","Air quality is safe. Go outside freely, exercise outdoors, open your windows."),
        ("Moderate","HRS 21–40","#EAB308","Acceptable for most people. If you have "+str(user_condition or "a health condition")+", reduce prolonged outdoor exertion."),
        ("Unhealthy for Sensitive Groups","HRS 41–60","#F97316","Chronic disease patients must reduce outdoor activity. Healthy adults should limit strenuous exercise outside."),
        ("Unhealthy","HRS 61–80","#DC2626","Everyone should reduce outdoor time. Patients must stay indoors, keep windows closed, take medications on schedule."),
        ("Very Unhealthy","HRS 81–99","#9333EA","Health alert. All outdoor activity must stop. Vulnerable patients must not go outside at all."),
        ("Hazardous","HRS 100","#7E22CE","Emergency. Everyone is at risk. Seek shelter. Call 112 if breathing becomes difficult.")]
for name,rng,color,body in LEVELS:
    md(f"""<div style="background:{color}10;border:1px solid {color}28;border-radius:12px;padding:14px 20px;margin-bottom:10px;display:flex;align-items:flex-start;gap:16px;flex-wrap:wrap">
<div style="min-width:220px;flex-shrink:0"><p style="font-family:Sora,sans-serif;font-size:14px;font-weight:700;color:{color};margin:0">{name}</p><p style="font-family:JetBrains Mono,monospace;font-size:11px;color:#64748B;margin:3px 0 0">{rng}</p></div>
<p style="font-size:13px;color:#94A3B8;line-height:1.55;flex:1;margin:0">{body}</p></div>""")

md('<div style="background:#111827;border:1px solid rgba(255,255,255,0.06);border-radius:12px;padding:16px 20px;margin-top:24px"><p style="font-size:12px;color:#4a5a7a;margin:0;line-height:1.8">⚕️ <strong style="color:#64748B">Medical Disclaimer:</strong> AirGuard NG provides environmental monitoring data for informational purposes only. It is not a substitute for professional medical advice, diagnosis, or treatment. Always consult your doctor regarding your specific health condition.</p></div>')
