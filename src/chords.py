"""
Chord analysis utilities for Beat & Stems Lab
Handles chord detection and progression analysis
"""
import numpy as np
import librosa
from typing import Dict, List, Optional, Tuple
from scipy.spatial.distance import cosine

from config import SAMPLE_RATE, HOP_LENGTH, CHORD_ANALYSIS_WINDOW, CHORD_CONFIDENCE_THRESH


# Chord templates for major and minor chords
CHORD_TEMPLATES = {
    'C': {'major': [1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0], 'minor': [1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0]},
    'C#': {'major': [0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0], 'minor': [0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0]},
    'D': {'major': [0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0], 'minor': [0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0]},
    'D#': {'major': [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0], 'minor': [0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0]},
    'E': {'major': [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1], 'minor': [1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1]},
    'F': {'major': [1, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0], 'minor': [1, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0]},
    'F#': {'major': [0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0], 'minor': [0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0]},
    'G': {'major': [0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 1], 'minor': [0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 1]},
    'G#': {'major': [1, 0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0], 'minor': [1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0]},
    'A': {'major': [1, 1, 0, 0, 1, 1, 0, 0, 0, 1, 0, 0], 'minor': [1, 1, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0]},
    'A#': {'major': [0, 1, 1, 0, 0, 1, 1, 0, 0, 0, 1, 0], 'minor': [0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 1, 0]},
    'B': {'major': [0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 0, 1], 'minor': [0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 1]}
}

NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


def extract_chroma_features(audio: np.ndarray, sr: int = SAMPLE_RATE) -> Tuple[np.ndarray, np.ndarray]:
    """
    Extract chroma features from audio
    
    Args:
        audio: Audio data
        sr: Sample rate
        
    Returns:
        Tuple of (chroma_features, times)
    """
    # Extract chroma features using librosa
    chroma = librosa.feature.chroma_cqt(
        y=audio, 
        sr=sr, 
        hop_length=HOP_LENGTH,
        bins_per_octave=12
    )
    
    # Get time points
    times = librosa.times_like(chroma, sr=sr, hop_length=HOP_LENGTH)
    
    return chroma, times


def detect_chord_from_chroma(chroma_vector: np.ndarray) -> Tuple[str, float]:
    """
    Detect chord from chroma vector using template matching
    
    Args:
        chroma_vector: 12-dimensional chroma vector
        
    Returns:
        Tuple of (chord_label, confidence)
    """
    # Normalize chroma vector
    chroma_norm = chroma_vector / (np.sum(chroma_vector) + 1e-8)
    
    best_chord = "N"  # No chord
    best_confidence = 0.0
    
    # Compare with all chord templates
    for root, qualities in CHORD_TEMPLATES.items():
        for quality, template in qualities.items():
            # Normalize template
            template_norm = np.array(template) / np.sum(template)
            
            # Calculate similarity (1 - cosine distance)
            similarity = 1 - cosine(chroma_norm, template_norm)
            
            if similarity > best_confidence:
                best_confidence = similarity
                best_chord = f"{root}{quality[0].upper()}"  # e.g., "Cm" for C minor
    
    return best_chord, best_confidence


def analyze_chord_progression(
    audio: np.ndarray, 
    sr: int = SAMPLE_RATE,
    window_size: float = CHORD_ANALYSIS_WINDOW,
    confidence_threshold: float = CHORD_CONFIDENCE_THRESH
) -> Dict[str, any]:
    """
    Analyze chord progression in audio
    
    Args:
        audio: Audio data
        sr: Sample rate
        window_size: Analysis window size in seconds
        confidence_threshold: Minimum confidence for chord detection
        
    Returns:
        Dictionary with chord analysis results
    """
    # Extract chroma features
    chroma, times = extract_chroma_features(audio, sr)
    
    # Analyze chords in windows
    window_samples = int(window_size * sr / HOP_LENGTH)
    chord_times = []
    chord_labels = []
    chord_confidences = []
    
    for i in range(0, chroma.shape[1], window_samples):
        # Get chroma for this window
        end_idx = min(i + window_samples, chroma.shape[1])
        window_chroma = np.mean(chroma[:, i:end_idx], axis=1)
        
        # Detect chord
        chord_label, confidence = detect_chord_from_chroma(window_chroma)
        
        # Only include chords above confidence threshold
        if confidence >= confidence_threshold:
            chord_times.append(times[i])
            chord_labels.append(chord_label)
            chord_confidences.append(confidence)
    
    # Merge consecutive identical chords
    merged_chords = merge_consecutive_chords(chord_times, chord_labels, chord_confidences)
    
    return {
        "chord_times": [c["time"] for c in merged_chords],
        "chord_labels": [c["label"] for c in merged_chords],
        "chord_confidences": [c["confidence"] for c in merged_chords],
        "total_chords": len(merged_chords),
        "chroma_features": chroma.tolist(),
        "chroma_times": times.tolist()
    }


def merge_consecutive_chords(
    times: List[float], 
    labels: List[str], 
    confidences: List[float]
) -> List[Dict[str, any]]:
    """
    Merge consecutive identical chords
    
    Args:
        times: Chord time points
        labels: Chord labels
        confidences: Chord confidences
        
    Returns:
        List of merged chord dictionaries
    """
    if not times:
        return []
    
    merged = []
    current_chord = {
        "time": times[0],
        "label": labels[0],
        "confidence": confidences[0]
    }
    
    for i in range(1, len(times)):
        if labels[i] == current_chord["label"]:
            # Same chord, update confidence
            current_chord["confidence"] = max(current_chord["confidence"], confidences[i])
        else:
            # Different chord, save current and start new
            merged.append(current_chord)
            current_chord = {
                "time": times[i],
                "label": labels[i],
                "confidence": confidences[i]
            }
    
    # Add last chord
    merged.append(current_chord)
    
    return merged


def detect_key_from_chroma(chroma: np.ndarray) -> Tuple[str, float]:
    """
    Detect musical key from chroma features
    
    Args:
        chroma: Chroma features
        
    Returns:
        Tuple of (key_label, confidence)
    """
    # Average chroma over time
    avg_chroma = np.mean(chroma, axis=1)
    
    # Key profiles (simplified)
    major_profile = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
    minor_profile = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
    
    best_key = "C"
    best_confidence = 0.0
    best_mode = "major"
    
    # Test all 12 keys in both major and minor
    for i in range(12):
        # Rotate profiles
        major_rotated = np.roll(major_profile, i)
        minor_rotated = np.roll(minor_profile, i)
        
        # Calculate correlations
        major_corr = np.corrcoef(avg_chroma, major_rotated)[0, 1]
        minor_corr = np.corrcoef(avg_chroma, minor_rotated)[0, 1]
        
        # Check major
        if major_corr > best_confidence:
            best_confidence = major_corr
            best_key = NOTE_NAMES[i]
            best_mode = "major"
        
        # Check minor
        if minor_corr > best_confidence:
            best_confidence = minor_corr
            best_key = NOTE_NAMES[i]
            best_mode = "minor"
    
    return f"{best_key} {best_mode}", best_confidence


def analyze_chord_complexity(chord_labels: List[str]) -> Dict[str, any]:
    """
    Analyze chord complexity and progression patterns
    
    Args:
        chord_labels: List of chord labels
        
    Returns:
        Dictionary with complexity analysis
    """
    if not chord_labels:
        return {
            "unique_chords": 0,
            "chord_changes": 0,
            "complexity_score": 0.0,
            "common_progressions": []
        }
    
    # Count unique chords
    unique_chords = len(set(chord_labels))
    
    # Count chord changes
    chord_changes = 0
    for i in range(1, len(chord_labels)):
        if chord_labels[i] != chord_labels[i-1]:
            chord_changes += 1
    
    # Calculate complexity score
    complexity_score = (unique_chords / len(chord_labels)) * (chord_changes / max(1, len(chord_labels) - 1))
    
    # Find common progressions (pairs)
    progressions = []
    for i in range(len(chord_labels) - 1):
        progression = f"{chord_labels[i]} → {chord_labels[i+1]}"
        progressions.append(progression)
    
    # Count progression frequencies
    from collections import Counter
    progression_counts = Counter(progressions)
    common_progressions = [{"progression": p, "count": c} for p, c in progression_counts.most_common(5)]
    
    return {
        "unique_chords": unique_chords,
        "chord_changes": chord_changes,
        "complexity_score": float(complexity_score),
        "common_progressions": common_progressions,
        "total_chords": len(chord_labels)
    }


def export_chord_progression(
    chord_times: List[float],
    chord_labels: List[str],
    output_path: str,
    format: str = "txt"
) -> str:
    """
    Export chord progression to file
    
    Args:
        chord_times: Chord time points
        chord_labels: Chord labels
        output_path: Output file path
        format: Output format ("txt" or "json")
        
    Returns:
        Path to exported file
    """
    if format == "txt":
        with open(output_path, 'w') as f:
            f.write("Chord Progression\n")
            f.write("=" * 20 + "\n\n")
            
            for i, (time, label) in enumerate(zip(chord_times, chord_labels)):
                f.write(f"{i+1:2d}. {time:6.2f}s - {label}\n")
    
    elif format == "json":
        import json
        data = {
            "chord_progression": [
                {"time": time, "chord": label, "index": i}
                for i, (time, label) in enumerate(zip(chord_times, chord_labels))
            ]
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    return output_path


def create_chord_summary(chord_labels: List[str]) -> Dict[str, any]:
    """
    Create summary statistics for chord progression
    
    Args:
        chord_labels: List of chord labels
        
    Returns:
        Dictionary with chord summary
    """
    if not chord_labels:
        return {
            "most_common_chord": "None",
            "chord_frequencies": {},
            "progression_length": 0
        }
    
    from collections import Counter
    chord_counts = Counter(chord_labels)
    
    return {
        "most_common_chord": chord_counts.most_common(1)[0][0],
        "chord_frequencies": dict(chord_counts),
        "progression_length": len(chord_labels),
        "unique_chord_count": len(chord_counts)
    }
