"""
Visualization utilities for Beat & Stems Lab
Handles waveform and spectrogram plotting
"""
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import librosa
from typing import List, Optional, Tuple

from config import (
    N_FFT, HOP_LENGTH, WAVEFORM_HEIGHT, SPECTROGRAM_HEIGHT,
    SAMPLE_RATE
)


def create_waveform_plot(audio: np.ndarray, sr: int, title: str = "Waveform") -> go.Figure:
    """
    Create an interactive waveform plot
    
    Args:
        audio: Audio data
        sr: Sample rate
        title: Plot title
        
    Returns:
        Plotly figure object
    """
    time = np.linspace(0, len(audio) / sr, len(audio))
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=time,
        y=audio,
        mode='lines',
        name='Waveform',
        line=dict(color='#1f77b4', width=1),
        hovertemplate='Time: %{x:.2f}s<br>Amplitude: %{y:.3f}<extra></extra>'
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Time (seconds)",
        yaxis_title="Amplitude",
        height=WAVEFORM_HEIGHT,
        showlegend=False,
        hovermode='x unified'
    )
    
    return fig


def create_spectrogram_plot(audio: np.ndarray, sr: int, title: str = "Spectrogram") -> go.Figure:
    """
    Create an interactive spectrogram plot
    
    Args:
        audio: Audio data
        sr: Sample rate
        title: Plot title
        
    Returns:
        Plotly figure object
    """
    # Compute spectrogram
    D = librosa.stft(audio, n_fft=N_FFT, hop_length=HOP_LENGTH)
    S_db = librosa.amplitude_to_db(np.abs(D), ref=np.max)
    
    # Time and frequency axes
    times = librosa.times_like(S_db, sr=sr, hop_length=HOP_LENGTH)
    freqs = librosa.fft_frequencies(sr=sr, n_fft=N_FFT)
    
    fig = go.Figure()
    fig.add_trace(go.Heatmap(
        z=S_db,
        x=times,
        y=freqs,
        colorscale='Viridis',
        colorbar=dict(title="dB"),
        hovertemplate='Time: %{x:.2f}s<br>Freq: %{y:.0f}Hz<br>dB: %{z:.1f}<extra></extra>'
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Time (seconds)",
        yaxis_title="Frequency (Hz)",
        height=SPECTROGRAM_HEIGHT,
        yaxis=dict(type='log', range=[np.log10(20), np.log10(20000)])
    )
    
    return fig


def create_waveform_with_beats(
    audio: np.ndarray, 
    sr: int, 
    beat_times: Optional[List[float]] = None,
    title: str = "Waveform with Beat Grid"
) -> go.Figure:
    """
    Create waveform plot with beat grid overlay
    
    Args:
        audio: Audio data
        sr: Sample rate
        beat_times: List of beat times in seconds
        title: Plot title
        
    Returns:
        Plotly figure object
    """
    time = np.linspace(0, len(audio) / sr, len(audio))
    
    fig = go.Figure()
    
    # Main waveform
    fig.add_trace(go.Scatter(
        x=time,
        y=audio,
        mode='lines',
        name='Waveform',
        line=dict(color='#1f77b4', width=1),
        hovertemplate='Time: %{x:.2f}s<br>Amplitude: %{y:.3f}<extra></extra>'
    ))
    
    # Beat grid overlay
    if beat_times:
        for i, beat_time in enumerate(beat_times):
            if 0 <= beat_time <= time[-1]:
                # Alternate colors for visual distinction
                color = '#ff7f0e' if i % 4 == 0 else '#2ca02c'
                line_width = 2 if i % 4 == 0 else 1
                
                fig.add_vline(
                    x=beat_time,
                    line_dash="dash",
                    line_color=color,
                    line_width=line_width,
                    annotation_text=f"Beat {i+1}" if i % 4 == 0 else "",
                    annotation_position="top right"
                )
    
    fig.update_layout(
        title=title,
        xaxis_title="Time (seconds)",
        yaxis_title="Amplitude",
        height=WAVEFORM_HEIGHT,
        showlegend=False,
        hovermode='x unified'
    )
    
    return fig


def create_multi_stem_comparison(
    stems: dict, 
    sr: int, 
    title: str = "Stem Comparison"
) -> go.Figure:
    """
    Create comparison plot of multiple stems
    
    Args:
        stems: Dictionary of {stem_name: audio_data}
        sr: Sample rate
        title: Plot title
        
    Returns:
        Plotly figure object
    """
    fig = make_subplots(
        rows=len(stems), 
        cols=1,
        subplot_titles=list(stems.keys()),
        vertical_spacing=0.05
    )
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    
    for i, (stem_name, audio) in enumerate(stems.items()):
        time = np.linspace(0, len(audio) / sr, len(audio))
        color = colors[i % len(colors)]
        
        fig.add_trace(
            go.Scatter(
                x=time,
                y=audio,
                mode='lines',
                name=stem_name,
                line=dict(color=color, width=1),
                showlegend=False
            ),
            row=i+1, col=1
        )
    
    fig.update_layout(
        title=title,
        height=200 * len(stems),
        showlegend=False
    )
    
    # Update all x-axes
    for i in range(len(stems)):
        fig.update_xaxes(title_text="Time (seconds)", row=i+1, col=1)
        fig.update_yaxes(title_text="Amplitude", row=i+1, col=1)
    
    return fig


def create_melody_visualization(
    audio: np.ndarray,
    sr: int,
    f0_times: np.ndarray,
    f0_frequencies: np.ndarray,
    f0_confidence: np.ndarray,
    title: str = "Melody Analysis"
) -> go.Figure:
    """
    Create melody visualization with pitch track overlay
    
    Args:
        audio: Audio data
        sr: Sample rate
        f0_times: Time points for F0
        f0_frequencies: F0 frequencies in Hz
        f0_confidence: Confidence values for F0
        title: Plot title
        
    Returns:
        Plotly figure object
    """
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=["Waveform", "Pitch Track"],
        vertical_spacing=0.1
    )
    
    # Waveform
    time = np.linspace(0, len(audio) / sr, len(audio))
    fig.add_trace(
        go.Scatter(
            x=time,
            y=audio,
            mode='lines',
            name='Waveform',
            line=dict(color='#1f77b4', width=1),
            showlegend=False
        ),
        row=1, col=1
    )
    
    # Pitch track
    # Filter by confidence
    confident_mask = f0_confidence > 0.5
    confident_times = f0_times[confident_mask]
    confident_freqs = f0_frequencies[confident_mask]
    
    fig.add_trace(
        go.Scatter(
            x=confident_times,
            y=confident_freqs,
            mode='lines+markers',
            name='Pitch Track',
            line=dict(color='#ff7f0e', width=2),
            marker=dict(size=4),
            showlegend=False
        ),
        row=2, col=1
    )
    
    fig.update_layout(
        title=title,
        height=600,
        showlegend=False
    )
    
    fig.update_xaxes(title_text="Time (seconds)", row=1, col=1)
    fig.update_yaxes(title_text="Amplitude", row=1, col=1)
    fig.update_xaxes(title_text="Time (seconds)", row=2, col=1)
    fig.update_yaxes(title_text="Frequency (Hz)", row=2, col=1, type='log')
    
    return fig


def create_chord_visualization(
    audio: np.ndarray,
    sr: int,
    chord_times: List[float],
    chord_labels: List[str],
    title: str = "Chord Analysis"
) -> go.Figure:
    """
    Create chord visualization with chord labels
    
    Args:
        audio: Audio data
        sr: Sample rate
        chord_times: Time points for chord changes
        chord_labels: Chord labels
        title: Plot title
        
    Returns:
        Plotly figure object
    """
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=["Waveform", "Chord Progression"],
        vertical_spacing=0.1
    )
    
    # Waveform
    time = np.linspace(0, len(audio) / sr, len(audio))
    fig.add_trace(
        go.Scatter(
            x=time,
            y=audio,
            mode='lines',
            name='Waveform',
            line=dict(color='#1f77b4', width=1),
            showlegend=False
        ),
        row=1, col=1
    )
    
    # Chord progression
    if chord_times and chord_labels:
        # Create chord regions
        for i in range(len(chord_times) - 1):
            start_time = chord_times[i]
            end_time = chord_times[i + 1]
            chord = chord_labels[i]
            
            fig.add_vrect(
                x0=start_time,
                x1=end_time,
                fillcolor="lightblue",
                opacity=0.3,
                layer="below",
                line_width=0,
                row=2, col=1
            )
            
            # Add chord label
            fig.add_annotation(
                x=(start_time + end_time) / 2,
                y=0.5,
                text=chord,
                showarrow=False,
                font=dict(size=12, color="black"),
                row=2, col=1
            )
    
    fig.update_layout(
        title=title,
        height=600,
        showlegend=False
    )
    
    fig.update_xaxes(title_text="Time (seconds)", row=1, col=1)
    fig.update_yaxes(title_text="Amplitude", row=1, col=1)
    fig.update_xaxes(title_text="Time (seconds)", row=2, col=1)
    fig.update_yaxes(title_text="Chords", row=2, col=1, range=[0, 1])
    
    return fig


def create_drum_visualization(
    audio: np.ndarray,
    sr: int,
    onset_times: List[float],
    drum_types: List[str],
    title: str = "Drum Analysis"
) -> go.Figure:
    """
    Create drum visualization with onset markers
    
    Args:
        audio: Audio data
        sr: Sample rate
        onset_times: Onset times in seconds
        drum_types: Types of drums detected
        title: Plot title
        
    Returns:
        Plotly figure object
    """
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=["Waveform", "Drum Onsets"],
        vertical_spacing=0.1
    )
    
    # Waveform
    time = np.linspace(0, len(audio) / sr, len(audio))
    fig.add_trace(
        go.Scatter(
            x=time,
            y=audio,
            mode='lines',
            name='Waveform',
            line=dict(color='#1f77b4', width=1),
            showlegend=False
        ),
        row=1, col=1
    )
    
    # Drum onsets
    colors = {'kick': '#d62728', 'snare': '#ff7f0e', 'hat': '#2ca02c'}
    
    for onset_time, drum_type in zip(onset_times, drum_types):
        color = colors.get(drum_type, '#1f77b4')
        
        fig.add_vline(
            x=onset_time,
            line_color=color,
            line_width=2,
            annotation_text=drum_type.upper(),
            annotation_position="top right",
            row=2, col=1
        )
    
    fig.update_layout(
        title=title,
        height=600,
        showlegend=False
    )
    
    fig.update_xaxes(title_text="Time (seconds)", row=1, col=1)
    fig.update_yaxes(title_text="Amplitude", row=1, col=1)
    fig.update_xaxes(title_text="Time (seconds)", row=2, col=1)
    fig.update_yaxes(title_text="Drum Onsets", row=2, col=1, range=[0, 1])
    
    return fig
