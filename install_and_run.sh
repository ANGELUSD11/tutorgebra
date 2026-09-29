#!/bin/bash

echo "==================================================="
echo "Welcome to TutorGebra AI - Setup and Run Script"
echo "==================================================="
echo ""

# Check if Python is installed
echo "[1/4] Checking Python installation..."
if ! command -v python3 &> /dev/null
then
    echo "Error: python3 is not installed."
    echo "Please install Python and try again."
    exit 1
fi

echo ""
echo "[2/4] Creating virtual environment (.venv)..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

echo ""
echo "[3/4] Installing dependencies..."
source .venv/bin/activate
python3 -m pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "[4/4] Installing Playwright Chromium browser..."
playwright install chromium

echo ""
echo "==================================================="
echo "Setup Complete! Starting TutorGebra AI Server..."
echo "Please leave this terminal open."
echo "Open your browser and go to http://localhost:8000"
echo "==================================================="
echo ""
python3 app/main.py
