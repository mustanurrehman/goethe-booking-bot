@echo off
title Goethe DETAILS Click Test — GERMANY
cd /d "%~dp0"
REM ============================================================
REM  Germany B1 (Hamburg) card ke "DETAILS" par click karke dekho
REM  kya khulta hai — Select modules / book button.
REM  Pakistan ka flow Germany jaise hi hai, isliye yahan confirm
REM  kar lete hain. Pehle launch_chrome_debug.bat chalao.
REM ============================================================
set USE_REAL_CHROME=1
set REAL_CHROME_PORT=9222
set DIAG_URL=https://www.goethe.de/ins/de/en/prf/ort/ham/gzb1.cfm
python diag_details.py
echo.
echo Done. Upar result dekho.
pause
