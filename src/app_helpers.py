"""
Shared helpers for the LTW Audio Streamlit app and analysis pipeline.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import librosa
import numpy as np

from config import PROJECTS_DIR
from src.io_utils import (
    ProjectManager,
    load_analysis_results,
    load_audio_file,
    save_analysis_results,
)


def normalize_melody_stats(stats: dict) -> dict:
    """Ensure melody statistics dict has keys the UI expects (legacy JSON may omit some)."""
    total = stats.get("total_notes", 0)
    return {
        "total_notes": total,
        "avg_duration": float(stats.get("avg_duration", 0.0)),
        "avg_confidence": float(stats.get("avg_confidence", 0.0)),
    }


def resolve_project_file(
    project: ProjectManager,
    path_str: Optional[str],
    filename: str,
) -> Optional[Path]:
    """
    Resolve a file path from project config (absolute, cwd-relative, or project-local).

    Handles paths like ``projects/MySong/voice.wav`` when the project dir is already
    ``projects/MySong``.
    """
    project_dir = project.project_path.resolve()
    candidates: List[Path] = []

    if path_str:
        p = Path(path_str)
        candidates.append(p)
        if not p.is_absolute():
            candidates.append(Path.cwd() / p)
            candidates.append(project_dir / p.name)
            parts = p.parts
            if len(parts) >= 2 and parts[0] == "projects":
                candidates.append(project_dir / Path(*parts[2:]))
            elif len(parts) == 1:
                candidates.append(project_dir / p)

    candidates.append(project_dir / filename)

    seen: set = set()
    for c in candidates:
        try:
            resolved = c.resolve()
        except (OSError, RuntimeError):
            continue
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.is_file():
            return resolved
    return None


def get_stem_paths_from_config(config: dict, project: ProjectManager) -> Dict[str, str]:
    """Return stem_name -> wav path from project config or stems folder."""
    paths = (config or {}).get("stems", {}).get("paths", {})
    if paths:
        return {k: str(v) for k, v in paths.items()}

    found: Dict[str, str] = {}
    if project.stems_path.exists():
        for wav in project.stems_path.glob("*.wav"):
            found[wav.stem] = str(wav)
    return found


def merge_beat_summary(config: dict, beat_analysis: dict) -> dict:
    """Store tempo/beat summary in config without embedding beat_times."""
    if "analysis" not in config:
        config["analysis"] = {}
    for field in ("tempo", "duration", "total_beats"):
        if field in beat_analysis:
            config["analysis"][field] = beat_analysis[field]
    return config


from src.melody import create_midi_from_notes


ANALYSIS_TYPES = ("tempo_beats", "drums", "melody", "bass", "chords")


def load_all_analysis_results(
    project: ProjectManager,
    session_cache: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Load analysis JSON from disk, merged with optional session cache."""
    results: Dict[str, Any] = {}
    if session_cache:
        results.update(session_cache)

    for analysis_type in ANALYSIS_TYPES:
        if analysis_type not in results:
            loaded = load_analysis_results(project, analysis_type)
            if loaded is not None:
                results[analysis_type] = loaded

    return results


def build_analysis_data_for_strudel(
    project: ProjectManager,
    analysis_results: Dict[str, Any],
) -> Dict[str, Any]:
    """Build the analysis_data dict expected by StrudelPatternGenerator."""
    tempo_beats = analysis_results.get("tempo_beats", {})
    chords = analysis_results.get("chords", {})
    config = project.load_project_config() or {}

    tempo = tempo_beats.get("tempo") or config.get("analysis", {}).get("tempo", 120)
    duration = tempo_beats.get("duration")
    if duration is None and config.get("audio"):
        duration = config["audio"].get("duration", 60)
    if duration is None:
        duration = 60

    return {
        "tempo": float(tempo) if tempo else 120.0,
        "duration": float(duration),
        "beat_times": tempo_beats.get("beat_times", []),
        "tempo_beats": tempo_beats,
        "drums": analysis_results.get("drums", {}),
        "melody": analysis_results.get("melody", {}),
        "bass": analysis_results.get("bass", {}),
        "chords": chords,
        "key": chords.get("key") or config.get("analysis", {}).get("key_guess"),
    }


def load_stems_from_project(project: ProjectManager) -> Dict[str, np.ndarray]:
    """Load separated stem WAV files from a project directory."""
    stems: Dict[str, np.ndarray] = {}
    stems_dir = project.project_path / "stems"
    if not stems_dir.exists():
        return stems

    for wav_path in stems_dir.glob("*.wav"):
        audio, sr = load_audio_file(wav_path)
        stems[wav_path.stem] = audio

    return stems


def get_stem_audio_for_analysis(
    kind: str,
    stems: Dict[str, np.ndarray],
    full_audio: np.ndarray,
    project: Optional[ProjectManager] = None,
) -> np.ndarray:
    """Return the best audio source for analysis (loads from disk if not in memory)."""

    def _load_stem(name: str) -> Optional[np.ndarray]:
        if name in stems:
            return stems[name]
        if project is not None:
            path = project.stems_path / f"{name}.wav"
            if path.exists():
                audio, _ = load_audio_file(path)
                return audio
        return None

    if kind == "drums":
        drums = _load_stem("drums")
        return drums if drums is not None else full_audio
    if kind == "bass":
        bass = _load_stem("bass")
        return bass if bass is not None else full_audio
    if kind == "melody":
        melody = _load_stem("other")
        if melody is None:
            melody = _load_stem("vocals")
        return melody if melody is not None else full_audio
    if kind == "chords":
        other = _load_stem("other")
        bass = _load_stem("bass")
        if other is not None and bass is not None:
            min_len = min(len(other), len(bass))
            return other[:min_len] + bass[:min_len]
        return full_audio
    return full_audio


def _quantize_time_to_beats(time: float, beat_times: List[float]) -> float:
    """Snap a time to the nearest beat."""
    if not beat_times:
        return time
    return min(beat_times, key=lambda b: abs(b - time))


def safe_extract_melody(
    audio: np.ndarray,
    sr: int,
    output_path: str,
    beat_times: Optional[List[float]] = None,
    quantize: bool = False,
) -> Dict[str, Any]:
    """Extract melody using librosa pYIN (TensorFlow-free, Apple Silicon safe)."""
    f0, voiced_flag, voiced_probs = librosa.pyin(
        audio,
        fmin=librosa.note_to_hz("C2"),
        fmax=librosa.note_to_hz("C7"),
        sr=sr,
    )

    times = librosa.times_like(f0, sr=sr)
    notes: List[Dict[str, Any]] = []
    current_note: Optional[Dict[str, Any]] = None
    min_duration = 0.1

    for i, (pitch, voiced) in enumerate(zip(f0, voiced_flag)):
        if voiced and not np.isnan(pitch):
            midi_pitch = int(round(librosa.hz_to_midi(pitch)))
            time = float(times[i])

            if current_note is None:
                current_note = {
                    "pitch": midi_pitch,
                    "start_time": time,
                    "velocity": 80,
                    "confidence": float(voiced_probs[i]) if voiced_probs is not None else 0.8,
                }
            elif current_note["pitch"] != midi_pitch:
                current_note["end_time"] = time
                current_note["duration"] = time - current_note["start_time"]
                if current_note["duration"] >= min_duration:
                    notes.append(current_note)
                current_note = {
                    "pitch": midi_pitch,
                    "start_time": time,
                    "velocity": 80,
                    "confidence": float(voiced_probs[i]) if voiced_probs is not None else 0.8,
                }
        elif current_note is not None:
            current_note["end_time"] = float(times[i])
            current_note["duration"] = float(times[i]) - current_note["start_time"]
            if current_note["duration"] >= min_duration:
                notes.append(current_note)
            current_note = None

    tempo, _ = librosa.beat.beat_track(y=audio, sr=sr)
    if isinstance(tempo, np.ndarray):
        tempo = float(tempo.item())
    else:
        tempo = float(tempo)

    if quantize and beat_times:
        for note in notes:
            note["start_time"] = _quantize_time_to_beats(note["start_time"], beat_times)
            if "end_time" in note:
                note["end_time"] = _quantize_time_to_beats(note["end_time"], beat_times)
                note["duration"] = note["end_time"] - note["start_time"]

    create_midi_from_notes(notes, tempo, output_path)

    return {
        "midi_path": output_path,
        "notes": notes,
        "statistics": {
            "total_notes": len(notes),
            "avg_duration": float(np.mean([n["duration"] for n in notes])) if notes else 0.0,
            "avg_confidence": float(np.mean([n.get("confidence", 0.8) for n in notes])) if notes else 0.0,
        },
        "method": "librosa_pyin",
    }


def discover_strudel_gallery() -> List[Dict[str, str]]:
    """Discover curated Strudel HTML/JS packs under projects/."""
    gallery: List[Dict[str, str]] = []
    if not PROJECTS_DIR.exists():
        return gallery

    pack_dirs = [
        ("WiredUp", "WiredUp Beats"),
        ("LTW_Strudel_Vol_2", "LTW Strudel Vol 2"),
        ("My_Original_Beats", "Original Beats"),
    ]

    for folder, label in pack_dirs:
        pack_path = PROJECTS_DIR / folder
        if not pack_path.exists():
            continue

        strudel_dir = pack_path / "strudel"
        search_roots = [strudel_dir, pack_path] if strudel_dir.exists() else [pack_path]

        for root in search_roots:
            for html_path in sorted(root.glob("*.html")):
                js_path = html_path.with_suffix(".js")
                gallery.append({
                    "pack": label,
                    "name": html_path.stem.replace("_", " ").title(),
                    "html_path": str(html_path),
                    "js_path": str(js_path) if js_path.exists() else "",
                })

    return gallery


def list_remix_files(strudel_dir: Path) -> List[Path]:
    """List remix_*.js files in a project's strudel folder."""
    if not strudel_dir.exists():
        return []
    return sorted(strudel_dir.glob("remix_*.js"))


def save_strudel_export(
    project: ProjectManager,
    code: str,
    filename: str,
    also_html: bool = True,
) -> Dict[str, str]:
    """Save Strudel code to project strudel folder, optionally with HTML player."""
    from src.strudel_integration import create_strudel_html

    out_dir = project.project_path / "strudel"
    out_dir.mkdir(parents=True, exist_ok=True)

    js_path = out_dir / filename
    with open(js_path, "w") as f:
        f.write(code)

    paths = {"js": str(js_path)}

    if also_html:
        html_path = out_dir / filename.replace(".js", ".html")
        title = filename.replace(".js", "").replace("_", " ").title()
        with open(html_path, "w") as f:
            f.write(create_strudel_html(code, title))
        paths["html"] = str(html_path)

    return paths
