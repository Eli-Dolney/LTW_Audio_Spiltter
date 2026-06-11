"""
LTW Audio - Main Application
Local audio analysis, stem separation, and Strudel live-coding studio.
"""
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional

# Matplotlib cache in writable dir (avoids 6s+ hang / grey screen on startup)
os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "ltw-mpl"))

import numpy as np
import streamlit as st

from config import APP_TITLE, APP_VERSION, STEM_METHOD_DEFAULT
from src.app_helpers import (
    build_analysis_data_for_strudel,
    get_stem_audio_for_analysis,
    get_stem_paths_from_config,
    load_all_analysis_results,
    list_remix_files,
    merge_beat_summary,
    normalize_melody_stats,
    safe_extract_melody,
)
from src.io_utils import (
    ProjectManager,
    load_audio_file,
    is_supported_format,
    create_project_from_audio,
    list_projects,
    save_analysis_results,
    get_stem_path,
    get_midi_path,
    save_audio_file,
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
    defaults = {
        "current_project": None,
        "audio_data": None,
        "audio_sr": None,
        "project_config": None,
        "analysis_results": {},
        "stems_data": {},
        "strudel_files": {},
        "workspace_mode": "Replicate",
        "show_create_player": False,
        "voice_path": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def sync_project_state(project: ProjectManager) -> None:
    """Load config, stems, and analysis from disk into session state."""
    st.session_state.project_config = project.load_project_config()
    # Fresh load per project (avoid leaking prior project's analysis)
    st.session_state.analysis_results = load_all_analysis_results(project, {})
    # Keep stems on disk only — loading all WAVs into session blows the 200MB Streamlit limit
    st.session_state.stems_data = {}

    config = st.session_state.project_config or {}
    st.session_state.audio_data = None
    st.session_state.audio_sr = None
    audio_meta = config.get("audio") or {}
    audio_path = audio_meta.get("path") or config.get("audio_file")
    default_sr = audio_meta.get("sr") or config.get("sample_rate", 44100)
    if audio_path:
        path = Path(audio_path)
        if not path.exists() and config.get("stems", {}).get("paths"):
            # Fallback: reconstruct rough mix from stems if original file moved
            from src.app_helpers import load_stems_from_project
            stems = load_stems_from_project(project)
            if stems:
                mix = sum(stems.values())
                st.session_state.audio_data = mix / max(len(stems), 1)
                st.session_state.audio_sr = default_sr
        elif path.exists():
            audio, sr = load_audio_file(path)
            st.session_state.audio_data = audio
            st.session_state.audio_sr = sr

    files = {}
    strudel_dir = project.project_path / "strudel"
    if strudel_dir.exists():
        for name, fname in [
            ("building_blocks", "building_blocks.js"),
            ("arrangement", "arrangement.js"),
            ("loops", "loops.js"),
            ("html", "strudel_player.html"),
            ("blocks_html", "strudel_blocks.html"),
            ("loops_html", "strudel_blocks.html"),
        ]:
            p = strudel_dir / fname
            if p.exists():
                files[name] = str(p)
        for remix in list_remix_files(strudel_dir):
            files[remix.stem] = str(remix)
    st.session_state.strudel_files = files

    from src.app_helpers import resolve_project_file

    voice_file = resolve_project_file(
        project,
        (config.get("voice") or {}).get("path"),
        "voice.wav",
    )
    st.session_state.voice_path = str(voice_file) if voice_file else None


def main_header():
    """Display main header"""
    st.markdown(f'<h1 class="main-header">🎵 {APP_TITLE}</h1>', unsafe_allow_html=True)
    st.markdown(
        f"<p style='text-align: center; color: #666;'>v{APP_VERSION} — Local stem splitter, Strudel remix engine & stem-slice playback</p>",
        unsafe_allow_html=True,
    )


def sidebar_controls():
    """Sidebar controls for file upload and project management"""
    st.sidebar.header("🎛️ Workspace")
    if "workspace_mode" not in st.session_state:
        st.session_state.workspace_mode = "Replicate"
    st.sidebar.radio(
        "Mode",
        ["Replicate", "Create"],
        key="workspace_mode",
        help="Replicate: analyze songs into Strudel. Create: build original beats.",
    )

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
                    sync_project_state(project)
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

        if (
            "project_select" not in st.session_state
            or st.session_state.project_select not in project_names
        ):
            st.session_state.project_select = next(
                (n for n in project_names if "Nice_2_Know_Ya_Full" in n),
                project_names[0],
            )

        st.sidebar.selectbox(
            "Select Project",
            project_names,
            key="project_select",
            help="Choose a project, then click Load",
        )

        if st.sidebar.button("📂 Load Project", type="primary", key="load_project_btn"):
            name = st.session_state.get("project_select")
            try:
                with st.spinner(f"Loading {name}..."):
                    project = ProjectManager(name)
                    st.session_state.current_project = project
                    sync_project_state(project)
                st.sidebar.success("✅ Project loaded!")
                st.rerun()
            except Exception as e:
                st.sidebar.error(f"❌ {e}")

        with st.sidebar.expander(f"📋 {len(projects)} projects", expanded=False):
            for p in projects:
                cfg = p.get("config", {})
                dur = cfg.get("audio", {}).get("duration")
                tempo = cfg.get("analysis", {}).get("tempo")
                meta = []
                if dur:
                    meta.append(f"{dur:.0f}s")
                if tempo:
                    meta.append(f"{tempo:.0f} BPM")
                st.caption(f"**{p['name']}**" + (f" — {', '.join(meta)}" if meta else ""))
    else:
        st.sidebar.info("No existing projects found")
    
    # Project info
    if st.session_state.current_project:
        st.sidebar.header("📋 Current Project")
        st.sidebar.write(f"**Name:** {st.session_state.current_project.project_name}")
        
        if st.session_state.project_config:
            cfg = st.session_state.project_config
            audio_info = cfg.get("audio") or {}
            duration = audio_info.get("duration") or cfg.get("duration")
            sr = audio_info.get("sr") or cfg.get("sample_rate")
            if duration:
                st.sidebar.write(f"**Duration:** {float(duration):.1f}s")
            if sr:
                st.sidebar.write(f"**Sample Rate:** {int(sr)} Hz")
            
            if "analysis" in st.session_state.project_config:
                analysis = st.session_state.project_config["analysis"]
                if "tempo" in analysis:
                    st.sidebar.write(f"**Tempo:** {analysis['tempo']:.1f} BPM")


def stem_separation_section():
    """Stem separation section"""
    from src.separation import StemSeparator, get_available_methods, estimate_separation_time
    from src.viz import create_multi_stem_comparison

    st.header("🎛️ Stem Separation")
    
    if st.session_state.audio_data is None:
        st.warning("⚠️ Please load an audio file first")
        return
    
    # Separation method selection
    available_methods = get_available_methods()
    if not available_methods:
        st.error(
            "❌ No stem separation engine is installed. "
            "Install Demucs with: `pip install demucs torch torchaudio`"
        )
        return

    method_keys = list(available_methods.keys())
    default_index = method_keys.index(STEM_METHOD_DEFAULT) if STEM_METHOD_DEFAULT in method_keys else 0
    selected_method = st.selectbox(
        "Separation Method",
        method_keys,
        index=default_index,
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
                        # Save to disk only; do not cache raw arrays in session (400MB+ in browser)
                    st.session_state.stems_data = {}

                    st.success("✅ Stem separation completed!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error during stem separation: {str(e)}")
    
    project = st.session_state.current_project
    config = st.session_state.project_config or {}
    stem_paths = get_stem_paths_from_config(config, project)

    if stem_paths:
        st.subheader("🎵 Separated Stems")

        with st.expander("Waveform overview (optional)", expanded=False):
            from src.app_helpers import load_stems_from_project
            stems_preview = load_stems_from_project(project)
            if stems_preview:
                fig = create_multi_stem_comparison(stems_preview, st.session_state.audio_sr)
                st.plotly_chart(fig, use_container_width=True)

        st.subheader("🔊 Preview & Download")
        for stem_name, path_str in stem_paths.items():
            stem_path = Path(path_str)
            if not stem_path.is_absolute():
                stem_path = project.project_path / stem_path
            if not stem_path.exists():
                stem_path = get_stem_path(project, stem_name)
            col_a, col_b = st.columns([3, 1])
            with col_a:
                if stem_path.exists():
                    st.audio(str(stem_path), format="audio/wav")
            with col_b:
                if stem_path.exists():
                    with open(stem_path, "rb") as f:
                        st.download_button(
                            f"⬇ {stem_name}",
                            data=f.read(),
                            file_name=f"{stem_name}.wav",
                            mime="audio/wav",
                            key=f"dl_{stem_name}",
                        )


def _run_full_stem_analysis():
    """Run tempo + drums + melody + bass + chords using separated stems when available."""
    from src.timing import create_beat_grid
    from src.drums import extract_drums_to_midi
    from src.chords import analyze_chord_progression, detect_key_from_chroma

    project = st.session_state.current_project
    audio = st.session_state.audio_data
    sr = st.session_state.audio_sr
    from src.app_helpers import load_stems_from_project
    stems = load_stems_from_project(project)

    progress = st.progress(0, text="Starting full analysis...")
    steps = [
        ("tempo_beats", lambda: create_beat_grid(audio, sr)),
        (
            "drums",
            lambda: extract_drums_to_midi(
                get_stem_audio_for_analysis("drums", stems, audio, project),
                sr,
                str(get_midi_path(project, "drums_basic")),
                confidence_threshold=0.35,
            ),
        ),
        (
            "melody",
            lambda: safe_extract_melody(
                get_stem_audio_for_analysis("melody", stems, audio, project),
                sr,
                str(get_midi_path(project, "melody")),
                beat_times=st.session_state.analysis_results.get("tempo_beats", {}).get("beat_times"),
            ),
        ),
        (
            "bass",
            lambda: safe_extract_melody(
                get_stem_audio_for_analysis("bass", stems, audio, project),
                sr,
                str(get_midi_path(project, "bass")),
                beat_times=st.session_state.analysis_results.get("tempo_beats", {}).get("beat_times"),
            ),
        ),
    ]

    for i, (name, fn) in enumerate(steps):
        progress.progress((i + 1) / 6, text=f"Analyzing {name}...")
        result = fn()
        save_analysis_results(project, name, result)
        st.session_state.analysis_results[name] = result

    progress.progress(5 / 6, text="Analyzing chords...")
    chord_audio = get_stem_audio_for_analysis("chords", stems, audio, project)
    chord_results = analyze_chord_progression(chord_audio, sr)
    key, key_conf = detect_key_from_chroma(np.array(chord_results["chroma_features"]))
    chord_results["key"] = key
    chord_results["key_confidence"] = key_conf
    save_analysis_results(project, "chords", chord_results)
    st.session_state.analysis_results["chords"] = chord_results

    config = st.session_state.project_config or {}
    tb = st.session_state.analysis_results.get("tempo_beats", {})
    merge_beat_summary(config, tb)
    if "analysis" not in config:
        config["analysis"] = {}
    config["analysis"]["key_guess"] = key
    project.save_project_config(config)
    st.session_state.project_config = config
    progress.progress(1.0, text="Done!")
    st.success("Full stem-based analysis complete.")


def analysis_section():
    """Audio analysis section"""
    from src.timing import create_beat_grid
    from src.drums import extract_drums_to_midi
    from src.viz import (
        create_waveform_plot,
        create_spectrogram_plot,
        create_waveform_with_beats,
    )

    st.header("📊 Audio Analysis")

    if st.session_state.audio_data is None:
        st.warning("⚠️ Please load an audio file first")
        return

    config = st.session_state.project_config or {}
    has_stems = bool(get_stem_paths_from_config(config, st.session_state.current_project))
    if not has_stems:
        st.info("Tip: Separate stems first for better drum/melody/bass accuracy.")

    if st.button("⚡ Run full analysis (stems-aware)", type="primary", key="full_analysis"):
        with st.spinner("Running full pipeline..."):
            try:
                _run_full_stem_analysis()
                st.rerun()
            except Exception as e:
                st.error(f"Analysis failed: {e}")

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
                    merge_beat_summary(config, beat_analysis)
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
                    beat_times = None
                    if "tempo_beats" in st.session_state.analysis_results:
                        beat_times = st.session_state.analysis_results["tempo_beats"].get("beat_times", [])

                    melody_audio = get_stem_audio_for_analysis(
                        "melody",
                        {},
                        st.session_state.audio_data,
                        st.session_state.current_project,
                    )
                    midi_path = get_midi_path(st.session_state.current_project, "melody")
                    melody_results = safe_extract_melody(
                        melody_audio,
                        st.session_state.audio_sr,
                        str(midi_path),
                        beat_times=beat_times,
                        quantize=quantize,
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
            stats = normalize_melody_stats(results.get("statistics", {}))

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
                    drum_audio = get_stem_audio_for_analysis(
                        "drums",
                        {},
                        st.session_state.audio_data,
                        st.session_state.current_project,
                    )
                    midi_path = get_midi_path(st.session_state.current_project, "drums_basic")
                    drum_results = extract_drums_to_midi(
                        drum_audio,
                        st.session_state.audio_sr,
                        str(midi_path),
                        confidence_threshold=confidence_threshold,
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
    from src.chords import analyze_chord_progression, detect_key_from_chroma

    st.header("🎼 Chord Analysis")
    
    if st.session_state.audio_data is None:
        st.warning("⚠️ Please load an audio file first")
        return
    
    if st.button("🎼 Analyze Chords", type="primary"):
        with st.spinner("Analyzing chord progression..."):
            try:
                chord_audio = get_stem_audio_for_analysis(
                    "chords",
                    {},
                    st.session_state.audio_data,
                    st.session_state.current_project,
                )
                chord_results = analyze_chord_progression(chord_audio, st.session_state.audio_sr)
                
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


def _render_voice_preview(project: ProjectManager, config: dict) -> Optional[Path]:
    """Show player + download when voice.wav exists; return resolved path."""
    from src.app_helpers import resolve_project_file
    import soundfile as sf

    voice_cfg = (config or {}).get("voice") or {}
    voice_path = resolve_project_file(
        project,
        voice_cfg.get("path") or st.session_state.get("voice_path"),
        "voice.wav",
    )
    if voice_path is None:
        return None

    st.session_state.voice_path = str(voice_path)
    try:
        info = sf.info(str(voice_path))
        dur_label = f"{info.duration:.1f}s"
    except Exception:
        dur_label = "unknown length"

    st.subheader("🔊 Extracted Voice")
    st.success(f"Voice file ready — **{voice_path.name}** ({dur_label})")
    st.audio(str(voice_path), format="audio/wav")
    with open(voice_path, "rb") as f:
        voice_bytes = f.read()
    st.download_button(
        "⬇ Download voice.wav",
        data=voice_bytes,
        file_name="voice.wav",
        mime="audio/wav",
        key="dl_voice",
    )
    st.caption(f"Saved at: `{voice_path}`")
    return voice_path


def voice_isolation_section():
    """Extract clean voice/speech from any audio (e.g. YouTube rips)."""
    from src.separation import (
        DEMUCS_AVAILABLE,
        extract_voice,
        estimate_separation_time,
    )
    from src.app_helpers import resolve_project_file

    st.header("🎙️ Voice Isolation")
    st.caption(
        "Pull out speech or vocals and discard background music and noise. "
        "Best for podcasts, interviews, and YouTube clips — not the same as music stem separation."
    )

    project = st.session_state.current_project
    config = st.session_state.project_config or {}

    if project is not None:
        existing = _render_voice_preview(project, config)
        if existing is not None:
            st.divider()

        vocals_stem = resolve_project_file(
            project,
            (config.get("stems") or {}).get("paths", {}).get("vocals"),
            "vocals.wav",
        )
        if vocals_stem is None and (project.stems_path / "vocals.wav").exists():
            vocals_stem = (project.stems_path / "vocals.wav").resolve()
        if vocals_stem is not None and existing is None:
            with st.expander("Preview: vocals stem (from Stems tab)", expanded=True):
                st.caption(
                    "You already separated stems — this is the Demucs **vocals** track. "
                    "Use **Extract Voice** below for a dedicated `voice.wav` export."
                )
                st.audio(str(vocals_stem), format="audio/wav")

    if st.session_state.audio_data is None:
        st.warning("⚠️ Please load an audio file first")
        return

    if not DEMUCS_AVAILABLE:
        st.error(
            "❌ Demucs is required for voice isolation. "
            "Install with: `pip install demucs torch torchaudio`"
        )
        return

    if project is None:
        st.warning("Create or load a project first so the voice file can be saved.")
        return

    duration = len(st.session_state.audio_data) / st.session_state.audio_sr
    est_time = estimate_separation_time(duration, "demucs:4stems")
    st.info(f"**Estimated processing time:** {est_time:.0f} seconds (Demucs)")

    if st.button("🎙️ Extract Voice", type="primary", key="extract_voice_btn"):
        with st.spinner("Isolating voice (Demucs)..."):
            try:
                voice_audio = extract_voice(
                    st.session_state.audio_data,
                    st.session_state.audio_sr,
                )
                voice_path = project.project_path / "voice.wav"
                save_audio_file(voice_audio, voice_path, st.session_state.audio_sr)
                if "voice" not in config:
                    config["voice"] = {}
                config["voice"]["path"] = "voice.wav"
                project.save_project_config(config)
                st.session_state.project_config = config
                st.session_state.voice_path = str(voice_path.resolve())
                st.rerun()
            except Exception as e:
                st.error(f"❌ Voice isolation failed: {e}")
                st.exception(e)


def strudel_section():
    """Strudel — building blocks, arrangement, remix lab, and stem slices."""
    from src.strudel_integration import StrudelPatternGenerator, bpm_to_cpm, generate_strudel_from_analysis
    from src.strudel_player_component import render_live_strudel_player
    from src.remix_engine import (
        LAYER_SOUND_PRESETS,
        get_preset_choices,
        render_custom_remix,
    )
    from src.app_helpers import get_stem_paths_from_config, save_strudel_export

    st.header("🎵 Strudel — Building Blocks, Remix Lab & Stem Slices")

    if st.session_state.current_project is None:
        st.warning("⚠️ Please load a project first.")
        return

    project = st.session_state.current_project
    analysis_results = load_all_analysis_results(
        project, st.session_state.analysis_results
    )
    st.session_state.analysis_results = analysis_results

    has_tempo = "tempo_beats" in analysis_results
    if not has_tempo:
        st.warning("Run **Tempo & Beats** or **Full analysis** before generating Strudel patterns.")
        return

    analysis_data = build_analysis_data_for_strudel(project, analysis_results)
    st.caption(
        f"Tempo: {analysis_data['tempo']:.1f} BPM | "
        f"Key: {analysis_data.get('key', '?')} | "
        f"Duration: {analysis_data['duration']:.1f}s"
    )

    if st.button("🎵 Generate Strudel replica", type="primary"):
        try:
            with st.spinner("Generating Strudel patterns + stem slices..."):
                config = project.load_project_config() or {}
                stem_paths = get_stem_paths_from_config(config, project)
                strudel_files = generate_strudel_from_analysis(
                    analysis_data,
                    str(project.project_path / "strudel"),
                    project_path=str(project.project_path),
                    project_name=project.project_name,
                    stem_paths=stem_paths,
                )
                st.session_state.strudel_files = strudel_files
                st.success("Strudel patterns generated!")
                if strudel_files.get("stem_remix"):
                    st.info(
                        "Stem slices ready! Run `python serve_samples.py` in the project folder "
                        "for strudel.cc playback, or use the Streamlit stem remix tab."
                    )
                st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

    files = st.session_state.get("strudel_files") or {}
    if not files:
        return

    default_cpm = bpm_to_cpm(float(analysis_data["tempo"]))
    remix_keys = sorted(k for k in files if k.startswith("remix_"))
    tab_labels = [
        "Live Player",
        "Remix Lab",
        "Building Blocks",
        "Arrangement",
        "Stem Slices",
    ] + [
        k.replace("remix_", "").replace("_", " ").title() for k in remix_keys
    ] + ["Downloads"]
    tabs = st.tabs(tab_labels)

    def _read_code(key: str) -> str:
        path = files.get(key)
        if path and Path(path).exists():
            return Path(path).read_text()
        return ""

    with tabs[0]:
        code = _read_code("arrangement") or _read_code("building_blocks") or _read_code("loops")
        if code:
            render_live_strudel_player(
                code,
                title="Arrangement",
                height=520,
                default_cpm=default_cpm,
            )
        else:
            st.info("Generate patterns first.")

    with tabs[1]:
        st.subheader("🎛️ Remix Lab")
        st.caption("Compose custom remixes from extracted patterns — tweak layers, styles, and variation.")

        preset_choices = get_preset_choices()
        col1, col2 = st.columns(2)
        with col1:
            global_preset = st.selectbox(
                "Global style preset",
                options=list(preset_choices.keys()),
                format_func=lambda k: preset_choices[k],
                key="remix_global_preset",
            )
        with col2:
            intensity = st.slider(
                "Variation intensity",
                0.0, 1.0, 0.3, 0.05,
                help="Higher = more random transforms (degrade, euclid, rev, etc.)",
                key="remix_intensity",
            )

        seed = st.session_state.get("remix_seed", 42)
        if st.button("🎲 Reroll seed", key="reroll_seed"):
            import random
            seed = random.randint(0, 99999)
            st.session_state.remix_seed = seed
            st.rerun()
        st.caption(f"Seed: {seed}")

        layer_cols = st.columns(4)
        enabled_layers = []
        layer_sounds: dict = {}
        for i, layer in enumerate(["drums", "bass", "melody", "chords"]):
            with layer_cols[i]:
                enabled = st.checkbox(layer.title(), value=True, key=f"remix_layer_{layer}")
                if enabled:
                    enabled_layers.append(layer)
                sound_opts = LAYER_SOUND_PRESETS.get(layer, {"default": ""})
                layer_sounds[layer] = st.selectbox(
                    f"{layer} sound",
                    options=list(sound_opts.keys()),
                    key=f"remix_sound_{layer}",
                )

        if st.button("🎵 Generate custom remix", type="primary", key="gen_custom_remix"):
            gen = StrudelPatternGenerator()
            blocks = gen._extract_blocks(analysis_data)
            custom_code = render_custom_remix(
                blocks,
                global_preset_id=global_preset,
                layer_sounds=layer_sounds,
                enabled_layers=enabled_layers,
                intensity=intensity,
                seed=seed,
            )
            st.session_state.custom_remix_code = custom_code
            paths = save_strudel_export(project, custom_code, "custom_remix.js")
            st.session_state.strudel_files["custom_remix"] = paths["js"]
            st.success("Custom remix generated!")

        custom_code = st.session_state.get("custom_remix_code", "")
        if custom_code:
            st.code(custom_code[:2000] + ("..." if len(custom_code) > 2000 else ""), language="javascript")
            render_live_strudel_player(
                custom_code,
                title="Custom Remix",
                height=480,
                default_cpm=default_cpm,
            )
            st.download_button(
                "Download custom_remix.js",
                custom_code,
                file_name="custom_remix.js",
                mime="text/javascript",
                key="dl_custom_remix",
            )

    with tabs[2]:
        code = _read_code("building_blocks") or _read_code("loops")
        if code:
            st.code(code, language="javascript")
            st.caption("Uncomment a solo line (drums, bass, melody, etc.) to hear one layer.")
            if st.button("Play building blocks", key="play_blocks"):
                render_live_strudel_player(
                    code, title="Building Blocks", default_cpm=default_cpm
                )

    with tabs[3]:
        code = _read_code("arrangement")
        if code:
            st.code(code, language="javascript")
            if st.button("Play arrangement", key="play_arrangement"):
                render_live_strudel_player(
                    code, title="Arrangement", default_cpm=default_cpm
                )

    with tabs[4]:
        st.subheader("🎧 Real Stem Slices")
        stem_code = _read_code("stem_remix_streamlit") or _read_code("stem_remix")
        if stem_code:
            st.caption(
                "Plays actual separated stem audio sliced by bar. "
                "For strudel.cc: run `python serve_samples.py` in the project folder."
            )
            st.code(stem_code[:1500] + ("..." if len(stem_code) > 1500 else ""), language="javascript")
            if st.button("Play stem recreation", key="play_stem_remix"):
                render_live_strudel_player(
                    stem_code, title="Stem Slices", default_cpm=default_cpm
                )
            shuffle_code = _read_code("stem_remix_shuffle")
            if shuffle_code and st.button("Play stem shuffle remix", key="play_stem_shuffle"):
                render_live_strudel_player(
                    shuffle_code, title="Stem Shuffle", default_cpm=default_cpm
                )
        else:
            st.info("Generate Strudel patterns with separated stems to create slice playback.")

    for i, rk in enumerate(remix_keys):
        with tabs[5 + i]:
            code = _read_code(rk)
            if code:
                st.code(code, language="javascript")
                if st.button(f"Play {rk}", key=f"play_{rk}"):
                    render_live_strudel_player(
                        code, title=rk, default_cpm=default_cpm
                    )

    with tabs[-1]:
        for label, key in [
            ("Arrangement HTML", "html"),
            ("Building blocks HTML", "blocks_html"),
        ]:
            if key in files and Path(files[key]).exists():
                with open(files[key], "rb") as f:
                    st.download_button(
                        f"Download {label}",
                        f.read(),
                        file_name=Path(files[key]).name,
                        mime="text/html",
                        key=f"dl_{key}",
                    )


def export_section():
    """Export section"""
    from src.export import (
        export_project_summary,
        export_analysis_report,
        create_export_package,
        export_daw_project,
    )

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
    try:
        _run_app()
    except Exception as e:
        st.error(f"App error: {e}")
        st.exception(e)


def _run_app():
    """Main UI (wrapped for top-level error display)."""
    initialize_session_state()
    main_header()
    sidebar_controls()
    
    # Main content
    if st.session_state.current_project is None:
        if st.session_state.workspace_mode == "Create":
            from src.create_studio import render_create_studio
            render_create_studio(None)
        else:
            st.info(f"👋 Welcome to {APP_TITLE}! Upload an audio file in the sidebar to get started.")
        
        # Show available projects
        projects = list_projects()
        if projects:
            st.subheader("📂 Available Projects")
            for project in projects:
                with st.expander(f"📁 {project['name']}"):
                    config = project["config"]
                    audio_info = config.get("audio") or {}
                    duration = audio_info.get("duration") or config.get("duration")
                    sr = audio_info.get("sr") or config.get("sample_rate")
                    if duration:
                        st.write(f"**Duration:** {float(duration):.1f}s")
                    if sr:
                        st.write(f"**Sample Rate:** {int(sr)} Hz")
                    
                    if "analysis" in config:
                        analysis = config["analysis"]
                        if "tempo" in analysis:
                            st.write(f"**Tempo:** {analysis['tempo']:.1f} BPM")
                    
                    if st.button(f"Load {project['name']}", key=f"load_{project['name']}", type="primary"):
                        with st.spinner(f"Loading {project['name']}..."):
                            st.session_state.current_project = ProjectManager(project['name'])
                            sync_project_state(st.session_state.current_project)
                        st.rerun()
    else:
        st.success(f"✅ Project: {st.session_state.current_project.project_name}")

        if st.session_state.workspace_mode == "Create":
            from src.create_studio import render_create_studio
            render_create_studio(st.session_state.current_project)
        else:
            tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
                "🎛️ Stems",
                "📊 Analysis",
                "🎼 Chords",
                "🎵 Strudel",
                "🎙️ Voice Isolate",
                "📤 Export",
                "ℹ️ About",
            ])

            with tab1:
                stem_separation_section()
            with tab2:
                analysis_section()
            with tab3:
                chord_analysis_section()
            with tab4:
                strudel_section()
            with tab5:
                voice_isolation_section()
            with tab6:
                export_section()
            with tab7:
                about_section()


def about_section():
    st.subheader(f"ℹ️ About {APP_TITLE} v{APP_VERSION}")
    st.write(f"""
            **{APP_TITLE} v{APP_VERSION}** — free, local audio splitter + Strudel recreation studio.

            ### v2 highlights
            - 🎛️ **Remix Engine**: 8 style presets from your extracted patterns
            - 🧪 **Remix Lab**: Layer toggles, sounds, variation intensity, seed reroll
            - 🎧 **Stem slices**: Real separated audio in Strudel via bar-aligned chops
            - 🧱 **Building blocks & arrangement**: Solo layers or full `arrange()` structure
            - 🍎 **Mac M4**: Demucs on MPS, librosa pYIN melody (no TensorFlow)

            ### Core pipeline
            - **Stem separation**: Demucs 4-stem (vocals, drums, bass, other)
            - **Analysis**: Tempo, drums, melody, bass, chords → MIDI + JSON
            - **Strudel**: Dynamics, swing, per-section patterns, 8 remixes + custom
            - **Create studio**: Genre templates and beat gallery

            ### Privacy
            - ✅ 100% local processing — your audio never leaves your machine
            - ✅ Projects and media are gitignored if you clone from GitHub

            [GitHub](https://github.com/Eli-Dolney/LTW_Audio_Spiltter) · [CHANGELOG](CHANGELOG.md)
            """)
    st.subheader("🔧 Technical Details")
    st.write(f"""
            - **Version**: {APP_VERSION}
            - **Default stems**: {STEM_METHOD_DEFAULT}
            - **Sample rate**: 44.1 kHz
            - **Strudel player**: @strudel/web (CDN for in-app live preview)
            - **Stem slices**: copy `.streamlit/config.toml.example` → `.streamlit/config.toml`
            """)


if __name__ == "__main__":
    main()
