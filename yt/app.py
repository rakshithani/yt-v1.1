"""
YouTube Video and Audio Downloader (Streamlit Web UI)
A clean, sleek browser interface powered by yt-dlp and FFmpeg.
"""

import os
import streamlit as st
from downloader import (
    download_media,
    get_video_info,
    check_ffmpeg,
    DownloaderError,
    format_bytes,
)

# Page configuration
st.set_page_config(
    page_title="YouTube Media Downloader",
    page_icon="🎬",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Custom modern CSS styling
st.markdown(
    """
    <style>
    /* Modern card and container styling */
    .main-header {
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .main-header h1 {
        font-weight: 800;
        background: linear-gradient(135deg, #FF4B4B 0%, #FF8533 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.25rem;
    }
    .main-header p {
        color: #888888;
        font-size: 1.05rem;
    }
    .info-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 16px;
        margin-top: 15px;
        margin-bottom: 15px;
    }
    .success-badge {
        display: inline-block;
        background: #1e4620;
        color: #4ade80;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .status-pill {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .status-ok {
        background: rgba(34, 197, 94, 0.15);
        color: #22c55e;
        border: 1px solid rgba(34, 197, 94, 0.3);
    }
    .status-warn {
        background: rgba(234, 179, 8, 0.15);
        color: #eab308;
        border: 1px solid rgba(234, 179, 8, 0.3);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Header Section
st.markdown(
    """
    <div class="main-header">
        <h1>🎬 YouTube Media Downloader</h1>
        <p>Download pristine 1080p/4K MP4 videos or extract clean 192kbps MP3 audio</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Sidebar - Settings & System Status
with st.sidebar:
    st.header("⚙️ System Status")
    ffmpeg_ok = check_ffmpeg()
    if ffmpeg_ok:
        st.markdown(
            '<div class="status-pill status-ok">🟢 FFmpeg Detected</div>',
            unsafe_allow_html=True,
        )
        st.caption("Stream merging and audio extraction are fully supported.")
    else:
        st.markdown(
            '<div class="status-pill status-warn">⚠️ FFmpeg Missing</div>',
            unsafe_allow_html=True,
        )
        st.warning(
            "FFmpeg is not in system PATH. Audio conversion to MP3 requires FFmpeg.\n\n"
            "**Install:**\n"
            "- Windows: `winget install Gyan.FFmpeg`\n"
            "- Mac: `brew install ffmpeg`\n"
            "- Linux: `sudo apt install ffmpeg`"
        )

    st.divider()
    st.subheader("📁 Output Directory")
    default_dir = os.path.abspath("downloads")
    output_dir = st.text_input(
        "Save files to:",
        value="downloads",
        help="Local folder where media files will be saved on your machine.",
    )
    st.caption(f"Full Path: `{os.path.abspath(output_dir)}`")

    st.divider()
    st.subheader("💡 Features")
    st.markdown(
        """
        - **High Quality**: Merges best video and audio streams seamlessly.
        - **Clean MP3**: Direct extraction with ID3 preservation.
        - **Direct Download**: Save locally or download directly in your browser.
        - **CLI Included**: Run via terminal anytime with `python downloader.py`.
        """
    )

# Initialize session state variables
if "preview_cache" not in st.session_state:
    st.session_state["preview_cache"] = {}
if "download_result" not in st.session_state:
    st.session_state["download_result"] = None
if "last_url" not in st.session_state:
    st.session_state["last_url"] = ""

# Main Form Area
with st.container():
    url_input = st.text_input(
        "YouTube Video URL",
        placeholder="https://www.youtube.com/watch?v=... or https://youtu.be/...",
        help="Paste any standard YouTube or YouTube Shorts URL here.",
    )

clean_url = url_input.strip()

# If user changed or cleared URL, reset previous download result
if clean_url != st.session_state["last_url"]:
    st.session_state["download_result"] = None
    st.session_state["last_url"] = clean_url

# Video Preview Section (cached in session state to avoid redundant network calls)
info = None
if clean_url and st.session_state["download_result"] is None:
    if clean_url in st.session_state["preview_cache"]:
        info = st.session_state["preview_cache"][clean_url]
    else:
        try:
            with st.spinner("Fetching video preview and available streams..."):
                info = get_video_info(clean_url)
                st.session_state["preview_cache"][clean_url] = info
        except Exception:
            info = None

    if info:
        with st.container():
            col_thumb, col_details = st.columns([1, 2])
            with col_thumb:
                if info.get("thumbnail"):
                    st.image(info["thumbnail"], width="stretch")
            with col_details:
                st.subheader(info.get("title", "Unknown Title"))
                st.write(f"👤 **Channel:** {info.get('uploader')}")
                st.write(f"⏱️ **Duration:** {info.get('duration_formatted')} | 👁️ **Views:** {info.get('view_count', 0):,}")

                # Display available resolutions and frame rates detected on this video
                avail_res = info.get("available_resolutions", [])
                avail_fps = info.get("available_fps", [])
                if avail_res or avail_fps:
                    res_badges = " ".join([f"`{r}p`" for r in avail_res if r in [2160, 1440, 1080, 720, 480, 360, 240, 144]])
                    fps_badges = " ".join([f"`{f}fps`" for f in avail_fps if f in [60, 50, 30, 25, 24, 15]])
                    caption_text = []
                    if res_badges:
                        caption_text.append(f"📺 **Resolutions:** {res_badges}")
                    if fps_badges:
                        caption_text.append(f"⚡ **Frame Rates:** {fps_badges}")
                    st.caption(" | ".join(caption_text))

# Quality & FPS options definition
ALL_VIDEO_QUALITIES = [
    ("best", "🌟 Best Available (Highest Native Resolution)"),
    ("2160", "📺 4K (2160p Ultra HD)"),
    ("1440", "🖥️ 1440p (2K QHD)"),
    ("1080", "✨ 1080p (Full HD)"),
    ("720", "⚡ 720p (HD)"),
    ("480", "📱 480p (Standard Definition)"),
    ("360", "📉 360p (Medium)"),
    ("240", "💾 240p (Low Bandwidth)"),
    ("144", "📦 144p (Smallest File)"),
]

AUDIO_QUALITIES = [
    ("320", "🎧 320 kbps (Extreme Fidelity)"),
    ("256", "🎶 256 kbps (Very High Quality)"),
    ("192", "🎵 192 kbps (Standard High Quality - Recommended)"),
    ("128", "📻 128 kbps (Good Quality)"),
    ("64", "🎙️ 64 kbps (Voice / Smallest File)"),
]

# Dynamically tag resolutions & FPS if preview is already loaded
detected_heights = set(info.get("available_resolutions", [])) if info else set()
detected_fps = set(info.get("available_fps", [])) if info else set()

video_options = []
for val, label in ALL_VIDEO_QUALITIES:
    if val != "best" and detected_heights:
        if int(val) in detected_heights:
            label += "  [✓ Native]"
        elif int(val) > max(detected_heights):
            label += "  [Exceeds Video Max]"
    video_options.append((val, label))

# FPS Options
fps_options = [
    ("best", "🌟 Best / Highest Available FPS"),
]
if detected_fps:
    has_60 = any(f >= 50 for f in detected_fps)
    label_60 = "⚡ 60 FPS (Ultra Smooth)  [✓ Available]" if has_60 else f"⚡ 60 FPS (Max: {max(detected_fps)} fps)"
    fps_options.append(("60", label_60))
    fps_options.append(("30", "🎬 30 FPS (Standard Motion)"))
    fps_options.append(("24", "🎞️ 24 FPS (Cinematic Rate)"))
else:
    fps_options.extend([
        ("60", "⚡ 60 FPS (Ultra Smooth)"),
        ("30", "🎬 30 FPS (Standard Motion)"),
        ("24", "🎞️ 24 FPS (Cinematic Rate)"),
    ])

format_selection = st.radio(
    "Choose Media Type",
    options=["🎬 Video (.mp4)", "🎵 Audio (.mp3)"],
    horizontal=True,
)
is_audio = "Audio" in format_selection
format_type = "audio" if is_audio else "video"

if not is_audio:
    col_res, col_fps = st.columns([3, 2])
    with col_res:
        quality_choice = st.selectbox(
            "Select Video Resolution (144p to 4K)",
            options=[opt[0] for opt in video_options],
            format_func=lambda x: dict(video_options).get(x, x),
            index=0,
            help="Choose your preferred video resolution from 144p up to 4K.",
        )
    with col_fps:
        fps_choice = st.selectbox(
            "Select Frame Rate (FPS)",
            options=[opt[0] for opt in fps_options],
            format_func=lambda x: dict(fps_options).get(x, x),
            index=0,
            help="Choose 60 FPS for ultra-smooth playback or 30 FPS for standard file sizes.",
        )
else:
    fps_choice = "best"
    quality_choice = st.selectbox(
        "Select Audio Bitrate",
        options=[opt[0] for opt in AUDIO_QUALITIES],
        format_func=lambda x: dict(AUDIO_QUALITIES).get(x, x),
        index=2,
        help="Higher bitrate delivers richer sound quality.",
    )

download_btn = st.button("🚀 Download Media", type="primary", use_container_width=True)

# Download Processing Section
if download_btn:
    if not clean_url:
        st.error("⚠️ Please enter a valid YouTube URL first.")
    elif format_type == "audio" and not ffmpeg_ok:
        st.error(
            "❌ Cannot process MP3: FFmpeg is required for audio extraction but was not found in your system PATH.\n"
            "Please install FFmpeg or choose Video format."
        )
    else:
        progress_bar = st.progress(0)
        status_box = st.empty()
        status_box.info("⏳ Initializing yt-dlp downloader...")

        def update_progress(data: dict):
            status = data.get("status")
            if status == "downloading":
                pct = float(data.get("percent", 0.0)) / 100.0
                pct = max(0.0, min(1.0, pct))
                progress_bar.progress(pct)
                status_box.markdown(
                    f"**📥 Downloading:** `{data.get('percent', 0.0)}%` "
                    f"| **Speed:** `{data.get('speed', 'N/A')}` "
                    f"| **ETA:** `{data.get('eta', 'N/A')}`"
                )
            elif status == "download_complete":
                progress_bar.progress(1.0)
                status_box.markdown("🔄 **Download stream complete.** Starting FFmpeg processing...")
            elif status == "processing":
                progress_bar.progress(1.0)
                status_box.markdown(f"⚙️ **{data.get('message', 'Processing media...')}**")
            elif status == "processing_done":
                status_box.markdown("✨ **Finalizing saved file...**")

        try:
            result = download_media(
                url=clean_url,
                format_type=format_type,
                quality=quality_choice,
                fps=fps_choice,
                output_dir=output_dir,
                progress_callback=update_progress,
            )
            st.session_state["download_result"] = result
            progress_bar.progress(1.0)
            status_box.empty()
        except DownloaderError as e:
            status_box.empty()
            st.error(f"❌ {e}")
        except Exception as e:
            status_box.empty()
            st.error(f"❌ Unexpected Error: {e}")

# Render Completed Download Details (persists across clicks & browser download)
result = st.session_state.get("download_result")
if result:
    st.success("🎉 Download and conversion completed successfully!")
    with st.container():
        st.markdown("### 📦 Download Details")
        st.write(f"**Title:** {result['title']}")
        st.write(f"**Channel:** {result['uploader']}")
        st.write(f"**Format:** {result['format']}")
        st.write(f"**Resolution / Quality:** `{result.get('resolution', 'N/A')}`")
        if not result["format"].startswith("Audio"):
            st.write(f"**Frame Rate:** `{result.get('fps', 'N/A')}`")
        st.write(f"**File Size:** {result['filesize_formatted']}")
        st.write(f"**Saved Locally To:** `{result['filepath']}`")

        filepath = result["filepath"]
        if os.path.exists(filepath):
            with open(filepath, "rb") as file:
                file_bytes = file.read()

            is_mp3 = result["format"].startswith("Audio")
            mime_type = "audio/mpeg" if is_mp3 else "video/mp4"

            col_dl, col_reset = st.columns([1, 1])
            with col_dl:
                st.download_button(
                    label=f"💾 Save {result['format']} to Browser",
                    data=file_bytes,
                    file_name=result["filename"],
                    mime=mime_type,
                    use_container_width=True,
                )
            with col_reset:
                if st.button("🔄 Download Another", use_container_width=True):
                    st.session_state["download_result"] = None
                    st.rerun()

            # In-browser media player preview
            st.divider()
            st.markdown("#### 🎧 Media Preview")
            if is_mp3:
                st.audio(file_bytes, format="audio/mp3")
            else:
                st.video(file_bytes, format="video/mp4")

