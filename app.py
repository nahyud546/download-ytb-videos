#!/usr/bin/env python3
"""
Web UI: mở trình duyệt, paste link YouTube, bấm Tải -> file MP4 lưu vào ./downloads/
Chạy:  python app.py
Mở:   http://127.0.0.1:5000
"""

from __future__ import annotations

import threading
import uuid
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_from_directory

from downloader import DEFAULT_OUTDIR, download_video, get_info

app = Flask(__name__)
JOBS: dict[str, dict] = {}  # job_id -> {status, url, file, error, progress}


def _run_job(job_id: str, url: str, quality: str):
    def hook(d):
        if d.get("status") == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)
            pct = (downloaded / total * 100) if total else 0
            JOBS[job_id]["progress"] = round(pct, 1)
        elif d.get("status") == "finished":
            JOBS[job_id]["progress"] = 100

    try:
        JOBS[job_id]["status"] = "downloading"
        fp = download_video(url, outdir=DEFAULT_OUTDIR, quality=quality, progress_hook=hook, quiet=True)
        JOBS[job_id].update(status="done", file=fp.name, progress=100)
    except Exception as e:  # noqa: BLE001
        JOBS[job_id].update(status="error", error=str(e))


@app.get("/")
def index():
    files = sorted(
        (p for p in Path(DEFAULT_OUTDIR).glob("*.mp4")),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )[:20]
    return render_template(
        "index.html",
        files=[{"name": p.name, "size_mb": round(p.stat().st_size / 1024 / 1024, 1)} for p in files],
    )


@app.post("/api/download")
def api_download():
    data = request.get_json(force=True, silent=True) or {}
    url = (data.get("url") or request.form.get("url") or "").strip()
    quality = (data.get("quality") or request.form.get("quality") or "best").strip()
    if not url:
        return jsonify({"ok": False, "error": "Thiếu link YouTube (url)."}), 400
    job_id = uuid.uuid4().hex[:8]
    JOBS[job_id] = {"status": "queued", "url": url, "progress": 0}
    threading.Thread(target=_run_job, args=(job_id, url, quality), daemon=True).start()
    return jsonify({"ok": True, "job_id": job_id})


@app.get("/api/status/<job_id>")
def api_status(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        return jsonify({"ok": False, "error": "Không tìm thấy job."}), 404
    return jsonify({"ok": True, "job": job})


@app.get("/api/info")
def api_info():
    url = (request.args.get("url") or "").strip()
    if not url:
        return jsonify({"ok": False, "error": "Thiếu ?url=..."}), 400
    try:
        return jsonify({"ok": True, "info": get_info(url)})
    except Exception as e:  # noqa: BLE001
        return jsonify({"ok": False, "error": str(e)}), 400


@app.get("/files/<path:name>")
def serve_file(name: str):
    return send_from_directory(DEFAULT_OUTDIR, name, as_attachment=True)


if __name__ == "__main__":
    Path(DEFAULT_OUTDIR).mkdir(parents=True, exist_ok=True)
    app.run(host="127.0.0.1", port=5000, debug=True)
