#!/bin/bash

# LTW Audio - Quick Start Script
echo "🎵 LTW Audio - Quick Start"
echo "=========================="

if [ ! -f "app.py" ]; then
    echo "❌ Error: app.py not found. Run from project root."
    exit 1
fi

if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found."
    echo "Run: ./setup.sh  OR  python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

echo "🔧 Activating virtual environment..."
source venv/bin/activate

echo "📦 Checking dependencies..."
python -c "import streamlit, librosa, demucs, torch" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing requirements..."
    pip install -r requirements.txt
fi

echo "🛑 Stopping any old Streamlit instances..."
pkill -f "streamlit run app.py" 2>/dev/null || true
sleep 1

echo "🚀 Starting LTW Audio at http://localhost:8501"
echo "   (Use 8501 only — ignore 8502 if an old test server was left running)"
echo "🛑 Press Ctrl+C to stop"
echo ""

streamlit run app.py
