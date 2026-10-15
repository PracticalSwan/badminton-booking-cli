@echo off
setlocal
cd /d "%~dp0"
"%~dp0.venv\Scripts\python.exe" "%~dp0booking.py" >> "%~dp0task_console.log" 2>&1
exit /b %errorlevel%
