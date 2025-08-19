#!/usr/bin/env python3
"""
Simplified audio analysis script for Beat & Stems Lab
Focuses on working features: tempo, stems, drums, chords
"""
import sys
import os
from pathlib import Path
import time

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def analyze_large_track(audio_file_path: str):
    """Analyze a large audio track using command-line tools"""
    
    print("🎵 Beat & Stems Lab - Large File Analysis")
    print("=" * 50)
    
    # Check if file exists
    if not os.path.exists(audio_file_path):
        print(f"❌ Error: File not found: {audio_file_path}")
        return
    
    print(f"📁 Analyzing: {audio_file_path}")
    
    try:
        # Import our modules
        from src.io_utils import ProjectManager
        from src.timing import analyze_tempo_and_beats
        from src.separation import separate_audio_file
        from src.drums import extract_drums_to_midi
        from src.chords import analyze_chord_progression
        from config import SAMPLE_RATE
        
        # Create project
        project_name = Path(audio_file_path).stem
        project = ProjectManager(project_name)
        print(f"✅ Created project: {project_name}")
        
        # Load audio
        print("🔄 Loading audio file...")
        import librosa
        audio, sr = librosa.load(audio_file_path, sr=SAMPLE_RATE, mono=True)
        duration = len(audio) / sr
        print(f"✅ Loaded audio: {duration:.1f} seconds, {sr} Hz")
        
        # Initialize config
        config = {
            "project_name": project_name,
            "audio_file": audio_file_path,
            "duration": duration,
            "sample_rate": sr,
            "analysis": {},
            "stems": {},
            "midi": {}
        }
        
        # Step 1: Tempo Analysis
        print("\n🎯 Step 1: Analyzing tempo and beats...")
        beat_analysis = analyze_tempo_and_beats(audio, sr)
        config["analysis"]["tempo"] = beat_analysis["bpm"]
        config["analysis"]["beat_times"] = beat_analysis["beat_times"]
        config["analysis"]["total_beats"] = beat_analysis["total_beats"]
        print(f"✅ Tempo: {beat_analysis['bpm']:.1f} BPM")
        print(f"✅ Total beats: {beat_analysis['total_beats']}")
        
        # Step 2: Stem Separation
        print("\n🎛️ Step 2: Separating stems...")
        print("This will take several minutes for a 10-minute track...")
        
        stems_dir = project.project_path / "stems"
        stems_dir.mkdir(exist_ok=True)
        
        # Use Demucs for separation
        from src.separation import StemSeparator
        separator = StemSeparator("demucs:4stems")
        stems = separator.separate_audio(audio, sr)
        
        stem_paths = {}
        for stem_name, stem_audio in stems.items():
            stem_path = project.project_path / "stems" / f"{stem_name}.wav"
            stem_path.parent.mkdir(exist_ok=True)
            
            from src.io_utils import save_audio_file
            save_audio_file(stem_audio, stem_path, sr)
            stem_paths[stem_name] = str(stem_path)
            print(f"✅ Saved {stem_name}: {stem_path}")
        
        config["stems"] = {
            "method": "demucs:4stems",
            "paths": stem_paths
        }
        
        # Step 3: Drum Analysis (skip melody for now)
        print("\n🥁 Step 3: Analyzing drums...")
        try:
            midi_dir = project.project_path / "midi"
            midi_dir.mkdir(exist_ok=True)
            
            drum_path = midi_dir / "drums_basic.mid"
            drum_results = extract_drums_to_midi(
                audio, sr, str(drum_path),
                tempo=beat_analysis["bpm"],
                confidence_threshold=0.5
            )
            
            config["midi"]["drums_basic"] = str(drum_path)
            print(f"✅ Extracted drums: {drum_results['total_hits']} hits")
            
        except Exception as e:
            print(f"⚠️ Drum extraction failed: {e}")
        
        # Step 4: Chord Analysis
        print("\n🎼 Step 4: Analyzing chords...")
        try:
            chord_results = analyze_chord_progression(audio, sr)
            config["analysis"]["chords"] = chord_results
            print(f"✅ Chord analysis: {chord_results['total_chords']} chords detected")
            
        except Exception as e:
            print(f"⚠️ Chord analysis failed: {e}")
        
        # Save project config
        project.save_project_config(config)
        print(f"\n✅ Project saved to: {project.project_path}")
        
        # Generate summary
        print("\n📋 Project Summary:")
        print(f"  Project: {project_name}")
        print(f"  Duration: {duration:.1f} seconds")
        print(f"  Tempo: {beat_analysis['bpm']:.1f} BPM")
        print(f"  Stems: {list(stems.keys())}")
        print(f"  Project folder: {project.project_path}")
        
        print("\n🎉 Analysis complete! You can now:")
        print("  1. Use the stems for remixing")
        print("  2. Import drum MIDI into your DAW")
        print("  3. View the chord analysis")
        print("  4. Open the project in the web app for visualization")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("Usage: python analyze_track_simple.py <audio_file>")
        print("Example: python analyze_track_simple.py 'Nightcrawler (Dom3x Remix) Edit.mp3'")
        return
    
    audio_file = sys.argv[1]
    analyze_large_track(audio_file)

if __name__ == "__main__":
    main()
