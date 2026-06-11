# Changelog

## 2.0.0 — Strudel Remix Engine

The biggest update yet: LTW Audio is now a full **local audio splitter + Strudel recreation tool** optimized for Mac M4 (Apple Silicon MPS).

### New in v2

- **Remix Engine** — 8 data-driven style presets (phat analog, glitch, lo-fi, trance, nostalgia, UK garage, phonk, house)
- **Remix Lab** — In-app UI to toggle layers, pick sounds, dial variation intensity, reroll seeds, preview live, and download `.js`
- **Stem Slice Playback** — Chop real separated stems by bar and play actual audio in Strudel via `samples()`
- **Higher-fidelity Strudel extraction** — Drum dynamics, note sustain (`c4@2`), swing detection, compressed mini-notation, per-section patterns, key-aware snapping
- **Building blocks + arrangement** — Solo any layer or play full song structure with `arrange()`
- **Voice isolation** — Dedicated vocal stem workflow
- **Create Studio** — Template browser and original beat gallery

### Platform

- **Demucs** is the default stem separator (MPS on Apple Silicon, CPU fallback)
- **librosa pYIN** for melody (no TensorFlow / CREPE required on Mac)
- Streamlit UI with embedded `@strudel/web` live player

### Dev / local-only (not in repo)

Personal projects, audio files, `GUIDE.md`, `legacy/`, and dev scripts stay local via `.gitignore`.

---

## 1.x — Initial release

- Streamlit GUI, Demucs/Spleeter separation, basic analysis, early Strudel pattern generation
