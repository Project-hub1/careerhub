@echo off
setlocal
cd /d "%~dp0"
echo ========================================
echo CareerHub setup
echo ========================================
if not exist venv (
  echo Creating Python virtual environment...
  python -m venv venv || goto :error
)
call venv\Scripts\activate.bat || goto :error
python -m pip install --upgrade pip || goto :error
python -m pip install -r requirements.txt || goto :error
if not exist .env copy /Y .env.example .env >nul
flask db upgrade || goto :error
python seed.py || goto :error
echo.
echo Setup complete.
echo Start the app with start.bat
echo URL: http://127.0.0.1:5000
echo.
pause
exit /b 0
:error
echo.
echo Setup failed. Check the error above.
pause
exit /b 1
