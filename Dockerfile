# Base image có sẵn Python + Playwright
FROM mcr.microsoft.com/playwright/python:v1.48.0-jammy

# Thư mục làm việc trong container
WORKDIR /app

# Copy toàn bộ code vào container
COPY . /app

# Cài đặt dependencies
RUN pip install --no-cache-dir flask python-dotenv requests playwright

# Mở cổng Flask
EXPOSE 8888

# Cài browser Chromium cho Playwright
RUN playwright install --with-deps chromium

# Lệnh chạy app Flask
CMD ["python", "webhook_server.py"]
