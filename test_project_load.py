#!/usr/bin/env python3
"""Verify project listing and load logic (no Streamlit UI)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.io_utils import ProjectManager, list_projects
from src.app_helpers import load_all_analysis_results, load_stems_from_project


def load_project(name: str) -> dict:
    pm = ProjectManager(name)
    config = pm.load_project_config()
    analysis = load_all_analysis_results(pm, {})
    stems = load_stems_from_project(pm)
    audio_path = (config or {}).get("audio", {}).get("path")
    audio_ok = bool(audio_path and Path(audio_path).exists())
    strudel_dir = pm.project_path / "strudel"
    strudel_ok = (strudel_dir / "arrangement.js").exists() or (strudel_dir / "building_blocks.js").exists()
    return {
        "name": name,
        "tempo": (config or {}).get("analysis", {}).get("tempo"),
        "analysis_keys": sorted(analysis.keys()),
        "stems": sorted(stems.keys()),
        "audio_ok": audio_ok,
        "strudel_ok": strudel_ok,
    }


def main():
    projects = list_projects()
    print(f"Found {len(projects)} projects\n")
    assert len(projects) > 0, "No projects found"

    targets = ["Nice_2_Know_Ya_Full"]
    seen = set()
    for name in targets:
        if name in seen:
            continue
        seen.add(name)
        if not any(p["name"] == name for p in projects):
            print(f"SKIP {name} (not in list)")
            continue
        info = load_project(name)
        print(f"✅ {info['name']}")
        print(f"   tempo={info['tempo']} analysis={info['analysis_keys']}")
        print(f"   stems={info['stems']} audio={info['audio_ok']} strudel={info['strudel_ok']}")
        assert info["audio_ok"], f"Audio missing for {name}"
        assert "tempo_beats" in info["analysis_keys"], "Expected tempo_beats analysis"
        assert info["strudel_ok"], "Expected strudel output"
        print()

    # Switch between two projects — no stale merge
    a = load_all_analysis_results(ProjectManager("Nice_2_Know_Ya_Full"), {})
    other = next(p["name"] for p in projects if p["name"] != "Nice_2_Know_Ya_Full")
    b = load_all_analysis_results(ProjectManager(other), {})
    assert a != b or other == "Nice_2_Know_Ya_Full", "Analysis should be per-project"
    print("✅ Project switch isolation OK")
    print("\nAll project load tests passed.")


if __name__ == "__main__":
    main()
