@echo off
title Pakistan B1 Slot Guard — watch mode
cd /d "%~dp0"
REM Har 3 min Pakistan B1 page check. Jab SELECT MODULES dikhe to notify + exit.
set USE_REAL_CHROME=1
set REAL_CHROME_PORT=9222
python pk_guard.py
pause
