@echo off
setlocal
title Resume Badminton Booking
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_booking.ps1"
set "EXITCODE=%ERRORLEVEL%"
echo.
if not "%EXITCODE%"=="0" echo Resume command failed with exit code %EXITCODE%.
pause
exit /b %EXITCODE%
