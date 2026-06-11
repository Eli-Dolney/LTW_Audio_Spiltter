"""
I/O utilities for Beat & Stems Lab
Handles file operations, project structure, and data persistence
"""
import os
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import soundfile as sf
import librosa
import numpy as np

from config import (
    PROJECTS_DIR, STEMS_DIR, MIDI_DIR, ANALYSIS_DIR,
    SUPPORTED_FORMATS, SAMPLE_RATE, EXPORT_SAMPLE_RATE,
    EXPORT_BIT_DEPTH, EXPORT_FORMAT, APP_VERSION
)


# Keys allowed inline in project.ltw.json (heavy data lives in analysis/*.json)
_ANALYSIS_SCALAR_KEYS = frozenset({
    "tempo", "duration", "total_beats", "key_guess", "key_confidence",
})


def slim_project_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Strip large embedded arrays/objects from config; keep paths and scalars only."""
    if not config:
        return config

    slim = dict(config)
    raw_analysis = config.get("analysis") or {}
    slim_analysis: Dict[str, Any] = {}

    for key, val in raw_analysis.items():
        if key in _ANALYSIS_SCALAR_KEYS and isinstance(val, (int, float, str, bool)):
            slim_analysis[key] = val
        elif isinstance(val, str) and (val.endswith(".json") or "/" in val):
            slim_analysis[key] = val

    slim["analysis"] = slim_analysis
    return slim


def config_is_bloated(config: Dict[str, Any]) -> bool:
    """True if config embeds large analysis payloads instead of file references."""
    analysis = config.get("analysis") or {}
    for key, val in analysis.items():
        if key in _ANALYSIS_SCALAR_KEYS:
            continue
        if isinstance(val, list) and len(val) > 20:
            return True
        if isinstance(val, dict) and key not in ("tempo",):
            return True
    return False


def merge_beat_summary(config: Dict[str, Any], beat_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Store tempo/beat summary in config without embedding beat_times."""
    if "analysis" not in config:
        config["analysis"] = {}
    for field in ("tempo", "duration", "total_beats"):
        if field in beat_analysis:
            config["analysis"][field] = beat_analysis[field]
    return config


class ProjectManager:
    """Manages project structure and file operations"""
    
    def __init__(self, project_name: str):
        self.project_name = project_name
        self.project_path = PROJECTS_DIR / project_name
        self.stems_path = self.project_path / STEMS_DIR
        self.midi_path = self.project_path / MIDI_DIR
        self.analysis_path = self.project_path / ANALYSIS_DIR
        
        # Create project structure
        self._create_project_structure()
    
    def _create_project_structure(self):
        """Create the project directory structure"""
        for path in [self.project_path, self.stems_path, self.midi_path, self.analysis_path]:
            path.mkdir(parents=True, exist_ok=True)
    
    def get_project_file(self) -> Path:
        """Get the project configuration file path"""
        return self.project_path / "project.ltw.json"
    
    def save_project_config(self, config: Dict[str, Any]):
        """Save project configuration to JSON file"""
        config = slim_project_config(config)
        config["version"] = APP_VERSION
        config["project_name"] = self.project_name
        
        with open(self.get_project_file(), 'w') as f:
            json.dump(config, f, indent=2)
    
    def load_project_config(self) -> Optional[Dict[str, Any]]:
        """Load project configuration from JSON file"""
        project_file = self.get_project_file()
        if not project_file.exists():
            return None
        
        with open(project_file, 'r') as f:
            raw = json.load(f)

        if config_is_bloated(raw):
            slim = slim_project_config(raw)
            self.save_project_config(slim)
            return slim

        return slim_project_config(raw)


def calculate_audio_checksum(audio_path: Path) -> str:
    """Calculate SHA256 checksum of audio file"""
    hash_sha256 = hashlib.sha256()
    with open(audio_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return f"sha256:{hash_sha256.hexdigest()}"


def load_audio_file(file_path: Path, target_sr: int = SAMPLE_RATE) -> Tuple[np.ndarray, int]:
    """
    Load audio file and resample if necessary
    
    Args:
        file_path: Path to audio file
        target_sr: Target sample rate
        
    Returns:
        Tuple of (audio_data, sample_rate)
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Audio file not found: {file_path}")
    
    # Load audio with librosa (handles resampling automatically)
    audio, sr = librosa.load(str(file_path), sr=target_sr, mono=True)
    
    return audio, sr


def save_audio_file(audio: np.ndarray, file_path: Path, sr: int = EXPORT_SAMPLE_RATE):
    """
    Save audio data to file
    
    Args:
        audio: Audio data as numpy array
        file_path: Output file path
        sr: Sample rate
    """
    # Ensure directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save with soundfile
    sf.write(str(file_path), audio, sr, subtype='FLOAT')


def is_supported_format(file_path: Path) -> bool:
    """Check if file format is supported"""
    return file_path.suffix.lower() in SUPPORTED_FORMATS


def get_audio_duration(file_path: Path) -> float:
    """Get duration of audio file in seconds"""
    try:
        info = sf.info(str(file_path))
        return info.duration
    except Exception as e:
        # Fallback to librosa
        audio, sr = librosa.load(str(file_path), sr=None, duration=None)
        return len(audio) / sr


def list_projects() -> list:
    """List projects using lightweight metadata (avoids loading multi-MB configs)."""
    if not PROJECTS_DIR.exists():
        return []

    projects = []
    for project_dir in sorted(PROJECTS_DIR.iterdir(), key=lambda p: p.name.lower()):
        if not project_dir.is_dir():
            continue
        project_file = project_dir / "project.ltw.json"
        if not project_file.exists():
            continue

        summary = _read_project_list_summary(project_dir.name, project_file)
        projects.append({"name": project_dir.name, "config": summary})

    return projects


def _read_project_list_summary(name: str, project_file: Path) -> Dict[str, Any]:
    """Read only small metadata for the project picker UI."""
    summary: Dict[str, Any] = {"audio": {}, "analysis": {}}
    try:
        size = project_file.stat().st_size
        if size > 200_000:
            # Bloated legacy config — read tempo/duration from analysis/tempo_beats.json if present
            tempo_file = project_file.parent / ANALYSIS_DIR / "tempo_beats.json"
            if tempo_file.exists():
                with open(tempo_file, "r") as f:
                    tb = json.load(f)
                summary["analysis"]["tempo"] = tb.get("tempo")
                summary["audio"]["duration"] = tb.get("duration")
            return summary

        with open(project_file, "r") as f:
            config = json.load(f)
        slim = slim_project_config(config)
        summary["audio"] = {
            k: slim.get("audio", {}).get(k)
            for k in ("duration", "sr")
            if slim.get("audio", {}).get(k) is not None
        }
        summary["analysis"] = {
            k: slim.get("analysis", {}).get(k)
            for k in ("tempo", "key_guess")
            if slim.get("analysis", {}).get(k) is not None
        }
    except Exception:
        pass
    return summary


def create_project_from_audio(audio_path: Path, project_name: str) -> ProjectManager:
    """
    Create a new project from an audio file
    
    Args:
        audio_path: Path to source audio file
        project_name: Name for the new project
        
    Returns:
        ProjectManager instance
    """
    # Validate input
    if not is_supported_format(audio_path):
        raise ValueError(f"Unsupported audio format: {audio_path.suffix}")
    
    # Create project manager
    project = ProjectManager(project_name)
    
    # Load audio to get metadata
    audio, sr = load_audio_file(audio_path)
    duration = len(audio) / sr
    
    # Create initial project config
    config = {
        "audio": {
            "path": str(audio_path.absolute()),
            "sr": sr,
            "duration": duration,
            "checksum": calculate_audio_checksum(audio_path)
        },
        "stems": {},
        "analysis": {},
        "midi": {},
        "created_at": str(Path().cwd()),
        "status": "loaded"
    }
    
    # Save initial config
    project.save_project_config(config)
    
    return project


def save_analysis_results(project: ProjectManager, analysis_type: str, results: Dict[str, Any]):
    """Save analysis results to project"""
    analysis_file = project.analysis_path / f"{analysis_type}.json"
    
    with open(analysis_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Update project config
    config = project.load_project_config()
    if config is None:
        config = {}
    
    if "analysis" not in config:
        config["analysis"] = {}
    
    config["analysis"][analysis_type] = str(analysis_file)
    project.save_project_config(config)


def load_analysis_results(project: ProjectManager, analysis_type: str) -> Optional[Dict[str, Any]]:
    """Load analysis results from project"""
    analysis_file = project.analysis_path / f"{analysis_type}.json"
    
    if not analysis_file.exists():
        return None
    
    with open(analysis_file, 'r') as f:
        return json.load(f)


def get_stem_path(project: ProjectManager, stem_name: str) -> Path:
    """Get path for a specific stem file"""
    return project.stems_path / f"{stem_name}.{EXPORT_FORMAT}"


def get_midi_path(project: ProjectManager, midi_name: str) -> Path:
    """Get path for a specific MIDI file"""
    return project.midi_path / f"{midi_name}.mid"
