#!/usr/bin/env python3
"""
Test script for Beat & Stems Lab installation
Verifies that all dependencies are properly installed
"""

import sys
import importlib
from pathlib import Path

def test_import(module_name, package_name=None):
    """Test if a module can be imported"""
    try:
        importlib.import_module(module_name)
        print(f"✅ {package_name or module_name}")
        return True
    except ImportError as e:
        print(f"❌ {package_name or module_name}: {e}")
        return False

def test_optional_import(module_name, package_name=None):
    """Test if an optional module can be imported"""
    try:
        importlib.import_module(module_name)
        print(f"✅ {package_name or module_name} (optional)")
        return True
    except ImportError:
        print(f"⚠️  {package_name or module_name} (optional) - not installed")
        return False

def main():
    """Run installation tests"""
    print("🎵 Beat & Stems Lab - Installation Test")
    print("=" * 50)
    
    # Test Python version
    python_version = sys.version_info
    if python_version >= (3, 9):
        print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    else:
        print(f"❌ Python {python_version.major}.{python_version.minor}.{python_version.micro} (requires 3.9+)")
        return False
    
    print("\n📦 Core Dependencies:")
    
    # Core dependencies
    core_deps = [
        ("streamlit", "Streamlit"),
        ("librosa", "librosa"),
        ("matplotlib", "matplotlib"),
        ("plotly", "plotly"),
        ("soundfile", "soundfile"),
        ("numpy", "numpy"),
        ("scipy", "scipy"),
        ("pretty_midi", "pretty_midi"),
    ]
    
    core_success = True
    for module, name in core_deps:
        if not test_import(module, name):
            core_success = False
    
    print("\n🎛️ Stem Separation:")
    
    # Stem separation (at least one required)
    separation_deps = [
        ("spleeter", "Spleeter"),
        ("demucs", "Demucs"),
    ]
    
    separation_success = False
    for module, name in separation_deps:
        if test_optional_import(module, name):
            separation_success = True
    
    if not separation_success:
        print("❌ No stem separation library found!")
        print("   Install at least one: pip install spleeter OR pip install demucs")
        core_success = False
    
    print("\n🎹 Melody Extraction:")
    
    # Melody extraction (optional but recommended)
    melody_deps = [
        ("crepe", "CREPE"),
        ("basic_pitch", "basic-pitch"),
    ]
    
    melody_success = False
    for module, name in melody_deps:
        if test_optional_import(module, name):
            melody_success = True
    
    if not melody_success:
        print("⚠️  No melody extraction library found!")
        print("   Recommended: pip install crepe")
    
    print("\n🔧 Optional Dependencies:")
    
    # Optional dependencies
    optional_deps = [
        ("essentia", "Essentia"),
        ("madmom", "madmom"),
        ("torch", "PyTorch"),
    ]
    
    for module, name in optional_deps:
        test_optional_import(module, name)
    
    print("\n📁 Project Structure:")
    
    # Check project structure
    required_files = [
        "app.py",
        "config.py",
        "requirements.txt",
        "README.md",
        "src/__init__.py",
        "src/io_utils.py",
        "src/viz.py",
        "src/separation.py",
        "src/timing.py",
        "src/melody.py",
        "src/chords.py",
        "src/drums.py",
        "src/export.py",
    ]
    
    structure_success = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} (missing)")
            structure_success = False
    
    print("\n" + "=" * 50)
    
    # Summary
    if core_success and separation_success and structure_success:
        print("🎉 Installation test PASSED!")
        print("\n🚀 You can now run the application:")
        print("   streamlit run app.py")
        
        if not melody_success:
            print("\n💡 For melody extraction, install CREPE:")
            print("   pip install crepe")
        
        return True
    else:
        print("❌ Installation test FAILED!")
        print("\n🔧 Please fix the issues above before running the application.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
