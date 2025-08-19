"""
Drum analysis utilities for Beat & Stems Lab
Handles drum onset detection and basic MIDI drum track creation
"""
import numpy as np
import librosa
import pretty_midi
from typing import Dict, List, Optional, Tuple
from scipy.signal import find_peaks

from config import (
    SAMPLE_RATE, HOP_LENGTH, DRUM_THRESH, DRUM_MAPPING,
    DRUM_FREQ_BANDS, MIDI_DRUM_VELOCITY, MIDI_DRUM_DURATION
)


def detect_drum_onsets(audio: np.ndarray, sr: int = SAMPLE_RATE) -> Dict[str, any]:
    """
    Detect drum onsets from audio
    
    Args:
        audio: Audio data
        sr: Sample rate
        
    Returns:
        Dictionary with onset detection results
    """
    # Calculate onset strength
    onset_env = librosa.onset.onset_strength(y=audio, sr=sr, hop_length=HOP_LENGTH)
    
    # Detect onset frames
    onset_frames = librosa.onset.onset_detect(
        onset_envelope=onset_env,
        sr=sr,
        hop_length=HOP_LENGTH,
        units='time'
    )
    
    # Convert to times
    onset_times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=HOP_LENGTH)
    
    # Get onset strengths at detected times
    onset_frames = librosa.time_to_frames(onset_times, sr=sr, hop_length=HOP_LENGTH)
    onset_strengths = onset_env[onset_frames] if len(onset_frames) > 0 else np.array([])
    
    return {
        "onset_times": onset_times.tolist(),
        "onset_strengths": onset_strengths.tolist(),
        "onset_count": len(onset_times)
    }


def classify_drum_hits(
    audio: np.ndarray, 
    onset_times: List[float], 
    sr: int = SAMPLE_RATE
) -> List[Dict[str, any]]:
    """
    Classify drum hits by type (kick, snare, hat, etc.)
    
    Args:
        audio: Audio data
        onset_times: List of onset times
        sr: Sample rate
        
    Returns:
        List of classified drum hits
    """
    drum_hits = []
    
    for onset_time in onset_times:
        # Get audio segment around onset
        start_sample = max(0, int((onset_time - 0.05) * sr))
        end_sample = min(len(audio), int((onset_time + 0.1) * sr))
        
        if end_sample <= start_sample:
            continue
        
        segment = audio[start_sample:end_sample]
        
        # Analyze frequency content
        drum_type = classify_drum_segment(segment, sr)
        
        drum_hits.append({
            "time": onset_time,
            "type": drum_type,
            "start_sample": start_sample,
            "end_sample": end_sample
        })
    
    return drum_hits


def classify_drum_segment(segment: np.ndarray, sr: int) -> str:
    """
    Classify a drum segment by type
    
    Args:
        segment: Audio segment
        sr: Sample rate
        
    Returns:
        Drum type classification
    """
    if len(segment) == 0:
        return "unknown"
    
    # Calculate frequency spectrum
    fft = np.abs(np.fft.fft(segment))
    freqs = np.fft.fftfreq(len(segment), 1/sr)
    
    # Get positive frequencies only
    pos_mask = freqs > 0
    freqs = freqs[pos_mask]
    fft = fft[pos_mask]
    
    # Calculate energy in different frequency bands
    kick_energy = np.sum(fft[(freqs >= DRUM_FREQ_BANDS["kick"][0]) & (freqs <= DRUM_FREQ_BANDS["kick"][1])])
    snare_energy = np.sum(fft[(freqs >= DRUM_FREQ_BANDS["snare"][0]) & (freqs <= DRUM_FREQ_BANDS["snare"][1])])
    hat_energy = np.sum(fft[(freqs >= DRUM_FREQ_BANDS["hat"][0]) & (freqs <= DRUM_FREQ_BANDS["hat"][1])])
    
    # Normalize by total energy
    total_energy = kick_energy + snare_energy + hat_energy
    if total_energy == 0:
        return "unknown"
    
    kick_ratio = kick_energy / total_energy
    snare_ratio = snare_energy / total_energy
    hat_ratio = hat_energy / total_energy
    
    # Classify based on energy ratios
    if kick_ratio > DRUM_THRESH["kick_lowband"]:
        return "kick"
    elif snare_ratio > DRUM_THRESH["snare_mid"]:
        return "snare"
    elif hat_ratio > DRUM_THRESH["hat_high"]:
        return "hat"
    else:
        return "unknown"


def create_drum_midi(
    drum_hits: List[Dict[str, any]],
    tempo: float,
    output_path: str
) -> pretty_midi.PrettyMIDI:
    """
    Create MIDI drum track from drum hits
    
    Args:
        drum_hits: List of classified drum hits
        tempo: Tempo in BPM
        output_path: Path to save MIDI file
        
    Returns:
        PrettyMIDI object
    """
    # Create MIDI object
    midi = pretty_midi.PrettyMIDI(initial_tempo=tempo)
    
    # Create drum track (channel 9 for drums)
    drum_track = pretty_midi.Instrument(program=0, is_drum=True, name="Drums")
    
    # Add drum notes
    for hit in drum_hits:
        drum_type = hit["type"]
        
        if drum_type in DRUM_MAPPING:
            note = pretty_midi.Note(
                velocity=MIDI_DRUM_VELOCITY,
                pitch=DRUM_MAPPING[drum_type],
                start=hit["time"],
                end=hit["time"] + MIDI_DRUM_DURATION
            )
            drum_track.notes.append(note)
    
    # Add drum track to MIDI
    midi.instruments.append(drum_track)
    
    # Save MIDI file
    midi.write(output_path)
    
    return midi


def analyze_drum_pattern(drum_hits: List[Dict[str, any]], tempo: float) -> Dict[str, any]:
    """
    Analyze drum pattern characteristics
    
    Args:
        drum_hits: List of drum hits
        tempo: Tempo in BPM
        
    Returns:
        Dictionary with drum pattern analysis
    """
    if not drum_hits:
        return {
            "total_hits": 0,
            "hit_density": 0.0,
            "pattern_complexity": 0.0,
            "drum_distribution": {}
        }
    
    # Count hits by type
    hit_types = [hit["type"] for hit in drum_hits]
    from collections import Counter
    type_counts = Counter(hit_types)
    
    # Calculate hit density (hits per second)
    if drum_hits:
        duration = max(hit["time"] for hit in drum_hits) - min(hit["time"] for hit in drum_hits)
        hit_density = len(drum_hits) / duration if duration > 0 else 0.0
    else:
        hit_density = 0.0
    
    # Calculate pattern complexity (variety of hit types)
    pattern_complexity = len(type_counts) / len(drum_hits) if drum_hits else 0.0
    
    # Analyze timing patterns
    hit_times = [hit["time"] for hit in drum_hits]
    if len(hit_times) > 1:
        intervals = np.diff(hit_times)
        timing_regularity = 1.0 / (1.0 + np.std(intervals))
    else:
        timing_regularity = 0.0
    
    return {
        "total_hits": len(drum_hits),
        "hit_density": float(hit_density),
        "pattern_complexity": float(pattern_complexity),
        "timing_regularity": float(timing_regularity),
        "drum_distribution": dict(type_counts),
        "hit_times": hit_times
    }


def detect_drum_loop(drum_hits: List[Dict[str, any]], tempo: float) -> Dict[str, any]:
    """
    Detect drum loop patterns
    
    Args:
        drum_hits: List of drum hits
        tempo: Tempo in BPM
        
    Returns:
        Dictionary with loop analysis
    """
    if len(drum_hits) < 4:
        return {
            "loop_length": 0,
            "loop_confidence": 0.0,
            "repetitions": 0
        }
    
    # Calculate expected beat interval
    beat_interval = 60.0 / tempo
    
    # Group hits by beat position
    hit_times = [hit["time"] for hit in drum_hits]
    beat_positions = []
    
    for hit_time in hit_times:
        # Find position within beat
        beat_pos = (hit_time % beat_interval) / beat_interval
        beat_positions.append(beat_pos)
    
    # Look for repeating patterns
    # This is a simplified approach - more sophisticated pattern detection could be added
    
    # Count hits per beat position
    from collections import Counter
    position_counts = Counter([round(pos, 2) for pos in beat_positions])
    
    # Find most common positions
    common_positions = position_counts.most_common(4)
    
    # Estimate loop length (simplified)
    loop_length = len(common_positions)
    loop_confidence = sum(count for _, count in common_positions) / len(drum_hits)
    
    return {
        "loop_length": loop_length,
        "loop_confidence": float(loop_confidence),
        "common_positions": [pos for pos, _ in common_positions],
        "repetitions": int(loop_confidence * len(drum_hits) / loop_length) if loop_length > 0 else 0
    }


def create_drum_summary(drum_hits: List[Dict[str, any]]) -> Dict[str, any]:
    """
    Create summary statistics for drum analysis
    
    Args:
        drum_hits: List of drum hits
        
    Returns:
        Dictionary with drum summary
    """
    if not drum_hits:
        return {
            "most_common_drum": "None",
            "total_hits": 0,
            "unique_drums": 0
        }
    
    # Count hits by type
    hit_types = [hit["type"] for hit in drum_hits]
    from collections import Counter
    type_counts = Counter(hit_types)
    
    # Get timing information
    hit_times = [hit["time"] for hit in drum_hits]
    
    return {
        "most_common_drum": type_counts.most_common(1)[0][0] if type_counts else "None",
        "total_hits": len(drum_hits),
        "unique_drums": len(type_counts),
        "first_hit": min(hit_times) if hit_times else 0.0,
        "last_hit": max(hit_times) if hit_times else 0.0,
        "drum_distribution": dict(type_counts)
    }


def extract_drums_to_midi(
    audio: np.ndarray,
    sr: int,
    output_path: str,
    tempo: Optional[float] = None,
    confidence_threshold: float = 0.5
) -> Dict[str, any]:
    """
    Complete drum extraction pipeline
    
    Args:
        audio: Audio data
        sr: Sample rate
        output_path: Path to save MIDI file
        tempo: Tempo for MIDI file
        confidence_threshold: Confidence threshold for onset detection
        
    Returns:
        Dictionary with extraction results
    """
    # Detect onsets
    onset_results = detect_drum_onsets(audio, sr)
    
    # Filter by confidence
    onset_times = []
    onset_strengths = onset_results["onset_strengths"]
    
    for i, strength in enumerate(onset_strengths):
        if strength >= confidence_threshold:
            onset_times.append(onset_results["onset_times"][i])
    
    # Classify drum hits
    drum_hits = classify_drum_hits(audio, onset_times, sr)
    
    # Get tempo if not provided
    if tempo is None:
        tempo, _ = librosa.beat.beat_track(y=audio, sr=sr)
    
    # Create MIDI file
    midi = create_drum_midi(drum_hits, tempo, output_path)
    
    # Analyze pattern
    pattern_analysis = analyze_drum_pattern(drum_hits, tempo)
    loop_analysis = detect_drum_loop(drum_hits, tempo)
    summary = create_drum_summary(drum_hits)
    
    return {
        "midi_path": output_path,
        "drum_hits": drum_hits,
        "tempo": tempo,
        "pattern_analysis": pattern_analysis,
        "loop_analysis": loop_analysis,
        "summary": summary,
        "total_hits": len(drum_hits)
    }


def filter_drum_hits_by_type(
    drum_hits: List[Dict[str, any]], 
    drum_type: str
) -> List[Dict[str, any]]:
    """
    Filter drum hits by type
    
    Args:
        drum_hits: List of drum hits
        drum_type: Type to filter for
        
    Returns:
        Filtered drum hits
    """
    return [hit for hit in drum_hits if hit["type"] == drum_type]


def create_drum_visualization_data(drum_hits: List[Dict[str, any]]) -> Dict[str, any]:
    """
    Create data for drum visualization
    
    Args:
        drum_hits: List of drum hits
        
    Returns:
        Dictionary with visualization data
    """
    if not drum_hits:
        return {
            "times": [],
            "types": [],
            "colors": []
        }
    
    times = [hit["time"] for hit in drum_hits]
    types = [hit["type"] for hit in drum_hits]
    
    # Color mapping for different drum types
    color_map = {
        "kick": "#d62728",
        "snare": "#ff7f0e", 
        "hat": "#2ca02c",
        "unknown": "#1f77b4"
    }
    
    colors = [color_map.get(drum_type, "#1f77b4") for drum_type in types]
    
    return {
        "times": times,
        "types": types,
        "colors": colors
    }
