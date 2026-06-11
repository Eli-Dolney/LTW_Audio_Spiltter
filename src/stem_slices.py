"""
Beat-aligned stem slicing and Strudel samples() code generation.
"""
from __future__ import annotations

import json
import math
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import soundfile as sf

from config import SAMPLE_RATE
from src.io_utils import load_audio_file


DEFAULT_PORT = 8765
STEM_NAMES = ("drums", "bass", "other", "vocals")


def _bar_boundaries(
    beat_times: List[float],
    beats_per_bar: int = 4,
) -> List[Tuple[float, float]]:
    """Return (start, end) times for each bar from beat grid."""
    if not beat_times or len(beat_times) < 2:
        return []

    boundaries: List[Tuple[float, float]] = []
    for i in range(0, len(beat_times) - beats_per_bar, beats_per_bar):
        start = beat_times[i]
        end_idx = min(i + beats_per_bar, len(beat_times) - 1)
        end = beat_times[end_idx]
        if end > start:
            boundaries.append((start, end))

    return boundaries


def slice_stem_at_bars(
    audio: np.ndarray,
    sr: int,
    boundaries: List[Tuple[float, float]],
    output_dir: Path,
    stem_name: str,
) -> List[Dict[str, Any]]:
    """Slice audio at bar boundaries and write WAV files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    slices: List[Dict[str, Any]] = []

    for i, (start, end) in enumerate(boundaries):
        start_sample = max(0, int(start * sr))
        end_sample = min(len(audio), int(end * sr))
        if end_sample <= start_sample:
            continue

        segment = audio[start_sample:end_sample]
        filename = f"{stem_name}_{i:03d}.wav"
        filepath = output_dir / filename
        sf.write(str(filepath), segment, sr)

        slices.append({
            "id": f"{stem_name}_{i}",
            "filename": filename,
            "start": start,
            "end": end,
            "index": i,
        })

    return slices


def slice_stems_for_project(
    project_path: Path,
    beat_times: List[float],
    stem_paths: Optional[Dict[str, str]] = None,
    beats_per_bar: int = 4,
    max_bars: int = 64,
) -> Dict[str, Any]:
    """
    Slice all available stems at bar boundaries.
    Returns manifest with slice metadata.
    """
    slices_root = project_path / "slices"
    slices_root.mkdir(parents=True, exist_ok=True)

    stems_dir = project_path / "stems"
    boundaries = _bar_boundaries(beat_times, beats_per_bar)
    if max_bars and len(boundaries) > max_bars:
        boundaries = boundaries[:max_bars]

    manifest: Dict[str, Any] = {
        "beats_per_bar": beats_per_bar,
        "total_bars": len(boundaries),
        "stems": {},
    }

    if stem_paths:
        stem_files = {k: Path(v) for k, v in stem_paths.items() if Path(v).exists()}
    else:
        stem_files = {}
        if stems_dir.exists():
            for wav in stems_dir.glob("*.wav"):
                if wav.stem in STEM_NAMES or wav.stem != "voice":
                    stem_files[wav.stem] = wav

    for stem_name, stem_path in stem_files.items():
        if stem_name == "voice":
            continue
        audio, sr = load_audio_file(stem_path)
        stem_slice_dir = slices_root / stem_name
        slices = slice_stem_at_bars(audio, sr, boundaries, stem_slice_dir, stem_name)
        manifest["stems"][stem_name] = slices

    manifest_path = slices_root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    return manifest


def copy_slices_to_static(
    project_path: Path,
    project_name: str,
    static_root: Optional[Path] = None,
) -> Path:
    """Copy slice WAVs to static/ for Streamlit static serving."""
    static_root = static_root or Path("static") / "slices" / _safe_dirname(project_name)
    slices_src = project_path / "slices"

    if static_root.exists():
        shutil.rmtree(static_root)
    static_root.mkdir(parents=True, exist_ok=True)

    if slices_src.exists():
        shutil.copytree(slices_src, static_root, dirs_exist_ok=True)

    return static_root


def _safe_dirname(name: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in name)


def generate_serve_samples_py(
    project_path: Path,
    port: int = DEFAULT_PORT,
) -> Path:
    """Generate a local HTTP server script for strudel.cc sample loading."""
    script_path = project_path / "serve_samples.py"
    slices_dir = project_path / "slices"

    script = f'''#!/usr/bin/env python3
"""Serve stem slices with CORS for Strudel (strudel.cc) playback."""
import http.server
import socketserver
from pathlib import Path

PORT = {port}
SLICES_DIR = Path(__file__).parent / "slices"


class CORSHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(SLICES_DIR), **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()


if __name__ == "__main__":
    print(f"Serving slices from {{SLICES_DIR}}")
    print(f"Open strudel.cc and use baseUrl: http://localhost:{{PORT}}/")
    with socketserver.TCPServer(("", PORT), CORSHandler) as httpd:
        httpd.serve_forever()
'''
    script_path.write_text(script)
    script_path.chmod(0o755)
    return script_path


def _build_samples_map(manifest: Dict[str, Any]) -> Tuple[str, str]:
    """Build Strudel samples() map entries and pattern strings."""
    map_entries: List[str] = []
    pattern_parts: Dict[str, List[str]] = {}

    for stem_name, slices in manifest.get("stems", {}).items():
        if not slices:
            continue
        ids = []
        for sl in slices:
            sid = sl["id"]
            fname = sl["filename"]
            map_entries.append(f'  {sid}: "{fname}"')
            ids.append(sid)
        pattern_parts[stem_name] = ids

    samples_block = "samples({\n" + ",\n".join(map_entries) + "\n}, { baseUrl: BASE_URL })"

    return samples_block, pattern_parts


def generate_stem_remix_js(
    manifest: Dict[str, Any],
    analysis_data: Dict[str, Any],
    output_path: Path,
    base_url: str = "http://localhost:8765/",
    mode: str = "recreate",
) -> str:
    """
    Generate Strudel code using real stem slices.
    mode: 'recreate' (original order) or 'remix' (shuffled/euclidean)
    """
    from src.strudel_integration import StrudelPatternGenerator, bpm_to_cpm

    tempo = analysis_data.get("tempo", 120)
    cpm = bpm_to_cpm(float(tempo))
    key = analysis_data.get("key", "unknown")

    gen = StrudelPatternGenerator()
    blocks = gen._extract_blocks(analysis_data)
    synth_defs = gen._blocks_sound_defs(blocks)

    sample_maps: List[str] = []
    layer_code: List[str] = []

    for stem_name, slices in manifest.get("stems", {}).items():
        if not slices:
            continue
        ids = []
        map_lines = []
        for sl in slices:
            sid = sl["id"]
            fname = sl["filename"]
            map_lines.append(f'  {sid}: "{fname}"')
            ids.append(sid)

        stem_base = f"{base_url.rstrip('/')}/{stem_name}/"
        sample_maps.append(
            f'// {stem_name} samples\n'
            f'samples({{\n' + ",\n".join(map_lines) + f'\n}}, {{ baseUrl: "{stem_base}" }})'
        )

        id_pattern = " ".join(ids)
        if mode == "remix":
            pattern = f'"{id_pattern}".euclid(5, {len(ids)}).sometimes(rev)'
        else:
            pattern = f'"{id_pattern}"'

        layer_code.append(
            f'  // Real {stem_name} slices\n'
            f'  s({pattern}).gain(0.85)'
        )

    samples_block = "\n".join(sample_maps)
    layers_body = ",\n\n".join(layer_code) if layer_code else '  s("bd").gain(0)'

    code = f"""// 🎧 Stem Slice Remix — real audio from separated stems
// Mode: {mode} | BPM: {tempo:.1f} | Key: {key}
// Run serve_samples.py then paste this into strudel.cc

setcpm({cpm:.2f});

{samples_block}

// --- Synth layers (extracted patterns) ---
{synth_defs}

// --- Real stem slices + synth stack ---
stack(
  chorus,

{layers_body}
)
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(code)
    return code


def generate_stem_assets(
    project_path: Path,
    project_name: str,
    analysis_data: Dict[str, Any],
    stem_paths: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    """Full pipeline: slice stems, copy to static, write serve script + stem_remix.js."""
    beat_times = analysis_data.get("beat_times") or analysis_data.get("tempo_beats", {}).get("beat_times", [])
    if not beat_times:
        return {}

    manifest = slice_stems_for_project(project_path, beat_times, stem_paths)
    if not manifest.get("stems"):
        return {}

    static_path = copy_slices_to_static(project_path, project_name)
    serve_script = generate_serve_samples_py(project_path)

    strudel_dir = project_path / "strudel"
    recreate_path = strudel_dir / "stem_remix.js"
    remix_path = strudel_dir / "stem_remix_shuffle.js"

    generate_stem_remix_js(manifest, analysis_data, recreate_path, "http://localhost:8765/", "recreate")
    generate_stem_remix_js(manifest, analysis_data, remix_path, "http://localhost:8765/", "remix")

    # Streamlit-friendly variant (static serving path)
    st_path = strudel_dir / "stem_remix_streamlit.js"
    generate_stem_remix_js(manifest, analysis_data, st_path, f"/app/static/slices/{_safe_dirname(project_name)}/", "recreate")

    return {
        "manifest": str(project_path / "slices" / "manifest.json"),
        "stem_remix": str(recreate_path),
        "stem_remix_shuffle": str(remix_path),
        "stem_remix_streamlit": str(st_path),
        "serve_samples": str(serve_script),
        "static_slices": str(static_path),
    }
