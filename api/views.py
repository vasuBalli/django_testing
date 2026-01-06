import yt_dlp
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from urllib.parse import quote
import json
import requests
import os
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Avg, Sum
from django.utils import timezone
from datetime import timedelta
from .models import TrafficLog
from .models import NginxTraffic
import logging

# Path to your cookie file
COOKIE_FILE = "/home/ubuntu/insta_cookies.txt"

logging.basicConfig(level=logging.INFO)
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
    logging.info("Testing endpoint hit")
    return JsonResponse({"ok": True})

@csrf_exempt
# @require_POST
def info(request):
    logging.info("Info endpoint hit")
    try:
        # logging.info(f"Received request: {request.GET.get("url")}")
        
        logging.info(request.body)
        url = json.loads(request.body).get("url", "").strip()
        logging.info(f"Received URL for info: {url}")
        if not url:
            return JsonResponse({"ok": False, "message": "Missing URL"})

        # Extract metadata (without download)
        with yt_dlp.YoutubeDL(get_ydl_opts()) as ydl:
            data = ydl.extract_info(url, download=False)
        logging.info(f"Extracted data: {data}")
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
        logging.info(f"Error in info endpoint: {e}")
        return JsonResponse({"ok": False, "message": str(e)})



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



def nginx_traffic_dashboard(request):
    now = timezone.now()
    last_24h = now - timedelta(hours=24)

    # UNIQUE IP COUNT
    unique_ips = (
        NginxTraffic.objects.filter(timestamp__gte=last_24h)
        .values("ip")
        .distinct()
        .count()
    )

    # HOURLY TRAFFIC
    hourly_data = []
    for i in range(24):
        start = now - timedelta(hours=23 - i)
        end = start + timedelta(hours=1)
        count = (
            NginxTraffic.objects.filter(timestamp__gte=start, timestamp__lt=end)
            .values("ip")
            .distinct()
            .count()
        )
        hourly_data.append({"hour": start.strftime("%H:%M"), "count": count})

    # TOP PAGES
    top_pages = (
        NginxTraffic.objects.filter(timestamp__gte=last_24h)
        .values("path")
        .annotate(unique_visitors=Count("ip", distinct=True))
        .order_by("-unique_visitors")[:10]
    )

    return render(
        request,
        "downloader/nginx_traffic_dashboard.html",
        {
            "unique_ips": unique_ips,
            "hourly_data": hourly_data,
            "top_pages": top_pages,
        },
    )

# @staff_member_required
def admin_traffic_dashboard(request):
    # time window
    now = timezone.now()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)

    total_24h = TrafficLog.objects.filter(timestamp__gte=last_24h).values("ip").distinct().count()

    avg_resp_24h = TrafficLog.objects.filter(timestamp__gte=last_24h).aggregate(Avg("response_time_ms"))["response_time_ms__avg"] or 0
    errors_24h = TrafficLog.objects.filter(timestamp__gte=last_24h, status_code__gte=500).count()

    top_paths = list(
        TrafficLog.objects.filter(timestamp__gte=last_24h)
        .values("path")
        .annotate(count=Count("id"))
        .order_by("-count")[:10]
    )

    # simple timeseries per hour for last 24h
    series = []
    for i in range(24):
        t0 = now - timedelta(hours=23-i)
        t1 = t0 + timedelta(hours=1)
        cnt = TrafficLog.objects.filter(timestamp__gte=t0, timestamp__lt=t1).values("ip").distinct().count()

        series.append({"time": t0.strftime("%Y-%m-%d %H:%M"), "count": cnt})

    context = {
        "total_24h": total_24h,
        "avg_resp_24h": round(avg_resp_24h or 0, 2),
        "errors_24h": errors_24h,
        "top_paths": top_paths,
        "series": series,
    }
    return render(request, "downloader/admin_traffic_dashboard.html", context)

# JSON endpoint for chart data (optional)
# @staff_member_required
def admin_traffic_data(request):
    now = timezone.now()
    series = []
    for i in range(24):
        t0 = now - timedelta(hours=23-i)
        t1 = t0 + timedelta(hours=1)
        cnt = TrafficLog.objects.filter(timestamp__gte=t0, timestamp__lt=t1).count()
        series.append({"time": t0.strftime("%Y-%m-%d %H:%M"), "count": cnt})
    return JsonResponse({"series": series})
