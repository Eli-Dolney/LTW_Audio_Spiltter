"""
Strudel Integration Module for LTW Audio Splitter
Generates Strudel code patterns based on audio analysis
"""
import json
import re
from typing import Dict, List, Any, Optional
from pathlib import Path
import numpy as np
from .strudel_templates import get_strudel_templates

class StrudelPatternGenerator:
    """Generates Strudel patterns from audio analysis data"""
    
    def __init__(self):
        self.drum_samples = {
            "kick": "bd",
            "snare": "sn", 
            "hihat": "hh",
            "open_hat": "oh",
            "crash": "crash",
            "ride": "ride"
        }
        self.templates = get_strudel_templates()
        
        self.chord_notes = {
            "C": ["c", "e", "g"],
            "D": ["d", "f#", "a"],
            "E": ["e", "g#", "b"],
            "F": ["f", "a", "c"],
            "G": ["g", "b", "d"],
            "A": ["a", "c#", "e"],
            "B": ["b", "d#", "f#"],
            "Cm": ["c", "eb", "g"],
            "Dm": ["d", "f", "a"],
            "Em": ["e", "g", "b"],
            "Fm": ["f", "ab", "c"],
            "Gm": ["g", "bb", "d"],
            "Am": ["a", "c", "e"],
            "Bm": ["b", "d", "f#"]
        }
    
    def generate_drum_pattern(self, drum_analysis: Dict[str, Any], tempo: float) -> str:
        """Generate Strudel drum pattern from drum analysis"""
        
        # Extract drum hits
        drum_hits = drum_analysis.get('drum_hits', [])
        if not drum_hits:
            return self._generate_basic_drum_pattern(tempo)
        
        # Group hits by type
        kicks = [hit for hit in drum_hits if hit.get('type') == 'kick']
        snares = [hit for hit in drum_hits if hit.get('type') == 'snare']
        hats = [hit for hit in drum_hits if hit.get('type') in ['hihat', 'hat']]
        
        # Generate patterns
        kick_pattern = self._create_drum_pattern(kicks, tempo, "bd")
        snare_pattern = self._create_drum_pattern(snares, tempo, "sn")
        hat_pattern = self._create_drum_pattern(hats, tempo, "hh")
        
        # Combine into Strudel code
        strudel_code = f"""
// Generated drum pattern from audio analysis
// Tempo: {tempo:.1f} BPM

d1 $ stack [
  {kick_pattern},
  {snare_pattern},
  {hat_pattern}
]
"""
        return strudel_code.strip()
    
    def _create_drum_pattern(self, hits: List[Dict], tempo: float, sample: str) -> str:
        """Create a Strudel pattern for a specific drum type"""
        if not hits:
            return f"silence"
        
        # Convert hit times to beat positions
        beat_length = 60.0 / tempo  # seconds per beat
        beat_positions = []
        
        for hit in hits:
            beat_pos = hit['time'] / beat_length
            beat_positions.append(beat_pos)
        
        # Create pattern string
        if len(beat_positions) <= 4:
            # Simple pattern
            pattern = "~ " * 4
            for i, pos in enumerate(beat_positions):
                if pos < 4:
                    pattern = pattern[:int(pos)*2] + sample + pattern[int(pos)*2+len(sample):]
            return f'"{pattern.strip()}"'
        else:
            # Complex pattern - use repetition instead of long arrays
            if len(beat_positions) > 16:
                # Too many hits, use repetition
                return f'"{sample}*{len(beat_positions)}"'
            else:
                # Moderate number of hits, use cat
                pattern_parts = []
                for pos in beat_positions:
                    if pos < 4:
                        pattern_parts.append(f'"{sample}"')
                    else:
                        # Use timing for off-beat hits
                        timing = pos - int(pos)
                        pattern_parts.append(f'"{sample}" ~{timing:.2f}')
                
                return f"cat [{', '.join(pattern_parts)}]"
    
    def _generate_basic_drum_pattern(self, tempo: float) -> str:
        """Generate a basic drum pattern when no analysis is available"""
        return f"""
// Basic drum pattern (no analysis data available)
// Tempo: {tempo:.1f} BPM

d1 $ stack [
  "bd ~ bd ~",
  "~ sn ~ sn", 
  "hh*8"
]
"""
    
    def generate_melody_pattern(self, melody_analysis: Dict[str, Any], tempo: float) -> str:
        """Generate Strudel melody pattern from melody analysis"""
        
        notes = melody_analysis.get('notes', [])
        if not notes:
            return self._generate_basic_melody_pattern(tempo)
        
        # Convert notes to Strudel format
        strudel_notes = []
        for note in notes:
            if 'pitch' in note and 'start_time' in note:
                # Convert MIDI note to Strudel note
                midi_note = note['pitch']
                strudel_note = self._midi_to_strudel_note(midi_note)
                strudel_notes.append(strudel_note)
        
        if not strudel_notes:
            return self._generate_basic_melody_pattern(tempo)
        
        # Create pattern
        if len(strudel_notes) <= 8:
            pattern = " ".join(strudel_notes)
            return f"""
// Generated melody pattern from audio analysis
// Tempo: {tempo:.1f} BPM

d2 $ n "{pattern}" # s "piano"
"""
        else:
            # Use cat for longer patterns
            note_strings = [f'"{note}"' for note in strudel_notes]
            return f"""
// Generated melody pattern from audio analysis  
// Tempo: {tempo:.1f} BPM

d2 $ n (cat [{', '.join(note_strings)}]) # s "piano"
"""
    
    def _midi_to_strudel_note(self, midi_note: int) -> str:
        """Convert MIDI note number to Strudel note format"""
        note_names = ['c', 'c#', 'd', 'd#', 'e', 'f', 'f#', 'g', 'g#', 'a', 'a#', 'b']
        octave = (midi_note // 12) - 1
        note_name = note_names[midi_note % 12]
        return f"{note_name}{octave}"
    
    def _generate_basic_melody_pattern(self, tempo: float) -> str:
        """Generate a basic melody pattern when no analysis is available"""
        return f"""
// Basic melody pattern (no analysis data available)
// Tempo: {tempo:.1f} BPM

d2 $ n "c4 d4 e4 f4" # s "piano"
"""
    
    def generate_chord_progression(self, chord_analysis: Dict[str, Any], tempo: float) -> str:
        """Generate Strudel chord progression from chord analysis"""
        
        chords = chord_analysis.get('chords', [])
        if not chords:
            return self._generate_basic_chord_progression(tempo)
        
        # Extract chord names
        chord_names = []
        for chord in chords:
            if 'chord' in chord:
                chord_name = chord['chord']
                if chord_name in self.chord_notes:
                    chord_names.append(chord_name)
        
        if not chord_names:
            return self._generate_basic_chord_progression(tempo)
        
        # Create chord pattern
        if len(chord_names) <= 4:
            chord_pattern = " ".join(chord_names)
            return f"""
// Generated chord progression from audio analysis
// Tempo: {tempo:.1f} BPM

d3 $ chord "{chord_pattern}" # s "pad"
"""
        else:
            # Use cat for longer progressions
            chord_strings = [f'"{chord}"' for chord in chord_names]
            return f"""
// Generated chord progression from audio analysis
// Tempo: {tempo:.1f} BPM

d3 $ chord (cat [{', '.join(chord_strings)}]) # s "pad"
"""
    
    def _generate_basic_chord_progression(self, tempo: float) -> str:
        """Generate a basic chord progression when no analysis is available"""
        return f"""
// Basic chord progression (no analysis data available)
// Tempo: {tempo:.1f} BPM

d3 $ chord "C Am F G" # s "pad"
"""
    
    def generate_complete_pattern(self, analysis_data: Dict[str, Any]) -> str:
        """Generate a complete Strudel pattern from all analysis data"""
        
        tempo = analysis_data.get('tempo', 120)
        drum_analysis = analysis_data.get('drums', {})
        melody_analysis = analysis_data.get('melody', {})
        chord_analysis = analysis_data.get('chords', {})
        
        # Generate individual patterns
        drum_pattern = self.generate_drum_pattern(drum_analysis, tempo)
        melody_pattern = self.generate_melody_pattern(melody_analysis, tempo)
        chord_pattern = self.generate_chord_progression(chord_analysis, tempo)
        
        # Combine into complete pattern
        complete_pattern = f"""
// Complete Strudel pattern generated from audio analysis
// Generated by LTW Audio Splitter

// Set tempo
setcpm ({tempo * 4})

// Drum pattern
{drum_pattern}

// Melody pattern  
{melody_pattern}

// Chord progression
{chord_pattern}

// Start all patterns
hush
d1
d2  
d3
"""
        
        return complete_pattern.strip()
    
    def suggest_template_pattern(self, analysis_data: Dict[str, Any]) -> str:
        """Suggest a template pattern based on analysis data"""
        return self.templates.analyze_and_suggest_template(analysis_data)
    
    def get_style_templates(self, style: str) -> Dict[str, str]:
        """Get all templates for a specific style"""
        patterns = self.templates.get_patterns_for_style(style)
        return {pattern: self.templates.get_template(style, pattern) 
                for pattern in patterns}
    
    def create_template_based_pattern(self, style: str, pattern: str, tempo: int = 120) -> str:
        """Create a pattern based on a template with custom tempo"""
        template = self.templates.get_template(style, pattern)
        
        # Replace tempo if specified
        if tempo != 120:
            template = template.replace("setcpm (480)", f"setcpm ({tempo * 4})")
        
        return template
    
    def save_strudel_code(self, code: str, output_path: str) -> None:
        """Save Strudel code to a file"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            f.write(code)
    
    def create_strudel_html(self, code: str, title: str = "Generated Pattern") -> str:
        """Create an HTML file that can run Strudel code"""
        
        # Escape the code for HTML
        escaped_code = code.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script type="module">
        import {{ repl }} from 'https://strudel.cc/strudel.js';
        
        let strudel;
        
        async function initStrudel() {{
            try {{
                strudel = await repl();
            }} catch (error) {{
                console.error('Error initializing Strudel:', error);
            }}
        }}
        
        function playPattern() {{
            const code = document.getElementById('strudel-code').value;
            
            if (!strudel) {{
                alert('Strudel not initialized yet. Please wait a moment and try again.');
                return;
            }}
            
            try {{
                strudel.evaluate(code);
            }} catch (error) {{
                console.error('Error playing pattern:', error);
                alert('Error playing pattern: ' + error.message);
            }}
        }}
        
        function stopPattern() {{
            if (strudel) {{
                strudel.hush();
            }}
        }}
        
        function copyCode() {{
            const code = document.getElementById('strudel-code').value;
            navigator.clipboard.writeText(code).then(() => {{
                alert('Code copied to clipboard!');
            }}).catch(err => {{
                console.error('Failed to copy code: ', err);
            }});
        }}
        
        // Initialize when page loads
        window.addEventListener('load', initStrudel);
    </script>
    <style>
        body {{
            font-family: 'Courier New', monospace;
            margin: 0;
            padding: 20px;
            background-color: #1a1a1a;
            color: #ffffff;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .strudel-editor {{
            width: 100%;
            height: 400px;
            background-color: #2a2a2a;
            border: 1px solid #444;
            border-radius: 5px;
            padding: 10px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            color: #ffffff;
            resize: vertical;
        }}
        .controls {{
            margin: 20px 0;
        }}
        button {{
            background-color: #4CAF50;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            margin-right: 10px;
            font-size: 16px;
        }}
        button:hover {{
            background-color: #45a049;
        }}
        .stop-btn {{
            background-color: #f44336;
        }}
        .stop-btn:hover {{
            background-color: #da190b;
        }}
        .info {{
            background-color: #333;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎵 {title}</h1>
        
        <div class="info">
            <h3>Generated by LTW Audio Splitter</h3>
            <p>This pattern was automatically generated from your audio analysis. You can edit the code below and press "Play" to hear it!</p>
        </div>
        
        <textarea class="strudel-editor" id="strudel-code">{escaped_code}</textarea>
        
        <div class="controls">
            <button onclick="playPattern()">▶️ Play</button>
            <button class="stop-btn" onclick="stopPattern()">⏹️ Stop</button>
            <button onclick="copyCode()">📋 Copy Code</button>
        </div>
        
        <div class="info">
            <h3>How to use:</h3>
            <ul>
                <li>Edit the code in the text area above</li>
                <li>Press "Play" to start the pattern</li>
                <li>Press "Stop" to stop all sounds</li>
                <li>Use "Copy Code" to copy the pattern to your clipboard</li>
            </ul>
        </div>
    </div>

</body>
</html>
"""
        
        return html_template


def generate_strudel_from_analysis(analysis_data: Dict[str, Any], output_dir: str) -> Dict[str, str]:
    """Main function to generate Strudel patterns from analysis data"""
    
    generator = StrudelPatternGenerator()
    
    # Generate complete pattern
    complete_pattern = generator.generate_complete_pattern(analysis_data)
    
    # Generate individual patterns
    tempo = analysis_data.get('tempo', 120)
    drum_pattern = generator.generate_drum_pattern(analysis_data.get('drums', {}), tempo)
    melody_pattern = generator.generate_melody_pattern(analysis_data.get('melody', {}), tempo)
    chord_pattern = generator.generate_chord_progression(analysis_data.get('chords', {}), tempo)
    
    # Generate suggested template
    suggested_template = generator.suggest_template_pattern(analysis_data)
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save files
    files_created = {}
    
    # Complete pattern
    complete_file = output_path / "complete_pattern.js"
    generator.save_strudel_code(complete_pattern, str(complete_file))
    files_created['complete'] = str(complete_file)
    
    # Individual patterns
    drum_file = output_path / "drum_pattern.js"
    generator.save_strudel_code(drum_pattern, str(drum_file))
    files_created['drums'] = str(drum_file)
    
    melody_file = output_path / "melody_pattern.js"
    generator.save_strudel_code(melody_pattern, str(melody_file))
    files_created['melody'] = str(melody_file)
    
    chord_file = output_path / "chord_pattern.js"
    generator.save_strudel_code(chord_pattern, str(chord_file))
    files_created['chords'] = str(chord_file)
    
    # Suggested template
    template_file = output_path / "suggested_template.js"
    generator.save_strudel_code(suggested_template, str(template_file))
    files_created['template'] = str(template_file)
    
    # Create HTML file
    html_content = generator.create_strudel_html(complete_pattern, "LTW Audio Splitter - Generated Pattern")
    html_file = output_path / "strudel_player.html"
    with open(html_file, 'w') as f:
        f.write(html_content)
    files_created['html'] = str(html_file)
    
    return files_created
