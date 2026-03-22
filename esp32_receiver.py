"""
AirGuard NG — ESP32 Data Receiver
===================================
Run this on the SAME computer as your Streamlit dashboard.
Make sure your ESP32 and your laptop are on the SAME WiFi network.

How it works:
  1. This script starts a tiny Flask server on port 5000
  2. Your ESP32 sends sensor readings via HTTP POST to this server
  3. Readings are saved to esp32_data.json
  4. The Streamlit dashboard reads esp32_data.json to show live hardware data

Run with:
  python esp32_receiver.py

Find your computer's local IP (needed for the ESP32 code):
  Windows: ipconfig → look for IPv4 Address (e.g. 192.168.8.101)
  Then paste that IP into the ESP32 Arduino code below.
"""

from flask import Flask, request, jsonify
from datetime import datetime
import json
import os

app = Flask(__name__)
DATA_FILE = "esp32_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"readings": [], "latest": None}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

@app.route("/sensor", methods=["POST"])
def receive_sensor():
    """
    ESP32 sends JSON like:
    {
      "gas_raw": 420,
      "gas_ppm": 12.4,
      "temperature": 31.2,
      "humidity": 68.5,
      "device_id": "airguard-device-01"
    }
    """
    try:
        payload = request.get_json()
        if not payload:
            return jsonify({"error": "No JSON received"}), 400

        reading = {
            "timestamp": datetime.now().isoformat(),
            "gas_raw":     payload.get("gas_raw", 0),
            "gas_ppm":     payload.get("gas_ppm", 0),
            "temperature": payload.get("temperature", 0),
            "humidity":    payload.get("humidity", 0),
            "device_id":   payload.get("device_id", "airguard-device-01"),
            "risk_level":  classify_gas(payload.get("gas_ppm", 0))
        }

        data = load_data()
        data["latest"] = reading
        data["readings"].append(reading)

        # Keep only last 200 readings in memory
        if len(data["readings"]) > 200:
            data["readings"] = data["readings"][-200:]

        save_data(data)
        print(f"[{reading['timestamp']}] Gas: {reading['gas_ppm']} ppm | Temp: {reading['temperature']}°C | Humidity: {reading['humidity']}% | Risk: {reading['risk_level']}")

        return jsonify({"status": "ok", "risk": reading["risk_level"]}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/latest", methods=["GET"])
def get_latest():
    """Dashboard calls this to get the most recent reading."""
    data = load_data()
    return jsonify(data.get("latest") or {"error": "No data yet"})


@app.route("/history", methods=["GET"])
def get_history():
    """Returns last N readings."""
    n = int(request.args.get("n", 50))
    data = load_data()
    return jsonify(data.get("readings", [])[-n:])


@app.route("/status", methods=["GET"])
def status():
    return jsonify({"status": "AirGuard NG receiver running", "file": DATA_FILE})


def classify_gas(ppm):
    """
    MQ2 sensor gas classification.
    Values are approximate — calibrate based on your specific MQ2 unit.
    """
    if ppm <= 50:   return "Good"
    elif ppm <= 100: return "Moderate"
    elif ppm <= 300: return "Unhealthy for Sensitive Groups"
    elif ppm <= 500: return "Unhealthy"
    elif ppm <= 700: return "Very Unhealthy"
    else:            return "Hazardous"


if __name__ == "__main__":
    print("=" * 55)
    print("  AirGuard NG — ESP32 Data Receiver")
    print("=" * 55)
    print("  Listening on: http://0.0.0.0:5000")
    print("  POST endpoint: http://[YOUR-IP]:5000/sensor")
    print("  GET latest:    http://[YOUR-IP]:5000/latest")
    print("  GET history:   http://[YOUR-IP]:5000/history")
    print("=" * 55)
    print()
    app.run(host="0.0.0.0", port=5000, debug=False)
