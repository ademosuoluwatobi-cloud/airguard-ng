"""
AirGuard NG — Data Extraction
Pulls live readings from all active Nigerian sensors via OpenAQ v3 API.
Run: python extraction.py
"""

import os
import requests
import pandas as pd
import time
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()
API_KEY  = os.getenv("e115598c847ef0afd78c88dfb347d1f6776d42c0def6a9c13e3c83fc16373d2a")   # reads from your .env file
HEADERS  = {"X-API-Key": "e115598c847ef0afd78c88dfb347d1f6776d42c0def6a9c13e3c83fc16373d2a"}
BASE_URL = "https://api.openaq.org/v3"


def assign_city(location_name):
    """Map a sensor location name to its Nigerian state group."""
    name = location_name.lower()

    LAGOS_KEYWORDS = [
        "lagos", "ikorodu", "magodo", "ikoyi", "dolphin", "ketu",
        "oshodi", "agege", "marina", "mile 2", "lawanson", "ojuelegba",
        "lamata", "ifako", "mmia", "makoko", "ewu", "redline",
        "bus terminal", "train station", "qbc", "interchange",
    ]
    OGUN_KEYWORDS  = ["arepo", "ogolonto", "ogun", "justrite"]
    CROSS_KEYWORDS = ["calabar", "ogada", "obubra", "cross river"]
    ABUJA_KEYWORDS = ["abuja", "wep"]

    if any(k in name for k in LAGOS_KEYWORDS):  return "Lagos State"
    if any(k in name for k in ABUJA_KEYWORDS):  return "FCT Abuja"
    if any(k in name for k in CROSS_KEYWORDS):  return "Cross River State"
    if any(k in name for k in OGUN_KEYWORDS):   return "Ogun State"
    return "Lagos State"   # safe default


def get_measurements(sensor_id, hours_back=24):
    url    = f"{BASE_URL}/sensors/{sensor_id}/measurements"
    now    = datetime.now(timezone.utc)
    since  = now - timedelta(hours=hours_back)
    params = {
        "datetime_from": since.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "datetime_to":   now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "limit": 100,
    }
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=10)
        time.sleep(0.4)
        return resp.json().get("results", [])
    except Exception as e:
        print(f"  ✗ Sensor {sensor_id}: {type(e).__name__}")
        return []


def main():
    sensors_file = "active_sensors.csv"
    if not os.path.exists(sensors_file):
        print(f"ERROR: {sensors_file} not found. Run data_pipeline.py first.")
        return

    active_sensors = pd.read_csv(sensors_file)

    # Reassign city names using the fixed function
    active_sensors["city"] = active_sensors["location_name"].apply(assign_city)

    all_rows  = []
    total     = len(active_sensors)

    print(f"Fetching readings for {total} sensors...\n")

    for i, row in active_sensors.iterrows():
        print(f"  [{i+1:02d}/{total}] {row['location_name']} ({row['parameter']})...")
        readings = get_measurements(row["sensor_id"])

        for r in readings:
            all_rows.append({
                "city":          row["city"],
                "location_name": row["location_name"],
                "sensor_id":     row["sensor_id"],
                "parameter":     row["parameter"],
                "value":         r["value"],
                "timestamp":     r["period"]["datetimeFrom"]["utc"],
                "lat":           row["lat"],
                "lon":           row["lon"],
            })

    df = pd.DataFrame(all_rows)
    df = df[df["value"] >= 0]   # remove bad sensor readings
    df.to_csv("raw_data.csv", index=False)

    print(f"\n{'─'*50}")
    print(f"Total readings saved: {len(df)}")
    print(df.groupby(["city", "parameter"])["value"].count().to_string())
    print(f"{'─'*50}")
    print("Saved → raw_data.csv")
    
    print("\nNext steps:")
    print("  python transformation.py")
    print("  python -m streamlit run Overview.py")

if __name__ == "__main__":
    main()
