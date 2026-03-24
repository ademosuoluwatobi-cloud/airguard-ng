"""
AirGuard NG — Auto Git Push
Runs extraction + transformation then pushes updated CSV to GitHub
so Streamlit Cloud stays live. Run this in a terminal alongside your dashboard.
"""
import subprocess, time, os
from datetime import datetime

INTERVAL = 300  # push every 5 minutes

def run(cmd):
    result = subprocess.run(cmd, shell=True, cwd=r"C:\Users\user\Documents\airguard-ng")
    return result.returncode

def push_data():
    now = datetime.now().strftime("%d %b %Y, %H:%M")
    print(f"\n[{now}] Running pipeline...")
    run("python extraction.py")
    run("python transformation.py")
    print(f"[{now}] Pushing to GitHub...")
    run("git add raw_data.csv transformed_data.csv sensor_locations.csv esp32_data.json")
    run(f'git commit -m "Auto data update {now}" --allow-empty')
    run("git push")
    print(f"[{now}] ✓ Done — Streamlit Cloud will update in ~30 seconds")

while True:
    push_data()
    time.sleep(INTERVAL) 
