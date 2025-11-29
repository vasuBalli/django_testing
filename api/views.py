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
@csrf_exempt
#@require_POST
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
    try:
        url = request.GET.get("url", "").strip()

        if not url:
            return JsonResponse({"ok": False, "message": "Missing URL"})

        # Extract the REAL CDN video URL
        with yt_dlp.YoutubeDL(get_ydl_opts()) as ydl:
            data = ydl.extract_info(url, download=False)

        entry = data["entries"][0] if "entries" in data else data

        video_url = entry["url"]
        filename = (entry.get("title") or "instagram_video").replace(" ", "_") + ".mp4"

        # Stream from Instagram CDN
        stream = requests.get(video_url, stream=True, timeout=20, headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.instagram.com/"
        })

        if stream.status_code != 200:
            return JsonResponse({"ok": False, "message": "CDN blocked: " + str(stream.status_code)})

        response = StreamingHttpResponse(
            stream.iter_content(chunk_size=1024 * 64),
            content_type="video/mp4"
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    except Exception as e:
        return JsonResponse({"ok": False, "message": f"Download failed: {str(e)}"})


# ------------------------------------------------------
# Health check
# ------------------------------------------------------
@require_GET
def health(request):
    return JsonResponse({"ok": True, "status": "running"})
