
import os
import sys
from pathlib import Path
import numpy as np
import json
import torch

# Add src to path
sys.path.append(os.getcwd())

from src.io_utils import (
    ProjectManager, load_audio_file, create_project_from_audio,
    save_analysis_results, get_stem_path, get_midi_path, save_audio_file,
    load_analysis_results,
)
from src.app_helpers import merge_beat_summary
# Import separation - validation is handled inside
from src.separation import StemSeparator, DEMUCS_AVAILABLE

from src.timing import create_beat_grid
from src.drums import extract_drums_to_midi
from src.chords import analyze_chord_progression, detect_key_from_chroma
from src.strudel_integration import generate_strudel_from_analysis
from src.app_helpers import build_analysis_data_for_strudel, safe_extract_melody


def main():
    # Configuration
    INPUT_FILE = Path("nice2knowya.wav")
    PROJECT_NAME = "Nice_2_Know_Ya_Full"
    
    # Use Demucs (PyTorch) instead of Spleeter
    SEPARATION_METHOD = "demucs:4stems" 
    
    print(f"🚀 Starting Ultimate M4 Pipeline for: {INPUT_FILE}")
    print(f"🖥️  Platform: Apple Silicon (Metal/MPS enabled: {torch.backends.mps.is_available()})")
    
    if not INPUT_FILE.exists():
        print(f"❌ Error: File {INPUT_FILE} not found! Please run the ffmpeg conversion command first.")
        return

    # 1. Create Project
    print("\n📁 Creating Project...")
    try:
        project = create_project_from_audio(INPUT_FILE, PROJECT_NAME)
        print(f"✅ Project created at: {project.project_path}")
    except Exception as e:
        print(f"❌ Error creating project: {e}")
        return

    # Load Audio
    print("🎵 Loading audio...")
    audio_data, audio_sr = load_audio_file(INPUT_FILE)
    config = project.load_project_config()

    # 2. Analyze Tempo & Beats
    print("\n🎼 Analyzing Tempo & Beats...")
    beat_analysis = create_beat_grid(audio_data, audio_sr)
    save_analysis_results(project, "tempo_beats", beat_analysis)
    merge_beat_summary(config, beat_analysis)
    project.save_project_config(config)
    print(f"✅ Tempo: {beat_analysis['tempo']:.1f} BPM")

    # 3. Separate Stems (Demucs)
    print(f"\n🎛️ Separating Stems ({SEPARATION_METHOD})...")
    stems = {}
    
    if not DEMUCS_AVAILABLE:
        print("⚠️  Demucs not detected. Please install it with 'pip install demucs'. Skipping separation.")
    else:
        try:
            # Explicitly using CPU or MPS if supported by Demucs wrapper
            # The src/separation.py wrapper handles loading.
            separator = StemSeparator(SEPARATION_METHOD)
            
            print("    Running Demucs separation (this may take a moment)...")
            stems = separator.separate_audio(audio_data, audio_sr)
            
            stem_paths = {}
            for stem_name, stem_audio in stems.items():
                stem_path = get_stem_path(project, stem_name)
                save_audio_file(stem_audio, stem_path, audio_sr)
                stem_paths[stem_name] = str(stem_path)
                print(f"    - Saved {stem_name}")
                
            config["stems"] = {
                "method": SEPARATION_METHOD,
                "paths": stem_paths
            }
            project.save_project_config(config)
            print("✅ Stem separation complete")
        except Exception as e:
            print(f"❌ Error separating stems: {e}")
            stems = {} # fallback

    # 4. Extract Musical Information
    
    # Drums (from 'drums' stem if available, else full mix)
    print("\n🥁 Analyzing Drums...")
    drum_audio = stems.get("drums", audio_data)
    drum_midi_path = get_midi_path(project, "drums_basic")
    try:
        drum_results = extract_drums_to_midi(
            drum_audio, 
            audio_sr, 
            str(drum_midi_path),
            confidence_threshold=0.4
        )
        save_analysis_results(project, "drums", drum_results)
        if "midi" not in config: config["midi"] = {}
        config["midi"]["drums_basic"] = str(drum_midi_path)
        print(f"✅ Drums extracted: {drum_results['summary']['total_hits']} hits")
    except Exception as e:
        print(f"❌ Error analyzing drums: {e}")

    # Melody (Using Librosa pYIN to avoid TF crashes)
    print("\n🎹 Analyzing Melody...")
    melody_audio = stems.get("other", stems.get("vocals", audio_data)) 
    melody_midi_path = get_midi_path(project, "melody")
    try:
        beat_times = beat_analysis.get("beat_times", [])
        
        # Use our safe extractor
        melody_results = safe_extract_melody(
            melody_audio,
            audio_sr,
            str(melody_midi_path),
            beat_times=beat_times
        )
        
        save_analysis_results(project, "melody", melody_results)
        config["midi"]["melody"] = str(melody_midi_path)
        print(f"✅ Melody extracted: {melody_results['statistics']['total_notes']} notes")
    except Exception as e:
        print(f"❌ Error analyzing melody: {e}")
        import traceback
        traceback.print_exc()

    # Bass (from 'bass' stem if available)
    print("\n🎸 Analyzing Bass...")
    bass_audio = stems.get("bass", audio_data)
    bass_midi_path = get_midi_path(project, "bass")
    try:
        beat_times = beat_analysis.get("beat_times", [])
        
        # Extract bass using same method as melody but focus on lower frequencies
        bass_results = safe_extract_melody(
            bass_audio,
            audio_sr,
            str(bass_midi_path),
            beat_times=beat_times
        )
        
        save_analysis_results(project, "bass", bass_results)
        config["midi"]["bass"] = str(bass_midi_path)
        print(f"✅ Bass extracted: {bass_results['statistics']['total_notes']} notes")
    except Exception as e:
        print(f"❌ Error analyzing bass: {e}")
        import traceback
        traceback.print_exc()
        bass_results = None

    # Chords
    print("\n🎼 Analyzing Chords...")
    # Mix other and bass for best chord detection if available
    if "other" in stems and "bass" in stems:
        chord_audio = stems["other"] + stems["bass"]
    else:
        chord_audio = audio_data
        
    try:
        chord_results = analyze_chord_progression(chord_audio, audio_sr)
        
        # Key detection
        chroma = chord_results["chroma_features"]
        key, key_conf = detect_key_from_chroma(np.array(chroma))
        chord_results["key"] = key
        chord_results["key_confidence"] = key_conf
        
        save_analysis_results(project, "chords", chord_results)
        config["analysis"]["key_guess"] = key
        print(f"✅ Key detected: {key} (Confidence: {key_conf:.2f})")
    except Exception as e:
        print(f"❌ Error analyzing chords: {e}")

    # Save final config
    project.save_project_config(config)

    # 5. Generate Strudel Patterns
    print("\n📝 Generating Strudel Patterns...")
    try:
        analysis_data = build_analysis_data_for_strudel(
            project,
            {
                "tempo_beats": beat_analysis,
                "drums": load_analysis_results(project, "drums") or {},
                "melody": load_analysis_results(project, "melody") or {},
                "bass": load_analysis_results(project, "bass") or {},
                "chords": load_analysis_results(project, "chords") or {},
            },
        )
        
        strudel_files = generate_strudel_from_analysis(
            analysis_data, 
            str(project.project_path / "strudel")
        )
        
        print("✅ Strudel generation complete!")
        print(f"Files saved to: {project.project_path / 'strudel'}")
        
        # Read and print the complete pattern
        if 'arrangement' in strudel_files:
            print("\n--- Generated Strudel Arrangement ---\n")
            with open(strudel_files['arrangement'], 'r') as f:
                print(f.read())
            print("\n------------------------------")
            
    except Exception as e:
        print(f"❌ Error generating Strudel: {e}")

if __name__ == "__main__":
    main()

