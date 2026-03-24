"""
AirGuard NG — Smart Cloud Sync
================================
Pushes data files to GitHub every 2–5 seconds ONLY when content has
actually changed. This keeps Streamlit Cloud and the Telegram bot
up-to-date with the latest hardware readings and sensor data.

How it works:
  1. Computes an MD5 hash of each watched file every 2 seconds
  2. If any file changed since the last push → commit + push immediately
  3. If nothing changed → skip (no empty commits, no Git noise)
  4. If push fails (network blip) → retries on the next cycle

Run:
  Terminal 1: python serial_reader.py
  Terminal 2: python telegram_bot.py
  Terminal 3: python git_push.py
  Terminal 4: python -m streamlit run overview.py
"""

import os
import time
import hashlib
import subprocess
from datetime import datetime, timezone, timedelta

# ── CONFIG ────────────────────────────────────────────────────
WAT = timezone(timedelta(hours=1))          # West Africa Time (UTC+1)

CHECK_INTERVAL  = 2     # seconds between change-detection checks
PUSH_COOLDOWN   = 5     # minimum seconds between consecutive pushes
                        # (prevents GitHub rate-limit on burst writes)

# Files to watch and sync
DATA_FILES = [
    "esp32_data.json",          # live hardware sensor readings
    "raw_data.csv",             # OpenAQ raw sensor data
    "transformed_data.csv",     # processed HRS + risk levels
    "sensor_locations.csv",     # per-location sensor map data
]

# ── STATE ─────────────────────────────────────────────────────
_last_hashes   = {}     # filename → last-pushed MD5
_last_push_ts  = 0.0    # epoch time of last successful push
_push_count    = 0      # total pushes this session
_skip_count    = 0      # total no-change skips this session


# ── HELPERS ──────────────────────────────────────────────────
def file_hash(path: str) -> str:
    """Return MD5 hex of file contents, or '' if file missing."""
    try:
        with open(path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except OSError:
        return ""


def files_changed() -> list[str]:
    """Return list of files whose content has changed since last push."""
    changed = []
    for fpath in DATA_FILES:
        if not os.path.exists(fpath):
            continue
        current = file_hash(fpath)
        if current and current != _last_hashes.get(fpath, ""):
            changed.append(fpath)
    return changed


def update_hashes(files: list[str]):
    """Record current hashes for the given files."""
    for fpath in files:
        _last_hashes[fpath] = file_hash(fpath)


def git_run(cmd: list[str], silent: bool = False) -> bool:
    """Run a git command. Returns True on success."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=20,
        )
        if result.returncode != 0 and not silent:
            # Only print meaningful errors, not "nothing to commit"
            stderr = result.stderr.strip()
            if stderr and "nothing to commit" not in stderr:
                print(f"  git warning: {stderr[:120]}")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("  ⚠ git command timed out — network issue?")
        return False
    except FileNotFoundError:
        print("  ✗ git not found. Install Git and add it to PATH.")
        return False


# ── SYNC ─────────────────────────────────────────────────────
def sync_changed(changed: list[str]) -> bool:
    """
    Stage → commit → push only the files that changed.
    Returns True on successful push.
    """
    global _push_count, _last_push_ts

    # 1. Stage only changed files
    for fpath in changed:
        git_run(["git", "add", fpath])

    # 2. Commit with WAT timestamp
    ts_wat  = datetime.now(WAT).strftime("%d %b %Y, %H:%M:%S WAT")
    files_s = ", ".join(os.path.basename(f) for f in changed)
    message = f"⚡ Live Sync [{ts_wat}] — {files_s}"

    committed = git_run(["git", "commit", "-m", message])
    if not committed:
        # Nothing staged / nothing to commit — update hashes so we
        # don't keep retrying the same unchanged content
        update_hashes(changed)
        return False

    # 3. Push
    pushed = git_run(["git", "push", "origin", "main"])
    if pushed:
        _push_count  += 1
        _last_push_ts = time.time()
        update_hashes(changed)
        print(
            f"  [{datetime.now(WAT).strftime('%H:%M:%S')} WAT] "
            f"✓ Push #{_push_count} — {files_s}"
        )
        return True
    else:
        print("  ✗ Push failed — will retry next cycle")
        # Don't update hashes: files are still "dirty", retry on next cycle
        return False


# ── MAIN ─────────────────────────────────────────────────────
def main():
    global _skip_count

    print("=" * 60)
    print("  AirGuard NG — Smart Cloud Sync")
    print("=" * 60)
    print(f"  Watching : {', '.join(DATA_FILES)}")
    print(f"  Interval : {CHECK_INTERVAL}s check / {PUSH_COOLDOWN}s min push gap")
    print(f"  Timezone : WAT (UTC+1)")
    print("=" * 60)
    print()

    # Seed hashes so first run only pushes genuine changes
    for fpath in DATA_FILES:
        if os.path.exists(fpath):
            _last_hashes[fpath] = file_hash(fpath)
            print(f"  Seeded hash for {fpath}")
    print()
    print("  Monitoring for changes...\n")

    while True:
        try:
            changed = files_changed()

            if not changed:
                _skip_count += 1
                # Print a heartbeat every 30 skips so you know it's alive
                if _skip_count % 30 == 0:
                    ts = datetime.now(WAT).strftime("%H:%M:%S")
                    print(
                        f"  [{ts} WAT] ♻ No changes — "
                        f"{_push_count} pushes, {_skip_count} skips"
                    )
            else:
                # Respect cooldown to avoid GitHub hammering
                elapsed = time.time() - _last_push_ts
                if elapsed < PUSH_COOLDOWN:
                    wait = PUSH_COOLDOWN - elapsed
                    time.sleep(wait)

                sync_changed(changed)

        except KeyboardInterrupt:
            print(f"\n  Stopped. Session: {_push_count} pushes, {_skip_count} skips.")
            break
        except Exception as e:
            print(f"  Unexpected error: {e}")
            time.sleep(5)

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
