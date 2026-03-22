"""
AirGuard NG — Telegram Alert Bot
===================================
Sends automatic alerts when:
  - Any city air quality reaches Unhealthy or worse
  - Arduino device gas level reaches BAD or worse (raw >= 250)

Commands:
  /status  — live city air quality readings
  /device  — latest hardware sensor reading
  /help    — show all commands

Run: python telegram_bot.py
"""

import os, json, time, requests, pandas as pd
from datetime import datetime
from styles import load_device_data, classify_gas, gas_is_dangerous, RISK_ADVICE

BOT_TOKEN = "8735966522:AAEkM9gnlILy5Qc6ejkAoWBKCxWSyDwHmJ4"
CHAT_ID   = "6436519383"
USER_NAME = "Oluwatobi"
BASE_URL  = f"https://api.telegram.org/bot{BOT_TOKEN}"

POLL_EVERY  = 30   # seconds between threshold checks
CMD_EVERY   =  3   # seconds between command polls

RISK_ORDER = ["Good","Moderate","Unhealthy for Sensitive Groups",
              "Unhealthy","Very Unhealthy","Hazardous"]
RISK_EMOJI = {
    "Good":"🟢","Moderate":"🟡","Unhealthy for Sensitive Groups":"🟠",
    "Unhealthy":"🔴","Very Unhealthy":"🟣","Hazardous":"☠️","No Data":"⚫",
}
STATE_FLAG = {
    "Lagos State":"🏙","Ogun State":"🌿",
    "Cross River State":"🌊","FCT Abuja":"🏛",
}

_alerted_cities = set()
_alerted_gas    = False
_last_update_id = 0


# ── TELEGRAM ─────────────────────────────────────────────────
def send(text: str):
    try:
        r = requests.post(
            f"{BASE_URL}/sendMessage",
            data={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"},
            timeout=10,
        )
        if r.status_code != 200:
            print(f"  Telegram error {r.status_code}: {r.text[:100]}")
    except Exception as e:
        print(f"  Send failed: {e}")

def get_updates(offset=0):
    try:
        r = requests.get(
            f"{BASE_URL}/getUpdates",
            params={"offset": offset, "timeout": 2, "limit": 10},
            timeout=8,
        )
        return r.json().get("result", [])
    except Exception:
        return []


# ── DATA ─────────────────────────────────────────────────────
def load_aq():
    try:    return pd.read_csv("transformed_data.csv")
    except: return pd.DataFrame()

def is_worse_or_equal(risk_a, risk_b):
    a = RISK_ORDER.index(risk_a) if risk_a in RISK_ORDER else -1
    b = RISK_ORDER.index(risk_b) if risk_b in RISK_ORDER else -1
    return a >= b


# ── MESSAGE BUILDERS ─────────────────────────────────────────
def msg_status():
    df = load_aq()
    if df.empty:
        return "⚠️ No air quality data yet. Run extraction.py first."
    now = datetime.now().strftime("%d %b %Y, %H:%M")
    lines = [f"🛡 <b>AirGuard NG — Live Status</b>", f"<i>{now}</i>", ""]
    for _, row in df.iterrows():
        city  = row["city"]
        emoji = RISK_EMOJI.get(row["risk_level"], "⚫")
        flag  = STATE_FLAG.get(city, "📍")
        lines.append(
            f"{flag} <b>{city}</b>\n"
            f"   {emoji} HRS <b>{row['hrs']}</b> · PM2.5 {round(row['value'],1)} µg/m³\n"
            f"   <i>{row['risk_level']}</i>"
        )
    lines += ["", "Send /device for hardware readings."]
    return "\n".join(lines)

def msg_device():
    device, _ = load_device_data()
    if not device:
        return ("📡 <b>AirGuard Device</b>\n\n"
                "Not connected. Run <code>serial_reader.py</code> "
                "and connect your Arduino via USB.")
    raw  = device.get("gas_raw", 0)
    ppm  = device.get("gas_ppm", "—")
    temp = device.get("temperature", "—")
    hum  = device.get("humidity", "—")
    risk = device.get("risk_level", "—")
    gl, gc, _, _, gi, _ = classify_gas(raw)
    ts = "—"
    try: ts = datetime.fromisoformat(device.get("timestamp","")).strftime("%d %b %Y, %H:%M:%S")
    except: pass
    return (f"🔩 <b>AirGuard Device — Live Reading</b>\n\n"
            f"📟 Device: <code>{device.get('device_id','airguard-uno-01')}</code>\n"
            f"🕐 Time:   {ts}\n\n"
            f"{gi} Gas PPM:    <b>{ppm}</b> ({gl})\n"
            f"🌡 Temp:       <b>{temp} °C</b>\n"
            f"💧 Humidity:   <b>{hum} %</b>\n"
            f"⚡ Risk level: <b>{risk}</b>")

def alert_aq(city, hrs, risk, pm25):
    emoji = RISK_EMOJI.get(risk, "🔴")
    flag  = STATE_FLAG.get(city, "📍")
    advice = RISK_ADVICE.get(risk, "")
    return (f"🚨 <b>Air Quality Alert — {city}</b>\n\n"
            f"{flag} {emoji} <b>{risk}</b>\n"
            f"HRS: <b>{hrs}</b> · PM2.5: <b>{pm25} µg/m³</b>\n\n"
            f"⚕️ {advice}\n\n"
            f"<i>Open AirGuard NG dashboard for full details.</i>")

def alert_gas(ppm, raw, risk):
    return (f"🔥 <b>GAS DANGER ALERT — AirGuard Device</b>\n\n"
            f"⚡ Gas level:  <b>{ppm} PPM</b> (raw: {raw})\n"
            f"🚨 Risk level: <b>{risk}</b>\n\n"
            f"<b>Take immediate action:</b>\n"
            f"• Open ALL windows and doors now\n"
            f"• Do NOT use any electrical switches\n"
            f"• Turn off gas cylinder at the source\n"
            f"• Evacuate the room immediately\n\n"
            f"🆘 Lagos Fire Service: <b>01-7944996</b>\n"
            f"🆘 Emergency:          <b>112</b>\n"
            f"🆘 NEMA:               <b>0800-CALLNEMA</b>")

def clear_gas_alert(ppm):
    return (f"✅ <b>Gas Level Cleared — AirGuard Device</b>\n\n"
            f"Gas concentration has dropped to <b>{ppm} PPM</b> — now safe.\n"
            f"Ensure area is well ventilated before re-entering.")


# ── COMMAND HANDLER ──────────────────────────────────────────
def handle(text: str):
    cmd = text.strip().lower().split()[0]
    if cmd in ["/start", "/help"]:
        send(f"👋 Hello {USER_NAME}!\n\n"
             f"🛡 <b>AirGuard NG Alert Bot</b>\n\n"
             f"I monitor Nigeria's air quality and your indoor gas sensor "
             f"and alert you automatically when conditions become dangerous.\n\n"
             f"<b>Commands:</b>\n"
             f"/status  — live air quality for all monitored cities\n"
             f"/device  — latest reading from your hardware sensor\n"
             f"/help    — show this message\n\n"
             f"<i>Automatic alerts fire when any city reaches Unhealthy "
             f"or your device gas level reaches the BAD threshold.</i>")
    elif cmd == "/status": send(msg_status())
    elif cmd == "/device": send(msg_device())
    else: send(f"Unknown command: <code>{text}</code>\nSend /help to see commands.")


# ── THRESHOLD CHECKER ────────────────────────────────────────
def check_thresholds():
    global _alerted_cities, _alerted_gas

    # Air quality
    df = load_aq()
    if not df.empty:
        for _, row in df.iterrows():
            city = row["city"]
            risk = row["risk_level"]
            if is_worse_or_equal(risk, "Unhealthy"):
                if city not in _alerted_cities:
                    _alerted_cities.add(city)
                    print(f"  [AQ ALERT] {city} → {risk}")
                    send(alert_aq(city, row["hrs"], risk, round(row["value"],1)))
                    time.sleep(1)
            else:
                _alerted_cities.discard(city)

    # Gas / hardware
    device, _ = load_device_data()
    if device:
        raw  = int(device.get("gas_raw", 0) or 0)
        ppm  = device.get("gas_ppm", 0)
        risk = device.get("risk_level", "Safe")
        if gas_is_dangerous(raw):
            if not _alerted_gas:
                _alerted_gas = True
                print(f"  [GAS ALERT] {ppm} PPM — {risk}")
                send(alert_gas(ppm, raw, risk))
        else:
            if _alerted_gas:
                # Gas cleared — send all-clear
                _alerted_gas = False
                send(clear_gas_alert(ppm))


# ── MAIN ─────────────────────────────────────────────────────
def main():
    global _last_update_id
    print("=" * 55)
    print("  AirGuard NG — Telegram Alert Bot")
    print("=" * 55)
    print(f"  Bot:     @airguardng_alert_bot")
    print(f"  Chat:    {CHAT_ID} ({USER_NAME})")
    print(f"  Check every {POLL_EVERY}s")
    print("=" * 55)

    send(f"🟢 <b>AirGuard NG Bot is online</b>\n\n"
         f"Hello {USER_NAME}! Monitoring air quality across Nigeria "
         f"and your indoor sensor.\n\nSend /help to see what I can do.")
    print("\n  Startup message sent. Monitoring...\n")

    last_check = 0
    last_cmd   = 0

    while True:
        now = time.time()

        # Poll commands every 3s
        if now - last_cmd >= CMD_EVERY:
            last_cmd = now
            for u in get_updates(offset=_last_update_id + 1):
                _last_update_id = u["update_id"]
                msg  = u.get("message", {})
                text = msg.get("text", "").strip()
                if text:
                    ts = datetime.fromtimestamp(msg.get("date",0)).strftime("%H:%M:%S")
                    print(f"  [{ts}] Received: {text}")
                    handle(text)

        # Check thresholds every 30s
        if now - last_check >= POLL_EVERY:
            last_check = now
            print(f"  [{datetime.now().strftime('%H:%M:%S')}] Checking thresholds...")
            check_thresholds()

        time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Stopped.")
        send("🔴 <b>AirGuard NG Bot has been stopped.</b>")
