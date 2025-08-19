"""
Configuration settings for Beat & Stems Lab
"""
import os
from pathlib import Path

# Audio processing defaults
SAMPLE_RATE = 44100
N_FFT = 2048
HOP_LENGTH = 512
OVERLAP = 0.75

# Melody extraction settings
MELODY_CONF_THRESH = 0.5
MELODY_MIN_NOTE_DURATION = 0.1  # seconds
MELODY_MAX_NOTE_DURATION = 2.0  # seconds

# Drum detection thresholds
DRUM_THRESH = {
    "kick_lowband": 0.65,
    "snare_mid": 0.6,
    "hat_high": 0.6
}

# Stem separation defaults
STEM_METHOD_DEFAULT = "spleeter:2stems"
STEM_METHODS = {
    "spleeter:2stems": "Vocals + Other",
    "spleeter:4stems": "Vocals + Drums + Bass + Other",
    "spleeter:5stems": "Vocals + Drums + Bass + Piano + Other",
    "demucs:4stems": "Vocals + Drums + Bass + Other (High Quality)",
    "demucs:5stems": "Vocals + Drums + Bass + Piano + Other (High Quality)"
}

# MIDI settings
MIDI_VELOCITY_DEFAULT = 64
MIDI_DRUM_VELOCITY = 80
MIDI_DRUM_DURATION = 0.1  # seconds

# Drum mapping (MIDI note numbers)
DRUM_MAPPING = {
    "kick": 35,
    "snare": 38,
    "closed_hat": 42,
    "open_hat": 46,
    "crash": 49
}

# Frequency bands for drum detection
DRUM_FREQ_BANDS = {
    "kick": (20, 150),      # Hz
    "snare": (150, 800),    # Hz
    "hat": (800, 8000)      # Hz
}

# Chord analysis
CHORD_ANALYSIS_WINDOW = 1.0  # seconds
CHORD_CONFIDENCE_THRESH = 0.3

# File paths and directories
PROJECTS_DIR = Path("projects")
STEMS_DIR = "stems"
MIDI_DIR = "midi"
ANALYSIS_DIR = "analysis"

# Supported audio formats
SUPPORTED_FORMATS = [".mp3", ".wav", ".flac", ".m4a", ".aac"]

# Visualization settings
WAVEFORM_HEIGHT = 300
SPECTROGRAM_HEIGHT = 400
MAX_AUDIO_LENGTH = 600  # seconds (10 minutes) for performance

# Export settings
EXPORT_SAMPLE_RATE = 44100
EXPORT_BIT_DEPTH = 32  # float
EXPORT_FORMAT = "wav"

# Performance settings
CHUNK_SIZE = 30  # seconds for processing long files
CACHE_ENABLED = True

# App settings
APP_TITLE = "Beat & Stems Lab"
APP_VERSION = "1.0.0"

# Privacy settings
OFFLINE_MODE = True
NO_INTERNET = os.getenv("NO_INTERNET", "1") == "1"
