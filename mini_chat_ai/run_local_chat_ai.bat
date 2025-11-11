@echo off
SETLOCAL

:: -----------------------------
:: Check Python installation
:: -----------------------------
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not in PATH.
    echo Please install Python from https://www.python.org/downloads/windows/
    pause
    exit /b
)

:: -----------------------------
:: Upgrade pip
:: -----------------------------
python -m pip install --upgrade pip

:: -----------------------------
:: Install required packages
:: -----------------------------
echo Installing required packages...
python -m pip install --upgrade flask torch transformers sentence-transformers faiss-cpu

:: -----------------------------
:: Start Flask server
:: -----------------------------
echo Starting AI chat server...
start "" cmd /k "python server.py"

:: -----------------------------
:: Wait for server to start
:: -----------------------------
timeout /t 5 /nobreak >nul

:: -----------------------------
:: Open default browser
:: -----------------------------
echo Opening chat page in default browser...
start http://127.0.0.1:5000

ENDLOCAL
