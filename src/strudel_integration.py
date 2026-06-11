"""
Strudel Integration Module for LTW Audio Splitter
Generates Strudel code patterns based on audio analysis with high-fidelity sequencing.
"""
import json
import math
import bisect
import urllib.parse
import numpy as np
from collections import Counter
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from .strudel_templates import get_strudel_templates
from .strudel_patterns import (
    compress_mini_notation,
    detect_swing,
    parse_key_to_scale,
    scale_hint_comment,
    snap_note_to_scale,
)


def bpm_to_cpm(bpm: float) -> float:
    """Strudel cycles per minute when one 4/4 bar equals one cycle (CPM = BPM / 4)."""
    if not isinstance(bpm, (int, float)) or bpm <= 0:
        return 30.0
    return float(bpm) / 4.0


# Default 1-bar fallbacks when analysis yields silence
_DEFAULT_DRUM = '"bd ~ sd ~ bd ~ sd ~"'
_DEFAULT_BASS = '"c2 ~ g1 ~ c2 ~ g1 ~"'
_DEFAULT_MELODY = '"c4 ~ e4 ~ g4 ~ e4 ~"'
_DEFAULT_CHORD = '"C Am F G"'


class StrudelPatternGenerator:
    """Generates Strudel patterns from audio analysis data using step sequencing"""
    
    def __init__(self):
        self.drum_samples = {
            "kick": "bd",
            "snare": "sd",
            "hat": "hh",
            "hihat": "hh",
            "open_hat": "oh",
            "closed_hat": "hh",
            "crash": "cp",
            "ride": "rd",
        }
        self.templates = get_strudel_templates()
    
    def _time_to_grid(self, time_sec: float, beat_duration: float, steps_per_beat: int = 4, beat_times: Optional[List[float]] = None) -> int:
        """Convert time in seconds to grid index, using actual beat times if available"""
        if beat_times and len(beat_times) > 0:
            # Find the nearest beat
            idx = bisect.bisect_left(beat_times, time_sec)
            if idx == 0:
                nearest_beat = beat_times[0]
                beat_idx = 0
            elif idx == len(beat_times):
                nearest_beat = beat_times[-1]
                beat_idx = len(beat_times) - 1
            else:
                # Choose closer beat
                if abs(time_sec - beat_times[idx-1]) < abs(time_sec - beat_times[idx]):
                    nearest_beat = beat_times[idx-1]
                    beat_idx = idx - 1
                else:
                    nearest_beat = beat_times[idx]
                    beat_idx = idx
            
            # Calculate sub-beat position (16th notes within the beat)
            if beat_idx < len(beat_times) - 1:
                next_beat = beat_times[beat_idx + 1]
                beat_dur = next_beat - nearest_beat
                if beat_dur > 0:
                    sub_beat = (time_sec - nearest_beat) / beat_dur
                    sub_step = int(round(sub_beat * steps_per_beat))
                    sub_step = max(0, min(steps_per_beat - 1, sub_step))
                else:
                    sub_step = 0
            else:
                sub_step = 0
            
            return beat_idx * steps_per_beat + sub_step
        
        # Fallback to calculated beat duration
        if beat_duration <= 0: return 0
        return int(round((time_sec / beat_duration) * steps_per_beat))

    def _quantize_to_bars(
        self,
        events: List[Dict],
        tempo: float,
        duration: float,
        steps_per_beat: int = 4,
        beats_per_bar: int = 4,
        beat_times: Optional[List[float]] = None,
        use_durations: bool = False,
        use_gain: bool = False,
        snap_key: Optional[str] = None,
    ) -> Tuple[List[List[str]], List[List[float]]]:
        """
        Quantize events into bars of step strings plus optional gain grid.
        """
        beat_duration = 60.0 / tempo
        bar_duration = beat_duration * beats_per_bar
        steps_per_bar = steps_per_beat * beats_per_bar
        step_duration = beat_duration / steps_per_beat

        if duration <= 0:
            duration = 60

        root, scale = parse_key_to_scale(snap_key or "C major")

        if beat_times and len(beat_times) > 0:
            total_beats = len(beat_times)
            total_bars = math.ceil(total_beats / beats_per_bar)
        else:
            total_bars = math.ceil(duration / bar_duration)

        grid = [["~" for _ in range(steps_per_bar)] for _ in range(total_bars)]
        gain_grid = [[1.0 for _ in range(steps_per_bar)] for _ in range(total_bars)]
        occupied = [[False for _ in range(steps_per_bar)] for _ in range(total_bars)]

        for event in events:
            t = event.get("time", 0)
            val = event.get("value", "")
            if snap_key and val and val != "~":
                val = snap_note_to_scale(val, root, scale)

            global_step = self._time_to_grid(t, beat_duration, steps_per_beat, beat_times)
            bar_idx = global_step // steps_per_bar
            step_idx = global_step % steps_per_bar

            if not (0 <= bar_idx < total_bars):
                continue

            gain = float(event.get("gain", event.get("strength", 1.0)))
            dur_steps = 1
            if use_durations and event.get("duration"):
                dur_steps = max(1, int(round(event["duration"] / step_duration)))

            if dur_steps > 1 and use_durations:
                val = f"{val}@{dur_steps}"

            current = grid[bar_idx][step_idx]
            if current == "~" and not occupied[bar_idx][step_idx]:
                grid[bar_idx][step_idx] = val
                gain_grid[bar_idx][step_idx] = gain
                for ds in range(1, min(dur_steps, steps_per_bar - step_idx)):
                    occupied[bar_idx][step_idx + ds] = True
            elif current == "~":
                continue
            else:
                if current.startswith("[") and current.endswith("]"):
                    content = current[1:-1]
                    grid[bar_idx][step_idx] = f"[{content},{val}]"
                else:
                    grid[bar_idx][step_idx] = f"[{current},{val}]"
                if use_gain:
                    gain_grid[bar_idx][step_idx] = max(gain_grid[bar_idx][step_idx], gain)

        if not use_gain:
            gain_grid = [[1.0] * steps_per_bar for _ in range(total_bars)]

        return grid, gain_grid

    def _simplify_bar_pattern(
        self, steps: List[str], gains: Optional[List[float]] = None
    ) -> Tuple[str, str]:
        """Convert steps into compressed mini-notation and optional gain pattern."""
        compressed = compress_mini_notation(steps)
        pattern = f"\"{compressed}\""
        gain_pattern = ""
        if gains and any(g < 0.95 for g in gains):
            gain_str = " ".join(f"{g:.2f}" if g < 0.95 else "1" for g in gains)
            gain_pattern = f".gain(\"{gain_str}\")"
        return pattern, gain_pattern

    def _get_events_from_drums(self, drum_analysis: Dict[str, Any]) -> List[Dict]:
        drum_hits = drum_analysis.get("drum_hits", [])
        events = []
        for hit in drum_hits:
            dtype = hit.get("type")
            sample = self.drum_samples.get(dtype)
            if sample:
                events.append({
                    "time": hit["time"],
                    "value": sample,
                    "gain": hit.get("gain", hit.get("strength", 1.0)),
                })
        return events

    def _get_events_from_melody(self, melody_analysis: Dict[str, Any]) -> List[Dict]:
        notes = melody_analysis.get("notes", [])
        events = []
        for note in notes:
            midi_note = note.get("pitch")
            start_time = note.get("start_time")
            if midi_note is not None and start_time is not None:
                note_name = self._midi_to_strudel_note(midi_note)
                events.append({
                    "time": start_time,
                    "value": note_name,
                    "duration": note.get("duration", 0.1),
                })
        return events

    def _get_events_from_chords(self, chord_analysis: Dict[str, Any]) -> List[Dict]:
        times = chord_analysis.get("chord_times", [])
        labels = chord_analysis.get("chord_labels", [])
        events = []
        for t, label in zip(times, labels):
            clean_label = label.replace(":", "")
            events.append({"time": t, "value": clean_label})
        return events

    def _get_events_from_bass(self, bass_analysis: Dict[str, Any]) -> List[Dict]:
        notes = bass_analysis.get("notes", [])
        events = []
        for note in notes:
            midi_note = note.get("pitch")
            start_time = note.get("start_time")
            if midi_note is not None and start_time is not None:
                note_name = self._midi_to_strudel_note(midi_note)
                events.append({
                    "time": start_time,
                    "value": note_name,
                    "duration": note.get("duration", 0.1),
                })
        return events

    def _bars_to_pattern_strings(
        self, grid: List[List[str]], gain_grid: Optional[List[List[float]]] = None
    ) -> List[str]:
        patterns = []
        for i, bar in enumerate(grid):
            gains = gain_grid[i] if gain_grid else None
            pat, _ = self._simplify_bar_pattern(bar, gains)
            patterns.append(pat)
        return patterns

    def generate_drum_track(
        self,
        drum_analysis: Dict[str, Any],
        tempo: float,
        duration: float,
        beat_times: Optional[List[float]] = None,
    ) -> str:
        events = self._get_events_from_drums(drum_analysis)
        if not events:
            return 's("silence")'

        grid, gain_grid = self._quantize_to_bars(
            events, tempo, duration, beat_times=beat_times, use_gain=True
        )
        bar_parts = []
        for i, bar in enumerate(grid):
            pat, gain_pat = self._simplify_bar_pattern(bar, gain_grid[i])
            bar_parts.append(f"s({pat}){gain_pat}" if gain_pat else f"s({pat})")
        formatted_bars = ",\n  ".join(bar_parts)
        swing = detect_swing(events, tempo, beat_times)
        swing_line = f".swingBy({swing:.2f}, 8)" if swing else ""

        return f"""cat([
  {formatted_bars}
]).bank("RolandTR808"){swing_line}.gain(0.8)"""

    def generate_melody_track(
        self,
        melody_analysis: Dict[str, Any],
        tempo: float,
        duration: float,
        beat_times: Optional[List[float]] = None,
        key: Optional[str] = None,
    ) -> str:
        events = self._get_events_from_melody(melody_analysis)
        if not events:
            return 's("silence")'

        grid, _ = self._quantize_to_bars(
            events, tempo, duration, beat_times=beat_times,
            use_durations=True, snap_key=key,
        )
        bar_patterns = self._bars_to_pattern_strings(grid)
        formatted_bars = ",\n  ".join(bar_patterns)
        swing = detect_swing(events, tempo, beat_times)
        swing_line = f".swingBy({swing:.2f}, 8)" if swing else ""

        return f"""note(cat([
  {formatted_bars}
])){swing_line}.sound("triangle").lpf(2000).delay("0.25:0.5")"""

    def generate_chord_track(
        self,
        chord_analysis: Dict[str, Any],
        tempo: float,
        duration: float,
        beat_times: Optional[List[float]] = None,
    ) -> str:
        events = self._get_events_from_chords(chord_analysis)
        if not events:
            return 's("silence")'

        grid, _ = self._quantize_to_bars(
            events, tempo, duration, steps_per_beat=1, beat_times=beat_times
        )
        bar_patterns = [
            f"\"{compress_mini_notation(bar)}\"" for bar in grid
        ]
        formatted_bars = ",\n  ".join(bar_patterns)

        return f"""chord(cat([
  {formatted_bars}
])).sound("sawtooth").lpf(1000).room(0.3).sustain(2)"""

    def generate_bass_track(
        self,
        bass_analysis: Dict[str, Any],
        tempo: float,
        duration: float,
        beat_times: Optional[List[float]] = None,
        key: Optional[str] = None,
    ) -> str:
        events = self._get_events_from_bass(bass_analysis)
        if not events:
            return 's("silence")'

        grid, _ = self._quantize_to_bars(
            events, tempo, duration, beat_times=beat_times,
            use_durations=True, snap_key=key,
        )
        bar_patterns = self._bars_to_pattern_strings(grid)
        formatted_bars = ",\n  ".join(bar_patterns)
        swing = detect_swing(events, tempo, beat_times)
        swing_line = f".swingBy({swing:.2f}, 8)" if swing else ""

        return f"""note(cat([
  {formatted_bars}
])){swing_line}.sound("gm_synth_bass_1").lpf(400).gain(1.2)"""

    def _midi_to_strudel_note(self, midi_note: int) -> str:
        note_names = ['c', 'c#', 'd', 'd#', 'e', 'f', 'f#', 'g', 'g#', 'a', 'a#', 'b']
        octave = (int(midi_note) // 12) - 1
        note_name = note_names[int(midi_note) % 12]
        return f"{note_name}{octave}"

    def extract_most_common_pattern(
        self,
        events: List[Dict],
        tempo: float,
        duration: float,
        steps_per_beat: int = 4,
        beat_times: Optional[List[float]] = None,
        use_durations: bool = False,
        use_gain: bool = False,
        snap_key: Optional[str] = None,
        bar_indices: Optional[List[int]] = None,
    ) -> Tuple[str, str]:
        """Find the best 1-bar pattern; returns (pattern, gain_suffix)."""
        if not events:
            return "\"~\"", ""

        grid, gain_grid = self._quantize_to_bars(
            events, tempo, duration, steps_per_beat=steps_per_beat,
            beat_times=beat_times, use_durations=use_durations,
            use_gain=use_gain, snap_key=snap_key,
        )

        bar_data: List[Tuple[str, str, int]] = []
        for i, bar in enumerate(grid):
            if bar_indices is not None and i not in bar_indices:
                continue
            pat, gain_pat = self._simplify_bar_pattern(bar, gain_grid[i])
            bar_data.append((pat, gain_pat, i))

        if not bar_data:
            return "\"~\"", ""

        counter = Counter(pat for pat, _, _ in bar_data)
        best_pattern = "\"~\""
        best_gain = ""
        max_score = -1

        for pattern, count in counter.items():
            content = pattern.replace('"', "").strip()
            tokens = content.split()
            events_count = sum(1 for t in tokens if t != "~" and not t.startswith("~*"))
            score = 0 if events_count == 0 else count * (events_count ** 0.5)
            if score > max_score:
                max_score = score
                best_pattern = pattern
                for pat, gain_pat, _ in bar_data:
                    if pat == pattern:
                        best_gain = gain_pat
                        break

        return best_pattern, best_gain

    def extract_top_patterns(
        self,
        events: List[Dict],
        tempo: float,
        duration: float,
        steps_per_beat: int = 4,
        beat_times: Optional[List[float]] = None,
        count: int = 2,
        use_durations: bool = False,
        use_gain: bool = False,
        snap_key: Optional[str] = None,
        bar_indices: Optional[List[int]] = None,
    ) -> List[Tuple[str, str]]:
        """Return up to `count` distinct scored bar patterns as (pattern, gain_suffix)."""
        if not events:
            return [("\"~\"", "")] * count

        grid, gain_grid = self._quantize_to_bars(
            events, tempo, duration, steps_per_beat=steps_per_beat,
            beat_times=beat_times, use_durations=use_durations,
            use_gain=use_gain, snap_key=snap_key,
        )

        bar_strings: List[Tuple[str, str]] = []
        for i, bar in enumerate(grid):
            if bar_indices is not None and i not in bar_indices:
                continue
            bar_strings.append(self._simplify_bar_pattern(bar, gain_grid[i]))

        counter = Counter(pat for pat, _ in bar_strings)
        scored: List[Tuple[float, str, str]] = []
        pat_to_gain = {pat: gain for pat, gain in bar_strings}

        for pattern, cnt in counter.items():
            content = pattern.replace('"', "").strip()
            tokens = content.split()
            events_count = sum(1 for t in tokens if t not in ("~", ".") and not t.startswith("~*"))
            score = 0.0 if events_count == 0 else cnt * (events_count ** 0.5)
            scored.append((score, pattern, pat_to_gain.get(pattern, "")))

        scored.sort(key=lambda x: x[0], reverse=True)
        results: List[Tuple[str, str]] = []
        seen: set = set()
        for score, pattern, gain_pat in scored:
            if pattern in seen:
                continue
            if score <= 0 and results:
                break
            if score <= 0 and not results:
                continue
            results.append((pattern, gain_pat))
            seen.add(pattern)
            if len(results) >= count:
                break

        while len(results) < count:
            results.append(results[0] if results else ("\"~\"", ""))
        return results[:count]

    def _get_analysis_context(
        self, analysis_data: Dict[str, Any]
    ) -> Tuple[float, float, Optional[List[float]], str, float]:
        tempo = analysis_data.get("tempo", 120)
        duration = analysis_data.get("duration", 60)
        if not isinstance(tempo, (int, float)):
            tempo = 120.0
        if not isinstance(duration, (int, float)):
            duration = 60.0
        beat_times = analysis_data.get("beat_times")
        if not beat_times:
            beat_times = analysis_data.get("tempo_beats", {}).get("beat_times")
        key = analysis_data.get("key") or analysis_data.get("chords", {}).get("key", "unknown")
        return float(tempo), float(duration), beat_times, str(key), bpm_to_cpm(float(tempo))

    @staticmethod
    def _pattern_or_fallback(pattern: str, fallback: str) -> str:
        stripped = pattern.replace('"', "").strip()
        if not stripped or stripped == "~" or all(t == "~" for t in stripped.split()):
            return fallback
        return pattern

    def _extract_blocks(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract main + variant patterns, per-section patterns, and metadata."""
        tempo, duration, beat_times, key, cpm = self._get_analysis_context(analysis_data)

        drum_events = self._get_events_from_drums(analysis_data.get("drums", {}))
        melody_events = self._get_events_from_melody(analysis_data.get("melody", {}))
        bass_events = self._get_events_from_bass(analysis_data.get("bass", {}))
        chord_events = self._get_events_from_chords(analysis_data.get("chords", {}))

        d_main, d_gain = self.extract_top_patterns(
            drum_events, tempo, duration, beat_times=beat_times, use_gain=True
        )[0]
        d_var, d_var_gain = self.extract_top_patterns(
            drum_events, tempo, duration, beat_times=beat_times, use_gain=True
        )[1]

        m_main, _ = self.extract_top_patterns(
            melody_events, tempo, duration, beat_times=beat_times,
            use_durations=True, snap_key=key,
        )[0]
        m_var, _ = self.extract_top_patterns(
            melody_events, tempo, duration, beat_times=beat_times,
            use_durations=True, snap_key=key,
        )[1]

        if bass_events:
            b_main, _ = self.extract_top_patterns(
                bass_events, tempo, duration, beat_times=beat_times,
                use_durations=True, snap_key=key,
            )[0]
            b_var, _ = self.extract_top_patterns(
                bass_events, tempo, duration, beat_times=beat_times,
                use_durations=True, snap_key=key,
            )[1]
        else:
            b_main, b_var = "\"~\"", "\"~\""

        if chord_events:
            c_main, _ = self.extract_top_patterns(
                chord_events, tempo, duration, steps_per_beat=1, beat_times=beat_times
            )[0]
            c_var, _ = self.extract_top_patterns(
                chord_events, tempo, duration, steps_per_beat=1, beat_times=beat_times
            )[1]
        else:
            c_main, c_var = "\"~\"", "\"~\""

        d_main = self._pattern_or_fallback(d_main, _DEFAULT_DRUM)
        d_var = self._pattern_or_fallback(d_var, d_main)
        b_main = self._pattern_or_fallback(b_main, _DEFAULT_BASS)
        b_var = self._pattern_or_fallback(b_var, b_main)
        m_main = self._pattern_or_fallback(m_main, _DEFAULT_MELODY)
        m_var = self._pattern_or_fallback(m_var, m_main)
        c_main = self._pattern_or_fallback(c_main, _DEFAULT_CHORD)
        c_var = self._pattern_or_fallback(c_var, c_main)

        section_patterns = self._extract_section_patterns(
            analysis_data, drum_events, melody_events, bass_events, chord_events, key
        )

        drum_swing = detect_swing(drum_events, tempo, beat_times)
        melody_swing = detect_swing(melody_events, tempo, beat_times)

        return {
            "tempo": tempo,
            "duration": duration,
            "beat_times": beat_times,
            "key": key,
            "cpm": cpm,
            "scale_hint": scale_hint_comment(key),
            "drum_main": d_main,
            "drum_variant": d_var,
            "drum_gain": d_gain,
            "drum_var_gain": d_var_gain,
            "drum_swing": drum_swing,
            "melody_swing": melody_swing,
            "bass_main": b_main,
            "bass_variant": b_var,
            "melody_main": m_main,
            "melody_variant": m_var,
            "chord_main": c_main,
            "chord_variant": c_var,
            "section_patterns": section_patterns,
        }

    def _extract_section_patterns(
        self,
        analysis_data: Dict[str, Any],
        drum_events: List[Dict],
        melody_events: List[Dict],
        bass_events: List[Dict],
        chord_events: List[Dict],
        key: str,
    ) -> Dict[str, Dict[str, str]]:
        """Extract dominant patterns per section label (intro/verse/chorus)."""
        tempo, duration, beat_times, _, _ = self._get_analysis_context(analysis_data)
        sections = self.detect_sections_with_ranges(analysis_data)
        result: Dict[str, Dict[str, str]] = {}

        for sec in sections:
            label = sec["label"]
            bar_indices = sec["bar_indices"]
            if label in result:
                continue

            d_pat, d_gain = self.extract_most_common_pattern(
                drum_events, tempo, duration, beat_times=beat_times,
                use_gain=True, bar_indices=bar_indices,
            )
            b_pat, _ = self.extract_most_common_pattern(
                bass_events, tempo, duration, beat_times=beat_times,
                use_durations=True, snap_key=key, bar_indices=bar_indices,
            )
            m_pat, _ = self.extract_most_common_pattern(
                melody_events, tempo, duration, beat_times=beat_times,
                use_durations=True, snap_key=key, bar_indices=bar_indices,
            )
            c_pat, _ = self.extract_most_common_pattern(
                chord_events, tempo, duration, steps_per_beat=1,
                beat_times=beat_times, bar_indices=bar_indices,
            )

            result[label] = {
                "drums": self._pattern_or_fallback(d_pat, _DEFAULT_DRUM),
                "drums_gain": d_gain,
                "bass": self._pattern_or_fallback(b_pat, _DEFAULT_BASS),
                "melody": self._pattern_or_fallback(m_pat, _DEFAULT_MELODY),
                "chords": self._pattern_or_fallback(c_pat, _DEFAULT_CHORD),
            }

        return result

    def detect_sections_with_ranges(
        self, analysis_data: Dict[str, Any], max_sections: int = 12
    ) -> List[Dict[str, Any]]:
        """Return sections with bar counts, labels, and bar index ranges."""
        flat = self.detect_sections(analysis_data, max_sections)
        sections: List[Dict[str, Any]] = []
        bar_start = 0
        for bars, label in flat:
            sections.append({
                "bars": bars,
                "label": label,
                "bar_indices": list(range(bar_start, bar_start + bars)),
            })
            bar_start += bars
        return sections

    def detect_sections(
        self, analysis_data: Dict[str, Any], max_sections: int = 12
    ) -> List[Tuple[int, str]]:
        """Label bars by drum density and collapse into intro / verse / chorus sections."""
        default = [(4, "intro"), (8, "verse"), (4, "chorus"), (8, "verse"), (4, "chorus")]
        tempo, duration, beat_times, _, _ = self._get_analysis_context(analysis_data)
        drum_events = self._get_events_from_drums(analysis_data.get("drums", {}))

        if not drum_events:
            return default

        grid, _ = self._quantize_to_bars(drum_events, tempo, duration, beat_times=beat_times)
        densities = [sum(1 for t in bar if t != "~") for bar in grid]
        if not densities or max(densities) == 0:
            return default

        if len(densities) > 2:
            p33 = float(np.percentile(densities, 33))
            p66 = float(np.percentile(densities, 66))
        else:
            p33, p66 = 1.0, 3.0

        labels: List[str] = []
        for d in densities:
            if d <= p33:
                labels.append("intro")
            elif d <= p66:
                labels.append("verse")
            else:
                labels.append("chorus")

        sections: List[Tuple[int, str]] = []
        cur = labels[0]
        count = 1
        for lab in labels[1:]:
            if lab == cur:
                count += 1
            else:
                sections.append((count, cur))
                cur = lab
                count = 1
        sections.append((count, cur))

        while len(sections) > max_sections and len(sections) > 1:
            merge_idx = 0
            min_sum = sections[0][0] + sections[1][0]
            for i in range(len(sections) - 1):
                s = sections[i][0] + sections[i + 1][0]
                if s < min_sum:
                    min_sum = s
                    merge_idx = i
            a_bars, a_lab = sections[merge_idx]
            b_bars, b_lab = sections[merge_idx + 1]
            merged_lab = a_lab if a_bars >= b_bars else b_lab
            sections[merge_idx : merge_idx + 2] = [(a_bars + b_bars, merged_lab)]

        if not any(lab == "chorus" for _, lab in sections):
            sections.append((4, "chorus"))
        return sections

    def _blocks_sound_defs(self, blocks: Dict[str, Any]) -> str:
        """Shared let bindings for drums, bass, melody, chords with dynamics and sections."""
        drum_gain = blocks.get("drum_gain", "")
        drum_var_gain = blocks.get("drum_var_gain", "")
        drum_swing = blocks.get("drum_swing")
        melody_swing = blocks.get("melody_swing")
        swing_d = f".swingBy({drum_swing:.2f}, 8)" if drum_swing else ""
        swing_m = f".swingBy({melody_swing:.2f}, 8)" if melody_swing else ""

        section_defs = ""
        section_stacks = ""
        sp = blocks.get("section_patterns", {})
        for label in ("intro", "verse", "chorus"):
            if label not in sp:
                continue
            p = sp[label]
            gain = p.get("drums_gain", "")
            section_defs += f"""
let {label}_drum_pat = {p["drums"]}
let {label}_bass_pat = {p["bass"]}
let {label}_melody_pat = {p["melody"]}
let {label}_chord_pat = {p["chords"]}
let {label}_drums = s({label}_drum_pat).bank("RolandTR808"){gain}.gain(0.9)
let {label}_bass = note({label}_bass_pat).sound("gm_synth_bass_1").lpf(400).gain(1.1)
let {label}_melody = note({label}_melody_pat).sound("triangle").lpf(1800)
let {label}_chords = chord({label}_chord_pat).sound("sawtooth").lpf(900).room(0.4)
"""
            if label == "intro":
                section_stacks += f"let {label} = {label}_drums\n"
            elif label == "verse":
                section_stacks += f"let {label} = stack({label}_drums, {label}_bass){swing_d}\n"
            else:
                section_stacks += (
                    f"let {label} = stack({label}_drums, {label}_bass, "
                    f"{label}_melody, {label}_chords){swing_d}{swing_m}\n"
                )

        if not section_stacks:
            section_stacks = """let intro   = drums
let verse   = stack(drums, bass)
let chorus  = stack(drums, bass, melody, chords)
let breakdown = drumsB"""

        return f"""{blocks.get("scale_hint", "")}

// --- PATTERN DEFINITIONS (1 bar each) ---
let drum_pat = {blocks["drum_main"]}
let drum_alt = {blocks["drum_variant"]}
let bass_pat = {blocks["bass_main"]}
let bass_alt = {blocks["bass_variant"]}
let melody_pat = {blocks["melody_main"]}
let melody_alt = {blocks["melody_variant"]}
let chord_pat = {blocks["chord_main"]}
let chord_alt = {blocks["chord_variant"]}

// --- SOUND DESIGN ---
let drums  = s(drum_pat).bank("RolandTR808"){drum_gain}{swing_d}.gain(0.9)
let drumsB = s(drum_alt).bank("RolandTR808"){drum_var_gain}.gain(0.85)
let bass   = note(bass_pat).sound("gm_synth_bass_1").lpf(400).gain(1.1).clip(1.1)
let bassB  = note(bass_alt).sound("gm_synth_bass_1").lpf(350).gain(1.0)
let melody = note(melody_pat).sound("triangle").lpf(1800).delay("0.25:0.4"){swing_m}
let melodyB = note(melody_alt).sound("piano").lpf(2000).gain(0.9)
let chords = chord(chord_pat).sound("sawtooth").lpf(900).room(0.4).sustain(1.5)
let chordsB = chord(chord_alt).sound("sawtooth").lpf(700).room(0.5).sustain(2)
{section_defs}
// --- SECTION STACKS (per-section extracted patterns) ---
{section_stacks}let breakdown = drumsB"""

    def generate_building_blocks_code(self, analysis_data: Dict[str, Any]) -> str:
        """Named building blocks — solo any layer or play the full stack."""
        blocks = self._extract_blocks(analysis_data)
        tempo, cpm, key = blocks["tempo"], blocks["cpm"], blocks["key"]

        return f"""// 🧱 Building Blocks
// BPM: {tempo:.1f} | CPM: {cpm:.1f} (one 4/4 bar = one cycle) | Key: {key}

setcpm({cpm:.2f});

{self._blocks_sound_defs(blocks)}

// --- SOLO: uncomment ONE line to hear a single layer ---
// intro
// verse
// chorus
// drums
// drumsB
// bass
// melody
// chords

chorus
"""

    def generate_arrangement_code(self, analysis_data: Dict[str, Any]) -> str:
        """Song structure using arrange() — intro / verse / chorus from energy heuristics."""
        blocks = self._extract_blocks(analysis_data)
        tempo, cpm, key, duration = blocks["tempo"], blocks["cpm"], blocks["key"], blocks["duration"]
        sections = self.detect_sections(analysis_data)

        arrange_lines = []
        for bars, label in sections:
            if label == "intro":
                pat = "intro"
            elif label == "verse":
                pat = "verse"
            elif label == "chorus":
                pat = "chorus"
            else:
                pat = "breakdown"
            arrange_lines.append(f"  [{bars}, {pat}]")

        arrange_body = ",\n".join(arrange_lines)

        return f"""// 🎼 Arrangement
// BPM: {tempo:.1f} | CPM: {cpm:.1f} | Key: {key} | ~{duration:.0f}s analyzed

setcpm({cpm:.2f});

{self._blocks_sound_defs(blocks)}

arrange(
{arrange_body}
)
"""

    def generate_loops_code(self, analysis_data: Dict[str, Any]) -> str:
        """Alias for building blocks (legacy filename loops.js)."""
        return self.generate_building_blocks_code(analysis_data)

    def generate_remix_files(self, analysis_data: Dict[str, Any], output_dir: str):
        """Generate ready-to-use remix files via the remix engine."""
        from .remix_engine import generate_all_remix_files

        blocks = self._extract_blocks(analysis_data)
        generate_all_remix_files(blocks, output_dir)

    def generate_complete_song(self, analysis_data: Dict[str, Any]) -> str:
        """Deprecated alias — use generate_arrangement_code instead."""
        return self.generate_arrangement_code(analysis_data)

    # Compatibility methods for existing interface
    def save_strudel_code(self, code: str, path: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f: f.write(code)

    def create_strudel_html(self, code: str, title: str) -> str:
        return create_strudel_html(code, title)

def create_strudel_html(code: str, title: str) -> str:
    """Generate HTML player for Strudel code - uses Strudel REPL iframe for reliability"""
    # URL encode the code for Strudel REPL
    encoded_code = urllib.parse.quote(code)
    strudel_repl_url = f"https://strudel.cc/?code={encoded_code}"
    
    # Escape HTML special characters for display
    escaped_code = code.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ 
            background: #111; 
            color: #fff; 
            font-family: sans-serif; 
            padding: 20px; 
            margin: 0;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        h1 {{ 
            text-align: center; 
            color: #0f0; 
            margin-bottom: 20px;
        }}
        .tabs {{
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }}
        .tab-btn {{
            padding: 10px 20px;
            background: #333;
            color: #fff;
            border: 1px solid #555;
            cursor: pointer;
            border-radius: 5px 5px 0 0;
        }}
        .tab-btn.active {{
            background: #0f0;
            color: #000;
        }}
        .tab-content {{
            display: none;
        }}
        .tab-content.active {{
            display: block;
        }}
        iframe {{
            width: 100%;
            height: 800px;
            border: 2px solid #0f0;
            border-radius: 5px;
            background: #000;
        }}
        textarea {{
            width: 100%;
            height: 600px;
            background: #222;
            color: #0f0;
            font-family: monospace;
            border: 2px solid #0f0;
            font-size: 14px;
            padding: 10px;
            box-sizing: border-box;
        }}
        .copy-btn {{
            padding: 10px 20px;
            margin-top: 10px;
            background: #0f0;
            color: #000;
            border: none;
            cursor: pointer;
            font-weight: bold;
            border-radius: 5px;
        }}
        .copy-btn:hover {{
            background: #0a0;
        }}
        .tips {{
            background: #333;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 5px;
            border: 1px solid #555;
        }}
        .tips strong {{
            color: #0f0;
        }}
        .tips a {{
            color: #0ff;
            text-decoration: underline;
        }}
    </style>
    <script>
        function switchTab(tabName) {{
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => {{
                tab.classList.remove('active');
            }});
            document.querySelectorAll('.tab-btn').forEach(btn => {{
                btn.classList.remove('active');
            }});
            
            // Show selected tab
            document.getElementById('tab_' + tabName).classList.add('active');
            document.getElementById('btn_' + tabName).classList.add('active');
        }}
        
        function copyCode() {{
            const code = document.getElementById('code').value;
            navigator.clipboard.writeText(code).then(() => {{
                alert('Code copied to clipboard! Paste it into strudel.cc');
            }});
        }}
    </script>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        
        <div class="tips">
            <strong>💡 How to Use:</strong><br>
            • <strong>Option 1 (Recommended):</strong> Click "Strudel REPL" tab to open the code in Strudel's official REPL<br>
            • <strong>Option 2:</strong> Click "Copy Code" button, then paste into <a href="https://strudel.cc" target="_blank">strudel.cc</a><br>
            • Edit the code in the textarea and copy/paste to experiment with different sounds!
        </div>
        
        <div class="tabs">
            <button id="btn_repl" class="tab-btn active" onclick="switchTab('repl')">🎵 Strudel REPL</button>
            <button id="btn_code" class="tab-btn" onclick="switchTab('code')">📝 View Code</button>
        </div>
        
        <div id="tab_repl" class="tab-content active">
            <iframe src="{strudel_repl_url}" title="Strudel REPL"></iframe>
        </div>
        
        <div id="tab_code" class="tab-content">
            <textarea id="code">{escaped_code}</textarea>
            <button class="copy-btn" onclick="copyCode()">📋 Copy Code to Clipboard</button>
        </div>
    </div>
</body>
</html>"""

def generate_strudel_from_analysis(
    analysis_data: Dict[str, Any],
    output_dir: str,
    project_path: Optional[str] = None,
    project_name: Optional[str] = None,
    stem_paths: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    """Main entry point: building blocks, arrangement, remixes, stem slices."""
    generator = StrudelPatternGenerator()
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    files: Dict[str, str] = {}

    blocks_code = generator.generate_building_blocks_code(analysis_data)
    blocks_path = out_path / "building_blocks.js"
    generator.save_strudel_code(blocks_code, str(blocks_path))
    files["building_blocks"] = str(blocks_path)

    arr_code = generator.generate_arrangement_code(analysis_data)
    arr_path = out_path / "arrangement.js"
    generator.save_strudel_code(arr_code, str(arr_path))
    files["arrangement"] = str(arr_path)

    # Legacy keys for older UI/tests
    loops_path = out_path / "loops.js"
    generator.save_strudel_code(blocks_code, str(loops_path))
    files["loops"] = str(loops_path)

    html_code = generator.create_strudel_html(arr_code, "Arrangement")
    html_path = out_path / "strudel_player.html"
    with open(html_path, "w") as f:
        f.write(html_code)
    files["html"] = str(html_path)

    blocks_html = generator.create_strudel_html(blocks_code, "Building Blocks")
    blocks_html_path = out_path / "strudel_blocks.html"
    with open(blocks_html_path, "w") as f:
        f.write(blocks_html)
    files["blocks_html"] = str(blocks_html_path)
    files["loops_html"] = str(blocks_html_path)

    generator.generate_remix_files(analysis_data, str(out_path))
    for remix_path in sorted(out_path.glob("remix_*.js")):
        files[remix_path.stem] = str(remix_path)

    if project_path and project_name:
        try:
            from .stem_slices import generate_stem_assets

            stem_files = generate_stem_assets(
                Path(project_path),
                project_name,
                analysis_data,
                stem_paths=stem_paths,
            )
            files.update(stem_files)
        except Exception:
            pass

    return files
