from playwright.sync_api import sync_playwright
import json

USERNAME = "your_username"
PASSWORD = "your_password"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)  # headless browser
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Linux; Android 12; SM-G991B)"
    )
    page = context.new_page()

    page.goto("https://www.instagram.com/accounts/login/")
    page.fill("input[name=username]", "fastapi_backend/tests.py")
    page.fill("input[name=password]", "Vasu@1918")
    page.click("button[type=submit]")

    page.wait_for_load_state("networkidle")
    
    cookies = context.cookies()
    with open("cookies.json", "w") as f:
        json.dump(cookies, f, indent=2)

    print("Cookies saved successfully!")
