"""
Export utilities for Beat & Stems Lab
Handles all file exports including WAV, MIDI, and text files
"""
import os
import json
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Any
import soundfile as sf
import pretty_midi

from config import EXPORT_SAMPLE_RATE, EXPORT_FORMAT
from .io_utils import save_audio_file


def export_project_summary(
    project_config: Dict[str, Any],
    output_path: Path
) -> str:
    """
    Export project summary as text file
    
    Args:
        project_config: Project configuration dictionary
        output_path: Output file path
        
    Returns:
        Path to exported file
    """
    with open(output_path, 'w') as f:
        f.write("Beat & Stems Lab - Project Summary\n")
        f.write("=" * 40 + "\n\n")
        
        # Audio information
        if "audio" in project_config:
            audio_info = project_config["audio"]
            f.write("AUDIO FILE:\n")
            f.write(f"  Path: {audio_info.get('path', 'Unknown')}\n")
            f.write(f"  Sample Rate: {audio_info.get('sr', 'Unknown')} Hz\n")
            f.write(f"  Duration: {audio_info.get('duration', 0):.2f} seconds\n")
            f.write(f"  Checksum: {audio_info.get('checksum', 'Unknown')}\n\n")
        
        # Analysis results
        if "analysis" in project_config:
            analysis = project_config["analysis"]
            f.write("ANALYSIS RESULTS:\n")
            
            if "tempo" in analysis:
                f.write(f"  Tempo: {analysis['tempo']:.1f} BPM\n")
            
            if "beat_times" in analysis:
                f.write(f"  Total Beats: {len(analysis['beat_times'])}\n")
            
            if "downbeat_times" in analysis:
                f.write(f"  Downbeats: {len(analysis['downbeat_times'])}\n")
            
            if "time_signature" in analysis:
                ts = analysis["time_signature"]
                f.write(f"  Time Signature: {ts.get('numerator', 4)}/{ts.get('denominator', 4)}\n")
            
            f.write("\n")
        
        # Stems information
        if "stems" in project_config:
            stems = project_config["stems"]
            f.write("STEMS:\n")
            f.write(f"  Method: {stems.get('method', 'Unknown')}\n")
            if "paths" in stems:
                for stem_name, stem_path in stems["paths"].items():
                    f.write(f"  {stem_name.capitalize()}: {stem_path}\n")
            f.write("\n")
        
        # MIDI information
        if "midi" in project_config:
            midi = project_config["midi"]
            f.write("MIDI FILES:\n")
            for midi_type, midi_path in midi.items():
                f.write(f"  {midi_type.capitalize()}: {midi_path}\n")
            f.write("\n")
        
        # Project metadata
        f.write("PROJECT METADATA:\n")
        f.write(f"  Version: {project_config.get('version', 'Unknown')}\n")
        f.write(f"  Created: {project_config.get('created_at', 'Unknown')}\n")
        f.write(f"  Status: {project_config.get('status', 'Unknown')}\n")
    
    return str(output_path)


def export_analysis_report(
    analysis_results: Dict[str, Any],
    output_path: Path
) -> str:
    """
    Export detailed analysis report
    
    Args:
        analysis_results: Analysis results dictionary
        output_path: Output file path
        
    Returns:
        Path to exported file
    """
    with open(output_path, 'w') as f:
        f.write("Beat & Stems Lab - Analysis Report\n")
        f.write("=" * 35 + "\n\n")
        
        # Tempo and timing
        if "tempo" in analysis_results:
            f.write("TEMPO & TIMING:\n")
            f.write(f"  BPM: {analysis_results['tempo']:.1f}\n")
            f.write(f"  Total Beats: {len(analysis_results.get('beat_times', []))}\n")
            f.write(f"  Duration: {analysis_results.get('duration', 0):.2f} seconds\n")
            
            if "rhythm_complexity" in analysis_results:
                f.write(f"  Rhythm Complexity: {analysis_results['rhythm_complexity']:.3f}\n")
            
            if "syncopation" in analysis_results:
                f.write(f"  Syncopation: {analysis_results['syncopation']:.3f}\n")
            
            f.write("\n")
        
        # Melody analysis
        if "melody" in analysis_results:
            melody = analysis_results["melody"]
            f.write("MELODY ANALYSIS:\n")
            f.write(f"  Total Notes: {melody.get('total_notes', 0)}\n")
            f.write(f"  Average Duration: {melody.get('avg_duration', 0):.3f} seconds\n")
            f.write(f"  Average Confidence: {melody.get('avg_confidence', 0):.3f}\n")
            
            if "pitch_range" in melody:
                pitch_range = melody["pitch_range"]
                f.write(f"  Pitch Range: {pitch_range[0]}-{pitch_range[1]} (MIDI notes)\n")
            
            f.write("\n")
        
        # Chord analysis
        if "chords" in analysis_results:
            chords = analysis_results["chords"]
            f.write("CHORD ANALYSIS:\n")
            f.write(f"  Total Chords: {chords.get('total_chords', 0)}\n")
            f.write(f"  Unique Chords: {chords.get('unique_chords', 0)}\n")
            f.write(f"  Chord Changes: {chords.get('chord_changes', 0)}\n")
            f.write(f"  Complexity Score: {chords.get('complexity_score', 0):.3f}\n")
            
            if "common_progressions" in chords:
                f.write("  Common Progressions:\n")
                for prog in chords["common_progressions"][:5]:
                    f.write(f"    {prog['progression']}: {prog['count']} times\n")
            
            f.write("\n")
        
        # Drum analysis
        if "drums" in analysis_results:
            drums = analysis_results["drums"]
            f.write("DRUM ANALYSIS:\n")
            f.write(f"  Total Hits: {drums.get('total_hits', 0)}\n")
            f.write(f"  Hit Density: {drums.get('hit_density', 0):.2f} hits/second\n")
            f.write(f"  Pattern Complexity: {drums.get('pattern_complexity', 0):.3f}\n")
            
            if "drum_distribution" in drums:
                f.write("  Drum Distribution:\n")
                for drum_type, count in drums["drum_distribution"].items():
                    f.write(f"    {drum_type}: {count} hits\n")
            
            f.write("\n")
    
    return str(output_path)


def export_midi_collection(
    midi_files: Dict[str, str],
    output_path: Path
) -> str:
    """
    Export collection of MIDI files as a single ZIP archive
    
    Args:
        midi_files: Dictionary of {name: file_path}
        output_path: Output ZIP file path
        
    Returns:
        Path to exported ZIP file
    """
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for name, file_path in midi_files.items():
            if os.path.exists(file_path):
                # Add file to ZIP with descriptive name
                zipf.write(file_path, f"{name}.mid")
    
    return str(output_path)


def export_stems_collection(
    stem_files: Dict[str, str],
    output_path: Path
) -> str:
    """
    Export collection of stem files as a single ZIP archive
    
    Args:
        stem_files: Dictionary of {name: file_path}
        output_path: Output ZIP file path
        
    Returns:
        Path to exported ZIP file
    """
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for name, file_path in stem_files.items():
            if os.path.exists(file_path):
                # Add file to ZIP with descriptive name
                zipf.write(file_path, f"{name}.{EXPORT_FORMAT}")
    
    return str(output_path)


def export_daw_project(
    project_config: Dict[str, Any],
    output_path: Path,
    daw_type: str = "generic"
) -> str:
    """
    Export project in DAW-compatible format
    
    Args:
        project_config: Project configuration
        output_path: Output file path
        daw_type: Target DAW type ("generic", "ableton", "logic", "fl")
        
    Returns:
        Path to exported file
    """
    if daw_type == "generic":
        return export_generic_daw_project(project_config, output_path)
    elif daw_type == "ableton":
        return export_ableton_project(project_config, output_path)
    elif daw_type == "logic":
        return export_logic_project(project_config, output_path)
    elif daw_type == "fl":
        return export_fl_project(project_config, output_path)
    else:
        raise ValueError(f"Unsupported DAW type: {daw_type}")


def export_generic_daw_project(
    project_config: Dict[str, Any],
    output_path: Path
) -> str:
    """
    Export generic DAW project file
    
    Args:
        project_config: Project configuration
        output_path: Output file path
        
    Returns:
        Path to exported file
    """
    # Create a generic project file with all necessary information
    project_data = {
        "project_info": {
            "name": project_config.get("project_name", "Unknown"),
            "version": project_config.get("version", "1.0.0"),
            "created_at": project_config.get("created_at", ""),
            "tempo": project_config.get("analysis", {}).get("tempo", 120.0),
            "time_signature": project_config.get("analysis", {}).get("time_signature", {"numerator": 4, "denominator": 4})
        },
        "audio_files": project_config.get("audio", {}),
        "stems": project_config.get("stems", {}),
        "midi_files": project_config.get("midi", {}),
        "analysis": project_config.get("analysis", {}),
        "export_notes": [
            "Import stems into separate tracks",
            "Import MIDI files for melody and drums",
            "Set project tempo to match detected BPM",
            "Use chord progression for reference",
            "Adjust timing as needed for your DAW"
        ]
    }
    
    with open(output_path, 'w') as f:
        json.dump(project_data, f, indent=2)
    
    return str(output_path)


def export_ableton_project(
    project_config: Dict[str, Any],
    output_path: Path
) -> str:
    """
    Export Ableton Live project information
    
    Args:
        project_config: Project configuration
        output_path: Output file path
        
    Returns:
        Path to exported file
    """
    # Create Ableton-specific project file
    ableton_data = {
        "ableton_project": {
            "tempo": project_config.get("analysis", {}).get("tempo", 120.0),
            "time_signature": project_config.get("analysis", {}).get("time_signature", {"numerator": 4, "denominator": 4}),
            "tracks": {
                "stems": {
                    "type": "audio",
                    "files": project_config.get("stems", {}).get("paths", {})
                },
                "melody": {
                    "type": "midi",
                    "file": project_config.get("midi", {}).get("melody", "")
                },
                "drums": {
                    "type": "midi",
                    "file": project_config.get("midi", {}).get("drums_basic", "")
                }
            },
            "setup_instructions": [
                "1. Create new Ableton Live project",
                "2. Set project tempo to detected BPM",
                "3. Import stem files to separate audio tracks",
                "4. Import melody MIDI to a new MIDI track",
                "5. Import drum MIDI to a new MIDI track",
                "6. Set drum track to Drum Rack instrument",
                "7. Adjust timing and quantization as needed"
            ]
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(ableton_data, f, indent=2)
    
    return str(output_path)


def export_logic_project(
    project_config: Dict[str, Any],
    output_path: Path
) -> str:
    """
    Export Logic Pro project information
    
    Args:
        project_config: Project configuration
        output_path: Output file path
        
    Returns:
        Path to exported file
    """
    # Create Logic Pro-specific project file
    logic_data = {
        "logic_project": {
            "tempo": project_config.get("analysis", {}).get("tempo", 120.0),
            "time_signature": project_config.get("analysis", {}).get("time_signature", {"numerator": 4, "denominator": 4}),
            "tracks": {
                "stems": {
                    "type": "audio",
                    "files": project_config.get("stems", {}).get("paths", {})
                },
                "melody": {
                    "type": "midi",
                    "file": project_config.get("midi", {}).get("melody", "")
                },
                "drums": {
                    "type": "midi",
                    "file": project_config.get("midi", {}).get("drums_basic", "")
                }
            },
            "setup_instructions": [
                "1. Create new Logic Pro project",
                "2. Set project tempo to detected BPM",
                "3. Import stem files to separate audio tracks",
                "4. Import melody MIDI to a new software instrument track",
                "5. Import drum MIDI to a new drum machine track",
                "6. Set drum track to Drum Machine Designer",
                "7. Adjust timing and quantization as needed"
            ]
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(logic_data, f, indent=2)
    
    return str(output_path)


def export_fl_project(
    project_config: Dict[str, Any],
    output_path: Path
) -> str:
    """
    Export FL Studio project information
    
    Args:
        project_config: Project configuration
        output_path: Output file path
        
    Returns:
        Path to exported file
    """
    # Create FL Studio-specific project file
    fl_data = {
        "fl_studio_project": {
            "tempo": project_config.get("analysis", {}).get("tempo", 120.0),
            "time_signature": project_config.get("analysis", {}).get("time_signature", {"numerator": 4, "denominator": 4}),
            "tracks": {
                "stems": {
                    "type": "audio",
                    "files": project_config.get("stems", {}).get("paths", {})
                },
                "melody": {
                    "type": "midi",
                    "file": project_config.get("midi", {}).get("melody", "")
                },
                "drums": {
                    "type": "midi",
                    "file": project_config.get("midi", {}).get("drums_basic", "")
                }
            },
            "setup_instructions": [
                "1. Create new FL Studio project",
                "2. Set project tempo to detected BPM",
                "3. Import stem files to separate mixer tracks",
                "4. Import melody MIDI to a new channel",
                "5. Import drum MIDI to FPC or Drum Machine",
                "6. Set drum channel to appropriate drum plugin",
                "7. Adjust timing and quantization as needed"
            ]
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(fl_data, f, indent=2)
    
    return str(output_path)


def create_export_package(
    project_config: Dict[str, Any],
    output_dir: Path,
    include_stems: bool = True,
    include_midi: bool = True,
    include_analysis: bool = True
) -> str:
    """
    Create complete export package with all files
    
    Args:
        project_config: Project configuration
        output_dir: Output directory
        include_stems: Whether to include stem files
        include_midi: Whether to include MIDI files
        include_analysis: Whether to include analysis files
        
    Returns:
        Path to export package ZIP file
    """
    package_path = output_dir / f"{project_config.get('project_name', 'project')}_export.zip"
    
    with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add project summary
        summary_path = output_dir / "project_summary.txt"
        export_project_summary(project_config, summary_path)
        zipf.write(summary_path, "project_summary.txt")
        
        # Add stems if requested
        if include_stems and "stems" in project_config:
            stems = project_config["stems"]
            if "paths" in stems:
                for stem_name, stem_path in stems["paths"].items():
                    if os.path.exists(stem_path):
                        zipf.write(stem_path, f"stems/{stem_name}.{EXPORT_FORMAT}")
        
        # Add MIDI files if requested
        if include_midi and "midi" in project_config:
            midi = project_config["midi"]
            for midi_type, midi_path in midi.items():
                if os.path.exists(midi_path):
                    zipf.write(midi_path, f"midi/{midi_type}.mid")
        
        # Add analysis files if requested
        if include_analysis and "analysis" in project_config:
            analysis = project_config["analysis"]
            for analysis_type, analysis_path in analysis.items():
                if os.path.exists(analysis_path):
                    zipf.write(analysis_path, f"analysis/{analysis_type}.json")
        
        # Add DAW project files
        daw_path = output_dir / "daw_project.json"
        export_generic_daw_project(project_config, daw_path)
        zipf.write(daw_path, "daw_project.json")
    
    return str(package_path)
