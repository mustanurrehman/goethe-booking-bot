@echo off
title Goethe DETAILS Click Test — INDIA
cd /d "%~dp0"
REM ============================================================
REM  India B1 card ke "DETAILS" par click karke dekho kya khulta hai.
REM  Ye batayega: booking ka asli entry point kya hai.
REM  Pehle launch_chrome_debug.bat chalao (Chrome khula + login).
REM ============================================================
set USE_REAL_CHROME=1
set REAL_CHROME_PORT=9222
set DIAG_URL=https://www.goethe.de/ins/in/en/spr/prf/gzb1.cfm
python diag_details.py
echo.
echo Done. Upar result dekho.
pause