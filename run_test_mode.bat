@echo off
title Goethe Bot — TEST MODE (no final confirm, no charge)
cd /d "%~dp0"
REM ============================================================
REM  TEST MODE — Karachi (ya koi bhi) slot par poora flow chalao,
REM  lekin LAST CONFIRM click NAHI hota. No 36000 PKR charge.
REM  Ye high-demand re-race (scoop) test ke liye hai.
REM
REM  Pehle launch_chrome_debug.bat chalao (Chrome khula + login).
REM  Real FINAL booking ke liye run_bot_real_chrome.bat use karo
REM  (jab Lahore slot khulegi).
REM ============================================================

set USE_REAL_CHROME=1
set REAL_CHROME_PORT=9222
set NO_FINAL_CONFIRM=1

echo TEST MODE: full flow up to review — final confirm NOT clicked.
echo.

python booking_helper.py --config config.csv --headless false --immediate

echo.
echo Test done. Review page tak pohncha (no booking submitted).
pause