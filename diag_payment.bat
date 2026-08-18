@echo off
title Goethe Payment Test — observe only
cd /d "%~dp0"
set USE_REAL_CHROME=1
set REAL_CHROME_PORT=9222
python diag_payment.py
echo.
echo Done. Result upar dekho.
pause
