@echo off
setlocal
cd /d "%~dp0"
if not exist venv\Scripts\activate.bat (
  echo Virtual environment not found. Run setup.bat first.
  pause
  exit /b 1
)
call venv\Scripts\activate.bat
cls
echo ========================================
echo CareerHub is starting...
echo ========================================
echo Open: http://127.0.0.1:5000
echo Press Ctrl+C to stop the server.
echo.
python run.py
pause
