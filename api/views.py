import yt_dlp
from django.http import JsonResponse, StreamingHttpResponse
from urllib.parse import quote
import requests
import os


COOKIE_FILE = "/home/ubuntu/insta_cookies.txt"   # MUST EXIST


def get_ydl_opts():
    return {
        "quiet": True,
        "nocheckcertificate": True,
        "extract_flat": False,
        "cookiefile": COOKIE_FILE,   # <─ FIXES Instagram login-required
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0 Safari/537.36"
            ),
            "Referer": "https://www.instagram.com/",
            "Accept-Language": "en-US,en;q=0.9",
            "Sec-Fetch-Site": "same-origin",
        },
    }


def extract_entry(data):
    if "entries" in data and data["entries"]:
        return data["entries"][0]
    return data


def info(request):
    url = request.GET.get("url", "")
    if not url:
        return JsonResponse({"ok": False, "message": "Missing URL"})

    try:
        with yt_dlp.YoutubeDL(get_ydl_opts()) as ydl:
            data = ydl.extract_info(url, download=False)

        entry = extract_entry(data)

        title = entry.get("title", "Instagram Video")
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
        return JsonResponse({"ok": False, "message": f"Error: {str(e)}"})


def download(request):
    url = request.GET.get("url", "")
    if not url:
        return JsonResponse({"ok": False, "message": "Missing URL"})

    try:
        with yt_dlp.YoutubeDL(get_ydl_opts()) as ydl:
            data = ydl.extract_info(url, download=False)

        entry = extract_entry(data)
        video_url = entry["url"]
        filename = (entry.get("title") or "instagram_video").replace(" ", "_") + ".mp4"

        # Stream from Instagram CDN
        stream = requests.get(video_url, stream=True, timeout=20, headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.instagram.com/"
        })

        if stream.status_code != 200:
            return JsonResponse({
                "ok": False,
                "message": f"CDN error: {stream.status_code}"
            })

        response = StreamingHttpResponse(
            stream.iter_content(chunk_size=1024 * 64),
            content_type="video/mp4"
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    except Exception as e:
        return JsonResponse({"ok": False, "message": f"Download failed: {e}"})
