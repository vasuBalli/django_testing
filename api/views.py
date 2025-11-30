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
        temp_path = "/tmp/%(id)s.%(ext)s"

        ydl_opts = {
            "quiet": True,
            "format": "bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
            "ffmpeg_location": "/usr/bin",   # <---- 
            "outtmpl": "/tmp/%(id)s.%(ext)s",
            "cookiefile": "/home/ubuntu/insta_cookies.txt",
            "http_headers": {
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://www.instagram.com/"
            }
        }


        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        # Final merged output file
        final_file = f"/tmp/{info['id']}.mp4"

        if not os.path.exists(final_file):
            return JsonResponse({"ok": False, "message": "Failed to combine audio/video"})

        def generate():
            with open(final_file, "rb") as f:
                for chunk in iter(lambda: f.read(1024 * 64), b""):
                    yield chunk

        response = StreamingHttpResponse(generate(), content_type="video/mp4")
        response["Content-Disposition"] = f'attachment; filename=\"{info.get('title','video')}.mp4\"'

        return response

    except Exception as e:
        return JsonResponse({"ok": False, "message": f"Download failed: {e}"})






# ------------------------------------------------------
# Health check
# ------------------------------------------------------
@require_GET
def health(request):
    return JsonResponse({"ok": True, "status": "running"})
