# api/ig_client.py
import os
import requests
from typing import Optional

# Recommended mobile headers (Instagram Android client)
DEFAULT_HEADERS = {
    "User-Agent": "Instagram 285.0.0.26.121 Android",
    "Accept": "*/*",
    "Accept-Language": "en-US",
    "Connection": "keep-alive",
    "X-IG-App-ID": "124024574287414",  # commonly used app id; keep it present
}
from .ig_login import instagram_login

def fetch_media_info(media_id: int, sessionid: Optional[str] = None, proxy: Optional[str] = None):
    if not sessionid:
        sessionid = instagram_login()  # auto-login

def fetch_media_info(media_id: int, sessionid: Optional[str] = None, proxy: Optional[str] = None) -> dict:
    """
    Calls Instagram private mobile endpoint to get media info JSON.
    Returns parsed JSON on success; raises requests.HTTPError on failure.
    """
    url = f"https://i.instagram.com/api/v1/media/{media_id}/info/"

    headers = DEFAULT_HEADERS.copy()

    cookies = {}
    if sessionid:
        cookies["sessionid"] = sessionid

    request_kwargs = {
        "headers": headers,
        "cookies": cookies or None,
        "timeout": 15,
    }

    if proxy:
        request_kwargs["proxies"] = {
            "http": proxy,
            "https": proxy,
        }

    resp = requests.get(url, **request_kwargs)
    # raise for non-200
    resp.raise_for_status()
    return resp.json()
