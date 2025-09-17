#!/usr/bin/env python3
"""
Quick test script to generate Strudel patterns from Day 'N' Nite
"""
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_strudel_generation():
    """Test Strudel pattern generation from Day 'N' Nite"""
    
    print("🎵 Testing Strudel Pattern Generation from Day 'N' Nite")
    print("=" * 60)
    
    # Audio file path
    audio_file = "Kid Cudi - Day 'N' Nite (SUBSHIFT Edit) [2120099592].m4a"
    
    if not Path(audio_file).exists():
        print(f"❌ Audio file not found: {audio_file}")
        return
    
    print(f"📁 Analyzing: {audio_file}")
    
    try:
        # Import our modules
        from src.io_utils import ProjectManager
        from src.timing import analyze_tempo_and_beats
        from src.drums import extract_drums_to_midi
        from src.chords import analyze_chord_progression
        from src.strudel_integration import generate_strudel_from_analysis
        from config import SAMPLE_RATE
        
        # Create project
        project_name = "Day_N_Nite_Test"
        project = ProjectManager(project_name)
        print(f"✅ Created project: {project_name}")
        
        # Load audio
        print("🔄 Loading audio file...")
        import librosa
        audio, sr = librosa.load(audio_file, sr=SAMPLE_RATE, mono=True)
        duration = len(audio) / sr
        print(f"✅ Loaded audio: {duration:.1f} seconds, {sr} Hz")
        
        # Quick tempo analysis
        print("\n🎯 Analyzing tempo...")
        beat_analysis = analyze_tempo_and_beats(audio, sr)
        tempo = beat_analysis.get('bpm', 120)
        print(f"✅ Detected tempo: {tempo:.1f} BPM")
        
        # Quick drum analysis
        print("\n🥁 Analyzing drums...")
        try:
            drum_results = extract_drums_to_midi(audio, sr, "temp_drums.mid", tempo=tempo)
            print(f"✅ Found {len(drum_results.get('drum_hits', []))} drum hits")
        except Exception as e:
            print(f"⚠️ Drum analysis failed: {e}")
            drum_results = {}
        
        # Quick chord analysis
        print("\n🎼 Analyzing chords...")
        try:
            chord_results = analyze_chord_progression(audio, sr)
            print(f"✅ Found {len(chord_results.get('chords', []))} chord changes")
        except Exception as e:
            print(f"⚠️ Chord analysis failed: {e}")
            chord_results = {}
        
        # Prepare analysis data
        analysis_data = {
            'tempo': tempo,
            'drums': drum_results,
            'melody': {},  # Skip melody for quick test
            'chords': chord_results
        }
        
        # Generate Strudel patterns
        print("\n🎵 Generating Strudel patterns...")
        strudel_files = generate_strudel_from_analysis(
            analysis_data, 
            str(project.project_path / "strudel")
        )
        
        print("✅ Strudel patterns generated!")
        print("\n📁 Generated files:")
        for file_type, file_path in strudel_files.items():
            print(f"  - {file_type}: {file_path}")
        
        # Show the complete pattern
        print("\n🎵 Complete Strudel Pattern:")
        print("-" * 40)
        with open(strudel_files['complete'], 'r') as f:
            complete_code = f.read()
        print(complete_code)
        
        # Show suggested template
        print("\n🎯 Suggested Template:")
        print("-" * 40)
        with open(strudel_files['template'], 'r') as f:
            template_code = f.read()
        print(template_code)
        
        print(f"\n🌐 HTML Player: {strudel_files['html']}")
        print("Open this file in your browser to play the patterns!")
        
        # Also show some style templates
        print("\n🎨 Available Style Templates:")
        from src.strudel_templates import get_strudel_templates
        templates = get_strudel_templates()
        
        # Show hip-hop templates (appropriate for Day 'N' Nite)
        print("\n🎤 Hip-Hop Templates:")
        hip_hop_templates = templates.get_style_templates("hip_hop")
        for pattern_name, pattern_code in hip_hop_templates.items():
            print(f"\n{pattern_name.upper()}:")
            print(pattern_code)
            break  # Just show one for brevity
        
        print(f"\n✅ Test complete! Check the generated files in: {project.project_path / 'strudel'}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_strudel_generation()
