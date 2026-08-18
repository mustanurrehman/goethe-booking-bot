@echo off
title Goethe Bot — Real Chrome (Attach)
cd /d "%~dp0"
REM ============================================================
REM  Step 2/2 — Bot real Chrome se attach hota hai
REM  Pehle launch_chrome_debug.bat chalao (login karo), phir ye.
REM  Ye browser ke cookies/naam ke saath book try karta hai.
REM ============================================================

set USE_REAL_CHROME=1
set REAL_CHROME_PORT=9222

echo Attaching to real Chrome on port 9222 ...
echo (Agar Chrome nahi khula, pehle launch_chrome_debug.bat chalao)
echo.

REM --immediate = wait NAHI karo, abhi koshish karo (test ke liye).
REM Booking day par agar wait chahiye to --immediate hata dena.
python booking_helper.py --config config.csv --headless false --immediate

echo.
echo Bot kaam khatam. Log upar dekho.
pause
