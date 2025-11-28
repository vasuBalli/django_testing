# api/ig_login.py
import requests
import os
import uuid

LOGIN_URL = "https://i.instagram.com/api/v1/accounts/login/"
USER_AGENT = "Instagram 285.0.0.26.121 Android"
DEVICE_ID = f"android-{uuid.uuid4().hex[:16]}"

def instagram_login():
    username = os.environ.get("meme_verse009")
    password = os.environ.get("Vasu@1918")

    if not username or not password:
        raise Exception("Missing IG_USERNAME or IG_PASSWORD")

    headers = {
        "User-Agent": USER_AGENT,
        "X-IG-App-ID": "124024574287414",
    }

    data = {
        "username": username,
        "enc_password": f"#PWD_INSTAGRAM_BROWSER:0:&:{password}",
        "device_id": DEVICE_ID,
        "login_attempt_count": "0"
    }

    response = requests.post(LOGIN_URL, data=data, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Instagram login failed: {response.text}")

    cookies = response.cookies.get_dict()

    if "sessionid" not in cookies:
        raise Exception(f"Login failed, sessionid missing. Response: {response.text}")

    return cookies["sessionid"]
