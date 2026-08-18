@echo off
title Goethe Page Diagnostic — GERMANY B1
cd /d "%~dp0"
REM ============================================================
REM  Germany B1 page (Hamburg) — structure dump.
REM  Pakistan ka flow Germany jaise hi hai. Dates published hain
REM  to finder/buttons ka asli structure yahan dekhenge.
REM  Pehle launch_chrome_debug.bat chalao (Chrome khula).
REM ============================================================
set USE_REAL_CHROME=1
set REAL_CHROME_PORT=9222
python diag_page.py https://www.goethe.de/ins/de/en/prf/ort/ham/gzb1.cfm
echo.
echo Done. Upar structure dekho.
pause
