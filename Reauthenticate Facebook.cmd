@echo off
setlocal
title Facebook Messenger Authentication
cd /d "%~dp0"
"%~dp0.venv\Scripts\python.exe" "%~dp0booking.py" --login
echo.
pause
exit /b %errorlevel%
