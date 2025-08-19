#!/bin/bash

# LTW Audio Splitter - Quick Start Script
# This script activates the virtual environment and starts the application

echo "🎵 LTW Audio Splitter - Quick Start"
echo "==================================="

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: app.py not found. Please run this script from the project root directory."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Error: Virtual environment not found. Please run the setup first."
    echo "Run: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if required packages are installed
echo "📦 Checking dependencies..."
python -c "import streamlit, librosa, demucs" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Error: Required packages not found. Installing..."
    pip install -r requirements.txt
fi

# Run the test script
echo "🧪 Running system tests..."
python test_app.py
if [ $? -ne 0 ]; then
    echo "❌ System tests failed. Please check the installation."
    exit 1
fi

# Start the application
echo "🚀 Starting LTW Audio Splitter..."
echo "📱 The application will open in your web browser at http://localhost:8501"
echo "🛑 Press Ctrl+C to stop the application"
echo ""

streamlit run app.py
