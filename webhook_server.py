import os
import time
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
import requests

# Load biến môi trường
load_dotenv()

USERNAME = os.getenv("LOGIN_USERNAME")
PASSWORD = os.getenv("LOGIN_PASSWORD")
DONE_URL = os.getenv("DONE_URL")

app = Flask(__name__)

def autofill_order(data):
    row_index = data.get("rowIndex")
    ma_b = data.get("ma_b")
    tong_tien = data.get("tong_tien")
    tong_tien_number = int(''.join(filter(str.isdigit, str(tong_tien) or "0")))

    phi_luu_ca = data.get("phi_luu_ca", 0)
    phi_luu_ca_number = int(''.join(filter(str.isdigit, str(phi_luu_ca) or "0")))

    phi_rot_diem = data.get("phi_rot_diem", 0)
    phi_rot_diem_number = int(''.join(filter(str.isdigit, str(phi_rot_diem) or "0")))

    phi_khac = data.get("phi_khac", "")
    phi_khac_number = int(''.join(filter(str.isdigit, str(phi_khac) or "0")))

    ly_do_phat_sinh = data.get("ly_do_phat_sinh", "")

    print(row_index, ma_b, tong_tien)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state="auth.json")
        page = context.new_page()

        page.goto("https://transport-dev.sonthanh.net.vn/")

        # Đăng nhập
        page.fill('input[placeholder="Tên đăng nhập"]', USERNAME)
        page.fill('input[placeholder="Mật khẩu"]', PASSWORD)
        page.click('button[type="submit"] >> text=Đăng nhập')

        page.wait_for_load_state("networkidle")
        page.locator("div.toggle-icon-container svg").click()

        page.locator("p.w-full.whitespace-nowrap", has_text="Đơn hàng").first.click()
        page.locator("p.w-full.py-1.whitespace-nowrap", has_text="Danh sách đơn hàng").click()

        page.click("body")

        page.fill('input[placeholder="Tìm kiếm theo mã đơn hàng"]', ma_b)
        page.press('input[placeholder="Tìm kiếm theo mã đơn hàng"]', "Enter")

        page.locator(f'td.text-blue-500:has-text("{ma_b}")').click()

        page.locator("p.normal-tab", has_text="Thu - Chi").click()
        page.get_by_role("button", name="Chỉnh sửa chi phí").click()

        # Nhập chi phí
        chi_input = page.locator("tr.table-hover-row", has_text="Cước vận chuyển") \
                        .locator("input[placeholder='Chi bình thường']")
        chi_input.wait_for(timeout=5000)
        chi_input.fill(str(tong_tien_number))

        # Lưu ca
        luu_ca_input = page.locator("tr.table-hover-row", has_text="Lưu ca xe") \
                           .locator("input[placeholder='Chi bình thường']")
        luu_ca_input.wait_for(timeout=5000)
        luu_ca_input.fill(str(phi_luu_ca_number))

        # Rớt điểm
        rot_diem_input = page.locator("tr.table-hover-row", has_text="Phí giao 2 điểm") \
                             .locator("input[placeholder='Chi bình thường']")
        rot_diem_input.wait_for(timeout=5000)
        rot_diem_input.fill(str(phi_rot_diem_number or "0"))

        # Phí khác
        phi_khac_input = page.locator("tr.table-hover-row", has_text="Phí khác") \
                             .locator("input[placeholder='Chi bình thường']")
        phi_khac_input.wait_for(timeout=5000)
        phi_khac_input.fill(str(phi_khac_number))

        # Ghi chú cho phí khác
        ghi_chu_input = page.locator("tr.table-hover-row", has_text="Phí khác") \
                             .locator('input[placeholder="Ghi chú"]')
        ghi_chu_input.wait_for(timeout=5000)
        ghi_chu_input.fill(ly_do_phat_sinh)

        page.locator("button", has_text="Cập nhật").click()
        page.wait_for_timeout(3000)

        # Gọi lại Apps Script để đánh dấu done
        if row_index and DONE_URL:
            try:
                requests.get(DONE_URL, params={"rowIndex": row_index})
                print(f"✅ Đã gửi yêu cầu đánh dấu 'done' cho dòng {row_index}")
            except Exception as e:
                print(f"❌ Không thể gửi đánh dấu 'done': {e}")

        browser.close()

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()

        if "ma_b" in data and "tong_tien" in data:
            autofill_order(data)
            return jsonify({"status": "success"}), 200

        elif "orders" in data:
            for order in data["orders"]:
                if "ma_b" in order and "tong_tien" in order:
                    autofill_order(order)
                    time.sleep(2)
            return jsonify({"status": "success", "count": len(data["orders"])}), 200

        else:
            return jsonify({"error": "Dữ liệu không hợp lệ"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8765)
