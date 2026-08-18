@echo off
title Goethe Chrome (Debug Port 9222)
REM ============================================================
REM  Step 1/2 — Real Chrome with remote debugging
REM  Ye real (headed) Chrome kholta hai with your real profile.
REM  Usme login karo (my.goethe.de), phir step 2 chalana.
REM ============================================================
echo Starting real Chrome with debugging port 9222...
echo.
echo IMPORTANT: Chrome khulega. Wahan jao aur login karo:
echo   https://my.goethe.de
echo.
echo Phir is window ko CHHONA MAT, bas 2nd bat file chalao.
echo.

start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" ^
  --remote-debugging-port=9222 ^
  --user-data-dir="%USERPROFILE%\goethe-real-profile" ^
  --no-first-run ^
  --profile-directory=Default

echo.
echo Chrome start ho gaya. Is window ko khula rakho (mat band karo).
pause
