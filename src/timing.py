"""
Timing analysis utilities for Beat & Stems Lab
Handles BPM detection, beat tracking, and downbeat detection
"""
import numpy as np
import librosa
from typing import Dict, List, Optional, Tuple
from scipy.signal import find_peaks

from config import SAMPLE_RATE, HOP_LENGTH


def analyze_tempo_and_beats(audio: np.ndarray, sr: int = SAMPLE_RATE) -> Dict[str, any]:
    """
    Analyze tempo and beat timing
    
    Args:
        audio: Audio data
        sr: Sample rate
        
    Returns:
        Dictionary containing tempo, beat times, and confidence
    """
    # Use librosa's tempo and beat tracking
    tempo, beat_frames = librosa.beat.beat_track(
        y=audio, 
        sr=sr, 
        hop_length=HOP_LENGTH,
        units='time'
    )
    
    # Convert beat frames to times
    beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=HOP_LENGTH)
    
    # Calculate beat confidence using onset strength
    onset_env = librosa.onset.onset_strength(y=audio, sr=sr, hop_length=HOP_LENGTH)
    
    # Convert beat times to frames for onset strength calculation
    beat_frames = librosa.time_to_frames(beat_times, sr=sr, hop_length=HOP_LENGTH)
    beat_strength = onset_env[beat_frames] if len(beat_frames) > 0 else np.array([])
    
    # Normalize beat strength
    beat_confidence = beat_strength / np.max(beat_strength) if len(beat_strength) > 0 else np.array([])
    
    # Detect downbeats (simplified heuristic)
    downbeat_times = detect_downbeats(beat_times, tempo, sr)
    
    return {
        "bpm": float(tempo),
        "beat_times": beat_times.tolist(),
        "beat_confidence": beat_confidence.tolist(),
        "downbeat_times": downbeat_times,
        "total_beats": len(beat_times),
        "duration": len(audio) / sr
    }


def detect_downbeats(beat_times: np.ndarray, tempo: float, sr: int) -> List[float]:
    """
    Detect downbeats using a simple heuristic
    
    Args:
        beat_times: Array of beat times
        tempo: Detected tempo in BPM
        sr: Sample rate
        
    Returns:
        List of downbeat times
    """
    if len(beat_times) == 0:
        return []
    
    # Calculate expected beat interval
    beat_interval = 60.0 / tempo
    
    # Group beats into measures (assuming 4/4 time)
    measures_per_beat = 4
    measure_duration = beat_interval * measures_per_beat
    
    downbeats = []
    current_measure_start = beat_times[0]
    
    for beat_time in beat_times:
        # Check if this beat is close to a measure boundary
        time_since_measure = (beat_time - current_measure_start) % measure_duration
        
        # Allow some tolerance (within 10% of beat interval)
        tolerance = beat_interval * 0.1
        
        if time_since_measure < tolerance or (measure_duration - time_since_measure) < tolerance:
            downbeats.append(float(beat_time))
            current_measure_start = beat_time
    
    return downbeats


def refine_beat_grid(beat_times: List[float], tempo: float, duration: float) -> List[float]:
    """
    Refine beat grid to be more regular
    
    Args:
        beat_times: Initial beat times
        tempo: Detected tempo
        duration: Audio duration
        
    Returns:
        Refined beat times
    """
    if not beat_times:
        return []
    
    beat_interval = 60.0 / tempo
    
    # Start from the first detected beat
    start_time = beat_times[0]
    
    # Generate regular grid
    refined_beats = []
    current_time = start_time
    
    while current_time <= duration:
        refined_beats.append(current_time)
        current_time += beat_interval
    
    return refined_beats


def analyze_rhythm_complexity(audio: np.ndarray, sr: int = SAMPLE_RATE) -> Dict[str, any]:
    """
    Analyze rhythm complexity and patterns
    
    Args:
        audio: Audio data
        sr: Sample rate
        
    Returns:
        Dictionary with rhythm analysis results
    """
    # Calculate onset strength
    onset_env = librosa.onset.onset_strength(y=audio, sr=sr, hop_length=HOP_LENGTH)
    
    # Find onset peaks
    onset_frames = librosa.onset.onset_detect(
        onset_envelope=onset_env,
        sr=sr,
        hop_length=HOP_LENGTH,
        units='time'
    )
    
    # Calculate rhythm features
    tempo, _ = librosa.beat.beat_track(y=audio, sr=sr, hop_length=HOP_LENGTH)
    
    # Calculate rhythm regularity
    if len(onset_frames) > 1:
        onset_intervals = np.diff(onset_frames)
        rhythm_regularity = 1.0 / (1.0 + np.std(onset_intervals))
    else:
        rhythm_regularity = 0.0
    
    # Calculate syncopation (simplified)
    syncopation = calculate_syncopation(onset_frames, tempo, sr)
    
    return {
        "onset_times": onset_frames.tolist(),
        "rhythm_regularity": float(rhythm_regularity),
        "syncopation": float(syncopation),
        "onset_count": len(onset_frames),
        "avg_onset_interval": float(np.mean(np.diff(onset_frames))) if len(onset_frames) > 1 else 0.0
    }


def calculate_syncopation(onset_times: np.ndarray, tempo: float, sr: int) -> float:
    """
    Calculate syncopation level (simplified)
    
    Args:
        onset_times: Onset times
        tempo: Tempo in BPM
        sr: Sample rate
        
    Returns:
        Syncopation score (0-1)
    """
    if len(onset_times) < 2:
        return 0.0
    
    beat_interval = 60.0 / tempo
    
    # Count onsets that don't align with strong beats
    syncopated_count = 0
    
    for onset_time in onset_times:
        # Find nearest beat
        beat_position = (onset_time % beat_interval) / beat_interval
        
        # Consider off-beat positions as syncopated
        if 0.25 < beat_position < 0.75:
            syncopated_count += 1
    
    return syncopated_count / len(onset_times)


def detect_time_signature(beat_times: List[float], tempo: float) -> Dict[str, any]:
    """
    Detect time signature from beat patterns
    
    Args:
        beat_times: Beat times
        tempo: Tempo in BPM
        
    Returns:
        Dictionary with time signature analysis
    """
    if len(beat_times) < 8:
        return {"numerator": 4, "denominator": 4, "confidence": 0.5}
    
    beat_interval = 60.0 / tempo
    
    # Analyze beat groupings
    beat_differences = np.diff(beat_times)
    
    # Look for patterns in beat intervals
    # This is a simplified approach - in practice, more sophisticated analysis would be needed
    
    # Count beats per measure by looking for longer intervals
    measure_boundaries = []
    for i, diff in enumerate(beat_differences):
        if diff > beat_interval * 1.5:  # Gap longer than 1.5 beats
            measure_boundaries.append(i + 1)
    
    if measure_boundaries:
        # Calculate beats per measure
        beats_per_measure = []
        prev_boundary = 0
        for boundary in measure_boundaries:
            beats_in_measure = boundary - prev_boundary
            beats_per_measure.append(beats_in_measure)
            prev_boundary = boundary
        
        # Add last measure
        beats_in_last_measure = len(beat_times) - prev_boundary
        if beats_in_last_measure > 0:
            beats_per_measure.append(beats_in_last_measure)
        
        # Most common beats per measure
        if beats_per_measure:
            numerator = max(set(beats_per_measure), key=beats_per_measure.count)
            confidence = beats_per_measure.count(numerator) / len(beats_per_measure)
        else:
            numerator = 4
            confidence = 0.5
    else:
        # Default to 4/4 if no clear pattern
        numerator = 4
        confidence = 0.3
    
    return {
        "numerator": numerator,
        "denominator": 4,  # Assume quarter note as beat unit
        "confidence": confidence
    }


def create_beat_grid(audio: np.ndarray, sr: int = SAMPLE_RATE) -> Dict[str, any]:
    """
    Create a complete beat grid analysis
    
    Args:
        audio: Audio data
        sr: Sample rate
        
    Returns:
        Complete beat grid analysis
    """
    # Get basic tempo and beats
    tempo_analysis = analyze_tempo_and_beats(audio, sr)
    
    # Refine beat grid
    refined_beats = refine_beat_grid(
        tempo_analysis["beat_times"],
        tempo_analysis["bpm"],
        tempo_analysis["duration"]
    )
    
    # Analyze rhythm complexity
    rhythm_analysis = analyze_rhythm_complexity(audio, sr)
    
    # Detect time signature
    time_signature = detect_time_signature(tempo_analysis["beat_times"], tempo_analysis["bpm"])
    
    return {
        "tempo": tempo_analysis["bpm"],
        "beat_times": refined_beats,
        "downbeat_times": tempo_analysis["downbeat_times"],
        "time_signature": time_signature,
        "rhythm_complexity": rhythm_analysis["rhythm_regularity"],
        "syncopation": rhythm_analysis["syncopation"],
        "duration": tempo_analysis["duration"],
        "total_beats": len(refined_beats)
    }


def validate_tempo_estimation(audio: np.ndarray, sr: int = SAMPLE_RATE) -> Dict[str, any]:
    """
    Validate tempo estimation with multiple methods
    
    Args:
        audio: Audio data
        sr: Sample rate
        
    Returns:
        Validation results
    """
    # Method 1: librosa beat_track
    tempo1, _ = librosa.beat.beat_track(y=audio, sr=sr, hop_length=HOP_LENGTH)
    
    # Method 2: librosa tempo
    tempo2 = librosa.beat.tempo(y=audio, sr=sr, hop_length=HOP_LENGTH)[0]
    
    # Method 3: onset-based tempo
    onset_env = librosa.onset.onset_strength(y=audio, sr=sr, hop_length=HOP_LENGTH)
    tempo3 = librosa.beat.tempo(onset_envelope=onset_env, sr=sr, hop_length=HOP_LENGTH)[0]
    
    tempos = [tempo1, tempo2, tempo3]
    
    # Calculate agreement
    mean_tempo = np.mean(tempos)
    std_tempo = np.std(tempos)
    agreement = 1.0 - (std_tempo / mean_tempo) if mean_tempo > 0 else 0.0
    
    return {
        "tempos": tempos,
        "mean_tempo": float(mean_tempo),
        "std_tempo": float(std_tempo),
        "agreement": float(agreement),
        "confidence": "high" if agreement > 0.8 else "medium" if agreement > 0.6 else "low"
    }
