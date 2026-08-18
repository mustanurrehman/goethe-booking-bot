@echo off
title PK B1 Probe — observe only
cd /d "%~dp0"
set USE_REAL_CHROME=1
set REAL_CHROME_PORT=9222
python diag_pk_probe.py
echo.
echo Done. Result upar dekho.
pause
