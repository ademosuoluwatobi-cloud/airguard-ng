"""
AirGuard NG — Serial Reader
============================
Reads sensor data from Arduino Uno over USB Serial.
Saves to esp32_data.json atomically on every reading.

Architecture:
  • Serial read loop runs in the main thread (blocking readline)
  • Every new reading is saved atomically (temp-file → rename)
  • git_push.py detects the file change and pushes to GitHub
  • Streamlit Cloud picks up the new commit within seconds

Run alongside your other processes:
  Terminal 1:  python serial_reader.py      ← this file
  Terminal 2:  python git_push.py
  Terminal 3:  python telegram_bot.py
  Terminal 4:  python -m streamlit run overview.py

IMPORTANT: Close Arduino IDE Serial Monitor before running this.
Arduino output format (one line per reading):
  GAS_RAW:145,GAS_PPM:12.3,GAS_LEVEL:GOOD,TEMP:27.1,HUM:63.0,RISK:Safe
"""

import serial
import serial.tools.list_ports
import json
import os
import time
import tempfile
from datetime import datetime, timezone, timedelta

# ── CONFIG ────────────────────────────────────────────────────
COM_PORT    = "COM11"       # fallback if auto-detect fails
BAUD_RATE   = 115200
DATA_FILE   = "esp32_data.json"
MAX_HISTORY = 500           # readings kept in memory / file
WAT         = timezone(timedelta(hours=1))  # West Africa Time


# ── PORT AUTO-DETECT ─────────────────────────────────────────
def find_arduino_port() -> str | None:
    """Scan COM ports for Arduino / CH340 / CP210x adapters."""
    keywords = ["arduino", "ch340", "cp210", "usb serial", "uart", "uno"]
    ports = serial.tools.list_ports.comports()
    for p in ports:
        desc = p.description.lower()
        if any(k in desc for k in keywords):
            print(f"  Auto-detected: {p.device} — {p.description}")
            return p.device
    return None


# ── PARSE ─────────────────────────────────────────────────────
def parse_line(line: str) -> dict | None:
    """
    Parse:  GAS_RAW:145,GAS_PPM:12.3,GAS_LEVEL:GOOD,TEMP:27.1,HUM:63.0,RISK:Safe
    Returns a clean dict, or None if the line is malformed / irrelevant.
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
            key = key.strip()
            val = val.strip()
            if   key == "GAS_RAW":   reading["gas_raw"]     = int(float(val))
            elif key == "GAS_PPM":   reading["gas_ppm"]     = round(float(val), 1)
            elif key == "GAS_LEVEL": reading["gas_level"]   = val
            elif key == "TEMP":      reading["temperature"] = round(float(val), 1)
            elif key == "HUM":       reading["humidity"]    = round(float(val), 1)
            elif key == "RISK":      reading["risk_level"]  = val

        # Require at minimum gas_raw and temperature
        if "gas_raw" not in reading or "temperature" not in reading:
            return None

        reading["device_id"] = "airguard-uno-01"
        reading["timestamp"] = datetime.now(WAT).isoformat()
        return reading

    except Exception:
        return None


# ── ATOMIC FILE SAVE ─────────────────────────────────────────
def save_data(data: dict):
    """
    Write JSON to a temp file then atomically rename over DATA_FILE.
    This guarantees the dashboard (and git_push.py) never reads a
    half-written file, even if a read happens mid-write.
    """
    dir_name = os.path.dirname(os.path.abspath(DATA_FILE)) or "."
    tmp_path = None
    try:
        fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
        with os.fdopen(fd, "w") as fh:
            json.dump(data, fh, indent=2)
        os.replace(tmp_path, DATA_FILE)   # atomic on Windows + Linux
    except Exception as e:
        print(f"  ⚠ Save error: {e}")
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


def load_data() -> dict:
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE) as fh:
                return json.load(fh)
        except Exception:
            pass
    return {"readings": [], "latest": None}


# ── PRINT HELPER ─────────────────────────────────────────────
def log(reading: dict, count: int):
    ts  = datetime.now(WAT).strftime("%H:%M:%S")
    ppm = reading.get("gas_ppm", "—")
    lvl = reading.get("gas_level", "—")
    tmp = reading.get("temperature", "—")
    hum = reading.get("humidity", "—")
    rsk = reading.get("risk_level", "—")
    raw = reading.get("gas_raw", "—")
    print(
        f"  [{ts} WAT] #{count:04d}  "
        f"Gas {ppm} ppm ({lvl}) raw={raw}  "
        f"Temp {tmp}°C  Hum {hum}%  Risk: {rsk}"
    )


# ── MAIN ─────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  AirGuard NG — Serial Reader")
    print("=" * 60)

    port = find_arduino_port() or COM_PORT
    print(f"  Port      : {port}  (fallback: {COM_PORT})")
    print(f"  Baud rate : {BAUD_RATE}")
    print(f"  Output    : {DATA_FILE}  (atomic writes)")
    print(f"  History   : last {MAX_HISTORY} readings kept")
    print("=" * 60)
    print()

    # Open serial port
    ser = None
    while ser is None:
        try:
            ser = serial.Serial(port, BAUD_RATE, timeout=2)
            print(f"  ✓ Opened {port} — waiting for readings...\n")
        except serial.SerialException as e:
            print(f"  ✗ Cannot open {port}: {e}")
            print("  → Close Arduino IDE Serial Monitor if open.")
            print("  → Check COM_PORT at top of this file.")
            print("  Retrying in 10 s...\n")
            time.sleep(10)
            # Re-probe in case device was reconnected
            port = find_arduino_port() or COM_PORT

    data  = load_data()
    count = 0

    while True:
        try:
            raw_bytes = ser.readline()
            if not raw_bytes:
                continue

            line = raw_bytes.decode("utf-8", errors="ignore")

            reading = parse_line(line)
            if reading is None:
                # Print non-data lines at low verbosity (Arduino debug output etc.)
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    print(f"  [skip] {stripped[:80]}")
                continue

            # ── Update in-memory store ────────────────────────
            data["latest"] = reading
            data["readings"].append(reading)
            if len(data["readings"]) > MAX_HISTORY:
                data["readings"] = data["readings"][-MAX_HISTORY:]

            # ── Atomic save → triggers git_push.py immediately ─
            save_data(data)
            count += 1
            log(reading, count)

        except KeyboardInterrupt:
            print(f"\n  Stopped. {count} readings captured.")
            break

        except serial.SerialException as e:
            print(f"\n  Serial error: {e}")
            print("  Attempting reconnect in 5 s...")
            time.sleep(5)
            try:
                ser.close()
            except Exception:
                pass
            try:
                port = find_arduino_port() or COM_PORT
                ser  = serial.Serial(port, BAUD_RATE, timeout=2)
                print(f"  ✓ Reconnected on {port}\n")
            except serial.SerialException:
                print("  ✗ Reconnect failed. Check USB cable.\n")
                ser = None
                time.sleep(5)

        except Exception as e:
            print(f"  Unexpected error: {e}")
            time.sleep(1)

    if ser:
        ser.close()


if __name__ == "__main__":
    main()
