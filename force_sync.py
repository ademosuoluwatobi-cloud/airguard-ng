import subprocess
import os

def total_force_push():
    print("🧹 Cleaning Git cache and forcing sync...")
    try:
        # 1. Remove cached files (fixes .gitignore issues)
        subprocess.run(["git", "rm", "-r", "--cached", "."], capture_output=True)
        
        # 2. Add everything fresh
        subprocess.run(["git", "add", "."], check=True)
        
        # 3. Commit
        subprocess.run(["git", "commit", "-m", "⚡ Emergency Force Sync: Resetting Cloud State"], check=True)
        
        # 4. Force Push
        subprocess.run(["git", "push", "origin", "main", "--force"], check=True)
        
        print("\n✅ SUCCESS: GitHub is now an exact mirror of your laptop.")
        print("Check your Streamlit Cloud link in 30 seconds!")
    except Exception as e:
        print(f"\n❌ FAILED: {e}")

if __name__ == "__main__":
    total_force_push()