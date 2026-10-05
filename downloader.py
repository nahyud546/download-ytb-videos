"""
Core downloader: nhập link YouTube -> tải MP4 chất lượng cao, lưu local.
Dùng yt-dlp (cho kết quả tương đương ytsave.to/en2 nhưng ổn định hơn,
không bị Cloudflare challenge, không cần browser).

Lý do không scrape trực tiếp https://ytsave.to/en2/:
- Site dùng Cloudflare "Just a moment" challenge, block mọi request curl/python.
- Không có public API, HTML/JS obfuscated, endpoint đổi liên tục -> dễ gãy.
- yt-dlp cho cùng output: MP4 high quality, merge best video + best audio.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Callable, Optional

import yt_dlp


DEFAULT_OUTDIR = Path(__file__).parent / "downloads"


def sanitize_url(url: str) -> str:
    return url.strip().strip('"').strip("'")


def is_valid_youtube_url(url: str) -> bool:
    patterns = [
        r"(https?://)?(www\.|m\.|music\.)?(youtube\.com/(watch|shorts|embed|live)|youtu\.be/)",
    ]
    return any(re.search(p, url) for p in patterns)


def build_opts(
    outdir: Path,
    quality: str = "best",
    progress_hook: Optional[Callable] = None,
    quiet: bool = False,
) -> dict:
    """
    quality: "best" | "1080p" | "720p" | "480p" ...
      - "best": bestvideo+bestaudio merge -> mp4 (tương đương nút HD cao nhất trên ytsave.to)
      - "1080p"/"720p": giới hạn chiều cao <= N, vẫn ưu tiên mp4
    """
    outdir.mkdir(parents=True, exist_ok=True)
    outtmpl = str(outdir / "%(title)s [%(id)s].%(ext)s")

    if quality == "best":
        fmt = "bv*+ba/b"
    else:
        h = re.sub(r"\D", "", quality) or "720"
        # Ưu tiên mp4, giới hạn chiều cao, fallback best
        fmt = f"bv*[height<={h}]+ba/b[height<={h}]/b"

    opts: dict = {
        "format": fmt,
        "merge_output_format": "mp4",  # luôn ra .mp4
        "outtmpl": outtmpl,
        "noplaylist": True,  # mặc định chỉ tải 1 video, tránh tải nhầm cả playlist
        "retries": 5,
        "fragment_retries": 5,
        "concurrent_fragment_downloads": 4,
        "quiet": quiet,
        "no_warnings": False,
        # Ép remux về mp4 tương thích cao (h264/aac) khi cần
        "postprocessors": [
            {"key": "FFmpegVideoConvertor", "preferedformat": "mp4"},
        ],
        "prefer_ffmpeg": True,
    }
    if progress_hook:
        opts["progress_hooks"] = [progress_hook]
    return opts


def download_video(
    url: str,
    outdir: str | Path = DEFAULT_OUTDIR,
    quality: str = "best",
    progress_hook: Optional[Callable] = None,
    quiet: bool = False,
) -> Path:
    """Tải 1 video, trả về Path file mp4 đã lưu."""
    url = sanitize_url(url)
    if not url:
        raise ValueError("URL rỗng.")
    if not is_valid_youtube_url(url):
        raise ValueError(f"URL không phải YouTube hợp lệ: {url}")

    outdir = Path(outdir)
    opts = build_opts(outdir, quality, progress_hook, quiet)

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        # Trường hợp extract trả về playlist (dù đã noplaylist), lấy entry đầu
        if info is None:
            raise RuntimeError("Không lấy được info video (video riêng tư / bị chặn / sai link).")
        if "entries" in info and info["entries"]:
            info = info["entries"][0]
        filename = ydl.prepare_filename(info)
        # Sau postprocessor, ext thành .mp4
        p = Path(filename)
        mp4_candidate = p.with_suffix(".mp4")
        if mp4_candidate.exists():
            return mp4_candidate
        if p.exists():
            return p
        # Fallback: tìm file mới nhất theo id
        vid = info.get("id", "")
        matches = sorted(outdir.glob(f"*{vid}*.mp4"), key=os.path.getmtime)
        if matches:
            return matches[-1]
        raise FileNotFoundError("Tải xong nhưng không tìm thấy file mp4.")


def get_info(url: str) -> dict:
    """Lấy tiêu đề/thumbnail mà không tải (dùng cho Web UI preview)."""
    url = sanitize_url(url)
    opts = {"quiet": True, "no_warnings": True, "skip_download": True, "noplaylist": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if "entries" in info:
            info = info["entries"][0]
        return {
            "id": info.get("id"),
            "title": info.get("title"),
            "duration": info.get("duration"),
            "uploader": info.get("uploader"),
            "thumbnail": info.get("thumbnail"),
        }
