@echo off
echo ===================================================
echo Welcome to TutorGebra AI - Setup and Run Script
echo ===================================================

echo.
echo [1/4] Checking Python installation...
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Error: Python is not installed or not added to PATH.
    echo Please install Python from https://www.python.org/downloads/ and try again.
    pause
    exit /b 1
)

echo.
echo [2/4] Creating virtual environment (.venv)...
if not exist ".venv" (
    python -m venv .venv
)

echo.
echo [3/4] Installing dependencies...
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.



echo.
echo ===================================================
echo Setup Complete! Starting TutorGebra AI Server...
echo Please leave this window open.
echo Open your browser and go to http://localhost:8000
echo ===================================================
echo.
python app/main.py

pause
