#!/bin/bash

echo "🍎 Setting up LTW Audio v2 for Mac (Apple Silicon / MPS friendly)..."

echo "🧹 Creating virtual environment..."
rm -rf venv
python3 -m venv venv
source venv/bin/activate

echo "⬆️  Upgrading pip..."
pip install --upgrade pip setuptools wheel

echo "🔥 Installing PyTorch..."
pip install torch torchaudio

echo "📦 Installing requirements..."
pip install -r requirements.txt

echo "✅ Installation complete!"
echo "🚀 Run: ./quick_start.sh"
echo "   Or:  source venv/bin/activate && streamlit run app.py"
