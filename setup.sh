#!/bin/bash

# LTW Audio Splitter - Setup Script for macOS/Linux
# This script sets up the complete environment from scratch

echo "🎵 LTW Audio Splitter - Setup"
echo "=============================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed. Please install Python 3.9 or higher."
    echo "Visit: https://www.python.org/downloads/"
    exit 1
fi

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python $python_version is installed, but Python $required_version or higher is required."
    exit 1
fi

echo "✅ Python $python_version detected"

# Create virtual environment
echo "🔧 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Install additional packages
echo "📦 Installing stem separation packages..."
pip install spleeter
pip install crepe

# Test installation
echo "🧪 Testing installation..."
python test_installation.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Setup completed successfully!"
    echo ""
    echo "🚀 To start the application, run:"
    echo "   ./quick_start.sh"
    echo ""
    echo "📖 For manual setup, see the README.md file"
else
    echo ""
    echo "❌ Setup failed. Please check the error messages above."
    echo "📖 For troubleshooting, see the README.md file"
    exit 1
fi
