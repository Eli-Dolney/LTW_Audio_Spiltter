"""
Melody extraction utilities for Beat & Stems Lab
Handles F0 detection and MIDI conversion
"""
import numpy as np
import librosa
import pretty_midi
from typing import Dict, List, Optional, Tuple
from scipy.signal import medfilt

try:
    import crepe
    CREPE_AVAILABLE = True
except ImportError:
    CREPE_AVAILABLE = False

from config import (
    SAMPLE_RATE, MELODY_CONF_THRESH, MELODY_MIN_NOTE_DURATION,
    MELODY_MAX_NOTE_DURATION, MIDI_VELOCITY_DEFAULT
)


def extract_melody_f0(audio: np.ndarray, sr: int = SAMPLE_RATE) -> Dict[str, np.ndarray]:
    """
    Extract fundamental frequency (F0) from audio using CREPE
    
    Args:
        audio: Audio data
        sr: Sample rate
        
    Returns:
        Dictionary containing F0 times, frequencies, and confidence
    """
    if not CREPE_AVAILABLE:
        raise ImportError("CREPE not available. Install with: pip install crepe")
    
    # Use CREPE for F0 detection
    time, frequency, confidence, _ = crepe.predict(
        audio, 
        sr, 
        step_size=int(1000 * sr / 16000),  # 10ms step size
        verbose=0
    )
    
    return {
        "times": time,
        "frequencies": frequency,
        "confidence": confidence
    }


def f0_to_midi_notes(
    f0_times: np.ndarray,
    f0_frequencies: np.ndarray,
    f0_confidence: np.ndarray,
    confidence_threshold: float = MELODY_CONF_THRESH,
    min_note_duration: float = MELODY_MIN_NOTE_DURATION,
    max_note_duration: float = MELODY_MAX_NOTE_DURATION
) -> List[Dict[str, any]]:
    """
    Convert F0 data to MIDI notes
    
    Args:
        f0_times: Time points for F0
        f0_frequencies: F0 frequencies in Hz
        f0_confidence: Confidence values
        confidence_threshold: Minimum confidence for valid pitch
        min_note_duration: Minimum note duration in seconds
        max_note_duration: Maximum note duration in seconds
        
    Returns:
        List of note dictionaries
    """
    notes = []
    
    # Filter by confidence
    confident_mask = f0_confidence > confidence_threshold
    confident_times = f0_times[confident_mask]
    confident_freqs = f0_frequencies[confident_mask]
    confident_conf = f0_confidence[confident_mask]
    
    if len(confident_times) == 0:
        return notes
    
    # Convert frequencies to MIDI note numbers
    midi_notes = librosa.hz_to_midi(confident_freqs)
    
    # Round to nearest integer
    midi_notes = np.round(midi_notes).astype(int)
    
    # Filter out invalid MIDI notes
    valid_mask = (midi_notes >= 0) & (midi_notes <= 127)
    valid_times = confident_times[valid_mask]
    valid_notes = midi_notes[valid_mask]
    valid_conf = confident_conf[valid_mask]
    
    if len(valid_times) == 0:
        return notes
    
    # Segment consecutive frames with same pitch into notes
    current_note = valid_notes[0]
    note_start = valid_times[0]
    note_confidence = [valid_conf[0]]
    
    for i in range(1, len(valid_times)):
        if valid_notes[i] == current_note:
            # Continue current note
            note_confidence.append(valid_conf[i])
        else:
            # End current note and start new one
            note_end = valid_times[i-1]
            note_duration = note_end - note_start
            
            # Only include notes within duration limits
            if min_note_duration <= note_duration <= max_note_duration:
                avg_confidence = np.mean(note_confidence)
                notes.append({
                    "pitch": int(current_note),
                    "start_time": float(note_start),
                    "end_time": float(note_end),
                    "duration": float(note_duration),
                    "confidence": float(avg_confidence),
                    "velocity": int(MIDI_VELOCITY_DEFAULT * avg_confidence)
                })
            
            # Start new note
            current_note = valid_notes[i]
            note_start = valid_times[i]
            note_confidence = [valid_conf[i]]
    
    # Handle last note
    if len(valid_times) > 0:
        note_end = valid_times[-1]
        note_duration = note_end - note_start
        
        if min_note_duration <= note_duration <= max_note_duration:
            avg_confidence = np.mean(note_confidence)
            notes.append({
                "pitch": int(current_note),
                "start_time": float(note_start),
                "end_time": float(note_end),
                "duration": float(note_duration),
                "confidence": float(avg_confidence),
                "velocity": int(MIDI_VELOCITY_DEFAULT * avg_confidence)
            })
    
    return notes


def quantize_notes_to_beats(
    notes: List[Dict[str, any]],
    beat_times: List[float],
    quantization_strength: float = 0.5
) -> List[Dict[str, any]]:
    """
    Quantize note timing to beat grid
    
    Args:
        notes: List of note dictionaries
        beat_times: List of beat times
        quantization_strength: How strongly to quantize (0-1)
        
    Returns:
        Quantized notes
    """
    if not beat_times or not notes:
        return notes
    
    quantized_notes = []
    
    for note in notes:
        # Find nearest beat for start and end times
        start_beat_idx = np.argmin(np.abs(np.array(beat_times) - note["start_time"]))
        end_beat_idx = np.argmin(np.abs(np.array(beat_times) - note["end_time"]))
        
        # Interpolate between original and quantized times
        quantized_start = beat_times[start_beat_idx]
        quantized_end = beat_times[end_beat_idx]
        
        # Apply quantization strength
        new_start = note["start_time"] * (1 - quantization_strength) + quantized_start * quantization_strength
        new_end = note["end_time"] * (1 - quantization_strength) + quantized_end * quantization_strength
        
        # Ensure minimum note duration
        if new_end - new_start < MELODY_MIN_NOTE_DURATION:
            new_end = new_start + MELODY_MIN_NOTE_DURATION
        
        quantized_note = note.copy()
        quantized_note["start_time"] = float(new_start)
        quantized_note["end_time"] = float(new_end)
        quantized_note["duration"] = float(new_end - new_start)
        
        quantized_notes.append(quantized_note)
    
    return quantized_notes


def create_midi_from_notes(
    notes: List[Dict[str, any]],
    tempo: float,
    output_path: str,
    track_name: str = "Melody"
) -> pretty_midi.PrettyMIDI:
    """
    Create MIDI file from note data
    
    Args:
        notes: List of note dictionaries
        tempo: Tempo in BPM
        output_path: Path to save MIDI file
        track_name: Name for the MIDI track
        
    Returns:
        PrettyMIDI object
    """
    # Create MIDI object
    midi = pretty_midi.PrettyMIDI(initial_tempo=tempo)
    
    # Create instrument
    instrument = pretty_midi.Instrument(program=0, name=track_name)  # Piano
    
    # Add notes
    for note_data in notes:
        note = pretty_midi.Note(
            velocity=note_data["velocity"],
            pitch=note_data["pitch"],
            start=note_data["start_time"],
            end=note_data["end_time"]
        )
        instrument.notes.append(note)
    
    # Add instrument to MIDI
    midi.instruments.append(instrument)
    
    # Save MIDI file
    midi.write(output_path)
    
    return midi


def extract_melody_to_midi(
    audio: np.ndarray,
    sr: int,
    output_path: str,
    tempo: Optional[float] = None,
    beat_times: Optional[List[float]] = None,
    quantize: bool = False,
    confidence_threshold: float = MELODY_CONF_THRESH
) -> Dict[str, any]:
    """
    Complete melody extraction pipeline
    
    Args:
        audio: Audio data
        sr: Sample rate
        output_path: Path to save MIDI file
        tempo: Tempo for MIDI file
        beat_times: Beat times for quantization
        quantize: Whether to quantize to beat grid
        confidence_threshold: Confidence threshold for F0
        
    Returns:
        Dictionary with extraction results
    """
    # Extract F0
    f0_data = extract_melody_f0(audio, sr)
    
    # Convert to MIDI notes
    notes = f0_to_midi_notes(
        f0_data["times"],
        f0_data["frequencies"],
        f0_data["confidence"],
        confidence_threshold
    )
    
    # Quantize if requested
    if quantize and beat_times:
        notes = quantize_notes_to_beats(notes, beat_times)
    
    # Get tempo if not provided
    if tempo is None:
        tempo, _ = librosa.beat.beat_track(y=audio, sr=sr)
    
    # Create MIDI file
    midi = create_midi_from_notes(notes, tempo, output_path)
    
    # Calculate statistics
    if notes:
        pitches = [note["pitch"] for note in notes]
        durations = [note["duration"] for note in notes]
        confidences = [note["confidence"] for note in notes]
        
        stats = {
            "total_notes": len(notes),
            "pitch_range": (min(pitches), max(pitches)),
            "avg_duration": np.mean(durations),
            "avg_confidence": np.mean(confidences),
            "total_duration": sum(durations)
        }
    else:
        stats = {
            "total_notes": 0,
            "pitch_range": (0, 0),
            "avg_duration": 0.0,
            "avg_confidence": 0.0,
            "total_duration": 0.0
        }
    
    return {
        "midi_path": output_path,
        "notes": notes,
        "f0_data": f0_data,
        "tempo": tempo,
        "statistics": stats
    }


def analyze_melody_characteristics(notes: List[Dict[str, any]]) -> Dict[str, any]:
    """
    Analyze melody characteristics
    
    Args:
        notes: List of note dictionaries
        
    Returns:
        Dictionary with melody analysis
    """
    if not notes:
        return {
            "pitch_range": 0,
            "melodic_intervals": [],
            "rhythm_diversity": 0.0,
            "melody_density": 0.0
        }
    
    pitches = [note["pitch"] for note in notes]
    durations = [note["duration"] for note in notes]
    
    # Pitch range
    pitch_range = max(pitches) - min(pitches)
    
    # Melodic intervals
    intervals = []
    for i in range(1, len(pitches)):
        interval = pitches[i] - pitches[i-1]
        intervals.append(interval)
    
    # Rhythm diversity (standard deviation of durations)
    rhythm_diversity = np.std(durations) if len(durations) > 1 else 0.0
    
    # Melody density (notes per second)
    total_duration = sum(durations)
    melody_density = len(notes) / total_duration if total_duration > 0 else 0.0
    
    return {
        "pitch_range": int(pitch_range),
        "melodic_intervals": intervals,
        "avg_interval": float(np.mean(intervals)) if intervals else 0.0,
        "rhythm_diversity": float(rhythm_diversity),
        "melody_density": float(melody_density),
        "total_notes": len(notes)
    }


def filter_notes_by_confidence(
    notes: List[Dict[str, any]],
    min_confidence: float = 0.7
) -> List[Dict[str, any]]:
    """
    Filter notes by confidence threshold
    
    Args:
        notes: List of note dictionaries
        min_confidence: Minimum confidence threshold
        
    Returns:
        Filtered notes
    """
    return [note for note in notes if note["confidence"] >= min_confidence]


def smooth_melody_line(notes: List[Dict[str, any]], window_size: int = 3) -> List[Dict[str, any]]:
    """
    Smooth melody line using median filtering
    
    Args:
        notes: List of note dictionaries
        window_size: Size of median filter window
        
    Returns:
        Smoothed notes
    """
    if len(notes) < window_size:
        return notes
    
    pitches = [note["pitch"] for note in notes]
    smoothed_pitches = medfilt(pitches, window_size)
    
    smoothed_notes = []
    for i, note in enumerate(notes):
        smoothed_note = note.copy()
        smoothed_note["pitch"] = int(smoothed_pitches[i])
        smoothed_notes.append(smoothed_note)
    
    return smoothed_notes
