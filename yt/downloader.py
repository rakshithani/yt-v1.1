"""
YouTube Video and Audio Downloader (CLI & Core Library)
Uses yt-dlp and FFmpeg for high-quality video and MP3 extraction.
"""

import os
import sys
import shutil
import argparse
from typing import Optional, Callable, Dict, Any
import yt_dlp


class DownloaderError(Exception):
    """Custom exception raised for downloader-specific issues."""
    pass


class _SilentLogger:
    """Internal logger to suppress raw stdout/stderr clutter from yt-dlp."""
    def debug(self, msg): pass
    def info(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): pass


def check_ffmpeg() -> bool:
    """
    Check if FFmpeg is installed and accessible in the system PATH.
    Automatically detects Windows WinGet packages if not yet added to current process PATH.
    Returns:
        bool: True if FFmpeg is found, False otherwise.
    """
    if shutil.which("ffmpeg") is not None:
        return True

    # Windows fallback: check WinGet package directories
    winget_root = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages")
    if os.path.isdir(winget_root):
        for root, _, files in os.walk(winget_root):
            if "ffmpeg.exe" in files:
                # Add found ffmpeg directory to current process PATH
                if root not in os.environ.get("PATH", ""):
                    os.environ["PATH"] = root + os.pathsep + os.environ.get("PATH", "")
                return True

    return False


def format_bytes(bytes_num: Optional[float]) -> str:
    """Format bytes into human-readable string (KB, MB, GB)."""
    if bytes_num is None or bytes_num <= 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    unit_index = 0
    size = float(bytes_num)
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1
    return f"{size:.2f} {units[unit_index]}"


def format_duration(seconds: Optional[int]) -> str:
    """Format seconds into HH:MM:SS or MM:SS."""
    if not seconds:
        return "00:00"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def parse_resolution(quality_str: Optional[str]) -> Optional[int]:
    """
    Extract integer video height (e.g. 2160 for 4K, 1080 for Full HD, 144, etc.).
    Returns None if 'best' or unspecified.
    """
    if not quality_str:
        return None
    q = str(quality_str).lower().strip()
    if "best" in q or "max" in q or "highest" in q:
        return None
    if "4k" in q or "2160" in q:
        return 2160
    if "1440" in q or "2k" in q or "qhd" in q:
        return 1440
    import re
    match = re.search(r"(\d{3,4})", q)
    if match:
        return int(match.group(1))
    return None


def parse_audio_bitrate(quality_str: Optional[str]) -> str:
    """Extract audio bitrate string (e.g. '320', '256', '192', '128', '64'). Default '192'."""
    if not quality_str:
        return "192"
    q = str(quality_str).lower().strip()
    import re
    match = re.search(r"(320|256|192|128|64)", q)
    if match:
        return match.group(1)
    return "192"


def parse_fps(fps_str: Optional[Any]) -> Optional[int]:
    """
    Extract target frame rate (e.g. 60, 30, 24).
    Returns None if 'best', 'any', or unspecified.
    """
    if not fps_str:
        return None
    s = str(fps_str).lower().strip()
    if "best" in s or "any" in s or "max" in s or "native" in s:
        return None
    import re
    match = re.search(r"(60|50|30|25|24)", s)
    if match:
        return int(match.group(1))
    return None


def get_video_info(url: str) -> Dict[str, Any]:
    """
    Fetch metadata, available video resolutions, and frame rates for a given YouTube URL.

    Args:
        url: Valid YouTube video URL.

    Returns:
        Dict containing title, uploader, duration, thumbnail, available_resolutions, available_fps, etc.
    """
    if not url or not url.strip():
        raise DownloaderError("Please provide a valid YouTube URL.")

    ydl_opts = {
        "quiet": True,
        "noprogress": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": False,
        "logger": _SilentLogger(),
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url.strip(), download=False)
            if not info:
                raise DownloaderError("Unable to fetch video information.")

            # Extract distinct available video heights and FPS
            formats = info.get("formats", [])
            heights = sorted(
                list(set(f.get("height") for f in formats if f.get("height") and f.get("vcodec") != "none")),
                reverse=True,
            )
            fps_options = sorted(
                list(set(int(f.get("fps")) for f in formats if f.get("fps") and f.get("vcodec") != "none")),
                reverse=True,
            )

            return {
                "id": info.get("id"),
                "title": info.get("title", "Unknown Title"),
                "uploader": info.get("uploader", "Unknown Channel"),
                "duration": info.get("duration", 0),
                "duration_formatted": format_duration(info.get("duration")),
                "thumbnail": info.get("thumbnail"),
                "view_count": info.get("view_count", 0),
                "webpage_url": info.get("webpage_url", url),
                "available_resolutions": heights,
                "available_fps": fps_options,
                "max_fps": max(fps_options) if fps_options else 30,
            }
    except yt_dlp.utils.DownloadError as e:
        clean_msg = str(e).split("ERROR:")[-1].strip()
        raise DownloaderError(f"Failed to fetch video details: {clean_msg}")
    except Exception as e:
        raise DownloaderError(f"Unexpected error while fetching video details: {str(e)}")


def download_media(
    url: str,
    format_type: str = "video",
    quality: Optional[str] = "best",
    fps: Optional[Any] = "best",
    output_dir: str = "downloads",
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> Dict[str, Any]:
    """
    Download a YouTube video (144p up to 4K MP4, with FPS selection) or extract audio (MP3) using yt-dlp and FFmpeg.

    Args:
        url: YouTube video URL.
        format_type: 'video' (or 'mp4') or 'audio' (or 'mp3').
        quality: Desired resolution (e.g. '2160', '1080', '720', '480', '360', '240', '144', or 'best')
                 or audio bitrate ('320', '256', '192', '128', '64'). Default: 'best'.
        fps: Target frame rate (e.g. '60', '30', '24', or 'best'). Default: 'best'.
        output_dir: Destination folder (automatically created if not present).
        progress_callback: Optional callable receiving progress/status dictionaries.

    Returns:
        Dict containing success status, title, filepath, format, quality, resolution, fps, and metadata.
    """
    if not url or not url.strip():
        raise DownloaderError("Please provide a valid YouTube URL.")

    clean_url = url.strip()
    norm_format = format_type.strip().lower()

    if norm_format not in ["video", "audio", "mp4", "mp3"]:
        raise DownloaderError(
            f"Unsupported format '{format_type}'. Allowed options are 'video' (or 'mp4') and 'audio' (or 'mp3')."
        )

    is_audio = norm_format in ["audio", "mp3"]
    ffmpeg_available = check_ffmpeg()

    # Audio extraction to MP3 requires FFmpeg
    if is_audio and not ffmpeg_available:
        raise DownloaderError(
            "FFmpeg was not found on your system PATH.\n"
            "FFmpeg is required to extract and convert audio to MP3.\n"
            "Please install FFmpeg:\n"
            "  - Windows: winget install Gyan.FFmpeg\n"
            "  - macOS:   brew install ffmpeg\n"
            "  - Linux:   sudo apt install ffmpeg"
        )

    # Prepare output directory
    abs_output_dir = os.path.abspath(output_dir)
    os.makedirs(abs_output_dir, exist_ok=True)

    # Define progress and post-processor hooks
    def _progress_hook(d: Dict[str, Any]):
        if not progress_callback:
            return
        status = d.get("status")
        if status == "downloading":
            downloaded = d.get("downloaded_bytes", 0)
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            percent = (downloaded / total * 100.0) if total > 0 else 0.0
            speed = d.get("_speed_str", "N/A")
            eta = d.get("_eta_str", "N/A")
            filename = os.path.basename(d.get("filename", ""))

            progress_callback({
                "status": "downloading",
                "percent": round(percent, 2),
                "downloaded_bytes": downloaded,
                "total_bytes": total,
                "speed": speed,
                "eta": eta,
                "filename": filename,
                "message": f"Downloading: {percent:.1f}% ({speed} | ETA: {eta})"
            })
        elif status == "finished":
            filename = os.path.basename(d.get("filename", ""))
            progress_callback({
                "status": "download_complete",
                "percent": 100.0,
                "filename": filename,
                "message": "Download finished. Processing..."
            })

    def _postprocessor_hook(d: Dict[str, Any]):
        if not progress_callback:
            return
        status = d.get("status")
        pp_name = d.get("postprocessor", "")
        if status == "started":
            if "ExtractAudio" in pp_name:
                msg = "Converting audio to MP3..."
            elif "Merger" in pp_name or "Fixup" in pp_name:
                msg = "Merging video and audio streams into MP4..."
            else:
                msg = f"Post-processing ({pp_name})..."

            progress_callback({
                "status": "processing",
                "percent": 100.0,
                "message": msg
            })
        elif status == "finished":
            progress_callback({
                "status": "processing_done",
                "percent": 100.0,
                "message": "Finalizing file..."
            })

    # Base output template
    outtmpl = os.path.join(abs_output_dir, "%(title)s.%(ext)s")

    # Configure yt-dlp options
    ydl_opts: Dict[str, Any] = {
        "outtmpl": outtmpl,
        "noplaylist": True,
        "quiet": True,
        "noprogress": True,
        "no_warnings": True,
        "logger": _SilentLogger(),
        "progress_hooks": [_progress_hook],
        "postprocessor_hooks": [_postprocessor_hook],
    }

    target_height = parse_resolution(quality) if not is_audio else None
    target_fps = parse_fps(fps) if not is_audio else None
    audio_bitrate = parse_audio_bitrate(quality) if is_audio else "192"

    if is_audio:
        ydl_opts.update({
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": audio_bitrate,
                }
            ],
        })
    else:
        # FPS condition filter
        if target_fps and target_fps >= 50:
            fps_cond = "[fps>=50]"
        elif target_fps and target_fps == 30:
            fps_cond = "[fps<=30]"
        elif target_fps and target_fps <= 25:
            fps_cond = "[fps<=25]"
        else:
            fps_cond = ""

        # Video format with resolution & FPS selection
        if ffmpeg_available:
            if target_height and fps_cond:
                format_expr = (
                    f"bestvideo[height={target_height}]{fps_cond}+bestaudio/"
                    f"bestvideo[height<={target_height}]{fps_cond}+bestaudio/"
                    f"bestvideo[height={target_height}]+bestaudio/"
                    f"bestvideo[height<={target_height}]+bestaudio/"
                    f"best[height<={target_height}]/best"
                )
            elif target_height:
                format_expr = (
                    f"bestvideo[height={target_height}]+bestaudio/"
                    f"bestvideo[height<={target_height}]+bestaudio/"
                    f"best[height<={target_height}]/best"
                )
            elif fps_cond:
                format_expr = f"bestvideo{fps_cond}+bestaudio/bestvideo+bestaudio/best"
            else:
                format_expr = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best"

            ydl_opts.update({
                "format": format_expr,
                "merge_output_format": "mp4",
            })
        else:
            if target_height:
                format_expr = f"best[height<={target_height}][ext=mp4]/best[height<={target_height}]/best"
            else:
                format_expr = "best[ext=mp4]/best"

            ydl_opts.update({
                "format": format_expr,
            })

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info and download
            info_dict = ydl.extract_info(clean_url, download=True)
            if not info_dict:
                raise DownloaderError("Failed to extract media information from URL.")

            # Determine final file path
            expected_filename = ydl.prepare_filename(info_dict)
            base_root, _ = os.path.splitext(expected_filename)

            if is_audio:
                final_filepath = f"{base_root}.mp3"
            else:
                if ffmpeg_available:
                    final_filepath = f"{base_root}.mp4"
                else:
                    final_filepath = expected_filename

            # If the calculated path doesn't exist, search the directory for the matching file
            if not os.path.exists(final_filepath):
                target_ext = ".mp3" if is_audio else ".mp4"
                video_id = info_dict.get("id", "")
                raw_title = info_dict.get("title", "")
                candidates = []
                for candidate in os.listdir(abs_output_dir):
                    if candidate.endswith(target_ext):
                        full_cand = os.path.join(abs_output_dir, candidate)
                        candidates.append((full_cand, os.path.getmtime(full_cand)))
                        if video_id and video_id in candidate:
                            final_filepath = full_cand
                            break
                        if raw_title and raw_title[:15].lower() in candidate.lower():
                            final_filepath = full_cand
                            break
                else:
                    if candidates and not os.path.exists(final_filepath):
                        # Pick the most recently created candidate
                        candidates.sort(key=lambda x: x[1], reverse=True)
                        final_filepath = candidates[0][0]

            file_size = os.path.getsize(final_filepath) if os.path.exists(final_filepath) else 0

            # Compute human-readable format and FPS labels
            actual_fps = info_dict.get("fps")
            fps_display = f"{int(actual_fps)} fps" if actual_fps else (f"{target_fps} fps" if target_fps else "Native FPS")

            if is_audio:
                format_label = f"Audio ({audio_bitrate} kbps MP3)"
                res_label = f"{audio_bitrate} kbps"
            else:
                res_label = f"{target_height}p" if target_height else (f"{info_dict.get('height')}p" if info_dict.get('height') else "Best Available")
                format_label = f"Video ({res_label} @ {fps_display} MP4)"

            return {
                "success": True,
                "title": info_dict.get("title", "Unknown Title"),
                "uploader": info_dict.get("uploader", "Unknown Channel"),
                "duration": info_dict.get("duration", 0),
                "duration_formatted": format_duration(info_dict.get("duration")),
                "thumbnail": info_dict.get("thumbnail"),
                "format": format_label,
                "quality": quality,
                "resolution": res_label,
                "fps": fps_display,
                "filepath": final_filepath,
                "filename": os.path.basename(final_filepath),
                "filesize_bytes": file_size,
                "filesize_formatted": format_bytes(file_size),
                "output_dir": abs_output_dir,
            }

    except yt_dlp.utils.DownloadError as e:
        clean_msg = str(e).split("ERROR:")[-1].strip()
        raise DownloaderError(f"Download Error: {clean_msg}")
    except DownloaderError:
        raise
    except Exception as e:
        raise DownloaderError(f"An unexpected error occurred: {str(e)}")


def cli_progress_handler(data: Dict[str, Any]):
    """CLI terminal progress renderer."""
    status = data.get("status")
    if status == "downloading":
        percent = data.get("percent", 0.0)
        speed = data.get("speed", "N/A")
        eta = data.get("eta", "N/A")
        bar_len = 30
        filled = int(bar_len * (percent / 100.0))
        bar = "█" * filled + "░" * (bar_len - filled)
        sys.stdout.write(f"\r  [{bar}] {percent:5.1f}% | {speed} | ETA: {eta}  ")
        sys.stdout.flush()
    elif status == "download_complete":
        sys.stdout.write("\n  ✓ Download stream finished. Handing off to FFmpeg...\n")
        sys.stdout.flush()
    elif status == "processing":
        message = data.get("message", "Processing...")
        sys.stdout.write(f"  ⚙ {message}\n")
        sys.stdout.flush()


def run_cli():
    """Main CLI execution handler with interactive mode support."""
    parser = argparse.ArgumentParser(
        description="Clean & Efficient YouTube Video and Audio Downloader (yt-dlp)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-u", "--url", type=str, help="YouTube video URL")
    parser.add_argument(
        "-f",
        "--format",
        choices=["video", "audio", "mp4", "mp3"],
        default="video",
        help="Download format: 'video' (best .mp4) or 'audio' (best .mp3). Default: video",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="downloads",
        help="Destination folder for downloads (default: 'downloads')",
    )

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print(" 🎬  YouTube Video & Audio Downloader (yt-dlp + FFmpeg)")
    print("=" * 60)

    # Check FFmpeg
    ffmpeg_ok = check_ffmpeg()
    if ffmpeg_ok:
        print("  [✓] FFmpeg detected on system PATH.")
    else:
        print("  [!] Warning: FFmpeg not found on PATH. Audio MP3 extraction requires FFmpeg.")

    url = args.url
    format_choice = args.format
    output_dir = args.output

    # Interactive prompt if URL is not provided via flags
    if not url:
        try:
            url = input("\n👉 Enter YouTube URL: ").strip()
            if not url:
                print("❌ Error: No URL provided. Exiting.")
                sys.exit(1)

            print("\nSelect format:")
            print("  [1] Best Quality Video (.mp4)")
            print("  [2] Best Quality Audio (.mp3)")
            choice = input("Enter choice (1 or 2, default: 1): ").strip()
            format_choice = "audio" if choice == "2" else "video"

            custom_out = input(f"Destination folder (default: '{output_dir}'): ").strip()
            if custom_out:
                output_dir = custom_out

        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user.")
            sys.exit(0)

    print(f"\nTarget Format : {'🎵 Audio (MP3)' if format_choice in ['audio', 'mp3'] else '🎬 Video (MP4)'}")
    print(f"Output Folder : {os.path.abspath(output_dir)}")
    print("\nFetching video information...")

    try:
        info = get_video_info(url)
        print(f"  Title    : {info.get('title')}")
        print(f"  Channel  : {info.get('uploader')}")
        print(f"  Duration : {info.get('duration_formatted')}")
        print("\nStarting download...")

        result = download_media(
            url=url,
            format_type=format_choice,
            output_dir=output_dir,
            progress_callback=cli_progress_handler,
        )

        print("\n" + "-" * 60)
        print("🎉 SUCCESS! Download and processing complete.")
        print(f"  File: {result['filename']}")
        print(f"  Size: {result['filesize_formatted']}")
        print(f"  Saved to: {result['filepath']}")
        print("-" * 60 + "\n")

    except DownloaderError as e:
        print(f"\n❌ Error: {e}\n")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n❌ Download aborted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected Failure: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    run_cli()
