@echo off
setlocal
title Badminton Booking CLI
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\launch_booking.ps1"
set "RC=%ERRORLEVEL%"
echo.
if not "%RC%"=="0" echo Manager exited with error code %RC%.
pause
exit /b %RC%
