"""
Stem separation utilities for Beat & Stems Lab
Handles audio source separation using Spleeter and Demucs
"""
import os
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import librosa
import soundfile as sf

# Spleeter import - optional since we're using Demucs
SPLEETER_AVAILABLE = False
try:
    from spleeter.separator import Separator
    SPLEETER_AVAILABLE = True
except ImportError:
    pass

try:
    import torch
    from demucs.pretrained import get_model
    from demucs.apply import apply_model
    DEMUCS_AVAILABLE = True
except ImportError:
    DEMUCS_AVAILABLE = False

from config import (
    SAMPLE_RATE, EXPORT_SAMPLE_RATE, EXPORT_FORMAT,
    STEM_METHODS, STEM_METHOD_DEFAULT
)
from .io_utils import save_audio_file, get_stem_path


class StemSeparator:
    """Handles audio stem separation using various methods"""
    
    def __init__(self, method: str = STEM_METHOD_DEFAULT):
        self.method = method
        self.separator = None
        self.demucs_model = None
        
        # Initialize the appropriate separation method
        self._initialize_separator()
    
    def _initialize_separator(self):
        """Initialize the separation method"""
        if self.method.startswith("spleeter:"):
            if not SPLEETER_AVAILABLE:
                raise ImportError("Spleeter not available. Install with: pip install spleeter")
            
            # Extract the number of stems from method name
            stem_count = self.method.split(":")[1].replace("stems", "")
            self.separator = Separator(f'spleeter:{stem_count}stems')
            
        elif self.method.startswith("demucs:"):
            if not DEMUCS_AVAILABLE:
                raise ImportError("Demucs not available. Install with: pip install demucs")
            
            # Extract the number of stems from method name
            stem_count = self.method.split(":")[1].replace("stems", "")
            # Use the correct model name for Demucs
            if stem_count == "4":
                self.demucs_model = get_model('htdemucs')
            elif stem_count == "5":
                self.demucs_model = get_model('htdemucs_ft')
            else:
                self.demucs_model = get_model('htdemucs')
            
        else:
            raise ValueError(f"Unknown separation method: {self.method}")
    
    def separate_audio(self, audio: np.ndarray, sr: int) -> Dict[str, np.ndarray]:
        """
        Separate audio into stems
        
        Args:
            audio: Input audio data
            sr: Sample rate
            
        Returns:
            Dictionary of {stem_name: audio_data}
        """
        if self.method.startswith("spleeter:"):
            return self._separate_with_spleeter(audio, sr)
        elif self.method.startswith("demucs:"):
            return self._separate_with_demucs(audio, sr)
        else:
            raise ValueError(f"Unsupported method: {self.method}")
    
    def _separate_with_spleeter(self, audio: np.ndarray, sr: int) -> Dict[str, np.ndarray]:
        """Separate audio using Spleeter"""
        # Spleeter expects stereo input
        if len(audio.shape) == 1:
            audio_stereo = np.stack([audio, audio])
        else:
            audio_stereo = audio
        
        # Ensure correct sample rate
        if sr != SAMPLE_RATE:
            audio_stereo = librosa.resample(audio_stereo, orig_sr=sr, target_sr=SAMPLE_RATE)
        
        # Perform separation
        prediction = self.separator.separate(audio_stereo)
        
        # Convert to mono and normalize
        stems = {}
        for stem_name, stem_audio in prediction.items():
            # Convert stereo to mono by averaging channels
            if len(stem_audio.shape) > 1:
                stem_mono = np.mean(stem_audio, axis=0)
            else:
                stem_mono = stem_audio
            
            # Normalize
            stem_mono = librosa.util.normalize(stem_mono)
            stems[stem_name] = stem_mono
        
        return stems
    
    def _separate_with_demucs(self, audio: np.ndarray, sr: int) -> Dict[str, np.ndarray]:
        """Separate audio using Demucs"""
        # Demucs expects specific input format
        if len(audio.shape) == 1:
            audio_stereo = np.stack([audio, audio])
        else:
            audio_stereo = audio
        
        # Ensure correct sample rate
        if sr != SAMPLE_RATE:
            audio_stereo = librosa.resample(audio_stereo, orig_sr=sr, target_sr=SAMPLE_RATE)
        
        # Convert to torch tensor
        audio_tensor = torch.from_numpy(audio_stereo).unsqueeze(0)  # Add batch dimension
        
        # Perform separation
        with torch.no_grad():
            separated = apply_model(self.demucs_model, audio_tensor, device='cpu')[0]
        
        # Convert back to numpy and process
        stems = {}
        stem_names = ['drums', 'bass', 'other', 'vocals']
        if separated.shape[0] == 5:
            stem_names = ['drums', 'bass', 'other', 'vocals', 'piano']
        
        for i, stem_name in enumerate(stem_names):
            stem_audio = separated[i].numpy()
            
            # Convert stereo to mono
            if len(stem_audio.shape) > 1:
                stem_mono = np.mean(stem_audio, axis=0)
            else:
                stem_mono = stem_audio
            
            # Normalize
            stem_mono = librosa.util.normalize(stem_mono)
            stems[stem_name] = stem_mono
        
        return stems
    
    def get_stem_names(self) -> List[str]:
        """Get the names of stems that will be produced"""
        if self.method == "spleeter:2stems":
            return ["vocals", "other"]
        elif self.method == "spleeter:4stems":
            return ["vocals", "drums", "bass", "other"]
        elif self.method == "spleeter:5stems":
            return ["vocals", "drums", "bass", "piano", "other"]
        elif self.method == "demucs:4stems":
            return ["drums", "bass", "other", "vocals"]
        elif self.method == "demucs:5stems":
            return ["drums", "bass", "other", "vocals", "piano"]
        else:
            raise ValueError(f"Unknown method: {self.method}")


def separate_audio_file(
    audio_path: Path,
    output_dir: Path,
    method: str = STEM_METHOD_DEFAULT,
    project_name: str = "default"
) -> Dict[str, Path]:
    """
    Separate an audio file into stems and save them
    
    Args:
        audio_path: Path to input audio file
        output_dir: Directory to save stems
        method: Separation method to use
        project_name: Name of the project
        
    Returns:
        Dictionary of {stem_name: output_path}
    """
    # Load audio
    audio, sr = librosa.load(str(audio_path), sr=SAMPLE_RATE, mono=True)
    
    # Create separator
    separator = StemSeparator(method)
    
    # Perform separation
    stems = separator.separate_audio(audio, sr)
    
    # Save stems
    stem_paths = {}
    for stem_name, stem_audio in stems.items():
        output_path = output_dir / f"{stem_name}.{EXPORT_FORMAT}"
        save_audio_file(stem_audio, output_path, EXPORT_SAMPLE_RATE)
        stem_paths[stem_name] = output_path
    
    return stem_paths


def get_available_methods() -> Dict[str, str]:
    """Get available separation methods with descriptions"""
    methods = {}
    
    # Always include Spleeter methods
    methods.update({
        "spleeter:2stems": "Vocals + Other (Fast)",
        "spleeter:4stems": "Vocals + Drums + Bass + Other",
        "spleeter:5stems": "Vocals + Drums + Bass + Piano + Other"
    })
    
    # Include Demucs if available
    if DEMUCS_AVAILABLE:
        methods.update({
            "demucs:4stems": "Vocals + Drums + Bass + Other (High Quality)",
            "demucs:5stems": "Vocals + Drums + Bass + Piano + Other (High Quality)"
        })
    
    return methods


def estimate_separation_time(audio_duration: float, method: str) -> float:
    """
    Estimate separation time based on audio duration and method
    
    Args:
        audio_duration: Duration in seconds
        method: Separation method
        
    Returns:
        Estimated time in seconds
    """
    # Rough estimates based on method and duration
    if method.startswith("spleeter:"):
        # Spleeter is relatively fast
        return audio_duration * 0.5  # 0.5x realtime
    elif method.startswith("demucs:"):
        # Demucs is slower but higher quality
        return audio_duration * 2.0  # 2x realtime
    else:
        return audio_duration * 1.0  # Default estimate


def validate_separation_method(method: str) -> bool:
    """Check if a separation method is available and valid"""
    if method.startswith("spleeter:"):
        return SPLEETER_AVAILABLE
    elif method.startswith("demucs:"):
        return DEMUCS_AVAILABLE
    else:
        return False


def get_separation_quality_info(method: str) -> Dict[str, str]:
    """Get information about separation quality for a method"""
    info = {
        "spleeter:2stems": {
            "quality": "Good",
            "speed": "Fast",
            "description": "Basic vocal separation, good for most music"
        },
        "spleeter:4stems": {
            "quality": "Good",
            "speed": "Fast",
            "description": "Four-way separation, balanced quality and speed"
        },
        "spleeter:5stems": {
            "quality": "Good",
            "speed": "Fast",
            "description": "Five-way separation including piano"
        },
        "demucs:4stems": {
            "quality": "Excellent",
            "speed": "Slow",
            "description": "High-quality separation, best for final results"
        },
        "demucs:5stems": {
            "quality": "Excellent",
            "speed": "Slow",
            "description": "High-quality five-way separation"
        }
    }
    
    return info.get(method, {
        "quality": "Unknown",
        "speed": "Unknown",
        "description": "Unknown method"
    })
