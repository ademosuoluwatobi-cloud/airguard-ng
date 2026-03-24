import os
import time
import subprocess
from datetime import datetime, timezone, timedelta

# Nigerian time — WAT is UTC+1
WAT = timezone(timedelta(hours=1))

# Files to sync
DATA_FILES = ["esp32_data.json", "raw_data.csv", "transformed_data.csv", "sensor_locations.csv"]

def sync_data():
    try:
        for file in DATA_FILES:
            if os.path.exists(file):
                subprocess.run(["git", "add", file], check=True)
        
        timestamp = datetime.now(WAT).strftime("%d %b %Y, %H:%M:%S WAT")
        subprocess.run(["git", "commit", "-m", f"Data Sync: {timestamp}"], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print(f"[{timestamp}] Sync Successful.")
    except Exception:
        pass

if __name__ == "__main__":
    print("AirGuard NG Cloud Sync Active — Nigerian Time (WAT UTC+1)")
    while True:
        sync_data()
        time.sleep(0.5)
