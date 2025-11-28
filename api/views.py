import yt_dlp
from django.http import JsonResponse, StreamingHttpResponse
from urllib.parse import quote
import os
import requests

COOKIES_FILE = os.path.join(os.getcwd(), "cookies.txt")

def get_ydl_opts():
    return {
        "quiet": True,
        # "cookiefile": COOKIES_FILE,
        "extract_flat": False,
        "nocheckcertificate": True,
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0 Safari/537.36"
            ),
            "Referer": "https://www.instagram.com/"
        }
    }


def info(request):
    url = request.GET.get("url", "")
    if not url:
        return JsonResponse({"ok": False, "message": "Missing URL"})

    try:
        with yt_dlp.YoutubeDL(get_ydl_opts()) as ydl:
            data = ydl.extract_info(url, download=False)

        # Flatten if needed
        if "entries" in data and data["entries"]:
            entry = data["entries"][0]
        else:
            entry = data

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


def download(request):
    url = request.GET.get("url", "")
    if not url:
        return JsonResponse({"ok": False, "message": "Missing URL"})

    try:
        with yt_dlp.YoutubeDL(get_ydl_opts()) as ydl:
            data = ydl.extract_info(url, download=False)

        if "entries" in data and data["entries"]:
            entry = data["entries"][0]
        else:
            entry = data

        video_url = entry["url"]
        filename = (entry.get("title") or "instagram_video").replace(" ", "_") + ".mp4"

        # Stream the mp4 file
        stream = requests.get(video_url, stream=True, timeout=15)

        resp = StreamingHttpResponse(
            stream.iter_content(chunk_size=1024 * 64),
            content_type="video/mp4"
        )
        resp["Content-Disposition"] = f'attachment; filename="{filename}"'
        return resp

    except Exception as e:
        return JsonResponse({"ok": False, "message": f"Download failed: {e}"})
