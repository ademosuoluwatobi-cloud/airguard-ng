"""
AirGuard NG — Serial Reader
============================
Reads key:value lines from Arduino Uno over USB Serial.
Saves to esp32_data.json atomically so dashboard always reads complete data.

Run alongside your dashboard:
  Terminal 1:  python serial_reader.py
  Terminal 2:  python telegram_bot.py
  Terminal 3:  python -m streamlit run overview.py

IMPORTANT: Close Arduino IDE Serial Monitor before running this.
Arduino output format:
  GAS_RAW:145,GAS_PPM:12.3,GAS_LEVEL:GOOD,TEMP:27.1,HUM:63.0,RISK:Safe
"""

import serial
import serial.tools.list_ports
import json
import os
import time
import tempfile
from datetime import datetime

# ── CONFIG ───────────────────────────────────────────────────
COM_PORT    = "COM11"
BAUD_RATE   = 115200
DATA_FILE   = "esp32_data.json"
MAX_HISTORY = 500


# ── AUTO-DETECT PORT ─────────────────────────────────────────
def find_arduino_port():
    ports = serial.tools.list_ports.comports()
    for p in ports:
        desc = p.description.lower()
        if any(x in desc for x in ["arduino","ch340","cp210","usb serial","uart"]):
            print(f"  Auto-detected: {p.device} — {p.description}")
            return p.device
    return None


# ── PARSE ARDUINO LINE ───────────────────────────────────────
def parse_line(line: str):
    """
    Parses: GAS_RAW:145,GAS_PPM:12.3,GAS_LEVEL:GOOD,TEMP:27.1,HUM:63.0,RISK:Safe
    Returns clean dict or None.
    """
    line = line.strip()
    if not line or "GAS_RAW" not in line:
        return None
    reading = {}
    try:
        for part in line.split(","):
            if ":" not in part:
                continue
            key, val = part.split(":", 1)
            key, val = key.strip(), val.strip()
            if   key == "GAS_RAW":   reading["gas_raw"]     = int(float(val))
            elif key == "GAS_PPM":   reading["gas_ppm"]     = round(float(val), 1)
            elif key == "GAS_LEVEL": reading["gas_level"]   = val
            elif key == "TEMP":      reading["temperature"] = round(float(val), 1)
            elif key == "HUM":       reading["humidity"]    = round(float(val), 1)
            elif key == "RISK":      reading["risk_level"]  = val
        if "gas_raw" not in reading or "temperature" not in reading:
            return None
        reading["device_id"] = "airguard-uno-01"
        reading["timestamp"] = datetime.now().isoformat()
        return reading
    except Exception:
        return None


# ── ATOMIC SAVE ──────────────────────────────────────────────
def save_data(data: dict):
    """
    Write to a temp file then atomically rename so the dashboard
    never reads a half-written file.
    """
    dir_name = os.path.dirname(os.path.abspath(DATA_FILE)) or "."
    try:
        fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_path, DATA_FILE)   # atomic on all platforms
    except Exception as e:
        print(f"  Save error: {e}")
        if os.path.exists(tmp_path):
            try: os.remove(tmp_path)
            except Exception: pass


def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"readings": [], "latest": None}


# ── MAIN ─────────────────────────────────────────────────────
def main():
    print("=" * 55)
    print("  AirGuard NG — Serial Reader")
    print("=" * 55)

    port = find_arduino_port() or COM_PORT
    print(f"  Port:      {port}")
    print(f"  Baud rate: {BAUD_RATE}")
    print(f"  Output:    {DATA_FILE}  (atomic real-time saves)")
    print("=" * 55)
    print()

    try:
        ser = serial.Serial(port, BAUD_RATE, timeout=2)
        print(f"  ✓ Opened {port} — waiting for readings...\n")
    except serial.SerialException as e:
        print(f"\n  ✗ Cannot open {port}: {e}")
        print()
        print("  Fixes:")
        print("  1. Close Arduino IDE Serial Monitor")
        print("  2. Check Device Manager for correct COM port")
        print("  3. Update COM_PORT at the top of this file")
        return

    data  = load_data()
    count = 0

    while True:
        try:
            raw_bytes = ser.readline()
            if not raw_bytes:
                continue

            line = raw_bytes.decode("utf-8", errors="ignore").strip()
            if line:
                print(f"  RAW › {line}")

            reading = parse_line(line)
            if reading is None:
                continue

            # Update store
            data["latest"] = reading
            data["readings"].append(reading)
            if len(data["readings"]) > MAX_HISTORY:
                data["readings"] = data["readings"][-MAX_HISTORY:]

            # Atomic save — dashboard gets fresh data immediately
            save_data(data)
            count += 1

            ts = datetime.now().strftime("%H:%M:%S")
            print(
                f"  [{ts}] ✓  "
                f"Gas {reading.get('gas_ppm','—')} ppm ({reading.get('gas_level','—')})  "
                f"Temp {reading.get('temperature','—')}°C  "
                f"Hum {reading.get('humidity','—')}%  "
                f"Risk: {reading.get('risk_level','—')}  #{count}"
            )

        except KeyboardInterrupt:
            print("\n\n  Stopped. Goodbye.")
            break
        except serial.SerialException as e:
            print(f"\n  Serial error: {e} — reconnecting in 5s...")
            time.sleep(5)
            try:
                ser.close()
                ser = serial.Serial(port, BAUD_RATE, timeout=2)
                print("  Reconnected.")
            except Exception:
                print("  Reconnect failed. Check USB cable.")
                time.sleep(5)
        except Exception as e:
            print(f"  Error: {e}")
            time.sleep(1)

    ser.close()


if __name__ == "__main__":
    main()
