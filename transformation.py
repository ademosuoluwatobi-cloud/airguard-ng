"""
AirGuard NG — Data Transformation
Reads raw_data.csv → normalises city names → calculates HRS → writes transformed_data.csv
Run: python transformation.py
"""

import pandas as pd
import json
import os


# ── CITY NAME NORMALISATION ─────────────────────────────────────────────────
# Handles whatever city names came out of extraction.py (old or new runs)
def normalise_city(city: str) -> str:
    c = str(city).lower()
    if any(x in c for x in ["lagos"]):                         return "Lagos State"
    if any(x in c for x in ["abuja", "fct"]):                  return "FCT Abuja"
    if any(x in c for x in ["calabar","cross river","ogada","obubra"]): return "Cross River State"
    if any(x in c for x in ["ogun"]):                          return "Ogun State"
    return "Lagos State"   # safe default for "Other" etc.


# ── HRS CALCULATION ──────────────────────────────────────────────────────────
def calculate_hrs(pm25: float):
    if pm25 < 0:      return 0.0, "No Data"
    elif pm25 <= 12:  return round((pm25 / 12) * 20, 1),                           "Good"
    elif pm25 <= 35.4:return round(20 + ((pm25 - 12)    / 23.4) * 20, 1),          "Moderate"
    elif pm25 <= 55.4:return round(40 + ((pm25 - 35.4)  / 20)   * 20, 1),          "Unhealthy for Sensitive Groups"
    elif pm25 <= 150.4:return round(60 + ((pm25 - 55.4) / 95)   * 20, 1),          "Unhealthy"
    elif pm25 <= 250.4:return round(80 + ((pm25 - 150.4)/ 100)  * 20, 1),          "Very Unhealthy"
    else:              return 100.0,                                                 "Hazardous"


# ── REPRESENTATIVE COORDINATES PER STATE ─────────────────────────────────────
# Used as the map pin for each state card.  We take the mean of all sensors
# belonging to that state so the pin sits at the geographic centre.
STATE_FALLBACK_COORDS = {
    "Lagos State":       (6.52,  3.39),
    "Ogun State":        (6.70,  3.43),
    "Cross River State": (5.03,  8.35),
    "FCT Abuja":         (9.08,  7.40),
}


def main():
    raw_file = "raw_data.csv"
    if not os.path.exists(raw_file):
        print(f"ERROR: {raw_file} not found.  Run extraction.py first.")
        return

    df = pd.read_csv(raw_file)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df[df["value"] >= 0]

    # Normalise city names (merges Calabar + Cross River → Cross River State)
    df["city"] = df["city"].apply(normalise_city)

    # ── PM2.5 latest value per state ─────────────────────────────────────────
    pm25 = df[df["parameter"] == "pm25"].copy()

    if pm25.empty:
        print("WARNING: No PM2.5 data found in raw_data.csv")
        return

    # For each state: latest reading across any of its sensors
    latest = (
        pm25.sort_values("timestamp", ascending=False)
            .groupby("city")
            .first()
            .reset_index()[["city", "value", "lat", "lon", "timestamp"]]
    )

    # Override lat/lon with mean coordinates of all sensors in that state
    mean_coords = (
        pm25.groupby("city")
            .agg(lat_mean=("lat", "mean"), lon_mean=("lon", "mean"))
            .reset_index()
    )
    result = latest.merge(mean_coords, on="city")
    result["lat"] = result["lat_mean"]
    result["lon"] = result["lon_mean"]
    result = result.drop(columns=["lat_mean", "lon_mean"])

    # Fill any missing coordinates from fallback table
    for _, row in result.iterrows():
        if pd.isna(row["lat"]) or pd.isna(row["lon"]):
            fb = STATE_FALLBACK_COORDS.get(row["city"], (6.52, 3.39))
            result.loc[result["city"] == row["city"], "lat"] = fb[0]
            result.loc[result["city"] == row["city"], "lon"] = fb[1]

    # Calculate HRS
    result[["hrs", "risk_level"]] = result["value"].apply(
        lambda v: pd.Series(calculate_hrs(float(v)))
    )

    result = result[["city", "value", "hrs", "risk_level", "lat", "lon"]]
    result = result.sort_values("hrs", ascending=False).reset_index(drop=True)

    result.to_csv("transformed_data.csv", index=False)

    print("Transformation complete:\n")
    print(result[["city", "value", "hrs", "risk_level"]].to_string(index=False))
    print(f"\nSaved → transformed_data.csv")

    # ── Also write per-location latest values for the map ──────────────────
    # This gives Overview.py individual sensor dots (not just state-level dots)
    all_params = df.copy()
    pm25_loc = (
        pm25.sort_values("timestamp", ascending=False)
            .groupby("location_name")
            .first()
            .reset_index()[["location_name", "city", "value", "lat", "lon", "timestamp"]]
    )
    pm25_loc[["hrs", "risk_level"]] = pm25_loc["value"].apply(
        lambda v: pd.Series(calculate_hrs(float(v)))
    )

    # Also pull latest temperature + humidity per location (for tooltips)
    def latest_param(param_name):
        p = df[df["parameter"] == param_name].copy()
        if p.empty:
            return pd.DataFrame(columns=["location_name", param_name])
        return (
            p.sort_values("timestamp", ascending=False)
             .groupby("location_name")
             .first()
             .reset_index()[["location_name", "value"]]
             .rename(columns={"value": param_name})
        )

    temp = latest_param("temperature")
    hum  = latest_param("relativehumidity")

    sensor_map = pm25_loc.copy()
    if not temp.empty:
        sensor_map = sensor_map.merge(temp, on="location_name", how="left")
    else:
        sensor_map["temperature"] = None
    if not hum.empty:
        sensor_map = sensor_map.merge(hum, on="location_name", how="left")
    else:
        sensor_map["relativehumidity"] = None

    sensor_map.to_csv("sensor_locations.csv", index=False)
    print(f"Saved → sensor_locations.csv  ({len(sensor_map)} individual sensor locations)")

    print("\nNext step:")
    print("  python -m streamlit run Overview.py")

if __name__ == "__main__":
    main()
