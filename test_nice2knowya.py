#!/usr/bin/env python3
"""Quick end-to-end test for Nice 2 Know Ya using existing stems."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.app_helpers import build_analysis_data_for_strudel, load_all_analysis_results
from src.drums import extract_drums_to_midi
from src.io_utils import (
    ProjectManager,
    get_midi_path,
    get_stem_path,
    load_audio_file,
    save_analysis_results,
)
from src.strudel_integration import generate_strudel_from_analysis

PROJECT_NAME = "Nice_2_Know_Ya_Full"


def main():
    project = ProjectManager(PROJECT_NAME)
    config = project.load_project_config()
    if not config:
        print(f"❌ Project not found: {PROJECT_NAME}")
        return 1

    print(f"🎵 Testing LTW Audio with: {PROJECT_NAME}")
    print(f"   Audio: {config.get('audio', {}).get('duration', 0):.1f}s")

    drum_stem = get_stem_path(project, "drums")
    if drum_stem.exists():
        print("\n🥁 Re-analyzing drums from separated stem (improved classifier)...")
        drum_audio, sr = load_audio_file(drum_stem)
        drum_results = extract_drums_to_midi(
            drum_audio,
            sr,
            str(get_midi_path(project, "drums_basic")),
            confidence_threshold=0.35,
        )
        save_analysis_results(project, "drums", drum_results)
        dist = drum_results["summary"].get("drum_distribution", {})
        print(f"   Hits: {drum_results['summary']['total_hits']}")
        print(f"   Distribution: {dist}")
        if drum_results["summary"]["total_hits"]:
            t0 = drum_results["summary"]["first_hit"]
            t1 = drum_results["summary"]["last_hit"]
            print(f"   Time span: {t0:.1f}s – {t1:.1f}s")
    else:
        print("⚠️  No drums stem — using existing drums.json")

    analysis_results = load_all_analysis_results(project)
    analysis_data = build_analysis_data_for_strudel(project, analysis_results)

    print(f"\n🎼 Tempo: {analysis_data['tempo']:.1f} BPM | Key: {analysis_data.get('key', '?')}")
    print(f"   Melody notes: {len(analysis_data.get('melody', {}).get('notes', []))}")
    print(f"   Bass notes: {len(analysis_data.get('bass', {}).get('notes', []))}")

    print("\n📝 Regenerating Strudel patterns...")
    files = generate_strudel_from_analysis(
        analysis_data, str(project.project_path / "strudel")
    )
    print("✅ Generated:")
    for k, v in sorted(files.items()):
        print(f"   - {k}: {v}")

    arrangement = Path(files.get("arrangement", ""))
    if arrangement.exists():
        lines = arrangement.read_text().splitlines()[:12]
        print("\n--- arrangement.js (preview) ---")
        print("\n".join(lines))
        print("...")

    print("\n🚀 Open the app: streamlit run app.py")
    print("   Load project 'Nice_2_Know_Ya_Full' → Strudel Replica → Play")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
