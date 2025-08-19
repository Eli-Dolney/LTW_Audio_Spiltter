"""
Beat & Stems Lab - Main Application
A local-only audio analysis and stem separation tool
"""
import streamlit as st
import os
import tempfile
from pathlib import Path
import numpy as np
import time
from typing import Dict, Any, Optional

# Import our modules
from config import (
    APP_TITLE, APP_VERSION, PROJECTS_DIR, SUPPORTED_FORMATS,
    STEM_METHOD_DEFAULT, STEM_METHODS
)
from src.io_utils import (
    ProjectManager, load_audio_file, is_supported_format,
    create_project_from_audio, list_projects, save_analysis_results,
    load_analysis_results, get_stem_path, get_midi_path
)
from src.viz import (
    create_waveform_plot, create_spectrogram_plot,
    create_waveform_with_beats, create_multi_stem_comparison
)
from src.separation import (
    StemSeparator, get_available_methods, estimate_separation_time,
    validate_separation_method
)
from src.timing import create_beat_grid, validate_tempo_estimation
from src.melody import extract_melody_to_midi, analyze_melody_characteristics
from src.chords import analyze_chord_progression, detect_key_from_chroma
from src.drums import extract_drums_to_midi, analyze_drum_pattern
from src.export import (
    export_project_summary, export_analysis_report,
    create_export_package, export_daw_project
)


# Page configuration
st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .status-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables"""
    if 'current_project' not in st.session_state:
        st.session_state.current_project = None
    if 'audio_data' not in st.session_state:
        st.session_state.audio_data = None
    if 'audio_sr' not in st.session_state:
        st.session_state.audio_sr = None
    if 'project_config' not in st.session_state:
        st.session_state.project_config = None
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = {}
    if 'stems_data' not in st.session_state:
        st.session_state.stems_data = {}


def main_header():
    """Display main header"""
    st.markdown('<h1 class="main-header">🎵 Beat & Stems Lab</h1>', unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #666;'>Version {APP_VERSION} - Local Audio Analysis & Stem Separation</p>", unsafe_allow_html=True)


def sidebar_controls():
    """Sidebar controls for file upload and project management"""
    st.sidebar.header("📁 Project Management")
    
    # File upload
    uploaded_file = st.sidebar.file_uploader(
        "Upload Audio File",
        type=['mp3', 'wav', 'flac', 'm4a', 'aac'],
        help="Upload an audio file to analyze"
    )
    
    if uploaded_file is not None:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = Path(tmp_file.name)
        
        # Validate file
        if is_supported_format(tmp_path):
            st.sidebar.success(f"✅ File uploaded: {uploaded_file.name}")
            
            # Project name input
            project_name = st.sidebar.text_input(
                "Project Name",
                value=uploaded_file.name.split('.')[0],
                help="Enter a name for this project"
            )
            
            if st.sidebar.button("🚀 Create Project", type="primary"):
                try:
                    # Create project
                    project = create_project_from_audio(tmp_path, project_name)
                    st.session_state.current_project = project
                    
                    # Load audio
                    audio, sr = load_audio_file(tmp_path)
                    st.session_state.audio_data = audio
                    st.session_state.audio_sr = sr
                    st.session_state.project_config = project.load_project_config()
                    
                    st.sidebar.success("✅ Project created successfully!")
                    st.rerun()
                    
                except Exception as e:
                    st.sidebar.error(f"❌ Error creating project: {str(e)}")
        else:
            st.sidebar.error("❌ Unsupported file format")
    
    # Load existing project
    st.sidebar.header("📂 Load Existing Project")
    projects = list_projects()
    
    if projects:
        project_names = [p["name"] for p in projects]
        selected_project = st.sidebar.selectbox(
            "Select Project",
            project_names,
            help="Load an existing project"
        )
        
        if st.sidebar.button("📂 Load Project"):
            try:
                project = ProjectManager(selected_project)
                st.session_state.current_project = project
                st.session_state.project_config = project.load_project_config()
                
                # Load audio if available
                if st.session_state.project_config and "audio" in st.session_state.project_config:
                    audio_path = Path(st.session_state.project_config["audio"]["path"])
                    if audio_path.exists():
                        audio, sr = load_audio_file(audio_path)
                        st.session_state.audio_data = audio
                        st.session_state.audio_sr = sr
                
                st.sidebar.success("✅ Project loaded successfully!")
                st.rerun()
                
            except Exception as e:
                st.sidebar.error(f"❌ Error loading project: {str(e)}")
    else:
        st.sidebar.info("No existing projects found")
    
    # Project info
    if st.session_state.current_project:
        st.sidebar.header("📋 Current Project")
        st.sidebar.write(f"**Name:** {st.session_state.current_project.project_name}")
        
        if st.session_state.project_config:
            if "audio" in st.session_state.project_config:
                audio_info = st.session_state.project_config["audio"]
                st.sidebar.write(f"**Duration:** {audio_info.get('duration', 0):.1f}s")
                st.sidebar.write(f"**Sample Rate:** {audio_info.get('sr', 0)} Hz")
            
            if "analysis" in st.session_state.project_config:
                analysis = st.session_state.project_config["analysis"]
                if "tempo" in analysis:
                    st.sidebar.write(f"**Tempo:** {analysis['tempo']:.1f} BPM")


def stem_separation_section():
    """Stem separation section"""
    st.header("🎛️ Stem Separation")
    
    if not st.session_state.audio_data is not None:
        st.warning("⚠️ Please load an audio file first")
        return
    
    # Separation method selection
    available_methods = get_available_methods()
    selected_method = st.selectbox(
        "Separation Method",
        list(available_methods.keys()),
        format_func=lambda x: f"{x} - {available_methods[x]}",
        help="Choose the stem separation method"
    )
    
    # Method info
    if selected_method:
        method_info = available_methods[selected_method]
        st.info(f"**Method:** {selected_method}\n\n**Description:** {method_info}")
        
        # Estimate processing time
        if st.session_state.audio_data is not None:
            duration = len(st.session_state.audio_data) / st.session_state.audio_sr
            est_time = estimate_separation_time(duration, selected_method)
            st.info(f"**Estimated processing time:** {est_time:.1f} seconds")
    
    # Separation button
    if st.button("🎚️ Separate Stems", type="primary"):
        if st.session_state.audio_data is not None and st.session_state.current_project:
            with st.spinner("Separating stems..."):
                try:
                    # Create separator
                    separator = StemSeparator(selected_method)
                    
                    # Perform separation
                    stems = separator.separate_audio(st.session_state.audio_data, st.session_state.audio_sr)
                    
                    # Save stems
                    stem_paths = {}
                    for stem_name, stem_audio in stems.items():
                        stem_path = get_stem_path(st.session_state.current_project, stem_name)
                        from src.io_utils import save_audio_file
                        save_audio_file(stem_audio, stem_path, st.session_state.audio_sr)
                        stem_paths[stem_name] = str(stem_path)
                    
                    # Update project config
                    config = st.session_state.project_config
                    config["stems"] = {
                        "method": selected_method,
                        "paths": stem_paths
                    }
                    st.session_state.current_project.save_project_config(config)
                    st.session_state.project_config = config
                    st.session_state.stems_data = stems
                    
                    st.success("✅ Stem separation completed!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error during stem separation: {str(e)}")
    
    # Display stems if available
    if st.session_state.stems_data:
        st.subheader("🎵 Separated Stems")
        
        # Stem comparison plot
        fig = create_multi_stem_comparison(st.session_state.stems_data, st.session_state.audio_sr)
        st.plotly_chart(fig, use_container_width=True)
        
        # Stem download buttons
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📥 Download Stems")
            for stem_name, stem_audio in st.session_state.stems_data.items():
                if st.button(f"Download {stem_name.capitalize()}"):
                    # Create download link
                    stem_path = get_stem_path(st.session_state.current_project, stem_name)
                    if stem_path.exists():
                        with open(stem_path, "rb") as f:
                            st.download_button(
                                label=f"Download {stem_name}.wav",
                                data=f.read(),
                                file_name=f"{stem_name}.wav",
                                mime="audio/wav"
                            )


def analysis_section():
    """Audio analysis section"""
    st.header("📊 Audio Analysis")
    
    if st.session_state.audio_data is None:
        st.warning("⚠️ Please load an audio file first")
        return
    
    # Analysis tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🎵 Waveform", "🎼 Tempo & Beats", "🎹 Melody", "🥁 Drums"])
    
    with tab1:
        st.subheader("Waveform & Spectrogram")
        
        # Waveform
        fig_wave = create_waveform_plot(st.session_state.audio_data, st.session_state.audio_sr)
        st.plotly_chart(fig_wave, use_container_width=True)
        
        # Spectrogram
        with st.expander("📈 Spectrogram"):
            fig_spec = create_spectrogram_plot(st.session_state.audio_data, st.session_state.audio_sr)
            st.plotly_chart(fig_spec, use_container_width=True)
    
    with tab2:
        st.subheader("Tempo & Beat Analysis")
        
        if st.button("🎯 Analyze Tempo & Beats", type="primary"):
            with st.spinner("Analyzing tempo and beats..."):
                try:
                    # Perform analysis
                    beat_analysis = create_beat_grid(st.session_state.audio_data, st.session_state.audio_sr)
                    
                    # Save results
                    save_analysis_results(st.session_state.current_project, "tempo_beats", beat_analysis)
                    st.session_state.analysis_results["tempo_beats"] = beat_analysis
                    
                    # Update project config
                    config = st.session_state.project_config
                    if "analysis" not in config:
                        config["analysis"] = {}
                    config["analysis"].update(beat_analysis)
                    st.session_state.current_project.save_project_config(config)
                    st.session_state.project_config = config
                    
                    st.success("✅ Tempo and beat analysis completed!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error during analysis: {str(e)}")
        
        # Display results
        if "tempo_beats" in st.session_state.analysis_results:
            results = st.session_state.analysis_results["tempo_beats"]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Tempo", f"{results['tempo']:.1f} BPM")
            with col2:
                st.metric("Total Beats", results['total_beats'])
            with col3:
                st.metric("Duration", f"{results['duration']:.1f}s")
            
            # Waveform with beats
            fig_beats = create_waveform_with_beats(
                st.session_state.audio_data,
                st.session_state.audio_sr,
                results.get('beat_times', [])
            )
            st.plotly_chart(fig_beats, use_container_width=True)
    
    with tab3:
        st.subheader("Melody Extraction")
        
        # Melody extraction options
        col1, col2 = st.columns(2)
        with col1:
            confidence_threshold = st.slider(
                "Confidence Threshold",
                min_value=0.1,
                max_value=0.9,
                value=0.5,
                step=0.1,
                help="Minimum confidence for note detection"
            )
        with col2:
            quantize = st.checkbox(
                "Quantize to Beat Grid",
                value=True,
                help="Quantize notes to nearest beat"
            )
        
        if st.button("🎹 Extract Melody", type="primary"):
            with st.spinner("Extracting melody..."):
                try:
                    # Get beat times if available
                    beat_times = None
                    if "tempo_beats" in st.session_state.analysis_results:
                        beat_times = st.session_state.analysis_results["tempo_beats"].get("beat_times", [])
                    
                    # Extract melody
                    midi_path = get_midi_path(st.session_state.current_project, "melody")
                    melody_results = extract_melody_to_midi(
                        st.session_state.audio_data,
                        st.session_state.audio_sr,
                        str(midi_path),
                        quantize=quantize,
                        beat_times=beat_times,
                        confidence_threshold=confidence_threshold
                    )
                    
                    # Save results
                    save_analysis_results(st.session_state.current_project, "melody", melody_results)
                    st.session_state.analysis_results["melody"] = melody_results
                    
                    # Update project config
                    config = st.session_state.project_config
                    if "midi" not in config:
                        config["midi"] = {}
                    config["midi"]["melody"] = str(midi_path)
                    st.session_state.current_project.save_project_config(config)
                    st.session_state.project_config = config
                    
                    st.success("✅ Melody extraction completed!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error during melody extraction: {str(e)}")
        
        # Display results
        if "melody" in st.session_state.analysis_results:
            results = st.session_state.analysis_results["melody"]
            stats = results["statistics"]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Notes", stats["total_notes"])
            with col2:
                st.metric("Avg Duration", f"{stats['avg_duration']:.3f}s")
            with col3:
                st.metric("Avg Confidence", f"{stats['avg_confidence']:.3f}")
    
    with tab4:
        st.subheader("Drum Analysis")
        
        confidence_threshold = st.slider(
            "Onset Detection Threshold",
            min_value=0.1,
            max_value=0.9,
            value=0.5,
            step=0.1,
            help="Minimum confidence for drum onset detection"
        )
        
        if st.button("🥁 Extract Drums", type="primary"):
            with st.spinner("Extracting drums..."):
                try:
                    # Extract drums
                    midi_path = get_midi_path(st.session_state.current_project, "drums_basic")
                    drum_results = extract_drums_to_midi(
                        st.session_state.audio_data,
                        st.session_state.audio_sr,
                        str(midi_path),
                        confidence_threshold=confidence_threshold
                    )
                    
                    # Save results
                    save_analysis_results(st.session_state.current_project, "drums", drum_results)
                    st.session_state.analysis_results["drums"] = drum_results
                    
                    # Update project config
                    config = st.session_state.project_config
                    if "midi" not in config:
                        config["midi"] = {}
                    config["midi"]["drums_basic"] = str(midi_path)
                    st.session_state.current_project.save_project_config(config)
                    st.session_state.project_config = config
                    
                    st.success("✅ Drum extraction completed!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error during drum extraction: {str(e)}")
        
        # Display results
        if "drums" in st.session_state.analysis_results:
            results = st.session_state.analysis_results["drums"]
            summary = results["summary"]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Hits", summary["total_hits"])
            with col2:
                st.metric("Most Common", summary["most_common_drum"])
            with col3:
                st.metric("Unique Drums", summary["unique_drums"])


def chord_analysis_section():
    """Chord analysis section"""
    st.header("🎼 Chord Analysis")
    
    if st.session_state.audio_data is None:
        st.warning("⚠️ Please load an audio file first")
        return
    
    if st.button("🎼 Analyze Chords", type="primary"):
        with st.spinner("Analyzing chord progression..."):
            try:
                # Analyze chords
                chord_results = analyze_chord_progression(st.session_state.audio_data, st.session_state.audio_sr)
                
                # Detect key
                chroma, _ = chord_results["chroma_features"], chord_results["chroma_times"]
                key, key_confidence = detect_key_from_chroma(np.array(chroma))
                chord_results["key"] = key
                chord_results["key_confidence"] = key_confidence
                
                # Save results
                save_analysis_results(st.session_state.current_project, "chords", chord_results)
                st.session_state.analysis_results["chords"] = chord_results
                
                # Update project config
                config = st.session_state.project_config
                if "analysis" not in config:
                    config["analysis"] = {}
                config["analysis"]["key_guess"] = key
                st.session_state.current_project.save_project_config(config)
                st.session_state.project_config = config
                
                st.success("✅ Chord analysis completed!")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error during chord analysis: {str(e)}")
    
    # Display results
    if "chords" in st.session_state.analysis_results:
        results = st.session_state.analysis_results["chords"]
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Chords", results["total_chords"])
        with col2:
            st.metric("Key", results.get("key", "Unknown"))
        with col3:
            st.metric("Key Confidence", f"{results.get('key_confidence', 0):.3f}")
        
        # Chord progression
        st.subheader("Chord Progression")
        if results["chord_labels"]:
            chord_text = " → ".join(results["chord_labels"])
            st.write(f"**Progression:** {chord_text}")
            
            # Chord times
            chord_data = list(zip(results["chord_times"], results["chord_labels"]))
            for i, (time, chord) in enumerate(chord_data):
                st.write(f"{i+1:2d}. {time:6.2f}s - {chord}")


def export_section():
    """Export section"""
    st.header("📤 Export")
    
    if not st.session_state.current_project:
        st.warning("⚠️ Please load a project first")
        return
    
    # Export options
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📄 Export Reports")
        
        if st.button("📋 Project Summary"):
            summary_path = st.session_state.current_project.project_path / "project_summary.txt"
            export_project_summary(st.session_state.project_config, summary_path)
            
            with open(summary_path, "r") as f:
                st.download_button(
                    label="Download Project Summary",
                    data=f.read(),
                    file_name="project_summary.txt",
                    mime="text/plain"
                )
        
        if st.button("📊 Analysis Report"):
            report_path = st.session_state.current_project.project_path / "analysis_report.txt"
            export_analysis_report(st.session_state.analysis_results, report_path)
            
            with open(report_path, "r") as f:
                st.download_button(
                    label="Download Analysis Report",
                    data=f.read(),
                    file_name="analysis_report.txt",
                    mime="text/plain"
                )
    
    with col2:
        st.subheader("🎵 Export MIDI")
        
        if "melody" in st.session_state.analysis_results:
            midi_path = get_midi_path(st.session_state.current_project, "melody")
            if midi_path.exists():
                with open(midi_path, "rb") as f:
                    st.download_button(
                        label="Download Melody MIDI",
                        data=f.read(),
                        file_name="melody.mid",
                        mime="audio/midi"
                    )
        
        if "drums" in st.session_state.analysis_results:
            drum_path = get_midi_path(st.session_state.current_project, "drums_basic")
            if drum_path.exists():
                with open(drum_path, "rb") as f:
                    st.download_button(
                        label="Download Drums MIDI",
                        data=f.read(),
                        file_name="drums_basic.mid",
                        mime="audio/midi"
                    )
    
    # DAW Export
    st.subheader("🎛️ DAW Export")
    
    daw_type = st.selectbox(
        "Target DAW",
        ["generic", "ableton", "logic", "fl"],
        format_func=lambda x: x.capitalize(),
        help="Select your DAW for export"
    )
    
    if st.button("🎛️ Export DAW Project"):
        daw_path = st.session_state.current_project.project_path / f"daw_project_{daw_type}.json"
        export_daw_project(st.session_state.project_config, daw_path, daw_type)
        
        with open(daw_path, "r") as f:
            st.download_button(
                label=f"Download {daw_type.capitalize()} Project",
                data=f.read(),
                file_name=f"daw_project_{daw_type}.json",
                mime="application/json"
            )
    
    # Complete package export
    st.subheader("📦 Complete Package")
    
    if st.button("📦 Export Complete Package", type="primary"):
        with st.spinner("Creating export package..."):
            try:
                package_path = create_export_package(
                    st.session_state.project_config,
                    st.session_state.current_project.project_path
                )
                
                with open(package_path, "rb") as f:
                    st.download_button(
                        label="Download Complete Package",
                        data=f.read(),
                        file_name=f"{st.session_state.current_project.project_name}_export.zip",
                        mime="application/zip"
                    )
                
                st.success("✅ Export package created successfully!")
                
            except Exception as e:
                st.error(f"❌ Error creating export package: {str(e)}")


def main():
    """Main application function"""
    # Initialize session state
    initialize_session_state()
    
    # Display header
    main_header()
    
    # Sidebar
    sidebar_controls()
    
    # Main content
    if st.session_state.current_project is None:
        st.info("👋 Welcome to Beat & Stems Lab! Upload an audio file to get started.")
        
        # Show available projects
        projects = list_projects()
        if projects:
            st.subheader("📂 Available Projects")
            for project in projects:
                with st.expander(f"📁 {project['name']}"):
                    config = project["config"]
                    if "audio" in config:
                        audio_info = config["audio"]
                        st.write(f"**Duration:** {audio_info.get('duration', 0):.1f}s")
                        st.write(f"**Sample Rate:** {audio_info.get('sr', 0)} Hz")
                    
                    if "analysis" in config:
                        analysis = config["analysis"]
                        if "tempo" in analysis:
                            st.write(f"**Tempo:** {analysis['tempo']:.1f} BPM")
                    
                    if st.button(f"Load {project['name']}", key=f"load_{project['name']}"):
                        st.session_state.current_project = ProjectManager(project['name'])
                        st.session_state.project_config = st.session_state.current_project.load_project_config()
                        st.rerun()
    else:
        # Project is loaded, show main interface
        st.success(f"✅ Project loaded: {st.session_state.current_project.project_name}")
        
        # Main tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🎛️ Stem Separation", 
            "📊 Analysis", 
            "🎼 Chords", 
            "📤 Export",
            "ℹ️ About"
        ])
        
        with tab1:
            stem_separation_section()
        
        with tab2:
            analysis_section()
        
        with tab3:
            chord_analysis_section()
        
        with tab4:
            export_section()
        
        with tab5:
            st.subheader("ℹ️ About Beat & Stems Lab")
            st.write("""
            **Beat & Stems Lab** is a local-only audio analysis and stem separation tool.
            
            ### Features:
            - 🎛️ **Stem Separation**: Separate vocals, drums, bass, and other instruments
            - 📊 **Audio Analysis**: Tempo detection, beat tracking, and rhythm analysis
            - 🎹 **Melody Extraction**: Extract lead melodies to MIDI
            - 🥁 **Drum Analysis**: Detect and classify drum patterns
            - 🎼 **Chord Analysis**: Identify chord progressions and key
            - 📤 **Export**: Export to various DAW formats
            
            ### Privacy:
            - ✅ **100% Local**: No data sent to external servers
            - ✅ **Offline**: Works without internet connection
            - ✅ **Private**: All processing happens on your computer
            
            ### Supported Formats:
            - Audio: MP3, WAV, FLAC, M4A, AAC
            - Export: WAV, MIDI, JSON, TXT, ZIP
            
            ### System Requirements:
            - Python 3.10+
            - 4GB+ RAM recommended
            - GPU acceleration optional (CUDA for Windows/NVIDIA)
            """)
            
            st.subheader("🔧 Technical Details")
            st.write(f"""
            - **Version**: {APP_VERSION}
            - **Sample Rate**: 44.1 kHz
            - **Export Format**: 32-bit float WAV
            - **MIDI Format**: Standard MIDI files
            - **Project Format**: JSON-based project files
            """)


if __name__ == "__main__":
    main()
