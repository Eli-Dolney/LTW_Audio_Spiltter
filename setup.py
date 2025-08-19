#!/usr/bin/env python3
"""
Setup script for Beat & Stems Lab
Helps with installation and dependency management
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stdout:
            print(f"   stdout: {e.stdout}")
        if e.stderr:
            print(f"   stderr: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version < (3, 9):
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} is not supported")
        print("   Please install Python 3.9 or higher")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def install_dependencies():
    """Install core dependencies"""
    print("\n📦 Installing core dependencies...")
    
    # Upgrade pip
    if not run_command(f"{sys.executable} -m pip install --upgrade pip", "Upgrading pip"):
        return False
    
    # Install core requirements
    if not run_command(f"{sys.executable} -m pip install -r requirements.txt", "Installing core dependencies"):
        return False
    
    return True

def install_stem_separation():
    """Install stem separation libraries"""
    print("\n🎛️ Installing stem separation...")
    
    print("Choose stem separation method:")
    print("1. Spleeter (fast, recommended)")
    print("2. Demucs (high quality, slower)")
    print("3. Both")
    print("4. Skip")
    
    choice = input("Enter choice (1-4): ").strip()
    
    if choice == "1":
        return run_command(f"{sys.executable} -m pip install spleeter", "Installing Spleeter")
    elif choice == "2":
        return run_command(f"{sys.executable} -m pip install demucs", "Installing Demucs")
    elif choice == "3":
        success1 = run_command(f"{sys.executable} -m pip install spleeter", "Installing Spleeter")
        success2 = run_command(f"{sys.executable} -m pip install demucs", "Installing Demucs")
        return success1 and success2
    elif choice == "4":
        print("⚠️  Skipping stem separation installation")
        return True
    else:
        print("❌ Invalid choice")
        return False

def install_melody_extraction():
    """Install melody extraction libraries"""
    print("\n🎹 Installing melody extraction...")
    
    print("Choose melody extraction method:")
    print("1. CREPE (recommended)")
    print("2. basic-pitch")
    print("3. Both")
    print("4. Skip")
    
    choice = input("Enter choice (1-4): ").strip()
    
    if choice == "1":
        return run_command(f"{sys.executable} -m pip install crepe", "Installing CREPE")
    elif choice == "2":
        return run_command(f"{sys.executable} -m pip install basic-pitch", "Installing basic-pitch")
    elif choice == "3":
        success1 = run_command(f"{sys.executable} -m pip install crepe", "Installing CREPE")
        success2 = run_command(f"{sys.executable} -m pip install basic-pitch", "Installing basic-pitch")
        return success1 and success2
    elif choice == "4":
        print("⚠️  Skipping melody extraction installation")
        return True
    else:
        print("❌ Invalid choice")
        return False

def install_optional_dependencies():
    """Install optional dependencies"""
    print("\n🔧 Installing optional dependencies...")
    
    print("Install optional dependencies? (y/n): ", end="")
    choice = input().strip().lower()
    
    if choice in ['y', 'yes']:
        # Install PyTorch (for GPU acceleration)
        print("Install PyTorch for GPU acceleration? (y/n): ", end="")
        pytorch_choice = input().strip().lower()
        
        if pytorch_choice in ['y', 'yes']:
            print("Choose PyTorch installation:")
            print("1. CPU only")
            print("2. CUDA (NVIDIA GPU)")
            print("3. Skip PyTorch")
            
            pytorch_type = input("Enter choice (1-3): ").strip()
            
            if pytorch_type == "1":
                run_command(f"{sys.executable} -m pip install torch torchvision torchaudio", "Installing PyTorch (CPU)")
            elif pytorch_type == "2":
                run_command(f"{sys.executable} -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118", "Installing PyTorch (CUDA)")
            elif pytorch_type == "3":
                print("⚠️  Skipping PyTorch installation")
        
        # Install other optional dependencies
        optional_packages = [
            ("essentia", "Essentia (advanced audio analysis)"),
            ("madmom", "madmom (advanced rhythm analysis)"),
        ]
        
        for package, description in optional_packages:
            print(f"Install {description}? (y/n): ", end="")
            if input().strip().lower() in ['y', 'yes']:
                run_command(f"{sys.executable} -m pip install {package}", f"Installing {package}")
    
    return True

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    
    directories = [
        "projects",
        "temp",
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created {directory}/")
    
    return True

def run_tests():
    """Run installation tests"""
    print("\n🧪 Running installation tests...")
    
    if Path("test_installation.py").exists():
        return run_command(f"{sys.executable} test_installation.py", "Running installation tests")
    else:
        print("⚠️  test_installation.py not found, skipping tests")
        return True

def main():
    """Main setup function"""
    print("🎵 Beat & Stems Lab - Setup")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Install dependencies
    if not install_dependencies():
        return False
    
    # Install stem separation
    if not install_stem_separation():
        return False
    
    # Install melody extraction
    if not install_melody_extraction():
        return False
    
    # Install optional dependencies
    if not install_optional_dependencies():
        return False
    
    # Create directories
    if not create_directories():
        return False
    
    # Run tests
    if not run_tests():
        return False
    
    print("\n" + "=" * 40)
    print("🎉 Setup completed successfully!")
    print("\n🚀 To start the application:")
    print("   streamlit run app.py")
    print("\n📖 For more information, see README.md")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
