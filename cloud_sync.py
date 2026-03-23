import os
import time
import subprocess
from datetime import datetime

# Files to sync
DATA_FILES = ["esp32_data.json", "raw_data.csv", "transformed_data.csv", "sensor_locations.csv"]

def sync_data():
    try:
        # 1. Add data files
        for file in DATA_FILES:
            if os.path.exists(file):
                subprocess.run(["git", "add", file], check=True)
        
        # 2. Commit
        timestamp = datetime.now().strftime("%H:%M:%S")
        subprocess.run(["git", "commit", "-m", f"🔄 Data Sync: {timestamp}"], check=True)
        
        # 3. Push
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print(f"[{timestamp}] ✓ Sync Successful.")
    except Exception:
        # This usually means no new data to push
        pass

if __name__ == "__main__":
    print("🚀 AirGuard NG Cloud Sync Active...")
    while True:
        sync_data()
        time.sleep(30) # Syncs every 30 Seconds