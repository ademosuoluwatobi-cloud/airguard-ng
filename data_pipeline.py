"""
AirGuard NG — Data Pipeline (Sensor Discovery)
Discovers all active Nigerian sensors from OpenAQ v3 and saves active_sensors.csv.

Run this ONCE (or when you want to refresh the sensor list):
    python data_pipeline.py

Then run:
    python extraction.py
    python transformation.py
    python -m streamlit run Overview.py
"""

import os
import requests
import pandas as pd
import time
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# ── Load API key — tries both .env and key.env ───────────────────────────────
load_dotenv(dotenv_path=".env")
load_dotenv(dotenv_path="key.env")   # your file is called key.env

API_KEY = os.getenv("OPENAQ_API_KEY")

if not API_KEY:
    print("ERROR: OPENAQ_API_KEY not found in .env or key.env")
    print("Open your key.env file and make sure it contains exactly:")
    print("  OPENAQ_API_KEY=your_actual_key_here")
    print("(no spaces, no quotes around the key)")
    raise SystemExit(1)

HEADERS  = {"X-API-Key": API_KEY}
BASE_URL = "https://api.openaq.org/v3"

# Parameters we care about — PM2.5, PM10, NO2, Temperature, Humidity
WANTED_PARAMS = {"pm25", "pm10", "no2", "temperature", "relativehumidity"}


# ── City assignment ──────────────────────────────────────────────────────────
def assign_city(location_name: str) -> str:
    """Map a sensor location name to its Nigerian state group."""
    name = location_name.lower()
    ABUJA  = ["abuja", "wep"]
    CROSS  = ["calabar", "ogada", "obubra", "cross river"]
    OGUN   = ["arepo", "ogun", "ogolonto", "justrite"]
    LAGOS  = [
        "lagos", "ikorodu", "magodo", "ikoyi", "dolphin", "ketu",
        "oshodi", "agege", "marina", "mile 2", "lawanson", "ojuelegba",
        "lamata", "ifako", "mmia", "makoko", "ewu", "redline",
        "bus terminal", "train station", "qbc", "interchange",
    ]
    if any(k in name for k in ABUJA): return "FCT Abuja"
    if any(k in name for k in CROSS): return "Cross River State"
    if any(k in name for k in OGUN):  return "Ogun State"
    if any(k in name for k in LAGOS): return "Lagos State"
    return "Lagos State"   # safe default


# ── API helpers ──────────────────────────────────────────────────────────────
def get_all_nigeria_locations():
    url    = f"{BASE_URL}/locations"
    params = {"countries_id": 100, "limit": 100}
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
        return resp.json().get("results", [])
    except Exception as e:
        print(f"  ERROR fetching locations: {e}")
        return []


def get_sensors(location_id):
    url = f"{BASE_URL}/locations/{location_id}/sensors"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        time.sleep(0.5)
        return resp.json().get("results", [])
    except Exception as e:
        print(f"  ERROR fetching sensors for location {location_id}: {e}")
        return []


def check_sensor_active(sensor_id):
    """Returns True if the sensor has at least one reading in the last 30 days."""
    url   = f"{BASE_URL}/sensors/{sensor_id}/measurements"
    now   = datetime.now(timezone.utc)
    since = now - timedelta(days=30)
    params = {
        "datetime_from": since.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "datetime_to":   now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "limit": 1,
    }
    try:
        resp    = requests.get(url, headers=HEADERS, params=params, timeout=10)
        time.sleep(0.5)
        results = resp.json().get("results", [])
        return len(results) > 0
    except Exception:
        return False


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    print("AirGuard NG — Discovering active Nigerian sensors")
    print("=" * 60)
    print(f"API key loaded: {API_KEY[:8]}...{API_KEY[-4:]}")
    print()

    locations = get_all_nigeria_locations()
    if not locations:
        print("No locations returned. Check your API key and internet connection.")
        return

    print(f"Found {len(locations)} total locations in Nigeria.\n")

    active_sensors = []
    for loc in locations:
        sensors = get_sensors(loc["id"])
        for s in sensors:
            param = s["parameter"]["name"]
            if param not in WANTED_PARAMS:
                continue
            is_active = check_sensor_active(s["id"])
            if is_active:
                city = assign_city(loc["name"])
                print(
                    f"  ✓ {loc['name']:<42} | "
                    f"{param:<18} | "
                    f"Sensor {s['id']:<12} | "
                    f"{city}"
                )
                active_sensors.append({
                    "location_id":   loc["id"],
                    "location_name": loc["name"],
                    "sensor_id":     s["id"],
                    "parameter":     param,
                    "lat":           loc["coordinates"]["latitude"],
                    "lon":           loc["coordinates"]["longitude"],
                    "city":          city,
                })

    df = pd.DataFrame(active_sensors)

    print(f"\n{'=' * 60}")
    print(f"Total active sensors found: {len(active_sensors)}")
    if not df.empty:
        print("\nBreakdown by state and parameter:")
        print(df.groupby(["city", "parameter"])["sensor_id"].count().to_string())
    print(f"{'=' * 60}")

    df.to_csv("active_sensors.csv", index=False)
    print("\n✓ Saved → active_sensors.csv")
    print("\nNext steps:")
    print("  python extraction.py")
    print("  python transformation.py")
    print("  python -m streamlit run Overview.py")


if __name__ == "__main__":
    main()
