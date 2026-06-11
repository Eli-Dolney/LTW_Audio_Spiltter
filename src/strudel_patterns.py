"""
Pattern utilities for Strudel code generation: compression, swing, key snapping.
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

NOTE_NAMES = ["c", "c#", "d", "d#", "e", "f", "f#", "g", "g#", "a", "a#", "b"]

MAJOR_SCALE = [0, 2, 4, 5, 7, 9, 11]
MINOR_SCALE = [0, 2, 3, 5, 7, 8, 10]


def compress_mini_notation(steps: List[str]) -> str:
    """Collapse repeats in a step list into Strudel mini-notation."""
    if not steps:
        return "~"

    parts: List[str] = []
    i = 0
    n = len(steps)

    while i < n:
        token = steps[i]
        j = i + 1
        while j < n and steps[j] == token:
            j += 1
        count = j - i
        if count > 1:
            if token == "~":
                parts.append(f"~*{count}")
            else:
                parts.append(f"{token}*{count}")
        else:
            parts.append(token)
        i = j

    return " ".join(parts)


def format_step_value(value: str, duration_steps: int = 1, gain: Optional[float] = None) -> str:
    """Format a grid cell with optional @duration and gain suffix."""
    if value == "~":
        return "~"
    out = value
    if duration_steps > 1:
        out = f"{value}@{duration_steps}"
    if gain is not None and gain < 0.95:
        out = f"{out}@{gain:.2f}" if "@" not in out else out
    return out


def detect_swing(
    events: List[Dict],
    tempo: float,
    beat_times: Optional[List[float]] = None,
    steps_per_beat: int = 4,
) -> Optional[float]:
    """
    Detect swing amount from offbeat event timing.
    Returns swingBy factor (0–0.5) or None if straight.
    """
    if not events or tempo <= 0:
        return None

    beat_duration = 60.0 / tempo
    step_duration = beat_duration / steps_per_beat
    offsets: List[float] = []

    for event in events:
        t = event.get("time", 0)
        if beat_times and len(beat_times) > 1:
            import bisect

            idx = bisect.bisect_left(beat_times, t)
            if idx == 0:
                beat_start = beat_times[0]
            elif idx >= len(beat_times):
                beat_start = beat_times[-1]
            else:
                beat_start = (
                    beat_times[idx - 1]
                    if abs(t - beat_times[idx - 1]) < abs(t - beat_times[idx])
                    else beat_times[idx]
                )
            pos_in_beat = (t - beat_start) / beat_duration if beat_duration > 0 else 0
        else:
            pos_in_beat = (t % beat_duration) / beat_duration if beat_duration > 0 else 0

        pos_in_beat = pos_in_beat % 1.0
        step_idx = round(pos_in_beat * steps_per_beat) % steps_per_beat
        # Offbeat 8th positions in 16th grid: steps 2, 6, 10, 14
        if step_idx in (2, 6, 10, 14):
            straight_time = (step_idx / steps_per_beat) * beat_duration
            actual_offset = (t - beat_start) - straight_time if beat_times else 0
            if step_duration > 0:
                offsets.append(actual_offset / step_duration)

    if len(offsets) < 4:
        return None

    avg = sum(offsets) / len(offsets)
    if abs(avg) < 0.05:
        return None
    return max(0.05, min(0.45, abs(avg) * 0.5))


def parse_key_to_scale(key: str) -> Tuple[str, List[int]]:
    """Parse key string like 'C major' or 'Am' into root + scale intervals."""
    if not key or key == "unknown":
        return "c", MAJOR_SCALE

    key = key.strip()
    mode = "major"
    root = "c"

    lower = key.lower().replace(" ", "")
    if "minor" in lower or lower.endswith("m"):
        mode = "minor"
        lower = lower.replace("minor", "").replace("min", "").rstrip("m")

    for name in sorted(NOTE_NAMES, key=len, reverse=True):
        if lower.startswith(name.replace("#", "sharp").replace("b", "flat")):
            root = name
            break
        if lower.startswith(name):
            root = name
            break

    # Handle sharp names in key strings like "C#"
    for i, name in enumerate(NOTE_NAMES):
        if name.upper() in key.upper()[:3]:
            root = name
            break

    scale = MINOR_SCALE if mode == "minor" else MAJOR_SCALE
    return root, scale


def snap_note_to_scale(note_name: str, root: str, scale: List[int]) -> str:
    """Snap a note like 'f#4' to nearest scale degree."""
    m = re.match(r"([a-g]#?)(-?\d+)", note_name.lower())
    if not m:
        return note_name

    note, octave = m.group(1), int(m.group(2))
    try:
        note_idx = NOTE_NAMES.index(note)
    except ValueError:
        return note_name

    root_idx = NOTE_NAMES.index(root) if root in NOTE_NAMES else 0
    rel = (note_idx - root_idx) % 12

    if rel in scale:
        return note_name

    best_dist = 13
    best_note = note_idx
    for deg in scale:
        for delta in (-1, 0, 1):
            candidate = (root_idx + deg + delta * 12) % 12
            dist = min(abs(candidate - note_idx), 12 - abs(candidate - note_idx))
            if dist < best_dist:
                best_dist = dist
                best_note = candidate

    return f"{NOTE_NAMES[best_note]}{octave}"


def scale_hint_comment(key: str) -> str:
    """Comment hint for Strudel scale."""
    root, scale = parse_key_to_scale(key)
    mode = "minor" if scale == MINOR_SCALE else "major"
    return f'// Key hint: .scale("{root}:{mode}")'
