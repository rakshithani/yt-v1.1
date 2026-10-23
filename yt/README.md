# 🎬 YouTube Video & Audio Downloader

A clean, efficient, and modular YouTube downloader supporting both **CLI** and **Streamlit Web UI**. Built with [yt-dlp](https://github.com/yt-dlp/yt-dlp) and [FFmpeg](https://ffmpeg.org/) for pristine 1080p/4K MP4 stream merging and clean 192kbps MP3 audio extraction.

---

## ✨ Features

- **Dual Modes**: Use the interactive **CLI** terminal tool or launch the sleek **Streamlit Web UI**.
- **Granular Video Quality (144p to 4K)**: Download in 4K (2160p), 1440p (2K), 1080p (Full HD), 720p (HD), 480p, 360p, 240p, 144p, or Best Available.
- **Frame Rate (FPS) Selection**: Choose between 60 FPS (ultra-smooth), 30 FPS (standard motion), 24 FPS (cinematic rate), or Best Available FPS.
- **Audio Bitrate Selection**: Choose from 320 kbps (extreme fidelity), 256 kbps, 192 kbps (standard), 128 kbps, or 64 kbps MP3.
- **Automatic Stream Detection**: Detects all native resolutions and frame rates supported by the specific video and highlights them.
- **Real-Time Progress**: Live updates showing download percentage, transfer speed, and ETA.
- **FFmpeg Integration**: Automatic detection of FFmpeg with stream merging and audio post-processing.
- **Browser Playback & Direct Download**: In the Web UI, preview media directly in the browser, download locally, or save directly in-browser.
- **Robust Error Handling**: Friendly, actionable error messages for invalid URLs, missing FFmpeg, and network timeouts.

---

## 📁 Project Structure

```text
yt/
├── downloader.py      # Core modular downloader logic + interactive CLI
├── app.py             # Sleek modern Streamlit Web Application
├── requirements.txt   # Python package dependencies (yt-dlp, streamlit)
├── README.md          # Complete documentation and setup guide
└── downloads/         # Output directory (auto-created on first download)
```

---

## 🛠️ Prerequisites

1. **Python 3.8+** installed.
2. **FFmpeg** installed and accessible in your system `PATH`.
   - *Why FFmpeg?* YouTube serves high-definition video (1080p, 1440p, 4K) as separate video and audio streams. FFmpeg is required to merge them into a single `.mp4` file and to convert audio streams into clean `.mp3` files.

---

## ⚙️ FFmpeg Installation Guide

### 🪟 Windows
The easiest method is using the Windows Package Manager (`winget`):
```powershell
winget install Gyan.FFmpeg
```
*Alternatively, via Chocolatey:*
```powershell
choco install ffmpeg
```
*Or Manual:*
1. Download the release build from [gyan.dev/ffmpeg/builds](https://www.gyan.dev/ffmpeg/builds/).
2. Extract the zip and copy the path to the `bin/` folder (e.g., `C:\ffmpeg\bin`).
3. Add that path to your **System Environment Variables** under `PATH`.
4. Verify by running `ffmpeg -version` in a new PowerShell/Command Prompt window.

### 🍎 macOS
Using [Homebrew](https://brew.sh/):
```bash
brew install ffmpeg
```
Verify:
```bash
ffmpeg -version
```

### 🐧 Linux (Ubuntu / Debian / Mint)
```bash
sudo apt update
sudo apt install ffmpeg
```
*For Arch Linux:*
```bash
sudo pacman -S ffmpeg
```
*For Fedora / RHEL:*
```bash
sudo dnf install ffmpeg
```

---

## 🚀 Quick Start & Installation

### 1. Clone or Open the Workspace
```bash
cd c:\Games\yt
```

### 2. (Optional but Recommended) Create a Virtual Environment
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Python Dependencies
```bash
pip install -r requirements.txt
```

---

## 💻 Usage

### 1. Terminal / CLI Version (`downloader.py`)

#### Interactive Mode
Run the script without arguments for a guided terminal experience:
```bash
python downloader.py
```
You will be prompted to:
1. Paste the YouTube URL.
2. Choose format: `[1] Video (.mp4)` or `[2] Audio (.mp3)`.
3. Specify destination directory (or press Enter for default `downloads/`).

#### Command-Line Arguments Mode
You can also run directly with arguments:

```bash
# Download Best Quality Video (.mp4)
python downloader.py -u "https://www.youtube.com/watch?v=dQw4w9WgXcQ" -f video

# Download Best Quality Audio (.mp3)
python downloader.py -u "https://www.youtube.com/watch?v=dQw4w9WgXcQ" -f audio

# Specify custom output directory
python downloader.py -u "https://www.youtube.com/watch?v=dQw4w9WgXcQ" -f audio -o "my_music"
```

Available flags:
- `-u`, `--url`: Target YouTube URL.
- `-f`, `--format`: Format choice (`video`, `audio`, `mp4`, `mp3`). Default: `video`.
- `-o`, `--output`: Destination directory. Default: `downloads`.

---

### 2. Web UI Version (`app.py`)

Launch the Streamlit web interface:
```bash
streamlit run app.py
```
Your browser will open automatically at `http://localhost:8501`.

#### Web UI Highlights:
- **System Check Badge**: Instantly shows if FFmpeg is detected.
- **Metadata Preview**: Automatically previews title, channel, duration, and thumbnail.
- **Live Progress & Status**: Shows real-time percentage, download speed, ETA, and post-processing indicators.
- **In-Browser Player & Direct Download**: Listen to or watch the downloaded media right inside the web page, or click the download button to save it through your browser.

---

## 🧩 Python API / Code Reusability

`downloader.py` provides modular functions you can import into any Python project:

```python
from downloader import download_media, get_video_info, check_ffmpeg

# Check FFmpeg status
if not check_ffmpeg():
    print("Warning: FFmpeg is missing!")

# Get video details before downloading
info = get_video_info("https://www.youtube.com/watch?v=example")
print(f"Title: {info['title']}, Duration: {info['duration_formatted']}")

# Download media with progress tracking
def my_progress_hook(data):
    if data['status'] == 'downloading':
        print(f"Progress: {data['percent']}% at {data['speed']}")

result = download_media(
    url="https://www.youtube.com/watch?v=example",
    format_type="audio",       # 'video' or 'audio'
    output_dir="downloads",
    progress_callback=my_progress_hook
)

print(f"Saved to: {result['filepath']}")
```

---

## ❓ Troubleshooting

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| `FFmpeg was not found on your system PATH` | FFmpeg is not installed or terminal PATH hasn't reloaded. | Install FFmpeg using `winget install Gyan.FFmpeg` (Windows) or `brew install ffmpeg` (Mac). Restart your terminal. |
| `Failed to fetch video details: Video unavailable` | URL is invalid, video is private, or region blocked. | Verify the URL plays in a private browser window. |
| `Sign in to confirm you're not a bot` | YouTube rate limiting or automated query detection. | Update `yt-dlp` to latest version (`pip install --upgrade yt-dlp`). |
| Streamlit command not found | Python Scripts folder not in PATH. | Run `python -m streamlit run app.py` instead. |

---

## 📜 License
This project is for educational and personal use in accordance with YouTube's Terms of Service and applicable copyright laws.
