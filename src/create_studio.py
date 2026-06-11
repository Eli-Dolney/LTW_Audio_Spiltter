"""
Strudel Create Studio — browse templates and curated beat packs with live playback.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import streamlit as st

from src.app_helpers import discover_strudel_gallery, save_strudel_export
from src.io_utils import ProjectManager
from src.strudel_player_component import render_live_strudel_player
from src.strudel_integration import bpm_to_cpm
from src.strudel_templates import get_strudel_templates


def render_create_studio(project: Optional[ProjectManager] = None) -> None:
    """Render the Create workspace tab."""
    st.header("Create — Strudel Beat Studio")
    st.markdown(
        "Build original beats from templates, browse curated packs (WiredUp, Vol 2, etc.), "
        "and play patterns live in the browser."
    )

    studio_tabs = st.tabs(["Live Editor", "Genre Templates", "Beat Gallery", "Sound Browser"])

    with studio_tabs[0]:
        _render_live_editor(project)

    with studio_tabs[1]:
        _render_template_browser()

    with studio_tabs[2]:
        _render_beat_gallery()

    with studio_tabs[3]:
        _render_sound_browser()


def _render_live_editor(project: Optional[ProjectManager]) -> None:
    st.subheader("Live Pattern Editor")

    default_code = st.session_state.get(
        "custom_strudel_code",
        """// LTW Audio — custom beat
setcpm(30)

stack(
  s("bd ~ sd ~ bd ~ sd ~").bank("RolandTR808").gain(0.9),
  note("c3 ~ g3 ~ c4 ~").sound("sawtooth").lpf(600).gain(0.8),
  chord("C Am F G").sound("piano").room(0.4).gain(0.6)
)
""",
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        tempo = st.number_input("BPM", min_value=60, max_value=200, value=120, key="create_bpm")
    with col2:
        st.caption(f"Strudel CPM ≈ {bpm_to_cpm(float(tempo)):.1f} (BPM ÷ 4)")

    code = st.text_area(
        "Strudel code",
        value=default_code,
        height=280,
        key="create_editor_code",
    )
    st.session_state.custom_strudel_code = code

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Play in browser", type="primary", key="create_play"):
            st.session_state.show_create_player = True
    with c2:
        if st.button("Insert tempo", key="create_insert_tempo"):
            if "setcpm" not in code:
                st.session_state.custom_strudel_code = f"setcpm({bpm_to_cpm(float(tempo)):.2f})\n\n" + code
                st.rerun()
    with c3:
        if project and st.button("Save to project", key="create_save_proj"):
            paths = save_strudel_export(project, code, "custom_beat.js")
            st.success(f"Saved to {paths['js']}")

    if st.session_state.get("show_create_player"):
        render_live_strudel_player(
            code,
            title="Custom Beat",
            height=520,
            default_cpm=bpm_to_cpm(float(tempo)),
        )


def _render_template_browser() -> None:
    st.subheader("Genre Templates")
    templates = get_strudel_templates()

    col1, col2 = st.columns(2)
    with col1:
        style = st.selectbox("Style", templates.get_all_styles(), key="tpl_style")
    with col2:
        patterns = templates.get_patterns_for_style(style) if style else []
        pattern = st.selectbox("Pattern", patterns, key="tpl_pattern") if patterns else None

    if style and pattern:
        template_code = templates.get_template(style, pattern)
        st.code(template_code, language="javascript")

        b1, b2, b3 = st.columns(3)
        with b1:
            if st.button("Load into editor", key="tpl_load"):
                st.session_state.custom_strudel_code = template_code
                st.session_state.show_create_player = True
                st.rerun()
        with b2:
            if st.button("Play template", key="tpl_play"):
                render_live_strudel_player(template_code, title=f"{style} — {pattern}", height=500)
        with b3:
            st.download_button(
                "Download .js",
                template_code,
                file_name=f"{style}_{pattern}.js",
                mime="text/javascript",
            )


def _render_beat_gallery() -> None:
    st.subheader("Curated Beat Packs")
    gallery = discover_strudel_gallery()

    if not gallery:
        st.info("No curated HTML beats found under `projects/`.")
        return

    packs = sorted({g["pack"] for g in gallery})
    pack = st.selectbox("Pack", packs, key="gallery_pack")
    items = [g for g in gallery if g["pack"] == pack]
    beat = st.selectbox(
        "Beat",
        items,
        format_func=lambda x: x["name"],
        key="gallery_beat",
    )

    if beat:
        st.caption(beat["html_path"])
        js_path = beat.get("js_path") or ""
        code = None
        if js_path and Path(js_path).exists():
            code = Path(js_path).read_text()
            with st.expander("View code"):
                st.code(code, language="javascript")

        if st.button("Open standalone player", key="gallery_open"):
            st.markdown(f"[Open in browser](file://{beat['html_path']})")

        if code and st.button("Play in app", key="gallery_play"):
            render_live_strudel_player(code, title=beat["name"], height=500)

        if code:
            st.download_button(
                "Download .js",
                code,
                file_name=f"{beat['name'].replace(' ', '_')}.js",
                mime="text/javascript",
            )


def _render_sound_browser() -> None:
    st.subheader("Strudel Sound Reference")
    sounds_js = Path("src/strudel_sounds.js")
    if sounds_js.exists():
        st.code(sounds_js.read_text()[:4000], language="javascript")
        st.caption("Use these bank/synth names in your patterns. Full reference: src/strudel_sounds.js")
    else:
        st.info("Sound reference file not found.")
