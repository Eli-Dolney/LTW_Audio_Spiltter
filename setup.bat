@echo off
REM LTW Audio Splitter - Setup Script for Windows
REM This script sets up the complete environment from scratch

echo 🎵 LTW Audio Splitter - Setup
echo ==============================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Python is not installed or not in PATH.
    echo Please install Python 3.9 or higher from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

REM Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set python_version=%%i
echo ✅ Python %python_version% detected

REM Create virtual environment
echo 🔧 Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo 📦 Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
echo 📦 Installing dependencies...
pip install -r requirements.txt

REM Install additional packages
echo 📦 Installing stem separation packages...
pip install spleeter
pip install crepe

REM Test installation
echo 🧪 Testing installation...
python test_installation.py

if errorlevel 1 (
    echo.
    echo ❌ Setup failed. Please check the error messages above.
    echo 📖 For troubleshooting, see the README.md file
    pause
    exit /b 1
) else (
    echo.
    echo ✅ Setup completed successfully!
    echo.
    echo 🚀 To start the application, run:
    echo    quick_start.bat
    echo.
    echo 📖 For manual setup, see the README.md file
)

pause
