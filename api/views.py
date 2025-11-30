import yt_dlp
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from urllib.parse import quote
import json
import requests
import os

# Path to your cookie file
COOKIE_FILE = "/home/ubuntu/insta_cookies.txt"


# ------------------------------------------------------
# yt-dlp options
# ------------------------------------------------------
def get_ydl_opts():
    return {
        "quiet": True,
        "nocheckcertificate": True,
        "extract_flat": False,
        "cookiefile": COOKIE_FILE,      # <-- your cookies
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0 Safari/537.36"
            ),
            "Referer": "https://www.instagram.com/",
            "Accept-Language": "en-US,en;q=0.9",
        },
    }


# ------------------------------------------------------
# /api/info
# ------------------------------------------------------
def testing(request):
    return JsonResponse({"ok": True})

@csrf_exempt
# @require_POST
def info(request):
    try:
        body = json.loads(request.body)
        url = body.get("url", "").strip()

        if not url:
            return JsonResponse({"ok": False, "message": "Missing URL"})

        # Extract metadata (without download)
        with yt_dlp.YoutubeDL(get_ydl_opts()) as ydl:
            data = ydl.extract_info(url, download=False)

        # If it's a carousel, pick first video
        entry = data["entries"][0] if "entries" in data else data

        title = entry.get("title") or "Instagram Video"
        duration = entry.get("duration")

        if duration:
            m, s = divmod(int(duration), 60)
            duration_str = f"{m}:{s:02d}"
        else:
            duration_str = ""

        return JsonResponse({
            "ok": True,
            "title": title,
            "duration": duration_str,
            "download_url": f"/api/download/?url={quote(url)}"
        })

    except Exception as e:
        return JsonResponse({"ok": False, "message": str(e)})


# ------------------------------------------------------
# /api/download
# ------------------------------------------------------
@require_GET
def download(request):
    url = request.GET.get("url", "").strip()
    if not url:
        return JsonResponse({"ok": False, "message": "Missing URL"})

    try:
        # Tell yt-dlp to merge best video+bestaudio into MP4
        ydl_opts = {
            "quiet": True,
            "merge_output_format": "mp4",
            "format": "bestvideo+bestaudio/best",
            "outtmpl": "/tmp/%(id)s.%(ext)s",
            "http_headers": {
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://www.instagram.com/"
            },
            "cookiefile": "/home/ubuntu/insta_cookies.txt"
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        filename = f"/tmp/{info['id']}.mp4"

        # Stream final merged MP4
        if not os.path.exists(filename):
            return JsonResponse({"ok": False, "message": "Download file missing"})

        def file_stream():
            with open(filename, "rb") as f:
                while True:
                    chunk = f.read(1024 * 64)
                    if not chunk:
                        break
                    yield chunk

        response = StreamingHttpResponse(file_stream(), content_type="video/mp4")
        response["Content-Disposition"] = f'attachment; filename=\"{info.get('title', 'video')}.mp4\"'
        return response

    except Exception as e:
        return JsonResponse({"ok": False, "message": f"Download failed: {e}"})




# ------------------------------------------------------
# Health check
# ------------------------------------------------------
@require_GET
def health(request):
    return JsonResponse({"ok": True, "status": "running"})
