@echo off
echo ============================================
echo  AirGuard NG — Auto Push to GitHub
echo ============================================

:: ── SET YOUR PATHS HERE ──────────────────────
set REPO=C:\Users\user\Documents\airguard-ng
set DOWNLOADS=C:\Users\user\Downloads

:: ── COPY ROOT FILES ──────────────────────────
echo Copying root files...
copy "%DOWNLOADS%\overview.py"     "%REPO%\overview.py"     /Y
copy "%DOWNLOADS%\styles.py"       "%REPO%\styles.py"       /Y

:: ── COPY PAGES FILES ─────────────────────────
echo Copying pages...
copy "%DOWNLOADS%\1_City_Deep_Dive.py"    "%REPO%\pages\1_City_Deep_Dive.py"    /Y
copy "%DOWNLOADS%\2_Compare_Cities.py"    "%REPO%\pages\2_Compare_Cities.py"    /Y
copy "%DOWNLOADS%\3_Historical_Trends.py" "%REPO%\pages\3_Historical_Trends.py" /Y
copy "%DOWNLOADS%\4_Alerts_Log.py"        "%REPO%\pages\4_Alerts_Log.py"        /Y
copy "%DOWNLOADS%\5_Health_Guide.py"      "%REPO%\pages\5_Health_Guide.py"      /Y
copy "%DOWNLOADS%\6_Best_Practices.py"    "%REPO%\pages\6_Best_Practices.py"    /Y
copy "%DOWNLOADS%\7_About.py"             "%REPO%\pages\7_About.py"             /Y
copy "%DOWNLOADS%\8_Device.py"            "%REPO%\pages\8_Device.py"            /Y

:: ── GIT PUSH ─────────────────────────────────
echo.
echo Pushing to GitHub...
cd /d "%REPO%"
git add overview.py styles.py pages/
git commit -m "Add floating nav button to all pages"
git push

echo.
echo ============================================
echo  Done! Check Streamlit to confirm deploy.
echo ============================================
pause
