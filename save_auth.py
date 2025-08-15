# save_auth.py
import os
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()
USERNAME = os.getenv("LOGIN_USERNAME")
PASSWORD = os.getenv("LOGIN_PASSWORD")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    # Truy cập trang và đăng nhập
    page.goto("https://transport-dev.sonthanh.net.vn/")
    page.fill('input[placeholder="Tên đăng nhập"]', USERNAME)
    page.fill('input[placeholder="Mật khẩu"]', PASSWORD)
    page.click('button[type="submit"] >> text=Đăng nhập')

    # Chờ cho đến khi chắc chắn login xong
    page.wait_for_url("**/dashboard", timeout=15000)  # hoặc URL nào bạn biết là trang chính sau khi login
    print("✅ Đăng nhập thành công")

    # Lưu trạng thái đăng nhập
    context.storage_state(path="auth.json")
    print("✅ Đã lưu trạng thái vào auth.json")

    browser.close()
