"""
AirGuard NG — Telegram Alert Bot
===================================
Real-time alerts for:
  • Gas danger from Arduino (fires within 3 seconds of detection)
  • Air quality threshold breach for any monitored city
  • Gas-cleared all-clear when danger subsides

Commands:
  /status  — live city air quality
  /device  — latest hardware reading
  /help    — all commands

Timing:
  • Gas danger check  : every 3 s  (matches hardware refresh rate)
  • AQ threshold check: every 30 s (OpenAQ data updates ~hourly)
  • Command poll      : every 3 s

Run:
  python telegram_bot.py
"""

import os
import json
import time
import requests
import pandas as pd
from datetime import datetime, timezone, timedelta
from styles import load_device_data, classify_gas, gas_is_dangerous, RISK_ADVICE
from dotenv import load_dotenv

# ── CONFIG ────────────────────────────────────────────────────
load_dotenv(dotenv_path="key.env")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    print("ERROR: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID missing in key.env")
    raise SystemExit(1)

USER_NAME  = "Oluwatobi"
BASE_URL   = f"https://api.telegram.org/bot{BOT_TOKEN}"
WAT        = timezone(timedelta(hours=1))

# Poll intervals (seconds)
GAS_CHECK_EVERY = 3    # hardware gas danger — check very frequently
CMD_POLL_EVERY  = 3    # Telegram command poll
AQ_CHECK_EVERY  = 30   # OpenAQ city air quality check

# ── CONSTANTS ────────────────────────────────────────────────
RISK_ORDER = [
    "Good", "Moderate", "Unhealthy for Sensitive Groups",
    "Unhealthy", "Very Unhealthy", "Hazardous",
]
RISK_EMOJI = {
    "Good": "🟢", "Moderate": "🟡",
    "Unhealthy for Sensitive Groups": "🟠",
    "Unhealthy": "🔴", "Very Unhealthy": "🟣",
    "Hazardous": "☠️", "No Data": "⚫",
}
STATE_FLAG = {
    "Lagos State": "🏙", "Ogun State": "🌿",
    "Cross River State": "🌊", "FCT Abuja": "🏛",
}

# ── ALERT STATE ───────────────────────────────────────────────
# Track what we've already alerted so we don't spam
_alerted_cities: set  = set()   # cities currently in Unhealthy+ state
_gas_alerted:    bool = False    # True while gas danger is active
_last_update_id: int  = 0


# ── TELEGRAM HELPERS ─────────────────────────────────────────
def send(text: str, retries: int = 3) -> bool:
    """Send a Telegram message. Retries up to `retries` times on failure."""
    for attempt in range(1, retries + 1):
        try:
            r = requests.post(
                f"{BASE_URL}/sendMessage",
                data={
                    "chat_id":    CHAT_ID,
                    "text":       text,
                    "parse_mode": "HTML",
                },
                timeout=10,
            )
            if r.status_code == 200:
                return True
            # 429 = rate limited — back off
            if r.status_code == 429:
                retry_after = r.json().get("parameters", {}).get("retry_after", 5)
                print(f"  Rate limited — waiting {retry_after}s")
                time.sleep(retry_after)
                continue
            print(f"  Telegram {r.status_code}: {r.text[:120]}")
        except requests.exceptions.Timeout:
            print(f"  Telegram timeout (attempt {attempt}/{retries})")
        except Exception as e:
            print(f"  Telegram error: {e}")
        if attempt < retries:
            time.sleep(2)
    return False


def get_updates(offset: int = 0) -> list:
    """Poll Telegram for new messages."""
    try:
        r = requests.get(
            f"{BASE_URL}/getUpdates",
            params={"offset": offset, "timeout": 2, "limit": 10},
            timeout=8,
        )
        return r.json().get("result", [])
    except Exception:
        return []


# ── DATA LOADERS ─────────────────────────────────────────────
def load_aq() -> pd.DataFrame:
    """Load the latest transformed city-level AQ data."""
    try:
        df = pd.read_csv("transformed_data.csv")
        return df if not df.empty else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def risk_rank(risk: str) -> int:
    """Return numeric rank of a risk level (higher = worse)."""
    try:
        return RISK_ORDER.index(risk)
    except ValueError:
        return -1


def is_unhealthy_or_worse(risk: str) -> bool:
    return risk_rank(risk) >= risk_rank("Unhealthy")


# ── MESSAGE BUILDERS ─────────────────────────────────────────
def msg_status() -> str:
    df  = load_aq()
    now = datetime.now(WAT).strftime("%d %b %Y, %H:%M WAT")
    if df.empty:
        return (
            f"🛡 <b>AirGuard NG — Status</b>\n"
            f"<i>{now}</i>\n\n"
            f"⚠️ No sensor data yet.\n"
            f"Run <code>extraction.py</code> then <code>transformation.py</code> first."
        )
    lines = [f"🛡 <b>AirGuard NG — Live Status</b>", f"<i>{now}</i>", ""]
    for _, row in df.iterrows():
        city  = row["city"]
        emoji = RISK_EMOJI.get(row["risk_level"], "⚫")
        flag  = STATE_FLAG.get(city, "📍")
        lines.append(
            f"{flag} <b>{city}</b>\n"
            f"   {emoji} HRS <b>{row['hrs']}</b> · "
            f"PM2.5 {round(float(row['value']), 1)} µg/m³\n"
            f"   <i>{row['risk_level']}</i>"
        )
    lines += ["", "Send /device for hardware readings."]
    return "\n".join(lines)


def msg_device() -> str:
    device, _ = load_device_data()
    if not device:
        return (
            "🔩 <b>AirGuard Device</b>\n\n"
            "Not connected.\n"
            "Run <code>serial_reader.py</code> and connect your Arduino via USB."
        )
    raw  = int(device.get("gas_raw", 0) or 0)
    ppm  = device.get("gas_ppm",     "—")
    temp = device.get("temperature", "—")
    hum  = device.get("humidity",    "—")
    risk = device.get("risk_level",  "—")
    did  = device.get("device_id",   "airguard-uno-01")
    gl, gc, _, _, gi, _ = classify_gas(raw)
    ts = "—"
    try:
        ts = datetime.fromisoformat(
            device.get("timestamp", "")
        ).strftime("%d %b %Y, %H:%M:%S")
    except Exception:
        pass
    return (
        f"🔩 <b>AirGuard Device — Live Reading</b>\n\n"
        f"📟 Device:    <code>{did}</code>\n"
        f"🕐 Time:      {ts}\n\n"
        f"{gi} Gas PPM:    <b>{ppm}</b>  ({gl})\n"
        f"🌡 Temp:       <b>{temp} °C</b>\n"
        f"💧 Humidity:   <b>{hum} %</b>\n"
        f"⚡ Risk level: <b>{risk}</b>"
    )


def alert_aq(city: str, hrs, risk: str, pm25: float) -> str:
    emoji  = RISK_EMOJI.get(risk, "🔴")
    flag   = STATE_FLAG.get(city, "📍")
    advice = RISK_ADVICE.get(risk, "")
    now    = datetime.now(WAT).strftime("%H:%M WAT")
    return (
        f"🚨 <b>Air Quality Alert — {city}</b>\n\n"
        f"{flag} {emoji} <b>{risk}</b>\n"
        f"HRS: <b>{hrs}</b> · PM2.5: <b>{pm25} µg/m³</b>\n"
        f"<i>Detected at {now}</i>\n\n"
        f"⚕️ {advice}\n\n"
        f"<i>Open AirGuard NG dashboard for full details.</i>"
    )


def alert_gas(ppm, raw: int, risk: str) -> str:
    now = datetime.now(WAT).strftime("%H:%M:%S WAT")
    return (
        f"🔥 <b>⚠️ GAS DANGER — AirGuard Device</b>\n\n"
        f"⚡ Gas level:  <b>{ppm} PPM</b>  (raw: {raw})\n"
        f"🚨 Risk level: <b>{risk}</b>\n"
        f"🕐 Detected:   {now}\n\n"
        f"<b>Take immediate action:</b>\n"
        f"• Open ALL windows and doors NOW\n"
        f"• Do NOT use any electrical switches\n"
        f"• Turn off gas cylinder at the source\n"
        f"• Evacuate the room immediately\n\n"
        f"🆘 Lagos Fire Service: <b>01-7944996</b>\n"
        f"🆘 Nigeria Emergency:  <b>112</b>\n"
        f"🆘 NEMA:               <b>0800-CALLNEMA</b>"
    )


def alert_gas_cleared(ppm) -> str:
    now = datetime.now(WAT).strftime("%H:%M:%S WAT")
    return (
        f"✅ <b>Gas Level Cleared — AirGuard Device</b>\n\n"
        f"Gas concentration has dropped to <b>{ppm} PPM</b> — now safe.\n"
        f"<i>Cleared at {now}</i>\n\n"
        f"Ensure the area is well ventilated before re-entering.\n"
        f"Check gas cylinder valve is fully closed."
    )


# ── COMMAND HANDLER ──────────────────────────────────────────
def handle(text: str):
    cmd = text.strip().lower().split()[0]
    if cmd in ["/start", "/help"]:
        send(
            f"👋 Hello {USER_NAME}!\n\n"
            f"🛡 <b>AirGuard NG Alert Bot</b>\n\n"
            f"I monitor Nigeria's air quality and your indoor gas sensor "
            f"and alert you automatically when conditions are dangerous.\n\n"
            f"<b>Commands:</b>\n"
            f"/status  — live AQ for all monitored cities\n"
            f"/device  — latest hardware sensor reading\n"
            f"/help    — show this message\n\n"
            f"<b>Automatic alerts:</b>\n"
            f"• Gas danger → fires within {GAS_CHECK_EVERY}s of detection\n"
            f"• City AQ breach → checked every {AQ_CHECK_EVERY}s\n"
            f"• Gas cleared → fires when danger subsides"
        )
    elif cmd == "/status":
        send(msg_status())
    elif cmd == "/device":
        send(msg_device())
    else:
        send(f"Unknown command: <code>{text}</code>\nSend /help to see commands.")


# ── THRESHOLD CHECKERS ────────────────────────────────────────
def check_gas():
    """
    Check hardware gas sensor every GAS_CHECK_EVERY seconds.
    Fires alert immediately when dangerous, fires all-clear when safe again.
    """
    global _gas_alerted

    device, _ = load_device_data()
    if not device:
        return

    raw  = int(device.get("gas_raw", 0) or 0)
    ppm  = device.get("gas_ppm",     0)
    risk = device.get("risk_level",  "Safe")

    if gas_is_dangerous(raw):
        if not _gas_alerted:
            _gas_alerted = True
            ts = datetime.now(WAT).strftime("%H:%M:%S")
            print(f"  [{ts} WAT] 🔥 GAS ALERT: {ppm} PPM — {risk}")
            send(alert_gas(ppm, raw, risk))
    else:
        if _gas_alerted:
            _gas_alerted = False
            ts = datetime.now(WAT).strftime("%H:%M:%S")
            print(f"  [{ts} WAT] ✅ Gas cleared: {ppm} PPM")
            send(alert_gas_cleared(ppm))


def check_air_quality():
    """
    Check city-level AQ from transformed_data.csv every AQ_CHECK_EVERY seconds.
    Alerts once per city per breach episode; clears when city recovers.
    """
    global _alerted_cities

    df = load_aq()
    if df.empty:
        return

    for _, row in df.iterrows():
        city = row["city"]
        risk = row["risk_level"]

        if is_unhealthy_or_worse(risk):
            if city not in _alerted_cities:
                _alerted_cities.add(city)
                ts = datetime.now(WAT).strftime("%H:%M:%S")
                print(f"  [{ts} WAT] 🏙 AQ ALERT: {city} → {risk}")
                send(alert_aq(city, row["hrs"], risk, round(float(row["value"]), 1)))
                time.sleep(1)   # small gap between back-to-back city alerts
        else:
            _alerted_cities.discard(city)


# ── MAIN ─────────────────────────────────────────────────────
def main():
    global _last_update_id

    print("=" * 60)
    print("  AirGuard NG — Telegram Alert Bot")
    print("=" * 60)
    print(f"  Chat ID  : {CHAT_ID}  ({USER_NAME})")
    print(f"  Gas check: every {GAS_CHECK_EVERY}s")
    print(f"  AQ check : every {AQ_CHECK_EVERY}s")
    print(f"  Cmd poll : every {CMD_POLL_EVERY}s")
    print("=" * 60)
    print()

    # Startup message
    now = datetime.now(WAT).strftime("%d %b %Y, %H:%M WAT")
    send(
        f"🟢 <b>AirGuard NG Bot is online</b>\n\n"
        f"Hello {USER_NAME}! Monitoring Nigeria's air quality and your indoor sensor.\n"
        f"<i>Started at {now}</i>\n\n"
        f"Send /help to see available commands."
    )
    print("  ✓ Startup message sent. Monitoring...\n")

    last_aq_check  = 0.0
    last_gas_check = 0.0
    last_cmd_poll  = 0.0

    while True:
        now_ts = time.time()

        # ── Command polling ───────────────────────────────────
        if now_ts - last_cmd_poll >= CMD_POLL_EVERY:
            last_cmd_poll = now_ts
            try:
                updates = get_updates(offset=_last_update_id + 1)
                for u in updates:
                    _last_update_id = u["update_id"]
                    msg  = u.get("message", {})
                    text = msg.get("text", "").strip()
                    if text:
                        ts_fmt = datetime.fromtimestamp(
                            msg.get("date", 0)
                        ).strftime("%H:%M:%S")
                        print(f"  [{ts_fmt}] ← {text}")
                        handle(text)
            except Exception as e:
                print(f"  Command poll error: {e}")

        # ── Gas danger check (high frequency) ────────────────
        if now_ts - last_gas_check >= GAS_CHECK_EVERY:
            last_gas_check = now_ts
            try:
                check_gas()
            except Exception as e:
                print(f"  Gas check error: {e}")

        # ── Air quality check (lower frequency) ──────────────
        if now_ts - last_aq_check >= AQ_CHECK_EVERY:
            last_aq_check = now_ts
            ts = datetime.now(WAT).strftime("%H:%M:%S")
            print(f"  [{ts} WAT] Checking city AQ thresholds...")
            try:
                check_air_quality()
            except Exception as e:
                print(f"  AQ check error: {e}")

        time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        ts = datetime.now(WAT).strftime("%H:%M:%S WAT")
        print(f"\n  Stopped at {ts}.")
        send("🔴 <b>AirGuard NG Bot has been stopped.</b>")
