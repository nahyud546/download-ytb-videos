#!/usr/bin/env python3
"""
CLI: chỉ cần nhập link YouTube -> tải ngay MP4 chất lượng cao về ./downloads/

Cách dùng:
  python download.py "https://www.youtube.com/watch?v=..."
  python download.py --quality 1080p "https://youtu.be/..."
  python download.py   # -> chế độ nhập link tương tác (paste nhiều link, mỗi dòng 1 link)
  python download.py --out ./my_videos --quality best < urls.txt
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from downloader import download_video


def print_progress(d):
    if d.get("status") == "downloading":
        total = d.get("total_bytes") or d.get("total_bytes_estimate")
        downloaded = d.get("downloaded_bytes", 0)
        if total:
            pct = downloaded / total * 100
            speed = d.get("speed")
            speed_s = f" {speed/1024/1024:.1f} MB/s" if speed else ""
            print(f"\r  ... {pct:5.1f}% ({downloaded/1024/1024:.1f}/{total/1024/1024:.1f} MB){speed_s}", end="", flush=True)
        else:
            print(f"\r  ... {downloaded/1024/1024:.1f} MB", end="", flush=True)
    elif d.get("status") == "finished":
        print("\n  -> Đang merge về MP4...")


def download_one(url: str, outdir: Path, quality: str) -> int:
    url = url.strip()
    if not url or url.startswith("#"):
        return 0
    print(f"\n[+] Đang tải: {url}")
    try:
        fp = download_video(url, outdir=outdir, quality=quality, progress_hook=print_progress)
        size_mb = fp.stat().st_size / 1024 / 1024
        print(f"[OK] Đã lưu: {fp} ({size_mb:.1f} MB)")
        return 0
    except Exception as e:
        print(f"[FAIL] {e}", file=sys.stderr)
        return 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Nhập link YouTube -> tải MP4 high quality về local")
    ap.add_argument("url", nargs="?", help="Link YouTube (bỏ trống để nhập tương tác)")
    ap.add_argument("--out", "-o", default="downloads", help="Thư mục lưu (mặc định: downloads)")
    ap.add_argument("--quality", "-q", default="best", help="best | 1080p | 720p | 480p (mặc định: best)")
    args = ap.parse_args()

    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)

    # 1 link trực tiếp
    if args.url:
        return download_one(args.url, outdir, args.quality)

    # pipe từ stdin (urls.txt) hoặc tương tác
    if not sys.stdin.isatty():
        fail = 0
        for line in sys.stdin:
            fail |= download_one(line, outdir, args.quality)
        return fail

    # Chế độ tương tác: paste link, Enter là tải ngay
    print("=== YouTube -> MP4 (high quality) ===")
    print("Paste link YouTube rồi Enter (gõ q để thoát, mỗi dòng 1 link).")
    fail = 0
    while True:
        try:
            url = input("\nLink> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break
        if url.lower() in ("q", "quit", "exit"):
            break
        if not url:
            continue
        fail |= download_one(url, outdir, args.quality)
    return fail


if __name__ == "__main__":
    raise SystemExit(main())
