#!/usr/bin/env python3
"""
Test script for Beat & Stems Lab
Verifies that all core modules are working correctly
"""
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    
    try:
        from config import APP_TITLE, APP_VERSION
        print(f"✅ Config imported: {APP_TITLE} v{APP_VERSION}")
    except Exception as e:
        print(f"❌ Config import failed: {e}")
        return False
    
    try:
        from src.io_utils import ProjectManager, load_audio_file
        print("✅ IO utils imported")
    except Exception as e:
        print(f"❌ IO utils import failed: {e}")
        return False
    
    try:
        from src.viz import create_waveform_plot
        print("✅ Visualization module imported")
    except Exception as e:
        print(f"❌ Visualization import failed: {e}")
        return False
    
    try:
        from src.separation import StemSeparator, get_available_methods
        print("✅ Separation module imported")
    except Exception as e:
        print(f"❌ Separation import failed: {e}")
        return False
    
    try:
        from src.timing import create_beat_grid
        print("✅ Timing module imported")
    except Exception as e:
        print(f"❌ Timing import failed: {e}")
        return False
    
    try:
        from src.melody import extract_melody_to_midi
        print("✅ Melody module imported")
    except Exception as e:
        print(f"❌ Melody import failed: {e}")
        return False
    
    try:
        from src.chords import analyze_chord_progression
        print("✅ Chords module imported")
    except Exception as e:
        print(f"❌ Chords import failed: {e}")
        return False
    
    try:
        from src.drums import extract_drums_to_midi
        print("✅ Drums module imported")
    except Exception as e:
        print(f"❌ Drums import failed: {e}")
        return False
    
    try:
        from src.export import export_project_summary
        print("✅ Export module imported")
    except Exception as e:
        print(f"❌ Export import failed: {e}")
        return False
    
    return True

def test_separation_methods():
    """Test available separation methods"""
    print("\nTesting separation methods...")
    
    try:
        from src.separation import get_available_methods
        methods = get_available_methods()
        print(f"✅ Available methods: {list(methods.keys())}")
        
        if methods:
            print("Available separation methods:")
            for method, description in methods.items():
                print(f"  - {method}: {description}")
        else:
            print("⚠️ No separation methods available")
            
    except Exception as e:
        print(f"❌ Separation methods test failed: {e}")
        return False
    
    return True

def test_project_creation():
    """Test project creation functionality"""
    print("\nTesting project creation...")
    
    try:
        from src.io_utils import ProjectManager
        from config import PROJECTS_DIR
        
        # Create a test project
        test_project = ProjectManager("test_project")
        print("✅ Project manager created")
        
        # Test project config
        config = {
            "project_name": "test_project",
            "version": "1.0.0",
            "created_at": "2024-01-01",
            "status": "test"
        }
        
        test_project.save_project_config(config)
        print("✅ Project config saved")
        
        loaded_config = test_project.load_project_config()
        print("✅ Project config loaded")
        
        # Clean up
        import shutil
        if test_project.project_path.exists():
            shutil.rmtree(test_project.project_path)
        print("✅ Test project cleaned up")
        
    except Exception as e:
        print(f"❌ Project creation test failed: {e}")
        return False
    
    return True

def main():
    """Run all tests"""
    print("🎵 Beat & Stems Lab - System Test")
    print("=" * 40)
    
    # Test imports
    if not test_imports():
        print("\n❌ Import tests failed. Please check your installation.")
        return False
    
    # Test separation methods
    if not test_separation_methods():
        print("\n❌ Separation methods test failed.")
        return False
    
    # Test project creation
    if not test_project_creation():
        print("\n❌ Project creation test failed.")
        return False
    
    print("\n🎉 All tests passed! The application is ready to use.")
    print("\nTo start the application, run:")
    print("  streamlit run app.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
