# Auto Download YouTube Video → MP4

Chỉ cần **nhập link YouTube → tự tải file MP4 chất lượng cao, lưu local** trong `downloads/`.

> Ghi chú về `https://ytsave.to/en2/`:
> Site này dùng Cloudflare challenge + không có public API nên **không scrape ổn định được bằng code**
> (curl/python đều bị 403 "Just a moment"). Repo này dùng `yt-dlp` — cho **cùng kết quả**
> (MP4, best video + best audio, merge về `.mp4`) nhưng ổn định, không cần browser.

## 1. Cài đặt (1 lần)

```bash
chmod +x run.sh
./run.sh
# hoặc thủ công:
pip install -r requirements.txt
sudo apt install -y ffmpeg   # bắt buộc để merge lên 1080p/4K
```

## 2. Cách dùng

### Cách A — CLI (nhanh nhất, chỉ nhập link là tải)

```bash
# Tải ngay 1 link, chất lượng cao nhất:
python3 download.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Giới hạn 1080p / 720p, đổi thư mục lưu:
python3 download.py -q 1080p -o ./downloads "https://youtu.be/xxxx"

# Chế độ tương tác (paste nhiều link, mỗi dòng 1 link, gõ q để thoát):
python3 download.py

# Tải hàng loạt từ file:
python3 download.py < urls.txt
```

File lưu ở: `downloads/<Tiêu đề> [<id>].mp4`

### Cách B — Web UI (paste link trên trình duyệt)

```bash
python3 app.py
# mở http://127.0.0.1:5000 -> paste link -> chọn Best/1080p/720p -> Tải ngay
```

API (nếu cần tích hợp):
- `POST /api/download  {"url": "...", "quality": "best"}` → `{"job_id": "..."}`
- `GET  /api/status/<job_id>` → `{status, progress, file, error}`
- `GET  /api/info?url=...` → `{title, thumbnail, duration, ...}`
- `GET  /files/<tên file>` → tải file mp4 về

## 3. Chất lượng

- Mặc định `best` = `bv*+ba/b` → lấy video tốt nhất + audio tốt nhất rồi merge về **MP4** (tương đương nút HD cao nhất trên ytsave.to).
- Muốn nhẹ hơn: `-q 1080p` / `-q 720p`.
- Luôn ra `.mp4` nhờ `merge_output_format=mp4` + `FFmpegVideoConvertor`.

## 4. Cấu trúc repo

```
.
├── download.py      # CLI: nhập link là tải
├── downloader.py    # core yt-dlp (dùng chung cho CLI + Web)
├── app.py           # Web UI Flask
├── templates/index.html
├── requirements.txt
├── run.sh
└── downloads/       # file mp4 lưu ở đây
```

## 5. Lưu ý bản quyền

Chỉ tải video bạn có quyền (video của bạn, Creative Commons, hoặc cho phép tải offline).
Không re-upload / phân phối lại nội dung có bản quyền.
