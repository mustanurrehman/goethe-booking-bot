@echo off
title Goethe Probe — Real Chrome (Check only)
cd /d "%~dp0"
REM ============================================================
REM  Real Chrome se sirf CHECK karo (book NAHI karta).
REM  Ye batayega ke Goethe ka page khulta hai ya Forbidden:
REM    - PAGE LOADED title='The Goethe...'  -> ACHA, page khula
REM    - BLOCKED/WAF or Forbidden -> abhi bhi block
REM  Pehle launch_chrome_debug.bat chalao (Chrome + login).
REM ============================================================

set USE_REAL_CHROME=1
set REAL_CHROME_PORT=9222

echo Checking slot/page through real Chrome...
echo.
python booking_helper.py --config config.csv --check-only

echo.
echo Done. Upar result dekho.
pause