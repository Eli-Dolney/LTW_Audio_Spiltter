"""
Data-driven Strudel remix engine: style presets, variations, and code generation.
"""
from __future__ import annotations

import random
from pathlib import Path
from typing import Any, Dict, List, Optional


# Layer effect chains keyed by preset id
REMIX_PRESETS: Dict[str, Dict[str, Any]] = {
    "phat_analog": {
        "name": "Phat Analog",
        "filename": "remix_1_phat_analog.js",
        "emoji": "🎛️",
        "global": "",
        "layers": {
            "drums": 'window.drums.clip(1.5).speed(0.9)',
            "bass": 'window.bass.sound("fmsynth").lpf(300).gain(1.3).clip(1.2)',
            "melody": 'window.melody.sound("celesta").room(0.8).delay("0.375:0.6")',
            "chords": 'window.chords.sound("juno").lpf(500).lpq(5)',
        },
    },
    "glitch": {
        "name": "Glitch / IDM",
        "filename": "remix_2_glitch.js",
        "emoji": "⚡",
        "global": "",
        "layers": {
            "drums": 'window.drums.segment(16).every(4, x=>x.fast(2)).bank("LinnDrum")',
            "bass": 'window.bass.segment(8).every(3, x=>x.speed(2)).sound("sawtooth").lpf(800)',
            "melody": 'window.melody.euclid(5,16).sound("pluck")',
            "chords": 'window.chords.arpeggiate().sound("pwm").speed(2).clip(1)',
        },
    },
    "lofi": {
        "name": "Lo-Fi Chill",
        "filename": "remix_3_lofi.js",
        "emoji": "☕",
        "global": '.slow(1.2)',
        "extra_layers": ['s("vinyl").gain(0.3)'],
        "layers": {
            "drums": 'window.drums.lpf(400).gain(1.2)',
            "bass": 'window.bass.sound("sine").lpf(300).gain(0.8).room(0.3)',
            "melody": 'window.melody.sound("rhodes").detune(0.5).vowel("a")',
            "chords": 'window.chords.sound("piano").room(2).hpf(200)',
        },
    },
    "trance": {
        "name": "Trance / EDM",
        "filename": "remix_4_trance.js",
        "emoji": "🔥",
        "global": '.fast(1.1)',
        "extra_layers": ['s("bd*4").bank("RolandTR909").gain(1.5).clip(1.2)'],
        "layers": {
            "drums": 'window.drums.hpf(800).gain(0.8)',
            "bass": 'window.bass.sound("sawtooth").lpf(400).gain(1.3).clip(1.1)',
            "melody": 'window.melody.sound("super").lpf(2000).lpq(5).delay(0.5).decay(0.1).sustain(0)',
            "chords": 'window.chords.sound("super").lpf(8000).room(2).sustain(1)',
        },
    },
    "nostalgia": {
        "name": "Nostalgia / TikTok",
        "filename": "remix_5_nostalgia.js",
        "emoji": "🌙",
        "global": '.slow(1.3)',
        "extra_layers": ['s("wind").gain(0.1)'],
        "layers": {
            "drums": 'window.drums.bank("LinnDrum").lpf(1200).room(0.5)',
            "bass": 'window.bass.sound("sine").lpf(200).gain(0.7).room(0.5)',
            "melody": 'window.melody.sound("vibraphone").room(3).delay("0.75:0.8").lpf(3000)',
            "chords": 'window.chords.sound("juno").vowel("o").lpf(800)',
        },
    },
    "uk_garage": {
        "name": "UK Garage",
        "filename": "remix_6_uk_garage.js",
        "emoji": "🇬🇧",
        "global": '.swingBy(0.25, 8)',
        "layers": {
            "drums": 'window.drums.bank("RolandTR909").struct("x*8").gain(1.1)',
            "bass": 'window.bass.sound("sawtooth").lpf(600).gain(1.2).clip(1.1)',
            "melody": 'window.melody.sound("gm_accordion").lpf(2500).delay("0.125:0.3")',
            "chords": 'window.chords.sound("juno").lpf(1200).room(0.6)',
        },
    },
    "phonk": {
        "name": "Phonk",
        "filename": "remix_7_phonk.js",
        "emoji": "💀",
        "global": '.slow(0.85)',
        "extra_layers": ['s("cowbell*2").gain(0.4)'],
        "layers": {
            "drums": 'window.drums.bank("RolandTR808").distort(0.8).gain(1.4)',
            "bass": 'window.bass.sound("sawtooth").lpf(200).gain(1.5).clip(1.3)',
            "melody": 'window.melody.sound("square").lpf(1500).gain(0.7)',
            "chords": 'window.chords.sound("sawtooth").lpf(400).room(0.8)',
        },
    },
    "house": {
        "name": "House",
        "filename": "remix_8_house.js",
        "emoji": "🏠",
        "global": '',
        "extra_layers": ['s("bd*4, ~, ~, ~").bank("RolandTR909").gain(1.2)'],
        "layers": {
            "drums": 'window.drums.bank("RolandTR909").hpf(400).gain(0.9)',
            "bass": 'window.bass.sound("sawtooth").lpf(500).gain(1.2)',
            "melody": 'window.melody.sound("gm_clarinet").lpf(3000).delay("0.25:0.4")',
            "chords": 'window.chords.sound("super").lpf(2000).room(1.5).sustain(0.5)',
        },
    },
}

# Per-layer sound overrides for Remix Lab
LAYER_SOUND_PRESETS: Dict[str, Dict[str, str]] = {
    "drums": {
        "808": '.bank("RolandTR808")',
        "909": '.bank("RolandTR909")',
        "linn": '.bank("LinnDrum")',
        "default": '.bank("RolandTR808")',
    },
    "bass": {
        "sub": '.sound("sine").lpf(200)',
        "analog": '.sound("fmsynth").lpf(300)',
        "808_bass": '.sound("gm_synth_bass_1").lpf(400)',
        "default": '.sound("gm_synth_bass_1").lpf(400)',
    },
    "melody": {
        "triangle": '.sound("triangle").lpf(1800)',
        "piano": '.sound("piano").lpf(2000)',
        "pluck": '.sound("pluck").lpf(2500)',
        "default": '.sound("triangle").lpf(1800)',
    },
    "chords": {
        "pad": '.sound("sawtooth").lpf(900).room(0.4)',
        "juno": '.sound("juno").lpf(800)',
        "super": '.sound("super").lpf(2000).room(1)',
        "default": '.sound("sawtooth").lpf(900).room(0.4)',
    },
}

VARIATION_TRANSFORMS = [
    ("degradeBy", lambda i: f'.degradeBy({0.1 + i * 0.15:.2f})'),
    ("euclid", lambda i: f'.euclid({3 + int(i * 4)}, 16)'),
    ("rev", lambda i: '.rev()'),
    ("jux", lambda i: '.jux(rev)'),
    ("sometimesBy", lambda i: f'.sometimesBy({0.2 + i * 0.2:.2f}, fast(2))'),
    ("ply", lambda i: f'.ply({2 + int(i * 2)})'),
    ("fast", lambda i: f'.fast({1.5 + i * 0.5:.1f})'),
    ("slow", lambda i: f'.slow({1.2 + i * 0.3:.1f})'),
]


def get_preset_ids() -> List[str]:
    return list(REMIX_PRESETS.keys())


def get_preset_choices() -> Dict[str, str]:
    return {pid: f"{p['emoji']} {p['name']}" for pid, p in REMIX_PRESETS.items()}


def build_definitions_block(blocks: Dict[str, Any]) -> str:
    """Build the shared definitions preamble for remix files."""
    tempo, cpm = blocks["tempo"], blocks["cpm"]
    from src.strudel_integration import StrudelPatternGenerator

    gen = StrudelPatternGenerator()
    sound_defs = gen._blocks_sound_defs(blocks)
    return f"""// BPM: {tempo:.1f} | CPM: {cpm:.1f}
setcpm({cpm:.2f});

{sound_defs}
// Remix helpers (window for REPL compatibility)
window.drums = drums;
window.bass = bass;
window.melody = melody;
window.chords = chords;
"""


def render_remix_code(
    blocks: Dict[str, Any],
    preset_id: str,
    enabled_layers: Optional[List[str]] = None,
    intensity: float = 0.0,
    seed: Optional[int] = None,
) -> str:
    """Render a remix stack from a preset with optional variation."""
    preset = REMIX_PRESETS.get(preset_id, REMIX_PRESETS["phat_analog"])
    enabled = enabled_layers or ["drums", "bass", "melody", "chords"]
    definitions = build_definitions_block(blocks)

    layer_exprs = []
    for layer in enabled:
        if layer in preset.get("layers", {}):
            expr = preset["layers"][layer]
            if intensity > 0:
                expr = apply_variation(expr, intensity, seed, layer)
            layer_exprs.append(f"  // {layer.title()}\n  {expr}")

    for extra in preset.get("extra_layers", []):
        layer_exprs.append(f"  {extra}")

    stack_body = ",\n\n".join(layer_exprs)
    global_mod = preset.get("global", "")

    return f"""// {preset['emoji']} STRUDEL REMIX: {preset['name'].upper()}
// FULL CODE (Copy ALL of this and paste into the player)

{definitions}

// REMIXED Playback
stack(
{stack_body}
){global_mod}
"""


def apply_variation(
    expr: str,
    intensity: float,
    seed: Optional[int],
    layer: str,
) -> str:
    """Apply seeded variation transforms based on intensity (0–1)."""
    if intensity <= 0:
        return expr

    rng = random.Random(seed)
    if seed is not None:
        rng = random.Random(seed + hash(layer) % 10000)

    num_transforms = max(1, int(intensity * 3))
    chosen = rng.sample(VARIATION_TRANSFORMS, min(num_transforms, len(VARIATION_TRANSFORMS)))

    result = expr
    for name, fn in chosen:
        result += fn(intensity)
    return result


def render_custom_remix(
    blocks: Dict[str, Any],
    global_preset_id: str = "phat_analog",
    layer_sounds: Optional[Dict[str, str]] = None,
    enabled_layers: Optional[List[str]] = None,
    intensity: float = 0.0,
    seed: Optional[int] = None,
) -> str:
    """Build a custom remix from Remix Lab controls."""
    enabled = enabled_layers or ["drums", "bass", "melody", "chords"]
    layer_sounds = layer_sounds or {}
    preset = REMIX_PRESETS.get(global_preset_id, REMIX_PRESETS["phat_analog"])
    definitions = build_definitions_block(blocks)

    layer_map = {
        "drums": "window.drums",
        "bass": "window.bass",
        "melody": "window.melody",
        "chords": "window.chords",
    }

    layer_exprs = []
    for layer in enabled:
        base = layer_map[layer]
        sound_key = layer_sounds.get(layer, "default")
        sound_mod = LAYER_SOUND_PRESETS.get(layer, {}).get(sound_key, "")

        if layer in preset.get("layers", {}):
            expr = preset["layers"][layer]
            # Replace window.X with base + sound mod if custom sound chosen
            if sound_key != "default" and sound_mod:
                expr = f"({base}{sound_mod})"
            if intensity > 0:
                expr = apply_variation(expr, intensity, seed, layer)
        else:
            expr = f"({base}{sound_mod})"
        layer_exprs.append(f"  {expr}")

    for extra in preset.get("extra_layers", []):
        layer_exprs.append(f"  {extra}")

    stack_body = ",\n\n".join(layer_exprs)
    global_mod = preset.get("global", "")

    return f"""// 🎛️ CUSTOM REMIX (Remix Lab)
// Seed: {seed} | Intensity: {intensity:.2f} | Preset: {preset['name']}

{definitions}

stack(
{stack_body}
){global_mod}
"""


def generate_all_remix_files(
    blocks: Dict[str, Any],
    output_dir: str,
) -> Dict[str, str]:
    """Write all preset remix files to output_dir."""
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    files: Dict[str, str] = {}

    for preset_id, preset in REMIX_PRESETS.items():
        code = render_remix_code(blocks, preset_id)
        filepath = out_path / preset["filename"]
        filepath.write_text(code)
        files[preset_id] = str(filepath)

    return files
