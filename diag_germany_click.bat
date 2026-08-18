@echo off
title Goethe Click Test — GERMANY (Select modules)
cd /d "%~dp0"
REM ============================================================
REM  Germany B1 (Hamburg) ka "Select modules" click karke dekhte
REM  hain kya khulta hai — module picker / booking wizard.
REM  Sirf OBSERVE karta hai, submit/payment nahi.
REM  Pehle launch_chrome_debug.bat chalao (Chrome khula + login).
REM ============================================================
set USE_REAL_CHROME=1
set REAL_CHROME_PORT=9222
set DIAG_URL=https://www.goethe.de/ins/de/en/prf/ort/ham/gzb1.cfm
set DIAG_BUTTON=Select modules
python diag_click.py
echo.
echo Done. Upar result dekho.
pause
