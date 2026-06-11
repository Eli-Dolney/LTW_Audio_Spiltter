import os
from pathlib import Path
from src.strudel_templates import get_strudel_templates
from src.strudel_integration import create_strudel_html

def create_original_beat(style="electronic", pattern="trance", output_name="spacey_trance"):
    """
    Generates an original beat using Strudel templates.
    """
    print(f"🎹 Generating {style}/{pattern} beat...")

    templates = get_strudel_templates()
    
    # Get the raw template code
    strudel_code = templates.get_template(style, pattern)
    
    # Setup output directory
    output_dir = Path("projects/My_Original_Beats")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save the JS file
    js_filename = f"{output_name}.js"
    js_path = output_dir / js_filename
    
    with open(js_path, "w") as f:
        f.write(strudel_code)
    
    print(f"✅ Strudel code saved to: {js_path}")
    
    # Generate HTML Player
    html_filename = f"{output_name}.html"
    html_content = create_strudel_html(strudel_code, f"Original Beat: {output_name}")
    
    html_path = output_dir / html_filename
    with open(html_path, "w") as f:
        f.write(html_content)
        
    print(f"✨ Player generated at: {html_path}")

if __name__ == "__main__":
    # Generate a batch of viral beats
    beats_to_make = [
        ("tiktok_viral", "phonk", "drift_phonk"),
        ("tiktok_viral", "jersey_club", "jersey_bounce"),
        ("tiktok_viral", "hyperpop", "hyperpop_glitch"),
        ("tiktok_viral", "dnb", "liquid_dnb"),
        ("electronic", "trance", "spacey_trance"),
        ("electronic", "psytrance", "alien_psytrance")
    ]

    for style, pattern, name in beats_to_make:
        create_original_beat(style, pattern, name)
        print("-" * 30)
    
    print("\n🎉 All beats generated in projects/My_Original_Beats/")
