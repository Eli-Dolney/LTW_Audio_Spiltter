"""
Strudel Pattern Templates for LTW Audio Splitter
Pre-defined beat patterns and templates for different musical styles
"""
from typing import Dict, List, Any
import random

class StrudelTemplates:
    """Collection of Strudel pattern templates for different musical styles"""
    
    def __init__(self):
        self.templates = {
            "hip_hop": self._get_hip_hop_templates(),
            "electronic": self._get_electronic_templates(),
            "rock": self._get_rock_templates(),
            "jazz": self._get_jazz_templates(),
            "ambient": self._get_ambient_templates(),
            "reggae": self._get_reggae_templates(),
            "funk": self._get_funk_templates(),
            "minimal": self._get_minimal_templates(),
            "tiktok_viral": self._get_tiktok_viral_templates()
        }
    
    def _get_tiktok_viral_templates(self) -> Dict[str, str]:
        """Viral styles for TikToks/Edits"""
        return {
            "phonk": """
// 🏎️ Drift Phonk (Aggressive)
// 155 BPM
setcpm(38.75);

stack(
  // Distorted 808s
  s("bd(3,8) [~ bd]").bank("RolandTR808").clip(2).gain(1.5),
  note("c1(3,8) [~ c1]").sound("sawtooth").lpf(300).gain(1.8),
  
  // Cowbell Melody (The Phonk Signature)
  note("c3 ~ d#3 ~ g3 ~ c4 ~").sound("cowbell").gain(1.2).room(0.5),
  
  // Fast Memphis Hi-Hats
  s("hh*8").bank("RolandTR808").speed("1 2").gain(0.8),
  
  // Dark Pad texture
  chord("Cm").sound("sawtooth").lpf(800).room(2)
)
""",
            "jersey_club": """
// 💃 Jersey Club (Bounce)
// 140 BPM
setcpm(35);

stack(
  // The Jersey Kick Pattern (Triplet feel on the 4th beat)
  // 1 . 2 . 3 . 4 . .
  s("bd ~ bd ~ bd ~ [bd ~ bd] ~").bank("RolandTR909").gain(1.3),
  
  // Vocal Chop / Bed squeak sample (Simulated)
  s("cp*4").bank("RolandTR808").speed("2").hpf(1000).gain(0.6),
  
  // Bouncy Synth
  note("c3 ~ ~ g3 ~ ~ c4 ~").sound("square").lpf(1500).decay(0.1)
)
""",
            "hyperpop": """
// ⚡ Hyperpop / Glitchcore
// 160 BPM
setcpm(40);

stack(
  // Distorted, fast drums
  s("bd*4").bank("RolandTR909").clip(1.5),
  s("sd(3,8)").bank("RolandTR909").crush(4).gain(1.2),
  
  // Glitchy Arps
  note("c4 e4 g4 b4").sound("sawtooth").speed("2").phaser(2),
  
  // Bubbling Bass
  note("c2*8").sound("sawtooth").lpf(sine.range(200, 800).fast(8))
)
""",
            "dnb": """
// 🏃 Drum & Bass / Breakcore
// 174 BPM
setcpm(43.5);

stack(
  // The Amen Break Pattern
  s("bd ~ ~ ~ sd ~ ~ bd ~ bd sd ~ ~ ~ ~ ~").bank("RolandTR909").speed(1.2),
  s("hh*16").bank("RolandTR909").gain(0.5),
  
  // Reese Bass
  note("f1").sound("sawtooth").detune(0.2).lpf(400).gain(1.5).sustain(4),
  
  // Atmospheric Pad
  chord("Fm9").sound("sawtooth").lpf(2000).room(3).slow(4)
)
"""
        }
    
    def _get_hip_hop_templates(self) -> Dict[str, str]:
        """Hip-hop style templates"""
        return {
            "basic": """
// Basic Hip-Hop Beat
d1 $ "bd ~ bd ~"
d2 $ "~ sn ~ sn"
d3 $ "hh*8"
""",
            "trap": """
// Trap Style Beat
d1 $ "bd ~ bd bd"
d2 $ "~ sn ~ sn"
d3 $ "hh*16"
d4 $ "~ ~ ~ crash"
""",
            "boom_bap": """
// Boom Bap Style
d1 $ "bd ~ ~ bd"
d2 $ "~ sn ~ sn"
d3 $ "hh*4"
d4 $ "~ ~ oh ~"
""",
            "drill": """
// Drill Style
d1 $ "bd bd ~ bd"
d2 $ "~ sn ~ sn"
d3 $ "hh*8"
d4 $ "~ ~ ~ crash"
"""
        }
    
    def _get_electronic_templates(self) -> Dict[str, str]:
        """Electronic music templates"""
        return {
            "house": """
// House Beat
d1 $ "bd ~ bd ~"
d2 $ "~ ~ sn ~"
d3 $ "hh*8"
d4 $ "~ ~ ~ oh"
""",
            "techno": """
// Techno Beat
d1 $ "bd ~ bd ~"
d2 $ "~ sn ~ sn"
d3 $ "hh*16"
d4 $ "~ ~ ~ crash"
""",
            "dubstep": """
// Dubstep Style
d1 $ "bd ~ ~ bd"
d2 $ "~ sn ~ sn"
d3 $ "hh*8"
d4 $ "~ ~ crash ~"
""",
            "ambient_techno": """
// Ambient Techno
d1 $ "bd ~ ~ ~"
d2 $ "~ ~ sn ~"
d3 $ "hh*4"
d4 $ "~ ~ ~ oh"
""",
            "trance": """
// Spacey Trance Beat
// 140 BPM
setcpm(35);

stack(
  // Driving Kick & Bass
  s("bd*4").bank("RolandTR909").gain(1.2),
  note("e1*4").sound("sawtooth").lpf(400).gain(1.5),
  
  // Arpeggiated Lead
  note("e3(3,8) a3(3,8) b3(3,8) e4(3,8)").sound("sawtooth").lpf(2000).delay(0.5).room(1.5).sustain(0.1),
  
  // Sweeping Pad
  chord("EM7").sound("sawtooth").lpf(sine.range(500, 8000).slow(16)).room(3).sustain(4)
)
""",
            "psytrance": """
// Psytrance Gallop
// 145 BPM
setcpm(36.25);

stack(
  // Kick
  s("bd*4").bank("RolandTR909").gain(1.5).clip(1.2),
  
  // The "Gallop" Bass (KBBK BBK)
  note("~ f1 f1 ~ ~ f1 f1 ~").sound("sawtooth").lpf(600).lpq(5).gain(1.3),
  
  // Alien FX
  s("bd(3,8)").speed("4 8 2").sound("square").hpf(2000).delay(0.25),
  
  // Acid Line
  note("f2 f3 f2 c3").sound("sawtooth").lpf(sine.range(200, 3000).fast(4)).lpq(20).sustain(0.2)
)
"""
        }
    
    def _get_rock_templates(self) -> Dict[str, str]:
        """Rock music templates"""
        return {
            "basic_rock": """
// Basic Rock Beat
d1 $ "bd ~ bd ~"
d2 $ "~ sn ~ sn"
d3 $ "hh*8"
d4 $ "~ ~ ~ crash"
""",
            "punk": """
// Punk Rock
d1 $ "bd bd bd bd"
d2 $ "sn sn sn sn"
d3 $ "hh*16"
""",
            "metal": """
// Metal Style
d1 $ "bd ~ bd bd"
d2 $ "~ sn ~ sn"
d3 $ "hh*16"
d4 $ "crash ~ ~ ~"
""",
            "alternative": """
// Alternative Rock
d1 $ "bd ~ ~ bd"
d2 $ "~ sn ~ sn"
d3 $ "hh*4"
d4 $ "~ ~ oh ~"
"""
        }
    
    def _get_jazz_templates(self) -> Dict[str, str]:
        """Jazz music templates"""
        return {
            "swing": """
// Swing Beat
d1 $ "bd ~ ~ bd"
d2 $ "~ sn ~ sn"
d3 $ "hh*4"
d4 $ "~ ~ oh ~"
""",
            "bebop": """
// Bebop Style
d1 $ "bd ~ ~ ~"
d2 $ "~ sn ~ sn"
d3 $ "hh*8"
d4 $ "~ ~ oh ~"
""",
            "fusion": """
// Jazz Fusion
d1 $ "bd ~ bd ~"
d2 $ "~ sn ~ sn"
d3 $ "hh*16"
d4 $ "~ ~ ~ crash"
""",
            "latin_jazz": """
// Latin Jazz
d1 $ "bd ~ ~ bd"
d2 $ "~ sn ~ sn"
d3 $ "hh*8"
d4 $ "~ ~ oh ~"
"""
        }
    
    def _get_ambient_templates(self) -> Dict[str, str]:
        """Ambient music templates"""
        return {
            "minimal": """
// Minimal Ambient
d1 $ "bd ~ ~ ~"
d2 $ "~ ~ sn ~"
d3 $ "hh*2"
""",
            "atmospheric": """
// Atmospheric
d1 $ "bd ~ ~ ~"
d2 $ "~ ~ ~ sn"
d3 $ "hh*4"
d4 $ "~ ~ oh ~"
""",
            "drone": """
// Drone Style
d1 $ "bd ~ ~ ~"
d2 $ "~ ~ ~ ~"
d3 $ "hh*1"
""",
            "textural": """
// Textural Ambient
d1 $ "bd ~ ~ ~"
d2 $ "~ sn ~ ~"
d3 $ "hh*8"
d4 $ "~ ~ oh ~"
"""
        }
    
    def _get_reggae_templates(self) -> Dict[str, str]:
        """Reggae music templates"""
        return {
            "one_drop": """
// One Drop Reggae
d1 $ "bd ~ ~ ~"
d2 $ "~ sn ~ sn"
d3 $ "hh*8"
d4 $ "~ ~ oh ~"
""",
            "rockers": """
// Rockers Style
d1 $ "bd ~ bd ~"
d2 $ "~ sn ~ sn"
d3 $ "hh*8"
d4 $ "~ ~ oh ~"
""",
            "steppers": """
// Steppers Style
d1 $ "bd ~ bd ~"
d2 $ "~ sn ~ sn"
d3 $ "hh*16"
""",
            "dub": """
// Dub Style
d1 $ "bd ~ ~ bd"
d2 $ "~ sn ~ sn"
d3 $ "hh*8"
d4 $ "~ ~ oh ~"
"""
        }
    
    def _get_funk_templates(self) -> Dict[str, str]:
        """Funk music templates"""
        return {
            "basic_funk": """
// Basic Funk
d1 $ "bd ~ bd ~"
d2 $ "~ sn ~ sn"
d3 $ "hh*16"
d4 $ "~ ~ oh ~"
""",
            "james_brown": """
// James Brown Style
d1 $ "bd ~ bd ~"
d2 $ "~ sn ~ sn"
d3 $ "hh*8"
d4 $ "~ ~ oh ~"
""",
            "p_funk": """
// P-Funk Style
d1 $ "bd ~ bd ~"
d2 $ "~ sn ~ sn"
d3 $ "hh*16"
d4 $ "~ ~ oh ~"
""",
            "modern_funk": """
// Modern Funk
d1 $ "bd ~ bd ~"
d2 $ "~ sn ~ sn"
d3 $ "hh*8"
d4 $ "~ ~ oh ~"
"""
        }
    
    def _get_minimal_templates(self) -> Dict[str, str]:
        """Minimal music templates"""
        return {
            "basic_minimal": """
// Basic Minimal
d1 $ "bd ~ ~ ~"
d2 $ "~ sn ~ ~"
d3 $ "hh*4"
""",
            "microhouse": """
// Microhouse
d1 $ "bd ~ ~ ~"
d2 $ "~ sn ~ ~"
d3 $ "hh*8"
d4 $ "~ ~ oh ~"
""",
            "minimal_techno": """
// Minimal Techno
d1 $ "bd ~ ~ ~"
d2 $ "~ sn ~ ~"
d3 $ "hh*16"
""",
            "ambient_minimal": """
// Ambient Minimal
d1 $ "bd ~ ~ ~"
d2 $ "~ ~ sn ~"
d3 $ "hh*2"
"""
        }
    
    def get_template(self, style: str, pattern: str = "basic") -> str:
        """Get a specific template"""
        if style in self.templates and pattern in self.templates[style]:
            return self.templates[style][pattern]
        return self.templates["hip_hop"]["basic"]  # Default fallback
    
    def get_random_template(self, style: str = None) -> str:
        """Get a random template from a style or all styles"""
        if style and style in self.templates:
            patterns = list(self.templates[style].keys())
            pattern = random.choice(patterns)
            return self.templates[style][pattern]
        else:
            # Random from all styles
            all_styles = list(self.templates.keys())
            random_style = random.choice(all_styles)
            patterns = list(self.templates[random_style].keys())
            random_pattern = random.choice(patterns)
            return self.templates[random_style][random_pattern]
    
    def get_all_styles(self) -> List[str]:
        """Get list of all available styles"""
        return list(self.templates.keys())
    
    def get_patterns_for_style(self, style: str) -> List[str]:
        """Get list of patterns for a specific style"""
        if style in self.templates:
            return list(self.templates[style].keys())
        return []
    
    def create_custom_template(self, drums: str, melody: str = None, chords: str = None, tempo: int = 120) -> str:
        """Create a custom template from user input"""
        template = f"""
// Custom Template - Tempo: {tempo} BPM
setcpm ({tempo * 4})

d1 $ "{drums}"
"""
        
        if melody:
            template += f'd2 $ n "{melody}" # s "piano"\n'
        
        if chords:
            template += f'd3 $ chord "{chords}" # s "pad"\n'
        
        template += """
hush
d1
"""
        
        if melody:
            template += "d2\n"
        
        if chords:
            template += "d3\n"
        
        return template.strip()
    
    def analyze_and_suggest_template(self, analysis_data: Dict[str, Any]) -> str:
        """Analyze audio data and suggest appropriate template"""
        tempo = analysis_data.get('tempo', 120)
        drums = analysis_data.get('drums', {})
        melody = analysis_data.get('melody', {})
        chords = analysis_data.get('chords', {})
        
        # Analyze tempo to suggest style
        if tempo < 80:
            suggested_style = "ambient"
        elif tempo < 100:
            suggested_style = "jazz"
        elif tempo < 120:
            suggested_style = "hip_hop"
        elif tempo < 140:
            suggested_style = "rock"
        elif tempo < 160:
            suggested_style = "electronic"
        else:
            suggested_style = "electronic"
        
        # Get drum complexity
        drum_hits = drums.get('drum_hits', [])
        if len(drum_hits) < 10:
            complexity = "minimal"
        elif len(drum_hits) < 20:
            complexity = "basic"
        else:
            complexity = "complex"
        
        # Choose appropriate pattern
        if suggested_style == "hip_hop":
            if complexity == "minimal":
                pattern = "basic"
            elif complexity == "basic":
                pattern = "boom_bap"
            else:
                pattern = "trap"
        elif suggested_style == "electronic":
            if complexity == "minimal":
                pattern = "ambient_techno"
            elif complexity == "basic":
                pattern = "house"
            else:
                pattern = "techno"
        else:
            pattern = "basic"
        
        return self.get_template(suggested_style, pattern)


def get_strudel_templates() -> StrudelTemplates:
    """Get the Strudel templates instance"""
    return StrudelTemplates()
