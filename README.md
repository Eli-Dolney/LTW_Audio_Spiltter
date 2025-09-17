# 🎵 LTW Audio Splitter

**Local-Only Audio Analysis & Stem Separation Tool**

LTW Audio Splitter is a powerful, privacy-focused audio analysis tool that runs entirely on your computer. No cloud services, no data uploads, no internet required after installation.

## ✨ Features

### 🎛️ Stem Separation
- **Spleeter Integration**: Fast 2/4/5-stem separation (vocals, drums, bass, piano, other)
- **Demucs Support**: High-quality separation (optional, slower)
- **Multiple Formats**: Export as WAV, FLAC, or other formats
- **Quality Control**: Compare stems with interactive visualizations

### 📊 Audio Analysis
- **Tempo Detection**: Accurate BPM detection with confidence scoring
- **Beat Tracking**: Precise beat grid with downbeat detection
- **Rhythm Analysis**: Syncopation and complexity metrics
- **Time Signature**: Automatic time signature detection

### 🎹 Melody Extraction
- **CREPE Integration**: State-of-the-art pitch detection
- **MIDI Export**: Convert melodies to standard MIDI files
- **Note Segmentation**: Intelligent note boundary detection
- **Beat Quantization**: Optional quantization to beat grid

### 🥁 Drum Analysis
- **Onset Detection**: Precise drum hit detection
- **Classification**: Kick, snare, hi-hat classification
- **Pattern Analysis**: Drum pattern complexity and loop detection
- **MIDI Export**: Drum patterns as MIDI files

### 🎼 Chord Analysis
- **Progression Detection**: Identify chord progressions
- **Key Detection**: Musical key and mode detection
- **Template Matching**: Major/minor chord recognition
- **Export Options**: Text and JSON chord charts

### 🎵 Strudel Live Coding
- **Pattern Generation**: Convert audio analysis to Strudel code
- **Style Templates**: Pre-built patterns for different musical genres
- **Live Coding**: Generate beats, melodies, and chord progressions
- **Web Player**: Download HTML files to play patterns in browser
- **Template Browser**: Browse and use style-specific templates

### 📤 Export & Integration
- **DAW Support**: Export for Ableton Live, Logic Pro, FL Studio
- **Multiple Formats**: WAV, MIDI, JSON, TXT, ZIP packages
- **Project Management**: Save and reload analysis projects
- **Batch Processing**: Process multiple files efficiently

## 🔒 Privacy & Offline Operation

- ✅ **100% Local**: All processing happens on your computer
- ✅ **No Internet Required**: Works completely offline after installation
- ✅ **No Data Uploads**: Your audio never leaves your machine
- ✅ **Open Source**: Transparent codebase with no hidden operations

## 🚀 Quick Start

### Prerequisites

Before you begin, make sure you have:
- **Python 3.9 or higher** installed on your system
- **Git** installed for cloning the repository
- **4GB RAM minimum** (8GB+ recommended)
- **2GB free disk space** for models and dependencies

### Option 1: Automated Setup (Recommended)

**macOS/Linux:**
```bash
git clone https://github.com/Eli-Dolney/LTW_Audio_Spiltter.git
cd LTW_Audio_Spiltter
chmod +x setup.sh
./setup.sh
```

**Windows:**
```cmd
git clone https://github.com/Eli-Dolney/LTW_Audio_Spiltter.git
cd LTW_Audio_Spiltter
setup.bat
```

**After setup, start the application:**
- **macOS/Linux**: `./quick_start.sh`
- **Windows**: `quick_start.bat`

### Option 2: Manual Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Eli-Dolney/LTW_Audio_Spiltter.git
   cd LTW_Audio_Spiltter
   ```

2. **Create and activate virtual environment**:
   ```bash
   # Create virtual environment
   python3 -m venv venv
   
   # Activate virtual environment
   # On macOS/Linux:
   source venv/bin/activate
   
   # On Windows:
   venv\Scripts\activate
   
   # Verify activation (you should see (venv) in your prompt)
   ```

   **Note**: If you get a permission error on macOS/Linux, you may need to make the script executable:
   ```bash
   chmod +x quick_start.sh
   ```

3. **Install dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Install stem separation** (choose one):
   ```bash
   # Fast option (recommended for most users)
   pip install spleeter
   
   # High quality option (slower, requires more RAM)
   pip install demucs
   ```

5. **Install melody extraction**:
   ```bash
   pip install crepe
   ```

### Running the Application

1. **Start the app**:
   ```bash
   streamlit run app.py
   ```

2. **Open your browser** to `http://localhost:8501`

3. **Upload an audio file** and start analyzing!

### Troubleshooting Installation

**macOS Users:**
- If you get a "command not found" error for `python3`, try using `python` instead
- If you get permission errors, you may need to use `sudo` for some commands
- Make sure you have the latest version of pip: `pip install --upgrade pip`

**Windows Users:**
- Make sure Python is added to your PATH during installation
- If you get "python is not recognized", restart your command prompt after installation
- Use `python` instead of `python3` on Windows
- If you get SSL errors, try: `pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt`

**Linux Users:**
- You may need to install additional system dependencies: `sudo apt-get install python3-dev python3-pip`
- For audio processing, you might need: `sudo apt-get install libsndfile1-dev`

## 📖 Usage Guide

### Step 1: Load Audio
- Upload an MP3, WAV, FLAC, M4A, or AAC file
- The app will create a project and load the audio
- View waveform and spectrogram immediately

### Step 2: Analyze Tempo & Beats
- Click "Analyze Tempo & Beats" in the Analysis tab
- View detected BPM, beat grid, and timing information
- Interactive waveform with beat markers

### Step 3: Separate Stems
- Choose separation method (Spleeter recommended for speed)
- Click "Separate Stems" and wait for processing
- Download individual stems or view comparison plots

### Step 4: Extract Melody
- Adjust confidence threshold for note detection
- Enable beat quantization for tighter timing
- Export melody as MIDI file

### Step 5: Analyze Drums
- Set onset detection threshold
- View drum hit classification and patterns
- Export drum patterns as MIDI

### Step 6: Chord Analysis
- Analyze chord progressions and key
- View chord changes over time
- Export chord charts

### Step 7: Generate Strudel Patterns
- Click "Generate Strudel Patterns" in the Strudel tab
- Browse style templates (Hip-Hop, Electronic, Rock, Jazz, etc.)
- Copy generated code to strudel.cc for live coding
- Download HTML player for offline use

### Step 8: Export Results
- Download individual files (stems, MIDI, reports)
- Export DAW-specific project files
- Create complete package with all results

## 🛠️ System Requirements

### Minimum Requirements
- **OS**: macOS 10.15+, Windows 10+, or Linux
- **Python**: 3.9 or higher
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 2GB free space for models and projects

### Recommended for Best Performance
- **RAM**: 16GB or more
- **CPU**: Multi-core processor (Intel i5/AMD Ryzen 5 or better)
- **GPU**: NVIDIA GPU with CUDA support (for Demucs acceleration)
- **Storage**: SSD for faster file operations

### GPU Acceleration (Optional)
For Windows users with NVIDIA GPUs:
```bash
# Install PyTorch with CUDA support
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

## 📁 Project Structure

```
LTW_Audio_Spiltter/
├── app.py                 # Main Streamlit application
├── config.py             # Configuration settings
├── requirements.txt      # Python dependencies
├── README.md            # This file
├── setup.sh             # macOS/Linux initial setup script
├── setup.bat            # Windows initial setup script
├── quick_start.sh       # macOS/Linux quick start script
├── quick_start.bat      # Windows quick start script
├── src/                 # Source code modules
│   ├── __init__.py
│   ├── io_utils.py      # File I/O and project management
│   ├── viz.py           # Visualization utilities
│   ├── separation.py    # Stem separation (Spleeter/Demucs)
│   ├── timing.py        # Tempo and beat analysis
│   ├── melody.py        # Melody extraction (CREPE)
│   ├── chords.py        # Chord analysis
│   ├── drums.py         # Drum analysis
│   └── export.py        # Export utilities
└── projects/            # Project storage (created automatically)
    └── <project_name>/
        ├── project.ltw.json
        ├── stems/
        ├── midi/
        └── analysis/
```

## 🎯 Use Cases

### Music Production
- **Remixing**: Separate tracks for remix projects
- **Sample Creation**: Extract clean samples from full tracks
- **Reference Analysis**: Study arrangement and production techniques
- **Backing Tracks**: Create karaoke-style backing tracks
- **Live Coding**: Generate Strudel patterns for live performance

### Music Education
- **Ear Training**: Analyze chord progressions and melodies
- **Rhythm Study**: Study drum patterns and timing
- **Composition**: Learn from existing songs
- **Transcription**: Convert audio to MIDI for notation
- **Live Coding**: Learn algorithmic composition with Strudel

### Research & Analysis
- **Musicology**: Analyze musical patterns and structures
- **Audio Processing**: Study audio characteristics
- **Machine Learning**: Prepare training data for ML models
- **Audio Forensics**: Analyze audio content and quality

## 🎵 Strudel Live Coding Integration

### What is Strudel?
Strudel is a web-based live coding environment inspired by TidalCycles. It allows you to create music patterns using code, perfect for algorithmic composition and live performance.

### How It Works in LTW Audio Splitter
1. **Analyze your audio** using the Analysis tab
2. **Generate Strudel patterns** from your analysis data
3. **Browse style templates** for different musical genres
4. **Copy code to strudel.cc** for live coding
5. **Download HTML player** for offline use

### Available Musical Styles
- **Hip-Hop**: Basic, Trap, Boom Bap, Drill
- **Electronic**: House, Techno, Dubstep, Ambient Techno
- **Rock**: Basic Rock, Punk, Metal, Alternative
- **Jazz**: Swing, Bebop, Fusion, Latin Jazz
- **Ambient**: Minimal, Atmospheric, Drone, Textural
- **Reggae**: One Drop, Rockers, Steppers, Dub
- **Funk**: Basic Funk, James Brown, P-Funk, Modern Funk
- **Minimal**: Basic Minimal, Microhouse, Minimal Techno, Ambient Minimal

### Getting Started with Strudel
1. Go to [strudel.cc](https://strudel.cc) in your browser
2. Copy generated code from LTW Audio Splitter
3. Paste into the Strudel editor
4. Press **Ctrl+Enter** to play
5. Edit the code to modify patterns

### Basic Strudel Commands
```javascript
// Play a drum pattern
d1 $ "bd sn bd sn"

// Play a melody
d2 $ n "c4 d4 e4 f4" # s "piano"

// Play chord progression
d3 $ chord "C Am F G" # s "pad"

// Stop all sounds
hush

// Set tempo
setcpm 480  // 120 BPM
```

## 🔧 Configuration

### Project Structure and .gitignore

This project includes a comprehensive `.gitignore` file that excludes:
- **Personal audio files** (MP3, WAV, FLAC, etc.)
- **Virtual environments** (venv/, .venv/)
- **Generated projects** (projects/ directory)
- **Cache and temporary files** (.cache/, *.tmp)
- **System files** (.DS_Store, Thumbs.db)
- **IDE files** (.vscode/, .idea/)
- **Large model files** (*.pth, *.h5)

This ensures that when others clone your repository, they get a clean installation without your personal files.

### Customizing Settings
Edit `config.py` to adjust:
- Sample rates and audio quality
- Analysis parameters and thresholds
- Export formats and settings
- Performance and caching options

### Advanced Options
```python
# In config.py
SAMPLE_RATE = 44100          # Audio sample rate
STEM_METHOD_DEFAULT = "spleeter:2stems"  # Default separation
MELODY_CONF_THRESH = 0.5     # Melody detection confidence
DRUM_THRESH = {...}          # Drum detection thresholds
```

## 🐛 Troubleshooting

### Common Issues

**"Spleeter not available"**
```bash
pip install spleeter
```

**"CREPE not available"**
```bash
pip install crepe
```

**"Out of memory"**
- Reduce audio file size
- Use Spleeter instead of Demucs
- Close other applications

**"Slow processing"**
- Use Spleeter for faster separation
- Reduce audio quality in config
- Enable GPU acceleration (if available)

### Performance Tips
- Use Spleeter for quick iterations, Demucs for final quality
- Process shorter audio segments for testing
- Close other applications during processing
- Use SSD storage for faster file operations

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup
```bash
git clone https://github.com/Eli-Dolney/LTW_Audio_Spiltter.git
cd LTW_Audio_Spiltter
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies
```

### Running Tests
```bash
pytest tests/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Spleeter**: Audio source separation by Deezer
- **Demucs**: High-quality separation by Facebook Research
- **CREPE**: Pitch detection by Google Research
- **librosa**: Audio analysis library
- **Streamlit**: Web application framework

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Eli-Dolney/LTW_Audio_Spiltter/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Eli-Dolney/LTW_Audio_Spiltter/discussions)
- **Documentation**: [Wiki](https://github.com/Eli-Dolney/LTW_Audio_Spiltter/wiki)

## 🗺️ Roadmap

### Phase 1 (Current)
- ✅ Core stem separation
- ✅ Basic analysis features
- ✅ Streamlit interface
- ✅ Export functionality

### Phase 2 (Planned)
- 🔄 Advanced chord detection
- 🔄 Better drum transcription
- 🔄 Batch processing
- 🔄 Plugin architecture

### Phase 3 (Future)
- 🔮 Real-time processing
- 🔮 Advanced visualization
- 🔮 Machine learning enhancements
- 🔮 Mobile app

---

**Made with ❤️ for the music community**

*LTW Audio Splitter - Your local audio analysis companion*
