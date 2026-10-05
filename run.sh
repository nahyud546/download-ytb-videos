#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
python3 -m pip install -r requirements.txt
# ffmpeg bắt buộc để merge best video+audio -> mp4
if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "[*] Chưa có ffmpeg, đang cài (cần sudo)..."
  sudo apt update && sudo apt install -y ffmpeg
fi
mkdir -p downloads
echo "OK. Chạy:  python3 download.py  |  hoặc:  python3 app.py"
