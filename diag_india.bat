@echo off
title Goethe Page Diagnostic — INDIA B1
cd /d "%~dp0"
REM ============================================================
REM  India B1 page (dates PUBLISHED hain) — structure dump.
REM  Same pr_finder widget as Pakistan, same www.goethe.de.
REM  Agar yahan buttons/iframe dikhe, hum flow fix kar ke
REM  Pakistan per confidence badha lenge.
REM  Pehle launch_chrome_debug.bat chalao (Chrome khula).
REM ============================================================
set USE_REAL_CHROME=1
set REAL_CHROME_PORT=9222
python diag_page.py https://www.goethe.de/ins/in/en/spr/prf/gzb1.cfm
echo.
echo Done. Upar structure dekho.
pause