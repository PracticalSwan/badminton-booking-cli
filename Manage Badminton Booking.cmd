@echo off
setlocal
title Badminton Booking CLI
cd /d "%~dp0"
"%~dp0.venv\Scripts\python.exe" "%~dp0booking_manager.py"
set "RC=%ERRORLEVEL%"
echo.
if not "%RC%"=="0" echo Manager exited with error code %RC%.
pause
exit /b %RC%
