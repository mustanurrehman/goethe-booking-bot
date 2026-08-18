@echo off
title Goethe Page Diagnostic
cd /d "%~dp0"
REM ============================================================
REM  Real Chrome (port 9222) se page ka structure dump karo.
REM  Ye batayega: iframes hain, pr_finder hai, buttons kahan hain.
REM  Pehle launch_chrome_debug.bat chalao (Chrome khula + login).
REM ============================================================
set USE_REAL_CHROME=1
set REAL_CHROME_PORT=9222
python diag_page.py
echo.
echo Done. Upar structure dekho.
pause