@echo off
setlocal
title Pause Badminton Booking
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0stop_booking.ps1"
set "EXITCODE=%ERRORLEVEL%"
echo.
if not "%EXITCODE%"=="0" echo Pause command failed with exit code %EXITCODE%.
pause
exit /b %EXITCODE%
