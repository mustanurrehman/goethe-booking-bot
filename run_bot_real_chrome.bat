@echo off
title Goethe Bot — FINAL BOOKING (Real Chrome)
cd /d "%~dp0"
REM ============================================================
REM  FINAL BOOKING — jb Lahore ki seat khulegi, ye chalao.
REM  Yeh real confirm click karta hai = REAL charge.
REM  NOTE: config.csv me city=Lahore honi chahiye aur modules
REM  decide kiye hue. Agar test karna ho (no charge) to
REM  run_test_mode.bat chalao (NO_FINAL_CONFIRM=1, no confirm).
REM  Pehle launch_chrome_debug.bat chalao (Chrome khula + login).
REM ============================================================

set USE_REAL_CHROME=1
set REAL_CHROME_PORT=9222

echo FINAL BOOKING MODE — real confirm click hoga (charge).
echo Check: config.csv me city=Lahore, modules set hain.
echo (Test chahiye to run_test_mode.bat use karo — NO charge.)
echo.

REM --immediate = wait NAHI karo, abhi koshish karo.
REM Booking-day timing chahiye to --immediate hata do (config.csv
REM ka booking_datetime use hoga).
python booking_helper.py --config config.csv --headless false --immediate

echo.
echo Bot kaam khatam. Log upar dekho.
pause
