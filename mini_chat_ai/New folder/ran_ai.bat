@echo off
SETLOCAL

:: Check Python
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Python not found. Please install it from https://www.python.org/downloads/windows/
    pause
    exit /b
)

:: Upgrade pip
python -m pip install --upgrade pip

:: Install packages
echo Installing required packages...
python -m pip install --upgrade flask openai

:: Start the Flask server
echo Starting Agyei AI server...
start "" cmd /k "python server.py"

:: Wait a few seconds
timeout /t 5 /nobreak >nul

:: Open browser
echo Opening chat in browser...
start http://127.0.0.1:5000

ENDLOCAL
