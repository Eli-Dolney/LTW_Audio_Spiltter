@echo off
REM LTW Audio Splitter - Quick Start Script for Windows
REM This script activates the virtual environment and starts the application

echo 🎵 LTW Audio Splitter - Quick Start
echo ===================================

REM Check if we're in the right directory
if not exist "app.py" (
    echo ❌ Error: app.py not found. Please run this script from the project root directory.
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo ❌ Error: Virtual environment not found. Please run the setup first.
    echo Run: python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt
    pause
    exit /b 1
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if required packages are installed
echo 📦 Checking dependencies...
python -c "import streamlit, librosa, demucs" 2>nul
if errorlevel 1 (
    echo ❌ Error: Required packages not found. Installing...
    pip install -r requirements.txt
)

REM Run the test script
echo 🧪 Running system tests...
python test_app.py
if errorlevel 1 (
    echo ❌ System tests failed. Please check the installation.
    pause
    exit /b 1
)

REM Start the application
echo 🚀 Starting LTW Audio Splitter...
echo 📱 The application will open in your web browser at http://localhost:8501
echo 🛑 Press Ctrl+C to stop the application
echo.

streamlit run app.py
