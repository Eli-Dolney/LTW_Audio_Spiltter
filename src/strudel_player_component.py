"""
Embedded live Strudel player for Streamlit using @strudel/web.
"""
from __future__ import annotations

import html as html_module
from pathlib import Path
from typing import Optional

import streamlit.components.v1 as components


def _escape_js_for_html(code: str) -> str:
    """Escape Strudel code for embedding inside a JS template literal."""
    return (
        code.replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("${", "\\${")
    )


def build_live_player_html(
    strudel_code: str,
    title: str = "LTW Audio Player",
    height: int = 420,
    show_tempo_slider: bool = True,
    default_cpm: float = 30.0,
) -> str:
    """Build standalone HTML with @strudel/web live playback."""
    escaped_code = _escape_js_for_html(strudel_code.strip())
    title_escaped = html_module.escape(title)

    tempo_controls = ""
    if show_tempo_slider:
        tempo_controls = f"""
        <div class="control-row">
            <label>Tempo (CPM)</label>
            <input type="range" id="cpmSlider" min="15" max="120" step="1" value="{default_cpm}"
                   oninput="document.getElementById('cpmVal').textContent=this.value">
            <span id="cpmVal">{default_cpm:.0f}</span>
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title_escaped}</title>
    <script type="module">
        import {{ init, evaluate, hush }} from 'https://esm.sh/@strudel/web@latest';

        const baseCode = `{escaped_code}`;

        window.playPattern = async () => {{
            try {{
                await init();
                let code = baseCode;
                const slider = document.getElementById('cpmSlider');
                if (slider) {{
                    const cpm = parseFloat(slider.value);
                    if (!baseCode.includes('setcpm')) {{
                        code = `setcpm(${{cpm}})\\n` + code;
                    }}
                }}
                await evaluate(code);
            }} catch (e) {{
                console.error('Strudel playback error:', e);
                const status = document.getElementById('status');
                if (status) status.textContent = 'Error: ' + e.message;
            }}
        }};

        window.stopPattern = () => {{
            try {{ hush(); }} catch (e) {{ console.error(e); }}
        }};

        init().then(() => {{
            const status = document.getElementById('status');
            if (status) status.textContent = 'Ready — press Play';
        }}).catch(e => {{
            const status = document.getElementById('status');
            if (status) status.textContent = 'Init failed (check internet for CDN)';
        }});
    </script>
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0;
            padding: 16px;
            background: #0d1117;
            color: #e6edf3;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }}
        h2 {{
            margin: 0 0 12px;
            font-size: 1.1rem;
            color: #58a6ff;
        }}
        .controls {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            align-items: center;
            margin-bottom: 12px;
        }}
        button {{
            padding: 10px 24px;
            border: none;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            font-size: 0.95rem;
        }}
        .play-btn {{ background: #238636; color: #fff; }}
        .stop-btn {{ background: #da3633; color: #fff; }}
        .play-btn:hover {{ background: #2ea043; }}
        .stop-btn:hover {{ background: #f85149; }}
        #status {{
            font-size: 0.85rem;
            color: #8b949e;
            flex: 1;
            min-width: 120px;
        }}
        .control-row {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-top: 8px;
            font-size: 0.85rem;
        }}
        .control-row label {{ min-width: 90px; color: #8b949e; }}
        .control-row input[type=range] {{ flex: 1; accent-color: #58a6ff; }}
        pre {{
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 10px;
            font-size: 11px;
            overflow: auto;
            max-height: 120px;
            color: #7ee787;
            margin: 0;
        }}
    </style>
</head>
<body>
    <h2>{title_escaped}</h2>
    <div class="controls">
        <button class="play-btn" onclick="playPattern()">Play</button>
        <button class="stop-btn" onclick="stopPattern()">Stop</button>
        <span id="status">Loading Strudel...</span>
    </div>
    {tempo_controls}
    <pre>{html_module.escape(strudel_code[:500])}{'...' if len(strudel_code) > 500 else ''}</pre>
</body>
</html>"""


def render_live_strudel_player(
    strudel_code: str,
    title: str = "Live Strudel",
    height: int = 480,
    show_tempo_slider: bool = True,
    default_cpm: float = 30.0,
) -> None:
    """Render embedded Strudel player in Streamlit."""
    import streamlit as st

    if not strudel_code or not strudel_code.strip():
        st.warning("No Strudel code to play.")
        return

    html = build_live_player_html(
        strudel_code,
        title=title,
        height=height,
        show_tempo_slider=show_tempo_slider,
        default_cpm=default_cpm,
    )
    components.html(html, height=height, scrolling=True)


def read_js_from_html_pack(html_path: str) -> Optional[str]:
    """Try to read companion .js file for a gallery HTML entry."""
    path = Path(html_path)
    js_path = path.with_suffix(".js")
    if js_path.exists():
        return js_path.read_text()
    return None
