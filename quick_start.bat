@echo off
REM LTW Audio - Quick Start for Windows

echo LTW Audio - Quick Start
echo =======================

if not exist "app.py" (
    echo Error: app.py not found.
    pause
    exit /b 1
)

if not exist "venv" (
    echo Error: venv not found. Run setup first.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

python -c "import streamlit, librosa, demucs" 2>nul
if errorlevel 1 pip install -r requirements.txt

echo Starting LTW Audio v2 at http://localhost:8501
streamlit run app.py
